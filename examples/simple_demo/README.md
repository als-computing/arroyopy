# Simple Arroyopy Demo

This is a complete, runnable example that demonstrates the basic concepts of Arroyopy.

## Overview

This demo shows a simple data pipeline:

```
Source → ZMQ → Listener → Operator → Publisher → ZMQ → Sink
         5555            (pipeline.yaml)         5556
```

- **Source** (`source.py`): Publishes test messages to ZMQ port 5555
- **Pipeline** (`pipeline.yaml`): Listens on 5555, processes messages, publishes to 5556
- **Sink** (`sink.py`): Subscribes to 5556 and prints messages to console

## Prerequisites

This demo requires arroyopy to be installed in your Python environment.

### Option 1: Using Pixi (Recommended)

**For trying out the demo:**

```bash
# Install pixi if you haven't already
curl -fsSL https://pixi.sh/install.sh | bash

# From the arroyopy root directory
pixi install
pixi shell
```

**For developing arroyopy:**

```bash
# Install with dev tools (testing, linting, etc.)
pixi install -e dev
pixi shell -e dev
```

This creates a complete Python environment with all dependencies installed.

### Option 2: Using pip

If you're just trying out arroyopy:

```bash
# From the arroyopy root directory
pip install -e .
```

This installs arroyopy in editable mode, making the `arroyo-run` command available.

### Verify Installation

Check that arroyopy is installed:

```bash
arroyo-run --help
```

You should see the available commands: `run`, `validate`, and `list-blocks`.

## Quick Start

You'll need **three terminal windows** to run this demo.

### Terminal 1: Start the Sink (Output Display)

```bash
cd examples/simple_demo
python sink.py
```

This will wait for messages and print them as they arrive.

### Terminal 2: Start the Pipeline

```bash
cd examples/simple_demo
arroyo-run run pipeline.yaml
```

The pipeline is now listening for incoming messages and ready to process them.

### Terminal 3: Start the Source (Data Generator)

```bash
cd examples/simple_demo
python source.py
```

This will send 10 test messages. Watch the output appear in Terminal 1!

## What's Happening?

1. **source.py** generates messages like "Message 1", "Message 2", etc.
2. The **pipeline** (running via `arroyo-run run`) receives each message
3. The **SimpleOperator** processes it, adding "PROCESSED #N: " prefix
4. The processed message is published to the output ZMQ socket
5. **sink.py** receives and displays: "PROCESSED #1: Message 1"

## Customization

### Run Continuously

Send infinite messages:
```bash
python source.py --count 0 --interval 0.5
```

### Change the Prefix

Edit `pipeline.yaml` and change the operator's `prefix` parameter, then restart the pipeline.

### Different Ports

All three components accept `--address` arguments:
```bash
python source.py --address tcp://127.0.0.1:6000
python sink.py --address tcp://127.0.0.1:6001
```

Update `pipeline.yaml` accordingly.

## Files

- **simple_operator.py**: Simple operator that adds a prefix to messages
- **zmq_components.py**: ZMQ listener and publisher wrappers for easy configuration
- **source.py**: ZMQ publisher that generates test data
- **sink.py**: ZMQ subscriber that displays output
- **pipeline.yaml**: Arroyo configuration connecting everything
- **README.md**: This file
- **quick_test.sh**: Automated test script for running the demo

## Next Steps

- Try modifying `SimpleOperator` to do different transformations
- Add multiple operators in sequence
- Experiment with different ZMQ socket types
- Add error handling and retry logic
