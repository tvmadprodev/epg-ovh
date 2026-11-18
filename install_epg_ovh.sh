#!/bin/sh
# EPG.OVH -> Github -> EPGImport; kompatybilne z BusyBox /bin/sh na OpenPLi i OpenATV.
# Nie zmienia list, EIT, epg.dat, ustawien skory ani TvMad OS Core.
set -eu
URL='https://github.com/tvmadprodev/epg-ovh/releases/download/epg-ovh'
TARGET='/etc/epgimport'
TMP="/tmp/epg-ovh-installer-$$"
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
mkdir -p "$TMP"
echo '==========================================='
echo ' EPG OVH Polska - instalacja dla Enigma2'
echo '==========================================='
if command -v curl >/dev/null 2>&1; then
    download() { curl -fLsS --retry 2 --connect-timeout 20 --max-time 180 -o "$2" "$1"; }
elif command -v wget >/dev/null 2>&1; then
    download() { wget -q -O "$2" "$1"; }
else
    echo 'BLAD: Wymagany curl lub wget.' >&2
    exit 1
fi
command -v python3 >/dev/null 2>&1 || { echo 'BLAD: Python3 nie jest dostepny.' >&2; exit 1; }
echo 'Pobieram zrodla i zweryfikowane mapowanie z GitHub...'
download "$URL/ovh.sources.xml" "$TMP/ovh.sources.xml"
download "$URL/ovh.channels.xml.gz" "$TMP/ovh.channels.xml.gz"
# Validate BEFORE touching any existing files.
python3 - "$TMP/ovh.sources.xml" "$TMP/ovh.channels.xml.gz" <<'PY'
import gzip,sys,xml.etree.ElementTree as ET
src,channels=sys.argv[1:]
r=ET.parse(src).getroot()
assert r.tag=='sources' and len(r.findall('.//source'))==2, 'Blad definicji zrodel'
assert len(r.findall('./mappings/channel'))==1, 'Brak pobierania mapowania'
with gzip.open(channels,'rb') as f:
    m=ET.parse(f).getroot()
assert m.tag=='channels' and len(m.findall('channel'))>=70, 'Mapowanie jest puste lub uszkodzone'
for ch in m.findall('channel'):
    assert ch.get('id') and (ch.text or '').startswith('1:0:'), 'Nieprawidlowa referencja DVB'
print('Zweryfikowano: 2 rodzaje EPG i',len(m.findall('channel')),'referencji DVB')
PY
mkdir -p "$TARGET"
stamp=$(date +%Y%m%d_%H%M%S)
for fname in ovh.sources.xml ovh.channels.xml.gz; do
    if [ -f "$TARGET/$fname" ]; then
        cp -p "$TARGET/$fname" "$TARGET/$fname.bak_$stamp"
        echo "Kopia: $TARGET/$fname.bak_$stamp"
    fi
    cp "$TMP/$fname" "$TARGET/$fname.new_$$"
    chmod 644 "$TARGET/$fname.new_$$"
    mv -f "$TARGET/$fname.new_$$" "$TARGET/$fname"
done
printf '\n'
echo 'GOTOWE. Nie wykonano automatycznego restartu GUI.'
echo 'Zrestartuj Enigma2 z pilota, potem EPGImport -> Zrodla.'
echo 'Wybierz Standard LUB Rozszerzone PLUS i uruchom import.'
if [ -f "$TARGET/ovh.local.sources.xml" ]; then
    echo 'UWAGA: Widze starszy ovh.local.sources.xml. Odznacz jego testowe zrodla w EPGImport.'
fi
echo 'Program aktualizuje sie z GitHuba codziennie automatycznie.'
sleep 6
