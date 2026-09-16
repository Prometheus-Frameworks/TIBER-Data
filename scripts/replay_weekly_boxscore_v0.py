"""Offline completed-season replay; compact evidence report, no promotion."""
import argparse
import json
from pathlib import Path
from publish_weekly_boxscore_candidate_v0 import prepare, canonical, sha

def replay(root, source_dir, source_commit, season, schedule_dir=None, schedule_commit=None):
    reports = []
    for week in range(1,19):
        e = prepare(root, source_dir, source_commit, schedule_dir, schedule_commit, replay_week=week)
        c = e['candidate']
        if c['scope']['season'] != season:
            raise ValueError('Replay source season mismatch')
        reports.append({'week': week, 'artifact_sha256': sha(canonical(e)),
            'coverage': e['coverage'], 'source_counts': c['coverage'], 'validation': c['validation']})
    return {'schema_version': 'weekly_boxscore_replay_report_v0', 'status': 'candidate_replay_completed',
        'season': season, 'source_support_commit': source_commit, 'weeks': reports,
        'limitations': ['Retrospective replay uses currently acquired corrected historical bytes.',
            'Not an as-of backtest or evidence that bytes were available before historical kickoffs.',
            'No scoring, role baseline, pace model or live evidence promotion; consumer scoring tested separately.',
            'Internal reconciliation is not independent provider corroboration.']}

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-dir', type=Path, required=True)
    p.add_argument('--source-commit', required=True)
    p.add_argument('--season', type=int, required=True)
    p.add_argument('--schedule-dir', type=Path)
    p.add_argument('--schedule-commit')
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args(); root=Path(__file__).resolve().parents[1]
    a.output.resolve().relative_to(root/'docs/audits')
    r=replay(root,a.source_dir,a.source_commit,a.season,a.schedule_dir,a.schedule_commit)
    with a.output.open('xb') as f: f.write(canonical(r))
    print(json.dumps({'weeks':len(r['weeks']), 'games':sum(w['source_counts']['game_count'] for w in r['weeks']),
        'conflicts':sum(len(w['validation']['metric_conflicts']) for w in r['weeks'])}))
