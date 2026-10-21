============================================================
  DraveRace  v0.2.7
  Een retro racer van Dravenlock Games
============================================================

Snel starten (Windows)
----------------------
  Dubbelklik op:  Start-DraveRace.bat

  De eerste keer zet het spel zelf alles klaar: het zoekt uw
  Python (3.10 of nieuwer), maakt een eigen omgeving aan en
  installeert de benodigde pakketten (ook de stem). Daarna start
  het spel. U hoeft niets handmatig te installeren.

Een Windows-programma (.exe) maken
----------------------------------
  Dubbelklik op:  Maak-DraveRace-EXE.bat

  Hiermee wordt een los bestand gemaakt:  dist\DraveRace.exe
  De stem (mofasa) wordt meegebakken, dus de .exe is groot maar
  werkt overal zonder Python.

Iets kapot? Opnieuw beginnen
----------------------------
  Dubbelklik op:  herstel.bat
  Dit wist de omgeving; de volgende start zet alles opnieuw op.

Bediening
---------
  Alles is met de muis te klikken (grote knoppen). Met het
  toetsenbord kan ook: pijltjes om te kiezen, Enter om te
  bevestigen, Esc om terug te gaan of te pauzeren.

  In de race:
    Pijl links / rechts : sturen
    Pijl omhoog         : gas geven
    Pijl omlaag         : remmen
    Spatie              : nitro (turbo)
    Esc of P            : pauze (er is ook een Pauze-knop)

Intro met stem (splashvenster)
------------------------------
  Bij het opstarten verschijnt het drakenlogo en spreekt de
  stem de titel en "Gemaakt door Dravenlock Games" uit. Dit is een
  apart splashvenster; daarna opent het spel zelf. Standaard wordt een
  mannenstem (code "M1") gebruikt; wilt u een andere stem, dan staan de
  beschikbare codes na de eerste start in de map "DraveRace-data"
  (naast het programma) in draverace-stemmen.txt; u kunt "voice_name"
  in DraveRace-data\config.json aanpassen. De stem kunt u in
  Instellingen aan- of uitzetten. Het stem-model wordt de eerste
  keer automatisch gedownload.

Donatieknop
----------
  Rechtsboven in de menu's staat een hartje-knop (Donatie). Die
  opent https://paypal.me/roger076 in uw browser.

Twee camera's
-------------
  - Achter de auto : pseudo-3D, de weg buigt voor u uit.
  - Bovenaanzicht  : van bovenaf; de auto draait mee met de
                     bocht en de weg schuift onder u door.
  U kiest de camera in het modusscherm.

Twee race-soorten
-----------------
  - Ronde-race   : rijd alle rondjes en eindig vooraan.
  - Achtervolging: haal de rivaal in voordat de tijd op is.
  Elke ronde wordt zwaarder: snellere tegenstanders en meer
  obstakels (pylonen, olie, rotsen, vangrails).

Auto's
------
  Vier auto's met eigen eigenschappen (topsnelheid, acceleratie,
  grip). Kies in het auto-scherm met de pijl-knoppen.

Draagbaar (portable) - waar staan mijn gegevens?
-------------------------------------------------
  Het spel bewaart NIETS in Windows-systeemmappen. Alles komt in
  een map "DraveRace-data" NAAST het programma: uw instellingen en
  voortgang (config.json), de lijst stemcodes (draverace-stemmen.txt)
  en, mocht het ooit misgaan, het foutenlog (draverace-fout.txt). Zo
  blijft uw C-schijf schoon en kunt u het spel met map en al
  verplaatsen of op een USB-stick zetten.

  Opnieuw beginnen met een schone lei? Verwijder de map
  "DraveRace-data"; de volgende start zet alles weer standaard.

Taal en geluid
--------------
  Het spel kiest automatisch uw systeemtaal (Nederlands of
  Engels). In Instellingen past u taal, geluid, muziek, stem en
  volume aan. Muziek en geluiden zijn volledig procedureel.

Donatie
-------
  DraveRace is gratis. Vindt u het leuk? Een donatie wordt zeer
  gewaardeerd:  https://paypal.me/roger076
  Vragen of ideeen:  service@dravenlock.nl

Veel plezier en houd uw banden op de weg!
