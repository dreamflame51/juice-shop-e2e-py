# Learning Log

## Lesson 1 — Bootstrap + config (2026-09-27)

**Ported:** `package.json` / `tsconfig.json` / `eslint.config.js` → `pyproject.toml` (uv, ruff, pyright);
`src/utils/config.ts` → `src/juice_shop_e2e/config.py`; `.env.example`, `docker-compose.yml` copied verbatim.

### Concepts
- uv ≈ npm + nvm: `pyproject.toml` / `uv.lock` / `.venv` / `.python-version`; `uv run` ≈ `npx`.
- `src/` layout: the package is importable only via the editable install in `.venv`, never from cwd.
- `pydantic-settings`: fields are type annotations; values are read from env / `.env` when the instance is created.
- `SecretStr` masks the value in `repr`/`str`; the real value only via `.get_secret_value()`.
- `Field(min_length=1)` = constraint, not a default; the field stays required.
- `@lru_cache` on a zero-arg function = lazy per-process singleton. `@deco` over `def f` means `f = deco(f)`.
- Class-body annotations are evaluated at import time (pydantic reads them at runtime) → a missing import is a `NameError`, not only a lint error.

### Pitfalls hit
- Class body with only comments → `IndentationError` (comments are not a body; use `pass`).
- `BaseSettings` does not read `.env` unless `env_file` is set.
- `.env` keys not modelled by the class → `extra_forbidden` (default for file sources). Fixed with `extra="ignore"` (the `.env` is shared with docker-compose).
- R8 reproduced: `TEST_USER_PASSWORD=` passed as `SecretStr('')` until `min_length=1`.
- pyright `reportCallIssue` on `Settings()`: `@dataclass_transform` makes fields look like required `__init__` args. Fixed with a narrow `# pyright: ignore[reportCallIssue]` plus a reason. `Settings.model_validate({})` is a trap: it skips `__init__`, where env loading happens.
- Missing `env_file_encoding="utf-8"`: on Windows / Python 3.12 the locale codepage is used → silent corruption of non-ASCII values.
- Stray keystrokes after Ctrl+S (`1S`, `rejectsBa`): read the error location first.

### TS → Python gotchas
- TS `if (!value)` rejects `""`; a pydantic `str` accepts it (R8).
- `HttpUrl` normalizes `http://localhost:3000` → `http://localhost:3000/` (trailing slash). Handle it when joining URLs in Lesson 2.
- A module-level `settings = Settings()` is also a singleton (`sys.modules`). The real problem is that it fails at import → pytest collection errors for every importing test file.
- `env_file=".env"` is cwd-relative (same as dotenv) → IDE runners with a different cwd won't find it.

### To revisit (weak answers)
- Why pyright flags `Settings()` / why `model_validate({})` is wrong.
- Why unknown keys fail for the `.env` file but not for OS env vars.
