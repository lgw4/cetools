"""Serialization and deserialization utilities for CETools data models."""

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Sequence, Type, TypeVar, Union

from pydantic import BaseModel

from .config import CONFIG_DIR
from .models import NPC, Character, Equipment, Party

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


class SerializationError(Exception):
    """Exception raised when serialization/deserialization fails."""

    pass


def to_json(obj: BaseModel, indent: int = 2) -> str:
    """
    Serialize a Pydantic model to JSON string.

    Args:
        obj: The Pydantic model instance to serialize
        indent: Number of spaces for indentation (default: 2)

    Returns:
        JSON string representation

    Raises:
        SerializationError: If serialization fails
    """
    try:
        return obj.model_dump_json(indent=indent, exclude_unset=True)
    except Exception as ex:
        raise SerializationError(f"Failed to serialize to JSON: {ex}") from ex


def from_json(json_str: str, model_class: Type[T]) -> T:
    """
    Deserialize a JSON string to a Pydantic model.

    Args:
        json_str: JSON string to deserialize
        model_class: The Pydantic model class to deserialize to

    Returns:
        Instance of the specified model class

    Raises:
        SerializationError: If deserialization fails
    """
    try:
        data = json.loads(json_str)
        return model_class.model_validate(data)
    except Exception as ex:
        raise SerializationError(f"Failed to deserialize from JSON: {ex}") from ex


def to_csv(objects: Sequence[BaseModel], include_headers: bool = True) -> str:
    """
    Serialize a list of Pydantic models to CSV string.

    Args:
        objects: Sequence of Pydantic model instances to serialize
        include_headers: Whether to include column headers

    Returns:
        CSV string representation

    Raises:
        SerializationError: If serialization fails
    """
    if not objects:
        return ""

    try:
        output = StringIO()

        # Get field names from the first object
        first_obj = objects[0]
        data_list = [obj.model_dump(exclude_unset=True) for obj in objects]

        # Flatten nested objects for CSV compatibility
        flattened_data = []
        for data in data_list:
            flattened = _flatten_dict(data)
            flattened_data.append(flattened)

        if not flattened_data:
            return ""

        # Get all possible field names
        all_fields = set()
        for data in flattened_data:
            all_fields.update(data.keys())

        fieldnames = sorted(list(all_fields))

        writer = csv.DictWriter(output, fieldnames=fieldnames)

        if include_headers:
            writer.writeheader()

        for data in flattened_data:
            # Ensure all fields are present
            row = {field: data.get(field, "") for field in fieldnames}
            writer.writerow(row)

        return output.getvalue()

    except Exception as ex:
        raise SerializationError(f"Failed to serialize to CSV: {ex}") from ex


def _flatten_dict(data: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """
    Flatten a nested dictionary for CSV export.

    Args:
        data: Dictionary to flatten
        parent_key: Parent key for nested structures
        sep: Separator for nested keys

    Returns:
        Flattened dictionary
    """
    items = []

    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            items.extend(_flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            # Convert lists to comma-separated strings
            if value and isinstance(value[0], dict):
                # For lists of objects, create indexed fields
                for idx, item in enumerate(value):
                    if isinstance(item, dict):
                        items.extend(_flatten_dict(item, f"{new_key}_{idx}", sep=sep).items())
                    else:
                        items.append((f"{new_key}_{idx}", str(item)))
            else:
                # For simple lists, join with commas
                items.append((new_key, ", ".join(str(item) for item in value)))
        else:
            items.append((new_key, value))

    return dict(items)


def _unflatten_dict(data: Dict[str, Any], sep: str = "_") -> Dict[str, Any]:
    """
    Convert a flattened dictionary (as produced by _flatten_dict) back into
    a nested dictionary suitable for Pydantic model construction.

    This supports indexed list fields like `equipment_0_name` which will be
    converted back into `equipment: [{"name": ...}]`.
    """
    result: Dict[str, Any] = {}

    for flat_key, value in data.items():
        parts = flat_key.split(sep)
        target = result

        for i, part in enumerate(parts):
            # If this is a numeric index, treat parent as a list
            if part.isdigit():
                idx = int(part)
                # previous key must have created a list
                # find the list in target (the previous key)
                # We skip handling bare numeric-leading keys as our flattener always
                # prefixes indices with a named key (e.g., equipment_0_name)
                continue

            # Look ahead to see if next part is an index
            next_is_index = (i + 1 < len(parts)) and parts[i + 1].isdigit()

            if next_is_index:
                # Ensure list exists for this key
                if part not in target or not isinstance(target[part], list):
                    target[part] = []

                # Ensure the list is large enough
                idx = int(parts[i + 1])
                while len(target[part]) <= idx:
                    target[part].append({})

                # Move target into the indexed dict
                target = target[part][idx]
                # Skip the index part on next loop iteration
                continue

            # Last part -> assign value
            if i == len(parts) - 1:
                # If value looks like a number, leave as-is; Pydantic will coerce
                target[part] = value
            else:
                # Ensure nested dict exists
                if part not in target or not isinstance(target[part], dict):
                    target[part] = {}
                target = target[part]

    return result


def save_to_file(
    obj: Union[BaseModel, Sequence[BaseModel]],
    file_path: Union[str, Path],
    format_type: str = "auto",
) -> None:
    """
    Save a Pydantic model or sequence of models to a file.

    Args:
        obj: The object(s) to save
        file_path: Path to save the file to
        format_type: Format to save in ('json', 'csv', or 'auto')

    Raises:
        SerializationError: If saving fails
        ValueError: If format_type is invalid
    """
    path = Path(file_path)

    # Auto-detect format from file extension
    if format_type == "auto":
        suffix = path.suffix.lower()
        if suffix == ".json":
            format_type = "json"
        elif suffix == ".csv":
            format_type = "csv"
        else:
            raise ValueError(f"Cannot auto-detect format for file: {path}")

    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        if format_type == "json":
            if isinstance(obj, BaseModel):
                content = to_json(obj)
            else:
                # For sequences, create a JSON array
                content = json.dumps(
                    [item.model_dump(exclude_unset=True) for item in obj], indent=2
                )
        elif format_type == "csv":
            if isinstance(obj, BaseModel):
                content = to_csv([obj])
            else:
                content = to_csv(obj)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

    except Exception as ex:
        raise SerializationError(f"Failed to save to file {path}: {ex}") from ex


def load_from_file(
    file_path: Union[str, Path], model_class: Type[T], format_type: str = "auto"
) -> Union[T, List[T]]:
    """
    Load a Pydantic model or list of models from a file.

    Args:
        file_path: Path to load the file from
        model_class: The Pydantic model class to deserialize to
        format_type: Format to load from ('json' or 'auto')

    Returns:
        Instance or list of instances of the specified model class

    Raises:
        SerializationError: If loading fails
        ValueError: If format_type is invalid
        FileNotFoundError: If the file doesn't exist
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Auto-detect format from file extension
    if format_type == "auto":
        suffix = path.suffix.lower()
        if suffix == ".json":
            format_type = "json"
        elif suffix == ".csv":
            format_type = "csv"
        else:
            raise ValueError(f"Cannot auto-detect format for file: {path}")

    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

        if format_type == "json":
            data = json.loads(content)
            if isinstance(data, list):
                return [model_class.model_validate(item) for item in data]
            else:
                return model_class.model_validate(data)
        elif format_type == "csv":
            # Parse CSV and reconstruct nested structures
            reader = csv.DictReader(StringIO(content))
            rows = list(reader)
            if not rows:
                raise SerializationError(f"CSV file {path} is empty")

            # If multiple rows, treat as list of objects
            objects: List[T] = []
            for row in rows:
                # Convert empty strings to None where appropriate
                cleaned = {k: (v if v != "" else None) for k, v in row.items()}
                nested = _unflatten_dict(cleaned)
                objects.append(model_class.model_validate(nested))

            if len(objects) == 1:
                return objects[0]
            return objects
        else:
            raise ValueError(f"Unsupported format for loading: {format_type}")

    except Exception as ex:
        raise SerializationError(f"Failed to load from file {path}: {ex}") from ex


# Convenience functions for specific model types
def save_character(
    character: Character, file_path: Union[str, Path], format_type: str = "auto"
) -> None:
    """Save a character to a file."""
    save_to_file(character, file_path, format_type)


def load_character(file_path: Union[str, Path], format_type: str = "auto") -> Character:
    """Load a character from a file."""
    result = load_from_file(file_path, Character, format_type)
    if isinstance(result, list):
        if len(result) != 1:
            raise SerializationError(f"Expected single character, found {len(result)}")
        return result[0]
    return result


def save_npc(npc: NPC, file_path: Union[str, Path], format_type: str = "auto") -> None:
    """Save an NPC to a file."""
    save_to_file(npc, file_path, format_type)


def load_npc(file_path: Union[str, Path], format_type: str = "auto") -> NPC:
    """Load an NPC from a file."""
    result = load_from_file(file_path, NPC, format_type)
    if isinstance(result, list):
        if len(result) != 1:
            raise SerializationError(f"Expected single NPC, found {len(result)}")
        return result[0]
    return result


def save_party(party: Party, file_path: Union[str, Path], format_type: str = "auto") -> None:
    """Save a party to a file."""
    save_to_file(party, file_path, format_type)


def load_party(file_path: Union[str, Path], format_type: str = "auto") -> Party:
    """Load a party from a file."""
    result = load_from_file(file_path, Party, format_type)
    if isinstance(result, list):
        if len(result) != 1:
            raise SerializationError(f"Expected single party, found {len(result)}")
        return result[0]
    return result


# This file contains GitHub Copilot generated content.
