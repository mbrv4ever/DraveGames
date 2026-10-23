============================================================
  DraveBeat  v0.1.0
  Een ritmespel van Dravenlock Games
============================================================

Snel starten (Windows)
----------------------
  Dubbelklik op:  Start-DraveBeat.bat

  De eerste keer zet het spel zelf alles klaar: het zoekt uw
  Python (3.10 of nieuwer), maakt een eigen omgeving aan en
  installeert de benodigde pakketten (ook de stem). Daarna start
  het spel. U hoeft niets handmatig te installeren.

Een Windows-programma (.exe) maken
----------------------------------
  Dubbelklik op:  Maak-DraveBeat-EXE.bat

  Hiermee wordt een los bestand gemaakt:  dist\DraveBeat.exe
  De stem wordt meegebakken, dus de .exe is groot maar werkt
  overal zonder Python.

Iets kapot? Opnieuw beginnen
----------------------------
  Dubbelklik op:  herstel.bat
  Dit wist de omgeving; de volgende start zet alles opnieuw op.

Doel van het spel
-----------------
  Noten vallen in vier banen naar de trefbalk onderaan. Raak elke
  noot precies op het moment dat hij de balk kruist. Hoe strakker
  uw timing, hoe meer punten: Perfect, Goed of Mis. Bouw een combo
  op en haal een zo hoog mogelijke accuratesse en rang (S is de
  hoogste). De muziek is volledig procedureel en de noten lopen
  mee op de maat.

Bediening
---------
    D, F, J, K   : de vier banen (van links naar rechts)
    of klik      : klik op een baan om die te raken
    Esc of P     : pauze
  Vlak voor de start telt het spel af: 3, 2, 1, go!

De nummers
----------
  Er zijn drie nummers, oplopend in tempo en drukte:
    Rustig (100 bpm) - rustige start, mooi om te oefenen
    Stevig (124 bpm) - steviger tempo, meer noten
    Snel   (140 bpm) - snel en druk, voor de geoefende speler
  Elk nummer heeft een eigen highscore. De noten van een nummer
  liggen vast, zodat u het kunt oefenen en uw score verbeteren.

Intro met stem (splashvenster)
------------------------------
  Bij het opstarten verschijnt het drakenlogo en spreekt de stem
  de titel en "Gemaakt door Dravenlock Games" uit. Dit is een apart
  splashvenster; daarna opent het spel. Standaard een mannenstem
  (code "M1"); andere codes staan na de eerste start in de map
  "DraveBeat-data" in dravebeat-stemmen.txt en u kunt "voice_name"
  in DraveBeat-data\config.json aanpassen. De stem kunt u in
  Instellingen aan- of uitzetten. Het stem-model wordt de eerste
  keer automatisch gedownload.

Donatieknop
-----------
  Rechtsboven in de menu's staat een hartje-knop (Donatie). Die
  opent https://paypal.me/roger076 in uw browser.

Draagbaar (portable) - waar staan mijn gegevens?
-------------------------------------------------
  Het spel bewaart NIETS in Windows-systeemmappen. Alles komt in
  een map "DraveBeat-data" NAAST het programma: uw instellingen en
  highscores (config.json), de lijst stemcodes
  (dravebeat-stemmen.txt) en, mocht het ooit misgaan, het
  foutenlog (dravebeat-fout.txt). Zo blijft uw C-schijf schoon en
  kunt u het spel met map en al verplaatsen of op een USB-stick
  zetten.

  Opnieuw beginnen met een schone lei? Verwijder de map
  "DraveBeat-data"; de volgende start zet alles weer standaard.

Taal en geluid
--------------
  Het spel kiest automatisch uw systeemtaal (Nederlands of Engels).
  In Instellingen past u taal, geluid, muziek, stem en volume aan.
  Muziek en geluiden zijn volledig procedureel.

Donatie
-------
  DraveBeat is gratis. Vindt u het leuk? Een donatie wordt zeer
  gewaardeerd:  https://paypal.me/roger076
  Vragen of ideeen:  service@dravenlock.nl

Veel plezier en blijf op de maat!
