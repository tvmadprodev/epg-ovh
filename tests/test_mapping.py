import gzip
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_mapping import choose, match_name, xmltv_index

class MapTests(unittest.TestCase):
    def test_keep_4k_separate(self):
        self.assertNotEqual(match_name('Eleven Sports 1 HD'),match_name('Eleven Sports 1 4K'))
    def test_tvn24_not_bis(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'pl.gz'
            root=ET.Element('tv')
            for id_ in ('TVN 24','TVN 24 BiS'):
                ch=ET.SubElement(root,'channel',id=id_)
                ET.SubElement(ch,'display-name').text=id_
            ET.SubElement(root,'programme',channel='TVN 24')
            with gzip.open(p,'wb') as f:f.write(ET.tostring(root))
            # Less than 50 channels should reject broken/partial source.
            with self.assertRaises(ValueError):xmltv_index([p])
    def test_no_guessed_4k(self):
        ids={('loose',match_name('Eleven Sports 1')):{'Eleven Sports 1'}}
        id_,_=choose('Eleven Sports 1 4K',ids,{}, {})
        self.assertIsNone(id_)
    def test_exact_tvn24_priority(self):
        ids={('loose',match_name('TVN 24')):{'TVN 24'},('exact','tvn 24'):{'TVN 24'},('loose',match_name('TVN 24 BiS')):{'TVN 24 BiS'}}
        disp={('loose',match_name('TVN 24')):{'TVN 24','TVN 24 BiS'}}
        id_,why=choose('TVN 24 HD',ids,disp,{})
        self.assertEqual(id_,'TVN 24')

if __name__=='__main__': unittest.main()
