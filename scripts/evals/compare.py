#!/usr/bin/env python3
"""Supplement primary outcomes with explicit paired contrasts and coverage."""
import argparse
import collections
import json
from pathlib import Path

import oracle
import run


def compare(results, corrected):
    indexed = {}
    for result in results:
        key = tuple(result[k] for k in ('case', 'cell', 'trial', 'arm'))
        if key in indexed:
            raise ValueError('Duplicate condition; cannot silently choose a scored attempt')
        indexed[key] = result
    groups = collections.defaultdict(list)
    for result in results:
        groups[result['cell']].append(result)
    cells = []
    for cell, rows in sorted(groups.items()):
        successes = sum(r['objective']['compliant_success'] for r in rows)
        seconds = sum(r['elapsed_seconds'] for r in rows)
        cells.append(dict(cell=cell, episodes=len(rows), primary_successes=successes,
                          supplementary_successes=sum(corrected[r['index']] for r in rows),
                          elapsed_seconds=seconds,
                          elapsed_seconds_per_primary_success=seconds/successes if successes else None))
    contrasts = []
    interactions = []
    for case, cell, trial in sorted({key[:3] for key in indexed}):
        arms = {key[3]: value for key, value in indexed.items() if key[:3] == (case, cell, trial)}
        for baseline, candidate in [('neither', 'accepted'), ('neither', 'both'), ('accepted', 'both'),
                                    ('neither', 'skill'), ('neither', 'workflow'), ('workflow', 'both'),
                                    ('skill', 'both'), ('checklist', 'both'), ('both', 'instructed'),
                                    ('accepted', 'discovery-only'), ('accepted', 'context-only'),
                                    ('accepted', 'verification-only')]:
            if baseline not in arms or candidate not in arms:
                continue
            a, b = arms[baseline], arms[candidate]
            contrasts.append(dict(case=case, cell=cell, trial=trial, baseline=baseline, candidate=candidate,
                                  baseline_index=a['index'], candidate_index=b['index'],
                                  primary_delta=int(b['objective']['compliant_success'])-int(a['objective']['compliant_success']),
                                  supplementary_delta=int(corrected[b['index']])-int(corrected[a['index']]),
                                  elapsed_seconds_delta=b['elapsed_seconds']-a['elapsed_seconds'],
                                  elapsed_time_ratio=b['elapsed_seconds']/a['elapsed_seconds'] if a['elapsed_seconds'] else None,
                                  tool_calls_delta=b['tool_calls']-a['tool_calls']))
        if all(arm in arms for arm in ('neither', 'skill', 'workflow', 'both')):
            weights = {'both': 1, 'skill': -1, 'workflow': -1, 'neither': 1}
            interactions.append(dict(case=case, cell=cell, trial=trial,
                                     primary_interaction=sum(weight*int(arms[arm]['objective']['compliant_success']) for arm, weight in weights.items()),
                                     supplementary_interaction=sum(weight*int(corrected[arms[arm]['index']]) for arm, weight in weights.items())))
    return dict(cells=cells, contrasts=contrasts, factorial_interactions=interactions,
                interpretation='Descriptive paired binary outcomes and resource observations, including failures. Supplementary corrections are exploratory. A binary interaction from one trial is not a causal mechanism, reliability estimate, independent utility score, or adoption decision.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch'); parser.add_argument('corrections'); parser.add_argument('output')
    args = parser.parse_args()
    root = Path(args.batch).resolve()
    run.verify(root)
    corrections = json.loads(Path(args.corrections).read_text())
    if corrections['plan_sha256'] != oracle.digest(root/'plan.json'):
        raise ValueError('Corrections belong to another plan')
    results = [json.loads(path.read_text()) for path in (root/'runs').glob('*/result.json')]
    corrected = {row['index']: row['supplementary_success'] for row in corrections['episodes']}
    if set(corrected) != {row['index'] for row in results}:
        raise ValueError('Corrections do not cover exactly the observed episodes')
    report = compare(results, corrected)
    report.update(plan_sha256=oracle.digest(root/'plan.json'), correction_version=corrections['version'],
                  correction_code_sha256=corrections['code_sha256'])
    run.save(Path(args.output), report)


if __name__ == '__main__':
    main()
