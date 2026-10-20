============================================================
  DraveBoulder  v0.1.0
  Een Boulder Dash van Dravenlock Games
============================================================

Snel starten (Windows)
----------------------
  Dubbelklik op:  Start-DraveBoulder.bat

  De eerste keer zet het spel zelf alles klaar: het zoekt uw
  Python (3.10 of nieuwer), maakt een eigen omgeving aan en
  installeert de benodigde pakketten (ook de stem). Daarna start
  het spel. U hoeft niets handmatig te installeren.

Een Windows-programma (.exe) maken
----------------------------------
  Dubbelklik op:  Maak-DraveBoulder-EXE.bat

  Hiermee wordt een los bestand gemaakt:  dist\DraveBoulder.exe
  De stem wordt meegebakken, dus de .exe is groot maar werkt
  overal zonder Python.

Iets kapot? Opnieuw beginnen
----------------------------
  Dubbelklik op:  herstel.bat
  Dit wist de omgeving; de volgende start zet alles opnieuw op.

Doel van het spel
-----------------
  U bent Rockford. Graaf door de aarde, verzamel genoeg diamanten
  en bereik de uitgang voor de tijd om is. Maar pas op: rotsen (en
  diamanten) vallen zodra de grond eronder weg is. Sta niet onder
  een vallende rots! Rotsen rollen ook van ronde dingen af.

  Er zijn 16 grotten (A t/m P), elk in 5 moeilijkheidsniveaus -
  samen 80 levels. Hogere niveaus: meer diamanten nodig, minder
  tijd.

Bediening
---------
    Pijltjes      : graven en lopen (omhoog/omlaag/links/rechts)
    Shift (inged.) : graven/pakken/duwen ZONDER zelf te stappen
    Esc of P      : pauze

  - Loop tegen aarde om te graven; loop over een diamant om hem te
    pakken.
  - Duw een rots opzij door er horizontaal tegenaan te lopen (als
    de plek erachter leeg is).
  - Verzamel genoeg diamanten (zie de teller linksboven): de
    uitgang gaat knipperen. Bereik hem op tijd!

De bewoners van de grot
-----------------------
  - Vuurvliegjes en vlinders zijn dodelijk bij aanraking. Laat een
    rots op een vlinder vallen: hij verandert in 9 diamanten!
  - De amoebe (groene blob) groeit. Sluit hem volledig in met
    rotsen/aarde en hij wordt diamant; laat hem te groot worden en
    hij wordt steen.
  - De toverwand (paars) verandert een vallende rots in een
    diamant (en andersom) als er ruimte onder is.

Levens en punten
----------------
  U begint met 3 levens. U verliest een leven als u verpletterd
  wordt, een vijand aanraakt of de tijd op is; daarna begint de
  grot opnieuw. Punten krijgt u voor diamanten en voor de tijd die
  overblijft bij de uitgang. Uw hoogste score wordt bewaard.

Intro met stem (splashvenster)
------------------------------
  Bij het opstarten verschijnt het drakenlogo en spreekt de stem
  de titel en "Gemaakt door Dravenlock Games" uit. Dit is een apart
  splashvenster; daarna opent het spel. Standaard een mannenstem
  (code "M1"); andere codes staan na de eerste start in de map
  "DraveBoulder-data" in draveboulder-stemmen.txt en u kunt
  "voice_name" in DraveBoulder-data\config.json aanpassen. De stem
  kunt u in Instellingen aan- of uitzetten. Het stem-model wordt de
  eerste keer automatisch gedownload.

Donatieknop
-----------
  Rechtsboven in de menu's staat een hartje-knop (Donatie). Die
  opent https://paypal.me/roger076 in uw browser.

Draagbaar (portable) - waar staan mijn gegevens?
-------------------------------------------------
  Het spel bewaart NIETS in Windows-systeemmappen. Alles komt in
  een map "DraveBoulder-data" NAAST het programma: uw instellingen,
  highscore en vordering (config.json), de lijst stemcodes
  (draveboulder-stemmen.txt) en, mocht het misgaan, het foutenlog
  (draveboulder-fout.txt). Zo blijft uw C-schijf schoon en kunt u
  het spel met map en al verplaatsen of op een USB-stick zetten.

  Opnieuw beginnen met een schone lei? Verwijder de map
  "DraveBoulder-data"; de volgende start zet alles weer standaard.

Taal en geluid
--------------
  Het spel kiest automatisch uw systeemtaal (Nederlands of Engels).
  In Instellingen past u taal, geluid, muziek, stem en volume aan.
  Muziek en geluiden zijn volledig procedureel.

Donatie
-------
  DraveBoulder is gratis. Vindt u het leuk? Een donatie wordt zeer
  gewaardeerd:  https://paypal.me/roger076
  Vragen of ideeen:  service@dravenlock.nl

Veel plezier en pas op voor vallende rotsen!
