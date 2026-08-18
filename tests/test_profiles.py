"""Profile isolation and immutable-manifest checks."""

import sqlite3

import pytest

import src.profiles as profiles_module

from src.profiles import (
    DEFAULT_PROFILE_ID,
    PROJECT_ROOT,
    load_profile,
    select_profile_id,
    verified_profile_snapshot,
)


def test_default_profile_is_the_tool_denominator(monkeypatch) -> None:
    monkeypatch.delenv("TOPVENUES_PROFILE", raising=False)
    assert select_profile_id() == DEFAULT_PROFILE_ID == "security-20"


def test_environment_can_select_an_explicit_profile(monkeypatch) -> None:
    monkeypatch.setenv("TOPVENUES_PROFILE", "security-20")
    assert select_profile_id() == "security-20"


def test_unknown_profile_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("TOPVENUES_PROFILE", "latest")
    with pytest.raises(ValueError, match="unknown profile"):
        select_profile_id()


def test_security_snapshot_matches_manifest() -> None:
    with verified_profile_snapshot("security-20", PROJECT_ROOT) as verified:
        assert verified.database_path.is_file()
        assert verified.profile.manifest["snapshot"]["papers"] == 20305
        assert verified.profile.manifest["snapshot"]["venues"] == 20


def test_verified_snapshot_closes_database_before_temp_cleanup(monkeypatch) -> None:
    connections: list[sqlite3.Connection] = []
    original_connect = profiles_module.sqlite3.connect

    def tracked_connect(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(profiles_module.sqlite3, "connect", tracked_connect)
    with verified_profile_snapshot("security-20", PROJECT_ROOT):
        pass

    assert len(connections) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        connections[0].execute("SELECT 1")
