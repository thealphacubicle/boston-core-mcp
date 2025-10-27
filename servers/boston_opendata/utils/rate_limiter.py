#!/usr/bin/env python3
"""Rate limiting implementation for the Boston OpenData MCP server."""

import asyncio
import time
from typing import Any, Dict, Optional

from .exceptions import RateLimitError


class TokenBucket:
    """Token bucket rate limiter implementation."""

    def __init__(
        self, capacity: int, refill_rate: float, initial_tokens: Optional[int] = None
    ):
        """Initialize token bucket.

        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Tokens added per second
            initial_tokens: Initial number of tokens (defaults to capacity)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = initial_tokens if initial_tokens is not None else capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if not enough tokens available
        """
        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate

        if tokens_to_add > 0:
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now

    async def wait_for_tokens(
        self, tokens: int = 1, timeout: Optional[float] = None
    ) -> bool:
        """Wait for tokens to become available.

        Args:
            tokens: Number of tokens needed
            timeout: Maximum time to wait (None for no timeout)

        Returns:
            True if tokens became available, False if timeout
        """
        start_time = time.time()

        while True:
            if await self.consume(tokens):
                return True

            if timeout is not None and (time.time() - start_time) >= timeout:
                return False

            # Wait a bit before checking again
            await asyncio.sleep(0.1)


class RateLimiter:
    """Rate limiter with support for multiple clients and different limits."""

    def __init__(
        self,
        default_capacity: int = 100,
        default_refill_rate: float = 1.0,
        burst_capacity: int = 10,
        burst_refill_rate: float = 10.0,
    ):
        """Initialize rate limiter.

        Args:
            default_capacity: Default bucket capacity for normal requests
            default_refill_rate: Default refill rate for normal requests
            burst_capacity: Bucket capacity for burst requests
            burst_refill_rate: Refill rate for burst requests
        """
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate
        self.burst_capacity = burst_capacity
        self.burst_refill_rate = burst_refill_rate

        # Per-client rate limiters
        self._clients: Dict[str, TokenBucket] = {}
        self._burst_limiter = TokenBucket(burst_capacity, burst_refill_rate)
        self._lock = asyncio.Lock()

    async def acquire(
        self,
        client_id: Optional[str] = None,
        tokens: int = 1,
        burst: bool = False,
        timeout: Optional[float] = None,
    ) -> bool:
        """Acquire tokens for a request.

        Args:
            client_id: Client identifier (None for global limit)
            tokens: Number of tokens needed
            burst: Whether this is a burst request
            timeout: Maximum time to wait

        Returns:
            True if tokens were acquired, False if rate limited

        Raises:
            RateLimitError: If rate limit is exceeded and no timeout specified
        """
        if burst:
            success = await self._burst_limiter.wait_for_tokens(tokens, timeout)
        else:
            if client_id is not None:
                success = await self._acquire_for_client(client_id, tokens, timeout)
            else:
                # Use global default limiter
                async with self._lock:
                    if "global" not in self._clients:
                        self._clients["global"] = TokenBucket(
                            self.default_capacity, self.default_refill_rate
                        )
                    success = await self._clients["global"].wait_for_tokens(
                        tokens, timeout
                    )

        if not success:
            retry_after = self._calculate_retry_after(client_id, burst)
            raise RateLimitError(
                f"Rate limit exceeded. Try again in {retry_after:.1f} seconds.",
                retry_after=retry_after,
            )

        return True

    async def _acquire_for_client(
        self, client_id: str, tokens: int, timeout: Optional[float]
    ) -> bool:
        """Acquire tokens for a specific client."""
        async with self._lock:
            if client_id not in self._clients:
                self._clients[client_id] = TokenBucket(
                    self.default_capacity, self.default_refill_rate
                )

        return await self._clients[client_id].wait_for_tokens(tokens, timeout)

    def _calculate_retry_after(self, client_id: Optional[str], burst: bool) -> float:
        """Calculate retry after time for rate limit error."""
        if burst:
            return self.burst_capacity / self.burst_refill_rate
        else:
            return self.default_capacity / self.default_refill_rate

    async def get_status(self, client_id: Optional[str] = None) -> Dict[str, any]:
        """Get current rate limiter status.

        Args:
            client_id: Client identifier (None for global status)

        Returns:
            Dictionary with status information
        """
        if client_id is not None and client_id in self._clients:
            bucket = self._clients[client_id]
            return {
                "tokens_available": bucket.tokens,
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
                "last_refill": bucket.last_refill,
            }
        elif client_id is None and "global" in self._clients:
            bucket = self._clients["global"]
            return {
                "tokens_available": bucket.tokens,
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
                "last_refill": bucket.last_refill,
            }
        else:
            return {
                "tokens_available": 0,
                "capacity": self.default_capacity,
                "refill_rate": self.default_refill_rate,
                "last_refill": time.time(),
            }


# Global rate limiter instance
rate_limiter = RateLimiter(
    default_capacity=100,  # 100 requests per minute
    default_refill_rate=100 / 60,  # Refill at 100 tokens per minute
    burst_capacity=20,  # Allow 20 burst requests
    burst_refill_rate=20 / 60,  # Refill burst at 20 tokens per minute
)
