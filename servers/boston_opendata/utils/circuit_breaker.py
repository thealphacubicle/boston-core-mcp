#!/usr/bin/env python3
"""Circuit breaker pattern implementation for the Boston OpenData MCP server."""

import asyncio
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar

from .exceptions import CircuitBreakerError

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is back


class CircuitBreaker:
    """Circuit breaker implementation with configurable thresholds."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        success_threshold: int = 3,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying half-open state
            expected_exception: Exception type to count as failures
            success_threshold: Number of successes needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function raises an exception
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}",
                        circuit_state="open",
                    )

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.expected_exception as e:
            await self._on_failure()
            raise
        except Exception as e:
            # Don't count unexpected exceptions as circuit breaker failures
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True

        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                # Failed during half-open, go back to open
                self.state = CircuitState.OPEN
            elif self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state.

        Returns:
            Dictionary with state information
        """
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }

    async def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None


class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""

    def __init__(self):
        """Initialize circuit breaker manager."""
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    def get_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        success_threshold: int = 3,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker.

        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures before opening
            recovery_timeout: Time to wait before trying half-open
            expected_exception: Exception type to count as failures
            success_threshold: Number of successes needed to close

        Returns:
            Circuit breaker instance
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception,
                success_threshold=success_threshold,
            )

        return self._breakers[name]

    async def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get state of all circuit breakers.

        Returns:
            Dictionary mapping breaker names to their states
        """
        return {name: breaker.get_state() for name, breaker in self._breakers.items()}

    async def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            await breaker.reset()


# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()

# Default circuit breaker for CKAN API calls
ckan_circuit_breaker = circuit_manager.get_breaker(
    "ckan_api", failure_threshold=3, recovery_timeout=30.0, expected_exception=Exception
)
