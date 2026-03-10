# Arroyo Stream Processing Toolset

Processing event or streaming data presents several technological challenges. A variety of technologies are often used by scientific user facilities. ZMQ is used to stream data and messages in a peer-to-peer fashion. Message brokers like Kafka, Redis and RabbitMQ are often employed to route and pass messages from instruments to processing workflows. Arroyo provides an API and structure to flexibly integrate with these tools and incorporate arbitrarily complex processing workflows, letting the hooks to the workflow code be independent of the connection code and hence reusable at a variety of instruments.

## Core Concepts

The basic structure of building an arroyo implementation is to implement groups of several classes:

- `Operator` - receives `Messages` from a listener and can optionally send `Messages` to one or more `Publisher` instances
- `Listener` - receives `Messages` from the external world, parse them into arroyo `Message` and sends them to an `Operator`
- `Publisher` - receives `Messages` from a `Listener` and publishes them to the outside world
- `Block` - a container that holds one operator with any number of listeners and publishers

## Configuration-Based Deployment

Arroyo supports declarative configuration via YAML files, making it easy to deploy and configure pipelines without writing code:

```yaml
blocks:
  - name: my_pipeline
    description: Process messages from ZMQ

    operator:
      class: myapp.operators.MessageProcessor
      kwargs:
        timeout: 30

    listeners:
      - class: arroyopy.zmq.ZMQListener
        kwargs:
          address: 'tcp://127.0.0.1:5555'

    publishers:
      - class: arroyopy.redis.RedisPublisher
        kwargs:
          channel: processed_data
```

Run from the command line:
```bash
arroyo run config/pipeline.yaml
```

See [docs/configuration.md](docs/configuration.md) for full details.

## Quick Start

### Installation

```bash
pip install arroyopy
```

With optional dependencies:
```bash
# Install with ZMQ support
pip install arroyopy[zmq]

# Install with Redis support
pip install arroyopy[redis]

# Install everything for development
pip install arroyopy[dev]
```

### Running a Pipeline

1. **Create a configuration file** (`pipeline.yaml`):

```yaml
blocks:
  - name: simple_pipeline
    description: Listen on ZMQ, process, publish to Redis

    operator:
      class: myapp.operators.SimpleProcessor

    listeners:
      - class: arroyopy.zmq.ZMQListener
        kwargs:
          address: 'tcp://127.0.0.1:5555'
          socket_type: 'SUB'

    publishers:
      - class: arroyopy.redis.RedisPublisher
        kwargs:
          host: localhost
          channel: output
```

2. **Run the pipeline**:

```bash
arroyo run pipeline.yaml
```

3. **Validate your configuration** (optional):

```bash
arroyo validate pipeline.yaml
```

### Multiple Blocks

You can define multiple blocks in a single configuration file:

```yaml
blocks:
  - name: data_ingestion
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

  - name: data_processing
    operator:
      class: myapp.operators.Processor
    listeners:
      - class: arroyopy.redis.RedisListener
        kwargs:
          channel: raw_data
    publishers:
      - class: arroyopy.zmq.ZMQPublisher
        kwargs:
          address: 'tcp://127.0.0.1:5556'
```

Run all blocks:
```bash
arroyo run config.yaml
```

Or run a specific block:
```bash
arroyo run config.yaml --block data_ingestion
```

## Deployment Options

Arroyo is un-opinionated about deployment decisions. It is intended to support listener-operator-publisher groups in:
- Single process
- Chain of processes where listening, processing and publishing can be linked together through a protocol like ZMQ. One process's publisher can communicate with another process's listener, etc.
- Configuration-based deployment via YAML files and CLI

This library is intended to provide base classes, and will also include more specific common subclasses, like those that communicate over ZMQ or Redis.

## Devloper Installation

## Developer Installation

### Option 1: Pixi (Recommended)

[Pixi](https://pixi.sh) provides reproducible environments across all platforms with automatic dependency resolution.

```bash
# Install Pixi
curl -fsSL https://pixi.sh/install.sh | bash

# Clone and navigate to the repository
git clone https://github.com/als-computing/arroyopy.git
cd arroyopy

# Install development environment
pixi install -e dev

# Run tests
pixi run -e dev test

# Run pre-commit checks
pixi run -e dev pre-commit
```

### Option 2: Conda/Mamba Environment

```bash
conda create -n arroyopy python=3.11
conda activate arroyopy
pip install -e '.[dev]'
```

### Option 3: Virtual Environment (venv)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Pre-commit

We use `pre-commit` for code quality checks. To test your changes:

```bash
pre-commit run --all-files
```

If `pre-commit` (including `black` formatter) makes changes:

```bash
git add .
pre-commit run --all-files
```

## Running Tests

With Pixi:
```bash
pixi run -e dev test
```

With pip/conda:
```bash
pytest src/_test/
```

# Copyright
Arroyo Stream Processing Toolset (arroyopy) Copyright (c) 2025, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Dept. of Energy).
All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Intellectual Property Office at
IPO@lbl.gov.

NOTICE.  This Software was developed under funding from the U.S. Department
of Energy and the U.S. Government consequently retains certain rights.  As
such, the U.S. Government has been granted for itself and others acting on
its behalf a paid-up, nonexclusive, irrevocable, worldwide license in the
Software to reproduce, distribute copies to the public, prepare derivative
works, and perform publicly and display publicly, and to permit others to do so.
