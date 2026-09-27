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

## API

### `tests/api/auth/test_login.py` — Auth API
Epic: `API: Authentication`

| Test | Category | Fixtures | Steps |
|---|---|---|---|
| `test_is_not_bypassable_via_sql_injection_in_the_email_field` | Security | `api` (no user needed; the payload targets the email field itself) | `POST /rest/user/login` with a SQLi payload in the email field → asserts 401 (documents expected-secure behaviour; `xfail(strict=True, raises=AssertionError)` since the known-vulnerable SUT accepts the payload) |
