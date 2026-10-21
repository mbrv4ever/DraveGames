# -*- coding: utf-8 -*-
"""DraveRainbow.py - opstartpunt voor DraveRainbow.

Houdt de naam los van de spelmodule (rainbow.py) zodat de Windows-EXE
'DraveRainbow.exe' heet. Vangt onverwachte fouten op en schrijft ze naar een
logbestand, zodat een crash nooit spoorloos verdwijnt.
"""
import datetime
import os
import sys
import traceback


def _log_path():
    try:
        import rainbow
        d = rainbow.config_dir()
    except Exception:
        d = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(d, "draverainbow-fout.txt")


def main():
    try:
        import rainbow
        rainbow.main()
    except SystemExit:
        raise
    except Exception:
        path = _log_path()
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n=== %s ===\n" % datetime.datetime.now().isoformat())
                f.write(traceback.format_exc())
        except Exception:
            pass
        sys.stderr.write("DraveRainbow is gestopt door een fout.\n")
        sys.stderr.write("Logboek: %s\n" % path)
        try:
            input("Druk op Enter om af te sluiten...")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
