"""Prepare exactly Data #267's three accepted historical identities offline.

This materializes reviewed branch files only. It does not regenerate consumers,
merge, deploy, refresh sources, or confer production authority.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_COMMIT = '22e9843df74ced8f2856c6463c86b626a79683d1'
PROPOSAL_PATH = 'docs/audits/team-identity-proposal-2026-09-10.json'
RECEIPT_PATH = 'exports/promoted/draft_review/team_identity_admission_v1.json'
OUTPUT_PATH = 'exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json'
ACCEPTANCE = 'https://github.com/Prometheus-Frameworks/TIBER-Data/pull/268#issuecomment-5627117154'
REVIEW = 'https://github.com/Prometheus-Frameworks/TIBER-Data/pull/268#issuecomment-5627016520'
GENERATED_AT = '2026-09-10T23:54:26Z'
EDGES = {'9487': '00-0038606', '8112': '00-0037238', '10219': '00-0038611'}


def historical(path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{PROPOSAL_COMMIT}:{path}'])


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load_proposal():
    raw = historical(PROPOSAL_PATH)
    # Preserve the archived proposed/inactive report; receipt supplies the later decision.
    if (ROOT / PROPOSAL_PATH).read_bytes() != raw:
        raise ValueError('Archived proposal drift')
    proposal = json.loads(raw)
    rows = proposal['identity']['proposed_records']
    if ({r['provider_player_id']: r['tiber_player_id'] for r in rows} != EDGES
            or len(rows) != 3
            or any(r['confidence'] != 'medium' or r['match_method'] != 'name_exact' for r in rows)):
        raise ValueError('Unexpected identity scope')
    return raw, proposal


def expected_receipt():
    raw, p = load_proposal()
    return {
        'schema_version': 'team_identity_admission_v1',
        'status': 'accepted_for_branch_preparation',
        'scope': 'three_historical_identity_edges_only',
        'proposal_commit': PROPOSAL_COMMIT,
        'proposal_path': PROPOSAL_PATH,
        'proposal_sha256': digest(raw),
        'operator_acceptance': ACCEPTANCE,
        'proposal_review': REVIEW,
        'identity_records': p['identity']['proposed_records'],
        'consumer_scope': p['proposed_permission_delta']['scope_to_preserve_if_later_accepted'],
        'sources': p['sources'],
        'limitations': p['limitations'],
        'historical_validation': p['historical_validation'],
        'consumer_bundle_regeneration_authorized': False,
        'merge_authorized': False,
        'production_deployment_authorized': False,
        'production_release_authorized': False,
        'artifact_generated_at': GENERATED_AT,
    }


def build(receipt=None):
    raw = ((ROOT / RECEIPT_PATH).read_bytes() if receipt is None
           else (json.dumps(receipt, indent=2, allow_nan=False) + '\n').encode())
    receipt = json.loads(raw)
    if json.dumps(receipt, sort_keys=True, allow_nan=False) != json.dumps(expected_receipt(), sort_keys=True, allow_nan=False):
        raise ValueError('Invalid or contradictory admission authority envelope')
    for source in receipt['sources']:
        # Only the old crosswalk is superseded. Every other source stays byte-identical.
        source_raw = (historical(source['path']) if source['path'] == OUTPUT_PATH
                      else (ROOT / source['path']).read_bytes())
        if digest(source_raw) != source['sha256']:
            raise ValueError(f"Source hash drift: {source['path']}")
    base = json.loads(historical(OUTPUT_PATH))
    if len(base['records']) != 72:
        raise ValueError('Unexpected base identity count')
    original = list(base['records'])
    base['records'] += receipt['identity_records']
    if (len({r['provider_canonical_id'] for r in base['records']}) != 75
            or len({r['tiber_player_id'] for r in base['records']}) != 75):
        raise ValueError('Identity collision')
    base['record_count'] = 75
    base['record_count_by_match_method']['name_exact'] += 3
    base['generated_at'] = GENERATED_AT
    base['coverage_notes']['slice'] += ' Plus three operator-authorized historical Team identities prepared on the review branch; see separate Team admission receipt. Production and consumer activation remain separately gated.'
    base['source_artifacts'].append({'artifact': 'TEAM_IDENTITY_ADMISSION_V1',
                                     'path': RECEIPT_PATH, 'sha256': digest(raw)})
    assert base['records'][:72] == original
    spec = importlib.util.spec_from_file_location('v2_validator', ROOT / 'scripts/promote_identity_crosswalk_rows.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    validator.validate_artifact(base)
    return base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    rendered = json.dumps(build(), indent=1, allow_nan=False) + '\n'
    target = ROOT / OUTPUT_PATH
    if args.check:
        if target.read_text() != rendered:
            raise ValueError('Prepared crosswalk differs from deterministic replay')
        print('Prepared 75-row crosswalk matches; original 72 rows preserved. No consumer or production activation.')
    else:
        # Never silently overwrite a newer extension or any unrelated current change.
        if target.read_bytes() not in (historical(OUTPUT_PATH), rendered.encode()):
            raise ValueError('Current crosswalk drift; refusing to overwrite')
        target.write_text(rendered)


if __name__ == '__main__':
    main()
