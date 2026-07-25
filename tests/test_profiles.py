"""Profile isolation and immutable-manifest checks."""

import copy
from dataclasses import replace

import pytest

from src.profiles import (
    DEFAULT_PROFILE_ID,
    PROJECT_ROOT,
    load_profile,
    select_profile_id,
    verified_profile_snapshot,
    verify_analysis_inputs,
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


def test_security_snapshot_and_preprint_input_match_manifest() -> None:
    with verified_profile_snapshot(
        "security-20",
        PROJECT_ROOT,
        verify_preprints=True,
    ) as verified:
        assert verified.database_path.is_file()
        assert verified.profile.manifest["snapshot"]["papers"] == 20305
        assert verified.profile.manifest["snapshot"]["venues"] == 20
        assert verified.profile.manifest["analysis_inputs"]["preprint_snapshot"]["records"] == 27749


def test_preprint_manifest_mismatch_fails_before_analysis(tmp_path) -> None:
    profile = load_profile("security-20", PROJECT_ROOT)
    wrong_input = tmp_path / "arxiv.jsonl.gz"
    wrong_input.write_bytes(b"not the frozen input")

    with pytest.raises(RuntimeError, match="size mismatch"):
        verify_analysis_inputs(replace(profile, preprint_snapshot_path=wrong_input))


def test_preprint_hash_mismatch_fails_before_analysis(tmp_path) -> None:
    profile = load_profile("security-20", PROJECT_ROOT)
    wrong_input = tmp_path / "arxiv.jsonl.gz"
    wrong_input.write_bytes(b"wrong")
    manifest = copy.deepcopy(profile.manifest)
    declaration = manifest["analysis_inputs"]["preprint_snapshot"]
    declaration["bytes"] = wrong_input.stat().st_size
    declaration["sha256"] = "0" * 64

    with pytest.raises(RuntimeError, match="SHA-256 mismatch"):
        verify_analysis_inputs(
            replace(
                profile,
                preprint_snapshot_path=wrong_input,
                manifest=manifest,
            )
        )


def test_missing_preprint_input_fails_before_analysis(tmp_path) -> None:
    profile = load_profile("security-20", PROJECT_ROOT)
    with pytest.raises(FileNotFoundError):
        verify_analysis_inputs(
            replace(profile, preprint_snapshot_path=tmp_path / "missing.jsonl.gz")
        )
