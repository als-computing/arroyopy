"""
Configuration loader for arroyo units.

This module provides functionality to load and instantiate arroyo units
from YAML configuration files, enabling declarative pipeline definitions.
"""
import importlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml

from .listener import Listener
from .operator import Operator
from .publisher import Publisher
from .unit import Unit

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when there's an error in the configuration."""

    pass


def _import_class(class_path: str) -> Type:
    """
    Dynamically import a class from a module path.

    Parameters
    ----------
    class_path : str
        Full path to class, e.g., 'arroyopy.zmq.ZMQListener'

    Returns
    -------
    Type
        The imported class

    Raises
    ------
    ConfigurationError
        If the class cannot be imported

    Example
    -------
    >>> cls = _import_class('arroyopy.zmq.ZMQListener')
    """
    try:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ValueError, ImportError, AttributeError) as e:
        raise ConfigurationError(f"Failed to import class '{class_path}': {e}")


def _instantiate_component(config: Dict[str, Any]) -> Any:
    """
    Instantiate a component (listener, operator, or publisher) from config.

    Parameters
    ----------
    config : dict
        Configuration dictionary with 'class', 'args', and/or 'kwargs' keys

    Returns
    -------
    Any
        Instantiated component

    Raises
    ------
    ConfigurationError
        If configuration is invalid or instantiation fails
    """
    if "class" not in config:
        raise ConfigurationError("Component configuration must have a 'class' field")

    class_path = config["class"]
    args = config.get("args", [])
    kwargs = config.get("kwargs", {})

    try:
        cls = _import_class(class_path)
        return cls(*args, **kwargs)
    except Exception as e:
        raise ConfigurationError(f"Failed to instantiate {class_path}: {e}")


def load_unit_from_config(config: Dict[str, Any]) -> Unit:
    """
    Load a Unit from a configuration dictionary.

    Parameters
    ----------
    config : dict
        Configuration dictionary defining the unit

    Returns
    -------
    Unit
        Instantiated Unit with all components configured

    Raises
    ------
    ConfigurationError
        If configuration is invalid

    Example
    -------
    >>> config = {
    ...     'name': 'my_pipeline',
    ...     'operator': {
    ...         'class': 'myapp.operators.MyOperator',
    ...         'kwargs': {'timeout': 30}
    ...     },
    ...     'listeners': [
    ...         {'class': 'arroyopy.zmq.ZMQListener',
    ...          'args': ['tcp://127.0.0.1:5555']}
    ...     ],
    ...     'publishers': [
    ...         {'class': 'arroyopy.redis.RedisPublisher',
    ...          'kwargs': {'host': 'localhost'}}
    ...     ]
    ... }
    >>> unit = load_unit_from_config(config)
    """
    if "name" not in config:
        raise ConfigurationError("Unit configuration must have a 'name' field")

    if "operator" not in config:
        raise ConfigurationError("Unit configuration must have an 'operator' field")

    name = config["name"]

    logger.info(f"Loading unit '{name}' from configuration")

    # Instantiate operator
    operator = _instantiate_component(config["operator"])
    if not isinstance(operator, Operator):
        raise ConfigurationError(
            f"Operator must be an instance of Operator, got {type(operator)}"
        )

    # Instantiate listeners
    listeners = []
    for i, listener_config in enumerate(config.get("listeners", [])):
        try:
            # For listeners, we need to pass the operator
            # Check if operator is in kwargs, if not add it
            if "kwargs" not in listener_config:
                listener_config["kwargs"] = {}
            if "operator" not in listener_config["kwargs"]:
                listener_config["kwargs"]["operator"] = operator

            listener = _instantiate_component(listener_config)
            if not isinstance(listener, Listener):
                raise ConfigurationError(
                    f"Listener must be an instance of Listener, got {type(listener)}"
                )
            listeners.append(listener)
        except Exception as e:
            raise ConfigurationError(f"Failed to load listener {i}: {e}")

    # Instantiate publishers
    publishers = []
    for i, publisher_config in enumerate(config.get("publishers", [])):
        try:
            publisher = _instantiate_component(publisher_config)
            if not isinstance(publisher, Publisher):
                raise ConfigurationError(
                    f"Publisher must be an instance of Publisher, got {type(publisher)}"
                )
            publishers.append(publisher)
        except Exception as e:
            raise ConfigurationError(f"Failed to load publisher {i}: {e}")

    # Create the unit
    unit = Unit(
        name=name, operator=operator, listeners=listeners, publishers=publishers
    )

    logger.info(f"Successfully loaded unit '{name}'")
    return unit


def load_units_from_yaml(yaml_path: str) -> List[Unit]:
    """
    Load one or more units from a YAML file.

    The YAML file can contain either a single unit configuration or
    a list of unit configurations under a 'units' key.

    Parameters
    ----------
    yaml_path : str
        Path to YAML configuration file

    Returns
    -------
    List[Unit]
        List of instantiated units

    Raises
    ------
    ConfigurationError
        If file cannot be read or configuration is invalid

    Example
    -------
    >>> units = load_units_from_yaml('config/pipeline.yaml')
    >>> for unit in units:
    ...     await unit.start()
    """
    path = Path(yaml_path)

    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {yaml_path}")

    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse YAML file: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to read configuration file: {e}")

    if data is None:
        raise ConfigurationError("Configuration file is empty")

    # Check if we have a single unit or multiple units
    if "units" in data:
        # Multiple units
        unit_configs = data["units"]
        if not isinstance(unit_configs, list):
            raise ConfigurationError("'units' must be a list")
    elif "name" in data and "operator" in data:
        # Single unit
        unit_configs = [data]
    else:
        raise ConfigurationError(
            "Configuration must contain either a 'units' list or a single unit definition"
        )

    units = []
    for i, unit_config in enumerate(unit_configs):
        try:
            unit = load_unit_from_config(unit_config)
            units.append(unit)
        except Exception as e:
            raise ConfigurationError(f"Failed to load unit {i}: {e}")

    logger.info(f"Loaded {len(units)} unit(s) from {yaml_path}")
    return units


def load_unit_from_yaml(yaml_path: str, unit_name: Optional[str] = None) -> Unit:
    """
    Load a single unit from a YAML file.

    Parameters
    ----------
    yaml_path : str
        Path to YAML configuration file
    unit_name : str, optional
        Name of specific unit to load (if file contains multiple units)

    Returns
    -------
    Unit
        The loaded unit

    Raises
    ------
    ConfigurationError
        If file cannot be read, unit not found, or configuration is invalid

    Example
    -------
    >>> unit = load_unit_from_yaml('config/pipeline.yaml', 'zmq_processor')
    >>> await unit.start()
    """
    units = load_units_from_yaml(yaml_path)

    if unit_name is None:
        if len(units) == 1:
            return units[0]
        else:
            raise ConfigurationError(
                f"File contains {len(units)} units. Specify unit_name to select one."
            )

    # Find unit by name
    for unit in units:
        if unit.name == unit_name:
            return unit

    raise ConfigurationError(
        f"Unit '{unit_name}' not found in configuration. "
        f"Available units: {[u.name for u in units]}"
    )
