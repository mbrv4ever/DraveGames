============================================================
  DraveTris  v0.1.0
  Een Tetris-spel van Dravenlock Games
============================================================

Snel starten (Windows)
----------------------
  Dubbelklik op:  Start-DraveTris.bat

  De eerste keer zet het spel zelf alles klaar: het zoekt uw
  Python (3.10 of nieuwer), maakt een eigen omgeving aan en
  installeert de benodigde pakketten (ook de stem). Daarna start
  het spel. U hoeft niets handmatig te installeren.

Een Windows-programma (.exe) maken
----------------------------------
  Dubbelklik op:  Maak-DraveTris-EXE.bat

  Hiermee wordt een los bestand gemaakt:  dist\DraveTris.exe
  De stem wordt meegebakken, dus de .exe is groot maar werkt
  overal zonder Python.

Iets kapot? Opnieuw beginnen
----------------------------
  Dubbelklik op:  herstel.bat
  Dit wist de omgeving; de volgende start zet alles opnieuw op.

Doel van het spel
-----------------
  De zeven bekende stukken vallen in de put. Schuif en draai ze
  zo dat u volledige horizontale rijen maakt; een volle rij
  verdwijnt en levert punten op. Vier rijen in een keer is een
  'Tetris' (de meeste punten). Hoe hoger uw level, hoe sneller de
  stukken vallen. De put vol = game over.

Bediening
---------
    Pijl links / rechts : schuiven
    Pijl omhoog of X    : draaien (met de klok mee)
    Z of Ctrl           : draaien (tegen de klok in)
    Pijl omlaag         : zacht zakken (sneller)
    Spatie              : hard laten vallen (meteen vast)
    C of Shift          : stuk vasthouden voor later (een keer per stuk)
    Esc of P            : pauze

  Het doorzichtige 'schaduw-stuk' onderin laat zien waar het
  huidige stuk landt. Rechts ziet u de volgende stukken; links
  het vastgehouden stuk. (Het schaduw-stuk kunt u in Instellingen
  uitzetten.)

Punten en levels
----------------
  1 rij = 100, 2 rijen = 300, 3 rijen = 500, 4 rijen (Tetris) =
  800, maal uw level. Zacht/hard laten vallen geeft kleine bonus.
  Elke 10 rijen gaat u een level omhoog en valt alles sneller. Uw
  hoogste score (highscore) wordt bewaard.

Intro met stem (splashvenster)
------------------------------
  Bij het opstarten verschijnt het drakenlogo en spreekt de stem
  de titel en "Gemaakt door Dravenlock Games" uit. Dit is een apart
  splashvenster; daarna opent het spel. Standaard een mannenstem
  (code "M1"); andere codes staan na de eerste start in de map
  "DraveTris-data" in dravetris-stemmen.txt en u kunt "voice_name"
  in DraveTris-data\config.json aanpassen. De stem kunt u in
  Instellingen aan- of uitzetten. Het stem-model wordt de eerste
  keer automatisch gedownload.

Donatieknop
-----------
  Rechtsboven in de menu's staat een hartje-knop (Donatie). Die
  opent https://paypal.me/roger076 in uw browser.

Draagbaar (portable) - waar staan mijn gegevens?
-------------------------------------------------
  Het spel bewaart NIETS in Windows-systeemmappen. Alles komt in
  een map "DraveTris-data" NAAST het programma: uw instellingen en
  highscore (config.json), de lijst stemcodes
  (dravetris-stemmen.txt) en, mocht het ooit misgaan, het
  foutenlog (dravetris-fout.txt). Zo blijft uw C-schijf schoon en
  kunt u het spel met map en al verplaatsen of op een USB-stick
  zetten.

  Opnieuw beginnen met een schone lei? Verwijder de map
  "DraveTris-data"; de volgende start zet alles weer standaard.

Taal en geluid
--------------
  Het spel kiest automatisch uw systeemtaal (Nederlands of Engels).
  In Instellingen past u taal, geluid, muziek, stem, schaduw-stuk
  en volume aan. Muziek en geluiden zijn volledig procedureel.

Donatie
-------
  DraveTris is gratis. Vindt u het leuk? Een donatie wordt zeer
  gewaardeerd:  https://paypal.me/roger076
  Vragen of ideeen:  service@dravenlock.nl

Veel plezier en stapel ze netjes!
