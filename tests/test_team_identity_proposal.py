"""Checks of Data #267's inactive proposal; never a promotion gate."""
import csv
import io
import json
from copy import deepcopy
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location('team_audit', ROOT / 'scripts/audit_team_identity_proposal.py')
audit = module_from_spec(spec)
spec.loader.exec_module(audit)


def inputs():
    raw = audit.read_inputs()
    p = audit.prior
    return [json.loads(raw[x]) for x in [p.CANDIDATES, p.CROSSWALK, p.COVERAGE]] + [list(csv.DictReader(io.StringIO(raw[p.CONFLICTS].decode())))]


def test_replay_inert_exact_edges_and_scope():
    report = audit.build_report()
    assert report == json.loads((ROOT / audit.REPORT).read_text())
    assert report['consumer_allowed'] is False
    assert report['operator_admission_decision'] is None
    assert report['proposed_permission_delta']['effective_admission'] is False
    assert report['proposed_permission_delta']['add_identity_edges_only'] == audit.EDGES
    assert report['identity']['existing_records'] == 72
    assert report['identity']['resulting_count_if_later_promoted'] == 75
    assert report['proposed_permission_delta']['scope_to_preserve_if_later_accepted'] == json.loads((ROOT / audit.RECEIPT).read_text())['consumer_scope']


def test_virtual_v2_preserves_all_existing_rows():
    args = inputs()
    before = deepcopy(args[1])
    rows = audit.prior.inspect_identities(*args)
    ps = spec_from_file_location('promoter', ROOT / 'scripts/promote_identity_crosswalk_rows.py')
    promoter = module_from_spec(ps)
    ps.loader.exec_module(promoter)
    virtual = deepcopy(before)
    virtual['records'] += rows
    virtual['record_count'] += 3
    virtual['record_count_by_match_method']['name_exact'] += 3
    promoter.validate_artifact(virtual)
    assert args[1] == before
    assert all(r['confidence'] == 'medium' and r['match_method'] == 'name_exact' for r in rows)


@pytest.mark.parametrize('sid', list(audit.EDGES))
@pytest.mark.parametrize('kind', ['candidate', 'reverse', 'promoted', 'conflict'])
def test_each_edge_rejects_collisions(sid, kind):
    args = inputs()
    row = deepcopy(next(r for r in args[0]['rows'] if r['sleeper_id'] == sid))
    if kind in ['candidate', 'reverse']:
        if kind == 'reverse':
            row['sleeper_id'] = 'synthetic-other'
        args[0]['rows'].append(row)
    elif kind == 'promoted':
        args[1]['records'].append({'provider_player_id': sid, 'tiber_player_id': row['tiber_player_id']})
    else:
        args[3].append({'player_id': row['tiber_player_id']})
    with pytest.raises(ValueError):
        audit.prior.inspect_identities(*args)


def test_denominators_exclusions_and_historical_team():
    subjects = audit.build_report()['historical_validation']['subjects']
    assert [len(s['outcome_weeks']) for s in subjects] == [16, 12, 12]
    assert subjects[0]['excluded_outcome_weeks'] == [19]
    assert subjects[0]['excluded_usage_weeks'] == [19]
    assert subjects[2]['historical_teams'] == ['WAS']
    assert all(not s['position_conflict'] and not s['missing_usage_weeks'] for s in subjects)
    assert audit.describe([{'week': 1, 'x': None}, {'week': 2, 'x': 0}], ['x']) == {
        'x': {'recorded_weeks': 2, 'nonnull_weeks': 1, 'null_weeks': [1], 'zero_weeks': [2]}}


def test_byte_drift_fails_closed(tmp_path):
    for path in audit.PINS:
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / path).read_bytes())
    (tmp_path / audit.RECEIPT).write_text('{}')
    with pytest.raises(ValueError, match='source drift'):
        audit.build_report(tmp_path)
