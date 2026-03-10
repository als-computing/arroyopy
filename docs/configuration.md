# Configuration-Based Units

This guide explains how to use arroyo's configuration system to define and run stream processing pipelines using YAML files.

## Overview

Arroyo's configuration system allows you to:
- Define processing blocks (operator + listeners + publishers) in YAML files
- Instantiate components with arguments and keyword arguments
- Run pipelines from the command line without writing Python code
- Manage multiple blocks in a single configuration file

## Core Concepts

### Block

A **Block** is a container that holds:
- **One Operator**: Processes messages
- **Any number of Listeners**: Sources that feed messages to the operator
- **Any number of Publishers**: Sinks that receive processed messages

### Configuration Structure

All YAML configurations must have a `blocks` key containing a list of block definitions.

A minimal configuration with one block:

```yaml
blocks:
  - name: my_pipeline
    operator:
      class: myapp.operators.MyOperator
      kwargs:
        timeout: 30
```

A complete configuration with listeners and publishers:

```yaml
blocks:
  - name: my_pipeline
    description: Process messages from ZMQ and publish to Redis

    operator:
      class: myapp.operators.MessageProcessor
      kwargs:
        batch_size: 100
        timeout: 30

    listeners:
      - class: arroyopy.zmq.ZMQListener
        kwargs:
          address: 'tcp://127.0.0.1:5555'
          socket_type: 'SUB'

    publishers:
      - class: arroyopy.redis.RedisPublisher
        kwargs:
          host: localhost
          port: 6379
          channel: processed_data
```

## Configuration Fields

### Top-Level Required Fields

- **`blocks`**: List of block definitions (required)

### Block Required Fields

- **`name`**: Unique identifier for the block
- **`operator`**: Operator configuration
  - **`class`**: Full Python path to operator class (e.g., `myapp.operators.MyOperator`)
  - **`args`** (optional): List of positional arguments
  - **`kwargs`** (optional): Dictionary of keyword arguments

### Block Optional Fields

- **`description`**: Human-readable description of the block
- **`listeners`**: List of listener configurations
- **`publishers`**: List of publisher configurations

### Component Structure

Each listener and publisher has the same structure:

```yaml
class: path.to.Class
args:  # optional list
  - arg1
  - arg2
kwargs:  # optional dictionary
  key1: value1
  key2: value2
```

## Multiple Units

You can define multiple blocks in a single file:

```yaml
blocks:
  - name: ingestion
    operator:
      class: myapp.operators.Ingestor
    listeners:
      - class: arroyopy.zmq.ZMQListener
        kwargs:
          address: 'tcp://127.0.0.1:5555'
    publishers:
      - class: arroyopy.redis.RedisPublisher
        kwargs:
          channel: raw_data

  - name: processing
    operator:
      class: myapp.operators.Processor
    listeners:
      - class: arroyopy.redis.RedisListener
        kwargs:
          channels: [raw_data]
    publishers:
      - class: arroyopy.zmq.ZMQPublisher
        kwargs:
          address: 'tcp://127.0.0.1:5556'
```

## Using the CLI

### Install

After installing arroyopy, the `arroyo` command is available:

```bash
pip install arroyopy
```

### Run a Block

```bash
# Run a single unit
arroyo run config/pipeline.yaml

# Run a specific block from multi-unit config
arroyo run config/multi.yaml --block processing

# Run with verbose logging
arroyo run config/pipeline.yaml --verbose
```

### Validate Configuration

```bash
# Validate without running
arroyo validate config/pipeline.yaml
```

### List Units

```bash
# List all blocks in a config file
arroyo list-blocks config/multi.yaml
```

## Using in Python Code

You can also load and run blocks programmatically:

```python
import asyncio
from arroyopy import load_block_from_yaml, load_blocks_from_yaml

# Load a single unit
async def main():
    block = load_block_from_yaml('config/pipeline.yaml')
    await block.start()

asyncio.run(main())
```

```python
# Load specific block from multi-unit config
block = load_block_from_yaml('config/multi.yaml', block_name='processing')
await block.start()
```

```python
# Load all blocks
blocks = load_blocks_from_yaml('config/multi.yaml')
for block in blocks:
    print(f"Found unit: {block.name}")
    await block.start()
```

## Example Configurations

### Simple ZMQ Pipeline

```yaml
blocks:
  - name: zmq_simple
    description: Simple ZMQ message processing

    operator:
      class: myapp.operators.EchoOperator

    listeners:
      - class: arroyopy.zmq.ZMQListener
        kwargs:
          address: 'tcp://127.0.0.1:5555'

    publishers:
      - class: arroyopy.zmq.ZMQPublisher
        kwargs:
          address: 'tcp://127.0.0.1:5556'
```

### File Watcher to Redis

```yaml
blocks:
  - name: file_watcher
    description: Watch directory and publish to Redis

    operator:
      class: arroyopy.app.redis_file_watcher.FileWatcherOperator

    listeners:
      - class: arroyopy.files.FileWatcherListener
        kwargs:
          watch_path: /data/incoming
          patterns: ['*.h5', '*.tif']

    publishers:
      - class: arroyopy.redis.RedisPublisher
        kwargs:
          host: localhost
          channel: new_files
```

### Development/Testing

```yaml
blocks:
  - name: dev_pipeline
    description: Development pipeline with stdout output

    operator:
      class: myapp.operators.DebugOperator

    listeners:
      - class: arroyopy.zmq.ZMQListener
        kwargs:
          address: 'tcp://127.0.0.1:5555'

    publishers:
      # Multiple publishers for debugging
      - class: myapp.publishers.StdoutPublisher
        kwargs:
          pretty_print: true
      - class: myapp.publishers.FilePublisher
        kwargs:
          output_path: /tmp/debug.jsonl
```

## Best Practices

### 1. Organize Configs by Environment

```
config/
  dev/
    pipeline.yaml
  staging/
    pipeline.yaml
  production/
    pipeline.yaml
```

### 2. Use Environment Variables

While YAML doesn't directly support environment variables, you can:
- Use templating tools (e.g., envsubst, jinja2)
- Load config and override values in Python

```python
import os
from arroyopy import load_block_from_yaml

block = load_block_from_yaml('config/pipeline.yaml')
# Override from environment
block.operator.timeout = int(os.getenv('TIMEOUT', 30))
```

### 3. Validate Configurations

Always validate configurations before deployment:

```bash
arroyo validate config/production/pipeline.yaml
```

### 4. Version Control

Keep configuration files in version control alongside your code.

### 5. Document Custom Components

Add docstrings to your operators, listeners, and publishers explaining their configuration options:

```python
class MyOperator(Operator):
    """
    Process messages with custom logic.

    Configuration:
        timeout (int): Processing timeout in seconds
        batch_size (int): Number of messages to batch
        algorithm (str): Processing algorithm to use
    """
    def __init__(self, timeout=30, batch_size=100, algorithm='standard'):
        self.timeout = timeout
        self.batch_size = batch_size
        self.algorithm = algorithm
```

## Error Handling

### Common Errors

**ConfigurationError: Cannot import class**
```
Failed to import class 'myapp.operators.MyOperator'
```
Solution: Ensure the module path is correct and the package is installed.

**ConfigurationError: Missing required field**
```
Block configuration must have a 'name' field
```
Solution: Add all required fields to your configuration.

**Type Errors**
```
Operator must be an instance of Operator, got <class 'dict'>
```
Solution: Verify your class inherits from the correct base class.

## Advanced Usage

### Dynamic Configuration

Load configuration from multiple sources:

```python
from arroyopy.config import load_block_from_config
import yaml

# Load base config
with open('config/base.yaml') as f:
    config = yaml.safe_load(f)

# Merge with environment-specific overrides
with open(f'config/{env}.yaml') as f:
    overrides = yaml.safe_load(f)
    config.update(overrides)

block = load_block_from_config(config)
```

### Custom Component Discovery

Register custom component locations:

```python
# In your application setup
import sys
sys.path.append('/path/to/custom/components')

# Now can reference in config
# class: custom_components.MyOperator
```

### Programmatic Configuration

Build configuration in code:

```python
from arroyopy import Block
from myapp.operators import MyOperator
from arroyopy.zmq import ZMQListener

operator = MyOperator(timeout=30)
listener = ZMQListener(operator, 'tcp://127.0.0.1:5555')

block = Block(
    name='programmatic',
    operator=operator,
    listeners=[listener]
)

await block.start()
```

## See Also

- [Block API Reference](api/block.md)
- [Configuration API Reference](api/config.md)
- [Example Configurations](../examples/config/)
