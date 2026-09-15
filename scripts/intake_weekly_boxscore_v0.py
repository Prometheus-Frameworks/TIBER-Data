"""Explicit nflverse CSV intake. Writes unadmitted raw snapshots only; never schedules itself."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LICENSE_URL = 'https://raw.githubusercontent.com/nflverse/nflverse-data/master/LICENSE.md'
AUDITED_LICENSE_SHA256 = '2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111'
RECEIPT_SCHEMA = 'weekly_boxscore_source_receipt_candidate_v0'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def clock():
    return datetime.now(timezone.utc).isoformat()

def fetch(url, cap=25_000_000):
    request = urllib.request.Request(url, headers={'User-Agent': 'TIBER-weekly-candidate-v0'})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(cap + 1)
    if len(raw) > cap:
        raise ValueError('Source exceeds byte cap')
    return raw

def asset(season, kind):
    tag = 'stats_' + kind
    release = json.loads(fetch(f'https://api.github.com/repos/nflverse/nflverse-data/releases/tags/{tag}'))
    matches = [a for a in release['assets'] if a['name'] == f'{tag}_week_{season}.csv']
    if len(matches) != 1:
        raise ValueError('Exact release asset unavailable')
    a = matches[0]
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', a.get('digest') or ''):
        raise ValueError('Release digest unavailable')
    return a

def receipt_clock(value):
    if not isinstance(value, str):
        raise ValueError('Source clock must be a timestamp')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Source clock must include offset')
    return dt

def validate_receipt(receipt, contents):
    if receipt.get('schema_version') != RECEIPT_SCHEMA or receipt.get('status') != 'unadmitted_candidate_source_snapshot':
        raise ValueError('Unsupported source receipt')
    if any(k in receipt for k in ('test_fixture', 'fixture', 'demo', 'synthetic')):
        raise ValueError('Fixture flags forbidden in source lane')
    scope = receipt['requested_scope']
    if type(scope.get('season')) is not int or not 1900 <= scope['season'] <= 2200 or scope.get('season_type') != 'REG' or type(scope.get('week')) is not int or not 1 <= scope['week'] <= 18:
        raise ValueError('Invalid explicit scope')
    compiled = receipt_clock(receipt.get('snapshot_compiled_at'))
    for kind in ('player', 'team'):
        p = receipt['sources'][kind]
        url = f"https://github.com/nflverse/nflverse-data/releases/download/stats_{kind}/stats_{kind}_week_{scope['season']}.csv"
        if p['source_url'] != url or p['file'] != kind + '.csv' or type(p['asset_id']) is not int or p['asset_id'] <= 0 or p.get('release_digest_matched') is not True:
            raise ValueError('Unsupported source family or asset')
        receipt_clock(p['release_asset_updated_at'])
        started = receipt_clock(p['retrieval_started_at'])
        completed = receipt_clock(p['retrieval_completed_at'])
        if not started <= completed <= compiled:
            raise ValueError('Source clock ordering invalid')
        raw = contents[kind + '.csv']
        if len(raw) != p['byte_count'] or digest(raw) != p['sha256']:
            raise ValueError('Source digest mismatch')
    a = receipt['attribution']
    if a['name'] != 'nflverse contributors' or a['license'] != 'CC BY 4.0' or a['license_source_url'] != LICENSE_URL or digest(contents['LICENSE.md']) != a['license_sha256'] or a['license_sha256'] != AUDITED_LICENSE_SHA256:
        raise ValueError('License snapshot mismatch')

def validate_reused_assets(prior, sources):
    for kind in ('player', 'team'):
        if prior['sources'][kind]['asset_id'] != sources[kind]['asset_id']:
            raise ValueError('Existing box-score receipt asset mismatch')
        saved = datetime.fromisoformat(prior['sources'][kind]['release_asset_updated_at'].replace('Z', '+00:00'))
        fetched = datetime.fromisoformat(sources[kind]['release_asset_updated_at'].replace('Z', '+00:00'))
        if saved != fetched:
            raise ValueError('Existing box-score release timestamp mismatch')

def acquire(season, week, destination):
    if not 1900 <= season <= 2200 or not 1 <= week <= 18:
        raise ValueError('Invalid scope')
    sources, contents = {}, {}
    for kind in ('player', 'team'):
        before = asset(season, kind)
        url = f'https://github.com/nflverse/nflverse-data/releases/download/stats_{kind}/stats_{kind}_week_{season}.csv'
        started = clock()
        raw = fetch(url)
        completed = clock()
        after = asset(season, kind)
        keys = ('id', 'size', 'digest', 'updated_at')
        if any(before[k] != after[k] for k in keys) or len(raw) != before['size'] or 'sha256:' + digest(raw) != before['digest']:
            raise ValueError('Release changed during intake; retry explicitly')
        contents[kind + '.csv'] = raw
        sources[kind] = {'file': kind + '.csv', 'source_url': url, 'asset_id': before['id'],
            'release_asset_updated_at': before['updated_at'], 'retrieval_started_at': started,
            'retrieval_completed_at': completed, 'sha256': digest(raw), 'byte_count': len(raw), 'release_digest_matched': True}
    contents['LICENSE.md'] = fetch(LICENSE_URL, 100_000)
    # Fixed existing license family. Changed terms require a new audit, not auto-acceptance.
    if digest(contents['LICENSE.md']) != '2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111':
        raise ValueError('License bytes changed; audit required')
    receipt = {'schema_version': RECEIPT_SCHEMA, 'status': 'unadmitted_candidate_source_snapshot',
        'requested_scope': {'season': season, 'season_type': 'REG', 'week': week}, 'snapshot_compiled_at': clock(),
        'sources': sources, 'attribution': {'name': 'nflverse contributors', 'license': 'CC BY 4.0',
            'license_url': 'https://creativecommons.org/licenses/by/4.0/', 'license_source_url': LICENSE_URL,
            'license_sha256': digest(contents['LICENSE.md']), 'notice': 'No endorsement implied; candidate, not admitted evidence.'},
        'limitations': ['Separate player/team retrievals are not an atomic upstream snapshot.',
            'Release clocks are not game finality or pre-cutoff availability witnesses.',
            'Missing observations are unknown. No source promotion or consumer activation.']}
    validate_receipt(receipt, contents)
    identity = digest(json.dumps([season, week, sources['player']['sha256'], sources['team']['sha256'], receipt['attribution']['license_sha256']]).encode())
    target = destination / f'{season}_w{week:02d}_{identity}'
    destination.mkdir(parents=True, exist_ok=True)
    if target.exists():
        prior = json.loads((target / 'receipt.json').read_bytes())
        validate_receipt(prior, {n: (target/n).read_bytes() for n in contents})
        if prior['requested_scope'] != receipt['requested_scope'] or any((target/n).read_bytes() != raw for n, raw in contents.items()):
            raise ValueError('Existing immutable snapshot differs')
        validate_reused_assets(prior, sources)
        return target, 'unchanged'
    # Older unadmitted snapshots used dated directory names. Preserve their
    # original receipt and path when validated source bytes match exactly.
    for existing in sorted(destination.glob(f'{season}_w{week:02d}_*')):
        if not existing.is_dir():
            continue
        prior = json.loads((existing / 'receipt.json').read_bytes())
        prior_contents = {n: (existing/n).read_bytes() for n in contents}
        validate_receipt(prior, prior_contents)
        if prior['requested_scope'] == receipt['requested_scope'] and prior_contents == contents:
            validate_reused_assets(prior, sources)
            return existing, 'unchanged'
    staging = Path(tempfile.mkdtemp(prefix='.intake-', dir=destination))
    try:
        for name, raw in contents.items():
            (staging/name).write_bytes(raw)
        (staging/'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        staging.rename(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return target, 'candidate_written'

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--season', type=int, required=True)
    p.add_argument('--week', type=int, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    path, status = acquire(args.season, args.week, root/'data/raw/weekly_boxscore')
    print(json.dumps({'path': str(path), 'status': status, 'next': 'Commit raw support before offline building.'}))
