#!/usr/bin/env python3
"""Build one Polish-only, referential EPGImport channel map from a curated DVB ref list.

No lamedb or bouquet data is read on end-user receivers. The curated service
references were extracted from *two explicitly Polish* bouquets by the maintainer.
Ambiguous TV IDs are skipped (with a report), never guessed.
"""
import argparse
import csv
import gzip
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

# Only vetted aliases of the *same Polish broadcast*. No broad fuzzy similarity.
NAME_ALIASES = {
    'TVN 24 HD': ['TVN 24', 'TVN24'],
    'TVN24 BiS HD': ['TVN24 BiS', 'TVN 24 BiS'],
    'TVP 1 HD': ['TVP 1', 'TVP1'],
    'TVP 2 HD': ['TVP 2', 'TVP2'],
    'Cartoon Network Poland HD': ['Cartoon Network Poland', 'Cartoon Network'],
    'Cartoonito Poland HD': ['Cartoonito Poland', 'Cartoonito'],
    'Eleven Sports 1 HD': ['Eleven Sports 1'],
    'Eleven Sports 1 4K': ['Eleven Sports 4K', 'Eleven Sports 1 4K'],
    'Dla Ciebie TV': ['DLACIEBIE TV'],
    'wPolsce24': ['wPolsce 24'],
    'CANAL+ PREMIUM HD': ['CANAL+ PREMIUM', 'Canal+ Premium'],
    'TVN Fabula': ['TVN Fabuła'],
    'TVP INFO HD': ['TVP INFO'],
    'TVP HD': ['TVP HD'],
    'Eurosport 1 Poland HD': ['Eurosport 1 Poland', 'Eurosport 1'],
    'Eurosport 2 Poland HD': ['Eurosport 2 Poland', 'Eurosport 2'],
    'KINO POLSKA HD': ['Kino Polska'],
    'Paramount Network Polska': ['Paramount Network Polska'],
    'Animal Planet Poland HD': ['Animal Planet Poland', 'Animal Planet'],
    'Discovery Poland HD': ['Discovery Poland', 'Discovery'],
    'Nick Jr': ['Nick Jr.'],
    'BBC Cbeebies': ['CBeebies'],
    'Sundance HD': ['Sundance TV', 'Sundance'],
    'Wydarzenia 24 HD': ['Wydarzenia 24'],
    'Polsat News HD': ['Polsat News'],
    'Polsat News 2 HD': ['Polsat News 2'],
    'SciFi HD': ['SciFi', 'Sci Fi'],
    'NATIONAL GEO HD': ['National Geographic'],
    'National Geographic Wild HD': ['Nat Geo Wild', 'National Geographic Wild'],
}


def exact_name(s):
    return ' '.join(unicodedata.normalize('NFKC', s or '').casefold().split())


def match_name(s):
    """Limited normalization: remove resolution suffix but KEEP 4K distinctly."""
    s = unicodedata.normalize('NFKD', s or '').casefold()
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r'^(?:pl[\s:|._-]+)', '', s)
    s = re.sub(r'\s+(?:full\s*hd|fhd|hd|sd|uhd)\s*$', '', s)
    return re.sub(r'[^a-z0-9]+', '', s)


def feed_channels(path):
    opener = gzip.open if str(path).lower().endswith('.gz') else open
    channels = []
    with opener(path,'rb') as f:
        parser = ET.iterparse(f, events=('start','end'))
        first = True
        for event,elem in parser:
            if first and event=='start':
                if elem.tag!='tv': raise ValueError(f'Brak korzenia XMLTV <tv> w {path}')
                first=False
            if event!='end':continue
            if elem.tag == 'programme':
                break
            if elem.tag == 'channel':
                cid = (elem.attrib.get('id') or '').strip()
                if cid:
                    display = [(x.text or '').strip() for x in elem.findall('display-name') if x.text]
                    channels.append((cid,display))
                elem.clear()
    if len(channels)<50: raise ValueError(f'Za malo kanalow XMLTV w {path}: {len(channels)}')
    return channels


def xmltv_index(paths):
    ids=defaultdict(set); display=defaultdict(set)
    all_ids=set(); counts={}
    for path in paths:
        rows=feed_channels(path)
        counts[str(path)] = len(rows)
        for cid, names in rows:
            all_ids.add(cid)
            ids[('exact',exact_name(cid))].add(cid)
            ids[('loose',match_name(cid))].add(cid)
            for nm in names:
                display[('exact',exact_name(nm))].add(cid)
                display[('loose',match_name(nm))].add(cid)
    return ids, display, all_ids,counts


def choose(name, ids, display, manual):
    override = manual.get(name)
    if override:
        present = ids.get(('exact',exact_name(override)),set())
        if override in present: return override, 'manual'
        return None, 'BLAD: manual ID nieobecny w XMLTV: '+override
    tries = [name] + NAME_ALIASES.get(name,[])
    ambiguous=[]
    for key in tries:
        for level, idx, strategy in [
            ('exact',ids,'xmltv_id_exact'),
            ('loose',ids,'xmltv_id_normalized'),
            ('exact',display,'display_exact'),
            ('loose',display,'display_normalized')
        ]:
            normkey = exact_name(key) if level=='exact' else match_name(key)
            candidates = idx.get((level,normkey), set())
            if len(candidates)==1: return next(iter(candidates)),strategy
            if len(candidates)>1: ambiguous.append((strategy,sorted(candidates)))
    if ambiguous:
        return None,'niejednoznaczne: '+', '.join('/'.join(x[1][:5]) for x in ambiguous[:2])
    return None,'brak identyfikatora w XMLTV'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--services', default='data/polish_services.tsv')
    ap.add_argument('--variants', default='data/verified_variants.tsv')
    ap.add_argument('--pl',default='pl.gz')
    ap.add_argument('--pltv',default='pltv.gz')
    ap.add_argument('--manual',default='data/manual_ids.json')
    ap.add_argument('--out',default='mappings/ovh.channels.xml')
    ap.add_argument('--report',default='reports/mapowanie.tsv')
    ap.add_argument('--min',type=int,default=70)
    a=ap.parse_args()
    src=list(csv.DictReader(open(a.services,encoding='utf-8'),delimiter='\t'))
    if a.variants and Path(a.variants).exists():
        extra=list(csv.DictReader(open(a.variants,encoding='utf-8'),delimiter='\t'))
        seen={r['ref'] for r in src}
        for r in extra:
            if r['ref'] in seen: continue
            src.append(r)
            seen.add(r['ref'])
    if len(src)<120:raise SystemExit('Za malo zweryfikowanych polskich referencji DVB')
    ids,display,all_ids,counts=xmltv_index([a.pl,a.pltv])
    manual=json.load(open(a.manual,encoding='utf-8')) if Path(a.manual).exists() else {}
    if not isinstance(manual,dict):raise ValueError('manual_ids.json must be JSON object')
    outcomes=[]
    for service in src:
        name,ref=service['name'],service['ref']
        if not re.fullmatch(r'1:0:[0-9A-Fa-f]+:(?:[0-9A-Fa-f]+:){7}',ref):
            raise ValueError('Nieprawidlowa referencja: '+ref)
        if ref.split(':')[6].upper()!='820000':
            raise ValueError('Obcy satelita w polskiej bazie: '+ref)
        cid,status=choose(name,ids,display,manual)
        outcomes.append({'name':name,'ref':ref,'id':cid or '', 'status':status})
    # Reject reuse of a feed ID across different channels unless these are true
    # normalized variants (e.g. Wydarzenia 24 and Wydarzenia 24 HD).
    byid=defaultdict(list)
    for r in outcomes:
        if r['id']:byid[r['id'].casefold()].append(r)
    for members in byid.values():
        normnames={match_name(r['name']) for r in members}
        if len(normnames)>1:
            for r in members:
                r['id']=''
                r['status']='KONFLIKT: ten sam XMLTV ID przypisany do roznych stacji: '+', '.join(sorted(set(x['name'] for x in members)))
    match=[r for r in outcomes if r['id']]
    print('Kanaly w XMLTV:',counts)
    print('Polskie referencje:',len(src),'dopasowane:',len(match),'pominiete:',len(src)-len(match))
    if len(match)<a.min: raise SystemExit('Za malo mapowan. Nie publikuj pliku. Wymagana kontrola raportu.')
    # XML with multiple service refs per XMLTV id, duplicate-safe, no text guessing.
    root=ET.Element('channels')
    for r in sorted(match,key=lambda row:(row['id'].casefold(),row['ref'])):
        ET.SubElement(root,'channel',{'id':r['id']}).text=r['ref']
    ET.indent(root,space='  ')
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
    ET.ElementTree(root).write(p,encoding='utf-8',xml_declaration=True)
    report=Path(a.report); report.parent.mkdir(parents=True,exist_ok=True)
    with report.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,['name','ref','id','status'],delimiter='\t',lineterminator='\n')
        w.writeheader();w.writerows(outcomes)
    print('Mapowanie:',p,'Raport:',report)
    print('TVN24:',[r for r in outcomes if r['name']=='TVN 24 HD'])

if __name__=='__main__':main()
