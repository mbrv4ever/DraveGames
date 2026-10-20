============================================================
  DraveArrow  v0.1.4
  Een boogschutter-spel van Dravenlock Games
============================================================

Snel starten (Windows)
----------------------
  Dubbelklik op:  Start-DraveArrow.bat

  De eerste keer zet het spel zelf alles klaar: het zoekt uw
  Python (3.10 of nieuwer), maakt een eigen omgeving aan en
  installeert de benodigde pakketten (ook de stem). Daarna start
  het spel. U hoeft niets handmatig te installeren.

Een Windows-programma (.exe) maken
----------------------------------
  Dubbelklik op:  Maak-DraveArrow-EXE.bat

  Hiermee wordt een los bestand gemaakt:  dist\DraveArrow.exe
  De stem wordt meegebakken, dus de .exe is groot maar werkt
  overal zonder Python.

Iets kapot? Opnieuw beginnen
----------------------------
  Dubbelklik op:  herstel.bat
  Dit wist de omgeving; de volgende start zet alles opnieuw op.

Bediening
---------
  Alles is met de muis te klikken (grote knoppen). Met het
  toetsenbord kan ook: pijltjes om te kiezen, Enter om te
  bevestigen, Esc om terug te gaan of te pauzeren.

  Tijdens het schieten:
    Muis bewegen        : richten
    Muisknop vasthouden : boog spannen; loslaten = schieten
    Pijl omhoog/omlaag  : hoek bijstellen (toetsenbord)
    Spatie vasthouden   : spannen; loslaten = schieten
    Esc of P            : pauze (er is ook een Pauze-knop)

  Hoe langer u spant, hoe meer kracht (zie de krachtmeter). De
  stippellijn toont de baan die de pijl ongeveer zal volgen -
  handig om te mikken. In latere rondes komt er wind bij.

Drie modi
---------
  - Schietbaan : raak alle schijven. De roos (goud) geeft de
                 meeste punten, de buitenrand het minst. Sommige
                 schijven bewegen; u heeft een beperkt aantal pijlen.
  - Precisie   : kleine doelen, weinig pijlen en veel wind. Voor
                 de scherpschutter.
  - Verdediging: vijanden (goblins, skeletten, vleermuizen) komen
                 op u af. Schiet ze neer voor ze u bereiken. Bij
                 een treffer verliest u leven. In de laatste golf
                 verschijnt een draak als eindbaas.

  Elke ronde/golf wordt zwaarder. Haalt u de laatste, dan wint u.

Intro met stem (splashvenster)
------------------------------
  Bij het opstarten verschijnt het drakenlogo en spreekt de
  stem de titel en "Gemaakt door Dravenlock Games" uit. Dit is een
  apart splashvenster; daarna opent het spel zelf. Standaard wordt een
  mannenstem (code "M1") gebruikt; wilt u een andere stem, dan staan de
  beschikbare codes na de eerste start in de map "DraveArrow-data"
  (naast het programma) in dravearrow-stemmen.txt; u kunt "voice_name"
  in DraveArrow-data\config.json aanpassen. De stem kunt u in Instellingen aan- of
  uitzetten. Het stem-model wordt de eerste keer automatisch
  gedownload.

Donatieknop
-----------
  Rechtsboven in de menu's staat een hartje-knop (Donatie). Die
  opent https://paypal.me/roger076 in uw browser.

Toegankelijkheid
----------------
  Grote, contrastrijke knoppen en tekst; volledige muis- en
  toetsenbordbediening; en de stippellijn voor de pijlbaan. De
  baanlijn kunt u in Instellingen aan- of uitzetten.

Draagbaar (portable) - waar staan mijn gegevens?
-------------------------------------------------
  Het spel bewaart NIETS in Windows-systeemmappen. Alles komt in
  een map "DraveArrow-data" NAAST het programma (de .exe of de
  map van het spel): uw instellingen en voortgang (config.json),
  de lijst stemcodes (dravearrow-stemmen.txt) en, mocht het ooit
  misgaan, het foutenlog (dravearrow-fout.txt). Zo blijft uw
  C-schijf schoon en kunt u het spel met map en al verplaatsen of
  op een USB-stick zetten.

  Opnieuw beginnen met een schone lei? Verwijder de map
  "DraveArrow-data"; de volgende start zet alles weer standaard.

Taal en geluid
--------------
  Het spel kiest automatisch uw systeemtaal (Nederlands of
  Engels). In Instellingen past u taal, geluid, muziek, stem,
  baanlijn en volume aan. Muziek en geluiden zijn volledig
  procedureel.

Donatie
-------
  DraveArrow is gratis. Vindt u het leuk? Een donatie wordt zeer
  gewaardeerd:  https://paypal.me/roger076
  Vragen of ideeen:  service@dravenlock.nl

Veel plezier en raak die roos!
