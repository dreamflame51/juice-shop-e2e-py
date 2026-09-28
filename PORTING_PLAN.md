# Porting Plan — juice-shop-e2e (TS) → juice-shop-e2e-py

Source (read-only): `C:\Users\salni\Documents\juice-shop-e2e`
Target: `C:\Users\salni\Documents\juice-shop-e2e-py`
Same SUT (Juice Shop v17.1.1 via Docker Compose), same `.env` keys, same coverage and assertions.

---

## 1. Target stack

| Concern | Choice | Note |
|---|---|---|
| Runtime / deps | Python 3.12 (pinned in `.python-version`), `uv`, `pyproject.toml` | 3.14 is installed locally; 3.12 is the brief's floor and the safest for wheel availability. uv downloads it. |
| Runner | `pytest` + `pytest-playwright` (**sync API**) | see §5 |
| API | Playwright `APIRequestContext` | TS uses Playwright's `request`, not a separate client → no reason for httpx. One exception, see Risk R1. |
| Models | `pydantic` v2 | replaces TS `interface` + `as T` casts with real runtime validation |
| Config | `pydantic-settings` | reads `.env` natively → no `python-dotenv` needed |
| Test data | `faker` | same role as `@faker-js/faker` |
| Lint/format | `ruff` | replaces ESLint (+ Prettier) |
| Types | `pyright` (`strict` for `src/`, `standard` for `tests/`) | replaces `tsc --noEmit` |
| Parallel | `pytest-xdist` | replaces `fullyParallel` workers |
| Reporting | `allure-pytest` → results; **Allure 3 Node CLI** (`npx allure@3.14.3`) → HTML | see Risk R4 |
| Perf | k6 script copied **unchanged** | k6 is JS by design; not a porting target |

Extra deps beyond the brief (approved; each gets a short why/alternative note in its lesson):
- `pytest-rerunfailures` — TS `retries: CI ? 2 : 0`. pytest has no built-in retries.
- `pytest-timeout` — TS `timeout: 45_000` per test. pytest has no built-in test timeout. Alternative: none (Playwright action timeouts only bound single actions).
- Sharding across CI machines (`--shard=1/4`): `pytest-split` **or** zero-dep matrix by directory. Decide in Lesson 10.

---

## 2. Architecture map

| TS | Python | Why it changes shape |
|---|---|---|
| `package.json` scripts | `pyproject.toml` + a few documented `uv run ...` commands | no npm-scripts equivalent in uv; keep commands in README |
| `playwright.config.ts` | `[tool.pytest.ini_options]` (`addopts`, `markers`) + root `conftest.py` (`base_url`, `browser_context_args`, `expect.set_options`) | pytest-playwright config = CLI flags + fixtures, not a config object |
| `tsconfig.json` | `[tool.pyright]` | |
| `eslint.config.js` | `[tool.ruff]` | `waitForTimeout` ban has no ruff rule → Risk R6 |
| `src/utils/config.ts` | `src/juice_shop_e2e/config.py` | `Settings(BaseSettings)` + cached accessor |
| `src/api/juice-shop.client.ts` | `src/juice_shop_e2e/api/client.py` + `api/models.py` | models split out; pydantic parses responses |
| `src/data/*.factory.ts` | `src/juice_shop_e2e/data/factories.py` | 3 tiny factories → one module (Python favours fewer, bigger modules) |
| `src/pages/*.page.ts` | `src/juice_shop_e2e/pages/{login,registration,products,basket,checkout}_page.py` | snake_case module names |
| `src/utils/wait.ts` | `src/juice_shop_e2e/utils/wait.py` | |
| `src/fixtures/test.ts` | `tests/conftest.py` (shared) + `tests/ui/conftest.py` (page objects, cookies) + `tests/api/conftest.py` | conftest **hierarchy** replaces one `test.extend` object; directory scoping replaces `layerFromFile` regex |
| `tests/{ui,api}/**/*.spec.ts` | `tests/{ui,api}/**/test_*.py` | pytest discovery convention |
| `tests/perf/checkout.js` | copied verbatim | |
| `docker-compose.yml`, `.env.example`, `allurerc.mjs` | copied verbatim | one `.env` source of truth kept |
| `.github/**` | rewritten for `uv` (`astral-sh/setup-uv`) | |
| `docs/test-catalog.md`, `CLAUDE.md` | ported with Python paths/fixture names | catalog HARD RULE carries over |

`src/` layout with an installed package (`juice_shop_e2e`) — so tests import `from juice_shop_e2e.pages...` with no `sys.path` hacks (the Python equivalent of `../../../src/...` relative imports).

---

## 3. Concept map

| TS / Playwright Test | Python / pytest | Gotcha |
|---|---|---|
| `base.extend<Fixtures>({...})` | `@pytest.fixture` functions in `conftest.py` | no central type — each fixture is a function; pytest injects by **parameter name** |
| `async ({dep}, use) => { setup; await use(x); teardown }` | `def f(dep): setup; yield x; teardown` | `yield` = `use()`; return type `Iterator[X]` / `Generator[X]` |
| fixture scope (test/worker) | `scope="function" \| "session"` (+ `module`, `class`, `package`) | under xdist, `session` = per worker (≈ TS `worker` scope) |
| `{ auto: true }` | `@pytest.fixture(autouse=True)` | autouse applies per conftest directory → natural layer labelling |
| overriding built-in `context` | define `context(context)` in conftest | same-name override receives the parent fixture |
| `request` fixture (API) | own `api_request_context` fixture from `playwright.request.new_context()` | **name clash**: `request` in pytest is `FixtureRequest` |
| `use: { baseURL }` | override session-scoped `base_url` fixture from `Settings` | keeps `.env` as the only source |
| `interface TestUser` | `pydantic.BaseModel` (data crossing a boundary) / `Protocol` (behaviour) / `TypedDict` (raw dicts) | choose by purpose, not 1:1 |
| `await response.json() as T` | `Model.model_validate(response.json())` | TS cast lies silently; pydantic raises → stricter, may surface real mismatches |
| `as const` endpoint map | module-level `Final` constants / small functions | no need for a class |
| `async/await` | plain calls (sync API) | `Promise.all([...])` → sequential calls unless concurrency *is* the intent (R1) |
| `'A' \| 'B'` unions | `Literal["A", "B"]` or `enum.StrEnum` | |
| `test.describe('X')` | `class TestX:` (no `__init__`) or just the module | |
| `beforeEach(() => allure.epic(...))` | `@allure.epic(...)` on the class | decorators, not hooks |
| `@smoke` in title + `--grep` | `@pytest.mark.smoke` + `-m smoke`, `--strict-markers` | typo in marker = error, unlike a grep |
| `test.fail()` | `@pytest.mark.xfail(strict=True, raises=AssertionError, reason=...)` | see R3 |
| `projects: [chromium]` | `--browser chromium` in `addopts` | |
| `trace: 'on-first-retry'` | `--tracing retain-on-failure` | no "on first retry" option (R5) |
| `expect.timeout` | `expect.set_options(timeout=10_000)` | |
| `forbidOnly` | n/a | pytest has no `.only` |
| `allure.step(name, fn)` | `with allure.step(name):` | context manager, not callback |
| `allure.attachment(...)` | `allure.attach(body, name, attachment_type)` | |
| `devices['Desktop Chrome']` | `browser_context_args` / `--device` | |
| fixture used only for side effect (`authedPage` unused) | `@pytest.mark.usefixtures("authed_page")` | avoids "unused parameter" |

---

## 4. Lessons (≤ ~1h each, one concept cluster)

| # | Slice | Python concepts | Ported TS |
|---|---|---|---|
| 1 | Bootstrap + config | uv project, `src` layout, `pyproject.toml`, ruff/pyright config, pydantic-settings, `SecretStr`, `lru_cache` | `package.json`, `tsconfig`, eslint, `config.ts`, `.env.example`, compose |
| 2 | First API test | pytest discovery, first fixtures (`api_request_context`, `base_url`), `yield` teardown, `xfail(strict)` | `api/auth` SQLi test + `login_raw` |
| 3 | Typed API client + models | pydantic models, `model_validate`, custom exception, properties, `Literal` | auth part of `juice-shop.client.ts` (`register`, `login`), rest of `tests/api/auth` (+ minimal `build_user`) |
| 4 | First UI test | pytest-playwright `page`/`context`, overriding `context`, `browser_context_args`, sync `expect` | `tests/ui/products/search` |
| 5 | Page objects | classes without assertions, `Locator` typing, `time.monotonic` retry loop, narrow `except` | `login`/`registration` pages, `wait.ts`, `ui/auth/*` (basket/checkout pages + rest of `ProductsPage` → Lessons 6–7) |
| 6 | Fixture graph + auth | dependency chain `test_user → registered_user → session → authed_page`, scopes, conftest hierarchy, `usefixtures` | `fixtures/test.ts`, `ui/basket/add-to-basket` |
| 7 | Data builders | faker, pydantic `Field` constraints for SUT rules, per-worker uniqueness | factories, basket/address/card client methods + models, `api/basket/checkout`, `api/basket/isolation`, `ui/basket/checkout` |
| 8 | Real concurrency | GIL vs I/O, threads vs asyncio, Playwright thread-affinity | `api/basket/concurrency` (R1) |
| 9 | Parallelism + retries | pytest-xdist, worker ids, markers, rerunfailures, timeout | playwright.config parallel/retries |
| 10 | Reporting | allure-pytest, autouse layer label, epic/category decorators, steps, attachments | `autoLayerLabel`, Allure calls across specs, `allurerc.mjs` |
| 11 | CI | setup-uv, caching, smoke on PR, sharded nightly, Allure history, k6 job | `.github/**` |

Allure tags are *required* by project rules, but land in Lesson 10. Until then specs carry `# TODO(lesson-10)` — deliberate, so reporting is learned as one cluster. Catalog (`docs/test-catalog.md`) is updated in every lesson that adds specs.

---

## 5. Why sync over async

- pytest calls test functions synchronously. Async tests need `pytest-asyncio` (or anyio) plus event-loop scope configuration — extra moving parts with no benefit.
- Test steps are strictly sequential (`click` → `expect` → `click`). async buys nothing when every line awaits the previous one.
- The sync API is the same driver underneath (greenlet bridge over the async core) — no speed penalty for serial steps.
- Parallelism comes from **processes** (xdist), not coroutines — same model as Playwright Test workers.
- Cost: no cheap in-test fan-out like `Promise.all`. Only one test actually needs it (R1).

---

## 6. Risks — things that don't translate 1:1

| # | Risk | Plan |
|---|---|---|
| R1 | `concurrency.spec.ts` fires 5 requests via `Promise.all`. Sync Playwright objects are bound to their creating thread → can't be called concurrently. A sequential loop would silently **destroy the test's intent** (no race = different test). | Lesson 8: isolated raw-call helper using `async_playwright` + `asyncio.gather` run in its own thread (zero new deps), vs `httpx` + `ThreadPoolExecutor` (new dep). Decide there. |
| R2 | Other `Promise.all` (address + card) | Sequential in Python. Not intent-relevant — parallelism there was only speed. |
| R3 | `test.fail()` is called **mid-test** (after setup), so a setup crash is a real failure. `xfail` covers the whole test → a broken setup would be hidden as "expected fail". | `raises=AssertionError` + client raises its own `ApiError`, not `AssertionError`. `strict=True` so an unexpected pass fails (same as TS). |
| R4 | Allure 3 generator is Node-only; Python has allure-pytest (results) but no Allure 3 CLI. | **Decided:** allure-pytest collects results; Node is kept **only** for `npx allure@3.14.3` HTML generation (pinned). Rejected: Allure 2 (needs a JRE), pytest-html (no history/trends/grouping), ReportPortal (needs its own server). |
| R5 | `trace: on-first-retry` has no pytest-playwright equivalent. | `--tracing retain-on-failure` (superset). |
| R6 | ESLint bans `waitForTimeout`; ruff can't ban a *method call* (TID251 bans imports/attributes by full path only). | CI grep step (`wait_for_timeout` / `time.sleep` in `tests/` + `src/`) — tiny, explicit. |
| R7 | faker API differs: no `petName`, `creditCardNumber(pattern)`, `zipCode('#####')`. | `numerify('#####')`, `numerify('4###########1111')`; `securityAnswer` → any random word (value is irrelevant, only non-empty). Keep healed constraints: 5-digit zip, `exp_year` 2080–2099. |
| R8 | TS `required()` rejects empty strings; pydantic-settings accepts `TEST_USER_PASSWORD=` (the `.env.example` default!) as valid `""`. | `min_length=1` on the field. Literal port = silent bug. |
| R9 | `session` fixture **mutates** `api` (login stores token). Hidden coupling: `api` is authed only if `session` is also requested. | Preserve behaviour, document it in the fixture docstring. Revisit only if you want. |
| R10 | Name clash `request` (pytest) vs `request` (Playwright). | `api_request_context`. |
| R11 | Sharding (`--shard=N/4`) is not built into pytest. | Lesson 11 decision (pytest-split vs directory matrix). |

---

## 7. Flagged TS issues — preserved as-is unless you decide otherwise

Per the rules: ported faithfully, not silently fixed.

1. **Wrong/duplicate category** — `tests/api/basket/checkout.spec.ts`: `beforeEach` labels `category=Performance`; the second test adds `Functional` → that test carries **two** category labels, and the smoke test (functional e2e flow) is labelled Performance. Likely a bug. → **Ignored for now**; ported as-is.
2. **Weak assertion** — `ui/basket/add-to-basket.spec.ts`: `toHaveText(/1/)` / `/2/` match any text containing the digit (`"10"`, `"12"`). Anchored `^\s*1\s*$` would be precise.
3. **Inherently flaky xfail** — `api/basket/concurrency.spec.ts`: the race is non-deterministic; if all 5 requests happen to serialize, `test.fail()` flips to an unexpected pass → red build. Same in Python with `strict=True`.
4. **Locator in a spec** — `ui/auth/login.spec.ts` uses `page.locator('#navbarAccount')` inline → violates "specs don't own locators". Candidate for a nav/header page object.
5. **Dead branch** — `layerFromFile` returns `'Perf'`, but perf never runs through Playwright (YAGNI). Not ported.
6. **`clickUntilVisible` catches every error**, not only timeouts → a real error (detached element, wrong selector) is retried until the deadline. Python port catches `playwright.sync_api.TimeoutError` only — this narrows behaviour; flag in Lesson 5.

---

## 8. Definition of done per lesson

`uv run ruff check .` · `uv run ruff format --check .` · `uv run pyright` · `uv run pytest` green (xfails expected) · catalog updated · `LEARNING_LOG.md` entry · one commit.
