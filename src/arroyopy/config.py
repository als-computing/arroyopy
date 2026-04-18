"""
Configuration loader for arroyo blocks.

This module provides functionality to load and instantiate arroyo blocks
from YAML configuration files, enabling declarative pipeline definitions.
"""
import importlib
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml

from .block import Block
from .listener import Listener
from .operator import Operator
from .publisher import Publisher

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when there's an error in the configuration."""

    pass


def _expand_env_var(value: str) -> str:
    """
    Expand environment variables in a string.

    Supports the following formats:
    - ${VAR_NAME} - Replace with environment variable value
    - ${VAR_NAME:-default_value} - Replace with env var, or default if not set
    - $VAR_NAME - Simple variable expansion

    Parameters
    ----------
    value : str
        String potentially containing environment variable references

    Returns
    -------
    str
        String with environment variables expanded

    Example
    -------
    >>> os.environ['MY_VAR'] = 'test'
    >>> _expand_env_var('${MY_VAR}')
    'test'
    >>> _expand_env_var('${MISSING:-default}')
    'default'
    """

    # Pattern for ${VAR_NAME:-default} or ${VAR_NAME}
    def replace_with_default(match):
        var_expr = match.group(1)
        if ":-" in var_expr:
            var_name, default_value = var_expr.split(":-", 1)
            return os.environ.get(var_name, default_value)
        else:
            var_name = var_expr
            env_value = os.environ.get(var_name)
            if env_value is None:
                raise ConfigurationError(
                    f"Environment variable '{var_name}' is not set and no default provided"
                )
            return env_value

    # Replace ${VAR} and ${VAR:-default}
    value = re.sub(r"\$\{([^}]+)\}", replace_with_default, value)

    # Replace simple $VAR (word boundaries to avoid partial matches)
    def replace_simple(match):
        var_name = match.group(1)
        env_value = os.environ.get(var_name)
        if env_value is None:
            raise ConfigurationError(
                f"Environment variable '{var_name}' is not set and no default provided"
            )
        return env_value

    value = re.sub(r"\$(\w+)", replace_simple, value)

    return value


def _expand_env_vars_in_config(config: Any) -> Any:
    """
    Recursively expand environment variables in configuration values.

    Processes dictionaries, lists, and strings to replace environment variable
    references with their actual values.

    Parameters
    ----------
    config : Any
        Configuration value (dict, list, str, or other type)

    Returns
    -------
    Any
        Configuration with environment variables expanded

    Example
    -------
    >>> os.environ['PORT'] = '5555'
    >>> config = {'address': 'tcp://127.0.0.1:${PORT}'}
    >>> _expand_env_vars_in_config(config)
    {'address': 'tcp://127.0.0.1:5555'}
    """
    if isinstance(config, dict):
        return {key: _expand_env_vars_in_config(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [_expand_env_vars_in_config(item) for item in config]
    elif isinstance(config, str):
        return _expand_env_var(config)
    else:
        # Return other types (int, bool, etc.) unchanged
        return config


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


def load_block_from_config(config: Dict[str, Any]) -> Block:
    """
    Load a Block from a configuration dictionary.

    Parameters
    ----------
    config : dict
        Configuration dictionary defining the unit

    Returns
    -------
    Block
        Instantiated Block with all components configured

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
    >>> block = load_block_from_config(config)
    """
    if "name" not in config:
        raise ConfigurationError("Block configuration must have a 'name' field")

    if "operator" not in config:
        raise ConfigurationError("Block configuration must have an 'operator' field")

    name = config["name"]

    logger.info(f"Loading block '{name}' from configuration")

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
    block = Block(
        name=name, operator=operator, listeners=listeners, publishers=publishers
    )

    logger.info(f"Successfully loaded block '{name}'")
    return block


def load_blocks_from_yaml(yaml_path: str) -> List[Block]:
    """
    Load one or more blocks from a YAML file.

    The YAML file must contain a 'blocks' key with a list of block configurations.

    Parameters
    ----------
    yaml_path : str
        Path to YAML configuration file

    Returns
    -------
    List[Block]
        List of instantiated blocks

    Raises
    ------
    ConfigurationError
        If file cannot be read or configuration is invalid

    Example
    -------
    >>> blocks = load_blocks_from_yaml('config/pipeline.yaml')
    >>> for block in blocks:
    ...     await block.start()
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

    # Expand environment variables in the loaded data
    data = _expand_env_vars_in_config(data)

    # Require 'blocks' key
    if "blocks" not in data:
        raise ConfigurationError(
            "Configuration must contain a 'blocks' key with a list of block definitions"
        )

    block_configs = data["blocks"]
    if not isinstance(block_configs, list):
        raise ConfigurationError("'blocks' must be a list")

    blocks = []
    for i, block_config in enumerate(block_configs):
        try:
            block = load_block_from_config(block_config)
            blocks.append(block)
        except Exception as e:
            raise ConfigurationError(f"Failed to load block {i}: {e}")

    logger.info(f"Loaded {len(blocks)} unit(s) from {yaml_path}")
    return blocks


def load_block_from_yaml(yaml_path: str, block_name: Optional[str] = None) -> Block:
    """
    Load a single block from a YAML file.

    Parameters
    ----------
    yaml_path : str
        Path to YAML configuration file
    block_name : str, optional
        Name of specific block to load (if file contains multiple blocks)

    Returns
    -------
    Block
        The loaded unit

    Raises
    ------
    ConfigurationError
        If file cannot be read, block not found, or configuration is invalid

    Example
    -------
    >>> block = load_block_from_yaml('config/pipeline.yaml', 'zmq_processor')
    >>> await block.start()
    """
    blocks = load_blocks_from_yaml(yaml_path)

    if block_name is None:
        if len(blocks) == 1:
            return blocks[0]
        else:
            raise ConfigurationError(
                f"File contains {len(blocks)} blocks. Specify block_name to select one."
            )

    # Find block by name
    for block in blocks:
        if block.name == block_name:
            return block

    raise ConfigurationError(
        f"Block '{block_name}' not found in configuration. "
        f"Available blocks: {[b.name for b in blocks]}"
    )
