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
- Why pyright flags `Settings()` / why `model_validate({})` is wrong. → re-asked in Lesson 2: still weak
  (answered the `lru_cache` question instead). Key phrase: "static analysis sees signatures, runtime sees data".
- Why unknown keys fail for the `.env` file but not for OS env vars. → re-asked in Lesson 2: half right.
  Key: env vars are looked up *from fields*; the `.env` file is read *from its lines*.

## Lesson 2 — First API test (2026-09-27)

**Ported:** `tests/api/auth/login.spec.ts` (SQLi test only) + `JuiceShopClient.loginRaw` →
`tests/api/auth/test_login.py`, `src/juice_shop_e2e/api/client.py`, `tests/conftest.py`.
`docs/test-catalog.md` started.

### Concepts
- Fixture = plain function, injected by **parameter name**; `conftest.py` is auto-discovered, visible to its dir and below.
- `yield` splits a fixture into setup / teardown; teardown runs even if the test fails. Return type `Iterator[X]`.
- Overriding a plugin fixture: same name in `conftest.py` (`base_url` from pytest-base-url). Scope must stay `session` (ScopeMismatch otherwise).
- `@pytest.fixture` default scope = `function` (≈ TS test scope).
- `@pytest.mark.xfail(strict=True, raises=AssertionError)`: `raises` is a filter (other exceptions → FAILED); `strict` turns an unexpected pass (XPASS) into FAILED.
- Classes: `__init__` + `self.x = ...`; `_x` = private by convention; objects are created without `new`.
- `obj.method()` is sugar for `Class.method(obj)`; that's why `self` exists. Calling via the class bypasses overrides.
- Keyword-only params (`*` in the signature) replace TS options objects: `new_context(base_url=...)`, `post(url, data=...)`.
- Protocols via dunders: `str(x)` → `x.__str__()`, callable → `__call__`. There is no `.toString()`.
- Playwright Python: `response.status` is a property, not a method.
- `--import-mode=importlib`: module names come from the full path, so same-basename test files don't clash.
- Direct import ⇒ direct dependency (`playwright` added explicitly, not inherited from pytest-playwright).

### Pitfalls hit
- VS Code "New File" creates paths relative to the *selected* folder → `tests\tests\...`; a stale tab of a moved file re-creates it on save.
- `base_url` inside the fixture referred to the fixture function itself (name lookup), not the settings field.
- `@lru_cache` erases the wrapped signature: pyright did not flag `get_settings(arg)`.
- `APIRequestContext.dispose` without `()` and on the class instead of the instance (bugbear B018).
- Nested `def api` indented inside another fixture → a local function pytest never sees.
- `new:` / `self` in a plain function; `pass` used as a name (reserved keyword).
- `docker compose` conflict: fixed `container_name: juice-shop-sut` is shared with the TS project → only one SUT at a time.

### TS → Python gotchas
- `test.fail()` mid-test vs `xfail` over the whole test (R3): verified by hand; SUT down → `playwright Error` → FAILED, not XFAIL.
- No `{ email }` shorthand; dict keys are quoted strings.
- `HttpUrl` trailing slash is harmless for absolute paths (`/rest/...` replaces the base path, like `new URL()`).

### To revisit (weak answers)
- XFAIL vs FAILED vs XPASS(strict): answered Q1 and Q3 wrong (thought the marker alone decides). Verified Q1 by hand.
