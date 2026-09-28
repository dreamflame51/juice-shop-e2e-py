# Test Catalog

Tracks every test in the suite: what it covers, the fixtures it relies on, the steps,
and the layer/category it's tagged with in Allure. Update this file whenever a test is
added, removed, or its scenario changes (project rule, see [CLAUDE.md](../CLAUDE.md)).

Legend: **Layer** = UI / API (Allure `parentSuite`, derived from the directory).
**Category** = Allure `category` label (Functional / Security / Performance).
**Fixtures** = setup that already happened before the test's first step (see
[tests/conftest.py](../tests/conftest.py)). Listed explicitly so it's clear whether a test
starts pre-authenticated/pre-seeded or drives that state itself.

Allure labels land in Lesson 10; until then the Epic/Category columns document the intent.

## UI

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
