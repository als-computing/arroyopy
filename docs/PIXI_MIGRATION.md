# Pixi Migration Summary

This document summarizes the conversion of arroyopy to use Pixi for package and environment management.

## What Changed

### New Files

1. **`pixi.toml`** - Main Pixi configuration file with:
   - Project metadata
   - Dependencies organized by category
   - Multiple environment definitions
   - Task definitions for common operations
   - Cross-platform support (Linux, macOS)

2. **`docs/pixi-guide.md`** - Comprehensive guide for using Pixi with arroyopy

### Modified Files

1. **`pyproject.toml`**
   - Removed `[tool.pixi.*]` sections (moved to `pixi.toml`)
   - Kept Python packaging metadata (still needed for pip installs)

2. **`README.md`**
   - Added Pixi as the recommended development approach
   - Reorganized installation section with three options:
     - Option 1: Pixi (Recommended)
     - Option 2: Conda/Mamba
     - Option 3: Virtual Environment
   - Added common pixi commands
   - Improved development workflow documentation

3. **`.github/workflows/ci.yaml`**
   - Added `test-pixi` job that runs tests on Linux, macOS, using Pixi
   - Kept `test-pip` job for backward compatibility
   - Tests now run on multiple platforms

## Pixi Configuration Details

### Environments

| Environment | Purpose | Includes |
|------------|---------|----------|
| `default` | Core dependencies only | Runtime requirements |
| `dev` | **Full development** | All tools + optional features |
| `prod` | Production-like | Core + optional features |
| `minimal` | Testing minimal setup | Core only |
| `docs` | Documentation building | MkDocs and tools |

### Features

Features are modular dependency groups that can be combined:

- **`dev`**: Development tools (pytest, black, flake8, pre-commit)
- **`zmq`**: ZMQ support (pyzmq)
- **`redis`**: Redis support (redis-py)
- **`file-watch`**: File watching (watchfiles)
- **`docs`**: Documentation tools (mkdocs, mkdocs-material)

### Tasks

Common tasks defined in `pixi.toml`:

| Task | Command | Purpose |
|------|---------|---------|
| `install-dev` | `pixi run install-dev` | Install package in editable mode |
| `test` | `pixi run test` | Run test suite |
| `test-cov` | `pixi run test-cov` | Run tests with coverage |
| `lint` | `pixi run lint` | Run flake8 linter |
| `format` | `pixi run format` | Format code with black |
| `format-check` | `pixi run format-check` | Check code formatting |
| `pre-commit` | `pixi run pre-commit` | Run all pre-commit hooks |
| `build` | `pixi run build` | Build package |
| `clean` | `pixi run clean` | Remove build artifacts |

## Migration Benefits

### For Developers

1. **Faster Setup**: One command (`pixi install`) sets up everything
2. **Reproducible**: Lock file ensures everyone has identical environments
3. **Cross-Platform**: Works identically on Linux, macOS
4. **Task Runner**: Built-in task definitions for common operations
5. **Multiple Environments**: Easy switching between dev/prod/minimal setups

### For CI/CD

1. **Faster Builds**: Pixi caches dependencies efficiently
2. **Matrix Testing**: Easy to test on multiple platforms
3. **Consistency**: Same environment locally and in CI

### For Project Maintenance

1. **Clear Dependencies**: All deps in one file (`pixi.toml`)
2. **Version Pinning**: Lock file prevents unexpected updates
3. **Conda Ecosystem**: Access to conda-forge's extensive package repository

## How to Use

### For New Contributors

```bash
# 1. Install Pixi (one-time)
curl -fsSL https://pixi.sh/install.sh | bash

# 2. Clone and setup
git clone https://github.com/als-computing/arroyopy.git
cd arroyopy
pixi install
pixi run install-dev

# 3. Start developing
pixi run test
```

### For Existing Contributors

If you've been using conda/pip:

```bash
# 1. Install Pixi
curl -fsSL https://pixi.sh/install.sh | bash

# 2. In the arroyopy directory
pixi install
pixi run install-dev

# 3. Use pixi commands instead
pixi run test        # instead of: pytest
pixi run format      # instead of: black .
pixi run lint        # instead of: flake8 .
```

### For Pip Users

Pixi doesn't replace pip! You can still use pip:

```bash
# Standard pip install still works
pip install arroyopy

# Or with editable mode
pip install -e '.[dev]'
```

The `pyproject.toml` is maintained for pip compatibility.

## Compatibility

### What Still Works

- ✅ `pip install arroyopy` - Standard pip installation
- ✅ `pip install -e '.[dev]'` - Editable installation
- ✅ Conda environments - Can still use conda directly
- ✅ Virtual environments - venv still works
- ✅ GitHub Actions with pip - Maintained for compatibility

### What's New

- ✅ `pixi install` - Fast, reproducible environment setup
- ✅ `pixi run <task>` - Task runner for common operations
- ✅ Multiple environments - dev/prod/minimal/docs
- ✅ Cross-platform testing - CI runs on Linux/macOS
- ✅ Lock file - `pixi.lock` ensures reproducibility

## Dependency Resolution

Pixi uses conda's dependency resolver, which handles complex dependencies better than pip in some cases:

- **Scientific packages**: NumPy, Pandas properly linked with optimized libraries
- **Binary dependencies**: Automatic handling of system libraries
- **Python version**: Managed as a dependency, not separate

## Future Improvements

Potential additions:

1. **Task Chains**: Combine tasks (e.g., `format-lint-test`)
2. **Environment Variables**: Add `.env` file support
3. **Custom Channels**: If needed for specific packages
4. **Workspace Support**: If we split into multiple packages
5. **Scripts**: Add more automation tasks

## Troubleshooting

### Pixi Not Found

```bash
# Reinstall pixi
curl -fsSL https://pixi.sh/install.sh | bash
# Restart your shell
```

### Dependency Conflicts

```bash
# Clean and reinstall
pixi clean
pixi install
```

### IDE Integration

**VS Code**: Should auto-detect `.pixi/envs/dev/bin/python`

**PyCharm**: Point to `.pixi/envs/dev/bin/python` in project settings

## Resources

- [Pixi Documentation](https://pixi.sh/latest/)
- [Pixi Guide for arroyopy](docs/pixi-guide.md)
- [GitHub Actions with Pixi](.github/workflows/ci.yaml)

## Questions?

- **Pixi issues**: https://github.com/prefix-dev/pixi/issues
- **Arroyopy issues**: https://github.com/als-computing/arroyopy/issues
- **Documentation**: See `docs/pixi-guide.md`
