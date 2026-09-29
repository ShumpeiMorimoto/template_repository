# Project Name

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A brief, compelling description of what your project does and why it's useful.

## Features

- Feature 1: Brief description
- Feature 2: Brief description
- Feature 3: Brief description

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) (Python package & project manager)

### Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name

# Install dependencies (automatically creates .venv)
uv sync
```

## Quick Start

```python
from your_package.core import YourMainClass

# Initialize
instance = YourMainClass(param1="hello")

# Basic usage
result = instance.do_something()
print(result)
```

## Usage

### Basic Example

```python
from your_package.core import YourMainClass
from your_package.utils import helper_function

# Example 1: Using the main class
obj = YourMainClass(param1="value", param2=42)
result = obj.do_something()

# Example 2: Using utility functions
cleaned = helper_function("  some text  ")
```

### Advanced Usage

```python
from your_package.core import YourMainClass

# Advanced configuration
obj = YourMainClass(param1="advanced", param2=100)
result = obj.do_something()
```

## Configuration

Configuration can be done via environment variables or a config file:

### Environment Variables

Copy `.env.example` to `.env` and fill in the values (`.env` is git-ignored):

```bash
cp .env.example .env
```

### Configuration File

Create a `config.yaml` file:

```yaml
api_key: "your-api-key"
setting: "value"
database:
  host: "localhost"
  port: 5432
```

## Development

### Setting up development environment

```bash
# Clone the repository
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name

# Install all dependencies — the `dev` group (pytest, ruff, ty) is included by default
# (uv automatically creates a .venv — no need to manually create one)
uv sync
```

### Code Style

This project uses:
- [ruff](https://docs.astral.sh/ruff/) for linting and code formatting
- [ty](https://docs.astral.sh/ty/) for type checking

Run linter and formatter:

```bash
# Check for lint errors
uv run ruff check .

# Auto-fix lint errors
uv run ruff check --fix .

# Format code
uv run ruff format .

# Type check
uv run ty check .
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=your_package

# Run specific test file
uv run pytest tests/test_core.py

# Run with verbose output
uv run pytest -v
```

Tests cannot open outbound network connections (`tests/conftest.py`). Mark a test with
`@pytest.mark.allow_network` to opt out.

## AI-assisted development (Claude Code)

This repository ships a [Claude Code](https://docs.claude.com/en/docs/claude-code) harness:

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Project rules loaded into every session |
| `.claude/settings.json` | Denies reading `.env` / credentials; wires the hooks below |
| `.claude/hooks/check-secrets.sh` | Blocks `git commit` when staged files contain secrets or `.env` files |
| `.claude/hooks/check-lint.sh` | Blocks `git commit` when staged Python fails ruff / ruff format / ty |
| `.claude/hooks/require-*-model.py` | Requires an explicit `model` on subagents and workflows |
| `.claude/skills/bootstrap-project/` | One-time: turn this template into a named project |
| `.claude/skills/code-review-expert/` | Structured quick/full code review with checklists |
| `.claude/skills/drawio/` | Generate draw.io diagrams |
| `.claude/skills/professional-doc-architect/` | Framework for technical documentation |
| `.claudeignore` | Keeps caches, data and lock files out of Claude's context |

Personal overrides go in `.claude/settings.local.json` (git-ignored).

## Project Structure

```
your-project/
├── .claude/
│   ├── settings.json
│   ├── hooks/
│   └── skills/
├── .github/
│   └── workflows/
│       └── test-build.yml
├── src/
│   └── your_package/
│       ├── __init__.py
│       ├── core.py
│       └── utils.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_core.py
├── docs/               # end-user documentation
├── dev-docs/           # developer notes, TODO, experiment logs
├── examples/
│   └── example.py
├── CLAUDE.md
├── .env.example
├── pyproject.toml
├── uv.lock
├── README.md
└── LICENSE
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Install dependencies: `uv sync`
4. Make your changes
5. Run lint and tests: `uv run ruff check . && uv run ruff format --check . && uv run ty check . && uv run pytest`
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/your-repo-name](https://github.com/yourusername/your-repo-name)

## Roadmap

- [ ] Feature 1 planned
- [ ] Feature 2 planned
- [ ] Feature 3 planned
