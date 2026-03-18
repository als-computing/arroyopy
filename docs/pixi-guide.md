# Getting Started with Pixi

This guide will help you get started with developing arroyopy using Pixi.

## What is Pixi?

[Pixi](https://pixi.sh) is a fast, cross-platform package manager built on top of conda. It provides:

- **Fast**: Parallel dependency resolution and downloads
- **Reproducible**: Lock files ensure consistent environments across platforms
- **Cross-platform**: Works on Linux, macOS
- **Easy**: Simple commands for common tasks
- **Flexible**: Multiple environments for different purposes

## Installation

### macOS and Linux

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

### Homebrew

```bash
brew install pixi
```

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/als-computing/arroyopy.git
cd arroyopy

# 2. Install dependencies (creates .pixi directory)
pixi install

# 3. Install the package in editable mode
pixi run install-dev

# 4. Run tests to verify everything works
pixi run test
```

That's it! You now have a fully configured development environment.

## Common Commands

### Environment Management

```bash
# Install all dependencies
pixi install

# Update dependencies
pixi update

# Clean and reinstall
pixi clean
pixi install

# Show information about the project
pixi info
```

### Running Tasks

```bash
# Run tests
pixi run test

# Run tests with coverage
pixi run test-cov

# Format code with black
pixi run format

# Check if code is formatted
pixi run format-check

# Run linter
pixi run lint

# Run all pre-commit checks
pixi run pre-commit

# Install pre-commit hooks
pixi run pre-commit-install
```

### Working with Environments

Pixi supports multiple environments defined in `pixi.toml`:

```bash
# Use the dev environment (includes all optional dependencies)
pixi shell -e dev

# List all available environments
pixi project info

# Run a command in a specific environment
pixi run -e dev test

# Install additional environment
pixi install -e docs
```

**Available Environments:**

- `default`: Core dependencies only
- `dev`: Full development environment (recommended)
- `prod`: Production-like with optional features
- `minimal`: Minimal dependencies for testing
- `docs`: Documentation building

## Development Workflow

### 1. Start a New Feature

```bash
# Create a new branch
git checkout -b feature/my-feature

# Ensure environment is up to date
pixi install
```

### 2. Make Changes

Edit code in your favorite editor. Pixi doesn't interfere with your IDE.

### 3. Run Tests

```bash
# Run tests as you develop
pixi run test

# Or run tests in watch mode (if you add pytest-watch)
pixi run test-watch
```

### 4. Format and Lint

```bash
# Format code
pixi run format

# Check linting
pixi run lint
```

### 5. Run Pre-commit Checks

```bash
# Run all checks
pixi run pre-commit

# Or install hooks to run automatically on commit
pixi run pre-commit-install
```

### 6. Commit and Push

```bash
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
```

## Adding Dependencies

### Runtime Dependency

Add to `[dependencies]` in `pixi.toml`:

```toml
[dependencies]
new-package = "*"
```

Then run:

```bash
pixi install
```

### Development Dependency

Add to `[feature.dev.dependencies]` in `pixi.toml`:

```toml
[feature.dev.dependencies]
new-dev-tool = "*"
```

Then run:

```bash
pixi install -e dev
```

### Optional Feature Dependency

Add to a feature's dependencies:

```toml
[feature.zmq.dependencies]
pyzmq = "*"
```

## Adding Tasks

Tasks are defined in `pixi.toml` under `[tasks]`:

```toml
[tasks]
my-task = "python -m my_module"
complex-task = { cmd = "python script.py", env = { DEBUG = "1" } }
```

Run with:

```bash
pixi run my-task
```

## Troubleshooting

### Environment Issues

If you have issues with the environment:

```bash
# Clean and reinstall
pixi clean
pixi install

# Or remove the .pixi directory manually
rm -rf .pixi
pixi install
```

### Dependency Conflicts

If dependencies can't be resolved:

1. Check `pixi.toml` for version conflicts
2. Try updating with `pixi update`
3. Check if packages are available on conda-forge
4. Consider using pip for packages not in conda

### Using Pip Packages

Some packages may not be available in conda-forge. You can still use pip:

```bash
# Enter the pixi shell
pixi shell -e dev

# Install with pip
pip install package-not-in-conda
```

Or add a task:

```toml
[tasks]
install-pip-deps = "pip install package1 package2"
```

### IDE Integration

#### VS Code

VS Code should automatically detect the Python interpreter in `.pixi/envs/dev/bin/python`.

To manually select it:
1. Press `Cmd/Ctrl + Shift + P`
2. Type "Python: Select Interpreter"
3. Choose `.pixi/envs/dev/bin/python`

#### PyCharm

1. Go to Settings → Project → Python Interpreter
2. Click the gear icon → Add
3. Choose "Existing environment"
4. Navigate to `.pixi/envs/dev/bin/python`

## Performance Tips

1. **Use solve groups**: Already configured to speed up dependency resolution
2. **Pin Python version**: We pin to `>=3.11,<3.13` for consistency
3. **Use pixi global cache**: Dependencies are cached globally, saving disk space
4. **Parallel installation**: Pixi installs packages in parallel automatically

## CI/CD Integration

Pixi works great in CI/CD. See `.github/workflows/` for examples using Pixi in GitHub Actions.

Basic example:

```yaml
- uses: prefix-dev/setup-pixi@v0.4.1
- run: pixi run test
```

## Further Reading

- [Pixi Documentation](https://pixi.sh/latest/)
- [Pixi GitHub](https://github.com/prefix-dev/pixi)
- [Conda-forge packages](https://conda-forge.org/feedstock-outputs/)

## Getting Help

- **Pixi Issues**: [GitHub Issues](https://github.com/prefix-dev/pixi/issues)
- **Arroyopy Issues**: [GitHub Issues](https://github.com/als-computing/arroyopy/issues)
- **Pixi Discord**: [Join the community](https://discord.gg/kKV8ZxyzY4)
