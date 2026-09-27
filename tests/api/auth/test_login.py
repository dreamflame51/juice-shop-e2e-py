import pytest

from juice_shop_e2e.api.client import JuiceShopClient

# TODO(lesson-10): allure epic "API: Authentication", category "Security"


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Known Juice Shop SQLi vulnerability: documents the expected secure behaviour",
)
def test_is_not_bypassable_via_sql_injection_in_the_email_field(api: JuiceShopClient) -> None:
    response = api.login_raw("' OR 1=1--", "anything")
    assert response.status == 401
