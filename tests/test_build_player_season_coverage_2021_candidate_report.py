from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "build_player_season_coverage_2021_candidate_report.py"
    )
    spec = spec_from_file_location("build_player_season_coverage_2021_candidate_report", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_candidate_payload(row_counts: dict[str, int]) -> dict:
    records = []
    for position, count in row_counts.items():
        for i in range(count):
            records.append(
                {
                    "player_id": f"00-{position}-{i}",
                    "position": position,
                    "season": 2021,
                    "season_type": "REG",
                    "coverage_status": "full_season",
                    "identity_confidence": "source_verified",
                }
            )
    return {
        "artifact_id": "player_season_coverage_2021_candidate.source_backed",
        "status": "candidate_evidence_artifact_not_promoted",
        "seasons": [2021],
        "season_type_scope": ["REG"],
        "included_positions": ["QB", "RB", "TE", "WR"],
        "records": records,
    }


_MATCHING_COUNTS = {"QB": 2, "RB": 3, "WR": 4, "TE": 1}


def test_missing_candidate_emits_inconclusive_decision() -> None:
    module = _load_module()
    report = module.build_report(None, None, [], _MATCHING_COUNTS)
    assert report["decision"] == "player_season_coverage_2021_candidate_build_inconclusive_requires_followup"
    assert report["candidate_exists"] is False


def test_validation_errors_emit_failed_decision() -> None:
    module = _load_module()
    payload = _fake_candidate_payload(_MATCHING_COUNTS)
    report = module.build_report(payload, "deadbeef", ["record[0]: missing source_refs"], _MATCHING_COUNTS)
    assert report["decision"] == "player_season_coverage_2021_candidate_build_failed_source_or_schema_check"
    assert report["validation_errors"]


def test_mismatched_counts_emit_redesign_decision() -> None:
    module = _load_module()
    payload = _fake_candidate_payload(_MATCHING_COUNTS)
    mismatched_source_counts = dict(_MATCHING_COUNTS, QB=999)
    report = module.build_report(payload, "deadbeef", [], mismatched_source_counts)
    assert report["decision"] == "player_season_coverage_2021_candidate_build_requires_source_boundary_redesign"
    assert report["reconciliation"]["counts_match"] is False


def test_no_comparison_available_emits_inconclusive_decision() -> None:
    module = _load_module()
    payload = _fake_candidate_payload(_MATCHING_COUNTS)
    report = module.build_report(payload, "deadbeef", [], None)
    assert report["decision"] == "player_season_coverage_2021_candidate_build_inconclusive_requires_followup"
    assert report["reconciliation"] is None


def test_matching_counts_and_clean_validation_emit_promotion_review_decision() -> None:
    module = _load_module()
    payload = _fake_candidate_payload(_MATCHING_COUNTS)
    report = module.build_report(payload, "deadbeef", [], _MATCHING_COUNTS)
    assert report["decision"] == "may_open_player_season_coverage_2021_promotion_review_issue"
    assert report["reconciliation"]["counts_match"] is True
    assert report["no_promoted_path_written"] is True
    assert report["identity_join_rate"] == 1.0


def test_decision_always_in_allowed_set() -> None:
    module = _load_module()
    for args in (
        (None, None, [], None),
        (_fake_candidate_payload(_MATCHING_COUNTS), "x", ["err"], _MATCHING_COUNTS),
        (_fake_candidate_payload(_MATCHING_COUNTS), "x", [], dict(_MATCHING_COUNTS, RB=0)),
        (_fake_candidate_payload(_MATCHING_COUNTS), "x", [], None),
        (_fake_candidate_payload(_MATCHING_COUNTS), "x", [], _MATCHING_COUNTS),
    ):
        report = module.build_report(*args)
        assert report["decision"] in module.ALLOWED_DECISIONS


def test_render_markdown_missing_candidate() -> None:
    module = _load_module()
    report = module.build_report(None, None, [], None)
    md = module.render_markdown(report)
    assert report["decision"] in md
    assert "not found" in md.lower()


def test_render_markdown_happy_path_contains_reconciliation_table() -> None:
    module = _load_module()
    payload = _fake_candidate_payload(_MATCHING_COUNTS)
    report = module.build_report(payload, "deadbeef", [], _MATCHING_COUNTS)
    md = module.render_markdown(report)
    assert report["decision"] in md
    assert "Reconciliation against #198" in md
    assert "not a promoted artifact" in md
