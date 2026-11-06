"""Run without network: python -m unittest discover -s tests -v"""
import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reporter', ROOT / 'scripts/quality_report.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class ReporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.evidence = Path(self.tmp.name)
        shutil.copytree(ROOT / 'sample-evidence', self.evidence, dirs_exist_ok=True)
        env = patch.dict(os.environ, {'GITHUB_SHA':'synthetic-demo','ACTIONS_ID_TOKEN_REQUEST_URL':'https://example.invalid/oidc','ACTIONS_ID_TOKEN_REQUEST_TOKEN':'never-print-me'})
        env.start()
        self.addCleanup(env.stop)
    def call(self, url, token, payload=None):
        if payload is None: return {'value':'mock-identity'}
        self.assertLessEqual(len(payload['input']),12000)
        return {'text':'Example assessment'}
    def test_success(self):
        result = r.generate(self.evidence,'https://example.run.app',call=self.call)
        for text in ['Measured evidence','AI assessment','Human evaluation','Limitations','synthetic-demo']: self.assertIn(text,result)
        self.assertNotIn('never-print-me',result)
    def test_missing_evidence_no_network(self):
        (self.evidence/'pylint.txt').unlink()
        with self.assertRaisesRegex(RuntimeError,'Missing evidence'): r.generate(self.evidence,'https://example.run.app',call=lambda *a: self.fail('network called'))
    def test_malformed_coverage(self):
        (self.evidence/'coverage.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError,'Invalid coverage'): r.generate(self.evidence,'https://example.run.app',call=self.call)
    def test_wrong_commit(self):
        (self.evidence/'commit.txt').write_text('different')
        with self.assertRaisesRegex(RuntimeError,'commit'): r.generate(self.evidence,'https://example.run.app',call=self.call)
    def test_empty_response(self):
        with self.assertRaisesRegex(RuntimeError,'usable assessment'): r.generate(self.evidence,'https://example.run.app',call=lambda *a: {'value':'id','text':''})
    def test_timeout(self):
        def fail(*args): raise TimeoutError()
        with self.assertRaises(TimeoutError): r.generate(self.evidence,'https://example.run.app',call=fail)
    def test_unauthorized(self):
        def fail(*args): raise RuntimeError('Service returned HTTP 403; no automatic retry.')
        with self.assertRaisesRegex(RuntimeError,'403'): r.generate(self.evidence,'https://example.run.app',call=fail)
    def test_truncation(self):
        (self.evidence/'pylint.txt').write_text('x'*30000)
        self.assertIn('TRUNCATED',r.generate(self.evidence,'https://example.run.app',call=self.call))
if __name__ == '__main__': unittest.main()
