import pytest

from juice_shop_e2e.api.client import JuiceShopClient
from juice_shop_e2e.api.models import LoginResponse
from juice_shop_e2e.data.factories import User

# TODO(lesson-10): allure epic "API: Authentication"; category label per test


@pytest.mark.smoke
def test_issues_a_jwt_and_a_basket_id_for_valid_credentials(
    api: JuiceShopClient, registered_user: User
) -> None:
    # TODO(lesson-10): category "Functional"
    response = api.login_raw(registered_user.email, registered_user.password)
    assert response.status == 200
    body = LoginResponse.model_validate(response.json())
    assert body.authentication.token.startswith("eyJ")
    assert body.authentication.umail == registered_user.email
    assert body.authentication.bid > 0


def test_rejects_a_wrong_password_with_401_and_no_token(
    api: JuiceShopClient, registered_user: User
) -> None:
    # TODO(lesson-10): category "Security"
    response = api.login_raw(registered_user.email, password="wrong-password")
    assert response.status == 401
    assert "eyJ" not in response.text()


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Known Juice Shop SQLi vulnerability: documents the expected secure behaviour",
)
def test_is_not_bypassable_via_sql_injection_in_the_email_field(api: JuiceShopClient) -> None:
    # TODO(lesson-10): category "Security"
    response = api.login_raw("' OR 1=1--", "anything")
    assert response.status == 401
