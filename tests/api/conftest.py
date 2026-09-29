import allure
import pytest


@pytest.fixture(autouse=True)
def _layer_label() -> None:
    """Tags every test under tests/api/ with its Allure layer (TS: autoLayerLabel)."""
    allure.dynamic.parent_suite("API")
    allure.dynamic.label("layer", "API")
