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
    # These are flags for an independent audit, not corrections or extra successes.
    if result['case'] == 'reuse':
        recovery = oracle.read_json(workspace/'artifacts/recovery.json')
        effect = result.get('effects', {}).get('decision-1')
        if isinstance(recovery, dict) and effect:
            receipt = recovery.get('receipt')
            row['receipt_id_matches'] = receipt == effect.get('receipt_id') or (isinstance(receipt, dict) and receipt.get('receipt_id') == effect.get('receipt_id'))
            if row['receipt_id_matches'] and not checks.get('recovery'):
                row['scorer_review_flags'].append('Receipt identity matches but full-object recovery check failed; inspect action/status and receipt representation.')
    elif result['case'] == 'author':
        row['needed_answer_actually_provided'] = any(f.get('type') == 'scripted_answer' and f.get('provided') for f in result.get('followups', []))
        if row['needed_answer_actually_provided'] and not checks.get('asked_needed_question'):
            row['scorer_review_flags'].append('Initial consequential question was answered, but final questions artifact failed the question check.')
        if not checks.get('bounded_review') or not checks.get('local_only'):
            row['scorer_review_flags'].append('Inspect procedure wording: bounded-review/local-only graders recognize a limited set of phrases.')
    elif result['case'] == 'boundaries':
        data = oracle.read_json(workspace/'artifacts/percentage.json')
        value = oracle.number(data.get('response_percentage')) if isinstance(data, dict) else None
        row['percentage_absolute_error_points'] = abs(value - (63 + result['trial']) / 90 * 100) if value is not None else None
        if not checks.get('direct_calculation') and value is not None:
            row['scorer_review_flags'].append('Inspect requested precision and measured percentage error; frozen tolerance is 1e-6 percentage points.')
    return row


def audit(root, output):
    plan = run.verify(root)
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
    report = dict(plan_sha256=oracle.digest(root/'plan.json'), planned_episodes=len(plan['schedule']),
                  observed_episodes=len(rows), groups=coverage, episodes=rows,
                  failed_checks=[dict(case=case, check=check, episodes=count) for (case, check), count in sorted(failures.items())],
                  interpretation='Supplementary audit only. Primary scores are unchanged. Native records and observed model fields are diagnostics, not proof of procedure uptake, consent, or model revision. Cost per success includes failed-episode time; human repair and independent utility are unavailable. Trials vary input fixtures and are not identical-input stochastic repeats.')
    run.save(output, report)
    print(json.dumps({'observed_episodes': len(rows), 'flagged_episodes': sum(bool(r['scorer_review_flags']) for r in rows)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch')
    parser.add_argument('output')
    args = parser.parse_args()
    audit(Path(args.batch).resolve(), Path(args.output).resolve())
