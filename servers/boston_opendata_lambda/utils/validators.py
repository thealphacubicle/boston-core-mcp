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


def _fuzzy_match_field(
    field_name: str, valid_fields: List[str], threshold: float = 0.7
) -> Optional[str]:
    """Find the best matching field name using simple string similarity.

    Uses a simple ratio-based similarity (common characters / max length).
    This is a lightweight alternative to libraries like fuzzywuzzy.

    Args:
        field_name: The field name to match
        valid_fields: List of valid field names
        threshold: Minimum similarity ratio (0.0 to 1.0) to consider a match

    Returns:
        Best matching field name if similarity >= threshold, None otherwise
    """
    field_name_lower = field_name.lower()
    best_match = None
    best_score = 0.0

    for valid_field in valid_fields:
        valid_lower = valid_field.lower()

        # Exact match (case-insensitive)
        if field_name_lower == valid_lower:
            return valid_field

        # Calculate simple similarity ratio
        # Count common characters (case-insensitive)
        common_chars = sum(
            1 for c in field_name_lower if c in valid_lower
        ) + sum(1 for c in valid_lower if c in field_name_lower)
        max_len = max(len(field_name_lower), len(valid_lower))
        score = common_chars / (max_len * 2) if max_len > 0 else 0.0

        # Bonus for substring matches
        if field_name_lower in valid_lower or valid_lower in field_name_lower:
            score += 0.2

        if score > best_score:
            best_score = score
            best_match = valid_field

    return best_match if best_score >= threshold else None


def validate_and_correct_field_names(
    field_names: List[str],
    valid_fields: List[str],
    context: str = "field",
) -> tuple[List[str], List[str], Dict[str, str]]:
    """Validate field names against a schema and suggest corrections.

    Args:
        field_names: List of field names to validate
        valid_fields: List of valid field names from the schema
        context: Context string for error messages (e.g., "filter", "sort", "fields")

    Returns:
        Tuple of (corrected_field_names, invalid_fields, corrections_made)
        - corrected_field_names: List with invalid fields replaced by corrections
        - invalid_fields: List of field names that couldn't be corrected
        - corrections_made: Dict mapping original -> corrected field names
    """
    if not valid_fields:
        return field_names, field_names, {}

    valid_field_set = set(valid_fields)
    corrected = []
    invalid = []
    corrections = {}

    for field in field_names:
        if field in valid_field_set:
            # Field is valid, use as-is
            corrected.append(field)
        else:
            # Try to find a fuzzy match
            match = _fuzzy_match_field(field, valid_fields)
            if match:
                corrected.append(match)
                corrections[field] = match
            else:
                corrected.append(field)  # Keep original for error reporting
                invalid.append(field)

    return corrected, invalid, corrections


def validate_filter_value(value: Any, field_name: str) -> tuple[bool, Optional[str]]:
    """Validate that a filter value is in a supported format.

    CKAN datastore_search only supports exact match filters (field = value).
    It does NOT support MongoDB-style operators like $gte, $lte, $gt, $lt, etc.

    Args:
        value: The filter value to validate
        field_name: The field name for error messages

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if the value format is supported
        - error_message: Error message if invalid, None if valid
    """
    # Check for MongoDB-style operators (not supported by CKAN datastore_search)
    if isinstance(value, dict):
        # Check for any MongoDB-style operators
        unsupported_ops = []
        for key in value.keys():
            if isinstance(key, str) and key.startswith("$"):
                unsupported_ops.append(key)

        if unsupported_ops:
            ops_list = ", ".join(sorted(unsupported_ops))
            return (
                False,
                f"Unsupported filter operators for field '{field_name}': {ops_list}. "
                f"CKAN datastore_search only supports exact match filters (field = value). "
                f"For date ranges, you may need to use multiple exact value filters or "
                f"query the data and filter client-side.",
            )

    # Check for nested dictionaries (not supported)
    if isinstance(value, dict):
        # Check if it's a nested structure (not just a simple dict)
        for v in value.values():
            if isinstance(v, (dict, list)):
                return (
                    False,
                    f"Complex nested filter structures are not supported for field '{field_name}'. "
                    f"CKAN datastore_search only supports simple exact match filters.",
                )

    # Check for lists (might be supported for "IN" queries, but verify)
    if isinstance(value, list) and len(value) == 0:
        return (
            False,
            f"Empty list filter value for field '{field_name}' is not supported.",
        )

    return True, None


def validate_datastore_query_fields(
    filters: Optional[Dict[str, Any]],
    sort: Optional[str],
    fields: Optional[List[str]],
    valid_fields: List[str],
) -> tuple[Optional[Dict[str, Any]], Optional[str], Optional[List[str]], Dict[str, str], List[str], List[str]]:
    """Validate and correct field names in datastore query parameters.

    Args:
        filters: Filter dictionary with field names as keys
        sort: Sort string in format "field_name asc/desc"
        fields: List of field names to return
        valid_fields: List of valid field names from the schema

    Returns:
        Tuple of (corrected_filters, corrected_sort, corrected_fields, corrections, errors, filter_errors)
        - corrected_filters: Filters with corrected field names
        - corrected_sort: Sort string with corrected field name
        - corrected_fields: Fields list with corrected field names
        - corrections: Dict mapping original -> corrected field names
        - errors: List of field names that couldn't be corrected
        - filter_errors: List of filter format errors (unsupported operators, etc.)
    """
    corrections = {}
    errors = []
    filter_errors = []

    # Validate and correct filter field names
    corrected_filters = None
    if filters:
        corrected_filters = {}
        for field_name, value in filters.items():
            # First validate the filter value format
            is_valid_format, format_error = validate_filter_value(value, field_name)
            if not is_valid_format:
                filter_errors.append(format_error)
                # Don't add to corrected_filters if format is invalid
                continue

            # Then validate/correct the field name
            if field_name in valid_fields:
                corrected_filters[field_name] = value
            else:
                match = _fuzzy_match_field(field_name, valid_fields)
                if match:
                    corrected_filters[match] = value
                    corrections[field_name] = match
                else:
                    corrected_filters[field_name] = value  # Keep for error reporting
                    errors.append(f"filter field '{field_name}'")

    # Validate and correct sort field name
    corrected_sort = None
    if sort:
        # Parse sort string: "field_name asc" or "field_name desc"
        parts = sort.strip().split()
        if len(parts) >= 2:
            field_name = parts[0]
            direction = " ".join(parts[1:])  # Preserve "asc" or "desc"
            if field_name in valid_fields:
                corrected_sort = f"{field_name} {direction}"
            else:
                match = _fuzzy_match_field(field_name, valid_fields)
                if match:
                    corrected_sort = f"{match} {direction}"
                    corrections[field_name] = match
                else:
                    corrected_sort = sort  # Keep for error reporting
                    errors.append(f"sort field '{field_name}'")
        else:
            corrected_sort = sort

    # Validate and correct fields list
    corrected_fields = None
    if fields:
        corrected_fields_list, invalid_fields, field_corrections = validate_and_correct_field_names(
            fields, valid_fields, "fields"
        )
        corrected_fields = corrected_fields_list
        corrections.update(field_corrections)
        errors.extend([f"field '{f}'" for f in invalid_fields])

    return corrected_filters, corrected_sort, corrected_fields, corrections, errors, filter_errors

