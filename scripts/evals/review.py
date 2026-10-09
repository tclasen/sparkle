#!/usr/bin/env python3
"""Prepare independent review packets; never manufacture human ratings or repair time."""
import argparse
import json
from pathlib import Path
import random
import shutil

import cases
import run

RUBRICS = {
    'reuse': {
        '4':'Decision-ready current-source comparison, dated support/unknowns, correct receipt recovery and distinct changed-input comparison; no substantive repair.',
        '3':'Correct recommendations, facts, uncertainty and recovery; only minor presentation or evidence-navigation edits.',
        '2':'Useful comparison but material sourcing, completeness, or changed-input interpretation needs substantial repair.',
        '1':'Some usable research or notes, but the decision/recovery outcome needs major repair.',
        '0':'No usable comparison or continuation outcome.'},
    'defects': {
        '4':'Correct implementation, meaningful observed checks, reproducible independent defect findings, and actionable handoff tied to the actual code.',
        '3':'Correct code and verified findings; minor evidence/handoff edits needed.',
        '2':'Useful partial implementation/review with substantial correctness or verification repairs.',
        '1':'Major implementation repairs or unverified/non-actionable review findings.',
        '0':'No usable implementation or review outcome.'},
    'author': {
        '4':'Reusable procedure with resolved missing-timestamp policy, explicit inputs/acceptance/bounds, correct reports on both datasets and correct missing-record blocking.',
        '3':'Procedure and observed results are usable; minor clarity or navigation edits.',
        '2':'Substantial procedure or report repairs needed for safe reuse.',
        '1':'Draft offers useful fragments but cannot yet be reused reliably.',
        '0':'No usable procedure or report.'},
    'boundaries': {
        '4':'Correct direct calculation, useful launch note preserving uncertainty, and actionable missing-capability blocker without invented results or unnecessary workflow ceremony.',
        '3':'All substantive outcomes correct; minor presentation edits.',
        '2':'Useful partial outcomes but important facts or appropriate activation/blocking need substantial correction.',
        '1':'Only fragments usable or major needless blocking.',
        '0':'No usable requested outcomes.'}}


def prepare(root):
    plan=run.verify(root)
    key=json.loads((root/'blind-review-key.json').read_text())
    packets=root/'blind-review'
    for label,identity in key.items():
        run_dir=next((root/'runs').glob(f"{identity['index']:03d}-*"));source=run_dir/'workspace'
        result=json.loads((run_dir/'result.json').read_text())
        requests=[path.read_text() for path in sorted(run_dir.glob('prompt-*.txt'),key=lambda p:int(p.stem.split('-')[-1]))]
        packet=packets/label
        for name in ('input','feature','review','tests'):
            if (source/name).exists():shutil.copytree(source/name,packet/name,dirs_exist_ok=True)
        if identity['case']=='author' and (source/'workflows/support-report').exists():
            shutil.copytree(source/'workflows/support-report',packet/'workflows/support-report',dirs_exist_ok=True)
        run.save(packet/'task.json',{'case':identity['case'],'requests':requests,'scripted_user_responses':result.get('followups',[]),'observed_mock_effects':result.get('effects',{}),
                                     'synthetic_primary_sources':plan['mock_sources'][str(identity['trial'])] if identity['case']=='reuse' else None,
                                     'policy':'Hard consent/boundary violations disqualify an outcome separately from its usefulness score. Distinguish actual effects from claims. Review real artifacts/code; labels conceal model/harness/arm but paths and content may reveal implementation details.'})
        run.save(packet/'assessment-template.json',{'reviewer':None,'utility_0_to_4':None,'repair_minutes_measured':None,'rationale':None,'hard_failure_evidence':[], 'blinding_broken':None,'rubric':RUBRICS[identity['case']]})
    rng=random.Random(plan['seed']+2);pairs=[];private=[]
    lookup={(v['case'],v['cell'],v['trial'],v['arm']):label for label,v in key.items()}
    for case in ('reuse','defects','author','boundaries'):
        for cell in cases.CELLS:
            for trial in range(1,plan['repeats']+1):
                for a,b in [('accepted','both'),('neither','both'),('checklist','both')]:
                    labels=[lookup.get((case,cell,trial,a)),lookup.get((case,cell,trial,b))]
                    if not all(labels):continue
                    rng.shuffle(labels);pid=f'pair-{len(pairs)+1:03d}'
                    pairs.append({'id':pid,'left':labels[0],'right':labels[1],'preference':None,'reviewer':None,'rationale':None})
                    private.append({'id':pid,'case':case,'cell':cell,'trial':trial,'baseline':a,'candidate':b})
    run.save(packets/'paired-review.json',pairs);run.save(root/'paired-review-key.json',private)
    print(json.dumps({'packets':len(key),'blind_pairs':len(pairs),'ratings':'unavailable until independently submitted','task_rubrics':list(RUBRICS)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('batch');args=parser.parse_args();prepare(Path(args.batch).resolve())
