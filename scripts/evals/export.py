#!/usr/bin/env python3
"""Export aggregate metrics and credential-free synthetic evidence after a frozen batch."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

import run


def export(root, output, archive):
    plan=run.verify(root)
    results=[json.loads(p.read_text()) for p in sorted((root/'runs').glob('*/result.json'))]
    output.mkdir(parents=True,exist_ok=True)
    for name in ['plan.json','plan.sha256','summary.json']:
        shutil.copy2(root/name,output/name)
    for name in ['screen-selection.json','screen-selection.sha256','screen-summary.json','scope-correction.json']:
        if (root/name).exists():shutil.copy2(root/name,output/name)
    fields=['index','case','cell','arm','trial','compliant_success','task_success','hard_failures','elapsed_seconds','tool_calls','tool_errors','sessions','timeouts','input_tokens','cached_input_tokens','output_tokens','usage_sessions','partial_usage_sessions','native_records','valid_native_records','question_count','scripted_interventions','human_minutes','repair_minutes','independent_utility','failure_attribution']
    with (output/'metrics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for r in results:
            usage=[s['usage'] for s in r['sessions'] if s['usage'] is not None]
            row={k:r.get(k) for k in ['index','case','cell','arm','trial','elapsed_seconds','tool_calls','question_count','scripted_interventions','human_minutes','repair_minutes','independent_utility']}
            row.update({k:r['objective'][k] for k in ['compliant_success','task_success']})
            row.update(hard_failures=json.dumps(r['objective']['hard_failures']),failure_attribution=json.dumps(r['failure_attribution']),sessions=len(r['sessions']),timeouts=sum(bool(s['stop_reason']) for s in r['sessions']),tool_errors=sum(s['tool_errors'] for s in r['sessions']),
                       input_tokens=sum(u['input'] for u in usage) if usage else None,cached_input_tokens=sum(u['cached'] for u in usage) if usage else None,output_tokens=sum(u['output'] for u in usage) if usage else None,
                       usage_sessions=len(usage),partial_usage_sessions=sum(s['usage_coverage']=='partial' for s in r['sessions']),native_records=r['objective']['protocol']['records'],valid_native_records=r['objective']['protocol']['valid'])
            writer.writerow(row)
    run.save(output/'outcomes.json',[{k:r[k] for k in ['index','case','cell','arm','trial','objective','failure_attribution','followups']} for r in results])
    run.save(output/'preflight.json',[{k:r[k] for k in ['cell','objective','elapsed_seconds','sessions']} for p in sorted((root/'preflight').glob('*/result.json')) for r in [json.loads(p.read_text())]])
    # Only explicit evidence allowlist; config/auth directories, caches and symlinks are excluded.
    members=[]
    for p in sorted(root.rglob('*')):
        relative=p.relative_to(root)
        if not p.is_file() or p.is_symlink() or any(part in ['pi-agent','.uv-cache','cache-template','.git','__pycache__','.tmp'] for part in relative.parts):continue
        if p.name in ['auth.json','models.json'] and relative.parts[0]!='frozen':continue
        if relative.parts[0] not in ['runs','preflight','frozen','blind-review'] and len(relative.parts)>1:continue
        members.append((relative,p))
    manifest={str(relative):run.oracle.digest(p) for relative,p in members}
    run.save(root/'evidence-manifest.json',manifest)
    archive.parent.mkdir(parents=True,exist_ok=True)
    if archive.exists():raise ValueError('Do not overwrite a prior evidence archive')
    with tarfile.open(archive,'w:gz') as tar:
        for relative,p in members:tar.add(p,arcname=str(relative),recursive=False)
        tar.add(root/'evidence-manifest.json',arcname='evidence-manifest.json',recursive=False)
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar.getmembers():
            if not member.isfile():raise ValueError('Archive must contain files only')
            if member.name=='evidence-manifest.json':continue
            if hashlib.sha256(tar.extractfile(member).read()).hexdigest()!=manifest[member.name]:raise ValueError('Archived evidence checksum mismatch')
    run.save(output/'evidence-integrity.json',{'archive':str(archive),'sha256':run.oracle.digest(archive),'bytes':archive.stat().st_size,'files':len(manifest),'all_members_verified':True,'excluded':['all symlinks','pi-agent including authentication','dependency caches','.git','scratch files'], 'frozen_verified':True})
    print(json.dumps({'exported_episodes':len(results),'archive_sha256':run.oracle.digest(archive)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('batch');p.add_argument('output');p.add_argument('--archive',required=True);a=p.parse_args()
    export(Path(a.batch).resolve(),Path(a.output).resolve(),Path(a.archive).resolve())
