#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0.2,<7"]
# ///
"""Structural checks and durable records; never executes or interprets workflow prose."""
import argparse
import contextlib
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid
import math
import yaml
from datetime import datetime, timezone

ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
STATUSES = {"pending", "running", "blocked", "failed", "completed", "skipped", "cancelled"}
TERMINAL = {"completed", "skipped"}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def ident(value):
    need(isinstance(value, str) and ID.fullmatch(value), f"invalid identifier: {value!r}")
    return value


def version(value):
    need(isinstance(value, str) and VERSION.fullmatch(value), f"invalid version: {value!r}")
    return tuple(map(int, value.split('.')))


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class MetadataLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        need(isinstance(key, str), 'metadata keys must be strings')
        need(key not in result, f'duplicate metadata key: {key}')
        result[key] = loader.construct_object(value_node)
    return result


MetadataLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def fields(value, allowed, location):
    need(isinstance(value, dict), f'{location}: mapping required')
    need(not set(value) - set(allowed.split()), f'{location}: unknown fields: {sorted(set(value) - set(allowed.split()))}')


def metadata(path):
    text = Path(path).read_text()
    match = re.match(r'\A---\s*\n(.*?)^---\s*$', text, re.M | re.S)
    need(match, 'YAML front matter required')
    data = yaml.load(match[1], Loader=MetadataLoader)
    def compatible(value, active=()):
        need(id(value) not in active, 'recursive YAML values are not JSON-compatible')
        if isinstance(value, dict):
            need(all(isinstance(k, str) for k in value), 'metadata keys must be strings')
            for v in value.values(): compatible(v, active + (id(value),))
        elif isinstance(value, list):
            for v in value: compatible(v, active + (id(value),))
        else:
            need(value is None or type(value) in (str, int, bool) or type(value) is float and math.isfinite(value), 'metadata values must be JSON-compatible')
    compatible(data)
    need(isinstance(data, dict), 'front matter must be a mapping')
    return data, text[match.end():]


def markdown_headings(prose):
    """Scan level 2–6 headings outside Markdown fenced code blocks."""
    fence = None
    offset = 0
    for line in prose.splitlines(keepends=True):
        text = line.rstrip('\r\n')
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', text)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker and (marker[1][0] == '~' or '`' not in marker[2]):
            fence = marker[1]
        else:
            heading = re.match(r'^(#{2,6}) (.*)$', text)
            if heading:
                yield (offset, offset + len(text), len(heading[1]), heading[2])
        offset += len(line)


class WorkflowProse:
    def __init__(self, prose, steps):
        self.prose = prose
        self.headings = list(markdown_headings(prose))
        self.ids = set()

        def collect(nodes):
            if isinstance(nodes, list):
                for node in nodes:
                    if isinstance(node, dict):
                        if isinstance(node.get('id'), str):
                            self.ids.add(node['id'])
                        collect(node.get('steps'))
        collect(steps)

    def is_step(self, heading):
        words = heading[3].split()
        return bool(words) and words[0] in self.ids

    def section(self, heading):
        end = next((h[0] for h in self.headings if h[0] > heading[0]
                    and (h[2] <= heading[2] or self.is_step(h))), len(self.prose))
        return self.prose[heading[1]:end]

    def step(self, sid):
        matches = [h for h in self.headings if h[3].split()[:1] == [sid]]
        need(len(matches) == 1, f'exactly one prose heading required for {sid}')
        return self.section(matches[0])

    def preamble(self):
        end = next((h[0] for h in self.headings if self.is_step(h)), len(self.prose))
        return self.prose[:end]

    def completion(self):
        heading = next((h for h in self.headings if h[2] == 2 and h[3].rstrip() == 'Completion criteria'), None)
        need(heading is not None, 'Completion criteria heading required')
        return self.section(heading)


def definition(path):
    data, prose = metadata(path)
    fields(data, 'schema id inputs steps', 'workflow')
    need(isinstance(data, dict), 'workflow metadata must be an object')
    need(type(data.get('schema')) is int and data.get('schema') == 1, 'workflow schema must be 1')
    ident(data.get('id'))
    need(isinstance(data.get('inputs', {}), dict), 'inputs must be an object')
    for name, spec in data.get('inputs', {}).items():
        ident(name)
        fields(spec, 'required default', f'input {name}')
        need(isinstance(spec, dict) and isinstance(spec.get('required', False), bool), f'invalid input {name}')
    steps = data.get('steps')
    sections = WorkflowProse(prose, steps)
    sections.completion()
    seen = set()

    def graph(nodes):
        need(isinstance(nodes, list) and nodes, 'nonempty steps list required')
        need(all(isinstance(n, dict) for n in nodes), 'step metadata must be objects')
        ids = [ident(n.get('id')) for n in nodes]
        need(len(ids) == len(set(ids)), 'duplicate step ID in scope')
        lookup = dict(zip(ids, nodes))
        for step in nodes:
            sid = step['id']
            need(sid not in seen, f'duplicate step ID: {sid}')
            seen.add(sid)
            section = sections.step(sid)
            kind = step.get('type')
            extra = {'decision': 'branches selection', 'subworkflow': 'workflow inputs', 'iteration': 'max_iterations steps'}.get(kind, '')
            fields(step, 'id type depends_on when join selected_dependencies skills capabilities ' + extra, sid)
            need(kind in {'task', 'decision', 'approval', 'subworkflow', 'iteration'}, f'invalid type for {sid}')
            deps = step.get('depends_on', [])
            need(isinstance(deps, list) and len(deps) == len(set(deps)), f'invalid dependencies: {sid}')
            need(all(d in lookup and d != sid for d in deps), f'missing or self dependency: {sid}')
            gates = step.get('when', [])
            need(isinstance(gates, list), f'invalid branch guards: {sid}')
            for gate in gates:
                need(isinstance(gate, dict), f'invalid guard: {sid}')
                fields(gate, 'decision branch', sid)
                dec = lookup.get(gate.get('decision'), {})
                need(dec.get('type') == 'decision' and gate.get('branch') in dec.get('branches', []), f'missing branch: {sid}')
                need(gate['decision'] in deps, f'branch decision must be a dependency: {sid}')
            need('selected_dependencies' not in step or step.get('join') == 'selected', f'selected_dependencies requires selected join: {sid}')
            if 'join' in step:
                need(step['join'] in {'all-active', 'selected'}, f'invalid join: {sid}')
                need(not gates, f'joins cannot have branch guards: {sid}')
                if step['join'] == 'selected':
                    selected = step.get('selected_dependencies')
                    need(isinstance(selected, list) and selected and len(set(selected)) == len(selected) and set(selected) <= set(deps), f'invalid selected dependencies: {sid}')
            need(isinstance(step.get('skills', []), list), f'invalid skills list: {sid}')
            for label in ('Task', 'Inputs', 'Outputs', 'Acceptance'):
                need(re.search(r'(?m)^'+label+r':', section), f'{sid}: missing {label} prose')
            for skill in step.get('skills', []):
                fields(skill, 'name required', sid)
                need(isinstance(skill, dict) and isinstance(skill.get('name'), str) and skill['name'], f'invalid skill: {sid}')
                need(isinstance(skill.get('required'), bool), f'skill required flag missing: {sid}')
                if not skill['required']:
                    need(re.search(r'\bFallback\b', section), f'optional skill needs Fallback prose: {sid}')
            need(isinstance(step.get('capabilities', []), list) and all(isinstance(c, str) and c for c in step.get('capabilities', [])), f'invalid capabilities: {sid}')
            if kind == 'decision':
                branches = step.get('branches')
                need(isinstance(branches, list) and branches and len(set(branches)) == len(branches), f'invalid branches: {sid}')
                for b in branches:
                    ident(b)
                need(step.get('selection', 'one') in {'one', 'many'}, f'invalid selection: {sid}')
            if kind == 'subworkflow':
                ref = step.get('workflow', {})
                fields(ref, 'id version', sid)
                ident(ref.get('id'))
                version(ref.get('version'))
                need(isinstance(step.get('inputs', {}), dict), f'invalid subworkflow inputs: {sid}')
            if kind == 'iteration':
                bound = step.get('max_iterations')
                need(type(bound) is int and bound > 0, f'invalid iteration bound: {sid}')
                graph(step.get('steps'))
        visited, active = set(), set()
        def visit(sid):
            need(sid not in active, f'dependency cycle at {sid}')
            if sid in visited:
                return
            active.add(sid)
            for dep in lookup[sid].get('depends_on', []):
                visit(dep)
            active.remove(sid)
            visited.add(sid)
        for sid in ids:
            visit(sid)
    graph(steps)
    return data


def walk(steps):
    for step in steps:
        yield step
        if step['type'] == 'iteration':
            yield from walk(step['steps'])


def release_dir(root, wid, ver):
    ident(wid)
    version(ver)
    return Path(root) / 'workflows' / wid / 'versions' / ver


def compositions(root, data, active):
    pins = {}
    for step in walk(data['steps']):
        if step['type'] != 'subworkflow':
            continue
        ref = step['workflow']
        pins.update(closure(root, ref['id'], ref['version'], active))
        child = definition(release_dir(root, ref['id'], ref['version']) / 'WORKFLOW.md')
        mapping = step.get('inputs', {})
        need(set(mapping) <= set(child.get('inputs', {})), f'unknown child inputs: {step["id"]}')
        for value in mapping.values():
            if isinstance(value, dict) and set(value) == {'input'}:
                need(value['input'] in data.get('inputs', {}), f'missing parent input reference: {step["id"]}')
                parent = data['inputs'][value['input']]
                need(parent.get('required') or 'default' in parent, f'input binding must always resolve: {step["id"]}')
        resolve_inputs(child, mapping)
    return pins


def closure(root, wid, ver, active=()):
    key = f'{wid}@{ver}'
    need(wid not in active, f'recursive composition: {wid}')
    folder = release_dir(root, wid, ver)
    data = definition(folder / 'WORKFLOW.md')
    manifest = read_json(folder / 'release.json')
    need(data['id'] == wid and manifest.get('id') == wid and manifest.get('version') == ver and manifest.get('schema') == 1, f'release identity mismatch: {key}')
    sha = digest(folder / 'WORKFLOW.md')
    need(manifest.get('sha256') == sha, f'altered release: {key}')
    pins = compositions(root, data, active + (wid,))
    need(manifest.get('composition') == {k: v['sha256'] for k, v in sorted(pins.items())}, f'composition hashes mismatch: {key}')
    pins[key] = {'id': wid, 'version': ver, 'sha256': sha}
    return pins


def publish(root, source, ver):
    version(ver)
    data = definition(source)
    pins = compositions(root, data, (data['id'],))
    folder = release_dir(root, data['id'], ver)
    folder.parent.mkdir(parents=True, exist_ok=True)
    folder.mkdir()  # Exclusive: even an incomplete existing release is never overwritten.
    (folder / 'WORKFLOW.md').write_bytes(Path(source).read_bytes())
    atomic(folder / 'release.json', {'schema': 1, 'id': data['id'], 'version': ver,
           'sha256': digest(folder / 'WORKFLOW.md'), 'composition': {k: v['sha256'] for k, v in sorted(pins.items())}, 'published_at': now()})
    closure(root, data['id'], ver)
    return str(folder)


def project(path):
    meta, _ = metadata(path)
    fields(meta, 'schema id input_defaults', 'project')
    need(type(meta.get('schema')) is int and meta.get('schema') == 1, 'project schema must be 1')
    ident(meta.get('id'))
    need(isinstance(meta.get('input_defaults', {}), dict), 'invalid project input defaults')
    for wid, defaults in meta.get('input_defaults', {}).items():
        ident(wid)
        need(isinstance(defaults, dict), 'workflow input defaults must be a mapping')
    return meta, Path(path).read_text()


def resolve_inputs(data, values):
    need(isinstance(values, dict), 'inputs must be an object')
    specs = data.get('inputs', {})
    need(set(values) <= set(specs), f'unknown inputs: {set(values) - set(specs)}')
    result = {k: s['default'] for k, s in specs.items() if 'default' in s}
    result.update(values)
    for k, spec in specs.items():
        need(not spec.get('required') or k in result and result[k] is not None, f'missing required input: {k}')
    return result


def records(steps, snapshot, inputs=None):
    result = {}
    for s in steps:
        rec = {'status': 'pending', 'attempts': []}
        if s['type'] == 'subworkflow':
            ref = s['workflow']
            child = definition(release_dir(snapshot, ref['id'], ref['version']) / 'WORKFLOW.md')
            mapped = {}
            for key, value in s.get('inputs', {}).items():
                if isinstance(value, dict) and set(value) == {'input'}:
                    need(inputs is not None and value['input'] in inputs, f'missing parent input binding: {s["id"]}')
                    mapped[key] = inputs[value['input']]
                else:
                    mapped[key] = value
            rec['inputs'] = resolve_inputs(child, mapped)
            rec['steps'] = records(child['steps'], snapshot, rec['inputs'])
        if s['type'] == 'iteration':
            rec['rounds'] = []
        result[s['id']] = rec
    return result


def initialize_round(steps, snapshot, inputs=None):
    return {'exit_met': None, 'assessment': '', 'evidence': [], 'steps': records(steps, snapshot, inputs)}


@contextlib.contextmanager
def mutation(run):
    lock = Path(run) / '.mutation.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        yield
    finally:
        lock.unlink()


def owner_check(run, owner):
    marker = read_json(Path(run) / 'owner.json')
    need(marker.get('owner') == owner, 'coordinator ownership mismatch')


def claim(run, owner, prior=None, evidence=None):
    need(owner.strip(), 'owner identity required')
    with mutation(run):
        marker = Path(run) / 'owner.json'
        old = read_json(marker) if marker.exists() else None
        if old:
            need(prior == old['owner'] and evidence and evidence.strip(), 'active coordinator exists; establish prior coordinator stopped and provide --prior-owner and --prior-stopped-evidence')
        atomic(marker, {'owner': owner, 'claimed_at': now(), 'prior_owner': prior, 'prior_stopped_evidence': evidence})
        with (Path(run) / 'journal.md').open('a') as f:
            f.write(f'\n- {now()} Coordinator claimed: {owner}. Prior stopped evidence: {evidence or "released/unowned run"}.\n')


def nonempty(value, label):
    need(isinstance(value, str) and value.strip(), f'{label} must be a nonempty string')


def string_list(value, label):
    need(isinstance(value, list), f'{label} must be a list')
    for item in value:
        nonempty(item, label)
    need(len(value) == len(set(value)), f'duplicate {label}')


def coordination_binding(binding):
    fields(binding, 'schema provider ticket peer claim_id work_area resources dependencies', 'coordination binding')
    need(type(binding.get('schema')) is int and binding['schema'] == 1, 'coordination schema must be 1')
    for key in ('provider', 'ticket', 'peer', 'claim_id', 'work_area'):
        nonempty(binding.get(key), key)
    for key in ('resources', 'dependencies'):
        string_list(binding.get(key), key)
    need(binding['ticket'] not in binding['dependencies'], 'ticket cannot depend on itself')


COORD_FIELDS = {
    'claim_intent': 'message_id',
    'claim_observation': 'accessible claim_seen active_claims',
    'dependency_assessment': 'ticket accepted',
    'conflict': 'active_claims',
    'resolution': 'resolves mode withdrawn_claims',
    'progress': '',
    'release': 'message_id status inspected',
    'handoff': 'message_id status inspected successor',
    'result_publication': 'message_id status inspected final evidence_refs',
}


def coordination_event(run, binding, event, prior):
    need(isinstance(event, dict) and event.get('kind') in COORD_FIELDS, 'invalid coordination event kind')
    kind = event['kind']
    fields(event, 'id kind claim_id observed_at explanation external_ref evidence ' + COORD_FIELDS[kind], 'coordination event')
    for key in ('id', 'claim_id', 'observed_at', 'explanation'):
        nonempty(event.get(key), key)
    need(event['id'] not in {e['id'] for e in prior}, 'duplicate coordination event ID')
    need(event['claim_id'] == binding['claim_id'], 'invalid claim reference')
    need(datetime.fromisoformat(event['observed_at'].replace('Z', '+00:00')).tzinfo is not None, 'observation time requires timezone')
    evidence(run, event.get('evidence'))
    if 'external_ref' in event:
        nonempty(event['external_ref'], 'external_ref')
    if kind in {'claim_observation', 'conflict'}:
        string_list(event.get('active_claims'), 'active_claims')
        if kind == 'claim_observation':
            for key in ('accessible', 'claim_seen'):
                need(type(event.get(key)) is bool, f'{key} boolean required')
            need(event['claim_seen'] == (binding['claim_id'] in event['active_claims']), 'claim_seen disagrees with active claims')
            need(event['accessible'] or not event['claim_seen'], 'inaccessible claim cannot be observed')
        else:
            need(set(event['active_claims']) - {binding['claim_id']}, 'competing claim required')
    if kind == 'dependency_assessment':
        need(event.get('ticket') in binding['dependencies'], 'invalid dependency reference')
        need(type(event.get('accepted')) is bool, 'accepted boolean required')
    if kind == 'resolution':
        string_list(event.get('resolves'), 'resolves')
        string_list(event.get('withdrawn_claims'), 'withdrawn_claims')
        need(event['resolves'] and event.get('mode') in {'withdrawals', 'user'}, 'resolution references and mode required')
        conflicts = {e['id']: set(e.get('active_claims', [])) - {binding['claim_id']}
                     for e in prior if e['kind'] in {'conflict', 'claim_observation'}}
        for ref in event['resolves']:
            need(ref in conflicts and conflicts[ref], 'invalid conflict reference')
            if event['mode'] == 'withdrawals':
                need(conflicts[ref] <= set(event['withdrawn_claims']), 'all competing claims must withdraw')
    if kind == 'claim_intent' or kind in {'release', 'handoff', 'result_publication'}:
        nonempty(event.get('message_id'), 'message_id')
        previous = [e for e in prior if e.get('message_id') == event['message_id']]
        if previous:
            need(kind != 'claim_intent' and all(e['kind'] == kind for e in previous), 'message ID reused for a different action')
            need(previous[-1]['status'] != 'confirmed', 'confirmed message cannot be retried')
            need(event.get('inspected') is True, 'inspect uncertain publication before retry or receipt')
            for key in ('final', 'evidence_refs', 'successor'):
                need(event.get(key) == previous[-1].get(key), f'changed message payload: {key}')
        if kind != 'claim_intent':
            need(event.get('status') in {'planned', 'uncertain', 'confirmed', 'not-performed'}, 'invalid publication status')
            if 'inspected' in event:
                need(type(event['inspected']) is bool, 'inspected boolean required')
            if event['status'] == 'confirmed':
                nonempty(event.get('external_ref'), 'confirmed external_ref')
        if kind == 'handoff':
            nonempty(event.get('successor'), 'successor')
        if kind == 'result_publication':
            final = event.get('final')
            fields(final, 'passed assessment evidence handoff', 'published final result')
            need(final.get('passed') is True, 'published final criteria must pass')
            assessment(run, final)
            string_list(event.get('evidence_refs'), 'evidence_refs')
            need(event['evidence_refs'], 'accessible evidence references required')


def validate_coordination(run, state):
    if 'coordination' not in state:
        return
    coord = state['coordination']
    fields(coord, 'binding events', 'coordination')
    coordination_binding(coord.get('binding'))
    need(isinstance(coord.get('events'), list), 'coordination events must be a list')
    for i, event in enumerate(coord['events']):
        coordination_event(run, coord['binding'], event, coord['events'][:i])


def coordination_transition(old, new):
    if 'coordination' not in old:
        need('coordination' not in new, 'cannot add binding to an existing run')
        return
    prev, cur = old['coordination'], new.get('coordination', {})
    need(cur.get('binding') == prev['binding'], 'changed frozen coordination binding')
    events = cur.get('events', [])
    need(len(events) >= len(prev['events']) and events[:len(prev['events'])] == prev['events'], 'changed coordination history')


def start(root, pid, wid, ver, inputs, environment, owner, coordination=None):
    if coordination is not None:
        coordination_binding(coordination)
    ident(pid)
    ident(wid)
    ppath = Path(root) / 'projects' / pid / 'PROJECT.md'
    pmeta, ptext = project(ppath)
    need(pmeta['id'] == pid, 'project identity mismatch')
    if ver is None:
        candidates = [p.name for p in (Path(root) / 'workflows' / wid / 'versions').iterdir() if p.is_dir() and VERSION.fullmatch(p.name)]
        need(candidates, 'no published versions')
        ver = max(candidates, key=version)
    pins = closure(root, wid, ver)
    data = definition(release_dir(root, wid, ver) / 'WORKFLOW.md')
    defaults = pmeta.get('input_defaults', {}).get(wid, {})
    need(isinstance(defaults, dict), 'workflow defaults must be an object')
    resolved = resolve_inputs(data, defaults | inputs)
    need(isinstance(environment.get('executor'), str) and environment['executor'], 'executor identity required')
    need(isinstance(environment.get('capabilities'), list) and all(isinstance(x, str) for x in environment['capabilities']), 'observed capabilities required')
    need(isinstance(environment.get('skills'), dict), 'resolved skill identities required')
    for name, identity in environment['skills'].items():
        need(isinstance(identity, dict) and identity.get('identity'), f'skill identity missing: {name}')
    rid = now().replace(':', '').replace('.', '-') + '-' + uuid.uuid4().hex[:8]
    run = Path(root) / 'projects' / pid / 'runs' / rid
    run.mkdir(parents=True)
    (run / 'artifacts').mkdir()
    snapshot = run / 'workflow-snapshot'
    for pin in pins.values():
        source = release_dir(root, pin['id'], pin['version'])
        dest = release_dir(snapshot, pin['id'], pin['version'])
        dest.mkdir(parents=True)
        for name in ('WORKFLOW.md', 'release.json'):
            (dest / name).write_bytes((source / name).read_bytes())
    context = run / 'project-snapshot.md'
    context.write_text(ptext)
    state = {'schema': 1, 'run_id': rid, 'project_id': pid, 'workflow': {'id': wid, 'version': ver},
             'pins': pins, 'inputs': resolved, 'project_sha256': digest(context), 'environment': environment,
             'created_at': now(), 'updated_at': now(), 'revision': 0, 'status': 'running',
             'steps': records(data['steps'], snapshot, resolved), 'final': None}
    if coordination is not None:
        state['coordination'] = {'binding': coordination, 'events': []}
    atomic(run / 'state.json', state)
    (run / 'journal.md').write_text(f'# Run {rid}\n\nSelected {wid}@{ver}. Inputs and project context are frozen in this run.\n')
    claim(run, owner)
    validate_run(run)
    return str(run)


def eligibility(step, state):
    """Structural only; returns ready, waiting, or skipped. Agent evaluates prose."""
    for gate in step.get('when', []):
        decision = state[gate['decision']]
        if decision['status'] == 'skipped':
            return 'skipped'
        if decision['status'] != 'completed':
            return 'waiting'
        if gate['branch'] not in decision.get('choice', []):
            return 'skipped'
    deps = step.get('selected_dependencies') if step.get('join') == 'selected' else step.get('depends_on', [])
    outcomes = [state[d]['status'] for d in deps]
    if any(s not in TERMINAL for s in outcomes):
        return 'waiting'
    if 'join' not in step and 'skipped' in outcomes:
        return 'skipped'
    return 'ready'


def evidence(run, paths):
    need(isinstance(paths, list) and paths, 'nonempty evidence list required')
    for name in paths:
        need(isinstance(name, str), 'evidence path must be a string')
        p = (Path(run) / name).resolve()
        need(not Path(name).is_absolute() and p.is_relative_to(Path(run).resolve()) and p.is_file(), f'missing or unsafe evidence: {name}')


def assessment(run, value):
    need(isinstance(value.get('assessment'), str) and value['assessment'].strip(), 'completion assessment required')
    evidence(run, value.get('evidence'))


def no_active(recs, context):
    for rec in recs.values():
        need(rec['status'] in TERMINAL | {'cancelled', 'failed'}, f'{context} has active work')
        if rec['status'] in TERMINAL:
            continue  # Descendants of skipped containers are inapplicable.
        if 'steps' in rec:
            no_active(rec['steps'], context)
        for rnd in rec.get('rounds', []):
            no_active(rnd['steps'], context)


def check_scope(run, steps, recs, snapshot, env, inactive=False, inputs=None):
    need(isinstance(recs, dict) and set(recs) == {s['id'] for s in steps}, 'checkpoint step IDs mismatch')
    for s in steps:
        sid = s['id']
        rec = recs[sid]
        need(isinstance(rec, dict), f'step record must be an object: {sid}')
        status = rec.get('status')
        need(status in STATUSES, f'invalid status: {sid}')
        eligible = eligibility(s, recs)
        if inactive:
            need(status in {'pending', 'cancelled'}, f'inactive container has started children: {sid}')
        if status == 'skipped':
            need(eligible == 'skipped', f'cannot skip applicable step: {sid}')
            need(rec.get('reason'), f'skip reason required: {sid}')
        attempts = rec.get('attempts')
        need(isinstance(attempts, list), f'attempts missing: {sid}')
        active_attempt = status == 'blocked' and attempts and attempts[-1].get('status') == 'running'
        if status in {'running', 'completed', 'failed'} or active_attempt:
            need(eligible == 'ready', f'dependencies not satisfied: {sid}')
            missing = [c for c in s.get('capabilities', []) if c not in env['capabilities']]
            missing += [k['name'] for k in s.get('skills', []) if k['required'] and k['name'] not in env['skills']]
            need(not missing, f'unavailable required capabilities or skills: {sid}: {missing}')
        if status in {'blocked', 'failed', 'cancelled'}:
            need(rec.get('reason'), f'{status} reason required: {sid}')
        if status in {'pending', 'skipped'}:
            need(not attempts, f'unstarted/skipped step has attempts: {sid}')
        if status == 'blocked' and attempts:
            need(attempts[-1]['status'] in {'running', 'failed', 'cancelled'}, f'blocked step has completed latest attempt: {sid}')
        if status == 'cancelled' and attempts:
            need(attempts[-1]['status'] in {'failed', 'cancelled'}, f'cancelled step has active attempt: {sid}')
        for i, attempt in enumerate(attempts, 1):
            need(isinstance(attempt, dict), f'attempt must be an object: {sid}')
            need(attempt.get('number') == i and attempt.get('status') in {'running', 'failed', 'completed', 'cancelled'}, f'invalid attempt: {sid}')
            if i < len(attempts):
                need(attempt['status'] in {'failed', 'cancelled'}, f'nonfailed prior attempt: {sid}')
            if attempt.get('evidence'):
                evidence(run, attempt['evidence'])
            if attempt['status'] == 'completed':
                assessment(run, attempt)
                need(all(a.get('status') in {'confirmed', 'not-performed'} for a in attempt.get('external_actions', [])), f'unreconciled external action at completion: {sid}')
            for action in attempt.get('external_actions', []):
                need(action.get('description') and action.get('status') in {'planned', 'confirmed', 'uncertain', 'not-performed'}, f'invalid external action: {sid}')
                if i < len(attempts):
                    need(action.get('reconciliation') and action['status'] in {'confirmed', 'not-performed'}, f'unreconciled external action before retry: {sid}')
        if status in {'running', 'failed', 'completed'}:
            need(attempts and attempts[-1]['status'] == status, f'latest attempt/status mismatch: {sid}')
        if status == 'completed':
            if s['type'] == 'decision':
                choice = rec.get('choice')
                need(isinstance(choice, list) and choice and len(set(choice)) == len(choice) and set(choice) <= set(s['branches']), f'invalid decision choice: {sid}')
                need(s.get('selection', 'one') == 'many' or len(choice) == 1, f'decision requires one branch: {sid}')
                need(rec.get('reason'), f'decision reason required: {sid}')
            if s['type'] == 'approval':
                approval = rec.get('approval', {})
                need(all(isinstance(approval.get(k), str) and approval[k].strip() for k in ('by', 'scope', 'result', 'approved_at')), f'concrete user approval required: {sid}')
                evidence(run, approval.get('evidence'))
        if s['type'] == 'subworkflow':
            ref = s['workflow']
            child = definition(release_dir(snapshot, ref['id'], ref['version']) / 'WORKFLOW.md')
            mapped = {k: inputs[v['input']] if isinstance(v, dict) and set(v) == {'input'} else v for k, v in s.get('inputs', {}).items()}
            need(rec.get('inputs') == resolve_inputs(child, mapped), f'changed subworkflow inputs: {sid}')
            check_scope(run, child['steps'], rec.get('steps'), snapshot, env, inactive or status in {'pending', 'skipped'}, rec['inputs'])
            if status == 'cancelled':
                no_active(rec['steps'], f'cancelled subworkflow: {sid}')
            if status == 'completed':
                need(all(r['status'] in TERMINAL for r in rec['steps'].values()), f'unfinished subworkflow: {sid}')
                assessment(run, rec.get('final', {}))
                need(rec['final'].get('passed') is True, f'subworkflow final criteria not passed: {sid}')
        if s['type'] == 'iteration':
            rounds = rec.get('rounds')
            need(isinstance(rounds, list) and len(rounds) <= s['max_iterations'], f'iteration bound exceeded: {sid}')
            need(not rounds or status not in {'pending', 'skipped'}, f'inactive iteration has rounds: {sid}')
            for i, rnd in enumerate(rounds):
                need('exit_met' in rnd and (rnd['exit_met'] is None or type(rnd['exit_met']) is bool), f'invalid exit assessment: {sid}')
                check_scope(run, s['steps'], rnd.get('steps'), snapshot, env, inactive, inputs)
                if status == 'cancelled':
                    no_active(rnd['steps'], f'cancelled iteration: {sid}')
                finished = all(r['status'] in TERMINAL for r in rnd['steps'].values())
                if i < len(rounds) - 1 or rnd['exit_met'] is not None:
                    need(finished, f'unfinished iteration round: {sid}')
                    assessment(run, rnd)
                if i < len(rounds) - 1:
                    need(rnd['exit_met'] is False, f'iteration continued without failed exit assessment: {sid}')
            if status == 'completed':
                need(rounds and rounds[-1]['exit_met'] is True, f'iteration exit not met: {sid}')
            if rounds and len(rounds) == s['max_iterations'] and rounds[-1]['exit_met'] is False and all(r['status'] in TERMINAL for r in rounds[-1]['steps'].values()):
                need(status in {'blocked', 'cancelled'}, f'iteration exhausted; record blocker: {sid}')


def validate_run(run, state=None):
    run = Path(run)
    state = read_json(run / 'state.json') if state is None else state
    need(isinstance(state, dict), 'state must be an object')
    need(state.get('schema') == 1 and state.get('run_id') == run.name and type(state.get('revision')) is int and state['revision'] >= 0, 'run identity/schema/revision mismatch')
    ident(state.get('project_id'))
    ref = state['workflow']
    snapshot = run / 'workflow-snapshot'
    pins = closure(snapshot, ref['id'], ref['version'])
    need(state.get('pins') == pins, 'snapshot pins mismatch')
    need(digest(run / 'project-snapshot.md') == state.get('project_sha256'), 'altered project snapshot')
    data = definition(release_dir(snapshot, ref['id'], ref['version']) / 'WORKFLOW.md')
    need(state.get('inputs') == resolve_inputs(data, state.get('inputs')), 'unresolved inputs')
    env = state.get('environment', {})
    need(env.get('executor') and isinstance(env.get('capabilities'), list) and isinstance(env.get('skills'), dict), 'executor environment missing')
    validate_coordination(run, state)
    check_scope(run, data['steps'], state.get('steps'), snapshot, env, inputs=state['inputs'])
    need(state.get('status') in {'running', 'blocked', 'failed', 'completed', 'cancelled'}, 'invalid run status')
    if state['status'] == 'completed':
        need(all(r['status'] in TERMINAL for r in state['steps'].values()), 'unfinished workflow')
        need(state.get('final', {}).get('passed') is True, 'workflow final criteria not passed')
        assessment(run, state['final'])
        if 'coordination' in state:
            coordination_ready(state)
            publications = [e for e in state['coordination']['events'] if e['kind'] == 'result_publication']
            need(publications and publications[-1]['status'] == 'confirmed', 'confirmed result publication required')
            need(publications[-1]['final'] == state['final'], 'final differs from published result')
    if state['status'] in {'blocked', 'failed', 'cancelled'}:
        need(state.get('reason'), 'run reason required')
    if state['status'] == 'cancelled':
        no_active(state['steps'], 'cancelled run')
    return state


def transitions(old, new, retry_authorization):
    need(set(old) <= set(new), 'discarded step records')
    for sid, cur in new.items():
        prev = old.get(sid, {'status': 'pending', 'attempts': []})
        need(len(cur['attempts']) >= len(prev['attempts']), f'discarded attempts: {sid}')
        for i, attempt in enumerate(prev['attempts']):
            replacement = cur['attempts'][i]
            need(set(attempt.get('evidence', [])) <= set(replacement.get('evidence', [])), f'discarded attempt evidence: {sid}')
            old_actions = attempt.get('external_actions', [])
            new_actions = replacement.get('external_actions', [])
            need(len(new_actions) >= len(old_actions), f'discarded external actions: {sid}')
            for a, b in zip(old_actions, new_actions):
                need(a['description'] == b['description'], f'changed external action identity: {sid}')
                if a['status'] in {'confirmed', 'not-performed'}:
                    need(a == b, f'changed reconciled action: {sid}')
            if attempt['status'] != 'running':
                # Failed actions may acquire reconciliation evidence, but outcomes/evidence remain.
                frozen = {k: v for k, v in attempt.items() if k != 'external_actions'}
                need(all(replacement.get(k) == v for k, v in frozen.items()), f'changed attempt history: {sid}')
                old_actions = attempt.get('external_actions', [])
                new_actions = replacement.get('external_actions', [])
                need(len(old_actions) == len(new_actions), f'discarded external actions: {sid}')
                for a, b in zip(old_actions, new_actions):
                    need(a['description'] == b['description'], f'changed external action identity: {sid}')
                    if a['status'] not in {'uncertain', 'planned'}:
                        need(a == b, f'changed reconciled external action: {sid}')
        if prev['status'] == 'cancelled':
            need(cur['status'] == 'cancelled', f'cancelled step cannot restart: {sid}')
        if prev['status'] in TERMINAL:
            need(prev == cur, f'changed completed/skipped work: {sid}')
        if len(cur['attempts']) > len(prev['attempts']):
            need(len(cur['attempts']) == len(prev['attempts']) + 1, f'attempts must advance one at a time: {sid}')
            need(cur['attempts'][-1]['status'] == 'running', f'new attempt must be checkpointed as running: {sid}')
            if prev['attempts']:
                need(retry_authorization, f'retry requires explicit authorization or declared policy evidence: {sid}')
                need(cur.get('retry_authorization') == retry_authorization, f'retry authorization must be recorded: {sid}')
        if 'steps' in cur:
            transitions(prev.get('steps', {}), cur['steps'], retry_authorization)
        if 'rounds' in cur:
            prior_rounds = prev.get('rounds', [])
            need(len(prior_rounds) <= len(cur['rounds']) <= len(prior_rounds) + 1, f'round history changed: {sid}')
            for a, b in zip(prior_rounds, cur['rounds']):
                transitions(a['steps'], b['steps'], retry_authorization)
                if a['assessment']:
                    need(all(b.get(k) == a[k] for k in ('exit_met', 'assessment', 'evidence')), f'changed iteration assessment: {sid}')
            for rnd in cur['rounds'][len(prior_rounds):]:
                transitions({}, rnd['steps'], retry_authorization)


def transition(run, owner, revision, note, apply, retry=None):
    need(note.strip(), 'journal note required')
    with mutation(run):
        owner_check(run, owner)
        old = validate_run(run)
        need(revision == old["revision"], "stale transition revision")
        new = copy.deepcopy(old)
        apply(new)
        need(old['status'] not in {'completed', 'cancelled'}, 'terminal run cannot be changed; create a new run')
        for k in ('schema', 'run_id', 'project_id', 'workflow', 'pins', 'inputs', 'project_sha256', 'environment', 'created_at'):
            need(new.get(k) == old.get(k), f'changed frozen run field: {k}')
        need(new.get('revision') == old['revision'], 'stale checkpoint revision')
        coordination_transition(old, new)
        transitions(old['steps'], new['steps'], retry)
        new['revision'] += 1
        new['updated_at'] = now()
        validate_run(run, new)
        # Journal first: interruption can leave a proposal note, never an unjournaled commit.
        with (Path(run) / 'journal.md').open('a') as f:
            f.write(f'\n- {now()} Checkpoint proposal revision {new["revision"]}, coordinator {owner}: {note}\n')
        atomic(Path(run) / 'state.json', new)
    return new['revision']


def scopes(run, state):
    snapshot = Path(run) / 'workflow-snapshot'
    ref = state['workflow']
    path = release_dir(snapshot, ref['id'], ref['version']) / 'WORKFLOW.md'
    def visit(path, steps, recs, prefix, inputs, active):
        for step in steps:
            rec = recs[step['id']]
            pointer = prefix + '/' + step['id']
            yield pointer, step, rec, recs, inputs, path, active
            enabled = active and rec['status'] == 'running'
            if step['type'] == 'subworkflow':
                ref = step['workflow']
                child = release_dir(snapshot, ref['id'], ref['version']) / 'WORKFLOW.md'
                yield from visit(child, definition(child)['steps'], rec['steps'], pointer+'/steps', rec['inputs'], enabled)
            for i, rnd in enumerate(rec.get('rounds', [])):
                yield from visit(path, step['steps'], rnd['steps'], pointer+f'/rounds/{i}/steps', inputs, enabled and i == len(rec['rounds'])-1 and rnd['exit_met'] is None)
    yield from visit(path, definition(path)['steps'], state['steps'], '/steps', state['inputs'], True)


def locate(run, state, pointer):
    item = next((item for item in scopes(run, state) if item[0] == pointer), None)
    need(item is not None, f'unknown step pointer: {pointer}; use ready or status --json')
    return item


def coordination_readiness(state):
    if 'coordination' not in state:
        return {'status': 'unbound', 'blockers': []}
    coord = state['coordination']
    binding = coord['binding']
    observed = None
    conflicts = set()
    dependencies = {}
    released = False
    transfers = {}
    for event in coord['events']:
        kind = event['kind']
        if kind == 'claim_observation':
            observed = event
        if kind in {'claim_observation', 'conflict'} and set(event['active_claims']) - {binding['claim_id']}:
            conflicts.add(event['id'])
        if kind == 'resolution':
            conflicts.difference_update(event['resolves'])
        if kind == 'dependency_assessment':
            dependencies[event['ticket']] = event['accepted']
        if kind in {'release', 'handoff'}:
            transfers[event['message_id']] = event['status']
            if event['status'] == 'confirmed':
                released = True
    blockers = []
    if observed is None or not observed['claim_seen']:
        blockers.append('claim-unobserved')
    if observed is not None and not observed['accessible']:
        blockers.append('ticket-unavailable')
    if conflicts:
        blockers.append('unresolved-conflict')
    if any(not dependencies.get(ticket, False) for ticket in binding['dependencies']):
        blockers.append('dependency-unassessed')
    if any(status in {'planned', 'uncertain'} for status in transfers.values()):
        blockers.append('transfer-unreconciled')
    if released:
        blockers.append('claim-released')
    return {'status': 'blocked' if blockers else 'observed-without-conflict',
            'blockers': blockers, 'conflicts': sorted(conflicts)}


def coordination_ready(state):
    blockers = coordination_readiness(state)['blockers']
    need(not blockers, 'coordination blocked: ' + ', '.join(blockers))


def readiness(run, state):
    rows = []
    for pointer, step, rec, peers, inputs, path, active in scopes(run, state):
        if rec['status'] in TERMINAL | {'cancelled'}:
            continue
        structural = eligibility(step, peers)
        missing = [c for c in step.get('capabilities', []) if c not in state['environment']['capabilities']]
        missing += [s['name'] for s in step.get('skills', []) if s['required'] and s['name'] not in state['environment']['skills']]
        if state['status'] in {'completed', 'cancelled'} or not active:
            category, reason = 'waiting', 'container is not running or round is closed'
        elif structural == 'skipped':
            category, reason = 'skippable', 'branch guard or skipped dependency excludes this step'
        elif structural == 'waiting':
            category, reason = 'waiting', 'dependencies or decision outcomes are unfinished'
        elif coordination_readiness(state)['blockers']:
            category, reason = 'coordination-blocked', ', '.join(coordination_readiness(state)['blockers'])
        elif missing:
            category, reason = 'capability-blocked', 'missing: ' + ', '.join(missing)
        elif rec['status'] in {'blocked', 'failed'}:
            category, reason = 'waiting', rec.get('reason', 'retry authorization required')
        else:
            category, reason = 'ready', 'begin attempt' if rec['status'] == 'pending' else 'inspect existing attempt; complete or reconcile'
        rows.append({'path': pointer, 'type': step['type'], 'status': rec['status'], 'category': category, 'reason': reason})
    return {'revision': state['revision'], 'steps': rows, 'coordination': coordination_readiness(state)}


def step_operation(run, state, pointer, op, result):
    _, step, rec, peers, inputs, path, active = locate(run, state, pointer)
    need(active, 'container is not running or round is closed')
    need(rec['status'] not in TERMINAL | {'cancelled'}, 'terminal step cannot be changed')
    fields(result, 'assessment evidence external_actions blockers handoff reason choice approval final authorization', 'step result')
    if op in {'begin', 'retry'}:
        coordination_ready(state)
        need(eligibility(step, peers) == 'ready', 'step is not structurally ready')
        need(rec['status'] == 'pending' if op == 'begin' else rec['status'] in {'failed', 'blocked'}, 'invalid begin/retry status')
        if op == 'retry':
            need(result.get('authorization'), 'retry authorization required')
            need(not rec['attempts'] or rec['attempts'][-1]['status'] != 'running', 'fail or resume the current attempt before retry')
            rec['retry_authorization'] = result['authorization']
        rec['attempts'].append({'number': len(rec['attempts'])+1, 'status': 'running', 'started_at': now(), 'external_actions': result.get('external_actions', [])})
        rec['status'] = 'running'
    elif op == 'skip':
        need(rec['status'] == 'pending' and eligibility(step, peers) == 'skipped', 'step is not structurally skippable')
        need(result.get('reason'), 'skip reason required')
        rec.update(status='skipped', reason=result['reason'])
    elif op == 'reconcile':
        need(rec['attempts'], 'no attempt to reconcile')
        need('external_actions' in result, 'action receipts required')
        rec['attempts'][-1]['external_actions'] = result['external_actions']
    elif op == 'block':
        need(result.get('reason'), 'block reason required')
        rec.update(status='blocked', reason=result['reason'])
    else:
        need(rec['attempts'] and rec['attempts'][-1]['status'] == 'running', 'running attempt required')
        attempt = rec['attempts'][-1]
        attempt.update({k: v for k, v in result.items() if k in {'assessment', 'evidence', 'external_actions', 'blockers', 'handoff'}})
        attempt['status'] = rec['status'] = 'completed' if op == 'complete' else 'failed'
        for k in ('choice', 'reason', 'approval', 'final'):
            if k in result: rec[k] = result[k]
    if result.get('handoff'): rec['handoff'] = result['handoff']


def round_operation(run, state, pointer, op, result):
    _, step, rec, peers, inputs, path, active = locate(run, state, pointer)
    need(active and step['type'] == 'iteration' and rec['status'] == 'running', 'running iteration required')
    if op == 'open':
        coordination_ready(state)
        need(not result, 'open does not accept a result')
        need(len(rec['rounds']) < step['max_iterations'], 'iteration bound exhausted')
        need(not rec['rounds'] or rec['rounds'][-1]['exit_met'] is False, 'assess previous round before opening another')
        rec['rounds'].append(initialize_round(step['steps'], Path(run)/'workflow-snapshot', inputs))
    else:
        fields(result, 'exit_met assessment evidence', 'round result')
        need(rec['rounds'] and rec['rounds'][-1]['exit_met'] is None, 'unassessed round required')
        need(type(result.get('exit_met')) is bool, 'exit_met boolean required')
        assessment(run, result)
        rec['rounds'][-1].update(result)
        if not result['exit_met'] and len(rec['rounds']) == step['max_iterations']:
            rec.update(status='blocked', reason='iteration bound exhausted')


def cancel_records(recs, reason):
    for rec in recs.values():
        if rec['status'] in TERMINAL | {'cancelled'}: continue
        rec.update(status='cancelled', reason=reason)
        if rec['attempts'] and rec['attempts'][-1]['status'] == 'running':
            rec['attempts'][-1]['status'] = 'cancelled'
        if 'steps' in rec: cancel_records(rec['steps'], reason)
        for rnd in rec.get('rounds', []): cancel_records(rnd['steps'], reason)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'inspect', 'publish'):
        p = sub.add_parser(name); p.add_argument('definition'); p.add_argument('--root', default='.' if name == 'publish' else None)
        if name == 'publish': p.add_argument('--version', required=True)
    p = sub.add_parser('verify-release'); p.add_argument('workflow'); p.add_argument('version'); p.add_argument('--root', default='.')
    p = sub.add_parser('project'); p.add_argument('project'); p.add_argument('--root', default='.'); p.add_argument('--brief', required=True)
    p = sub.add_parser('start'); p.add_argument('project'); p.add_argument('workflow'); p.add_argument('--version'); p.add_argument('--root', default='.'); p.add_argument('--inputs'); p.add_argument('--environment', required=True); p.add_argument('--owner', required=True)
    p.add_argument('--coordination')
    for name in ('status', 'ready', 'context', 'validate-run', 'claim', 'release', 'step', 'round', 'finish', 'cancel'):
        p = sub.add_parser(name); p.add_argument('run')
        if name == 'status': p.add_argument('--json', action='store_true')
        if name in {'context', 'step', 'round'}: p.add_argument('step')
        if name == 'step': p.add_argument('op', choices=['begin', 'complete', 'fail', 'block', 'skip', 'retry', 'reconcile'])
        if name == 'round': p.add_argument('op', choices=['open', 'assess'])
        if name in {'step', 'round', 'finish', 'cancel', 'claim', 'release'}: p.add_argument('--owner', required=True)
        if name in {'step', 'round', 'finish', 'cancel'}: p.add_argument('--revision', required=True, type=int)
        if name in {'step', 'round', 'finish'}: p.add_argument('--result', required=name == 'finish')
        if name == 'cancel': p.add_argument('--reason', required=True)
        if name == 'claim':
            p.add_argument('--prior-owner'); p.add_argument('--prior-stopped-evidence')
    p = sub.add_parser('coordination'); p.add_argument('run')
    ops = p.add_subparsers(dest='op', required=True)
    ops.add_parser('show')
    p = ops.add_parser('record'); p.add_argument('--result', required=True)
    p.add_argument('--owner', required=True); p.add_argument('--revision', required=True, type=int)
    args = parser.parse_args()
    cmd = args.command
    if cmd in {'validate', 'inspect', 'publish'}:
        data = definition(args.definition)
        if args.root: compositions(args.root, data, (data['id'],))
        result = {'valid': True, 'id': data['id'], 'diagnostics': []}
        if cmd == 'inspect': result.update(inputs=data.get('inputs', {}), steps=data['steps'])
        if cmd == 'publish': result = {'release': publish(args.root, args.definition, args.version)}
    elif cmd == 'verify-release': result = closure(args.root, args.workflow, args.version)
    elif cmd == 'project':
        ident(args.project)
        dest = Path(args.root)/'projects'/args.project
        dest.mkdir(parents=True, exist_ok=False)
        for name in ('inputs', 'outputs', 'runs'): (dest/name).mkdir()
        meta = {'schema': 1, 'id': args.project, 'input_defaults': {}}
        (dest/'PROJECT.md').write_text('---\n'+yaml.safe_dump(meta, sort_keys=False)+'---\n# Project\n\n## Brief\n'+args.brief+'\n\n## Work areas\nRecord paths and mutation boundaries here.\n')
        result = {'project': str(dest)}
    elif cmd == 'start': result = {'run': start(args.root, args.project, args.workflow, args.version, read_json(args.inputs) if args.inputs else {}, read_json(args.environment), args.owner, read_json(args.coordination) if args.coordination else None)}
    else:
        state = validate_run(args.run)
        if cmd == 'coordination' and args.op == 'show':
            result = {'revision': state['revision'], 'coordination': state.get('coordination')}
        elif cmd == 'claim':
            claim(args.run, args.owner, args.prior_owner, args.prior_stopped_evidence)
            result = {'owner': args.owner}
        elif cmd == 'release':
            with mutation(args.run):
                owner_check(args.run, args.owner)
                (Path(args.run)/'owner.json').unlink()
            result = {'released': True}
        elif cmd == 'validate-run': result = {'valid': True, 'revision': state['revision'], 'diagnostics': []}
        elif cmd == 'ready': result = readiness(args.run, state)
        elif cmd == 'status':
            result = dict(state, readiness=readiness(args.run, state)) if args.json else None
            if result is None:
                rows = readiness(args.run, state)['steps']
                print(f"{state['status']} | revision {state['revision']} | {sum(r['status'] in TERMINAL for r in state['steps'].values())}/{len(state['steps'])} top-level steps done")
                for row in rows:
                    approval = ' | approval pending' if row['type'] == 'approval' else ''
                    print(f"{row['path']}: {row['status']} / {row['category']} — {row['reason']}{approval}")
                return
        elif cmd == 'context':
            pointer, step, rec, peers, inputs, path, active = locate(args.run, state, args.step)
            data, prose = metadata(path)
            sections = WorkflowProse(prose, data['steps'])
            section = sections.step(step['id'])
            preamble = sections.preamble()
            ancestors = []
            for parent_path, parent_step, parent_rec, parent_peers, _, parent_file, _ in scopes(args.run, state):
                if not pointer.startswith(parent_path + '/'):
                    continue
                parent_data, parent_prose = metadata(parent_file)
                parent_section = WorkflowProse(parent_prose, parent_data['steps']).step(parent_step['id'])
                ancestors.append({'path': parent_path, 'metadata': parent_step, 'prose': parent_section,
                                  'predecessors': {d: parent_peers[d] for d in parent_step.get('depends_on', [])}})
            result = {'ancestors': ancestors, 'path': pointer, 'revision': state['revision'], 'metadata': step, 'workflow_context': preamble, 'step_prose': section, 'completion_criteria': sections.completion(), 'inputs': inputs, 'project': (Path(args.run)/'project-snapshot.md').read_text(), 'predecessors': {d: peers[d] for d in step.get('depends_on', [])}, 'record': rec}
        else:
            supplied = read_json(args.result) if getattr(args, 'result', None) else {}
            def apply(new):
                if cmd == 'coordination':
                    need('coordination' in new, 'run has no coordination binding')
                    if supplied.get('kind') == 'result_publication':
                        coordination_ready(new)
                        need(all(r['status'] in TERMINAL for r in new['steps'].values()), 'unfinished workflow cannot publish result')
                    new['coordination']['events'].append(supplied)
                elif cmd == 'step': step_operation(args.run, new, args.step, args.op, supplied)
                elif cmd == 'round': round_operation(args.run, new, args.step, args.op, supplied)
                elif cmd == 'finish':
                    fields(supplied, 'passed assessment evidence handoff', 'final result')
                    new.update(status='completed', final=supplied)
                elif cmd == 'cancel':
                    need(args.reason.strip(), 'cancellation reason required')
                    cancel_records(new['steps'], args.reason)
                    new.update(status='cancelled', reason=args.reason)
                if cmd in {'step', 'round'}:
                    blocked = [r.get('reason', 'blocked') for _, _, r, *_ in scopes(args.run, new) if r['status'] in {'blocked', 'failed'}]
                    new['status'] = 'blocked' if blocked else 'running'
                    if blocked: new['reason'] = '; '.join(blocked)
                    else: new.pop('reason', None)
            result = {'revision': transition(args.run, args.owner, args.revision, cmd+' '+getattr(args, 'op', '')+' '+getattr(args, 'step', ''), apply, supplied.get('authorization'))}
    print(json.dumps(result, indent=2, sort_keys=True))


def diagnostic(error):
    message = str(error)
    rules = [('duplicate', 'WF_DUPLICATE', 'Remove the duplicate key or identifier.'), ('unknown fields', 'WF_FIELD', 'Use only documented structural fields.'), ('heading', 'WF_PROSE', 'Add the matching stable-ID heading.'), ('prose', 'WF_PROSE', 'Add Task, Inputs, Outputs and Acceptance sections.'), ('YAML', 'WF_YAML', 'Use one safe YAML front matter mapping with JSON-compatible values.'), ('revision', 'RUN_REVISION', 'Read status and use its current revision.'), ('owner', 'RUN_OWNER', 'Claim ownership using the recovery protocol.'), ('evidence', 'RUN_EVIDENCE', 'Save evidence within the run and reference its relative path.')]
    code, correction = next(((code, fix) for word, code, fix in rules if word.lower() in message.lower()), ('WF_INVALID', 'Inspect the relevant document or run context and correct the reported constraint.'))
    return {'code': code, 'severity': 'error', 'location': {'document': sys.argv[2] if len(sys.argv)>2 else None, 'step': next((a for a in sys.argv[3:] if a.startswith('/steps/')), None)}, 'explanation': message, 'suggested_correction': correction}


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, AttributeError, IndexError, StopIteration, yaml.YAMLError) as error:
        print(json.dumps({'diagnostics': [diagnostic(error)]}), file=sys.stderr)
        sys.exit(1)
