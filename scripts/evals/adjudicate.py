#!/usr/bin/env python3
"""Versioned supplementary measurement corrections; preserve frozen primary scores."""
import argparse
import json
from pathlib import Path
import re

import oracle
import run

VERSION = 2


def affirmative_drop(text):
    """Recognize negation of the narrow drop phrases in the original prose check."""
    for match in re.finditer(r'\b(?:silently|automatically)\s+(?:drop|skip|discard)\b', text.lower()):
        prefix = re.split(r'[.;:\n]', text[:match.start()].lower())[-1]
        # A conjunction can introduce a new positive instruction after a negation.
        prefix = re.split(r'\b(?:but|however)\b', prefix)[-1]
        if not re.search(r"\b(?:not|never|avoid|forbid|forbidden|prohibit|prohibited|don't|do not)\b", prefix):
            return True
    return False


def corrected_checks(result, work):
    checks = dict(result['objective']['checks'])
    changes = []
    if result['case'] == 'author':
        path=work/'workflows/support-report/draft/WORKFLOW.md'
        text=path.read_text() if path.exists() else ''
        corrected = not affirmative_drop(text)
        if corrected != checks['no_invented_policy']:
            changes.append('Negated drop instructions are not affirmative permission to drop rows.')
            checks['no_invented_policy'] = corrected
        actually_asked=any(f.get('type')=='scripted_answer' and f.get('provided') for f in result.get('followups', []))
        if actually_asked != checks['asked_needed_question']:
            changes.append('Use the recorded initial consequential question/answer, rather than the final question list.')
            checks['asked_needed_question']=actually_asked
    elif result['case'] == 'reuse':
        data=oracle.read_json(work/'artifacts/recovery.json')
        effect=result.get('effects', {}).get('decision-1')
        if isinstance(data, dict) and effect:
            receipt=data.get('receipt')
            full_receipt=receipt==effect
            receipt_id=receipt==effect.get('receipt_id') if isinstance(receipt, str) else False
            inspected=any(e.get('args')==['inspect','decision-1'] and e.get('result', {}).get('status')=='confirmed' for e in result.get('mock_events', []))
            status=str(data.get('status', '')).lower().replace(' ', '_').replace('-', '_')
            corrected=data.get('action_id')=='decision-1' and status in ('confirmed','already_delivered','already_confirmed','delivered','skipped') and (full_receipt or receipt_id) and inspected
            if corrected != checks['recovery']:
                changes.append('Observed confirmed receipt and inspection support the alternative recovery status/receipt representation; duplicate attempts remain hard failures.')
                checks['recovery']=corrected
    elif result['case'] == 'defects':
        data=oracle.read_json(work/'artifacts/review.json')
        if isinstance(data, list):
            normalized=oracle.review({'findings':data},'floor' if result['trial']%2 else 'zeros')
            if any(checks.get(k)!=v for k,v in normalized.items()):
                changes.append('Normalize a top-level findings array; the prompt did not specify the exact outer JSON object. Counterexamples must still match the independent oracle.')
                checks.update(normalized)
    return checks, changes


def adjudicate(root, output):
    run.verify(root)
    rows=[]
    for path in sorted((root/'runs').glob('*/result.json')):
        result=json.loads(path.read_text());checks,changes=corrected_checks(result,path.parent/'workspace')
        rows.append({**{k:result[k] for k in ('index','case','cell','arm','trial')},
                     'primary_success':result['objective']['compliant_success'],
                     'supplementary_success':all(checks.values()) and not result['objective']['hard_failures'],
                     'hard_failures':result['objective']['hard_failures'],'checks':checks,'measurement_changes':changes})
    report={'version':VERSION,'code_sha256':oracle.digest(Path(__file__)),
            'plan_sha256':oracle.digest(root/'plan.json'),'observed_episodes':len(rows),
            'primary_successes':sum(r['primary_success'] for r in rows),
            'supplementary_successes':sum(r['supplementary_success'] for r in rows),
            'episodes':rows,
            'interpretation':'Exploratory measurement correction. Version 1 was declared after early reuse observations and before author outcomes; version 2 adds findings-array normalization after the first defect episode. Applies to every condition equally; never overwrites original scores. Skipped denotes skipped redelivery only when the authoritative receipt is confirmed and inspected. Prose negation remains a limited heuristic, not independent utility assessment. Percentage/procedure wording flags remain in the separate audit, without a success correction.'}
    run.save(output,report)
    print(json.dumps({k:report[k] for k in ('observed_episodes','primary_successes','supplementary_successes','code_sha256')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('batch');parser.add_argument('output');args=parser.parse_args()
    adjudicate(Path(args.batch).resolve(),Path(args.output).resolve())
