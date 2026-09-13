"""Record bounded operator promotion separately from immutable preparation receipts.

Offline replay only. This receipt grants historical consumer use in the proposed
activation change; it does not authorize merging or deploying that change.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

import materialize_team_roster_identity_admission as preparation

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = 'c0a7d1e98161c23f64f67c075f81eb71d6ba693a'
OUTPUT_PATH = 'exports/promoted/draft_review/team_roster_identity_promotion_v1.json'
PINS = {
    preparation.OUTPUT_PATH: '72521b56b1edd92fbb1feac974ab2608a599004f378974192e885278a4007011',
    preparation.RECEIPT_PATH: 'cc61d1e236138e1c1e6685fb444c3db81da1188d7cfcc895b278164916e9be4f',
    **{p: h for p, h in preparation.PINS.items() if p != preparation.OUTPUT_PATH},
}
OPERATOR_MESSAGE = ('Proceed with the nineteen-player historical promotion receipt and matching Team consumer '
                    'activation changes, tests, paired PRs and independent review. Preserve all source limitations '
                    'and exclude Antonio Williams. Stop before merging or deploying the activation changes.')


def canonical(value):
    # JSON equality distinguishes false from 0 and rejects non-finite numbers.
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def read_source(path):
    raw = subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{BASE_COMMIT}:{path}'],
                                  env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'})
    preparation.require(hashlib.sha256(raw).hexdigest() == PINS[path], f'Promotion source hash drift: {path}')
    preparation.require((ROOT / path).read_bytes() == raw, f'Promotion working source drift: {path}')
    return raw


def expected_receipt():
    sources = {p: read_source(p) for p in PINS}
    receipt = json.loads(sources[preparation.RECEIPT_PATH])
    identities = json.loads(sources[preparation.OUTPUT_PATH])
    # Replay the previously reviewed source checks, including exact edges,
    # confidence, unknown weeks and preservation of the original 75 rows.
    preparation.require(canonical(preparation.build(receipt)) == canonical(identities), 'Preparation replay drift')
    return {
        'schema_version': 'team_roster_identity_promotion_v1',
        'status': 'accepted_for_historical_consumer_use',
        'scope': 'nineteen_historical_identity_edges_only',
        'decision_date': '2026-09-13',
        'baseline_commit': BASE_COMMIT,
        'preparation_receipt': {'path': preparation.RECEIPT_PATH, 'sha256': PINS[preparation.RECEIPT_PATH]},
        'operator_acceptance': {'source': 'operator_conversation', 'date': '2026-09-13',
                                'operator_message': OPERATOR_MESSAGE, 'public_receipt_url': None},
        'historical_consumer_use_authorized': True,
        'consumer_activation_changes_authorized': True,
        'merge_authorized': False,
        'deployment_authorized': False,
        'production_release_authorized': False,
        'identity_records': receipt['identity_records'],
        'player_ids': list(preparation.EDGES),
        'excluded_player_ids': receipt['excluded_player_ids'],
        'exclusion_context': receipt['exclusion_context'],
        'consumer_scope': receipt['consumer_scope'],
        'historical_validation': receipt['historical_validation'],
        'sources': [{'commit': BASE_COMMIT, 'path': p, 'sha256': h} for p, h in PINS.items()],
        'limitations': receipt['limitations'],
        'release_boundary': 'The historical-use grant is separate from release authority. Activation changes require independent review and separate authorization before merge or any deployment. Earlier preparation receipts remain unchanged.',
        'source_acquired_at': None, 'source_updated_at': None,
        'original_release_hash': None, 'package_version': None,
        'attribution': {'name': 'nflverse contributors', 'source_url': 'https://github.com/nflverse/nflverse-pbp',
                        'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                        'notice': 'No endorsement implied. Scoped terms assessment is dated 2026-09-07; original acquisition terms receipt is unavailable.'},
    }


def validate(receipt):
    preparation.require(canonical(receipt) == canonical(expected_receipt()), 'Invalid promotion authority envelope')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    raw = (json.dumps(expected_receipt(), indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    path = ROOT / OUTPUT_PATH
    if path.exists() or args.check:
        preparation.require(path.read_bytes() == raw, 'Committed promotion differs from replay; refusing overwrite')
    else:
        path.write_bytes(raw)
    print(f'{OUTPUT_PATH}: sha256={hashlib.sha256(raw).hexdigest()}')


if __name__ == '__main__':
    main()
