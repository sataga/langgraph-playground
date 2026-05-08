# Repository Guidelines

## Project Structure & Module Organization

This is a small Python 3.12 project. The current entry point is `main.py` at the repository root. Project metadata lives in `pyproject.toml`, and the Python version is pinned in `.python-version`. `README.md` is present but currently empty.

Use a `tests/` directory for test files as the project grows. If the application expands beyond a single script, move reusable code into a package directory such as `langgraph_playground/` and keep `main.py` as a thin CLI or startup wrapper.

## Build, Test, and Development Commands

- `python main.py`: run the current application entry point.
- `python -m venv .venv`: create a local virtual environment if one is not already present.
- `.\.venv\Scripts\Activate.ps1`: activate the virtual environment on Windows PowerShell.
- `python -m pip install -e .`: install the project in editable mode.

There are no declared runtime dependencies or build scripts yet. Add dependencies to `pyproject.toml` rather than importing undeclared packages.

## Coding Style & Naming Conventions

Use standard Python style: 4-space indentation, `snake_case` for functions and variables, `PascalCase` for classes, and uppercase names for constants. Keep functions small and give modules names that describe behavior, for example `graph_runner.py` or `state_store.py`.

Prefer type hints for public functions and code that crosses module boundaries. Keep side effects under `if __name__ == "__main__":` so modules remain importable from tests.

## Testing Guidelines

No test framework is configured yet. When adding tests, use `pytest` unless the project adopts another framework. Put tests under `tests/` and name files `test_*.py`.

Recommended command after adding pytest:

```powershell
python -m pytest
```

Focus tests on graph behavior, state transitions, and any external integrations. Use fixtures or fakes for networked services rather than calling real APIs in unit tests.

## Commit & Pull Request Guidelines

This repository has no commits yet, so there is no existing commit convention to follow. Use concise, imperative commit messages, for example `Add graph runner entry point` or `Configure pytest`.

Pull requests should include a short summary, the reason for the change, test results, and any setup or configuration notes. Link related issues when available. Include screenshots only for changes that affect visual output or developer-facing UI.

## Security & Configuration Tips

Do not commit secrets, API keys, or populated local environment files. Keep virtual environments, build artifacts, and caches out of version control; `.gitignore` already excludes `.venv`, `__pycache__`, and build outputs.
