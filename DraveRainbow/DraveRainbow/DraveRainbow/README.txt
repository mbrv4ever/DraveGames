============================================================
  DraveRainbow  v0.1.0
  Een Rainbow-Islands-spel van Dravenlock Games
============================================================

Snel starten (Windows)
----------------------
  Dubbelklik op:  Start-DraveRainbow.bat

  De eerste keer zet het spel zelf alles klaar: het zoekt uw
  Python (3.10 of nieuwer), maakt een eigen omgeving aan en
  installeert de benodigde pakketten (ook de stem). Daarna start
  het spel. U hoeft niets handmatig te installeren.

Een Windows-programma (.exe) maken
----------------------------------
  Dubbelklik op:  Maak-DraveRainbow-EXE.bat

  Hiermee wordt een los bestand gemaakt:  dist\DraveRainbow.exe
  De stem wordt meegebakken, dus de .exe is groot maar werkt
  overal zonder Python.

Iets kapot? Opnieuw beginnen
----------------------------
  Dubbelklik op:  herstel.bat
  Dit wist de omgeving; de volgende start zet alles opnieuw op.

Doel van het spel
-----------------
  Klim van eiland naar eiland naar de top - maar onderin komt het
  water omhoog en jaagt u op. Uw geheime wapen: u maakt
  REGENBOGEN. Een regenboog is een boog waar u op staat en
  overheen klimt om hoger te komen, en die vijanden verslaat als
  u hem op ze maakt (ze laten dan fruit vallen voor punten). Bereik
  de vlag bovenaan voor het water u inhaalt!

Bediening
---------
    Pijl links / rechts : lopen
    Pijl omhoog of W    : springen (ingedrukt = hoger)
    Spatie              : maak een regenboog voor u
    Esc of P            : pauze

  Maak een regenboog, spring erop, klim naar de top ervan en maak
  vandaar de volgende - zo klimt u steeds hoger. Een regenboog
  verdwijnt na enkele seconden, dus blijf in beweging.

Punten en levens
----------------
  U krijgt punten voor verslagen vijanden, verzamelde diamanten en
  fruit, en voor het halen van een eiland. U begint met 3 levens;
  u verliest er een als een vijand u raakt of het water u inhaalt.
  Daarna gaat het water iets terug en begint u net onder uw laatste
  veilige plek. Uw hoogste score wordt bewaard. Er zijn 5 eilanden.

Intro met stem (splashvenster)
------------------------------
  Bij het opstarten verschijnt het drakenlogo en spreekt de stem
  de titel en "Gemaakt door Dravenlock Games" uit. Dit is een apart
  splashvenster; daarna opent het spel. Standaard een mannenstem
  (code "M1"); andere codes staan na de eerste start in de map
  "DraveRainbow-data" in draverainbow-stemmen.txt en u kunt
  "voice_name" in DraveRainbow-data\config.json aanpassen. De stem
  kunt u in Instellingen aan- of uitzetten. Het stem-model wordt de
  eerste keer automatisch gedownload.

Donatieknop
-----------
  Rechtsboven in de menu's staat een hartje-knop (Donatie). Die
  opent https://paypal.me/roger076 in uw browser.

Draagbaar (portable) - waar staan mijn gegevens?
-------------------------------------------------
  Het spel bewaart NIETS in Windows-systeemmappen. Alles komt in
  een map "DraveRainbow-data" NAAST het programma: uw instellingen
  en highscore (config.json), de lijst stemcodes
  (draverainbow-stemmen.txt) en, mocht het misgaan, het foutenlog
  (draverainbow-fout.txt). Zo blijft uw C-schijf schoon en kunt u
  het spel met map en al verplaatsen of op een USB-stick zetten.

  Opnieuw beginnen met een schone lei? Verwijder de map
  "DraveRainbow-data"; de volgende start zet alles weer standaard.

Taal en geluid
--------------
  Het spel kiest automatisch uw systeemtaal (Nederlands of Engels).
  In Instellingen past u taal, geluid, muziek, stem en volume aan.
  Muziek en geluiden zijn volledig procedureel.

Donatie
-------
  DraveRainbow is gratis. Vindt u het leuk? Een donatie wordt zeer
  gewaardeerd:  https://paypal.me/roger076
  Vragen of ideeen:  service@dravenlock.nl

Veel plezier en klim naar de top!
