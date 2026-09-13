"""Materialize the operator-accepted nineteen-edge historical Team batch offline.

Only existing, hash-pinned repository evidence is read. The earlier receipts and
75 identity rows remain unchanged. This CLI cannot merge or activate production.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess

from promote_identity_crosswalk_rows import build_record, validate_artifact

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = 'e65791d3169c0234b80bdb4bfb00c3ed848d64dd'
GENERATED_AT = '2026-09-13T12:59:02Z'
OUTPUT_PATH = 'exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json'
RECEIPT_PATH = 'exports/promoted/draft_review/team_roster_identity_admission_v1.json'
CANDIDATES = 'exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json'
COVERAGE = 'exports/promoted/nfl/player_season_coverage_v0.json'
CONFLICTS = 'exports/candidates/identity_crosswalk/identity_crosswalk_review_v0.csv'
USAGE = 'data/processed/evidence/player_weekly_usage_2025.source_backed.json'
OUTCOMES = 'data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json'
ADMISSION = 'exports/promoted/draft_review/evidence_admission_v1.json'
PREVIOUS_RECEIPT = 'exports/promoted/draft_review/team_identity_admission_v1.json'
PINS = {
    CANDIDATES: '45a69f2176104249d3ea416ccdd71dadd8196c6f5dfe3f1bf4e303580ecf47cd',
    OUTPUT_PATH: '02e360f58837f620e26b071992f90c444486388e692e39c5dcffc23f63e8a0c9',
    COVERAGE: 'd45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac',
    CONFLICTS: '3f7002c33e6ef31a07e1a63db10f3ecbeefcb0328f78e083893973f55ea137f8',
    USAGE: '30a8e17370270e2fa5d055c7a771f19af2fe7bd89282cd2373f7704a492412cb',
    OUTCOMES: 'f241112115c9a625abead3410db89db6b4a8b603ce1dd663a45ff0697563e3a2',
    ADMISSION: '603e52409c5d07820bc58c5c0b7d6df91e4eb7cdc31326633d1c24e35c34811c',
    PREVIOUS_RECEIPT: '4ed7a6e7d0310c0f3b3e3c70a53f7d7ec0fb0c22dbd931702ea5efc4399f84ef',
}
# Exact reviewed edges and confidence tiers; no runtime name resolver.
EDGES = {
    '10444': ('00-0038979', 'name_exact'), '10218': ('00-0038618', 'name_exact'),
    '8127': ('00-0038046', 'name_exact'), '11571': ('00-0039798', 'name_exact'),
    '11575': ('00-0039875', 'name_exact'), '5022': ('00-0034351', 'gsis_direct'),
    '5892': ('00-0035685', 'gsis_direct'), '5927': ('00-0035659', 'gsis_direct'),
    '6768': ('00-0036212', 'espn_bridge'), '6819': ('00-0036252', 'espn_bridge'),
    '7525': ('00-0036912', 'name_exact'), '8142': ('00-0037664', 'name_exact'),
    '8146': ('00-0037740', 'name_exact'), '8161': ('00-0038128', 'name_exact'),
    '9508': ('00-0039032', 'name_exact'), '10213': ('00-0038563', 'name_exact'),
    '11834': ('00-0039424', 'name_exact'), '12048': ('00-0039299', 'name_exact'),
    '12507': ('00-0040666', 'name_exact'),
}
REVIEW_REFERENCES = {
    'source': 'independent_agent_review_in_operator_conversation',
    'review_date': '2026-09-13',
    'proposal_sha256': 'a00fbfe876db14372a170c3a579971537c5074b1632f2688e3b2e09c6a775e8b',
    'review_sha256': '471237237f5be9fce7185f12464084bfd8dc9f25e3d85e91f648b30d7b50b996',
    'result': 'no_material_findings_on_nineteen_edge_proposal',
    'public_receipt_url': None,
    'implementation_review': 'pending_separate_review',
}
ACCEPTANCE = {
    'source': 'operator_conversation', 'date': '2026-09-13',
    'operator_message': 'Okay sounds good', 'public_receipt_url': None,
    'context': 'Acceptance followed independent proposal review and an explanation that transferred players retain their historical weekly teams.',
    'scope': 'nineteen reviewed historical identity edges; Data branch materialization and matching Fantasy consumer integration preparation; no merge or production release',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def historical(path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{BASE_COMMIT}:{path}'],
                                   env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'})


def load_sources():
    loaded = {}
    for path, expected in PINS.items():
        raw = historical(path) if path == OUTPUT_PATH else (ROOT / path).read_bytes()
        require(digest(raw) == expected, f'Source hash drift: {path}')
        loaded[path] = list(csv.DictReader(io.StringIO(raw.decode()))) if path == CONFLICTS else json.loads(raw)
    return loaded


def weekly_summary(sid, gsis, sources, scope):
    lanes = {}
    for name, path in [('outcome', OUTCOMES), ('usage', USAGE)]:
        all_rows = [r for r in sources[path]['records'] if r['player_id'] == gsis and r['season'] == 2025]
        rows = sorted([r for r in all_rows if 1 <= r['week'] <= 18], key=lambda r: r['week'])
        require(rows and len({r['week'] for r in rows}) == len(rows), 'Missing or duplicate admitted weekly key')
        lanes[name] = (rows, sorted(r['week'] for r in all_rows if not 1 <= r['week'] <= 18))
    outcomes, usage = lanes['outcome'][0], lanes['usage'][0]
    require([r['week'] for r in outcomes] == [r['week'] for r in usage], 'Cohort usage coverage changed')
    for out, use in zip(outcomes, usage):
        require(all(out.get(k) == use.get(k) for k in ['team', 'opponent', 'position', 'targets', 'receptions', 'rushing_attempts']),
                'Cohort context or shared count conflict')
        require(all(use.get(k) is None for k in scope['unavailable_usage_fields']), 'Unsupported usage populated')
    denominators = {}
    for fields, rows in [(scope['outcome_fields'], outcomes), (scope['usage_fields'], usage)]:
        for field in fields:
            values = [r.get(field) for r in rows]
            require(all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values),
                    'Reviewed cohort contains missing or invalid numeric values')
            denominators[field] = {'recorded_weeks': len(rows), 'nonnull_weeks': len(values),
                                   'zero_weeks': [r['week'] for r in rows if r[field] == 0]}
    weeks = [r['week'] for r in outcomes]
    return {'player_id': sid, 'outcome_weeks': weeks, 'usage_weeks': [r['week'] for r in usage],
            'unknown_calendar_weeks': sorted(set(range(1, 19)) - set(weeks)),
            'excluded_outcome_weeks': lanes['outcome'][1], 'excluded_usage_weeks': lanes['usage'][1],
            'historical_teams': sorted({r['team'] for r in outcomes}),
            'historical_positions': sorted({r['position'] for r in outcomes}), 'denominators': denominators}


def expected_receipt(sources=None):
    s = load_sources() if sources is None else sources
    base = s[OUTPUT_PATH]['records']
    require(len(base) == 75, 'Unexpected baseline identity count')
    candidates = s[CANDIDATES]
    generated = datetime.fromisoformat(candidates['generated_at']).strftime('%Y-%m-%dT%H:%M:%SZ')
    require(generated == '2026-08-08T18:17:13Z', 'Candidate generation clock drift')
    records, raw_candidates, coverage = [], [], []
    scope = s[ADMISSION]['consumer_scope']
    require(s[ADMISSION]['status'] == 'accepted' and scope == s[PREVIOUS_RECEIPT]['consumer_scope'], 'Prior scope drift')
    for sid, (gsis, tier) in EDGES.items():
        matches = [c for c in candidates['rows'] if c['sleeper_id'] == sid or c['tiber_player_id'] == gsis]
        require(len(matches) == 1, 'Candidate identity collision')
        c = matches[0]
        require(c['sleeper_id'] == sid and c['tiber_player_id'] == gsis and c['match_tier'] == tier, 'Exact reviewed edge drift')
        require(not any(r['provider_player_id'] == sid or r['tiber_player_id'] == gsis for r in base), 'Baseline identity collision')
        require(not any(r['player_id'] == gsis or sid in [r['gsis_match'], r['espn_match']] for r in s[CONFLICTS]), 'Conflict review overlap')
        canonical = [r for r in s[COVERAGE]['records'] if r['player_id'] == gsis and r['season'] == 2025 and r['season_type'] == 'REG']
        require(len(canonical) == 1, 'Canonical season identity ambiguous')
        ev = c['evidence']
        require(canonical[0]['player_name'] == c['player_name'] and canonical[0]['position'] == c['position']
                and str(canonical[0]['provider_ids']['espn_id']) == str(ev['coverage_espn_id']), 'Canonical identity disagreement')
        if tier == 'name_exact':
            require(ev['sleeper_gsis_id'] is None and ev['sleeper_espn_id'] is None, 'Unexpected name-only provider evidence')
        else:
            require(str(ev['sleeper_espn_id']) == str(ev['coverage_espn_id']), 'ESPN agreement missing')
            if tier == 'gsis_direct':
                require(isinstance(ev['sleeper_gsis_id'], str) and ev['sleeper_gsis_id'].strip() == gsis, 'GSIS agreement missing')
        records.append(build_record(c, generated))
        raw_candidates.append(c)
        coverage.append(weekly_summary(sid, gsis, s, scope))
    return {
        'schema_version': 'team_roster_identity_admission_v1', 'status': 'accepted_for_branch_and_consumer_preparation',
        'scope': 'nineteen_historical_identity_edges_only', 'artifact_generated_at': GENERATED_AT,
        'baseline_commit': BASE_COMMIT, 'operator_acceptance': ACCEPTANCE, 'proposal_review': REVIEW_REFERENCES,
        'identity_records': records, 'candidate_evidence': raw_candidates, 'historical_validation': coverage,
        'consumer_scope': scope,
        'sources': [{'commit': BASE_COMMIT, 'path': p, 'sha256': h} for p, h in PINS.items()],
        'excluded_player_ids': ['13301'],
        'exclusion_context': 'Antonio Williams is outside the approved 2025 cohort. The manager identifies him as a rookie without 2025 NFL evidence; no history is fabricated or acquired.',
        'consumer_bundle_regeneration_authorized': True,
        'merge_authorized': False, 'production_deployment_authorized': False, 'production_release_authorized': False,
        'limitations': [
            'Recorded weeks are observations, not certified games played; missing weeks are unknown, never zero, bye or DNP.',
            'Only 2025 weeks 1–18; game_type/game_id absent. Historical teams remain weekly source teams, separately from current Sleeper teams.',
            'Fourteen name_exact identities remain medium confidence; three gsis_direct and two espn_bridge identities remain high confidence.',
            'Raw candidate evidence is preserved. GSIS whitespace is trimmed only to check agreement for the existing reviewed mapping.',
            'V2 row source_updated_at is the candidate-generation clock, not the provider update time. Original acquisition/update clocks remain unavailable.',
            'No original Sleeper dump or original name-candidate census was replayed; this is admission of existing committed candidates.',
            'Terms assessment remains dated 2026-09-07; original acquisition terms receipt is unavailable; no new acquisition or terms assessment.',
            'No current role, health, eligibility, ownership, forecast, regression, ranking, league points or transaction authority.',
            'Proposal review does not certify this implementation. Merge and production require a separate operator decision.',
        ],
    }


def build(receipt=None):
    sources = load_sources()
    expected = expected_receipt(sources)
    actual = json.loads((ROOT / RECEIPT_PATH).read_bytes()) if receipt is None else receipt
    require(json.dumps(actual, sort_keys=True, allow_nan=False) == json.dumps(expected, sort_keys=True, allow_nan=False),
            'Invalid or contradictory admission authority envelope')
    receipt_raw = (json.dumps(expected, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    base = sources[OUTPUT_PATH]
    base['records'] = base['records'] + actual['identity_records']
    require(len({r['provider_canonical_id'] for r in base['records']}) == 94
            and len({r['tiber_player_id'] for r in base['records']}) == 94, 'Identity collision')
    base['record_count'] = 94
    base['record_count_by_match_method'] = dict(sorted(Counter(r['match_method'] for r in base['records']).items()))
    base['generated_at'] = GENERATED_AT
    base['coverage_notes']['slice'] += ' Plus nineteen operator-accepted historical Team identities; see team_roster_identity_admission_v1. Branch and consumer preparation only; no merge or production release.'
    base['source_artifacts'].append({'artifact': 'TEAM_ROSTER_IDENTITY_ADMISSION_V1', 'path': RECEIPT_PATH, 'sha256': digest(receipt_raw)})
    validate_artifact(base)
    return base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    receipt = expected_receipt()
    receipt_raw = (json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    crosswalk = (json.dumps(build(receipt), indent=1, allow_nan=False) + '\n').encode()
    target, grant = ROOT / OUTPUT_PATH, ROOT / RECEIPT_PATH
    if args.check:
        require(grant.read_bytes() == receipt_raw and target.read_bytes() == crosswalk, 'Committed admission differs from deterministic replay')
    else:
        require(not grant.exists() or grant.read_bytes() == receipt_raw, 'Current receipt drift; refusing to overwrite')
        require(target.read_bytes() in (historical(OUTPUT_PATH), crosswalk), 'Current crosswalk drift; refusing to overwrite')
        grant.write_bytes(receipt_raw)
        target.write_bytes(crosswalk)
    print('94 identities; original 75 preserved; exactly nineteen additions. No source refresh, merge or production activation.')


if __name__ == '__main__':
    main()
