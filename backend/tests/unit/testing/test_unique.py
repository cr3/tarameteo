"""Unit tests for the unique testing module."""

import enum

import pytest
from hamcrest import (
    assert_that,
    has_properties,
    is_,
)
from sqlalchemy.types import (
    BigInteger,
    Boolean,
    Enum,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    Unicode,
    UnicodeText,
)

from ...models import (
    DefaultTest,
    ForeignKeyTest,
    NotNullableTest,
    NullableTest,
    ServerDefaultTest,
)


class StubEnum(enum.Enum):
    """Stub enum."""

    TEST = enum.auto()


@pytest.mark.parametrize(
    "column_type, matches",
    [
        (BigInteger(), is_(int)),
        (Boolean(), True),
        (Enum(StubEnum), StubEnum.TEST),
        (Integer(), is_(int)),
        (LargeBinary(), is_(bytes)),
        (SmallInteger(), is_(int)),
        (String(), is_(str)),
        (Text(), is_(str)),
        (Unicode(), is_(str)),
        (UnicodeText(), is_(str)),
    ],
)
def test_unique_db_value(column_type, matches, unique):
    """A unique db-value should return a valid value."""
    result = unique("db-value", column_type)

    assert_that(result, matches)


def test_unique_db_value_error(unique):
    """An invalid db-value should raise a ValueError."""
    with pytest.raises(ValueError):
        unique("db-value", None)


@pytest.mark.parametrize(
    "model, matches",
    [
        (DefaultTest, has_properties(value=is_(None))),
        (ForeignKeyTest, has_properties(value=is_(None))),
        (NotNullableTest, has_properties(value=is_(str))),
        (NullableTest, has_properties(value=is_(None))),
        (ServerDefaultTest, has_properties(value=is_(None))),
    ],
)
def test_unique_db_model(model, matches, unique):
    """A unique db-model should return a valid model."""
    result = unique("db-model", model)

    assert_that(result, matches)
