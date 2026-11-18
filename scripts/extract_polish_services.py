#!/usr/bin/env python3
"""Maintainer-only tool. Extract Polish DVB refs from a user-supplied Enigma2 settings ZIP.
Never automatically infer nationality from arbitrary bouquet titles.
"""
import argparse
import csv
from io import StringIO
from pathlib import Path
import zipfile

ALLOWED = ('userbouquet.polskie.tv', 'userbouquet.polskieFTA.tv')
SKIP = ('VOD ', 'Test180')
NAMESPACE = 0x820000  # 13.0 E, Hot Bird standard namespace


def get_db(zf):
    member = next((n for n in zf.namelist() if n.endswith('/lamedb5') or n == 'lamedb5'), None)
    if member is None:
        raise RuntimeError('Brak lamedb5')
    records = {}
    for ln in zf.read(member).decode('utf-8','replace').splitlines():
        if not ln.startswith('s:') or ',"' not in ln:
            continue
        hdr, rest = ln[2:].split(',"', 1)
        fields = hdr.split(':')
        if len(fields)<5: continue
        try:
            sid, ns, tsid, onid = [int(f, 16) for f in fields[:4]]
        except ValueError:
            continue
        name = rest.split('"',1)[0].strip()
        records[(sid,tsid,onid,ns)]=name
    return records


def extract(source):
    with zipfile.ZipFile(source) as zf:
        db=get_db(zf)
        members={Path(n).name:n for n in zf.namelist()}
        rows={}
        for shortname in ALLOWED:
            if shortname not in members: raise RuntimeError('Brak bukietu: '+shortname)
            for line in zf.read(members[shortname]).decode('utf8','replace').splitlines():
                if not line.startswith('#SERVICE '): continue
                val=line[9:].strip().split(':')
                if len(val)<11 or val[0:2]!=['1','0']: continue
                try:
                    sid,tsid,onid,ns=[int(v,16) for v in val[3:7]]
                except ValueError: continue
                if ns != NAMESPACE: continue
                name=db.get((sid,tsid,onid,ns))
                if not name or any(name.lower().startswith(ex.lower()) for ex in SKIP): continue
                ref=':'.join(val[:10])+':'
                rows[ref]={'name':name,'ref':ref,'origin':shortname}
        return sorted(rows.values(),key=lambda r:(r['name'].casefold(),r['ref']))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('zipfile')
    ap.add_argument('--output', default='data/polish_services.tsv')
    a=ap.parse_args()
    rows=extract(a.zipfile)
    if len(rows)<120: raise SystemExit('Zbyt malo polskich kanalow: '+str(len(rows)))
    p=Path(a.output);p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,['name','ref','origin'],delimiter='\t',lineterminator='\n')
        w.writeheader();w.writerows(rows)
    print('Zapisano',len(rows),'zweryfikowanych referencji z polskich bukietow:',p)

if __name__=='__main__':main()
