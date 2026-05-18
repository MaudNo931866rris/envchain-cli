"""Tests for envchain.dependency."""

from __future__ import annotations

import pytest

from envchain.dependency import (
    DependencyError,
    add_dependency,
    get_dependencies,
    list_all_dependencies,
    remove_dependency,
    resolve_order,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.dependency._store_dir", lambda: tmp_path)
    yield tmp_path


def test_add_dependency_creates_entry():
    add_dependency("app", "base")
    assert "base" in get_dependencies("app")


def test_add_dependency_idempotent():
    add_dependency("app", "base")
    add_dependency("app", "base")
    assert get_dependencies("app").count("base") == 1


def test_add_multiple_dependencies():
    add_dependency("app", "base")
    add_dependency("app", "secrets")
    deps = get_dependencies("app")
    assert "base" in deps
    assert "secrets" in deps


def test_add_self_dependency_raises():
    with pytest.raises(DependencyError, match="cannot depend on itself"):
        add_dependency("app", "app")


def test_add_empty_profile_raises():
    with pytest.raises(DependencyError, match="profile name"):
        add_dependency("", "base")


def test_add_empty_dependency_raises():
    with pytest.raises(DependencyError, match="dependency name"):
        add_dependency("app", "")


def test_remove_dependency():
    add_dependency("app", "base")
    remove_dependency("app", "base")
    assert get_dependencies("app") == []


def test_remove_missing_dependency_raises():
    with pytest.raises(DependencyError, match="does not depend on"):
        remove_dependency("app", "ghost")


def test_get_dependencies_empty_profile():
    assert get_dependencies("nonexistent") == []


def test_resolve_order_simple_chain():
    add_dependency("app", "base")
    add_dependency("base", "core")
    order = resolve_order("app")
    assert order.index("core") < order.index("base")
    assert order.index("base") < order.index("app")


def test_resolve_order_no_deps():
    order = resolve_order("standalone")
    assert order == ["standalone"]


def test_resolve_order_circular_raises():
    add_dependency("a", "b")
    add_dependency("b", "a")
    with pytest.raises(DependencyError, match="circular"):
        resolve_order("a")


def test_list_all_dependencies_empty():
    assert list_all_dependencies() == {}


def test_list_all_dependencies_populated():
    add_dependency("app", "base")
    add_dependency("svc", "shared")
    data = list_all_dependencies()
    assert "app" in data
    assert "svc" in data
