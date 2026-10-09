#!/usr/bin/env python3
"""Run a declared one-trial subset without changing a previously frozen full plan."""
import argparse
import json
from pathlib import Path

import cases
import oracle
import run


def selection(plan, plan_hash):
    selected = [item for item in plan['schedule'] if item['trial'] == 1]
    return {'original_plan_sha256': plan_hash, 'selected_trial': 1,
            'episode_indices': [item['index'] for item in selected],
            'planned_episodes': len(selected),
            'planned_sessions': sum(len(cases.prompts(item['case'], 1)) for item in selected),
            'selection_rule': 'Every condition in every case and model/harness cell, trial 1 only; no selection by outcome.',
            'reason': 'Honor the requested initial screening with one repeat. Additional diagnostic conditions expand the original 64-episode design to 104 episodes.',
            'interpretation': 'Provisional screening; no repeated-trial reliability, statistical proof, or established catalog benefit.'}


def execute(root, operation):
    plan = run.verify(root)
    declared = selection(plan, oracle.digest(root/'plan.json'))
    path = root/'screen-selection.json'
    if path.exists():
        if json.loads(path.read_text()) != declared or oracle.digest(path) != (root/'screen-selection.sha256').read_text().strip():
            raise ValueError('Screen selection changed')
    else:
        if operation != 'prepare':
            raise ValueError('Declare the selection with prepare before running it')
        run.save(path, declared)
        (root/'screen-selection.sha256').write_text(oracle.digest(path)+'\n')
    if operation == 'prepare':
        print(json.dumps(declared));return
    if operation == 'run':
        for item in plan['schedule']:
            if item['index'] not in declared['episode_indices']:continue
            print('START', json.dumps(item), flush=True)
            result = run.execute(root, plan, item)
            print('DONE', json.dumps({k: result[k] for k in ('index', 'elapsed_seconds', 'failure_attribution', 'objective')}), flush=True)
    run.summarize(root)
    report = json.loads((root/'summary.json').read_text())
    observed = [json.loads(p.read_text()) for p in (root/'runs').glob('*/result.json')]
    if any(r['index'] not in declared['episode_indices'] for r in observed):
        raise ValueError('Non-screen episodes present; report them separately rather than mixing denominators')
    report.update(planned=declared['planned_episodes'], original_plan_episodes=len(plan['schedule']),
                  completed_matrix=sorted(r['index'] for r in observed)==sorted(declared['episode_indices']),
                  screen_selection_sha256=oracle.digest(path), uncertainty=declared['interpretation'])
    for group in report['groups']:
        group.pop('all_repeats_success', None)
        group['screen_trial_success'] = group['attempted'] == 1 and group['successes'] == 1
    run.save(root/'screen-summary.json', report)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare','run','summarize'])
    parser.add_argument('batch')
    args=parser.parse_args()
    execute(Path(args.batch).resolve(), args.operation)
