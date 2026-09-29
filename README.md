# 🧃 Juice Shop E2E — Python

End-to-end UI + API automation against [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/),
written in **Python 3.12 + pytest + Playwright**, reported through **Allure 3** and gated in
**GitHub Actions**.

It is a deliberate, test-for-test port of a TypeScript/Playwright suite: same SUT, same `.env`, same
coverage and assertions — rebuilt with idiomatic Python rather than translated line by line.
Every test is listed in the **[test catalog](docs/test-catalog.md)**.

## Stack

| Concern | Tool | Why |
|---|---|---|
| Runtime / deps | Python 3.12, [uv](https://docs.astral.sh/uv/), `pyproject.toml` + `uv.lock` | fast, reproducible (`uv sync --locked` ≈ `npm ci`) |
| Runner | pytest + pytest-playwright (**sync API**) | tests are sequential steps; parallelism comes from processes |
| API | Playwright `APIRequestContext` | one HTTP stack for UI and API |
| Models | pydantic v2 | responses are **validated at runtime** (TS `as T` only trusts) |
| Config | pydantic-settings | `.env` → typed `Settings`, password as `SecretStr` |
| Test data | faker | unique data per test, no static fixtures |
| Lint / types | ruff, pyright (`strict` for `src/`) | replaces ESLint + `tsc --noEmit` |
| Parallel / resilience | pytest-xdist, pytest-rerunfailures, pytest-timeout | TS workers / `retries` / `timeout` |
| Reporting | allure-pytest → **Allure 3** HTML (`npx allure@3.14.3`) | trends + flaky history, no JRE |
| Load | k6 (script shared with the TS project) | |
| SUT | Docker Compose (`bkimminich/juice-shop:v17.1.1`) | |

## Getting started

Prerequisites: [uv](https://docs.astral.sh/uv/getting-started/installation/), Docker, Node 20+ (only
for the Allure HTML generator).

```powershell
uv sync                                   # creates .venv, installs Python 3.12 + deps from uv.lock
uv run playwright install chromium
create local .env file                    # then set TEST_USER_PASSWORD
docker compose up -d --wait               # start Juice Shop, wait for healthy
uv run pytest
```

`.env` is the single source of truth for the base URL, SUT port and test-user password — `Settings`,
`docker-compose.yml` and k6 all read it. Nothing environment-specific is hardcoded.

> Juice Shop keeps state (e.g. product stock) until restarted. For a clean run: `docker compose restart`.
> CI always starts a fresh container.

## Commands

| Command | What it does |
|---|---|
| `uv run pytest` | full suite, 4 xdist workers |
| `uv run pytest -m smoke` | smoke subset — the PR gate |
| `uv run pytest tests/api` / `tests/ui` | one layer |
| `uv run pytest -n 0 --headed tests/ui/auth` | serial, visible browser (debugging) |
| `uv run playwright show-trace test-results/<test>/trace.zip` | inspect a failed test's trace |
| `npx allure@3.14.3 generate allure-results` | build the Allure report into `allure-report/` |
| `npx allure@3.14.3 open allure-report` | serve the report |
| `uv run ruff check .; uv run ruff format --check .; uv run pyright` | static checks |

## Layout

```
src/juice_shop_e2e/          installed package (src layout: tests import the installed code, no sys.path hacks)
  config.py                  Settings (pydantic-settings), cached get_settings()
  api/client.py              JuiceShopClient: *_raw methods return responses; plain methods raise ApiError
  api/models.py              pydantic request/response models
  data/factories.py          User / Address / Card models (SUT rules as Field constraints) + faker builders
  pages/                     page objects — locators and actions only, no assertions
  utils/wait.py              click_until_visible (monotonic deadline, retries only on timeouts)
tests/
  conftest.py                shared fixtures: base_url, api_request_context, api, test_user → registered_user → session
  api/conftest.py            Allure layer label for API tests
  ui/conftest.py             context override (banner/cookie dismissal), authed_page, page-object fixtures, layer label
  api/**, ui/**              tests (assertions + orchestration only)
  perf/checkout.js           k6 load scenario
```

## Design decisions worth knowing

- **Fixture graph instead of `test.extend`.** `test_user → registered_user → session → authed_page`;
  pytest injects by parameter name and builds each fixture once per test, so page objects and the API
  client share the same authenticated `page` / client. Side-effect-only fixtures use `usefixtures`.
- **Directory-scoped conftests replace path regexes.** The Allure layer label is an autouse fixture in
  `tests/api/conftest.py` / `tests/ui/conftest.py`, not a regex over the file path.
- **Known vulnerabilities as strict xfails.** `xfail(strict=True, raises=AssertionError)`: only the final
  assertion may fail; a broken setup raises `ApiError` and stays red; a fixed vulnerability (XPASS)
  fails the build.
- **Validation at the boundary.** pydantic models parse every response and encode SUT rules
  (5-digit zip, 16-digit card, `expYear` ≥ 2080), so a broken factory fails fast with a precise message.
- **Every API call is an Allure step** with request/response attachments (`JuiceShopClient._call`).
- **Parallelism is measured, not assumed.** Locally 4 workers were fastest (16 were slower than serial:
  one browser per worker). CI uses `-n auto` and `--reruns 2`; no reruns locally so flakes stay visible.
- **No hardcoded waits.** Web-first `expect` for UI; a CI grep bans `wait_for_timeout` / `time.sleep`.

## Flagged TypeScript issues

Ported faithfully and documented instead of silently "fixed":
duplicate `category` label in the API checkout spec (#1), weak `/1/` quantity regex (#2), inherently flaky
concurrency xfail (#3), inline locator in a spec (#4), catch-all retry in `clickUntilVisible` (#6, narrowed to
timeouts here). **#7 was fixed**: a bare `mat-card` locator also matched Juice Shop's "challenge solved"
notification — parallel runs made it flaky.

## CI

| Workflow | Trigger | Jobs |
|---|---|---|
| `pr.yml` | pull request | ruff + format + pyright + hardcoded-wait grep; smoke suite on a fresh SUT; Allure preview on gh-pages |
| `nightly.yml` | 02:00 daily | full suite sharded by layer (`api` / `ui`); k6 load test; merged Allure report with persisted history |

Required secret: `TEST_USER_PASSWORD`.

## Status

All TypeScript specs are ported except `api/basket/concurrency.spec.ts` (5 truly concurrent requests; sync
Playwright objects are thread-bound, so it needs an `asyncio` or thread-pool helper).
