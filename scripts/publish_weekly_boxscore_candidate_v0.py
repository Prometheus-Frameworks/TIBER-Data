"""Offline revision-safe candidate publication. Never writes promoted exports or an admission."""
import argparse
import csv
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from build_weekly_boxscore_candidate_v0 import build_candidate
from intake_weekly_boxscore_v0 import validate_receipt, AUDITED_LICENSE_SHA256, LICENSE_URL
from datetime import datetime

VERSION = 'weekly_boxscore_publication_candidate_v0'

def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def committed(root, commit, path):
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Exact support commit required')
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    env = {**os.environ, 'GIT_NO_LAZY_FETCH': '1'}
    raw = subprocess.check_output(['git', '-C', str(root), 'show', f'{commit}:{relative}'], env=env)
    if path.read_bytes() != raw:
        raise ValueError('Uncommitted support bytes')
    return raw

def coverage(candidate, schedule_raw=None):
    observed = set(candidate['coverage']['game_ids'])
    result = {'observed_game_ids': sorted(observed), 'scheduled_game_ids': None,
        'missing_game_ids': None, 'unexpected_game_ids': None,
        'schedule_coverage': 'unavailable', 'game_finality': 'unknown',
        'full_week_final': False, 'reason': 'No pinned schedule source supplied.'}
    if schedule_raw is None:
        return result
    reader = csv.DictReader(io.StringIO(schedule_raw.decode('utf-8-sig')))
    required = {'game_id', 'season', 'week', 'game_type', 'home_team', 'away_team', 'home_score', 'away_score'}
    if not required.issubset(reader.fieldnames or []) or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError('Unsupported schedule columns')
    scope = candidate['scope']
    games = {}
    for r in reader:
        if None in r or any(v is None for v in r.values()):
            raise ValueError('Malformed schedule row')
        if (r['season'], r['week'], r['game_type']) != (str(scope['season']), str(scope['week']), 'REG'):
            continue
        if not r['game_id'] or r['game_id'] in games or not r['home_team'] or not r['away_team'] or r['home_team'] == r['away_team']:
            raise ValueError('Invalid schedule identity')
        games[r['game_id']] = r
    if not games:
        raise ValueError('Schedule scope empty')
    for t in candidate['teams']:
        i = t['identity']
        if i['game_id'] in games:
            g = games[i['game_id']]
            if {i['team'], i['opponent_team']} != {g['home_team'], g['away_team']}:
                raise ValueError('Schedule game/team conflict')
    expected = set(games)
    result.update(scheduled_game_ids=sorted(expected), missing_game_ids=sorted(expected-observed),
        unexpected_game_ids=sorted(observed-expected),
        schedule_coverage='matched' if expected == observed else 'partial_or_conflicting',
        reason='Schedule membership only. Scores and elapsed kickoff time do not certify finality.')
    return result

def prepare(root, source_dir, source_commit, schedule_dir=None, schedule_commit=None, replay_week=None):
    names = ('player.csv', 'team.csv', 'receipt.json', 'LICENSE.md')
    contents = {n: committed(root, source_commit, source_dir/n) for n in names}
    receipt = json.loads(contents['receipt.json'])
    validate_receipt(receipt, contents)
    # Explicit replay scope is a derivation request, never alteration of the acquisition receipt.
    build_receipt = json.loads(json.dumps(receipt))
    if replay_week is not None:
        build_receipt['requested_scope']['week'] = replay_week
    candidate = build_candidate(contents['player.csv'], contents['team.csv'], build_receipt)
    candidate['source_receipt'] = receipt
    candidate['source_support_commit'] = source_commit
    schedule_raw, schedule_receipt = None, None
    if schedule_dir:
        schedule_receipt = json.loads(committed(root, schedule_commit, schedule_dir/'receipt.json'))
        schedule_raw = committed(root, schedule_commit, schedule_dir/'games.csv')
        license_raw = committed(root, schedule_commit, schedule_dir/'LICENSE.md')
        if (sha(license_raw) != AUDITED_LICENSE_SHA256
                or schedule_receipt['attribution']['license_sha256'] != AUDITED_LICENSE_SHA256
                or schedule_receipt['attribution']['name'] != 'nflverse contributors'
                or schedule_receipt['attribution']['license'] != 'CC BY 4.0'
                or schedule_receipt['attribution']['license_source_url'] != LICENSE_URL):
            raise ValueError('Schedule license mismatch')
        if (schedule_receipt.get('status') != 'unadmitted_schedule_snapshot'
                or schedule_receipt.get('source_family') != 'nflverse/nflverse-data/schedules'
                or schedule_receipt.get('schema_version') != 'weekly_schedule_source_candidate_v0'
                or schedule_receipt.get('source_url') != 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv'
                or schedule_receipt.get('release_digest_matched') is not True
                or schedule_receipt.get('sha256') != sha(schedule_raw)
                or schedule_receipt.get('byte_count') != len(schedule_raw)
                or any(k in schedule_receipt for k in ('test_fixture','fixture','demo','synthetic'))):
            raise ValueError('Schedule receipt mismatch')
        if type(schedule_receipt.get('asset_id')) is not int or schedule_receipt['asset_id'] <= 0:
            raise ValueError('Invalid schedule asset')
        for key in ('release_asset_updated_at', 'retrieval_started_at', 'retrieval_completed_at'):
            if datetime.fromisoformat(schedule_receipt[key].replace('Z', '+00:00')).tzinfo is None:
                raise ValueError('Invalid schedule clock')
        schedule_receipt = {**schedule_receipt, 'source_support_commit': schedule_commit}
    return {'schema_version': VERSION, 'status': 'candidate_needs_review', 'consumer_admitted': False,
        'candidate': candidate, 'coverage': coverage(candidate, schedule_raw),
        'schedule_receipt': schedule_receipt, 'source_receipt_sha256': sha(contents['receipt.json']),
        'builder_sha256': sha(Path(__file__).read_bytes()),
        'fact_builder_sha256': sha((root/'scripts/build_weekly_boxscore_candidate_v0.py').read_bytes())}

def publish(envelope, directory):
    """Append revisions with a lock. Index is an unadmitted candidate inventory, never runtime input."""
    scope = envelope['candidate']['scope']
    stream = directory / f"{scope['season']}_REG_w{scope['week']:02d}"
    stream.mkdir(parents=True, exist_ok=True)
    content = canonical(envelope)
    identity = sha(content)
    with (stream/'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        index_path = stream/'index.json'
        index = json.loads(index_path.read_bytes()) if index_path.exists() else {'consumer_admitted': False, 'revisions': []}
        if index.get('consumer_admitted') is not False:
            raise ValueError('Invalid candidate inventory')
        for entry in index['revisions']:
            path = stream/(entry['sha256']+'.json')
            if sha(path.read_bytes()) != entry['sha256']:
                raise ValueError('Revision inventory corruption')
        if index['revisions'] and index['revisions'][-1]['sha256'] == identity:
            return {'status': 'unchanged', 'sha256': identity, 'stream': str(stream)}
        path = stream/(identity+'.json')
        if path.exists():
            if path.read_bytes() != content:
                raise ValueError('Immutable revision conflict')
        else:
            with path.open('xb') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
        index['revisions'].append({'revision': len(index['revisions'])+1, 'sha256': identity,
            'previous_sha256': index['revisions'][-1]['sha256'] if index['revisions'] else None})
        fd, temp = tempfile.mkstemp(dir=stream, prefix='.index-')
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(canonical(index)); f.flush(); os.fsync(f.fileno())
            os.replace(temp, index_path)
        finally:
            if os.path.exists(temp): os.unlink(temp)
    return {'status': 'candidate_revision_written', 'sha256': identity, 'stream': str(stream)}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-dir', type=Path, required=True)
    p.add_argument('--source-commit', required=True)
    p.add_argument('--schedule-dir', type=Path)
    p.add_argument('--schedule-commit')
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    e = prepare(root, args.source_dir, args.source_commit, args.schedule_dir, args.schedule_commit)
    print(json.dumps(publish(e, root/'exports/candidates/weekly_boxscore/revisions')))
