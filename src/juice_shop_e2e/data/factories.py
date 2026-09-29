from faker import Faker
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from juice_shop_e2e.config import get_settings


class User(BaseModel):
    email: str
    password: str = Field(repr=False)
    security_answer: str


class Address(BaseModel):
    """Delivery address as the SUT expects it (camelCase on the wire)."""

    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    full_name: str
    mobile_num: str = Field(pattern=r"^\d{10}$")
    zip_code: str = Field(pattern=r"^\d{5}$")
    street_address: str
    city: str
    state: str
    country: str


class Card(BaseModel):
    """Payment card as the SUT expects it (camelCase on the wire)."""

    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    full_name: str
    card_num: str = Field(pattern=r"^\d{16}$")
    exp_month: int = Field(ge=1, le=12)
    # Juice Shop hardcodes a minimum expYear of 2080 server-side (unrelated to the current date).
    exp_year: int = Field(ge=2080, le=2099)


fake = Faker()


def build_user() -> User:
    """Unique per call so parallel workers never collide on a registered email."""
    return User(
        email=f"{fake.user_name()}.{fake.pystr(min_chars=8, max_chars=8)}@e2e.test".lower(),
        password=get_settings().test_user_password.get_secret_value(),
        security_answer=fake.word(),
    )


def build_address() -> Address:
    return Address(
        full_name=fake.name(),
        mobile_num=fake.numerify("#" * 10),
        zip_code=fake.numerify("#####"),
        street_address=fake.street_address(),
        city=fake.city(),
        state=fake.state(),
        country=fake.country(),
    )


def build_card() -> Card:
    return Card(
        full_name=fake.name(),
        card_num=fake.numerify("4###########1111"),
        exp_month=fake.random_int(min=1, max=12),
        exp_year=fake.random_int(min=2080, max=2099),
    )
