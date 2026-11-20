# Python Project Management with `uv`

`uv` is an extremely fast Python package installer and resolver, written in Rust. It is designed as a drop-in replacement for `pip`, `pip-tools`, `virtualenv`, and `venv`. This reference covers the most common `uv` commands for modern Python development across the training and serving workflows.

## Installation

Install `uv` on your system using one of the following commands:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Core Workflows

`uv` can operate in two modes: as a global `pip` replacement or as a project-level environment manager.

### 1. Virtual Environments

The `uv venv` command creates and manages virtual environments, similar to Python's built-in `venv` module.

```bash
# Create a virtual environment named .venv using Python 3.12
uv venv -p 3.12

# Create and activate (on Linux/macOS)
source .venv/bin/activate

# Create and activate (on Windows)
.venv\Scripts\activate
```

Once activated, you can use `uv pip` to manage packages within that environment.

### 2. Installing Packages

The `uv pip` command is a high-speed replacement for `pip`.

```bash
# Install packages into the active virtual environment
uv pip install "fastapi[all]" uvicorn

# Install from a requirements.txt file
uv pip install -r requirements.txt

# Uninstall packages
uv pip uninstall fastapi
```

### 3. Reproducible Environments

For reproducible builds, `uv` can replace `pip-tools` to compile and sync dependencies from a `pyproject.toml` or `requirements.in` file.

**`uv pip compile`**: Resolves dependencies and creates a lock file.

```bash
# Compile requirements.in into requirements.txt
uv pip compile requirements.in -o requirements.txt

# Compile pyproject.toml into a lock file
uv pip compile pyproject.toml -o uv.lock
```

**`uv pip sync`**: Installs packages from a lock file, ensuring the exact versions are used. This is the fastest and most reliable way to install project dependencies.

```bash
# Sync the environment with a requirements.txt file
uv pip sync requirements.txt

# Sync the environment with a uv.lock file
uv pip sync uv.lock
```

## Running Commands

The `uv run` command executes a command within the project's virtual environment, without needing to activate it first. `uv` automatically discovers the `.venv` directory.

```bash
# Run a Python script
uv run python my_script.py

# Run a CLI tool installed in the environment
uv run pytest
```

## Standalone Script Execution (PEP 723)

`uv run` can execute standalone Python scripts that declare their own dependencies inline using PEP 723 metadata:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "torch==2.14.1",
#     "transformers==5.19.0",
#     "trl==1.15.0",
#     "peft==0.21.2",
#     "accelerate==1.15.0",
#     "datasets==5.0.1",
#     "bitsandbytes==0.50.2",
#     "huggingface_hub",
# ]
# ///

import torch
print(f"CUDA available: {torch.cuda.is_available()}")
```

Execute directly without activating a virtual environment:

```bash
uv run script.py
```
