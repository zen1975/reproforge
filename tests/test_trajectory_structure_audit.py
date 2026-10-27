"""Regression tests for independent TQS structural-component analogue."""
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'studies/arxiv-2610.13152/experiments/run_structural_audit.py'
spec=importlib.util.spec_from_file_location('tqs_structural_audit',PATH)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class StructuralAuditTests(unittest.TestCase):
    def test_fixture_audit(self):
        self.assertEqual(m.audit()['assertions_passed'],6)
    def test_transition_constant_zero(self):
        self.assertEqual(m.tool_transition_entropy([m.step('read_file','x')]*8),0)
    def test_commit_middle_one(self):
        s=[m.step('read_file','x')]*10;s[3]=m.step('write_file','ok');self.assertEqual(m.solution_commitment_point(s),1)
    def test_no_commit_zero(self):
        self.assertEqual(m.solution_commitment_point([m.step('read_file','x')]*4),0)
    def test_error_repetition_zero(self):
        s=[m.step('execute_bash','error',['a'],True)]*4;self.assertEqual(m.post_error_diversity(s),0)
    def test_error_recovery_one(self):
        s=[m.step('execute_bash','error',['a'],True),m.step('read_file','new',['b']),m.step('submit','ok')];self.assertEqual(m.post_error_diversity(s),1)
    def test_no_error_undefined(self):
        self.assertIsNone(m.post_error_diversity([m.step('read_file','x')]*3))
    def test_zero_entropy_undefined(self):
        self.assertIsNone(m.observation_entropy_collapse([m.step('read_file','aaaa')]*4))
    def test_reject_unknown_action(self):
        with self.assertRaises(ValueError):m.features([m.step('unknown','x')]*3)
    def test_reject_short_trace(self):
        with self.assertRaises(ValueError):m.features([m.step('read_file','x')])

if __name__=='__main__':unittest.main()
