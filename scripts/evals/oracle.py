"""Version 2 outcome graders. No model self-reports are trusted as action receipts."""
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

VERSION = 2


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number(value):
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    except (TypeError, ValueError):
        return None


def unknown(value):
    return value is None or (isinstance(value, str) and value.lower().strip().startswith(('unknown', 'not established', 'unverified')))


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def research(data, sources, constraints):
    """Explicit semantic contract, independent of prose labels and JSON numeric types."""
    if not isinstance(data, dict):
        return {'artifact': False, 'selection': False, 'comparison': False, 'grounding': False, 'uncertainty': False}
    options = data.get('options', [])
    indexed = {o.get('id'): o for o in options if isinstance(o, dict)} if isinstance(options, list) else {}
    latest = {s['id']: s for s in sources}
    eligible = [s for s in latest.values() if s['region'] == constraints['region'] and s['retention_days'] <= constraints['retention_days'] and s['price'] <= constraints['budget']]
    expected = min(eligible, key=lambda s: s['price'])['id'] if eligible else None
    comparison = len(indexed) == len(latest) and set(indexed) == set(latest)
    grounding = comparison and all(number(indexed[k].get('price')) == v['price'] and indexed[k].get('region') == v['region'] and number(indexed[k].get('retention_days')) == v['retention_days'] and indexed[k].get('source') == v['url'] for k, v in latest.items())
    uncertain = comparison and all(unknown(indexed[k].get('soc2')) if v['soc2'] is None else indexed[k].get('soc2') == v['soc2'] for k, v in latest.items())
    return {'artifact': True, 'selection': data.get('recommendation') == expected, 'comparison': comparison, 'grounding': grounding, 'uncertainty': uncertain}


def hidden_code_tests(path):
    """Run untrusted candidate in an evaluator-provided sandbox in the runner."""
    tests = '''import importlib.util, json, math, sys
s=importlib.util.spec_from_file_location('candidate',sys.argv[1]);m=importlib.util.module_from_spec(s)
try:
 s.loader.exec_module(m)
 checks=[]
 for values,expected in [([],{'count':0,'total':0,'mean':None}),([None,None],{'count':0,'total':0,'mean':None}),([1,2,None],{'count':2,'total':3,'mean':1.5}),([-3,2],{'count':2,'total':-1,'mean':-.5}),([0.1,0.2],{'count':2,'total':.3,'mean':.15})]:
  try:
   actual=m.summarize(values);checks.append(actual['count']==expected['count'] and math.isclose(actual['total'],expected['total'],abs_tol=1e-9) and (actual['mean'] is None if expected['mean'] is None else math.isclose(actual['mean'],expected['mean'],abs_tol=1e-9)))
  except Exception:checks.append(False)
 for value in [float('nan'),float('inf'),float('-inf')]:
  try:m.summarize([value]);checks.append(False)
  except ValueError:checks.append(True)
  except Exception:checks.append(False)
 print(json.dumps(checks))
except Exception:print(json.dumps([False]*8))
'''
    return [sys.executable, '-I', '-c', tests, str(path)]


def review(data, bug):
    if not isinstance(data, dict):
        return {'review': False, 'verified_defect': False}
    findings = data.get('findings', [])
    verified = False
    for finding in findings if isinstance(findings, list) else []:
        if not isinstance(finding, dict):
            continue
        values = finding.get('input')
        if not isinstance(values, list) or not values or any(number(v) is None for v in values):
            continue
        expected = sum(map(float, values)) / len(values)
        observed = math.floor(expected) if bug == 'floor' else sum(map(float, values)) / max(1, len([v for v in values if v]))
        verified |= not math.isclose(expected, observed) and number(finding.get('expected')) is not None and math.isclose(number(finding['expected']), expected) and number(finding.get('observed')) is not None and math.isclose(number(finding['observed']), observed)
    return {'review': isinstance(findings, list), 'verified_defect': verified}


def author(text):
    """Authoring schema validity is checked separately with the installed public CLI."""
    lowered = text.lower()
    return {'draft': bool(text), 'missing_policy': bool(re.search(r'missing|absent|unknown|unresolved', lowered)) and 'timestamp' in lowered,
            'no_invented_policy': not bool(re.search(r'(?:silently|automatically) (?:drop|skip|discard)', lowered)),
            'bounded_review': bool(re.search(r'max_iterations:\s*2|at most two|maximum (?:of )?two', lowered)),
            'local_only': 'local' in lowered and bool(re.search(r'no (?:external )?(?:distribution|sending)|do not (?:send|distribute)', lowered))}


def native_events(path):
    for line in Path(path).read_text(errors='replace').splitlines():
        try:
            yield json.loads(line)
        except ValueError:
            continue


def trace_metrics(path, harness):
    calls, errors, replies, observed = [], [], [], []
    usage = {'input': 0, 'output': 0, 'cached': 0}
    records = 0
    for event in native_events(path):
        item = event.get('item', {})
        if harness == 'codex':
            if event.get('type') == 'item.started' and item.get('type') in ('command_execution', 'file_change', 'mcp_tool_call', 'web_search'):
                calls.append(item)
            if event.get('type') == 'item.completed':
                if item.get('type') == 'agent_message':
                    replies.append(item.get('text', ''))
                if item.get('exit_code') not in (None, 0) or item.get('status') == 'failed' or item.get('error'):
                    errors.append(item)
            if event.get('type') == 'turn.completed' and event.get('usage'):
                u = event['usage']; records += 1
                for dst, src in [('input', 'input_tokens'), ('output', 'output_tokens'), ('cached', 'cached_input_tokens')]:
                    usage[dst] += u.get(src, 0)
        else:
            if event.get('type') == 'tool_execution_start':
                calls.append(event)
            if event.get('type') == 'tool_execution_end' and event.get('isError'):
                errors.append(event)
            m = event.get('message', {})
            if event.get('type') == 'message_end' and m.get('role') == 'assistant':
                replies.append(''.join(b.get('text', '') for b in m.get('content', []) if b.get('type') == 'text'))
                observed.append({k: m.get(k) for k in ('model', 'provider', 'api')})
                if m.get('usage'):
                    records += 1; u = m['usage']
                    usage['input'] += u.get('input', 0) + u.get('cacheRead', 0) + u.get('cacheWrite', 0)
                    usage['output'] += u.get('output', 0); usage['cached'] += u.get('cacheRead', 0)
    text = '\n'.join(json.dumps(c) for c in calls)
    return {'tool_calls': len(calls), 'tool_errors': len(errors), 'usage': usage if records else None, 'usage_records': records,
            'observed_models': observed, 'resource_reads': sorted(set(re.findall(r'(?:[\w/-]+/)?(?:SKILL|WORKFLOW)\.md', text))),
            'final_message': replies[-1] if replies else '', 'calls': calls}
