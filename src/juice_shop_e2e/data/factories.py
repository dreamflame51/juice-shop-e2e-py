from faker import Faker
from pydantic import BaseModel, Field

from juice_shop_e2e.config import get_settings


class User(BaseModel):
    email: str
    password: str = Field(repr=False)
    security_answer: str


fake = Faker()


def build_user() -> User:
    """Unique per call so parallel workers never collide on a registered email."""
    return User(
        email=f"{fake.user_name()}.{fake.pystr(min_chars=8, max_chars=8)}@e2e.test".lower(),
        password=get_settings().test_user_password.get_secret_value(),
        security_answer=fake.word(),
    )
