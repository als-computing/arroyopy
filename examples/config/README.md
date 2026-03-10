# Arroyo Configuration Examples

This directory contains example YAML configuration files for arroyo units.

## Files

### simple_pipeline.yaml
A basic configuration showing a single unit with:
- One operator
- One ZMQ listener
- One ZMQ publisher

**Usage:**
```bash
arroyo run simple_pipeline.yaml
```

### multi_block.yaml
Demonstrates multiple blocks in a single configuration file:
- `data_ingestion`: Reads from ZMQ, writes to Redis
- `data_processing`: Reads from Redis, writes to ZMQ
- `monitoring`: Monitors the pipeline

**Usage:**
```bash
# Run all blocks
arroyo multi_block.yaml

# Run specific block
arroyo multi_block.yaml --block data_ingestion
```

### file_watcher.yaml
Shows file system watching integration:
- Watches a directory for new files
- Publishes file events to Redis

**Usage:**
```bash
arroyo run file_watcher.yaml
```

### dev_pipeline.yaml
Simple development/testing configuration with:
- Minimal dependencies
- Multiple publishers for debugging (stdout + file)

**Usage:**
```bash
arroyo run dev_pipeline.yaml
```

## Configuration Structure

All configurations follow this structure:

```yaml
name: unique_unit_name
description: Optional description

operator:
  class: path.to.OperatorClass
  kwargs:
    arg1: value1
    arg2: value2

listeners:
  - class: path.to.ListenerClass
    kwargs:
      key: value

publishers:
  - class: path.to.PublisherClass
    kwargs:
      key: value
```

## Creating Your Own Configuration

1. **Copy a template:**
   ```bash
   cp examples/config/simple_pipeline.yaml my_pipeline.yaml
   ```

2. **Customize the operator:**
   ```yaml
   operator:
     class: myapp.operators.MyOperator
     kwargs:
       my_setting: value
   ```

3. **Add listeners:**
   ```yaml
   listeners:
     - class: arroyopy.zmq.ZMQListener
       kwargs:
         address: 'tcp://localhost:5555'
   ```

4. **Add publishers:**
   ```yaml
   publishers:
     - class: arroyopy.redis.RedisPublisher
       kwargs:
         channel: output
   ```

5. **Validate:**
   ```bash
   arroyo validate my_pipeline.yaml
   ```

6. **Run:**
   ```bash
   arroyo run my_pipeline.yaml
   ```

## Available Components

### Built-in Listeners
- `arroyopy.zmq.ZMQListener` - Listen to ZMQ sockets
- `arroyopy.redis.RedisListener` - Listen to Redis pub/sub
- `arroyopy.files.FileWatcherListener` - Watch file system

### Built-in Publishers
- `arroyopy.redis.RedisPublisher` - Publish to Redis

### Creating Custom Components

See [../../docs/configuration.md](../../docs/configuration.md) for details on creating custom operators, listeners, and publishers.

## Tips

- **Use environment-specific configs:** Create separate configs for dev, staging, production
- **Validate before deploying:** Always run `arroyo validate` before deployment
- **Version control:** Keep configs in git alongside your code
- **Document settings:** Add comments to explain configuration choices

## Troubleshooting

**"Cannot import class" error:**
- Ensure your Python package is installed
- Check the full module path is correct
- Verify the class name matches exactly

**"Missing required field" error:**
- Ensure you have both `name` and `operator` fields
- Check YAML syntax is valid

**Unit won't start:**
- Check that all dependencies (ZMQ, Redis, etc.) are running
- Verify addresses and ports are correct
- Use `--verbose` flag for detailed logging
