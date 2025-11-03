#!/usr/bin/env python3
"""Input validation utilities for the Boston OpenData MCP server."""

import re
import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .exceptions import ValidationError


class SearchDatasetsRequest(BaseModel):
    """Validation model for search_datasets tool."""

    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results"
    )

    @validator("query")
    def validate_query(cls, v):
        # Remove excessive whitespace
        v = " ".join(v.split())

        # Check for potentially malicious patterns
        if re.search(r'[<>"\']', v):
            raise ValidationError("Query contains invalid characters")

        return v


class ListAllDatasetsRequest(BaseModel):
    """Validation model for list_all_datasets tool."""

    limit: int = Field(
        default=20, ge=1, le=100, description="Number of datasets to return"
    )


class GetDatasetInfoRequest(BaseModel):
    """Validation model for get_dataset_info tool."""

    dataset_id: str = Field(..., min_length=1, max_length=100, description="Dataset ID")

    @validator("dataset_id")
    def validate_dataset_id(cls, v):
        # Remove whitespace
        v = v.strip()

        # Check for valid dataset ID pattern (alphanumeric, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValidationError("Dataset ID contains invalid characters")

        return v


class QueryDatastoreRequest(BaseModel):
    """Validation model for query_datastore tool."""

    resource_id: str = Field(..., description="Resource ID (UUID format)")
    limit: int = Field(
        default=10, ge=1, le=1000, description="Number of records to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of records to skip")
    search_text: Optional[str] = Field(
        None, max_length=500, description="Full-text search query"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Filter by field values"
    )
    sort: Optional[str] = Field(None, max_length=100, description="Sort specification")
    fields: Optional[List[str]] = Field(None, description="Specific fields to return")

    @validator("resource_id")
    def validate_resource_id(cls, v):
        # Remove whitespace
        v = v.strip()

        # Validate UUID format
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValidationError("Resource ID must be a valid UUID")

        return v

    @validator("search_text")
    def validate_search_text(cls, v):
        if v is not None:
            # Remove excessive whitespace
            v = " ".join(v.split())

            # Check for potentially malicious patterns
            if re.search(r'[<>"\']', v):
                raise ValidationError("Search text contains invalid characters")

        return v

    @validator("filters")
    def validate_filters(cls, v):
        if v is not None:
            # Limit number of filters
            if len(v) > 20:
                raise ValidationError("Too many filters (maximum 20)")

            # Validate filter keys and values
            for key, value in v.items():
                if not isinstance(key, str) or len(key) > 50:
                    raise ValidationError(f"Invalid filter key: {key}")

                if isinstance(value, str) and len(value) > 200:
                    raise ValidationError(f"Filter value too long for key: {key}")

        return v

    @validator("sort")
    def validate_sort(cls, v):
        if v is not None:
            # Remove whitespace
            v = v.strip()

            # Validate sort format: "field_name asc" or "field_name desc"
            if not re.match(r"^[a-zA-Z0-9_]+ (asc|desc)$", v, re.IGNORECASE):
                raise ValidationError(
                    "Sort must be in format 'field_name asc' or 'field_name desc'"
                )

        return v

    @validator("fields")
    def validate_fields(cls, v):
        if v is not None:
            # Limit number of fields
            if len(v) > 50:
                raise ValidationError("Too many fields requested (maximum 50)")

            # Validate field names
            for field in v:
                if not isinstance(field, str) or not re.match(
                    r"^[a-zA-Z0-9_]+$", field
                ):
                    raise ValidationError(f"Invalid field name: {field}")

        return v


class GetDatastoreSchemaRequest(BaseModel):
    """Validation model for get_datastore_schema tool."""

    resource_id: str = Field(..., description="Resource ID (UUID format)")

    @validator("resource_id")
    def validate_resource_id(cls, v):
        # Remove whitespace
        v = v.strip()

        # Validate UUID format
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValidationError("Resource ID must be a valid UUID")

        return v


def validate_tool_request(tool_name: str, arguments: Dict[str, Any]) -> BaseModel:
    """Validate tool request arguments.

    Args:
        tool_name: Name of the tool being called
        arguments: Tool arguments to validate

    Returns:
        Validated request model

    Raises:
        ValidationError: If validation fails
    """
    validation_models = {
        "search_datasets": SearchDatasetsRequest,
        "list_all_datasets": ListAllDatasetsRequest,
        "get_dataset_info": GetDatasetInfoRequest,
        "query_datastore": QueryDatastoreRequest,
        "get_datastore_schema": GetDatastoreSchemaRequest,
    }

    if tool_name not in validation_models:
        raise ValidationError(f"Unknown tool: {tool_name}")

    try:
        return validation_models[tool_name](**arguments)
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Validation failed: {str(e)}")


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize a string value for safe use.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)

    # Remove excessive whitespace
    value = " ".join(value.split())

    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length] + "..."

    # Remove potentially dangerous characters
    value = re.sub(r'[<>"\']', "", value)

    return value


def validate_pagination_params(
    limit: int, offset: int, max_limit: int = 1000
) -> tuple[int, int]:
    """Validate and normalize pagination parameters.

    Args:
        limit: Number of items to return
        offset: Number of items to skip
        max_limit: Maximum allowed limit

    Returns:
        Tuple of (validated_limit, validated_offset)

    Raises:
        ValidationError: If parameters are invalid
    """
    if limit < 1:
        raise ValidationError("Limit must be at least 1")

    if limit > max_limit:
        raise ValidationError(f"Limit cannot exceed {max_limit}")

    if offset < 0:
        raise ValidationError("Offset must be non-negative")

    # Prevent excessive offset that could cause performance issues
    if offset > 100000:
        raise ValidationError("Offset too large (maximum 100,000)")

    return limit, offset

