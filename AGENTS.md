# Repository Guidelines

## Project Structure & Module Organization
- `binaries/`: CLI, daemon, runtime, coordinator binaries.
- `libraries/`: Core crates (communication, message, telemetry, shared memory, etc.).
- `apis/`: Language APIs (Rust, Python, C/C++). Python bindings live under `apis/python/*`.
- `examples/`: Runnable dataflows and language-specific demos (see `cargo run --example ...`).
- `node-hub/`: Prebuilt nodes (mostly Python) with their own `pyproject.toml` and tests.
- `tests/`: Integration-style dataflows and latency/queue tests.
- `docs/`, `docker/`, `.github/`: Documentation, container assets, and CI workflows.

## Build, Test, and Development Commands
- Rust check/build:
  - `cargo check --all --exclude dora-dav1d --exclude dora-rav1e`
  - `cargo build --all --exclude dora-node-api-python --exclude dora-operator-api-python --exclude dora-ros2-bridge-python`
- Rust tests:
  - `cargo test --all --exclude dora-dav1d --exclude dora-rav1e --exclude dora-node-api-python --exclude dora-operator-api-python --exclude dora-ros2-bridge-python`
- Formatting & lint:
  - `cargo fmt --all` and `cargo clippy --all`
- Examples:
  - `cargo run --example rust-dataflow`
- CLI (local install) and quick run:
  - `cargo install --path binaries/cli --locked`
  - `dora up && dora build examples/rust-dataflow/dataflow.yml && dora run examples/rust-dataflow/dataflow.yml`
- Python nodes (node-hub or APIs):
  - `uv venv --seed -p 3.12 && uv pip install -e apis/python/node`
  - `uv run ruff check .` and `uv run pytest`

## Coding Style & Naming Conventions
- Rust: `rustfmt` defaults; prefer idiomatic module layout; crate names kebab-case, Rust types CamelCase, functions snake_case.
- Python: `ruff` for lint/format; modules and files snake_case; tests under `tests/test_*.py`.
- YAML graphs: concise IDs, snake_case names; keep graphs in `examples/*` or package roots.

## Testing Guidelines
- Rust: place unit tests in-module; integration tests under `tests/` per crate. Run with `cargo test` (see excludes above).
- Python (node-hub): write `pytest` tests in `tests/`; use fixtures to skip GPU/network when not available; run with `uv run pytest`.
- Dataflow checks: prefer `dora build ...` then `dora start ... --detach` for smoke tests; add minimal graphs in `tests/*` when feasible.

## Commit & Pull Request Guidelines
- Commits: imperative mood; keep scope focused. Conventional prefixes welcome (e.g., `feat:`, `fix:`, `docs:`).
- PRs: include a clear description, linked issues, reproduction or example commands, and docs updates if behavior changes. Ensure CI (check, test, fmt, clippy) passes.

## Security & Configuration Tips
- Do not commit credentials or large model artifacts. Use environment variables and `.gitignore`d files for secrets. Prefer reproducible installs via `uv` and `cargo --locked`.
