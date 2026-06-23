# Spark — CLI Scaffolding Tool

## Overview

**Spark** is a Python CLI scaffolding tool that generates project structures from predefined templates. Installable via `uv tool install spark`. Designed primarily for personal use but built with production-quality architecture from day one.

### Commands (v1)

| Command | Purpose |
|---------|---------|
| `spark create <name>` | Interactive scaffolding wizard — pick a template type, generate the full project tree |
| `spark dev` | Run `process-compose up` from the project root (wrapper around process-compose) |

### Commands (future, not designed)

| Command | Purpose |
|---------|---------|
| `spark add <thing>` | Inject add-ons into an existing scaffolded project |

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Language | Python 3.12+ | You chose it; mature CLI ecosystem |
| CLI framework | [Typer](https://typer.tiangolo.com/) | Industry standard for Python CLIs. Built on Click. Type-hint driven. |
| Terminal UI | [Rich](https://rich.readthedocs.io/) | Progress bars, colored prompts, styled output, tables. Everything you want for a professional feel. |
| Package manager | [uv](https://docs.astral.sh/uv/) | You already use it. Spark delegates `uv init` and `uv add` for pyproject generation. |
| Process runner | [process-compose](https://f1bonacc1.github.io/process-compose/) | Already in your stack. Spark just wraps the CLI. |
| Testing | pytest | Standard. Already in your toolchain. |
| Linting | ruff | Fast, Python-native, covers flake8/isort/black. |

---

## Architecture

### High-level design

Spark is structured as a pipeline:

```
User input (CLI args + interactive prompts)
    → Template selection (which scaffold to build)
    → Scaffold engine (generate dirs + files)
    → Output (project on disk)
```

### Module layout

```
spark/
├── __init__.py             # Version, metadata
├── __main__.py             # Entry: `python -m spark` or `spark`
├── cli.py                  # Typer app, command definitions
├── app.py                  # Application orchestration (ties phases together)
├── scaffold/               # Core scaffolding logic
│   ├── __init__.py
│   ├── engine.py           # Creates dirs, writes files, runs uv commands
│   └── templates.py        # Template definitions (dir tree, file stubs, deps)
├── ui/                     # All terminal I/O
│   ├── __init__.py
│   ├── prompter.py         # Interactive prompts (Rich-based)
│   ├── progress.py         # Progress bars, spinners, status indicators
│   └── console.py          # Shared Rich Console instance, styling config
├── utils/                  # Pure helper functions
│   ├── __init__.py
│   ├── errors.py           # Exception hierarchy
│   └── logging_config.py   # Logging setup (Rich handler)
└── tests/
    ├── __init__.py
    ├── test_scaffold.py    # Unit tests for scaffold engine
    ├── test_templates.py   # Template structure validation
    └── test_cli.py         # Integration tests (invoke CLI, check output)
```

### Key architectural decisions

**Separation of concerns:**
- `templates.py` owns *what* to build (data)
- `engine.py` owns *how* to build it (machinery)
- `cli.py` owns *when* to build (user input / commands)
- `ui/` owns *the look* (presentation)
- `app.py` orchestrates them in order

This means you can change the template structure without touching the engine, and change the terminal output without touching the logic. Prototyper V2's problem was mixing these — every feature touched everything.

**Template model:**
Each template is a dataclass:

```python
@dataclass
class Template:
    name: str
    label: str                  # Human-readable name for prompts
    description: str
    directory_tree: dict        # Nested dict of dirs → files
    stubs: dict[str, str]       # File path → content template
    dependencies: list[str]     # uv add packages
```

The `directory_tree` is a simple nested dict:

```python
{
    "app": {
        "core": {
            "__init__.py": None,       # None = empty file
            "auth.py": "auth.py.jinja",
            "database.py": "database.py.jinja",
            ...
        },
        "routers": {"__init__.py": None},
        "services": {
            "__init__.py": None,
            "auth_service.py": "auth_service.py.jinja",
            "user_service.py": "user_service.py.jinja",
        },
        ...
    },
    "tests": {
        "__init__.py": None,
        "unit": {"__init__.py": None},
        "integration": {"__init__.py": None},
    },
    ...
}
```

Plain dicts — no YAML, no external schema. Later this can be serialized to YAML if wanted.

**uv delegation:**
Spark does NOT ship pyproject.toml, .gitignore, .python-version, or uv.lock. It runs `uv init <name>` which generates those correctly. Then it runs `uv add <deps>` to install packages. This keeps Spark tiny and always compatible with uv's latest conventions.

**Error handling architecture:**
A small exception hierarchy — not a sprawling one:

```python
class SparkError(Exception):
    """Base for all spark errors."""

class TemplateNotFound(SparkError):
    """Requested template doesn't exist."""

class ProjectExistsError(SparkError):
    """Target directory already exists."""

class ScaffoldError(SparkError):
    """Something went wrong during generation."""
```

Every command wraps in a top-level handler that catches `SparkError`, logs it, prints a styled error to the user, and exits non-zero. No silent failures.

**Logging:**
Uses Rich's `logging.Handler` to send logs to the console with timestamps and colors. DEBUG/INFO for development, WARNING/ERROR for user-visible problems. This is set up once at startup and never touched again — Prototyper V2's sin was scattering log setup everywhere.

---

## Phase 1: Project skeleton + scaffolding engine

**Goal:** Get the core `spark create` working end-to-end. Run `spark create my-project`, pick a template, get a project on disk.

**Why this matters:** This is the foundation. If the engine is clean, every feature after is just adding templates or commands. Rushing this is how Prototyper V2 got tangled.

**What to build:**
- [ ] Initialize project: `uv init spark`, set up pyproject.toml with typer + rich deps
- [ ] Create the module structure above (cli.py, app.py, scaffold/, ui/, utils/)
- [ ] Implement `Template` dataclass and two template definitions: `api`, `basic`
- [ ] Implement `scaffold/engine.py` — given a Template + project path:
  - Creates directory tree recursively
  - Writes empty `__init__.py` files where needed
  - Writes stub files from template content
  - Runs `uv init` then `uv add` for dependencies
- [ ] Implement `ui/prompter.py` — Rich-based interactive:
  - Select template type from a list
  - Confirm project name if not provided via arg
- [ ] Implement `ui/progress.py` — Rich progress bar during scaffolding
- [ ] Implement `cli.py` — `spark create` command that calls the orchestration
- [ ] Wire up `app.py` — orchestration: prompt → select template → scaffold → report
- [ ] Set up logging (Rich handler, `SPARK_LOG_LEVEL` env var)
- [ ] Basic error handling: catch `ProjectExistsError`, `TemplateNotFound`, show styled error

**Key decisions:**
- **Stub files are plain strings in Python**, not Jinja templates for v1. Variables like `{{project_name}}` are replaced with `.replace()`. Keeps it simple.
- **Empty `__init__.py`** files are the default for any Python directory. No special "should I create this?" logic.
- **`uv init` + `uv add`** runs as subprocess. Errors bubble up as `ScaffoldError`.

**Quality bar:**
- Every module has a `__init__.py` that exports its public API
- Type hints on every function signature
- Functions are small (under 20 lines) and do one thing
- No `print()` anywhere — all output goes through Rich Console
- Tests: scaffold engine can run without a TTY (integration-safe)

**Expected outcome:**
```
$ spark create my-api
✔ Which template?  API
⠋ Creating project...
  ✔ Running uv init...
  ✔ Creating directory structure...
  ✔ Installing dependencies (uv add)...
✔ Project ready at ./my-api
$ cd my-api && ls
```

**Next:** Phase 2 — stub file content, `spark dev` command, concrete template definitions.

---

## Phase 2: Template stubs + spark dev

**Goal:** Fill in the actual stub files for each template, and add `spark dev` as a process-compose wrapper.

**Why this matters:** The templates need real content so scaffolding produces a *runable* project, not just empty folders. And `spark dev` closes the loop — create, then immediately run.

**What to build:**
- [ ] Write stub content for all API template files:
  - `app/main.py` — minimal FastAPI app with health check
  - `app/core/database.py` — SQLAlchemy async engine setup
  - `app/core/auth.py` — password hashing + JWT stubs
  - `app/core/exceptions.py` — application exception classes
  - `app/core/logging_config.py` — logging setup
  - `app/models.py` — Base + example User model
  - `app/schemas.py` — example Pydantic schemas
  - `app/services/auth_service.py` / `user_service.py` — service stubs
  - `app/ws/connections.py` / `manager.py` — websocket manager stubs
- [ ] Write stub for Basic template:
  - `src/main.py` — minimal Typer CLI entry point
  - No app/, core/, models/, schemas/, ws/
- [ ] Write `process-compose.yaml` stub for API template (uvicorn + redis)
- [ ] Implement `spark dev` — detects `process-compose.yaml` in CWD (or arg), runs `process-compose up`
- [ ] Write `.env.example` and `.gitignore` stubs (basic Python defaults, API-specific additions)

**Key decisions:**
- Stub files contain real, working code — not placeholder comments. An API main.py actually starts uvicorn. A basic main.py actually runs a typer app. This makes `spark create` → `spark dev` a valid workflow.
- `.env.example` includes keys for DB URL, secret key, redis URL — commented out with sensible defaults.
- `process-compose.yaml` is pre-configured with uvicorn + any sidecars (redis).

**Quality bar:**
- Every stub file is valid Python (no syntax errors)
- Import chains work: `main.py` can import from `core.database`, etc.
- Basic template has zero references to FastAPI, auth, database, websockets
- `spark dev` fails gracefully with a clear message if no process-compose.yaml is found

**Expected outcome:**
```
$ spark create my-api -- --template api
$ cd my-api
$ spark dev
  → Runs process-compose up (starts uvicorn + redis)
```

**Next:** Phase 3 — testing, CI, polish.

---

## Phase 3: Testing, CI, polish

**Goal:** Make the project production-grade with tests, CI pipeline, and UX polish.

**Why this matters:** This is where "code quality" stops being aspirational and becomes enforced. Every change from here on has a guardrail.

**What to build:**
- [ ] CLI integration tests:
  - `test_create_creates_directory` — run `spark create test-proj`, assert dir exists
  - `test_create_api_template` — assert the full tree matches expected
  - `test_create_basic_template` — assert basic tree
  - `test_create_existing_dir` — assert error/message when dir exists
  - `test_dev_no_compose_file` — assert graceful error
  - `test_dev_with_compose_file` — mock process-compose, assert it's called
  - `test_create_with_name_arg` — non-interactive mode
- [ ] Unit tests:
  - `test_template_definitions` — validate template structures have required keys
  - `test_scaffold_engine` — mock filesystem, verify tree creation
- [ ] Set up pytest config: `pyproject.toml` test config, conftest with fixtures
- [ ] Add `ruff` configuration to pyproject.toml
- [ ] Set up GitHub Actions CI:
  - Python 3.12 / 3.13 matrix
  - `ruff check .`
  - `pytest -v`
  - `uv build` (verify package builds)
- [ ] UX polish:
  - Color-coded output: green for success, yellow for warnings, red for errors
  - "Project created successfully" summary panel (Rich Panel)
  - Suggested next steps: `cd my-project && spark dev`
  - Version flag: `spark --version`
  - Help text: `spark --help` shows clean, organized command list

**Key decisions:**
- Tests use `pytest` with `tmp_path` fixture — no real filesystem contamination
- CLI tests use Typer's `CliRunner` (from `typer.testing`) — simulates stdin/stdout without subprocess
- Mock `uv init` and `uv add` calls in tests (don't actually run uv in CI)
- Ruff config in pyproject.toml — single source of truth

**Quality bar:**
- `ruff check .` passes with zero errors
- All tests pass
- Test coverage > 80% for scaffold engine
- CI is green

**Expected outcome:**
```
$ ruff check .
$ pytest -v --cov=spark
  10 passed
$ uv build
  Successfully built spark-0.1.0.tar.gz
```

---

## Phase 4: Distribution + documentation

**Goal:** Package spark for `uv tool install spark` and write clear documentation.

**Why this matters:** Distribution is the last mile. If it's not easy to install and understand, the tool doesn't exist.

**What to build:**
- [ ] Configure `pyproject.toml` for uv tool distribution:
  - `[project.scripts]` entry point: `spark = "spark.cli:app"`
  - Proper metadata: author, description, license, classifiers
- [ ] Write `README.md`:
  - What is Spark?
  - Quick start: `uv tool install spark` → `spark create my-proj`
  - Available templates
  - Commands reference
- [ ] Test `uv tool install .` works from repo root
- [ ] Test `spark create` from a clean environment (not in repo)
- [ ] Write `CONTRIBUTING.md` — how to add a template, dev setup
- [ ] (Optional) Publish to PyPI or keep as `uv tool install git+...`

**Key decisions:**
- `uv tool install spark` is the distribution channel (no homebrew, no npm)
- README is the primary documentation — keeps maintenance surface small
- PyPI publish is optional for v1; uv can install from GitHub directly

**Expected outcome:**
```
$ uv tool install spark
$ spark create my-api
✔ Which template?  API
✔ Project created at ./my-api
✔ Next: cd my-api && spark dev
```

---

## Template specifications

### API template

```
{project_name}/
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml           # via uv init
├── README.md                # via uv init
├── uv.lock                  # via uv init
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, uvicorn startup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── exceptions.py
│   │   └── logging_config.py
│   ├── routers/
│   │   └── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── user_service.py
│   └── ws/
│       ├── __init__.py
│       ├── connections.py
│       └── manager.py
├── scripts/
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── __init__.py
│   └── integration/
│       └── __init__.py
└── process-compose.yaml
```

**Dependencies:** `fastapi[standard]`, `sqlalchemy`, `asyncpg`, `pyjwt`, `pwdlib[argon2]`, `pytest`, `pytest-asyncio`, `redis[asyncio]`

### Basic template

```
{project_name}/
├── .gitignore
├── .python-version
├── pyproject.toml            # via uv init
├── README.md                 # via uv init
├── uv.lock                   # via uv init
├── src/
│   ├── __init__.py
│   └── main.py               # Typer CLI entry point
├── tests/
│   ├── __init__.py
│   └── unit/
│       └── __init__.py
└── scripts/
```

**Dependencies:** `typer`, `rich`, `pytest`

---

## Teaching moments (woven throughout)

| Phase | Concept | Where it shows up |
|-------|---------|-------------------|
| 1 | Separation of concerns | The module split: templates vs engine vs UI vs CLI |
| 1 | Minimal public API | Each `__init__.py` exports only what's needed |
| 1 | Defense in depth | Error hierarchy: don't catch `Exception`, catch `SparkError` |
| 1 | Single responsibility | Functions under 20 lines, one job each |
| 2 | Composition over inheritance | Templates are dataclasses, not subclasses |
| 2 | Dependency injection | Pass Console/Path to scaffold engine, don't import globally |
| 3 | Testing pyramid | Unit tests (fast) → integration tests (CLI) → manual (rare) |
| 3 | Config as code | Ruff/flake8 config in pyproject.toml, not a separate file |
| 4 | Distribution as UX | Entry points, tool install, zero-config install |
