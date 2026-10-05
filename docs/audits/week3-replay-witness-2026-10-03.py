"""Offline provenance repair: freshly materialize exact retained W3 bytes, never admit them."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from publish_weekly_boxscore_candidate_v0 import canonical, prepare, publish

BASE = 'eac3b9bc22cf1fa230b233a09f5e031a2a9b409a'
IMPLEMENTATION = 'e1e92078c626b9e2e502e927ba0de79afd26f451'
SUPPORT = '2b58e2c22ccd2430041afcfbd143b057830878f0'
DIGEST = 'f3366ac1c2192641c6e94ba7c756ed2e12ba73b37550619ae143deaeab9f9902'
SOURCE = 'data/raw/weekly_boxscore/2026_w03_6e8426cf948791cd5819b9e3ea7a5bb3ee3290370e1133bab7aeb488b093d196'
SCHEDULE = 'data/raw/weekly_schedule/f3f8613f47dc9568f61506723d819ecac75c5b526de49884dc18d678c69de062'
CANDIDATE = f'exports/candidates/weekly_boxscore/revisions/2026_REG_w03/{DIGEST}.json'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def git_bytes(commit, path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{commit}:{path}'])

def run(output):
    # Refuse altered implementation or candidate; prepare also authenticates every raw member.
    members = [f'{SOURCE}/{name}' for name in ['player.csv', 'team.csv', 'receipt.json', 'LICENSE.md']]
    members += [f'{SCHEDULE}/{name}' for name in ['games.csv', 'receipt.json', 'LICENSE.md']]
    members += [CANDIDATE, str(Path(CANDIDATE).parent / 'index.json')]
    implementations = [f'scripts/{name}' for name in ['publish_weekly_boxscore_candidate_v0.py',
        'build_weekly_boxscore_candidate_v0.py', 'intake_weekly_boxscore_v0.py', 'intake_weekly_schedule_v0.py']]
    pins = []
    for path in members + implementations:
        raw = (ROOT / path).read_bytes()
        commit = IMPLEMENTATION if path in implementations else BASE
        if raw != git_bytes(commit, path):
            raise ValueError(f'Altered pinned member: {path}')
        pins.append({'path': path, 'size': len(raw), 'sha256': digest(raw), 'commit': commit})
    subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', SUPPORT, BASE], check=True)
    start = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    envelope = prepare(ROOT, ROOT / SOURCE, SUPPORT, ROOT / SCHEDULE, SUPPORT)
    raw = canonical(envelope)
    if digest(raw) != DIGEST or raw != (ROOT / CANDIDATE).read_bytes():
        raise ValueError('Replay differs from selected candidate')
    # New isolated publication witnesses fresh materialization, never the missing original clock.
    with tempfile.TemporaryDirectory(prefix='tiber-w3-replay-') as temp:
        result = publish(envelope, Path(temp))
        materialized = Path(result['stream']) / f'{DIGEST}.json'
        if result['status'] != 'candidate_revision_written' or materialized.read_bytes() != raw:
            raise ValueError('Fresh materialization failed')
        repeated = publish(envelope, Path(temp))
        if repeated['status'] != 'unchanged':
            raise ValueError('Repeat publication is not a no-op')
    end = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    second = canonical(prepare(ROOT, ROOT / SOURCE, SUPPORT, ROOT / SCHEDULE, SUPPORT))
    if second != raw:
        raise ValueError('Second replay differs')
    witness = {'schema_version': 'week3_fresh_replay_generation_witness_v1',
        'witness_kind': 'fresh_offline_replay_materialization', 'base': IMPLEMENTATION,
        'selected_data_head': BASE, 'support_commit': SUPPORT, 'candidate_path': CANDIDATE,
        'original_candidate_generated_at': None, 'build_started_at': start, 'build_completed_at': end,
        'result': {'status': result['status'], 'sha256': result['sha256']},
        'checks': {'candidate_byte_equal': True, 'second_replay_byte_equal': True,
            'repeat_publication': repeated['status'], 'support_ancestor': True},
        'source_admission': False, 'rop_purpose_acceptance': False, 'evidence_cutoff': None,
        'finality': 'unknown', 'independent_review': 'pending',
        'limitations': ['This clock witnesses a new materialization, not the original September 30 build.',
            'Adoption as a downstream generation witness requires explicit reviewed replay semantics.',
            'No provider retrieval, source admission, original receipt mutation or current pointer update.',
            'Weekly aggregates cannot establish a post-Jefferson target window, snaps or routes.']}
    output.mkdir(parents=True, exist_ok=False)
    witness_raw = canonical(witness)
    (output / 'build-receipt.json').write_bytes(witness_raw)
    manifest = {'schema_version': 'week3_replay_member_manifest_v1', 'selected_data_head': BASE,
        'implementation_commit': IMPLEMENTATION, 'source_support_commit': SUPPORT,
        'candidate_sha256': DIGEST, 'members': pins,
        'build_receipt': {'file': 'build-receipt.json', 'size': len(witness_raw), 'sha256': digest(witness_raw)},
        'independent_review': 'pending', 'consumer_admitted': False}
    (output / 'manifest.json').write_bytes(canonical(manifest))
    print(json.dumps({'candidate_sha256': DIGEST, 'members_authenticated': len(pins),
        'build_completed_at': end, 'source_admission': False}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    run(args.output_dir)
