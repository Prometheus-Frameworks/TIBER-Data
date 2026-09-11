"""Fail-closed checks for the three-edge branch preparation, not deployment."""
import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location('team_materializer', ROOT / 'scripts/materialize_team_identity_admission.py')
m = module_from_spec(spec)
spec.loader.exec_module(m)


def test_exact_replay_preserves_72_and_medium_three():
    result = m.build()
    assert result == json.loads((ROOT / m.OUTPUT_PATH).read_bytes())
    old = json.loads(m.historical(m.OUTPUT_PATH))
    assert result['records'][:72] == old['records']
    additions = result['records'][72:]
    assert len(additions) == 3
    assert {r['provider_player_id']: r['tiber_player_id'] for r in additions} == m.EDGES
    assert all(r['match_method'] == 'name_exact' and r['confidence'] == 'medium' for r in additions)
    assert result['record_count_by_match_method'] == {'gsis_direct': 23, 'espn_bridge': 6, 'name_exact': 46}
    assert result['source_artifacts'][-1]['sha256'] == hashlib.sha256((ROOT / m.RECEIPT_PATH).read_bytes()).hexdigest()


def test_scope_denominators_and_sources_preserved():
    receipt = m.expected_receipt()
    proposal = json.loads(m.historical(m.PROPOSAL_PATH))
    assert receipt['consumer_scope']['weeks'] == [1, 18]
    assert receipt['limitations'] == proposal['limitations']
    subjects = receipt['historical_validation']['subjects']
    assert [len(s['outcome_weeks']) for s in subjects] == [16, 12, 12]
    assert subjects[0]['excluded_outcome_weeks'] == [19]
    assert subjects[2]['historical_teams'] == ['WAS']
    assert receipt['identity_records'][2]['team'] == 'JAX'
    for source in receipt['sources']:
        if source['path'] != m.OUTPUT_PATH:
            assert hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest() == source['sha256']
    assert json.loads((ROOT / m.PROPOSAL_PATH).read_bytes())['consumer_allowed'] is False
    assert all(receipt[k] is False for k in ['consumer_bundle_regeneration_authorized',
        'merge_authorized', 'production_deployment_authorized', 'production_release_authorized'])


@pytest.mark.parametrize('kind', ['extra_edge', 'missing_edge', 'confidence', 'team', 'weeks',
    'source', 'acceptance', 'review', 'proposal', 'status', 'limitations', 'denominator',
    'extra_authority', 'merge', 'numeric_false'])
def test_contradictory_receipt_fails_closed(kind):
    r = deepcopy(m.expected_receipt())
    if kind == 'extra_edge': r['identity_records'].append(deepcopy(r['identity_records'][0]))
    if kind == 'missing_edge': r['identity_records'].pop()
    if kind == 'confidence': r['identity_records'][0]['confidence'] = 'high'
    if kind == 'team': r['identity_records'][2]['team'] = 'WAS'
    if kind == 'weeks': r['consumer_scope']['weeks'] = [1, 19]
    if kind == 'source': r['sources'][0]['sha256'] = '0' * 64
    if kind == 'acceptance': r['operator_acceptance'] = 'invented'
    if kind == 'review': r['proposal_review'] = 'invented'
    if kind == 'proposal': r['proposal_commit'] = '0' * 40
    if kind == 'status': r['status'] = 'accepted'
    if kind == 'limitations': r['limitations'] = []
    if kind == 'denominator': r['historical_validation']['subjects'][0]['outcome_weeks'].append(19)
    if kind == 'extra_authority': r['consumer_allowed'] = True
    if kind == 'merge': r['merge_authorized'] = True
    if kind == 'numeric_false': r['merge_authorized'] = 0
    with pytest.raises(ValueError, match='authority envelope'):
        m.build(r)


def test_current_source_drift_fails(tmp_path, monkeypatch):
    # Read archived bytes before substituting an isolated current checkout.
    proposal = m.historical(m.PROPOSAL_PATH)
    crosswalk = m.historical(m.OUTPUT_PATH)
    for source in m.expected_receipt()['sources']:
        path = tmp_path / source['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / source['path']).read_bytes())
    for path in [m.PROPOSAL_PATH, m.RECEIPT_PATH]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    candidate = tmp_path / 'exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json'
    candidate.write_text('{}')
    monkeypatch.setattr(m, 'ROOT', tmp_path)
    monkeypatch.setattr(m, 'historical', lambda path: proposal if path == m.PROPOSAL_PATH else crosswalk)
    with pytest.raises(ValueError, match='Source hash drift'):
        m.build()


@pytest.mark.parametrize('check', [False, True])
def test_legacy_materializer_cannot_discard_three_rows(check):
    before = (ROOT / m.OUTPUT_PATH).read_bytes()
    args = [sys.executable, str(ROOT / 'scripts/materialize_draft_review_identity_admission.py')]
    if check: args.append('--check')
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    assert result.returncode != 0
    assert 'would discard accepted rows' in result.stderr
    assert (ROOT / m.OUTPUT_PATH).read_bytes() == before


def test_new_cli_check_and_idempotent_write():
    before = (ROOT / m.OUTPUT_PATH).read_bytes()
    for args in [[], ['--check']]:
        subprocess.run([sys.executable, str(ROOT / 'scripts/materialize_team_identity_admission.py'), *args],
                       cwd=ROOT, check=True, capture_output=True)
        assert (ROOT / m.OUTPUT_PATH).read_bytes() == before
