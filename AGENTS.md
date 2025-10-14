# Repository Guidelines

## Project Structure & Module Organization
Source crates live under `libraries/` and `binaries/`. Use `examples/` for runnable dataflows and `node-hub/` for prebuilt Python nodes. Language bindings reside in `apis/`, while integration scenarios sit in `tests/`. Keep documentation and design notes under `docs/` or repo-level `.md` files. Favor colocating small helpers beside their caller to preserve module cohesion.

## Build, Test, and Development Commands
- `cargo check --all --exclude dora-dav1d --exclude dora-rav1e`: fast structural validation for the Rust workspace.
- `cargo test --all --exclude dora-dav1d --exclude dora-rav1e --exclude dora-node-api-python --exclude dora-operator-api-python --exclude dora-ros2-bridge-python`: run the standard test suite.
- `cargo fmt --all` and `uv run ruff check .`: enforce Rust and Python formatting/linting.
- `cargo clippy --all`: catch Rust correctness and style issues.
- `uv venv --seed -p 3.12 && uv pip install -e apis/python/node && uv run pytest`: prepare and test the Python node API.
- `dora build && dora start --detach`: validate dataflows before publishing.

## Coding Style & Naming Conventions
Rust follows rustfmt defaults; crates use kebab-case, modules and functions snake_case, and types CamelCase. Python modules stay snake_case with Ruff enforcing imports and spacing. Prefer `eyre`/`anyhow` for Rust error contexts and raise typed exceptions in Python. Keep public APIs documented with `///` comments or docstrings.

## Testing Guidelines
Name Rust unit tests after the behaviour under test and keep integration suites in `tests/`. For dataflow checks, combine `cargo test` with a targeted `dora start` to ensure nodes interact correctly. Python tests live in `tests/test_*.py` and may rely on fixtures to skip GPU or network dependencies. Treat flakiness as a bug; add regression tests before merging fixes.

## Commit & Pull Request Guidelines
Write commits in the imperative mood (“Add telemetry exporter”) and group logical changes. Ensure PR descriptions summarize the problem, highlight impacts on operators or APIs, and link issues. Include reproduction steps or `cargo test` output when the change touches runtime behaviour. Request review from domain owners and wait for CI to pass before merging.

## Security & Environment Notes
Store API keys outside the repository; scripts like `test_env_api_key.sh` illustrate the expected environment variables. Review shell scripts under `docker/` and install helpers for platform-specific steps, and avoid checking secrets into `out/` or `target/`. On macOS, prefer `uv` over global `pip` to keep dependencies reproducible.
