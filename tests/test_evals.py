#!/usr/bin/env python3
"""Grade known good/bad outcomes, not the grader's implementation details."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts/evals'))
import oracle


class OutcomeGrading(unittest.TestCase):
    def test_research_semantic_variants_and_mutations(self):
        sources = [{'id':'a','price':80,'region':'EU','retention_days':7,'soc2':None,'url':'https://a.invalid/v2'},
                   {'id':'b','price':70,'region':'US','retention_days':7,'soc2':'certified','url':'https://b.invalid/v1'}]
        data = {'recommendation':'a','options':copy.deepcopy(sources)}
        for o in data['options']:o['source']=o.pop('url')
        data['options'][0]['price']='80';data['options'][0]['soc2']='Unknown: no primary evidence'
        policy = {'budget':100,'region':'EU','retention_days':7}
        self.assertTrue(all(oracle.research(data,sources,policy).values()))
        for field,value in [('price',79),('region','US'),('retention_days',30),('source','https://a.invalid/v1'),('soc2','certified')]:
            bad=copy.deepcopy(data);bad['options'][0][field]=value
            self.assertFalse(all(oracle.research(bad,sources,policy).values()))
        bad=copy.deepcopy(data);bad['recommendation']='b'
        self.assertFalse(oracle.research(bad,sources,policy)['selection'])
        self.assertFalse(all(oracle.research({'recommendation':'a'},sources,policy).values()))

    def test_independent_review_requires_reproducible_counterexample(self):
        good={'findings':[{'input':[2,3],'expected':'2.5','observed':2}]}
        self.assertTrue(oracle.review(good,'floor')['verified_defect'])
        for bad in [{'findings':[]},{'findings':[{'input':[2,2],'expected':2,'observed':2}]},{'findings':[{'input':[2,3],'expected':2.5,'observed':3}]}]:
            self.assertFalse(oracle.review(bad,'floor')['verified_defect'])
        self.assertTrue(oracle.review({'findings':[{'input':[0,2],'expected':1,'observed':2}]},'zeros')['verified_defect'])

    def test_hidden_tests_distinguish_plausible_broken_code(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'candidate.py'
            good='import math\ndef summarize(values):\n v=[x for x in values if x is not None]\n if any(not math.isfinite(x) for x in v):raise ValueError()\n return dict(count=len(v),total=sum(v),mean=sum(v)/len(v) if v else None)\n'
            p.write_text(good)
            result=json.loads(subprocess.check_output(oracle.hidden_code_tests(p),text=True))
            self.assertTrue(all(result))
            p.write_text(good.replace('sum(v)/len(v)','sum(v)//len(v)'))
            self.assertFalse(all(json.loads(subprocess.check_output(oracle.hidden_code_tests(p),text=True))))

    def test_unknown_and_numbers_do_not_accept_false_claims(self):
        self.assertIsNone(oracle.number(True));self.assertIsNone(oracle.number('NaN'))
        self.assertTrue(oracle.unknown(None));self.assertFalse(oracle.unknown('certified'))

    def test_missing_usage_is_not_zero_and_mcp_errors_count(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.jsonl'
            p.write_text(json.dumps({'type':'item.completed','item':{'type':'mcp_tool_call','status':'failed','error':'bad args'}})+'\n')
            m=oracle.trace_metrics(p,'codex');self.assertIsNone(m['usage']);self.assertEqual(m['tool_errors'],1)


if __name__=='__main__':unittest.main()
