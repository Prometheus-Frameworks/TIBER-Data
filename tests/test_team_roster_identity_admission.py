"""Bounded nineteen-edge admission: source integrity, authority and preservation."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import materialize_team_roster_identity_admission as m


def test_replay_preserves_every_prior_row_and_exact_nineteen():
    result = m.build()
    assert result == json.loads((ROOT / m.OUTPUT_PATH).read_bytes())
    assert result['records'][:75] == json.loads(m.historical(m.OUTPUT_PATH))['records']
    additions = result['records'][75:]
    assert {r['provider_player_id']: (r['tiber_player_id'], r['match_method']) for r in additions} == m.EDGES
    assert result['record_count_by_match_method'] == {'gsis_direct': 26, 'espn_bridge': 8, 'name_exact': 60}
    assert all(r['confidence'] == ('medium' if r['match_method'] == 'name_exact' else 'high') for r in additions)
    assert '13301' not in {r['provider_player_id'] for r in result['records']}
    assert result['source_artifacts'][-1]['sha256'] == hashlib.sha256((ROOT / m.RECEIPT_PATH).read_bytes()).hexdigest()


def test_historical_teams_denominators_and_raw_provider_evidence():
    receipt = m.expected_receipt()
    subjects = {r['player_id']: r for r in receipt['historical_validation']}
    assert subjects['5892']['historical_teams'] == ['DET']
    assert subjects['6819']['historical_teams'] == ['IND']
    assert [len(subjects[p]['outcome_weeks']) for p in m.EDGES] == [12,16,13,16,17,15,17,10,14,17,17,15,7,4,13,17,9,10,9]
    assert sum(len(s['outcome_weeks']) for s in subjects.values()) == 248
    assert sum(len(s['unknown_calendar_weeks']) for s in subjects.values()) == 94
    assert sum(len(s['excluded_outcome_weeks']) for s in subjects.values()) == 9
    raw = {c['sleeper_id']: c for c in receipt['candidate_evidence']}
    assert raw['5892']['evidence']['sleeper_gsis_id'].startswith(' ')
    assert all(r['source_updated_at'] == '2026-08-08T18:17:13Z' for r in receipt['identity_records'])
    assert receipt['operator_acceptance']['source'] == 'operator_conversation'
    assert receipt['operator_acceptance']['public_receipt_url'] is None
    assert receipt['proposal_review']['implementation_review'] == 'pending_separate_review'


@pytest.mark.parametrize('change', ['extra', 'missing', 'tier', 'gsis', 'team', 'weeks', 'source',
    'acceptance', 'review', 'scope', 'exclusion', 'denominator', 'merge', 'numeric_false', 'consumer', 'extra_authority'])
def test_contradictory_receipt_rejected(change):
    r = deepcopy(m.expected_receipt())
    if change == 'extra': r['identity_records'].append(deepcopy(r['identity_records'][0]))
    if change == 'missing': r['identity_records'].pop()
    if change == 'tier': r['identity_records'][0]['confidence'] = 'high'
    if change == 'gsis': r['identity_records'][0]['tiber_player_id'] = '00-0000000'
    if change == 'team': r['identity_records'][0]['team'] = 'NO'
    if change == 'weeks': r['consumer_scope']['weeks'] = [1, 19]
    if change == 'source': r['sources'][0]['sha256'] = '0' * 64
    if change == 'acceptance': r['operator_acceptance']['source'] = 'github_comment'
    if change == 'review': r['proposal_review']['implementation_review'] = 'passed'
    if change == 'scope': r['scope'] = 'all_candidates'
    if change == 'exclusion': r['excluded_player_ids'] = []
    if change == 'denominator': r['historical_validation'][0]['outcome_weeks'].append(19)
    if change == 'merge': r['merge_authorized'] = True
    if change == 'numeric_false': r['merge_authorized'] = 0
    if change == 'consumer': r['consumer_bundle_regeneration_authorized'] = False
    if change == 'extra_authority': r['forecast_allowed'] = True
    with pytest.raises(ValueError, match='authority envelope'):
        m.build(r)


def test_source_drift_fails_before_materialization(tmp_path, monkeypatch):
    historical = m.historical
    for path in m.PINS:
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(historical(path))
    (tmp_path / m.CANDIDATES).write_text('{}')
    monkeypatch.setattr(m, 'ROOT', tmp_path)
    monkeypatch.setattr(m, 'historical', historical)
    with pytest.raises(ValueError, match='Source hash drift'):
        m.expected_receipt()


def test_cli_replay_is_idempotent_and_optimization_preserves_gates():
    before = {p: (ROOT / p).read_bytes() for p in [m.OUTPUT_PATH, m.RECEIPT_PATH]}
    for args in [[], ['--check']]:
        subprocess.run([sys.executable, '-O', str(ROOT / 'scripts/materialize_team_roster_identity_admission.py'), *args],
                       cwd=ROOT, check=True, capture_output=True)
        assert before == {p: (ROOT / p).read_bytes() for p in before}
