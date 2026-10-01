# Test Catalog

Tracks every test in the suite: what it covers, the fixtures it relies on, the steps,
and the layer/category it's tagged with in Allure. Update this file whenever a test is
added, removed, or its scenario changes.

Legend: **Layer** = UI / API (Allure `parentSuite`, derived from the directory).
**Category** = Allure `category` label (Functional / Security / Performance).
**Fixtures** = setup that already happened before the test's first step (see
[tests/conftest.py](../tests/conftest.py)). Listed explicitly so it's clear whether a test
starts pre-authenticated/pre-seeded or drives that state itself.

Epic/category come from `pytestmark` / `@allure.label` in each module; the layer from an autouse
fixture in `tests/api/conftest.py` / `tests/ui/conftest.py`. Every API call is an Allure step with
request/response attachments (`JuiceShopClient._call`).

## UI

### `tests/ui/auth/test_login.py` — Login
Epic: `UI: Authentication`

| Test | Category | Fixtures | Steps |
|---|---|---|---|
| `smoke` `test_a_registered_user_can_log_in` | Functional | `registered_user` (API-registers a fresh user before the test starts), `login_page`, `page` | Open login page → submit `registered_user`'s valid credentials → assert redirect to `#/search` and account nav visible (inline `#navbarAccount` locator kept as in TS, flagged issue #4) |
| `test_rejects_invalid_credentials_without_revealing_whether_the_account_exists` | Security | `registered_user` (API-registered), `login_page`; a second, wholly unregistered user is built inline with `build_user()` | Two steps sharing the same assertion: (1) log in with `registered_user`'s email + wrong password → assert generic "invalid email or password" error; (2) log in with a never-registered email → assert the identical generic error |

### `tests/ui/auth/test_registration.py` — Registration
Epic: `UI: Authentication`

| Test | Category | Fixtures | Steps |
|---|---|---|---|
| `smoke` `test_a_new_customer_can_register_and_then_log_in` | Functional | `test_user` (factory-built, **not** registered: registration itself is under test), `registration_page`, `login_page`, `page` | Open registration page → register `test_user` through the UI form → assert redirect to `#/login` → log in with the same credentials → assert redirect to `#/search` |
| `test_blocks_submission_when_the_repeated_password_does_not_match` | Functional | `test_user` (factory-built), `registration_page` | Fill email/password with a mismatched repeat password → assert submit button stays disabled |

### `tests/ui/basket/test_add_to_basket.py` — Basket
Epic: `UI: Shopping`

| Test | Category | Fixtures | Steps |
|---|---|---|---|
| `smoke` `test_an_authenticated_user_can_add_a_product_to_the_basket` | Functional | `authed_page` via `usefixtures` (registers + logs in a user via the API, injects the session token, no UI login); `products_page`, `basket_page` | Open products page → add product from catalogue → assert snackbar confirmation → open basket → assert row/quantity/checkout button state (quantity regex `/1/` is weak, flagged issue #2) |
| `test_basket_seeded_through_the_api_is_reflected_in_the_ui` | Functional | `authed_page` via `usefixtures`; `api` + `session` used mid-test to seed the basket; `basket_page` | Seed 2 units via `api.add_to_basket(session.basket_id, ...)` → open basket UI → assert quantity reflects the API-seeded state (regex `/2/`, flagged issue #2) |

### `tests/ui/basket/test_checkout.py` — Checkout
Epic: `UI: Shopping`

| Test | Category | Fixtures | Steps |
|---|---|---|---|
| `smoke` `test_a_user_can_complete_checkout_end_to_end` | Functional | `authed_page` (registers + logs in a user via the API, no UI login); `session` via `usefixtures` (keeps `api` authenticated); `api` used mid-test to seed address/card; `products_page`, `basket_page`, `checkout_page` | Seed a delivery address + payment card via `api.create_address` / `api.create_card` → add product via UI → open basket → go to checkout → select address → select delivery method → select payment → place order → assert confirmation heading and `#/order-completion/<id>` URL |

### `tests/ui/products/test_search.py` — Product search
Epic: `UI: Shopping`

| Test | Category | Fixtures | Steps |
|---|---|---|---|
| `smoke` `test_returns_only_products_matching_the_search_term` | Functional | `products_page` (anonymous catalogue browsing, no auth needed) | Open the catalogue → search "apple" via `products_page.search()` → assert exactly 2 results, matching "Apple Juice" and "Apple Pomace" |
| `test_shows_a_no_results_state_for_a_term_that_matches_nothing` | Functional | `products_page` | Open the catalogue → search a nonsense term → assert the "No results found" message is visible |

## API

### `tests/api/auth/test_login.py` — Auth API
Epic: `API: Authentication`

| Test | Category | Fixtures | Steps |
|---|---|---|---|
| `smoke` `test_issues_a_jwt_and_a_basket_id_for_valid_credentials` | Functional | `registered_user` (API-registered) | `POST /rest/user/login` with valid credentials → assert 200, parse into `LoginResponse`, JWT shape (`eyJ` prefix), `umail` equals the user's email, basket id > 0 |
| `test_rejects_a_wrong_password_with_401_and_no_token` | Security | `registered_user` (API-registered) | `POST /rest/user/login` with a wrong password → assert 401 and no token (`eyJ`) leaked in the body |
| `test_is_not_bypassable_via_sql_injection_in_the_email_field` | Security | `api` (no user needed; the payload targets the email field itself) | `POST /rest/user/login` with a SQLi payload in the email field → asserts 401 (documents expected-secure behaviour; `xfail(strict=True, raises=AssertionError)` since the known-vulnerable SUT accepts the payload) |

### `tests/api/basket/test_checkout.py` — Checkout API
Epic: `API: Shopping`

| Test | Category | Fixtures | Steps |
|---|---|---|---|
| `smoke` `test_completes_an_order_end_to_end_and_returns_a_confirmation` | Performance (flagged TS issue #1, ported as-is) | `api` + `session` (registers + logs in a user, authenticates the `api` client) | Add product to basket via `api.add_to_basket` → assert basket has 1 product with quantity 2 → create address + card (sequential, was `Promise.all`) → `POST checkout` → assert confirmation id format |
| `test_empties_the_basket_once_the_order_is_placed` | Performance + Functional (two labels, flagged TS issue #1) | `api` + `session` | Add product → create address + card → check out → assert basket is empty afterward |

### `tests/api/basket/test_isolation.py` — Basket isolation between users
Epic: `API: Shopping`

| Test | Category | Fixtures | Steps |
|---|---|---|---|
| `test_rejects_adding_items_to_another_users_basket` | Security | `session` (victim, API-registered + logged in); `attacker` (module fixture: a second user registered + logged in with its own client; inline in TS) | Attacker calls `add_to_basket_raw` against the victim's `basket_id` → assert `401` |
| `test_does_not_let_another_user_read_a_victims_basket_contents` | Security | `api` + `session` (victim); `attacker` | Victim adds an item to their own basket → attacker calls `get_basket_raw` against the victim's `basket_id` → asserts `403` (documents expected-secure behaviour; `xfail(strict=True, raises=AssertionError)` since the known-vulnerable SUT returns `200` with the victim's basket) |
| `test_does_not_let_another_user_check_out_a_victims_basket` | Security | `api` + `session` (victim); `attacker`, who creates their own address/card | Victim adds an item to their own basket → attacker calls `checkout_raw` against the victim's `basket_id` with the attacker's own address/card → asserts `403` (`xfail(strict=True, raises=AssertionError)` since the known-vulnerable SUT returns `200` and completes the order) |

### `tests/api/basket/test_concurrency.py` — Basket concurrency
Epic: `API: Shopping`

| Test | Category | Fixtures | Steps |
|---|---|---|---|
| `smoke` `test_concurrent_adds_of_the_same_product_are_not_lost` | Functional | `api` + `session` (registers + logs in a user); `base_url` (the raw requests bypass Playwright) | Fire 5 identical `POST /api/BasketItems/` (qty 1) at once via `post_json_concurrently` (stdlib `urllib` threads released by a barrier: sync Playwright can't be shared across threads, R1) → assert all 200 → assert basket quantities sum to 5 (`xfail(strict=True, raises=AssertionError)`: the SUT races on the "row exists" check, 1 × 200 + 4 × 500; non-deterministic in theory, flagged TS issue #3) |

## Perf (k6)

### `tests/perf/checkout.js`
Copied unchanged from the TS project (k6 is JS by design, not a porting target). Nightly only, run
outside pytest against the Dockerized SUT; `.env` is exported so the script sees `__ENV.BASE_URL` /
`__ENV.TEST_USER_PASSWORD`.

| Scenario | Steps | Thresholds |
|---|---|---|
| Stateful checkout under ramping load (0→10→0 VUs over ~2m) | Register → login → think time → add to basket (spread across in-stock SKUs) → think time → create address + card → checkout → record `checkout_duration` | `http_req_failed` rate < 1%, `http_req_duration` p95 < 250ms, `checkout_duration` p95 < 300ms, checks rate > 99% |
