# Pixi Quick Reference Card

## Installation

```bash
# Linux/macOS
curl -fsSL https://pixi.sh/install.sh | bash

# macOS (Homebrew)
brew install pixi


## First Time Setup

```bash
cd arroyopy
pixi install              # Install dependencies
pixi run install-dev      # Install package in editable mode
```

## Daily Commands

```bash
# Testing
pixi run test             # Run tests
pixi run test-verbose     # Verbose output
pixi run test-cov         # With coverage report

# Code Quality
pixi run format           # Format code with black
pixi run format-check     # Check formatting
pixi run lint             # Run flake8
pixi run pre-commit       # Run all checks

# Development
pixi run install-dev      # Reinstall in editable mode
pixi run clean            # Clean build artifacts
```

## Environment Commands

```bash
# List environments
pixi project info

# Use specific environment
pixi shell -e dev         # Enter dev shell
pixi run -e dev test      # Run in dev environment

# Available environments:
# - default: Core only
# - dev: Full development (recommended)
# - prod: Production-like
# - minimal: Minimal setup
# - docs: Documentation tools
```

## Dependency Management

```bash
# Update dependencies
pixi update

# Add dependency
# Edit pixi.toml, then:
pixi install

# Clean and reinstall
pixi clean
pixi install
```

## Common Tasks

| Task | Command |
|------|---------|
| Run tests | `pixi run test` |
| Format code | `pixi run format` |
| Lint code | `pixi run lint` |
| Pre-commit checks | `pixi run pre-commit` |
| Install hooks | `pixi run pre-commit-install` |
| Build package | `pixi run build` |
| Clean artifacts | `pixi run clean` |

## Git Workflow

```bash
# Start feature
git checkout -b feature/my-feature
pixi install

# Develop and test
# (edit code)
pixi run test
pixi run format
pixi run pre-commit

# Commit
git add .
git commit -m "My feature"
git push
```

## IDE Setup

### VS Code
- Python interpreter: `.pixi/envs/dev/bin/python`
- Should auto-detect

### PyCharm
- Settings → Project → Python Interpreter
- Add → Existing → `.pixi/envs/dev/bin/python`

## Troubleshooting

```bash
# Environment issues
pixi clean && pixi install

# Update pixi itself
curl -fsSL https://pixi.sh/install.sh | bash

# View detailed info
pixi info
pixi project info
```

## Help

```bash
pixi --help              # General help
pixi run --help          # Task help
pixi install --help      # Install help
```

## Online Resources

- Pixi Docs: https://pixi.sh/latest/
- Project Guide: docs/pixi-guide.md
- Migration Notes: docs/PIXI_MIGRATION.md
