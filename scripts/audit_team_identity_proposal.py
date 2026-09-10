#!/usr/bin/env python3
"""Offline Data #267 proposal replay; stdout only, never admission or promotion."""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'b0c79de5403864796a5701dc42bcda8eafd788ab'
REPORT = 'docs/audits/team-identity-proposal-2026-09-10.json'
EDGES = {'9487': '00-0038606', '8112': '00-0037238', '10219': '00-0038611'}
HELPER = 'scripts/audit_draft_review_evidence_admission.py'
HELPER_HASH = 'da63168f1465e4e9f4a1f499e0a2154d69c74d82a88b1ace5809f49d417d023c'
if hashlib.sha256((ROOT / HELPER).read_bytes()).hexdigest() != HELPER_HASH:
    raise ValueError('audit helper drift')
spec = importlib.util.spec_from_file_location('team_proposal_precedent', ROOT / HELPER)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
# Private module instance: reuse reviewed checks without changing the archived audit.
prior.EDGES = EDGES
prior.REFERENCE = {}
RECEIPT = 'exports/promoted/draft_review/evidence_admission_v1.json'
PINS = {p: prior.PINS[p] for p in [prior.CANDIDATES, prior.COVERAGE, prior.CONFLICTS, prior.USAGE, prior.OUTCOMES]}
PINS.update({prior.CROSSWALK: 'c0e5c32a20b0397ff22e994a0fd48ec16907b5909f0880e0ebd3c7c89f0f9809',
             RECEIPT: '603e52409c5d07820bc58c5c0b7d6df91e4eb7cdc31326633d1c24e35c34811c',
             HELPER: HELPER_HASH})


def read_inputs(root=ROOT):
    raw = {}
    for path, expected in PINS.items():
        raw[path] = (root / path).read_bytes()
        prior.require(hashlib.sha256(raw[path]).hexdigest() == expected, f'source drift: {path}')
    return raw


def describe(rows, fields):
    result = {}
    for field in fields:
        values = [r[field] for r in rows if r[field] is not None]
        result[field] = {'recorded_weeks': len(rows), 'nonnull_weeks': len(values),
                         'null_weeks': sorted(r['week'] for r in rows if r[field] is None),
                         'zero_weeks': sorted(r['week'] for r in rows if r[field] == 0)}
    return result


def build_report(root=ROOT):
    raw = read_inputs(root)
    candidate, promoted, coverage = [json.loads(raw[p]) for p in [prior.CANDIDATES, prior.CROSSWALK, prior.COVERAGE]]
    prior.require(candidate['sources']['coverage_artifact']['sha256'] == PINS[prior.COVERAGE], 'coverage lineage drift')
    conflicts = list(csv.DictReader(io.StringIO(raw[prior.CONFLICTS].decode())))
    proposed = prior.inspect_identities(candidate, promoted, coverage, conflicts)
    usage, outcomes = [json.loads(raw[p]) for p in [prior.USAGE, prior.OUTCOMES]]
    weekly = prior.inspect_weekly(usage, outcomes)
    for subject in weekly['subjects']:
        pid = subject['inspected_gsis']
        ur, ore = [[r for r in x['records'] if r['player_id'] == pid and 1 <= r['week'] <= 18] for x in [usage, outcomes]]
        subject['excluded_usage_weeks'] = sorted(r['week'] for r in usage['records'] if r['player_id'] == pid and r['week'] > 18)
        subject['excluded_outcome_weeks'] = sorted(r['week'] for r in outcomes['records'] if r['player_id'] == pid and r['week'] > 18)
        subject['missing_usage_weeks'] = sorted(set(subject['outcome_weeks']) - set(subject['usage_weeks']))
        subject['outcome_denominators'] = describe(ore, prior.OUTCOME_FIELDS)
        subject['usage_denominators'] = describe(ur, ['target_share', 'air_yards_share'])
        subject['historical_positions'] = sorted({r['position'] for r in ore})
    receipt = json.loads(raw[RECEIPT])
    return {
        'schema_version': 'team_identity_proposal_v0_1', 'status': 'proposed_inactive',
        'consumer_allowed': False, 'operator_admission_decision': None,
        'base_commit': BASE, 'issue': 'https://github.com/Prometheus-Frameworks/TIBER-Data/issues/267',
        'sources': [{'path': p, 'sha256': h} for p, h in PINS.items()],
        'identity': {'proposed_records': proposed, 'existing_records': len(promoted['records']),
                     'resulting_count_if_later_promoted': len(promoted['records']) + len(proposed),
                     'candidate_generation_time': candidate['generated_at'],
                     'source_updated_at_semantics': 'candidate generation at V2 second precision, not provider update',
                     'provider_updated_at': None, 'raw_sleeper_replay': 'unavailable; original name census not rerun',
                     'raw_sleeper_sha256': candidate['sources']['sleeper_players_dump']['sha256'],
                     'candidate_names': [{'sleeper_id': r['sleeper_id'], 'canonical_name': r['player_name'], 'sleeper_name': r['evidence']['sleeper_name']} for r in candidate['rows'] if r['sleeper_id'] in EDGES]},
        'historical_validation': weekly,
        'proposed_permission_delta': {'add_identity_edges_only': EDGES,
            'effective_admission': False, 'existing_receipt_unchanged': RECEIPT,
            'scope_to_preserve_if_later_accepted': receipt['consumer_scope'],
            'conditions': ['Independent exact-head review and explicit operator acceptance required.',
                'Later materialization must preserve all 72 rows and bind a separate accepted receipt.',
                'Consumer bundle regeneration, merge and production release remain separately gated.']},
        'limitations': ['Recorded weeks are observations, not certified games played.',
            'Missing weeks are unknown, never zero, bye or DNP.',
            'Weeks 1–18 are the documented 2025 regular-season boundary; game_type/game_id absent.',
            'Candidate team is dated identity context; historical team remains the weekly source team.',
            'No provider-ID agreement: Sleeper GSIS and ESPN evidence are null; name_exact remains medium.',
            'No current role, injury, roster eligibility, ownership, forecast, ranking or transaction authority.',
            'Terms assessment remains dated 2026-09-07; original acquisition receipt/clocks are unavailable.',
            'No new source acquisition or refreshed terms assessment occurred.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    rendered = json.dumps(build_report(), indent=2, allow_nan=False) + '\n'
    if args.check:
        prior.require((ROOT / REPORT).read_text() == rendered, 'proposal replay mismatch')
        print('Three-edge inactive proposal matches; 72 promoted rows unchanged.')
    else:
        print(rendered, end='')


if __name__ == '__main__':
    main()
