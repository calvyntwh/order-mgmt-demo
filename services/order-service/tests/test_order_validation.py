import pytest
from pydantic import ValidationError

from app.orders import CreateOrderIn


def test_invalid_item_name():
    with pytest.raises(ValidationError):
        CreateOrderIn(item_name="", quantity=1)

def test_invalid_quantity():
    with pytest.raises(ValidationError):
        CreateOrderIn(item_name="widget", quantity=0)
    with pytest.raises(ValidationError):
        CreateOrderIn(item_name="widget", quantity=101)

def test_invalid_notes():
    with pytest.raises(ValidationError):
        CreateOrderIn(item_name="widget", quantity=1, notes="x"*1001)
