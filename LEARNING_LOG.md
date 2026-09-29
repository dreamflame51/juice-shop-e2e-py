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
  → re-asked in Lesson 6: all three answered correctly.

## Lesson 6 — Fixture graph + auth (2026-09-29)

**Ported:** `session` + `authedPage` fixtures; `basket.page.ts` → `BasketPage`; `ProductsPage` snackbar /
`product_card` / `add_to_basket`; client `_auth_headers`, `add_to_basket_raw`, `add_to_basket`;
`tests/ui/basket/add-to-basket.spec.ts` → `tests/ui/basket/test_add_to_basket.py`.

### Concepts
- Fixture graph `test_user → registered_user → session → authed_page`; each fixture built once per test.
- R9 in action: `session` calls `api.login()`, which stores the token in the **same** cached `api` instance.
- `@pytest.mark.usefixtures("authed_page")` for side-effect-only fixtures; page objects share the cached `page`.
- Python `add_init_script` has no `arg`: embed values with `json.dumps(...)` (a valid, escaped JS literal).
- `@property` ≈ TS getter (accessed without `()`); conditional expression `a if cond else b` ≈ `cond ? a : b`.
- `dict[str, str]` ≈ `Record<string, string>`.
- `locator.filter(has_text=...)`, `get_by_role("button", name=re.compile(...))`, chained `locator(...)`.
- `_raw` method returns the response for status assertions; the plain method goes through `_ensure_ok` for setup.

### Pitfalls hit
- `from pydantic import json` (auto-import): pyright was silent because `pydantic.json` has a module-level `__getattr__`; runtime `AttributeError`. Import stdlib modules directly.
- Unquoted dict keys `{name: ...}` (JS habit; Python evaluates variables).
- `get_by_role("button", name=name)` with the product name, and no `.click()` (not caught: it's a call, not a bare attribute).
- `has_text="productName"` (string literal instead of the variable; unused param would need ruff `ARG`).
- Regex written as JS literal strings `"/placed .* into basket/i"` → exact-text match; must be `re.compile(...)`.
- `self._token.__dict__` for headers; `{..., quantity}` shorthand; options object passed as a positional dict; `self._auth.headersS`.
- `add_to_basket` calling itself (infinite recursion).
- Payload keys changed to `basketId` / `productId` → SUT 500 "ProductId undefined". SUT contract keys are copied verbatim.
- Not running `ruff check --fix` (import order) — fixed by me several times.

### TS → Python gotchas
- New flagged TS issue #7: `mat-card` also matches the "challenge solved" notification → the search test saw 3 cards after a 500 solved "Error Handling". Deferred to Lesson 9 (flakiness), parity kept for now.
- Flagged issue #2 (`/1/`, `/2/` weak regex) ported as-is with comments.

### To revisit (weak answers)
- Why `usefixtures` + why page objects share the authenticated page (cached `page`): described the outcome, not the mechanism.
- Who authenticates `api`: thought the `api` fixture logs in (it's `session`, mutating the shared instance).
- Why `json.dumps` for the init script: answered "no such method" (it's escaping/injection safety).
  → re-asked in Lesson 7: all three answered correctly.

## Lesson 7a — Data builders + checkout client (2026-09-29)

Lesson 7 split into 7a (factories, checkout client, API checkout tests) and 7b (basket isolation + UI checkout).

**Ported:** `address.factory.ts` / `card.factory.ts` → `Address` / `Card` models + `build_address` / `build_card`;
client `get_basket(_raw)`, `create_address`, `create_card`, `checkout(_raw)` + response/request models;
`tests/api/basket/checkout.spec.ts` → `tests/api/basket/test_checkout.py`.

### Concepts
- `ConfigDict(alias_generator=to_camel, validate_by_name=True)` + `model_dump(by_alias=True)`: snake_case in Python, camelCase on the wire.
- `Field(alias="Products")` for one-off PascalCase keys; `list[Model]` parses every element.
- SUT rules in the model: `Field(pattern=...)` for strings, `Field(ge=..., le=...)` for numbers → a broken factory fails fast.
- Model = rules, factory = values (`fake.random_int`, `fake.numerify("#" * 10)`); `"#" * 10` ≈ `'#'.repeat(10)`.
- pydantic models take keyword arguments only (`BaseModel.__init__(self, **data)`).
- Parametrized URLs as small module functions (`_basket(id)`, `_checkout(id)` built from `_basket`).
- `Promise.all` → sequential calls when parallelism was only for speed (R2).
- `len(x)` (→ `__len__`); `assert x == []` gives a better failure diff than `len(x) == 0`.
- `re.fullmatch` returns `Match | None`; `assert re.fullmatch(...)` checks truthiness.
- Trailing ("magic") comma keeps ruff format from collapsing; `x = 1,` is a tuple.
- TS doesn't parse JSON into types (`as T` is compile-time only); property names equal JSON keys there.

### Pitfalls hit
- `mobile_num = str(Field(...))` (assignment instead of annotation); `\s{5}` pattern on street address.
- Positional args to `Address(...)` and `OrderDetails({...})`.
- `Card` class indented inside `Address` (ImportError); `card_num: int = Field(ge=16, le=16)` (value, not length; card numbers are strings).
- `exp_month=Field(ge=1, le=12)` passed as a value in the factory.
- Empty class body with only a comment; `-> .data.id` copied from my TODO shorthand.
- `{ couponData: "", order_details }` (unquoted key + shorthand, again); missing auth headers on checkout.
- `api.create_address` without `()` / argument (F401 unused factory imports was the hint).
- `assert confirmation == re.fullmatch(...)` (str vs Match → always False).
- **Recurring:** test name paraphrased (`test_empties_er`, 5th time); test placed out of TS order.
- Teacher error: referenced stale line numbers after the file changed; use method names instead.

### TS → Python gotchas
- `/api/Addresss/` (three `s`) is the real Juice Shop route; copy SUT routes/keys verbatim.
- Flagged TS issue #1 (Performance/Functional labels) kept as TODO comments.

### To revisit (weak answers)
- Why SUT constraints live in the model: "extra check" without the *broken factory fails fast* point.
- `alias_generator` + `by_alias=True`: didn't know (without it snake_case keys go to the SUT).
- `re.fullmatch` returns `Match | None`: didn't know why `== ` is always False.

## Lesson 7b — Basket isolation + UI checkout (2026-09-29)

7a took ~3h; 7b done in one go at the user's request ("finish 7 as is").

**Ported:** `tests/api/basket/isolation.spec.ts` → `tests/api/basket/test_isolation.py` (1 pass + 2 xfail);
`checkout.page.ts` → `CheckoutPage`; `tests/ui/basket/checkout.spec.ts` → `tests/ui/basket/test_checkout.py`.

### Concepts
- Module-local fixture `attacker` (user's own idea): extracts the 3× duplicated "second user" setup. Setup
  order changes vs TS (attacker before victim's seeding) without changing intent; a broken attacker setup is
  `ERROR`, not masked by `xfail(raises=AssertionError)`.
- `usefixtures("session")` to make an implicit dependency (authenticated `api`) explicit.
- Adjacent string literals concatenate at compile time; ruff format joins them back when they fit.
- `click(force=True)`; `True` / `False` / `None` are capitalized.
- Private helper for identical page-object steps while keeping the TS public method names.
- `to_have_url("...")` = exact full-URL match; `re.compile(...)` = regex search (anchors optional).

### Pitfalls hit
- Changed literal (quantity 2 vs 1).
- Draft and skeleton mixed in one file → every method declared twice (`reportRedeclaration`), empty bodies.
- `{name: ...}` options object / positional `name` in `get_by_role` (again).
- Missing `re.IGNORECASE` (`/i`), raw string instead of `re.compile` for a URL, dropped assertion.
  User asked me to apply these last three fixes ("do it yourself").

### To revisit (weak answers)
- Why `attacker` can't mask a broken setup: said "xfail only applies inside the test" (it covers setup too;
  it's the `raises` filter).
- String vs `re.compile` in `to_have_url`: thought string = substring and `re.compile` "escapes" (reversed).

## Lesson 9 — Parallelism + retries (2026-09-29)

Mode switch (interview MVP, ~4h left): Claude writes, the user reviews and asks "why".

- `pytest-xdist` (`-n 4`): workers are processes (≈ Playwright Test workers); session fixtures run per worker.
  Measured: serial 21.2s, `-n 4` 16.6s, `-n auto` (16) 26.5s → more workers ≠ faster (one browser each).
- `pytest-timeout` (`timeout = 45`, seconds) ≈ TS `timeout: 45_000`.
- `pytest-rerunfailures`: CI-only `--reruns 2` ≈ TS `retries: CI ? 2 : 0` (no reruns locally, so flakes stay visible).
- `--tracing retain-on-failure` (superset of TS `on-first-retry`, R5), screenshots/videos on failure → `test-results/`.
- Flagged TS issue #7 fixed: `mat-grid-tile mat-card` (verified with a DOM probe; the challenge notification lives
  outside the grid). Parallel sessions all receive the broadcast notification, so xdist made the flake likelier.
- Shared-SUT state: repeated checkouts drained Apple Juice stock → `400 out of stock` in 8 tests. Fix: restart the
  SUT (Juice Shop re-seeds on start); CI always starts a fresh container. Stock check precedes the auth check,
  so the isolation test saw 400 instead of 401.
