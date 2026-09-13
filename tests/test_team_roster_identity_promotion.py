"""Promotion must add authority without changing evidence or granting release."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import materialize_team_roster_identity_promotion as m


def test_exact_promotion_preserves_preparation_and_source_limits():
    r = m.validate(json.loads((ROOT / m.OUTPUT_PATH).read_bytes()))
    before = json.loads((ROOT / m.preparation.RECEIPT_PATH).read_bytes())
    for key in ['identity_records', 'consumer_scope', 'historical_validation', 'limitations', 'excluded_player_ids']:
        assert r[key] == before[key]
    assert len(r['player_ids']) == 19 and '13301' not in r['player_ids']
    assert r['historical_consumer_use_authorized'] is True
    assert r['consumer_activation_changes_authorized'] is True
    assert all(r[k] is False for k in ['merge_authorized', 'deployment_authorized', 'production_release_authorized'])
    assert r['operator_acceptance']['public_receipt_url'] is None
    assert r['attribution']['license'] == 'CC BY 4.0'


@pytest.mark.parametrize('change', ['extra', 'missing', 'confidence', 'team', 'weeks', 'source',
    'acceptance', 'scope', 'exclusion', 'denominator', 'merge', 'numeric_false', 'use', 'extra_authority'])
def test_invalid_promotion_rejected(change):
    r = deepcopy(m.expected_receipt())
    if change == 'extra': r['player_ids'].append('13301')
    if change == 'missing': r['identity_records'].pop()
    if change == 'confidence': r['identity_records'][0]['confidence'] = 'high'
    if change == 'team': r['historical_validation'][0]['historical_teams'] = ['NO']
    if change == 'weeks': r['consumer_scope']['weeks'] = [1, 19]
    if change == 'source': r['sources'][0]['sha256'] = '0' * 64
    if change == 'acceptance': r['operator_acceptance']['operator_message'] = 'Okay sounds good'
    if change == 'scope': r['scope'] = 'all_players'
    if change == 'exclusion': r['excluded_player_ids'] = []
    if change == 'denominator': r['historical_validation'][0]['outcome_weeks'].append(19)
    if change == 'merge': r['merge_authorized'] = True
    if change == 'numeric_false': r['deployment_authorized'] = 0
    if change == 'use': r['historical_consumer_use_authorized'] = False
    if change == 'extra_authority': r['forecast_allowed'] = True
    with pytest.raises(ValueError, match='authority envelope'):
        m.validate(r)


def test_working_source_drift_rejected(tmp_path, monkeypatch):
    # Pinned commit is still read from the real repo; only working bytes differ.
    real = m.subprocess.check_output
    monkeypatch.setattr(m.subprocess, 'check_output', lambda *a, **kw: real(
        ['git', '-C', str(ROOT), 'show', f'{m.BASE_COMMIT}:{m.preparation.RECEIPT_PATH}']))
    monkeypatch.setattr(m, 'ROOT', tmp_path)
    p = tmp_path / m.preparation.RECEIPT_PATH
    p.parent.mkdir(parents=True)
    p.write_text('{}')
    with pytest.raises(ValueError, match='working source drift'):
        m.read_source(m.preparation.RECEIPT_PATH)


def test_optimized_replay_and_authority_gate():
    code = ('import sys; sys.path.insert(0, "scripts"); import materialize_team_roster_identity_promotion as m; '
            'r=m.expected_receipt(); r["deployment_authorized"]=True; m.validate(r)')
    result = subprocess.run([sys.executable, '-O', '-c', code], cwd=ROOT, capture_output=True)
    assert result.returncode != 0 and b'Invalid promotion authority envelope' in result.stderr
    subprocess.run([sys.executable, '-O', 'scripts/materialize_team_roster_identity_promotion.py', '--check'],
                   cwd=ROOT, check=True, capture_output=True)
