# Python environment with uv

Use uv exclusively for the Python environment in this project.

## Environment commands

- Use uv to install, sync, and lock Python dependencies
- Never use pip, pip-tools, poetry, or conda for dependency management
- Do not use direct `python` commands

Use these commands:

- Install dependencies: `uv add <package>`
- Remove dependencies: `uv remove <package>`
- Sync dependencies: `uv sync`

## Running Python Code

- Run a Python script with `uv run <script-name>.py`
- Run Python tools like pytest with `uv run pytest`
