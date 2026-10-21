============================================================
  DraveBricks  v0.1.0
  Een Breakout/Arkanoid van Dravenlock Games
============================================================

Snel starten (Windows)
----------------------
  Dubbelklik op:  Start-DraveBricks.bat

  De eerste keer zet het spel zelf alles klaar: het zoekt uw
  Python (3.10 of nieuwer), maakt een eigen omgeving aan en
  installeert de benodigde pakketten (ook de stem). Daarna start
  het spel. U hoeft niets handmatig te installeren.

Een Windows-programma (.exe) maken
----------------------------------
  Dubbelklik op:  Maak-DraveBricks-EXE.bat

  Hiermee wordt een los bestand gemaakt:  dist\DraveBricks.exe
  De stem wordt meegebakken, dus de .exe is groot maar werkt
  overal zonder Python.

Iets kapot? Opnieuw beginnen
----------------------------
  Dubbelklik op:  herstel.bat
  Dit wist de omgeving; de volgende start zet alles opnieuw op.

Doel van het spel
-----------------
  Kaats de bal met de peddel omhoog en sla alle stenen kapot.
  Sommige stenen zijn steviger (meerdere klappen); stenen met '#'
  zijn onverwoestbaar en blijven staan. Verlies de bal onderaan,
  dan raakt u een leven kwijt. Maak alle 8 levels leeg om te winnen.

Bediening
---------
    Muis of pijltjes links/rechts : peddel bewegen
    Spatie of klik                : bal lanceren / laser schieten
    Esc of P                      : pauze
  Alle menu's zijn ook met muis te klikken (grote knoppen).

Power-ups (vallen uit stenen, vang ze met de peddel)
----------------------------------------------------
  B  Breed  - bredere peddel (tijdelijk)
  3  Multi  - splitst in drie ballen
  T  Traag  - langzamere bal (tijdelijk)
  P  Plak   - bal blijft op de peddel plakken; los met spatie/klik
  L  Laser  - de peddel kan schieten (spatie/klik)
  V  Vuur   - de bal gaat dwars door stenen heen (tijdelijk)
  +  Leven  - een extra leven

Intro met stem (splashvenster)
------------------------------
  Bij het opstarten verschijnt het drakenlogo en spreekt de stem
  de titel en "Gemaakt door Dravenlock Games" uit. Dit is een apart
  splashvenster; daarna opent het spel. Standaard een mannenstem
  (code "M1"); andere codes staan na de eerste start in de map
  "DraveBricks-data" in dravebricks-stemmen.txt en u kunt
  "voice_name" in DraveBricks-data\config.json aanpassen. De stem
  kunt u in Instellingen aan- of uitzetten. Het stem-model wordt de
  eerste keer automatisch gedownload.

Donatieknop
-----------
  Rechtsboven in de menu's staat een hartje-knop (Donatie). Die
  opent https://paypal.me/roger076 in uw browser.

Draagbaar (portable) - waar staan mijn gegevens?
-------------------------------------------------
  Het spel bewaart NIETS in Windows-systeemmappen. Alles komt in
  een map "DraveBricks-data" NAAST het programma: uw instellingen
  en highscore (config.json), de lijst stemcodes
  (dravebricks-stemmen.txt) en, mocht het ooit misgaan, het
  foutenlog (dravebricks-fout.txt). Zo blijft uw C-schijf schoon en
  kunt u het spel met map en al verplaatsen of op een USB-stick
  zetten.

  Opnieuw beginnen met een schone lei? Verwijder de map
  "DraveBricks-data"; de volgende start zet alles weer standaard.

Taal en geluid
--------------
  Het spel kiest automatisch uw systeemtaal (Nederlands of Engels).
  In Instellingen past u taal, geluid, muziek, stem en volume aan.
  Muziek en geluiden zijn volledig procedureel.

Donatie
-------
  DraveBricks is gratis. Vindt u het leuk? Een donatie wordt zeer
  gewaardeerd:  https://paypal.me/roger076
  Vragen of ideeen:  service@dravenlock.nl

Veel plezier en sla die stenen kapot!
