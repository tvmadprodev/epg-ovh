#!/usr/bin/env python3
"""Fail if converting OVH PLUS changes channel identifiers, event times or titles."""
import argparse
import gzip
import itertools
import xml.etree.ElementTree as ET

def keys(file):
    with gzip.open(file,'rb') as fp:
        root=None
        for status,node in ET.iterparse(fp,events=('start','end')):
            if root is None and status=='start':root=node
            if status!='end':continue
            if node.tag=='channel':
                yield ('channel',node.get('id'),node.findtext('display-name'))
            elif node.tag=='programme':
                yield ('programme',node.get('channel'),node.get('start'),node.get('stop'),node.findtext('title'))
            else:continue
            root.clear()

def verify(before,after,minimum=0):
    number=0
    for number,(a,b) in enumerate(itertools.zip_longest(keys(before),keys(after)),1):
        if a!=b:
            raise ValueError('Inconsistent XMLTV source / result at item %d: %s != %s'%(number,a,b))
    if number<minimum:raise ValueError('Too few channels and events: %d'%number)
    print('OK: source and formatted feed have the same channel IDs, titles, event times and order:',number)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('before');p.add_argument('after')
    p.add_argument('--min-items',type=int,default=0)
    x=p.parse_args()
    verify(x.before,x.after,x.min_items)
