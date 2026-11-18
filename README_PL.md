# EPG.OVH Polska dla EPGImport (OpenPLi / OpenATV / Enigma2)

Zrodlo danych XMLTV: **EPG.OVH** (https://epg.ovh). Ten projekt udostepnia dwa pliki EPG z GitHub Releases i osobne mapowanie referencji DVB polskich kanalow z Hot Birda 13.0E. Autorzy danych XMLTV: EPG.OVH. Warto wesprzec serwis: https://epg.ovh/

## Jakie pliki sa dostepne

Po pierwszym udanym przebiegu Actions: https://github.com/tvmadprodev/epg-ovh/releases/tag/epg-ovh

- `pl.gz`: EPG standard (5 dni)
- `pltv.gz`: EPG+ (kategorie, rok produkcji itd., o ile dane sa obecne w XMLTV)
- `ovh.channels.xml`: **stale** mapowanie polskich DVB referencji do rzeczywistych identyfikatorow EPG.OVH
- `ovh.sources.xml`: dwa zrodla EPGImport (z mechanizmem `<mappings>` jak Rytec)
- `install_epg_ovh.sh`: instalator dla odbiornika, przez DreamExplorer lub shell
- `SHA256SUMS.txt`: sumy kontrolne publikowanych plikow

**Dwa zrodla do wyboru:** najlepiej zaznaczyc jedno (Standard LUB PLUS). Przy zaznaczeniu obu zdarzenia sie pokrywaja, a EPGImport nie gwarantuje scalania metadanych. Enigma2 moze nie wyswietlac wszystkich dodatkowych pol XMLTV w standardowej skorce.

## Dla wlasciciela repozytorium: pierwsza publikacja

Zgraj pliki z paczki do repozytorium `tvmadprodev/epg-ovh`, zachowujac strukture katalogow. Zastap istniejacy `.github/workflows/epg-ovh.yml` jego nowsza wersja z tej paczki. **Nie kasuj README z GitHuba, jesli chcesz go zachowac; mozesz zastapic nim ten plik.**

Najlatwiej na Linux Mint przez terminal (`git` musi byc zainstalowany):

```sh
git clone https://github.com/tvmadprodev/epg-ovh.git
cp -a /SCIEZKA/DO/ROZPAKOWANEGO_PAKIETU/. epg-ovh/
cd epg-ovh
git add .
git commit -m 'EPG OVH: mapowanie polskich DVB, EPG+ i instalator'
git push origin main
```

Powyzej `/SCIEZKA/DO/ROZPAKOWANEGO_PAKIETU` to folder z `.github/`, `data/`, `scripts/` itd. Zalogowanie Git do GitHuba przy `git push` moze wymagac Git Credential Manager lub tokenu (GitHub nie przyjmuje hasla do konta w konsoli).

Alternatywnie wszystkie pliki mozna wgrywac przez interfejs WWW GitHuba, zachowujac sciezki.

1. Wejdz w GitHub > Actions > workflow `EPG OVH Polska - Standard, Plus i mapowanie Enigma2`.
2. Kliknij **Run workflow**, ustaw `rebuild_mapping=false` (na pierwszy raz nie ma jeszcze mapy i skrypt utworzy ja automatycznie).
3. Gdy wynik bedzie **zielony**, wejdz w Releases i sprawdz opublikowane pliki (w tym EPG, mapowanie i aktualny instalator IPK). W repo powstana `mappings/ovh.channels.xml` i `reports/mapowanie.tsv`.
4. **Sprawdz raport**, zwlaszcza TVN24, Eleven, Cartoon Network i wiersze `brak` lub `niejednoznaczne`. Nieopublikowane/mapowane automatycznie bez pewnosci pozycje celowo pozostaja bez EPG.
5. Codzienna aktualizacja `pl.gz` i `pltv.gz` jest zaplanowana na 03:17 UTC. Mapowanie nie jest automatycznie przebudowywane po pierwszym wygenerowaniu.

**Uwaga:** jezeli GitHub Actions nie moze pobrac `pltv.gz` z EPG.OVH albo zdalne repo ma blokade push z GitHub Actions, wykonanie nie bedzie zielone. Wtedy potrzebna jest analiza logu, nie publikuj niezweryfikowanego mapowania.

## Uniwersalna instalacja na dekoderze

1. Pobierz `install_epg_ovh.sh` i umiesc go w `/tmp/` przez FTP.
2. W DreamExplorer wybierz plik `.sh` i uzyj opcji wykonania skryptu (nazwa opcji zalezy od wersji DreamExplorer). Jesli przegladarka plikow nie wykonuje skryptow, uzyj SSH: `sh /tmp/install_epg_ovh.sh`.
3. Skrypt pobierze *aktualne* `ovh.sources.xml` i `ovh.channels.xml` z GitHub Releases, sprawdzi XML i zrobi kopie istniejacych plikow.
4. Skrypt **nie restartuje** Enigma2, nie usuwa `epg.dat`, nie zmienia bukietow i nie instaluje dodatkowych wtyczek.
5. Zrob restart GUI Enigma2 z pilota. Otworz EPGImport -> Zrodla, wybierz jedno z dwoch zrodel, zapisz i uruchom pierwszy reczny import.
6. W EPGImport wlacz automatyczny import, np. o 07:00 czasu lokalnego.

Przegladarki plikow roznia sie sposobem uruchamiania `.sh`. W niektorych potrzebne jest uprawnienie wykonywania: `chmod 755 /tmp/install_epg_ovh.sh`. Archiwum ZIP zapisuje dla tego skryptu tryb 0755, ale nie kazdy klient FTP go zachowuje.

## Jak mapowanie powstaje, i czego NIE robi

- Baza `data/polish_services.tsv` zostala jednorazowo zebrana z `lamedb5`, `userbouquet.polskie.tv`, `userbouquet.polskieFTA.tv` (13E) udostepnionych przez opiekuna projektu.
- Jest w niej **212 referencji** polskich uslug DVB z tych dwoch bukietow. Wstepnie usunieto techniczne VOD 205-208 i kanaliki Test180*.
- Nie pobiera `lamedb` ani list u koncowego odbiorcy. Kazdy dekoder z takimi samymi referencjami 13E moze uzyc mapowania.
- Dla obcych wersji Cartoon Network, Nickelodeon itp. nie istnieja wpisy w mapowaniu, poniewaz nie sa na zaufanej liscie polskich DVB ref.
- `scripts/build_mapping.py` porownuje **prawdziwe identyfikatory** XMLTV z obu feedow; pomija przypadki niepewne. Rejestruje pelny raport. Nie robi fuzzy/Levenshtein.
- Referencje sa **specyficzne dla DVB**; dla DVB-T2, DVB-C, IPTV i alternatywnych list ze zmienionymi service references beda potrzebne dodatkowe, zweryfikowane wpisy.
- Nie ma gwarancji, ze kazda z 212 pozycji znajduje sie w aktualnym XMLTV. Liczba **rzeczywiscie przypisanych** znajduje sie w raporcie po pierwszym Actions run.

## Reczne poprawki w przyszlosci (bez regeneracji na odbiornikach)

Najbezpieczniej poprawic `mappings/ovh.channels.xml` na GitHubie i commitowac. Po kolejnej aktualizacji Actions spakuje go i udostepni na stalym adresie.

Mozna tez zmienic `data/polish_services.tsv` i/lub `data/manual_ids.json` z dokladnym `<channel id>` z EPG.OVH, a potem uruchomic Actions recznie z `rebuild_mapping=true`. Zrobi to **jednorazowy przebudowujacy commit**, bez uruchamiania generatora u odbiorcow.

Nie zaleca sie codziennej automatycznej przebudowy mapowania wedlug nazw, bo identyfikatory/aliasy XMLTV moga byc niejednoznaczne.

## Kwestie techniczne i prawne

Mapowanie obejmuje tylko polskie DVB ref 13E, a nie wszystkie satelity ani wszystkie mozliwe listy. Nie gwarantujemy, ze puste EPG oznacza blad w dekoderze: czasem danego kanalu nie ma w pliku XMLTV. Dane i logotypy EPG.OVH naleza do ich autorow; upewnij sie, ze zasady redystrybucji pozwalaja na publikowanie kopii XMLTV w GitHub Releases. Samo darmowe korzystanie z EPG nie zawsze oznacza licencje na dalsza redystrybucje.


## Mapowanie XML (od 1.0-r2)

Nowe zrodla i instalator pobieraja mapowanie `ovh.channels.xml` bez kompresji. `pl.gz` i `pltv.gz` nadal sa kompresowane. W EPGImport zaznacz Standard lub PLUS, zapisz i uruchom import reczny. Gdy import wynosi 0, sprawdz log EPGImport (INFO).

## Aktualizacja mapowania 1.0-r3 (18.11.2026)

Oprocz 212 bazowych referencji polskich stacji z Hot Birda 13E dodano **148 innych, zweryfikowanych referencji DVB** w `data/verified_variants.tsv`. Zostaly sprawdzone na podstawie `lamedb5` z aktualnej listy kanalow: identyczna nazwa i operator, nie na podstawie zgadywania nazwy przez uzytkownika. Dotyczy to m.in. dodatkowych CANAL+ Sport 3/4, Extra 2/3 oraz CANAL+ 1 w roznych bukietach.

Jawnie zatwierdzone ID XMLTV (`data/manual_ids.json`):
- `Historia Poland` → `Discovery Historia`
- `ID Poland HD` → `ID`
- `Turbo Xtra Poland HD / DTX HD` → `DTX`
- `Mezzo TV` → `Mezzo`
- `Paramount Network Polska` → `Paramount Channel`

Dla Mango brak zweryfikowanego odpowiednika w EPG.OVH. Nie przypisujemy mu obcego programu.

Uwaga techniczna: jedna z dawnych referencji `Wydarzenia 24` w analizowanym `lamedb5` wystepuje pod nowa nazwa `Polsat News Polityka HD` — nie rozszerzamy jej automatycznie bez oddzielnej weryfikacji.

Codzienna aktualizacja odswieza tylko dane `pl.gz` i `pltv.gz`; mapa jest zachowywana bez automatycznego dopasowywania zagranicznych stacji. Do odbiornikow OpenPLi/OpenATV przeznaczony jest IPK **epg-ovh-pl-installer_1.0-r3_all.ipk**. Po instalacji zrestartuj GUI Enigma2, w EPGImport wybierz jedno zrodlo i wykonaj import reczny.


## Czytelne EPG PLUS (18.11.2026)

Od tej aktualizacji tylko `pltv.gz` jest dodatkowo formatowany na GitHub Actions z mysla o Enigma2. Oryginalny `pl.gz` (Standard) i `ovh.channels.xml` (mapowanie) nie sa zmieniane.

- Zamiast `G: komedia. R: 2025. W: 12. O: 6/10` w opisie pojawia sie `Komedia • 2025 • Wiek: od 12 lat • Ocena: 6/10`.
- Odcinki `E252` i `S1E5/6` sa pokazywane czytelnie jako `Odcinek 252` lub `Sezon 1, odcinek 5/6`.
- Odpowiednie znane gatunki maja dodatkowo kod DVB (np. `Comedy`, `Documentary`, `News`) rozpoznawany przez EPGImport.
- Ograniczenia wiekowe z pola `W:` sa dodawane jako prawidlowe `<rating><value>12+</value></rating>`, zeby Enigma2 mogla wyswietlac wiek w osobnym polu.
- Surowe, niezmienione EPG rozszerzone pozostaje w Releases jako `pltv.source.gz` (kopia do ewentualnego rollbacku).

Przed opublikowaniem formatter jest testowany na aktualnym, kompletnym pliku EPG.OVH; sprawdza takze zgodnosc wszystkich kanalow, tytulow i godzin. Gdy test sie nie powiedzie, workflow nie nadpisuje poprzedniej dobrej kopii EPG.

**Nie jest wymagany nowy IPK**, bo adresy `pl.gz`, `pltv.gz`, `ovh.sources.xml` i `ovh.channels.xml` pozostaja takie same. Na dekoderze wystarczy wybrac tylko PLUS, wyczyscic dotychczasowe dane EPG na czas testu i uruchomic nowy import. Zielony tekst i jego polozenie zalezy od skina i tego, czy odbiornik interpretuje gatunek/oceny DVB.
