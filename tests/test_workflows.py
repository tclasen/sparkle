#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0.2,<7"]
# ///
"""Acceptance checks for the focused public CLI, without editing run state."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT/'shared/scripts/workflow.py'

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = self.root/'environment.json'
        self.env.write_text(json.dumps({'executor':'test','capabilities':[], 'skills':{}}))
        self.call('project','sample','--root',self.root,'--brief','Acceptance fixture')

    def call(self, *args, ok=True):
        p = subprocess.run([sys.executable,str(HELPER),*map(str,args)],capture_output=True,text=True)
        if ok:
            self.assertEqual(p.returncode,0,p.stderr)
            return json.loads(p.stdout)
        self.assertNotEqual(p.returncode,0,p.stdout)
        return json.loads(p.stderr)['diagnostics'][0]

    def document(self, steps, wid='fixture', inputs=None):
        data={'schema':1,'id':wid,'inputs':inputs or {},'steps':steps}
        def sections(nodes):
            return ''.join(f'## {s["id"]} — Task\n\nTask: Perform work.\nInputs: Frozen inputs.\nOutputs: Artifact.\nAcceptance: Evidence supports result.\nFallback: Work locally.\n\n'+sections(s.get('steps',[])) for s in nodes)
        p=self.root/(wid+'.md')
        p.write_text('---\n'+yaml.safe_dump(data,sort_keys=False)+'---\n# Fixture\n\n## Execution interaction policy\nBlock unresolved gaps.\n\n'+sections(steps)+'## Completion criteria\nAll checks pass.\n')
        return p

    def launch(self, steps, wid='fixture'):
        doc=self.document(steps,wid)
        self.call('publish',doc,'--root',self.root,'--version','1.0.0')
        run=Path(self.call('start','sample',wid,'--root',self.root,'--environment',self.env,'--owner','one')['run'])
        (run/'artifacts/proof.txt').write_text('Observed test evidence')
        return run

    def result(self, **kw):
        return {'assessment':'Checks passed','evidence':['artifacts/proof.txt'],**kw}

    def mutate(self, run, command, *args, result=None, ok=True, owner='one', revision=None):
        rev=self.call('status',run,'--json')['revision'] if revision is None else revision
        extra=[]
        if result is not None:
            p=self.root/'result.json';p.write_text(json.dumps(result));extra=['--result',p]
        return self.call(command,run,*args,*extra,'--owner',owner,'--revision',rev,ok=ok)

    def complete(self,run,path,**kw):
        self.mutate(run,'step',path,'begin')
        self.mutate(run,'step',path,'complete',result=self.result(**kw))

    def coordinated(self, ticket='T-1', claim='claim-a', dependencies=None):
        binding = dict(schema=1, provider='fixture', ticket=ticket, peer='session-a',
                       claim_id=claim, work_area=str(self.root), resources=[], dependencies=dependencies or [])
        path = self.root/'binding.json'
        path.write_text(json.dumps(binding))
        if not (self.root/'workflows/peer/versions/1.0.0').exists():
            doc = self.document([{'id':'work','type':'task'}], 'peer')
            self.call('publish', doc, '--root', self.root, '--version', '1.0.0')
        run = Path(self.call('start', 'sample', 'peer', '--root', self.root,
                            '--environment', self.env, '--owner', 'one', '--coordination', path)['run'])
        (run/'artifacts/proof.txt').write_text('Simulated external observation, not provider evidence')
        return run

    def test_coordination_binding_isolation(self):
        a = self.coordinated()
        b = self.coordinated('T-2', 'claim-b')
        for run, ticket in ((a, 'T-1'), (b, 'T-2')):
            state = self.call('status', run, '--json')
            self.assertEqual(state['coordination']['binding']['ticket'], ticket)
            self.assertEqual(state['coordination']['events'], [])
        path = self.root/'binding.json'
        binding = json.loads(path.read_text())
        binding['dependencies'] = ['T-2']
        path.write_text(json.dumps(binding))
        self.call('start', 'sample', 'peer', '--root', self.root, '--environment', self.env,
                  '--owner', 'one', '--coordination', path, ok=False)
        self.assertEqual(self.call('status', b, '--json')['coordination']['binding']['dependencies'], [])

    def event(self, run, kind, **kwargs):
        coord = self.call('coordination', run, 'show')['coordination']
        return dict(id=f"event-{len(coord['events'])}", kind=kind,
                    claim_id=coord['binding']['claim_id'], observed_at='2026-10-08T12:00:00Z',
                    explanation='Simulated observation', evidence=['artifacts/proof.txt'], **kwargs)

    def record(self, run, kind, ok=True, **kwargs):
        return self.mutate(run, 'coordination', 'record', result=self.event(run, kind, **kwargs), ok=ok)

    def test_coordination_records(self):
        run = self.coordinated()
        event = self.event(run, 'claim_intent', message_id='claim-message')
        self.mutate(run, 'coordination', 'record', result=event, owner='wrong', ok=False)
        self.mutate(run, 'coordination', 'record', result=event, revision=42, ok=False)
        self.mutate(run, 'coordination', 'record', result=event)
        self.mutate(run, 'coordination', 'record', result=event, ok=False)
        for override in ({'claim_id':'other'}, {'evidence':['missing']}, {'binding':{}},
                         {'observed_at':'yesterday'}, {'observed_at':'2026-10-08T12:00:00'}):
            bad = self.event(run, 'progress') | override
            self.mutate(run, 'coordination', 'record', result=bad, ok=False)
        self.record(run, 'dependency_assessment', ticket='undeclared', accepted=True, ok=False)
        self.record(run, 'resolution', resolves=['missing'], mode='user', withdrawn_claims=[], ok=False)
        self.record(run, 'progress')
        coord = self.call('coordination', run, 'show')['coordination']
        self.assertEqual(coord['events'][0], event)
        self.assertEqual(len(coord['events']), 2)
        self.mutate(run, 'cancel', '--reason', 'fixture cancellation')
        self.record(run, 'progress', ok=False)
        self.call('validate-run', run)

    def observe(self, run, competitors=None, accessible=True):
        claim = self.call('coordination', run, 'show')['coordination']['binding']['claim_id']
        return self.record(run, 'claim_observation', accessible=accessible, claim_seen=accessible,
                           active_claims=([claim] + (competitors or [])) if accessible else [])

    def test_peer_races_dependencies_and_recovery(self):
        # Simulated independent machines: each initially misses the other claim.
        a = self.coordinated(dependencies=['T-parent'])
        b = self.coordinated('T-1', 'claim-b')
        self.assertIn('claim-unobserved', self.call('ready', a)['coordination']['blockers'])
        self.mutate(a, 'step', '/steps/work', 'begin', ok=False)
        self.observe(a)
        self.mutate(a, 'step', '/steps/work', 'begin', ok=False)
        self.record(a, 'dependency_assessment', ticket='T-parent', accepted=False)
        self.record(a, 'dependency_assessment', ticket='T-parent', accepted=True)
        self.observe(b)
        self.mutate(a, 'step', '/steps/work', 'begin')
        self.mutate(b, 'step', '/steps/work', 'begin')  # Remaining duplicate-work risk.
        self.observe(a, ['claim-b'])
        self.observe(b, ['claim-a'])
        conflict = self.call('ready', a)['coordination']['conflicts'][0]
        self.observe(a)  # A clean reread is insufficient to resolve the collision.
        self.assertIn('unresolved-conflict', self.call('ready', a)['coordination']['blockers'])
        self.mutate(a, 'step', '/steps/work', 'fail', result={'reason':'collision'})
        self.mutate(a, 'step', '/steps/work', 'retry', result={'authorization':'test retry'}, ok=False)
        self.record(a, 'resolution', resolves=[conflict], mode='withdrawals', withdrawn_claims=[], ok=False)
        self.record(a, 'resolution', resolves=[conflict], mode='withdrawals', withdrawn_claims=['claim-b'])
        self.observe(a, accessible=False)
        self.assertIn('ticket-unavailable', self.call('ready', a)['coordination']['blockers'])
        self.mutate(a, 'step', '/steps/work', 'retry', result={'authorization':'test retry'}, ok=False)
        self.observe(a)
        self.mutate(a, 'step', '/steps/work', 'retry', result={'authorization':'test retry'})
        self.record(b, 'release', message_id='release-b', status='confirmed', external_ref='fixture:withdrawal')
        self.assertIn('claim-released', self.call('ready', b)['coordination']['blockers'])
        self.mutate(b, 'cancel', '--reason', 'withdrew conflicting claim')

    def test_publication_uncertainty_handoff_and_cancellation(self):
        run = self.coordinated()
        self.record(run, 'claim_intent', message_id='claim-write')
        # Lost claim response: retain intent; a failed read does not authorize work.
        self.observe(run, accessible=False)
        self.mutate(run, 'step', '/steps/work', 'begin', ok=False)
        self.observe(run)  # Simulated inspection found the stable claim message.
        publication = dict(message_id='result-write', status='planned', final=self.result(passed=True),
                           evidence_refs=['fixture://accessible/result'])
        self.record(run, 'result_publication', **publication, ok=False)
        self.complete(run, '/steps/work')
        self.mutate(run, 'finish', result=publication['final'], ok=False)
        self.record(run, 'result_publication', **publication)
        publication['status'] = 'uncertain'
        self.record(run, 'result_publication', **publication, ok=False)
        publication['inspected'] = True
        self.record(run, 'result_publication', **(publication | {'final': self.result(passed=True, assessment='changed')}), ok=False)
        self.record(run, 'result_publication', **publication)
        self.mutate(run, 'finish', result=publication['final'], ok=False)
        publication.update(status='confirmed', external_ref='fixture://ticket/result-message')
        self.record(run, 'result_publication', **publication)
        self.record(run, 'result_publication', **publication, ok=False)
        self.mutate(run, 'finish', result=self.result(passed=True, assessment='different'), ok=False)
        self.mutate(run, 'finish', result=publication['final'])
        before = (run/'state.json').read_bytes()
        self.record(run, 'progress', ok=False)
        self.assertEqual(before, (run/'state.json').read_bytes())
        self.call('validate-run', run)
        other = self.coordinated('T-2', 'claim-b')
        self.observe(other)
        self.record(other, 'handoff', message_id='handoff', status='uncertain', successor='T-3')
        self.mutate(other, 'step', '/steps/work', 'begin', ok=False)
        self.record(other, 'handoff', message_id='handoff', status='confirmed', successor='T-3',
                    external_ref='fixture://handoff', ok=False)
        self.record(other, 'handoff', message_id='handoff', status='confirmed', successor='T-3',
                    external_ref='fixture://handoff', inspected=True)
        self.mutate(other, 'step', '/steps/work', 'begin', ok=False)
        self.record(other, 'release', message_id='release', status='uncertain')
        self.mutate(other, 'cancel', '--reason', 'cancel despite failed release notification')
        self.assertEqual(self.call('coordination', other, 'show')['coordination']['events'][-1]['status'], 'uncertain')

    def test_linear_and_guards(self):
        run=self.launch([{'id':'draft','type':'task'},{'id':'check','type':'task','depends_on':['draft']}])
        self.assertEqual(self.call('ready',run)['steps'][1]['category'],'waiting')
        before=(run/'state.json').read_bytes()
        self.assertEqual(self.mutate(run,'step','/steps/draft','begin',revision=9,ok=False)['code'],'RUN_REVISION')
        self.assertEqual(self.mutate(run,'step','/steps/draft','begin',owner='other',ok=False)['code'],'RUN_OWNER')
        self.assertEqual(before,(run/'state.json').read_bytes())
        self.complete(run,'/steps/draft')
        context=self.call('context',run,'/steps/check')
        self.assertEqual(context['predecessors']['draft']['status'],'completed')
        self.complete(run,'/steps/check')
        self.mutate(run,'finish',result=self.result(passed=True))
        self.mutate(run,'cancel','--reason','late',ok=False)
        self.call('validate-run',run)

    def test_branch_join_approval(self):
        run=self.launch([{'id':'choose','type':'decision','branches':['a','b']},
            {'id':'left','type':'task','depends_on':['choose'],'when':[{'decision':'choose','branch':'a'}]},
            {'id':'right','type':'task','depends_on':['choose'],'when':[{'decision':'choose','branch':'b'}]},
            {'id':'review','type':'approval','depends_on':['left','right'],'join':'all-active'}])
        self.complete(run,'/steps/choose',choice=['a'],reason='Fixture choice')
        self.assertEqual(self.call('ready',run)['steps'][1]['category'],'skippable')
        self.mutate(run,'step','/steps/right','skip',result={'reason':'Unselected'})
        self.complete(run,'/steps/left')
        self.mutate(run,'step','/steps/review','begin')
        self.mutate(run,'step','/steps/review','complete',result=self.result(),ok=False)
        self.mutate(run,'step','/steps/review','complete',result=self.result(approval={'by':'fixture-user','scope':'test artifact','result':'approved','approved_at':'fixture-time','evidence':['artifacts/proof.txt']}))
        self.mutate(run,'finish',result=self.result(passed=True))

    def test_recovery_and_cancellation(self):
        run=self.launch([{'id':'act','type':'task'}])
        action={'description':'External fixture action','status':'planned'}
        self.mutate(run,'step','/steps/act','begin',result={'external_actions':[action]})
        self.mutate(run,'step','/steps/act','fail',result={'reason':'interrupted'})
        self.mutate(run,'step','/steps/act','retry',result={'authorization':'Explicit fixture retry'},ok=False)
        self.mutate(run,'step','/steps/act','reconcile',result={'external_actions':[dict(action,status='not-performed',reconciliation='Inspected target; absent')]})
        self.mutate(run,'step','/steps/act','retry',result={'authorization':'Explicit fixture retry'})
        self.call('claim',run,'--owner','two',ok=False)
        self.call('claim',run,'--owner','two','--prior-owner','one','--prior-stopped-evidence','Fixture coordinator terminated')
        self.mutate(run,'cancel','--reason','User requested stop',owner='two')
        self.assertEqual(len(self.call('status',run,'--json')['steps']['act']['attempts']),2)

    def test_iteration_exhaustion_and_success(self):
        for passed in (False,True):
            run=self.launch([{'id':'loop','type':'iteration','max_iterations':1,'steps':[{'id':'check','type':'task'}]}],wid='passing' if passed else 'exhausted')
            self.mutate(run,'step','/steps/loop','begin')
            self.mutate(run,'round','/steps/loop','open')
            path=next(r['path'] for r in self.call('ready',run)['steps'] if '/rounds/' in r['path'])
            self.assertEqual(self.call('context',run,path)['ancestors'][0]['path'], '/steps/loop')
            self.complete(run,path)
            self.mutate(run,'round','/steps/loop','assess',result=self.result(exit_met=passed))
            if passed:
                self.mutate(run,'step','/steps/loop','complete',result=self.result())
                self.mutate(run,'finish',result=self.result(passed=True))
            else:
                self.assertEqual(self.call('status',run,'--json')['status'],'blocked')
                self.mutate(run,'round','/steps/loop','open',ok=False)
                self.mutate(run,'cancel','--reason','Bound exhausted')

    def test_nested_composition_and_snapshot(self):
        child=self.document([{'id':'check','type':'task'}],'child',{'topic':{'required':True}})
        self.call('publish',child,'--root',self.root,'--version','1.0.0')
        run=self.launch([{'id':'nested','type':'subworkflow','workflow':{'id':'child','version':'1.0.0'},'inputs':{'topic':'frozen'}}])
        self.mutate(run,'step','/steps/nested','begin')
        path=next(r['path'] for r in self.call('ready',run)['steps'] if r['path'].endswith('/check'))
        self.assertEqual(self.call('context',run,path)['inputs'],{'topic':'frozen'})
        (self.root/'workflows/child/versions/1.0.0/WORKFLOW.md').write_text('altered source')
        self.complete(run,path)
        self.mutate(run,'step','/steps/nested','complete',result=self.result(final=self.result(passed=True)))
        self.mutate(run,'finish',result=self.result(passed=True))

    def test_yaml_diagnostics_and_capabilities(self):
        doc=self.document([{'id':'check','type':'task'}])
        original=doc.read_text()
        for text in [original.replace('schema: 1','schema: 1\nschema: 1'),original.replace('schema: 1','schema: 1\nextra: true'),original.replace('## check','## missing'),original.replace('schema: 1','schema: !!python/object:bad {}'), original.replace('inputs: {}','inputs: {x: {default: 2026-01-01}}')]:
            doc.write_text(text)
            diagnostic=self.call('validate',doc,ok=False)
            self.assertTrue(all(k in diagnostic for k in ('code','severity','location','explanation','suggested_correction')))
        run=self.launch([{'id':'check','type':'task','capabilities':['absent']}],'blocked')
        self.assertEqual(self.call('ready',run)['steps'][0]['category'],'capability-blocked')
        self.mutate(run,'step','/steps/check','begin',ok=False)

    def test_examples_and_bundles(self):
        subprocess.run([sys.executable,str(ROOT/'scripts/bundle.py'),'--check'],check=True)
        for p in (ROOT/'examples').rglob('WORKFLOW.md'): self.call('validate',p)
        for name in ('define-workflow','execute-workflow'):
            self.call('validate',ROOT/'skills'/name/'assets/WORKFLOW.md')

if __name__=='__main__': unittest.main()
