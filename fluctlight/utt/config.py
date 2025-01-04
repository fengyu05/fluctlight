import os
from typing import Any, Optional, Callable


def config_default(
    key: str,
    default_value: Optional[Any] = None,
    accept_values: Optional[list[Any]] = None,
    validator: Optional[Callable] = None,
) -> Any:
    value = os.environ.get(key, default_value)
    if accept_values:
        if value not in accept_values:
            raise ValueError(f"Invalid value for {key}: {value}")
    if validator:
        if not validator(value):
            raise ValueError(f"Invalid value for {key}: {value}")
    return value


def config_default_float(
    key: str, default_value: Any = 0.0, validator: Optional[Callable] = None
) -> float:
    return float(config_default(key, default_value=default_value, validator=validator))


def config_default_int(
    key: str, default_value: Any = 0, validator: Optional[Callable] = None
) -> int:
    return int(config_default(key, default_value=default_value, validator=validator))


_TRUTHY_VALUES = {"true", "1", "yes", "t", "y"}


def config_default_bool(key: str, default_value: bool = False) -> bool:
    return str(os.environ.get(key, default_value)).lower() in _TRUTHY_VALUES
