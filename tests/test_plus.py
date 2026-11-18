import gzip
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'scripts'))
from format_plus import read_header,display_line,update_programme,convert

class PlusTests(unittest.TestCase):
    def test_metadata_from_real_ovh_examples(self):
        examples={
            'G: komedia. R: 2025. W: 12. O: 6/10\n\nOpis':
                'Komedia • 2025 • Wiek: od 12 lat • Ocena: 6/10',
            'G: serial szpiegowski. S1E5/6. R: 2023. W: 12. O: 5/10\nOpis':
                'Serial szpiegowski • 2023 • Sezon 1, odcinek 5/6 • Wiek: od 12 lat • Ocena: 5/10',
            'G: teleturniej. E1118. W: 7\nOpis':
                'Teleturniej • Odcinek 1118 • Wiek: od 7 lat',
            'G: Sport, Pilka nozna. R: 2026':
                'Sport, Pilka nozna • 2026',
        }
        for line,expected in examples.items():
            with self.subTest(line=line):
                metadata,body=read_header(line)
                self.assertEqual(display_line(metadata),expected)
    def test_epgimport_native_genre_and_age(self):
        node=ET.fromstring('<programme channel="Canal+ Premium" start="20261118180000 +0000"><title>Film</title><desc>G: komedia. R: 2025. W: 12. O: 6/10&#10;&#10;Oryginalny opis.</desc><category lang="pl">komedia</category></programme>')
        stats=Counter()
        update_programme(node,stats)
        self.assertEqual([x.text for x in node.findall('category')],['Comedy','komedia'])
        self.assertEqual(node.findtext('rating/value'),'12+')
        self.assertIn('Oryginalny opis.',node.findtext('desc'))
        self.assertEqual(node.get('start'),'20261118180000 +0000')
        self.assertEqual(node.findtext('title'),'Film')
    def test_unknown_metadata_stays_untouched(self):
        for desc in ['Normalny tekst','G: komedia. NIEZNANE: 123. R: 2025\nOpis']:
            node=ET.Element('programme')
            ET.SubElement(node,'desc').text=desc
            update_programme(node,Counter())
            self.assertEqual(node.findtext('desc'),desc)
    def test_streaming_counts_and_original_descriptions(self):
        xml=b'<tv generator-info-name="OVH"><channel id="TVP 2"><display-name>TVP 2</display-name></channel><programme channel="TVP 2" start="20261118180000 +0000" stop="20261118190000 +0000"><title>A</title><desc>G: komedia. W: 12&#10;Opis.</desc><category lang="pl">komedia</category></programme><programme channel="TVP 2" start="20261118190000 +0000" stop="20261118200000 +0000"><title>B</title><desc>Bez prefiksu.</desc></programme></tv>'
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'before.gz';b=Path(d)/'after.gz'
            with gzip.open(a,'wb') as f:f.write(xml)
            c=convert(a,b,min_events=2,min_formatted=1)
            self.assertEqual(c['events'],2)
            with gzip.open(b,'rb') as f:root=ET.parse(f).getroot()
            self.assertEqual(root.attrib['generator-info-name'],'OVH')
            self.assertEqual(len(root.findall('programme')),2)
            self.assertEqual(root.findall('programme')[1].findtext('desc'),'Bez prefiksu.')

if __name__=='__main__': unittest.main()
