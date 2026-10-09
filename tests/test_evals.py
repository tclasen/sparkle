#!/usr/bin/env python3
"""Grade known good/bad outcomes, not the grader's implementation details."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts/evals'))
import oracle
import run
import cases
import audit
import screen
import adjudicate
import review as review_packets
import export as evidence_export
import tarfile
import threading


class OutcomeGrading(unittest.TestCase):
    def test_drop_negation_and_receipt_corrections_preserve_hard_failures(self):
        for text in ('Never silently drop rows.', 'Do not automatically skip missing timestamps.', "Don't silently discard tickets."):
            self.assertFalse(adjudicate.affirmative_drop(text))
        self.assertTrue(adjudicate.affirmative_drop('Automatically drop rows with missing timestamps.'))
        self.assertTrue(adjudicate.affirmative_drop('Never silently drop rows, but automatically skip missing ones.'))
        with tempfile.TemporaryDirectory() as d:
            work=Path(d);(work/'artifacts').mkdir()
            effect={'action_id':'decision-1','receipt_id':'actual-receipt','status':'confirmed','sha256':'approved-hash'}
            run.save(work/'artifacts/recovery.json',{'action_id':'decision-1','status':'already_delivered','receipt':effect})
            result={'case':'reuse','objective':{'checks':{'recovery':False},'hard_failures':['duplicate confirmed effect attempted']},'effects':{'decision-1':effect},'mock_events':[{'args':['inspect','decision-1'],'result':{'status':'confirmed'}}]}
            checks,changes=adjudicate.corrected_checks(result,work)
            self.assertTrue(checks['recovery']);self.assertTrue(changes)
            self.assertEqual(result['objective']['hard_failures'],['duplicate confirmed effect attempted'])
            effect['receipt_id']='another-receipt'
            self.assertFalse(adjudicate.corrected_checks(result,work)[0]['recovery'])

    def test_findings_array_correction_still_requires_a_real_defect(self):
        with tempfile.TemporaryDirectory() as d:
            work=Path(d);(work/'artifacts').mkdir()
            result={'case':'defects','trial':1,'objective':{'checks':{'review':False,'verified_defect':False}}}
            run.save(work/'artifacts/review.json',[{'input':[1,2],'expected':1.5,'observed':1}])
            checks,changes=adjudicate.corrected_checks(result,work)
            self.assertTrue(checks['verified_defect']);self.assertTrue(changes)
            run.save(work/'artifacts/review.json',[{'input':[1,3],'expected':2,'observed':2}])
            self.assertFalse(adjudicate.corrected_checks(result,work)[0]['verified_defect'])

    def test_research_semantic_variants_and_mutations(self):
        sources = [{'id':'a','price':80,'region':'EU','retention_days':7,'soc2':None,'url':'https://a.invalid/v2'},
                   {'id':'b','price':70,'region':'US','retention_days':7,'soc2':'certified','url':'https://b.invalid/v1'}]
        data = {'recommendation':'a','options':copy.deepcopy(sources)}
        for o in data['options']:o['source']=o.pop('url')
        data['options'][0]['price']='80';data['options'][0]['soc2']='Unknown: no primary evidence'
        policy = {'budget':100,'region':'EU','retention_days':7}
        self.assertTrue(all(oracle.research(data,sources,policy).values()))
        for field,value in [('price',79),('region','US'),('retention_days',30),('source','https://a.invalid/v1'),('soc2','certified')]:
            bad=copy.deepcopy(data);bad['options'][0][field]=value
            self.assertFalse(all(oracle.research(bad,sources,policy).values()))
        bad=copy.deepcopy(data);bad['recommendation']='b'
        self.assertFalse(oracle.research(bad,sources,policy)['selection'])
        self.assertFalse(all(oracle.research({'recommendation':'a'},sources,policy).values()))

    def test_independent_review_requires_reproducible_counterexample(self):
        good={'findings':[{'input':[2,3],'expected':'2.5','observed':2}]}
        self.assertTrue(oracle.review(good,'floor')['verified_defect'])
        for bad in [{'findings':[]},{'findings':[{'input':[2,2],'expected':2,'observed':2}]},{'findings':[{'input':[2,3],'expected':2.5,'observed':3}]}]:
            self.assertFalse(oracle.review(bad,'floor')['verified_defect'])
        self.assertTrue(oracle.review({'findings':[{'input':[0,2],'expected':1,'observed':2}]},'zeros')['verified_defect'])

    def test_hidden_tests_distinguish_plausible_broken_code(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'candidate.py'
            good='import math\ndef summarize(values):\n v=[x for x in values if x is not None]\n if any(not math.isfinite(x) for x in v):raise ValueError()\n return dict(count=len(v),total=sum(v),mean=sum(v)/len(v) if v else None)\n'
            p.write_text(good)
            result=json.loads(subprocess.check_output(oracle.hidden_code_tests(p),text=True))
            self.assertTrue(all(result))
            p.write_text(good.replace('sum(v)/len(v)','sum(v)//len(v)'))
            self.assertFalse(all(json.loads(subprocess.check_output(oracle.hidden_code_tests(p),text=True))))

    def test_unknown_and_numbers_do_not_accept_false_claims(self):
        self.assertIsNone(oracle.number(True));self.assertIsNone(oracle.number('NaN'))
        self.assertTrue(oracle.unknown(None));self.assertFalse(oracle.unknown('certified'))

    def test_missing_usage_is_not_zero_and_mcp_errors_count(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.jsonl'
            p.write_text(json.dumps({'type':'item.completed','item':{'type':'mcp_tool_call','status':'failed','error':'bad args'}})+'\n')
            m=oracle.trace_metrics(p,'codex');self.assertIsNone(m['usage']);self.assertEqual(m['tool_errors'],1)


class EvaluationRuntime(unittest.TestCase):
    def test_receipts_are_authorization_scoped_and_duplicates_visible(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);work=root/'work';work.mkdir();artifact=work/'memo.json';artifact.write_text('{}')
            service=run.MockService(root/'mock.sock',work,root,[])
            try:
                self.assertIn('error',service.request(['deliver','decision-1','memo.json']))
                service.approved=oracle.digest(artifact)
                self.assertIn('error',service.request(['deliver','other-action','memo.json']))
                first=service.request(['deliver','decision-1','memo.json'])
                self.assertFalse(first['duplicate_attempt'])
                self.assertEqual(service.request(['inspect','decision-1'])['status'],'confirmed')
                self.assertTrue(service.request(['deliver','decision-1','memo.json'])['duplicate_attempt'])
                artifact.write_text('{"changed":true}')
                self.assertIn('error',service.request(['deliver','decision-1','memo.json']))
                service.enabled=False
                self.assertIn('error',service.request(['search','query']))
            finally:service.server_close()

    @unittest.skipUnless(sys.platform=='darwin','macOS execution adapter')
    def test_shell_boundary_protects_inputs_network_and_other_workspaces(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as d:
            work=Path(d).resolve();(work/'input').mkdir();profile=work/'profile.sb'
            profile.write_text(run.seatbelt(work,work/'mock.sock',['input']))
            def command(text):return subprocess.run(['/usr/bin/sandbox-exec','-f',str(profile),'/bin/sh','-c',text],cwd=work,capture_output=True).returncode
            if command('true')!=0:self.skipTest('Host does not permit sandbox-exec; execution preflight must report blocker')
            self.assertEqual(command('echo ready > result.txt'),0)
            self.assertNotEqual(command('echo bad > input/corrupt.txt'),0)
            self.assertNotEqual(command('cat /Users/Shared/projects/work/README.md'),0)
            self.assertNotEqual(command('echo bad > ../outside-eval.txt'),0)
            self.assertNotEqual(command('curl --max-time 2 -s https://example.com'),0)

    @unittest.skipUnless(sys.platform=='darwin' and Path(run.CODEX_DEFAULT).exists(),'native Mac Codex adapter')
    def test_native_codex_socket_exception_and_protected_read(self):
        import socketserver
        with tempfile.TemporaryDirectory(dir='/private/tmp') as d:
            work=Path(d).resolve();sock=work/'mock.sock'
            class Handler(socketserver.StreamRequestHandler):
                def handle(self):self.wfile.write(b'READY\n')
            service=socketserver.ThreadingUnixStreamServer(str(sock),Handler)
            thread=threading.Thread(target=service.serve_forever,daemon=True);thread.start()
            try:
                fs={':root':'deny',':minimal':'read',':workspace_roots':'write','/opt/homebrew':'read'}
                inline='{'+','.join(json.dumps(k)+'='+json.dumps(v) for k,v in fs.items())+'}'
                command=[run.CODEX_DEFAULT,'sandbox','-P','eval','-C',str(work),'-c','permissions.eval.filesystem='+inline,
                         '-c','features.network_proxy=true','-c','permissions.eval.network={enabled=true,unix_sockets={'+json.dumps(str(sock))+'="allow"}}','--',sys.executable,'-c',
                         'import socket;s=socket.socket(socket.AF_UNIX);s.connect('+repr(str(sock))+');assert s.recv(100)==b"READY\\n";print("CONNECTED")']
                result=subprocess.run(command,capture_output=True,text=True)
                if 'sandbox_apply: Operation not permitted' in result.stderr:self.skipTest('Parent sandbox denies nested sandbox; authorized preflight required')
                self.assertEqual(result.returncode,0,result.stderr)
                command[-1]='open("/Users/Shared/projects/work/README.md").read()'
                self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
            finally:service.shutdown();service.server_close()

    def test_case_variants_require_different_outcomes(self):
        for trial in range(1,4):
            source=cases.sources(trial)
            def expected(region,budget):
                data={'recommendation':'C' if region=='EU' else 'A','options':[dict(s,source=s['url']) for s in source]}
                return all(oracle.research(data,source,{'budget':budget,'region':region,'retention_days':7}).values())
            self.assertTrue(expected('EU',100));self.assertTrue(expected('US',130))
        self.assertNotEqual(cases.files('defects',1)['review/mean.py'],cases.files('defects',2)['review/mean.py'])

    def test_screen_selects_every_condition_without_selecting_outcomes(self):
        schedule=[dict(index=n,trial=t,case=c,cell=cell,arm='both') for n,(t,c,cell) in enumerate((t,c,cell) for t in (1,2,3) for c in ('reuse','defects','author','boundaries') for cell in cases.CELLS)]
        declared=screen.selection({'schedule':schedule},'frozen-hash')
        selected=[item for item in schedule if item['index'] in declared['episode_indices']]
        self.assertEqual(len(selected),16)
        self.assertEqual({(r['case'],r['cell']) for r in selected},{(c,cell) for c in ('reuse','defects','author','boundaries') for cell in cases.CELLS})
        self.assertTrue(all(r['trial']==1 for r in selected))
        self.assertEqual(declared['planned_sessions'],52)


class EvidenceExport(unittest.TestCase):
    def test_review_packets_include_authored_procedure_and_actual_request(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);frozen=root/'frozen/evaluator';frozen.mkdir(parents=True)
            (frozen/'run.py').write_bytes(Path(run.__file__).read_bytes())
            plan={'seed':1,'repeats':1,'frozen_hashes':run.hashes(root/'frozen')}
            run.save(root/'plan.json',plan);(root/'plan.sha256').write_text(oracle.digest(root/'plan.json'))
            run.save(root/'blind-review-key.json',{'item-001':{'index':1,'case':'author','cell':next(iter(cases.CELLS)),'trial':1,'arm':'both'}})
            episode=root/'runs/001-author-test';work=episode/'workspace';draft=work/'workflows/support-report/draft/WORKFLOW.md';draft.parent.mkdir(parents=True)
            draft.write_text('The actual authored procedure.')
            (episode/'prompt-1.txt').write_text('The actual request and its authorization scope.')
            run.save(episode/'result.json',{'followups':[],'effects':{}})
            review_packets.prepare(root)
            packet=root/'blind-review/item-001'
            self.assertEqual((packet/'workflows/support-report/draft/WORKFLOW.md').read_text(),draft.read_text())
            self.assertEqual(json.loads((packet/'task.json').read_text())['requests'],['The actual request and its authorization scope.'])

    def test_supplementary_audit_preserves_failures_and_missing_usage(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'workspace';(root/'artifacts').mkdir(parents=True)
            run.save(root/'artifacts/percentage.json',{'response_percentage':71.11})
            result={'index':1,'case':'boundaries','cell':'test','arm':'both','trial':1,
                    'sessions':[{'usage':None,'exit_code':1,'stop_reason':None}],
                    'elapsed_seconds':2,'objective':{'compliant_success':False,'checks':{'direct_calculation':False},'protocol':{'records':0,'valid':0}}}
            row=audit.observe(result,root)
            self.assertFalse(row['primary_success'])
            self.assertEqual(row['sessions_with_usage'],0)
            self.assertEqual(row['nonzero_exit_sessions'],1)
            self.assertGreater(row['percentage_absolute_error_points'],0)
            self.assertTrue(row['scorer_review_flags'])
            result.update(case='author',followups=[{'type':'scripted_answer','provided':True}])
            result['objective']['checks']={'asked_needed_question':False,'bounded_review':True,'local_only':True}
            self.assertTrue(audit.observe(result,root)['needed_answer_actually_provided'])
            self.assertFalse(audit.observe(result,root)['primary_success'])
            result['cell']='pi-gpt-oss-120b-medium'
            row=audit.observe(result,root)
            self.assertIsNone(row['local_model_not_loaded_at_episode_start'])
            self.assertEqual(row['local_loaded_digests_after_sessions'],[])
            run.save(root.parent/'invocation-1.json',{'model_before':{'models':[]}})
            result['sessions'][0]['model_after']={'models':[{'model':'gpt-oss:120b','digest':'observed-weights'}]}
            row=audit.observe(result,root)
            self.assertTrue(row['local_model_not_loaded_at_episode_start'])
            self.assertEqual(row['local_loaded_digests_after_sessions'],['observed-weights'])
            result['case']='defects'
            run.save(root/'artifacts/review.json',[{'input':[1,2],'expected':1.5,'observed':1},{'input':[1,3],'expected':2,'observed':2}])
            row=audit.observe(result,root)
            self.assertEqual(row['review_items'],2)
            self.assertEqual(row['verified_counterexamples'],1)
            self.assertEqual(row['items_without_verified_counterexample'],1)

    def test_export_excludes_authentication_caches_and_symlinks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'batch';root.mkdir();frozen=root/'frozen/evaluator';frozen.mkdir(parents=True)
            (frozen/'run.py').write_bytes(Path(run.__file__).read_bytes())
            plan={'frozen_hashes':run.hashes(root/'frozen')}
            run.save(root/'plan.json',plan);(root/'plan.sha256').write_text(oracle.digest(root/'plan.json'))
            run.save(root/'summary.json',{})
            (root/'pi-agent').mkdir();(root/'pi-agent/auth.json').write_text('FAKE_SECRET')
            (root/'cache-template').mkdir();(root/'cache-template/private.txt').write_text('FAKE_CACHE')
            work=root/'runs/test/workspace';work.mkdir(parents=True)
            (work/'link').symlink_to(root/'pi-agent/auth.json')
            (work/'safe.txt').write_text('synthetic observed evidence')
            archive=Path(d)/'evidence.tar.gz';output=Path(d)/'report'
            evidence_export.export(root,output,archive)
            with tarfile.open(archive) as tar:
                names=tar.getnames()
                self.assertIn('runs/test/workspace/safe.txt',names)
                self.assertFalse(any('auth.json' in n or 'cache-template' in n or n.endswith('/link') for n in names))
            self.assertTrue(json.loads((output/'evidence-integrity.json').read_text())['all_members_verified'])


if __name__=='__main__':unittest.main()
