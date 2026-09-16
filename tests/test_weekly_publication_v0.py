import copy
import importlib.util
import json
from pathlib import Path
import sys
import shutil
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import publish_weekly_boxscore_candidate_v0 as pub
import intake_weekly_boxscore_v0 as intake
import intake_weekly_schedule_v0 as schedule_intake
from test_weekly_boxscore_candidate_v0 import fixtures,encode,receipt,box

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/raw/weekly_boxscore/2026_w01_20260914'

class PublicationTests(unittest.TestCase):
    def candidate(self):
        p,t=map(encode,fixtures())
        return box.build_candidate(p,t,receipt(p,t))

    def test_real_receipt_validates_and_fixture_flags_fail(self):
        r=json.loads((SOURCE/'receipt.json').read_bytes())
        content={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md')}
        intake.validate_receipt(r,content)
        for key in ('fixture','demo','synthetic','test_fixture'):
            altered={**r,key:False}
            with self.assertRaisesRegex(ValueError,'Fixture'): intake.validate_receipt(altered,content)
        altered=copy.deepcopy(r);altered['sources']['player']['source_url']='https://example.org/fixture.csv'
        with self.assertRaises(ValueError): intake.validate_receipt(altered,content)
        for kind in ('player','team'):
            altered=copy.deepcopy(r);altered['sources'][kind]['row_count']+=1
            with self.assertRaisesRegex(ValueError,'row count'):intake.validate_receipt(altered,content)
            altered=copy.deepcopy(r);altered['sources'][kind]['row_count']=True
            with self.assertRaisesRegex(ValueError,'row count'):intake.validate_receipt(altered,content)

    def test_intake_noop_and_release_race_fail_closed(self):
        r=json.loads((SOURCE/'receipt.json').read_bytes())
        content={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md')}
        assets={k:{'id':v['asset_id'],'size':v['byte_count'],'digest':'sha256:'+v['sha256'],
            'updated_at':v['release_asset_updated_at']} for k,v in r['sources'].items()}
        def fake_fetch(url,cap=0):
            return content['LICENSE.md' if url==intake.LICENSE_URL else 'player.csv' if 'stats_player/' in url else 'team.csv']
        with tempfile.TemporaryDirectory() as d, patch.object(intake,'asset',side_effect=lambda year,kind:assets[kind]), patch.object(intake,'fetch',side_effect=fake_fetch):
            first,status=intake.acquire(2026,1,Path(d));before=(first/'receipt.json').read_bytes()
            second,status=intake.acquire(2026,1,Path(d))
            self.assertEqual(status,'unchanged');self.assertEqual(first,second)
            self.assertEqual(before,(second/'receipt.json').read_bytes())
        with tempfile.TemporaryDirectory() as d, patch.object(intake,'asset',side_effect=[assets['player'],{**assets['player'],'id':1}]), patch.object(intake,'fetch',side_effect=fake_fetch):
            with self.assertRaisesRegex(ValueError,'changed'):intake.acquire(2026,1,Path(d))
            self.assertEqual(list(Path(d).iterdir()),[])

    def test_intake_reuses_committed_dated_snapshot_without_rewriting_receipt(self):
        r=json.loads((SOURCE/'receipt.json').read_bytes())
        content={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md')}
        assets={k:{'id':v['asset_id'],'size':v['byte_count'],'digest':'sha256:'+v['sha256'],
            'updated_at':v['release_asset_updated_at']} for k,v in r['sources'].items()}
        def fake_fetch(url,cap=0):
            return content['LICENSE.md' if url==intake.LICENSE_URL else 'player.csv' if 'stats_player/' in url else 'team.csv']
        with tempfile.TemporaryDirectory() as d, patch.object(intake,'asset',side_effect=lambda year,kind:assets[kind]), patch.object(intake,'fetch',side_effect=fake_fetch):
            existing=Path(d)/SOURCE.name
            shutil.copytree(SOURCE,existing)
            before={p.name:p.read_bytes() for p in existing.iterdir()}
            actual,status=intake.acquire(2026,1,Path(d))
            self.assertEqual((actual,status),(existing,'unchanged'))
            self.assertEqual(list(Path(d).iterdir()),[existing])
            self.assertEqual(before,{p.name:p.read_bytes() for p in existing.iterdir()})
            # A corrupt legacy snapshot must not be silently reused or replaced.
            (existing/'player.csv').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'digest'): intake.acquire(2026,1,Path(d))
            self.assertEqual(list(Path(d).iterdir()),[existing])

    def test_schedule_reuse_validates_receipt_and_preserves_bytes(self):
        source=next((ROOT/'data/raw/weekly_schedule').glob('*/receipt.json')).parent
        raw=(source/'games.csv').read_bytes(); license_raw=(source/'LICENSE.md').read_bytes()
        receipt_bytes=(source/'receipt.json').read_bytes(); r=json.loads(receipt_bytes)
        asset={'id':r['asset_id'],'size':len(raw),'digest':'sha256:'+pub.sha(raw),'updated_at':r['release_asset_updated_at']}
        mutations=[lambda r:r.update(schema_version='bad'),lambda r:r.update(sha256='0'*64),
            lambda r:r.update(asset_id=1),lambda r:r.update(asset_id=True),lambda r:r.update(release_asset_updated_at='2000-01-01T00:00:00Z'),lambda r:r.update(retrieval_started_at='invalid'),
            lambda r:r['attribution'].update(license='unknown'),lambda r:r.update(fixture=False),
            lambda r:r.update(limitations=[])]
        with tempfile.TemporaryDirectory() as d, patch.object(schedule_intake,'schedule_asset',return_value=asset), patch.object(schedule_intake,'fetch',side_effect=lambda url,*args:raw if url==schedule_intake.URL else license_raw):
            target=Path(d)/pub.sha(raw); shutil.copytree(source,target)
            self.assertEqual(schedule_intake.acquire_schedule(Path(d)),target)
            self.assertEqual((target/'receipt.json').read_bytes(),receipt_bytes)
            for mutate in mutations:
                altered=copy.deepcopy(r); mutate(altered)
                bad=json.dumps(altered).encode();(target/'receipt.json').write_bytes(bad)
                with self.assertRaises(ValueError):schedule_intake.acquire_schedule(Path(d))
                self.assertEqual((target/'receipt.json').read_bytes(),bad)
            (target/'receipt.json').write_bytes(b'{broken')
            with self.assertRaises(ValueError):schedule_intake.acquire_schedule(Path(d))
            (target/'receipt.json').unlink()
            with self.assertRaises(FileNotFoundError):schedule_intake.acquire_schedule(Path(d))
            self.assertEqual(list(Path(d).iterdir()),[target])

    def test_schedule_receipt_rejects_release_after_retrieval(self):
        source=next((ROOT/'data/raw/weekly_schedule').glob('*/receipt.json')).parent
        raw=(source/'games.csv').read_bytes();license_raw=(source/'LICENSE.md').read_bytes()
        r=json.loads((source/'receipt.json').read_bytes())
        r['release_asset_updated_at']='2099-01-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'clock order'):
            schedule_intake.validate_schedule_receipt(r,raw,license_raw)

    def test_boxscore_reuse_binds_both_assets_in_both_directory_formats(self):
        r=json.loads((SOURCE/'receipt.json').read_bytes())
        contents={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md')}
        assets={k:{'id':v['asset_id'],'size':v['byte_count'],'digest':'sha256:'+v['sha256'],
            'updated_at':v['release_asset_updated_at']} for k,v in r['sources'].items()}
        def fake_fetch(url,*args):
            return contents['LICENSE.md' if url==intake.LICENSE_URL else 'player.csv' if 'stats_player/' in url else 'team.csv']
        for legacy in (False,True):
            for kind in ('player','team'):
                with self.subTest(legacy=legacy,kind=kind), tempfile.TemporaryDirectory() as d, patch.object(intake,'asset',side_effect=lambda year,k:assets[k]), patch.object(intake,'fetch',side_effect=fake_fetch):
                    if legacy:
                        target=Path(d)/SOURCE.name;shutil.copytree(SOURCE,target)
                    else:target,_=intake.acquire(2026,1,Path(d))
                    saved=json.loads((target/'receipt.json').read_bytes());saved['sources'][kind]['release_asset_updated_at']='2000-01-01T00:00:00Z'
                    (target/'receipt.json').write_bytes(pub.canonical(saved))
                    before={p.name:p.read_bytes() for p in target.iterdir()}
                    with self.assertRaisesRegex(ValueError,'timestamp'):intake.acquire(2026,1,Path(d))
                    self.assertEqual(before,{p.name:p.read_bytes() for p in target.iterdir()})
                    self.assertEqual(list(Path(d).iterdir()),[target])
                    saved['sources'][kind]['release_asset_updated_at']=r['sources'][kind]['release_asset_updated_at']
                    saved['sources'][kind]['asset_id']=1
                    (target/'receipt.json').write_bytes(pub.canonical(saved))
                    with self.assertRaisesRegex(ValueError,'asset'):intake.acquire(2026,1,Path(d))

    def test_reused_asset_timestamps_accept_equivalent_offsets(self):
        r=json.loads((SOURCE/'receipt.json').read_bytes());prior=copy.deepcopy(r)
        for source in prior['sources'].values():
            source['release_asset_updated_at']=source['release_asset_updated_at'].replace('Z','+00:00')
        intake.validate_reused_assets(prior,r['sources'])

    def test_receipt_clocks_fail_closed_in_both_directory_formats(self):
        r=json.loads((SOURCE/'receipt.json').read_bytes())
        contents={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md')}
        assets={k:{'id':v['asset_id'],'size':v['byte_count'],'digest':'sha256:'+v['sha256'],
            'updated_at':v['release_asset_updated_at']} for k,v in r['sources'].items()}
        def fake_fetch(url,*args):
            return contents['LICENSE.md' if url==intake.LICENSE_URL else 'player.csv' if 'stats_player/' in url else 'team.csv']
        mutations=[('invalid compiled',lambda r:r.update(snapshot_compiled_at='invalid')),
            ('naive compiled',lambda r:r.update(snapshot_compiled_at='2026-09-14T13:16:53')),
            ('early compiled',lambda r:r.update(snapshot_compiled_at='2000-01-01T00:00:00Z'))]
        for kind in ('player','team'):
            mutations.append((kind+' reversed',lambda r,k=kind:r['sources'][k].update(retrieval_completed_at='2000-01-01T00:00:00Z')))
            mutations.append((kind+' updated after retrieval',lambda r,k=kind:r['sources'][k].update(release_asset_updated_at='2099-01-01T00:00:00Z')))
        for legacy in (False,True):
            for label,mutate in mutations:
                with self.subTest(legacy=legacy,mutation=label), tempfile.TemporaryDirectory() as d, patch.object(intake,'asset',side_effect=lambda year,k:assets[k]), patch.object(intake,'fetch',side_effect=fake_fetch):
                    if legacy:
                        target=Path(d)/SOURCE.name;shutil.copytree(SOURCE,target)
                    else:target,_=intake.acquire(2026,1,Path(d))
                    saved=json.loads((target/'receipt.json').read_bytes());mutate(saved)
                    (target/'receipt.json').write_bytes(pub.canonical(saved))
                    before={p.name:p.read_bytes() for p in target.iterdir()}
                    with self.assertRaises(ValueError):intake.acquire(2026,1,Path(d))
                    self.assertEqual(before,{p.name:p.read_bytes() for p in target.iterdir()})
                    self.assertEqual(list(Path(d).iterdir()),[target])

    def test_asset_updates_cannot_fall_inside_retrieval_window(self):
        r=json.loads((SOURCE/'receipt.json').read_bytes())
        contents={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md')}
        for kind in ('player','team'):
            with self.subTest(kind=kind):
                altered=copy.deepcopy(r)
                altered['sources'][kind].update(release_asset_updated_at='2026-09-14T12:01:00Z',
                    retrieval_started_at='2026-09-14T12:00:00Z',retrieval_completed_at='2026-09-14T12:02:00Z')
                with self.assertRaisesRegex(ValueError,'clock ordering'):
                    intake.validate_receipt(altered,contents)
        source=next((ROOT/'data/raw/weekly_schedule').glob('*/receipt.json')).parent
        schedule=json.loads((source/'receipt.json').read_bytes())
        schedule.update(release_asset_updated_at='2026-09-14T12:01:00Z',
            retrieval_started_at='2026-09-14T12:00:00Z',retrieval_completed_at='2026-09-14T12:02:00Z')
        with self.subTest(kind='schedule'):
            with self.assertRaisesRegex(ValueError,'clock order'):
                schedule_intake.validate_schedule_receipt(schedule,(source/'games.csv').read_bytes(),(source/'LICENSE.md').read_bytes())
        schedule['release_asset_updated_at']='2026-09-14T08:00:00-04:00'
        schedule_intake.validate_schedule_receipt(schedule,(source/'games.csv').read_bytes(),(source/'LICENSE.md').read_bytes())

    def test_team_retrieval_cannot_overlap_player_retrieval(self):
        r=json.loads((SOURCE/'receipt.json').read_bytes())
        contents={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md')}
        r['sources']['player'].update(release_asset_updated_at='2026-09-14T12:00:00Z',
            retrieval_started_at='2026-09-14T12:00:00Z',retrieval_completed_at='2026-09-14T12:02:00Z')
        r['sources']['team'].update(release_asset_updated_at='2026-09-14T12:00:00Z',
            retrieval_started_at='2026-09-14T12:01:00Z',retrieval_completed_at='2026-09-14T12:03:00Z')
        with self.assertRaisesRegex(ValueError,'cross-asset'):
            intake.validate_receipt(r,contents)
        r['sources']['team']['retrieval_started_at']='2026-09-14T08:02:00-04:00'
        intake.validate_receipt(r,contents)

    def test_receipt_clock_order_uses_instants_and_allows_equality(self):
        r=json.loads((SOURCE/'receipt.json').read_bytes())
        contents={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md')}
        r['snapshot_compiled_at']='2026-09-14T10:00:00-04:00'
        for source in r['sources'].values():
            source['release_asset_updated_at']='2026-09-14T09:00:00-04:00'
            source['retrieval_started_at']='2026-09-14T15:00:00+02:00'
            source['retrieval_completed_at']='2026-09-14T14:00:00Z'
        r['sources']['team']['retrieval_started_at']='2026-09-14T10:00:00-04:00'
        intake.validate_receipt(r,contents)

    def test_standalone_builder_validates_source_lane_before_output(self):
        for mutation in ('valid','fixture','test_fixture','url','license'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(dir=ROOT/'exports/candidates/weekly_boxscore') as d:
                source=Path(d)/'source';source.mkdir();out=Path(d)/'candidate.json'
                contents={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md','receipt.json')}
                r=json.loads(contents['receipt.json'])
                if mutation in ('fixture','test_fixture'):r[mutation]=False
                elif mutation=='url':r['sources']['player']['source_url']='https://example.test/unsupported'
                elif mutation=='license':
                    contents['LICENSE.md']=b'Changed terms';r['attribution']['license_sha256']=pub.sha(contents['LICENSE.md'])
                contents['receipt.json']=pub.canonical(r)
                for name,raw in contents.items():(source/name).write_bytes(raw)
                def fake_git(args,**kwargs):
                    return str(ROOT)+'\n' if args[1]=='rev-parse' else contents[Path(args[2]).name]
                argv=['builder','--source-dir',str(source),'--source-commit','a'*40,'--output',str(out)]
                with patch.object(sys,'argv',argv),patch.object(box.subprocess,'check_output',side_effect=fake_git):
                    if mutation=='valid':
                        with patch('builtins.print'):box.main()
                    else:
                        with self.assertRaises(ValueError):box.main()
                self.assertEqual(out.exists(),mutation=='valid')

    def test_revision_chain_corruption_rejected_before_noop_or_append(self):
        first={'candidate':self.candidate()}; second=copy.deepcopy(first)
        second['candidate']['players'][0]['observed']['receiving_yards']=42
        third=copy.deepcopy(second);third['candidate']['players'][0]['observed']['receiving_yards']=43
        mutations=[lambda r:r.reverse(),lambda r:r[1].update(revision=9),
            lambda r:r[0].update(revision=True),lambda r:r[1].update(previous_sha256='0'*64),
            lambda r:r[0].pop('previous_sha256'),lambda r:r[0].update(sha256='../bad')]
        for mutate in mutations:
            with tempfile.TemporaryDirectory() as d:
                pub.publish(first,Path(d));result=pub.publish(second,Path(d));stream=Path(result['stream'])
                index=stream/'index.json';value=json.loads(index.read_bytes());mutate(value['revisions'])
                index.write_bytes(pub.canonical(value));before={p.name:p.read_bytes() for p in stream.iterdir()}
                for candidate in (second,third):
                    with self.assertRaisesRegex(ValueError,'revision chain'):pub.publish(candidate,Path(d))
                    self.assertEqual(before,{p.name:p.read_bytes() for p in stream.iterdir()})

    def test_prepare_rejects_fixture_receipt_at_publication_boundary(self):
        content={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md','receipt.json')}
        r=json.loads(content['receipt.json']);r['test_fixture']=True
        content['receipt.json']=json.dumps(r).encode()
        with patch.object(pub,'committed',side_effect=lambda root,commit,path:content[path.name]):
            with self.assertRaisesRegex(ValueError,'Fixture'):pub.prepare(ROOT,SOURCE,'a'*40)

    def test_changed_license_rejected_even_when_receipt_hash_matches(self):
        r=json.loads((SOURCE/'receipt.json').read_bytes())
        content={n:(SOURCE/n).read_bytes() for n in ('player.csv','team.csv','LICENSE.md')}
        content['LICENSE.md']=b'Changed terms'
        r['attribution']['license_sha256']=pub.sha(content['LICENSE.md'])
        with self.assertRaisesRegex(ValueError,'License'):intake.validate_receipt(r,content)

    def test_publication_wrapper_rejects_uncommitted_support(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            with self.assertRaises(Exception): pub.prepare(ROOT,Path(d),'0'*40)

    def test_schedule_publication_arguments_are_an_optional_pair(self):
        cases=((ROOT,None),(None,'a'*40))
        for schedule_dir,schedule_commit in cases:
            with self.subTest(schedule_dir=schedule_dir,schedule_commit=schedule_commit), patch.object(pub,'committed') as committed:
                with self.assertRaisesRegex(ValueError,'pair'):
                    pub.prepare(ROOT,SOURCE,'a'*40,schedule_dir,schedule_commit)
                committed.assert_not_called()

    def test_no_schedule_never_means_complete(self):
        c=pub.coverage(self.candidate())
        self.assertIsNone(c['scheduled_game_ids']);self.assertFalse(c['full_week_final'])

    def schedule(self, extra=False, conflict=False):
        return encode([{'game_id':'SYNTHETIC_GAME','season':2026,'week':1,'game_type':'REG',
            'home_team':'AAA','away_team':'CCC' if conflict else 'BBB','home_score':21,'away_score':7}]+
            ([{'game_id':'SYNTHETIC_MISSING','season':2026,'week':1,'game_type':'REG',
            'home_team':'DDD','away_team':'EEE','home_score':'','away_score':''}] if extra else []))

    def test_schedule_match_does_not_certify_finality(self):
        c=pub.coverage(self.candidate(),self.schedule())
        self.assertEqual(c['schedule_coverage'],'matched');self.assertEqual(c['game_finality'],'unknown')

    def test_missing_game_reported(self):
        c=pub.coverage(self.candidate(),self.schedule(extra=True))
        self.assertEqual(c['missing_game_ids'],['SYNTHETIC_MISSING'])

    def test_schedule_conflict_and_duplicates_rejected(self):
        with self.assertRaises(ValueError): pub.coverage(self.candidate(),self.schedule(conflict=True))
        raw=self.schedule();raw+=raw.splitlines(keepends=True)[1]
        with self.assertRaises(ValueError): pub.coverage(self.candidate(),raw)

    def test_noop_correction_and_prior_bytes_preserved(self):
        e={'candidate':self.candidate()}
        with tempfile.TemporaryDirectory() as d:
            first=pub.publish(e,Path(d)); path=Path(first['stream'])/(first['sha256']+'.json'); before=path.read_bytes()
            again=pub.publish(e,Path(d));self.assertEqual(again['status'],'unchanged')
            updated=copy.deepcopy(e);updated['candidate']['players'][0]['observed']['receiving_yards']=31
            second=pub.publish(updated,Path(d))
            self.assertNotEqual(first['sha256'],second['sha256']);self.assertEqual(path.read_bytes(),before)
            index=json.loads((Path(first['stream'])/'index.json').read_bytes())
            self.assertEqual(len(index['revisions']),2)
            self.assertEqual(index['revisions'][1]['previous_sha256'],first['sha256'])
            path.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):pub.publish(updated,Path(d))

if __name__=='__main__':unittest.main()
