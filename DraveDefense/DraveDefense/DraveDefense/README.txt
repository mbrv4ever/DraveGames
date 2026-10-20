============================================================
  DraveDefense  v0.2.0
  Een D&D tower-defense van Dravenlock Games
============================================================

Snel starten (Windows)
----------------------
  Dubbelklik op:  Start-DraveDefense.bat

  De eerste keer zet het spel zelf alles klaar: het zoekt uw
  Python (3.10 of nieuwer), maakt een eigen omgeving aan en
  installeert de benodigde pakketten (ook de stem). Daarna start
  het spel. U hoeft niets handmatig te installeren.

Een Windows-programma (.exe) maken
----------------------------------
  Dubbelklik op:  Maak-DraveDefense-EXE.bat

  Hiermee wordt een los bestand gemaakt:  dist\DraveDefense.exe
  De stem wordt meegebakken, dus de .exe is groot maar werkt
  overal zonder Python.

Iets kapot? Opnieuw beginnen
----------------------------
  Dubbelklik op:  herstel.bat
  Dit wist de omgeving; de volgende start zet alles opnieuw op.

Doel van het spel
-----------------
  Vijanden lopen over het pad naar uw kasteel (rechts). Houd ze
  tegen door torens te bouwen op de open grasvelden. Bereikt een
  vijand het kasteel, dan verliest u een leven. Zijn al uw levens
  op, dan valt het kasteel. Overleef alle golven om te winnen.

Bediening
---------
  Alles met de muis:
    Klik op een open grasveld   : bouwmenu (kies een toren)
    Klik op een bestaande toren : upgraden, verplaatsen of
                                  verkopen
    Knop 'Start golf'           : de volgende golf laten komen
                                  (spatie kan ook)
    Esc of P                    : pauze (of sluit een open menu)

  Tussen de golven door heeft u rustig de tijd om te bouwen en
  upgraden. Druk op 'Start golf' als u klaar bent.

De torens
---------
  Boogschutter (55 goud) : snel, goedkoop, een doel tegelijk.
  Magier       (95 goud) : krachtig, raakt meerdere vijanden
                           tegelijk (splash).
  Vorsttoren   (75 goud) : weinig schade, maar vertraagt vijanden
                           zodat uw andere torens meer tijd hebben.

  Elke toren is twee keer te upgraden (meer schade en bereik).
  Een toren verplaatsen kan gratis: kies 'Verplaats' en klik een
  open veld aan. Een verslagen vijand levert goud op; verkopen
  geeft goud terug.

Intro met stem (splashvenster)
------------------------------
  Bij het opstarten verschijnt het drakenlogo en spreekt de stem
  de titel en "Gemaakt door Dravenlock Games" uit. Dit is een apart
  splashvenster; daarna opent het spel. Standaard een mannenstem
  (code "M1"); andere codes staan na de eerste start in de map
  "DraveDefense-data" in dravedefense-stemmen.txt en u kunt
  "voice_name" in DraveDefense-data\config.json aanpassen. De stem
  kunt u in Instellingen aan- of uitzetten. Het stem-model wordt de
  eerste keer automatisch gedownload.

Donatieknop
-----------
  Rechtsboven in de menu's staat een hartje-knop (Donatie). Die
  opent https://paypal.me/roger076 in uw browser.

Draagbaar (portable) - waar staan mijn gegevens?
-------------------------------------------------
  Het spel bewaart NIETS in Windows-systeemmappen. Alles komt in
  een map "DraveDefense-data" NAAST het programma: uw instellingen
  en beste golf (config.json), de lijst stemcodes
  (dravedefense-stemmen.txt) en, mocht het ooit misgaan, het
  foutenlog (dravedefense-fout.txt). Zo blijft uw C-schijf schoon
  en kunt u het spel met map en al verplaatsen of op een USB-stick
  zetten.

  Opnieuw beginnen met een schone lei? Verwijder de map
  "DraveDefense-data"; de volgende start zet alles weer standaard.

Taal en geluid
--------------
  Het spel kiest automatisch uw systeemtaal (Nederlands of Engels).
  In Instellingen past u taal, geluid, muziek, stem en volume aan.
  Muziek en geluiden zijn volledig procedureel.

Donatie
-------
  DraveDefense is gratis. Vindt u het leuk? Een donatie wordt zeer
  gewaardeerd:  https://paypal.me/roger076
  Vragen of ideeen:  service@dravenlock.nl

Veel plezier en verdedig dat kasteel!
