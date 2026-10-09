#!/usr/bin/env python3
"""Report observation coverage and scorer-review flags without rescoring a batch."""
import argparse
import collections
import json
from pathlib import Path
import statistics

import oracle
import run


def observe(result, workspace):
    sessions = result['sessions']
    checks = result['objective']['checks']
    row = {k: result[k] for k in ('index', 'case', 'cell', 'arm', 'trial')}
    row.update(primary_success=result['objective']['compliant_success'],
               failed_checks=[k for k, v in checks.items() if not v],
               sessions=len(sessions),
               sessions_with_usage=sum(s.get('usage') is not None for s in sessions),
               sessions_with_partial_usage=sum(s.get('usage_coverage') == 'partial' for s in sessions),
               interrupted_sessions=sum(bool(s.get('stop_reason')) for s in sessions),
               nonzero_exit_sessions=sum(s.get('exit_code') not in (None, 0) for s in sessions),
               observed_models=[json.loads(value) for value in sorted({json.dumps(m, sort_keys=True) for s in sessions for m in s.get('observed_models', [])})],
               native_record_count=result['objective']['protocol']['records'],
               native_valid_record_count=result['objective']['protocol']['valid'],
               elapsed_seconds=result['elapsed_seconds'],
               scorer_review_flags=[])
    if 'gpt-oss' in result['cell']:
        before = oracle.read_json(workspace.parent/'invocation-1.json')
        state = before.get('model_before') if isinstance(before, dict) else None
        row['local_model_not_loaded_at_episode_start'] = not bool(state.get('models')) if isinstance(state, dict) and isinstance(state.get('models'), list) else None
        row['local_loaded_digests_after_sessions'] = sorted({m['digest'] for s in sessions for m in (s.get('model_after') or {}).get('models', []) if m.get('digest') and m.get('model') == 'gpt-oss:120b'})
        row['sessions_with_loaded_model_metadata'] = sum(any(m.get('model') == 'gpt-oss:120b' for m in (s.get('model_after') or {}).get('models', [])) for s in sessions)
    # These are flags for an independent audit, not corrections or extra successes.
    if result['case'] == 'reuse':
        recovery = oracle.read_json(workspace/'artifacts/recovery.json')
        effect = result.get('effects', {}).get('decision-1')
        if isinstance(recovery, dict) and effect:
            receipt = recovery.get('receipt')
            row['recovery_status'] = recovery.get('status')
            row['receipt_id_matches'] = receipt == effect.get('receipt_id') or (isinstance(receipt, dict) and receipt.get('receipt_id') == effect.get('receipt_id'))
            if row['receipt_id_matches'] and not checks.get('recovery'):
                row['scorer_review_flags'].append('Receipt identity matches but recovery failed; inspect action ID, literal confirmed status requirement, and full receipt representation.')
    elif result['case'] == 'author':
        row['needed_answer_actually_provided'] = any(f.get('type') == 'scripted_answer' and f.get('provided') for f in result.get('followups', []))
        if row['needed_answer_actually_provided'] and not checks.get('asked_needed_question'):
            row['scorer_review_flags'].append('Initial consequential question was answered, but final questions artifact failed the question check.')
        if not checks.get('bounded_review') or not checks.get('local_only'):
            row['scorer_review_flags'].append('Inspect procedure wording: bounded-review/local-only graders recognize a limited set of phrases.')
        if not checks.get('no_invented_policy'):
            row['scorer_review_flags'].append('Inspect drop-policy negation; the frozen phrase check also matches prohibitions on dropping rows.')
    elif result['case'] == 'defects':
        data=oracle.read_json(workspace/'artifacts/review.json')
        findings=data if isinstance(data,list) else data.get('findings',[]) if isinstance(data,dict) else []
        if not isinstance(findings,list):findings=[]
        bug='floor' if result['trial']%2 else 'zeros'
        row['review_items']=len(findings)
        row['verified_counterexamples']=sum(oracle.review({'findings':[finding]},bug)['verified_defect'] for finding in findings)
        row['items_without_verified_counterexample']=len(findings)-row['verified_counterexamples']
        if isinstance(data,list):
            row['scorer_review_flags'].append('Top-level findings array; inspect outer-object ambiguity and the supplementary normalization.')
    elif result['case'] == 'boundaries':
        data = oracle.read_json(workspace/'artifacts/percentage.json')
        value = oracle.number(data.get('response_percentage')) if isinstance(data, dict) else None
        row['percentage_absolute_error_points'] = abs(value - (63 + result['trial']) / 90 * 100) if value is not None else None
        if not checks.get('direct_calculation') and value is not None:
            row['scorer_review_flags'].append('Inspect requested precision and measured percentage error; frozen tolerance is 1e-6 percentage points.')
    return row


def audit(root, output):
    plan = run.verify(root)
    screen = oracle.read_json(root/'screen-selection.json')
    if screen is not None:
        if oracle.digest(root/'screen-selection.json') != (root/'screen-selection.sha256').read_text().strip() or screen['original_plan_sha256'] != oracle.digest(root/'plan.json'):
            raise ValueError('Screen selection changed')
    rows = []
    groups = collections.defaultdict(list)
    failures = collections.Counter()
    for path in sorted((root/'runs').glob('*/result.json')):
        result = json.loads(path.read_text())
        row = observe(result, path.parent/'workspace')
        rows.append(row)
        groups[(row['case'], row['cell'], row['arm'])].append(row)
        failures.update((row['case'], name) for name in row['failed_checks'])
    coverage = []
    for (case, cell, arm), items in sorted(groups.items()):
        success = [r for r in items if r['primary_success']]
        seconds = sum(r['elapsed_seconds'] for r in items)
        coverage.append(dict(case=case, cell=cell, arm=arm, episodes=len(items),
                             successful_episodes=len(success),
                             sessions=sum(r['sessions'] for r in items),
                             sessions_with_usage=sum(r['sessions_with_usage'] for r in items),
                             sessions_with_partial_usage=sum(r['sessions_with_partial_usage'] for r in items),
                             episodes_with_native_records=sum(bool(r['native_record_count']) for r in items),
                             native_records=sum(r['native_record_count'] for r in items),
                             valid_native_records=sum(r['native_valid_record_count'] for r in items),
                             median_success_seconds=statistics.median(r['elapsed_seconds'] for r in success) if success else None,
                             elapsed_seconds_per_success=seconds / len(success) if success else None,
                             flagged_episodes=sum(bool(r['scorer_review_flags']) for r in items)))
        if 'gpt-oss' in cell:
            coverage[-1].update(episodes_starting_without_loaded_model=sum(r.get('local_model_not_loaded_at_episode_start') is True for r in items),
                                episodes_with_start_model_metadata=sum(r.get('local_model_not_loaded_at_episode_start') is not None for r in items),
                                loaded_digests=sorted({d for r in items for d in r.get('local_loaded_digests_after_sessions', [])}))
        if case=='defects':
            coverage[-1].update(review_items=sum(r['review_items'] for r in items),
                                verified_counterexamples=sum(r['verified_counterexamples'] for r in items),
                                items_without_verified_counterexample=sum(r['items_without_verified_counterexample'] for r in items))
    report = dict(plan_sha256=oracle.digest(root/'plan.json'), planned_episodes=screen['planned_episodes'] if screen else len(plan['schedule']),
                  original_plan_episodes=len(plan['schedule']),
                  observed_episodes=len(rows), groups=coverage, episodes=rows,
                  failed_checks=[dict(case=case, check=check, episodes=count) for (case, check), count in sorted(failures.items())],
                  interpretation='Supplementary audit only. Primary scores are unchanged. Native records and observed model fields are diagnostics, not proof of procedure uptake, consent, or model revision. Cost per success includes failed-episode time; human repair and independent utility are unavailable. Full-plan trials vary input fixtures and are not identical-input stochastic repeats; a selected one-trial screen has no repeated-trial reliability estimate.')
    run.save(output, report)
    print(json.dumps({'observed_episodes': len(rows), 'flagged_episodes': sum(bool(r['scorer_review_flags']) for r in rows)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch')
    parser.add_argument('output')
    args = parser.parse_args()
    audit(Path(args.batch).resolve(), Path(args.output).resolve())
