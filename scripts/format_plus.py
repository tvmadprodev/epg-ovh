#!/usr/bin/env python3
"""Convert OVH's PLUS description metadata into readable text and DVB EPG fields.

This touches only the PLUS XMLTV feed. It does not alter channel IDs, event
times, titles, the descriptive body, or EPGImport channel mappings.
"""
import argparse
import gzip
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from xml.sax.saxutils import quoteattr

CATEGORIES = {
    'komedia':'Comedy', 'film komediowy':'Comedy', 'serial komediowy':'Comedy',
    'komedia romantyczna':'Romance', 'film romantyczny':'Romance',
    'melodramat':'Romance', 'dramat':'Drama', 'dramat obyczajowy':'Drama',
    'film obyczajowy':'Drama', 'serial obyczajowy':'Soap',
    'serial dramatyczny':'Drama', 'telenowela':'Soap',
    'serial szpiegowski':'Detective/Thriller',
    'serial kryminalny':'Crime/Mystery', 'film kryminalny':'Crime/Mystery',
    'serial sensacyjny':'Action', 'film sensacyjny':'Action',
    'film akcji':'Action', 'film przygodowy':'Adventure/Western/War',
    'film wojenny':'Adventure/Western/War',
    'film dokumentalny':'Documentary', 'serial dokumentalny':'Documentary',
    'dokument':'Documentary', 'program dokumentalny':'Documentary',
    'film przyrodniczy':'Nature/Animals/Environment',
    'program przyrodniczy':'Nature/Animals/Environment',
    'program informacyjny':'News', 'serwis informacyjny':'News',
    'wiadomosci':'News', 'magazyn informacyjny':'News Magazine',
    'magazyn pilkarski':'Sport Magazine', 'magazyn sportowy':'Sport Magazine',
    'sport':'Sports', 'sporty':'Sports', 'pilka nozna':'Football/Soccer',
    'tenis':'Tennis/Squash', 'teleturniej':'Game Show/Quiz/Contest',
    'reality show':'Reality', 'program rozrywkowy':'Variety Show',
    'program muzyczny':'Music', 'magazyn muzyczny':'Music',
    'program publicystyczny':'Discussion/Interview/Debate',
    'talk show':'Talk Show', 'serial animowany':'Cartoons/Puppets',
    'film animowany':'Animated', 'bajka':'Cartoons/Puppets',
    'program dla dzieci':"Children's/Youth Programme",
    'serial dla dzieci':"Children's/Youth Programme",
    'program edukacyjny':'Educational', 'film krotkometrazowy':'Film',
    'film fabularny':'Film', 'film':'Film', 'program kulinarny':'Cooking',
    'magazyn kulinarny':'Cooking'
}
FIELD_SPLIT = re.compile(r'\.\s+(?=(?:S\d+E\d+|E\d+|R\s*:|W\s*:|O\s*:))',re.I)
SE = re.compile(r'S(\d+)E(\d+)(?:/(\d+))?$',re.I)
EP = re.compile(r'E(\d+)(?:/(\d+))?$',re.I)

def normalize(value):
    value=unicodedata.normalize('NFKD',value or '').casefold()
    return re.sub(r'\s+',' ',''.join(ch for ch in value if not unicodedata.combining(ch))).strip()

def read_header(description):
    if not description: return None
    header,sep,body=description.partition('\n')
    if not re.match(r'^\s*G\s*:\s*\S',header,re.I): return None
    tokens=FIELD_SPLIT.split(header.strip())
    if not tokens[0].startswith('G:'): return None
    genre=tokens[0][2:].strip().strip('. ')
    if not genre or re.search(r'\.\s+[A-Za-z]{1,20}\s*:',genre):return None
    data={'genre':genre}
    for token in tokens[1:]:
        token=token.strip().strip('. ')
        match=SE.fullmatch(token)
        if match:
            data['season'],data['episode'],data['total']=match.groups()
        elif EP.fullmatch(token):
            data['episode'],data['total']=match.groups()
        elif re.fullmatch(r'R\s*:\s*\d{4}',token,re.I):
            data['year']=token.split(':')[1].strip()
        elif re.fullmatch(r'W\s*:\s*\d{1,2}',token,re.I):
            data['age']=int(token.split(':')[1].strip())
        elif re.fullmatch(r'O\s*:\s*\d+(?:[,.]\d+)?\s*/\s*\d+',token,re.I):
            data['score']=re.sub(r'\s+','',token.split(':',1)[1])
        else:
            return None # Unknown source syntax: do not lose any metadata.
    return data,body.strip() if sep else ''

def display_line(data):
    chunks=[data['genre'][0].upper()+data['genre'][1:]]
    if data.get('year'):chunks.append(data['year'])
    if data.get('episode'):
        number=data['episode']+(('/'+data['total']) if data.get('total') else '')
        if data.get('season'):
            chunks.append('Sezon %s, odcinek %s'%(data['season'],number))
        else:
            chunks.append('Odcinek '+number)
    if 'age' in data:
        if data['age']==0:chunks.append('Bez ograniczeń wiekowych')
        elif 0<data['age']<=18:chunks.append('Wiek: od %d lat'%data['age'])
    if data.get('score'):chunks.append('Ocena: '+data['score'])
    return ' • '.join(chunks)

def update_programme(p,counts):
    desc=p.find('desc')
    parsed=read_header(desc.text if desc is not None else None)
    if not parsed:
        counts['unchanged']+=1
        return
    data,body=parsed
    desc.text=display_line(data)+('\n\n'+body if body else '')
    counts['formatted']+=1
    # OpenPLi EPGImport converts *English* categories to native DVB genres.
    # Preserve original Polish category for other XMLTV consumers.
    old=p.find('category')
    key=normalize(data['genre'])
    category=CATEGORIES.get(key)
    if category is None and (key.startswith('sport,') or key.startswith('sports,')):
        category='Sports'
    if category and old is not None:
        extra=ET.Element('category',{'lang':'en'})
        extra.text=category
        p.insert(list(p).index(old),extra)
        counts['native_genre']+=1
    # The upstream PLUS has W:12 in the description, but no <rating>.
    # EPGImport parses <rating><value>12+</value></rating> as DVB age 12+.
    age=data.get('age')
    if age is not None and 4<=age<=18:
        rating=ET.Element('rating',{'system':'PL'})
        ET.SubElement(rating,'value').text=str(age)+'+'
        old_rating=p.find('rating')
        p.insert(list(p).index(old_rating) if old_rating is not None else len(p),rating)
        counts['native_age']+=1

def convert(original,target,min_events=0,min_formatted=0):
    counts=Counter()
    with gzip.open(original,'rb') as source,open(target,'wb') as file:
        with gzip.GzipFile(fileobj=file,mode='wb',compresslevel=6,mtime=0) as out:
            root=None
            for event,node in ET.iterparse(source,events=('start','end')):
                if event=='start' and root is None:
                    if node.tag!='tv':raise ValueError('Missing XMLTV root')
                    root=node
                    attrs=''.join(' %s=%s'%(k,quoteattr(str(v))) for k,v in root.attrib.items())
                    out.write(('<?xml version="1.0" encoding="utf-8"?>\n<tv%s>\n'%attrs).encode('utf-8'))
                    continue
                if event!='end':continue
                if node.tag=='channel':counts['channels']+=1
                elif node.tag=='programme':
                    counts['events']+=1
                    update_programme(node,counts)
                else:continue
                out.write(ET.tostring(node,encoding='utf-8'))
                out.write(b'\n')
                root.clear()
            if root is None:raise ValueError('Empty XMLTV')
            out.write(b'</tv>\n')
    if counts['events']<min_events or counts['formatted']<min_formatted:
        raise ValueError('Suspicious result: '+str(counts))
    print('Formatted EPG PLUS:',dict(counts))
    return counts

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--min-events',type=int,default=0)
    parser.add_argument('--min-formatted',type=int,default=0)
    args=parser.parse_args()
    convert(args.input,args.output,args.min_events,args.min_formatted)
