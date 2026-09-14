"""Capture nflverse-data's released schedule as unadmitted coverage evidence, not finality."""
import json
from pathlib import Path
import shutil
import tempfile
from intake_weekly_boxscore_v0 import fetch, digest, clock, LICENSE_URL

URL='https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv'
def schedule_asset():
    j=json.loads(fetch('https://api.github.com/repos/nflverse/nflverse-data/releases/tags/schedules'))
    matches=[a for a in j['assets'] if a['name']=='games.csv']
    if len(matches)!=1: raise ValueError('Schedule asset unavailable')
    return matches[0]

def acquire_schedule(destination):
    before=schedule_asset(); started=clock(); raw=fetch(URL); completed=clock(); after=schedule_asset()
    if any(before[k]!=after[k] for k in ('id','digest','updated_at','size')) or before['digest']!='sha256:'+digest(raw) or before['size']!=len(raw):
        raise ValueError('Schedule release changed or digest mismatch')
    license_raw=fetch(LICENSE_URL,100_000)
    if digest(license_raw)!='2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111': raise ValueError('License changed; audit required')
    receipt={'schema_version':'weekly_schedule_source_candidate_v0','status':'unadmitted_schedule_snapshot',
        'source_family':'nflverse/nflverse-data/schedules','source_url':URL,'asset_id':before['id'],
        'sha256':digest(raw),'byte_count':len(raw),'release_asset_updated_at':before['updated_at'],
        'retrieval_started_at':started,'retrieval_completed_at':completed,'release_digest_matched':True,
        'attribution':{'name':'nflverse contributors','license':'CC BY 4.0', 'license_url':'https://creativecommons.org/licenses/by/4.0/',
            'license_source_url':LICENSE_URL,'license_sha256':digest(license_raw)},
        'limitations':['Released nflverse schedule; no explicit final-status field.',
            'Schedule membership and populated scores do not certify game finality. No admission or activation.']}
    destination.mkdir(parents=True,exist_ok=True); target=destination/digest(raw)
    if target.exists():
        if (target/'games.csv').read_bytes()!=raw or (target/'LICENSE.md').read_bytes()!=license_raw: raise ValueError('Existing snapshot differs')
        return target
    staging=Path(tempfile.mkdtemp(prefix='.schedule-',dir=destination))
    try:
        (staging/'games.csv').write_bytes(raw);(staging/'LICENSE.md').write_bytes(license_raw)
        (staging/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');staging.rename(target)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return target
if __name__=='__main__':
    print(acquire_schedule(Path(__file__).resolve().parents[1]/'data/raw/weekly_schedule'))
