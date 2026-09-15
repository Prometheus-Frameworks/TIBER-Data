"""Capture nflverse-data's released schedule as unadmitted coverage evidence, not finality."""
import json
from datetime import datetime
from pathlib import Path
import shutil
import tempfile
from intake_weekly_boxscore_v0 import fetch, digest, clock, LICENSE_URL, AUDITED_LICENSE_SHA256

URL='https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv'
def validate_schedule_receipt(receipt, raw, license_raw):
    expected = {'schema_version':'weekly_schedule_source_candidate_v0',
        'status':'unadmitted_schedule_snapshot','source_family':'nflverse/nflverse-data/schedules',
        'source_url':URL,'sha256':digest(raw),'byte_count':len(raw),'release_digest_matched':True}
    if not isinstance(receipt, dict) or any(receipt.get(k) != v for k,v in expected.items()):
        raise ValueError('Schedule receipt mismatch')
    if receipt.get('release_digest_matched') is not True or type(receipt.get('byte_count')) is not int or any(k in receipt for k in ('test_fixture','fixture','demo','synthetic')):
        raise ValueError('Schedule receipt mismatch')
    if type(receipt.get('asset_id')) is not int or receipt['asset_id'] <= 0:
        raise ValueError('Invalid schedule asset')
    dates=[]
    for key in ('release_asset_updated_at','retrieval_started_at','retrieval_completed_at'):
        value=receipt.get(key)
        if not isinstance(value,str): raise ValueError('Invalid schedule clock')
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        if dt.tzinfo is None: raise ValueError('Invalid schedule clock')
        dates.append(dt)
    if dates[0]>dates[2] or dates[1]>dates[2]: raise ValueError('Invalid schedule clock order')
    expected_attribution={'name':'nflverse contributors','license':'CC BY 4.0',
        'license_url':'https://creativecommons.org/licenses/by/4.0/',
        'license_source_url':LICENSE_URL,'license_sha256':AUDITED_LICENSE_SHA256}
    if receipt.get('attribution')!=expected_attribution or digest(license_raw)!=AUDITED_LICENSE_SHA256:
        raise ValueError('Schedule license mismatch')
    limitations=receipt.get('limitations')
    if not isinstance(limitations,list) or not limitations or any(not isinstance(v,str) or not v.strip() for v in limitations):
        raise ValueError('Invalid schedule limitations')

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
    validate_schedule_receipt(receipt,raw,license_raw)
    destination.mkdir(parents=True,exist_ok=True); target=destination/digest(raw)
    if target.exists():
        if (target/'games.csv').read_bytes()!=raw or (target/'LICENSE.md').read_bytes()!=license_raw: raise ValueError('Existing snapshot differs')
        saved=json.loads((target/'receipt.json').read_bytes())
        validate_schedule_receipt(saved,raw,license_raw)
        if saved['asset_id']!=before['id']:
            raise ValueError('Existing schedule receipt asset mismatch')
        if datetime.fromisoformat(saved['release_asset_updated_at'].replace('Z','+00:00')) != datetime.fromisoformat(before['updated_at'].replace('Z','+00:00')):
            raise ValueError('Existing schedule release timestamp mismatch')
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
