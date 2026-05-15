"""Tests for envchain.rating."""
import pytest

from envchain.rating import (
    RatingError,
    clear_rating,
    get_rating,
    list_ratings,
    set_rating,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.rating._store_dir", lambda: tmp_path)
    yield tmp_path


def test_set_and_get_rating():
    set_rating("myproject", 4)
    assert get_rating("myproject") == 4


def test_get_rating_returns_none_when_not_set():
    assert get_rating("ghost") is None


def test_set_rating_empty_profile_raises():
    with pytest.raises(RatingError, match="empty"):
        set_rating("", 3)


def test_set_rating_out_of_range_raises():
    with pytest.raises(RatingError, match="between"):
        set_rating("proj", 0)
    with pytest.raises(RatingError, match="between"):
        set_rating("proj", 6)


def test_set_rating_non_integer_raises():
    with pytest.raises(RatingError):
        set_rating("proj", 3.5)  # type: ignore[arg-type]


def test_set_rating_boundary_values():
    set_rating("low", 1)
    set_rating("high", 5)
    assert get_rating("low") == 1
    assert get_rating("high") == 5


def test_clear_rating_returns_true_when_existed():
    set_rating("proj", 3)
    assert clear_rating("proj") is True
    assert get_rating("proj") is None


def test_clear_rating_returns_false_when_missing():
    assert clear_rating("nonexistent") is False


def test_list_ratings_sorted():
    set_rating("zebra", 2)
    set_rating("alpha", 5)
    set_rating("mango", 3)
    result = list_ratings()
    assert list(result.keys()) == ["alpha", "mango", "zebra"]


def test_list_ratings_empty():
    assert list_ratings() == {}


def test_overwrite_rating():
    set_rating("proj", 2)
    set_rating("proj", 5)
    assert get_rating("proj") == 5
