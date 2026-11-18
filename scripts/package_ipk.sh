#!/bin/sh
# Builds a portable opkg Debian-ar IPK for the EPG.OVH installer.
set -eu
NAME='epg-ovh-pl-installer_1.0-r2_all.ipk'
ROOT=$(pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT HUP INT TERM
mkdir -p "$WORK/control" "$WORK/data/usr/share/epg-ovh"
cp "$ROOT/install_epg_ovh.sh" "$WORK/data/usr/share/epg-ovh/install_epg_ovh.sh"
chmod 755 "$WORK/data/usr/share/epg-ovh/install_epg_ovh.sh"
cat > "$WORK/control/control" <<'CTL'
Package: epg-ovh-pl-installer
Version: 1.0-r2
Architecture: all
Maintainer: tvmadprodev
Section: misc
Priority: optional
Description: EPG OVH Polska - Standard i Rozszerzone PLUS dla EPGImport
 Instaluje dwa zrodla i nieskompresowane mapowanie XML z GitHub.
Homepage: https://github.com/tvmadprodev/epg-ovh
CTL
cat > "$WORK/control/postinst" <<'POST'
#!/bin/sh
set -e
printf '\n[EPG OVH PL] Instalacja zrodel i mapowania XML...\n'
sh /usr/share/epg-ovh/install_epg_ovh.sh
printf '\n[EPG OVH PL] GOTOWE. Zrestartuj GUI Enigma2.\n'
exit 0
POST
chmod 755 "$WORK/control/postinst"
(cd "$WORK/control" && tar -czf "$WORK/control.tar.gz" ./control ./postinst)
(cd "$WORK/data" && tar -czf "$WORK/data.tar.gz" ./usr/share/epg-ovh/install_epg_ovh.sh)
printf '2.0\n' > "$WORK/debian-binary"
rm -f "$ROOT/$NAME"
(cd "$WORK" && ar q "$ROOT/$NAME" debian-binary control.tar.gz data.tar.gz)
ar t "$ROOT/$NAME"
echo "IPK ready: $ROOT/$NAME"
