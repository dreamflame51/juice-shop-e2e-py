import allure
import pytest

from juice_shop_e2e.api.client import JuiceShopClient
from juice_shop_e2e.api.models import LoginResponse
from juice_shop_e2e.data.factories import User

pytestmark = [allure.epic("API: Authentication")]


@pytest.mark.smoke
@allure.label("category", "Functional")
def test_issues_a_jwt_and_a_basket_id_for_valid_credentials(
    api: JuiceShopClient, registered_user: User
) -> None:
    response = api.login_raw(registered_user.email, registered_user.password)
    assert response.status == 200
    body = LoginResponse.model_validate(response.json())
    assert body.authentication.token.startswith("eyJ")
    assert body.authentication.umail == registered_user.email
    assert body.authentication.bid > 0


@allure.label("category", "Security")
def test_rejects_a_wrong_password_with_401_and_no_token(
    api: JuiceShopClient, registered_user: User
) -> None:
    response = api.login_raw(registered_user.email, password="wrong-password")
    assert response.status == 401
    assert "eyJ" not in response.text()


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Known Juice Shop SQLi vulnerability: documents the expected secure behaviour",
)
@allure.label("category", "Security")
def test_is_not_bypassable_via_sql_injection_in_the_email_field(api: JuiceShopClient) -> None:
    response = api.login_raw("' OR 1=1--", "anything")
    assert response.status == 401
