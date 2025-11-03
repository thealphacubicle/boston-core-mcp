#!/usr/bin/env python3
"""Configuration management for the Boston OpenData MCP server."""

import os
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings

from .utils.exceptions import ConfigurationError


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # CKAN API Configuration
    ckan_base_url: str = Field(
        default="https://data.boston.gov/api/3/action",
        description="Base URL for CKAN API",
    )

    # Timeout Configuration
    api_timeout: float = Field(
        default=30.0, ge=1.0, le=300.0, description="API request timeout in seconds"
    )
    connect_timeout: float = Field(
        default=10.0, ge=1.0, le=60.0, description="Connection timeout in seconds"
    )
    read_timeout: float = Field(
        default=30.0, ge=1.0, le=300.0, description="Read timeout in seconds"
    )

    # Rate Limiting Configuration
    rate_limit_capacity: int = Field(
        default=100, ge=1, le=1000, description="Rate limit bucket capacity"
    )
    rate_limit_refill_rate: float = Field(
        default=100 / 60,  # 100 requests per minute
        ge=0.1,
        le=100.0,
        description="Rate limit refill rate (tokens per second)",
    )
    burst_capacity: int = Field(
        default=20, ge=1, le=100, description="Burst request capacity"
    )
    burst_refill_rate: float = Field(
        default=20 / 60,  # 20 requests per minute
        ge=0.1,
        le=50.0,
        description="Burst refill rate (tokens per second)",
    )

    # Circuit Breaker Configuration
    circuit_breaker_failure_threshold: int = Field(
        default=3, ge=1, le=20, description="Circuit breaker failure threshold"
    )
    circuit_breaker_recovery_timeout: float = Field(
        default=30.0,
        ge=5.0,
        le=300.0,
        description="Circuit breaker recovery timeout in seconds",
    )
    circuit_breaker_success_threshold: int = Field(
        default=3, ge=1, le=10, description="Circuit breaker success threshold"
    )

    # Retry Configuration
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum number of retries"
    )
    retry_delay: float = Field(
        default=1.0, ge=0.1, le=10.0, description="Initial retry delay in seconds"
    )
    retry_backoff_multiplier: float = Field(
        default=2.0, ge=1.0, le=5.0, description="Retry backoff multiplier"
    )
    max_retry_delay: float = Field(
        default=60.0, ge=1.0, le=300.0, description="Maximum retry delay in seconds"
    )

    # Data Limits
    max_records: int = Field(
        default=1000, ge=1, le=10000, description="Maximum number of records per query"
    )
    max_response_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024,
        le=100 * 1024 * 1024,  # 100MB
        description="Maximum response size in bytes",
    )
    max_request_size: int = Field(
        default=1024 * 1024,  # 1MB
        ge=1024,
        le=10 * 1024 * 1024,  # 10MB
        description="Maximum request size in bytes",
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    log_include_extra: bool = Field(
        default=True, description="Include extra fields in JSON logs"
    )

    # Health Check Configuration
    health_check_interval: float = Field(
        default=30.0, ge=5.0, le=300.0, description="Health check interval in seconds"
    )
    health_check_timeout: float = Field(
        default=5.0, ge=1.0, le=30.0, description="Health check timeout in seconds"
    )

    # Connection Pool Configuration
    max_connections: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of connections in pool"
    )
    max_keepalive_connections: int = Field(
        default=20, ge=1, le=100, description="Maximum number of keepalive connections"
    )
    keepalive_expiry: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Keepalive connection expiry in seconds",
    )

    # Environment
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @validator("log_format")
    def validate_log_format(cls, v):
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()

    @validator("environment")
    def validate_environment(cls, v):
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()

    @validator("ckan_base_url")
    def validate_ckan_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("CKAN base URL must start with http:// or https://")
        return v.rstrip("/")

    class Config:
        env_prefix = "BOSTON_OPENDATA_"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Backward compatibility exports
CKAN_BASE_URL = settings.ckan_base_url
API_TIMEOUT = settings.api_timeout
MAX_RECORDS = settings.max_records

# Additional timeout configurations
CONNECT_TIMEOUT = settings.connect_timeout
READ_TIMEOUT = settings.read_timeout

# Rate limiting
RATE_LIMIT_CAPACITY = settings.rate_limit_capacity
RATE_LIMIT_REFILL_RATE = settings.rate_limit_refill_rate
BURST_CAPACITY = settings.burst_capacity
BURST_REFILL_RATE = settings.burst_refill_rate

# Circuit breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD = settings.circuit_breaker_failure_threshold
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = settings.circuit_breaker_recovery_timeout
CIRCUIT_BREAKER_SUCCESS_THRESHOLD = settings.circuit_breaker_success_threshold

# Retry configuration
MAX_RETRIES = settings.max_retries
RETRY_DELAY = settings.retry_delay
RETRY_BACKOFF_MULTIPLIER = settings.retry_backoff_multiplier
MAX_RETRY_DELAY = settings.max_retry_delay

# Data limits
MAX_RESPONSE_SIZE = settings.max_response_size
MAX_REQUEST_SIZE = settings.max_request_size

# Connection pool
MAX_CONNECTIONS = settings.max_connections
MAX_KEEPALIVE_CONNECTIONS = settings.max_keepalive_connections
KEEPALIVE_EXPIRY = settings.keepalive_expiry

# Environment
ENVIRONMENT = settings.environment
DEBUG = settings.debug

