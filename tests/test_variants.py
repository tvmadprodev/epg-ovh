import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

class VariantTests(unittest.TestCase):
    def test_real_refs_are_unique_and_polish_only(self):
        with (ROOT/'data/polish_services.tsv').open(encoding='utf8') as f:
            base=list(csv.DictReader(f,delimiter='\t'))
        with (ROOT/'data/verified_variants.tsv').open(encoding='utf8') as f:
            extras=list(csv.DictReader(f,delimiter='\t'))
        assert len(base)==212 and len(extras)==148
        refs=[r['ref'] for r in base+extras]
        self.assertEqual(len(refs),len(set(refs)))
        self.assertTrue({r['name'] for r in extras}<={r['name'] for r in base})
        for r in extras:
            self.assertTrue(r['ref'].startswith('1:0:'))
            self.assertEqual(r['ref'].split(':')[6].upper(),'820000')

    def test_canal_duplicate_refs_are_present(self):
        with (ROOT/'data/verified_variants.tsv').open(encoding='utf8') as f:
            extras=list(csv.DictReader(f,delimiter='\t'))
        byname={}
        for r in extras:byname.setdefault(r['name'],[]).append(r['ref'])
        self.assertIn('1:0:1:3D55:2C88:13E:820000:0:0:0:',byname['CANAL+ 1 HD'])
        self.assertIn('1:0:1:3AD2:514:13E:820000:0:0:0:',byname['CANAL+ SPORT 3 HD'])
        self.assertIn('1:0:1:3AF1:514:13E:820000:0:0:0:',byname['CANAL+ SPORT 4 HD'])

    def test_verified_missing_ids(self):
        ids=json.loads((ROOT/'data/manual_ids.json').read_text(encoding='utf8'))
        self.assertEqual(ids['Historia Poland'],'Discovery Historia')
        self.assertEqual(ids['ID Poland HD'],'ID')
        self.assertEqual(ids['Turbo Xtra Poland HD'],'DTX')
        self.assertNotIn('Mango',ids)

if __name__=='__main__':unittest.main()
