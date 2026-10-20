============================================================
  DraveDragon  v0.2.0
  Een vlieggame van Dravenlock Games
============================================================

Snel starten (Windows)
----------------------
  Dubbelklik op:  Start-DraveDragon.bat

  De eerste keer zet het spel zelf alles klaar: het zoekt uw
  Python (3.10 of nieuwer), maakt een eigen omgeving aan en
  installeert de benodigde pakketten (ook de stem). Daarna start
  het spel. U hoeft niets handmatig te installeren.

Een Windows-programma (.exe) maken
----------------------------------
  Dubbelklik op:  Maak-DraveDragon-EXE.bat

  Hiermee wordt een los bestand gemaakt:  dist\DraveDragon.exe
  De stem wordt meegebakken, dus de .exe is groot maar werkt
  overal zonder Python.

Iets kapot? Opnieuw beginnen
----------------------------
  Dubbelklik op:  herstel.bat
  Dit wist de omgeving; de volgende start zet alles opnieuw op.

Bediening
---------
  EEN knop! Tik om te klimmen:
    Spatie / muisknop / pijl omhoog : klimmen (tik herhaaldelijk)
    Laat los                        : dalen
    Esc of P                        : pauze (er is ook een Pauze-knop)

  Doel: vlieg met de draak door de openingen tussen de stenen
  pilaren. Raak je een pilaar, het plafond of de grond, dan stort
  je neer. Elke gehaalde opening is een punt; edelstenen geven 5
  punten extra. De snelheid loopt langzaam op.

Drie moeilijkheidsgraden
------------------------
  Na "Spelen" kiest u een stand (met een eigen highscore per stand):
    Makkelijk - ruime openingen, rustig tempo. Ontspannen vliegen.
    Moeilijk  - gemiddelde openingen; de snelheid loopt geleidelijk op.
    Zwaar     - krappe openingen, hoog tempo. Voor de durfal.

Intro met stem (splashvenster)
------------------------------
  Bij het opstarten verschijnt het drakenlogo en spreekt de stem
  de titel en "Gemaakt door Dravenlock Games" uit. Dit is een apart
  splashvenster; daarna opent het spel. Standaard een mannenstem
  (code "M1"); andere codes staan na de eerste start in de map
  "DraveDragon-data" in dravedragon-stemmen.txt en u kunt
  "voice_name" in DraveDragon-data\config.json aanpassen. De stem
  kunt u in Instellingen aan- of uitzetten. Het stem-model wordt de
  eerste keer automatisch gedownload.

Donatieknop
-----------
  Rechtsboven in de menu's staat een hartje-knop (Donatie). Die
  opent https://paypal.me/roger076 in uw browser.

Draagbaar (portable) - waar staan mijn gegevens?
-------------------------------------------------
  Het spel bewaart NIETS in Windows-systeemmappen. Alles komt in
  een map "DraveDragon-data" NAAST het programma: uw instellingen
  en highscore (config.json), de lijst stemcodes
  (dravedragon-stemmen.txt) en, mocht het ooit misgaan, het
  foutenlog (dravedragon-fout.txt). Zo blijft uw C-schijf schoon en
  kunt u het spel met map en al verplaatsen of op een USB-stick
  zetten.

  Opnieuw beginnen met een schone lei? Verwijder de map
  "DraveDragon-data"; de volgende start zet alles weer standaard.

Taal en geluid
--------------
  Het spel kiest automatisch uw systeemtaal (Nederlands of Engels).
  In Instellingen past u taal, geluid, muziek, stem, rustige stand
  en volume aan. Muziek en geluiden zijn volledig procedureel.

Donatie
-------
  DraveDragon is gratis. Vindt u het leuk? Een donatie wordt zeer
  gewaardeerd:  https://paypal.me/roger076
  Vragen of ideeen:  service@dravenlock.nl

Veel plezier en blijf in de lucht!
