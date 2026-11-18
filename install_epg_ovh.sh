#!/bin/sh
# EPG.OVH Polska -> GitHub -> EPGImport (OpenPLi / OpenATV)
# Nie zmienia EIT, epg.dat, list kanalow ani TvMad OS Core.
set -eu
URL='https://github.com/tvmadprodev/epg-ovh/releases/download/epg-ovh'
TARGET='/etc/epgimport'
TMP="/tmp/epg-ovh-installer-$$"
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP"
printf '\n=== EPG.OVH Polska - instalacja ===\n'

if command -v curl >/dev/null 2>&1; then
    download() { curl -fLsS --retry 2 --connect-timeout 20 --max-time 180 -o "$2" "$1"; }
elif command -v wget >/dev/null 2>&1; then
    download() { wget -q -O "$2" "$1"; }
else
    echo 'BLAD: Nie znaleziono curl ani wget.' >&2
    exit 1
fi
command -v python3 >/dev/null 2>&1 || { echo 'BLAD: Brak Python3.' >&2; exit 1; }

echo 'Pobieram ovh.sources.xml i ovh.channels.xml z GitHub...'
download "$URL/ovh.sources.xml" "$TMP/ovh.sources.xml"
download "$URL/ovh.channels.xml" "$TMP/ovh.channels.xml"

# Weryfikacja przed jakimikolwiek zmianami w /etc/epgimport.
python3 - "$TMP/ovh.sources.xml" "$TMP/ovh.channels.xml" <<'PYVALIDATE'
import sys
from xml.etree import ElementTree as ET
src, mapping = sys.argv[1:]
r = ET.parse(src).getroot()
assert r.tag == 'sources', 'Niepoprawny plik zrodel'
entries = r.findall('.//source')
assert len(entries) == 2, 'Oczekiwano dwoch zrodel EPG'
for source in entries:
    assert source.attrib.get('channels') == 'ovh.channels.xml', 'Niepoprawna nazwa mapowania'
    assert source.attrib.get('type') == 'gen_xmltv', 'Niepoprawny format EPG'
    assert source.findtext('url', '').startswith('https://github.com/tvmadprodev/epg-ovh/'), 'Niepoprawny URL EPG'
m = r.findall('./mappings/channel')
assert len(m) == 1 and m[0].get('name') == 'ovh.channels.xml', 'Niepoprawna definicja mapowania'
assert m[0].findtext('url', '').endswith('/ovh.channels.xml'), 'Niepoprawny adres mapowania'
root = ET.parse(mapping).getroot()
assert root.tag == 'channels', 'Niepoprawny kanalowy XML'
channels = root.findall('channel')
assert len(channels) >= 150, 'Za malo referencji w mapowaniu'
for c in channels:
    ref = (c.text or '').strip()
    assert c.get('id') and ref.startswith('1:0:'), 'Niepoprawny wpis w mapowaniu'
    assert ref.split(':')[6].upper() == '820000', 'Obcy satelita w mapowaniu'
print('OK: 2 zrodla, %d polskich referencji DVB, mapowanie XML.' % len(channels))
PYVALIDATE

mkdir -p "$TARGET"
stamp=$(date +%Y%m%d_%H%M%S)
for fname in ovh.sources.xml ovh.channels.xml; do
    if [ -f "$TARGET/$fname" ]; then
        cp -p "$TARGET/$fname" "$TARGET/$fname.bak_$stamp"
        echo "Kopia poprzedniej wersji: $fname"
    fi
    cp "$TMP/$fname" "$TARGET/$fname.new_$$"
    chmod 644 "$TARGET/$fname.new_$$"
    mv -f "$TARGET/$fname.new_$$" "$TARGET/$fname"
done
if [ -f "$TARGET/ovh.channels.xml.gz" ]; then
    cp -p "$TARGET/ovh.channels.xml.gz" "$TARGET/ovh.channels.xml.gz.bak_$stamp"
    rm -f "$TARGET/ovh.channels.xml.gz"
    echo 'Usunieto stare skompresowane mapowanie (kopia zapasowa zachowana).'
fi
printf '\nGOTOWE: %s/ovh.sources.xml i ovh.channels.xml\n' "$TARGET"
echo 'Restart GUI Enigma2 -> EPGImport -> Zrodla -> wybierz Standard LUB PLUS -> import reczny.'
echo 'Nalezy odznaczyc stare zrodla OVH, jesli byly dodane wczesniej.'
sleep 5
