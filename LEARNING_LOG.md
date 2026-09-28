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
  → re-asked in Lesson 3: XPASS right but missed that `strict` makes it FAILED; confused ERROR (fixture phase)
  with FAILED (test body). Demonstrated with `BASE_URL` override → FAILED, traceback points into the test body.
- "What does pyright even do?": explained as `tsc --noEmit`, never runs code or reads `.env`.

## Lesson 3 — Typed API client + models (2026-09-27)

**Ported:** `JuiceShopClient.register` / `login` + `json()` helper → `src/juice_shop_e2e/api/client.py`;
response shapes → `src/juice_shop_e2e/api/models.py`; `user.factory.ts` → `src/juice_shop_e2e/data/factories.py`;
`testUser` / `registeredUser` fixtures; remaining two tests of `tests/api/auth/login.spec.ts`.
Scope change vs plan: basket/address/card client methods moved to Lesson 7 (ported together with their tests).

### Concepts
- `BaseModel` vs TS `interface`: a live class validated at runtime; `Model.model_validate(response.json())` replaces `as T`.
- Nested models (`LoginResponse.authentication: Authentication`); field names must match JSON keys exactly.
- `BaseModel` ignores unknown fields by default (unlike `BaseSettings` + `.env`), which is right for API responses.
- A model describes data shape only; logic lives in the client.
- Custom exception: `class ApiError(Exception)` with a docstring body; `raise`, not `return`.
- Guard clause: `if not response.ok: raise ...` then `return response`.
- Late binding: names inside a function are resolved at call time, so helpers may be defined below their callers (still put them above for readability).
- `str | None` attribute annotation (≈ `token?: string`), needed so pyright doesn't infer `None`.
- Fixture instances are cached per test: every consumer gets the same `api` / `test_user` object.
- `in` / `not in` (→ `__contains__`) replaces `toContain`.
- Markers must be declared (`markers = [...]`) under `--strict-markers`; an unknown marker is a collection error.
- f-strings ≈ template literals.
- `Field(repr=False)` hides a value from `repr` (and from pytest assertion introspection output).

### Pitfalls hit
- `TestUser` would be collected by pytest (`Test*` classes) → renamed to `User`.
- First factory draft: no email suffix/domain (collisions under parallel runs), random password instead of `.env`, static security answer.
- `if (!response == 200):` / `else` without `:` / `return ApiError(...)` instead of `raise`.
- Logic placed inside a model (`response = raw_login()` in `AuthSession`); typo `unmail` would fail validation.
- `login` first posted to `USERS` without a body instead of calling `login_raw`.
- `return api.register(user)` returns `None` (and assigning it to a variable doesn't change that).
- Added `@smoke` to a non-smoke test, then replaced it with a non-existent `@pytest.mark.test` (caught by `--strict-markers`).

### TS → Python gotchas
- `faker` API differs (R7): `user_name()`, `pystr(min_chars=8, max_chars=8)`, `word()` instead of `petName()`.
- JSON payload keys stay camelCase (the SUT's contract); Python names are snake_case.
- pydantic lax mode coerces `"6"` → `6` but rejects `"abc"`.
- In Playwright Python: `ok` / `url` / `status` are properties; `text()` / `json()` are methods (they read the body).

### To revisit (weak answers)
- `model_validate` vs `as T`: fuzzy on *when/where* pydantic fails (immediately, at the parse line, with the field path).
- Why `ApiError` and not `assert`: missed the concrete `xfail(raises=AssertionError)` masking mechanism.
  → re-asked in Lesson 4: both wrong again (thought failure at `bid > 0`; answered XPASS instead of XFAIL).
  Demonstrated the `ValidationError` path. Memo:

  | In an xfail test | Status |
  |---|---|
  | `AssertionError` raised (matches `raises`), setup included | XFAIL (green) |
  | any other exception | FAILED / ERROR (red) |
  | test passes, `strict=True` | FAILED `[XPASS(strict)]` (red) |

## Lesson 4 — First UI test (2026-09-28)

**Ported:** `tests/ui/products/search.spec.ts` → `tests/ui/products/test_search.py`; `context` override →
`tests/ui/conftest.py`; minimal `ProductsPage` (`open`, `search`, `product_cards`, `no_results_message`);
`expect.timeout` → `expect.set_options(timeout=10_000)` in `tests/conftest.py`.

### Concepts
- pytest-playwright fixtures: `browser` (session), `context` / `page` (function); `base_url` fixture flows into the context automatically.
- Same-name fixture override: `def context(context)` receives the plugin's fixture and extends it.
- Directory scoping: `tests/ui/conftest.py` applies only to `tests/ui/**`.
- pytest injects fixtures **by name only**; type annotations are for pyright and ignored at runtime.
- `add_init_script` takes JS source as a string (TS serializes an arrow function via `toString()`).
- `TypedDict` (`SetCookieParam`): a dict with a fixed key set, checked only statically (≈ TS object type).
- Module-level code in `conftest.py` runs once (imported once during collection) → `expect.set_options(...)`.
- Web-first `expect(locator)` retries until the timeout; plain `assert locator.count()` checks once → flaky. `assert` is for API data.
- UI tests are parametrized per browser: `test_x[chromium]`.
- `_name` = private contract; locators used by tests stay public.

### Pitfalls hit
- Auto-import picked `playwright.async_api.BrowserContext` → pyright `reportUnusedCoroutine`. Always `sync_api`.
- Cookie list: one dict with empty values, then cookie names used as dict keys instead of `"name"` values (caught by `TypedDict`).
- `base_url.goto(...)` inside a page object; missing `self._page = page`; `click` / `fill` / `press` without `()` (B018 again).
- Weakened assertion: `to_contain_text(["Apple"])` instead of both product names (would pass with unrelated results).
- Test names not mirroring the TS titles (twice).

### TS → Python gotchas
- `readonly` locator fields → plain attributes set in `__init__`.
- `getByText` → `get_by_text`; everything else keeps its name in snake_case, no `await`.

### To revisit (weak answers)
- Why `expect` over `assert` in UI: missed "auto-retry".
- Why the UI `context` override doesn't affect API tests: answered "because of the type annotation" (wrong: directory scoping; pytest ignores annotations).
  → re-asked in Lesson 5: both answered correctly ("retries → flakiness"; "conftest applies to its dir and below").

## Lesson 5 — Page objects (2026-09-28)

**Ported:** `wait.ts` → `src/juice_shop_e2e/utils/wait.py`; `login.page.ts`, `registration.page.ts` →
`src/juice_shop_e2e/pages/`; `tests/ui/auth/login.spec.ts`, `registration.spec.ts` → `tests/ui/auth/`.
Scope change vs plan: basket/checkout pages and the rest of `ProductsPage` move to Lessons 6–7 (ported with their tests).

### Concepts
- `time.monotonic()` for deadlines (never jumps, unlike wall-clock `time.time()`); both are seconds → `timeout / 1000`.
- `while True:` ≈ `for (;;)`.
- Narrow `except PlaywrightTimeoutError` (aliased so it doesn't shadow the builtin `TimeoutError`); bare `raise` re-raises the caught exception with its message and traceback. Deliberate narrowing vs TS (flagged issue #6) documented in code.
- Keyword-only params (`*,`) with defaults ≈ TS options object `{ timeout = ..., interval = ... }`.
- Regex: `re.compile(r"...")`, raw strings, `re.IGNORECASE` ≈ `/.../i`; a plain string in `to_have_url` means exact match.
- Playwright Python: `locator.first` / `.last` are properties; `.nth(i)` is a method.
- Missing fixture name → `ERROR at setup` + "fixture 'x' not found"; pyright can't catch it (fixture names are pytest's business).
- VS Code F2 (Rename Symbol) renames every usage at once.
- Run the full suite after every step: it caught a regression in a file untouched by the step.

### Pitfalls hit
- `wait.py` draft: `Localtor` typo, missing `=` for a default, `monotonic()/1000` (wrong direction), `timeout=deadline` (absolute clock value as a duration), `if` without `:`, `raise Exception` (flagged by ruff B904).
- `register_ling`, `registred_user`, `RegistationPage` typos (pyright doesn't flag new attribute names or fixture param names).
- A variable named `str` shadowing the builtin.
- The second step of the "doesn't reveal whether the account exists" test was dropped: without it the property under test isn't checked.
- Accidental `no_results_message` → `_no_results_message` rename in `ProductsPage` (restored via `git restore`).
- Manually wrapped signature committed unformatted: run `ruff format` before review.
- **Recurring:** test names paraphrased instead of mirroring the TS title (4 times in Lessons 3–5). Rule: TS title → lowercase → spaces to `_`.
- Teacher error: I first said `.first()` is a method in Python; it's a property.

### TS → Python gotchas
- Flagged TS issue #4 (inline `#navbarAccount` locator in a spec) ported as-is with a comment.

### To revisit (weak answers)
- `monotonic` vs `time`: thought they return different formats (both are seconds; the difference is clock stability).
- Bare `raise` vs `raise Exception`: answered "catches errors better" (it's about preserving the original exception).
- `test_user` vs `registered_user`: knew why, missed what breaks when swapped.
