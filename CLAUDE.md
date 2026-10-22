# How to Work With Me

**Be a critical coding companion.** I'm not always right. Present counter-arguments, surface tradeoffs, and push back on ideas that don't hold up. When a decision is ambiguous, lay out the options instead of silently picking one.

**Provide friction.** Don't default to agreement. No sycophancy, no glazing.

# Project Context

<!-- Fill in per repo -->
- **Purpose:** ...
- **Entry points:** ...

# Tooling

- `uv` for environments and dependencies. Never call `pip` directly.
- `ruff` for formatting and linting (line length 99).
- `ty` for static type checking.
- `pytest` for tests, configured with `testpaths = ["tests"]` and `--import-mode=importlib`.
- Python 3.12+.

## Verification

Before reporting a task as done, run all of these and fix every failure:

```bash
uv run ruff format
uv run ruff check --fix
uv run ty check
uv run pytest
```

Never silence a failure with `# type: ignore`, `# noqa`, or a skipped test without asking first.

## Dependencies

Ask before adding any dependency, runtime or dev. Once approved, use `uv add` / `uv add --dev`.

## Git

Never commit, push, or run any git command that changes repository state. I handle git.

# Repository Layout

- `src/<package>/` — source code
- `tests/` — tests for `src/`
- `tests/_mocks/` — test doubles
- `experiments/YYMMDD_short_description/` — one directory per experiment (e.g. `experiments/261022_prompt_ablation/`) holding its scripts, notebooks, tests, and outputs

Single src-layout package at the repo root. If a second package becomes necessary, propose converting to a uv workspace rather than doing it silently.

# Design Principles

- **Locality of Behavior**: keep related logic together so behavior can be understood without jumping across files.
- **Common Reason for Change**: group things that change together; separate things that change independently.
- **Less code, less debt**: simple, linear code. Build minimal functionality, verify it works, then add complexity.
- **Composition over inheritance. Protocols over ABCs.**
- **Clean core, details at the edges**: IO, parsing, and third-party APIs live at the boundaries; core logic operates on typed domain objects.
- **Minimal changes**: only touch code related to the task. Mark issues spotted in unrelated code with `TODO:` instead of fixing them.

# Python Rules

## Types and Data

- Full type hint coverage, including tests.
- Avoid `typing.Any` and `typing.cast` — they bypass type safety and aren't always caught by tooling. Use `object` and narrow, or parse into a model.
- Use modern syntax: `X | None`, built-in generics, PEP 695 type parameters (`def first[T](xs: list[T]) -> T`), `type` aliases.
- Internal data structures: `@dataclass(frozen=True, slots=True)`. Mutable only with a stated reason.
- External data (JSON, API responses, LLM output, config): parse into pydantic models at the boundary, hand typed objects inward.
- Prefer functional, immutable approaches: return new values instead of mutating arguments.

## Control Flow and Errors

- **No recursion.** All logic must be iterative.
- Functions should generally stay under ~60 lines — a signal to split, not a hard limit.
- Use early returns to avoid nesting.
- Declare data at the smallest possible scope.
- **Exceptions** for conditions that *can* happen (bad input, network failure). Don't catch broad exceptions just to keep going — code should fail loudly.
- **Assertions** for conditions that should *never* happen (broken invariants):
  - side-effect-free boolean tests
  - every assertion has a message stating what broke
  - never statically provable (always true or always false)

## Concurrency

- Use async IO via `anyio` (not raw `asyncio`) when IO actually runs concurrently — many requests, streaming, fan-out. Plain sync code is fine otherwise.
- No threading or multiprocessing for IO-bound work.

## Style and Comments

- Order functions top-down: composing functions before the components they call.
- Short docstrings on public functions and classes. No module docstrings.
- Inline comments only when the *why* is non-obvious: a hidden constraint, a subtle invariant, a workaround. Never describe what the code does, and never leave comments narrating your changes.
- The 99-character limit applies only to Python. Don't wrap prompts, Markdown, HTML, CSS, YAML, or other resource files to satisfy it.

## Operational Visibility

- Every entry point (script, CLI command) logs with `loguru` to stdout/stderr — no log files. Long-running, batch, or network operations log their major stages and completion.
- Use `tqdm` for item-level progress over measurable collections, with `desc`, `total`, and `unit` when available.
- Route loguru output through `tqdm.write` so log lines don't break progress bars.

## Experiments

Experiment directories hold throwaway code. Everything outside them follows the full rules below.

- A new experiment gets a new directory prefixed with today's date. Work only inside the current experiment; past experiments are a historical record — don't update them when `src/` changes.
- Experiments may import from `src/`; `src/` never imports from `experiments/`.
- Relaxed inside experiments: type hint coverage, docstrings, the 60-line guideline, the async rule (threads are fine for IO), and ruff/ty checks (`experiments/` is excluded in `pyproject.toml`).
- Still applies: no recursion, fail loudly, logging for entry points.
- Tests for experiment code live in the experiment directory and are run explicitly: `uv run pytest experiments/<dir>`.
- When experiment code proves worth keeping, propose promoting it into `src/`, where full rules and tests apply.
- Don't edit `.ipynb` files unless asked.

# Testing

Tests exist to find bugs now, not to protect a long-lived API. The biggest risk in research code is silently wrong results; crashes report themselves.

Priorities, in order:
1. Runtime assertions and type checks in the code itself.
2. One end-to-end smoke test per pipeline, on tiny real input.
3. Targeted tests where bugs are silent: parsing, data transformations, metrics, aggregation.
4. When a bug is found, first write a test that reproduces it, then fix it.

- Skip tests for glue and plumbing.
- Derive expected values independently (by hand, from a reference, from a known case). Never recompute them with the implementation's own logic.
- Tests are disposable: when behavior changes intentionally, delete or rewrite obsolete tests and say so. Never delete or weaken a test to make it pass.
- Name tests after behavior, not implementation: `test_is_zero_config`, `test_returns_null_cache`.
- Comments and docstrings in tests only when the behavior isn't self-explanatory.
- One assertion per test; aggregate multiple properties into a dict and compare once.
- Async tests use the anyio pytest plugin (`@pytest.mark.anyio`).

## Test Doubles

- Avoid monkey-patching. Inject dependencies and pass a test double.
- Prefer real implementations (in-memory, `tmp_path`, tiny datasets). Write a double only for slow, costly, or nondeterministic dependencies (LLM/API calls, external services).
- Doubles live in `tests/_mocks/`, explicitly subclass the Protocol they replace, and are exposed as fixtures.

## Recording and Snapshots

- `pytest-recording` only for expensive or nondeterministic network calls. Filter credentials in `vcr_config`. Re-record when requests change; never hand-edit cassettes.
- `pytest-snapshot` for complex outputs. Review snapshot diffs before accepting them.

