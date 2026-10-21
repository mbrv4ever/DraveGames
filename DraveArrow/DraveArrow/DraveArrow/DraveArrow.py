# -*- coding: utf-8 -*-
"""DraveArrow.py - opstartpunt voor DraveArrow.

Houdt de naam los van de spelmodule (arrow.py) zodat de Windows-EXE
'DraveArrow.exe' heet. Vangt onverwachte fouten op en schrijft ze naar een
logbestand, zodat een crash nooit spoorloos verdwijnt.
"""
import datetime
import os
import sys
import traceback


def _log_path():
    try:
        import arrow
        d = arrow.config_dir()
    except Exception:
        d = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(d, "dravearrow-fout.txt")


def main():
    try:
        import arrow
        arrow.main()
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
        sys.stderr.write("DraveArrow is gestopt door een fout.\n")
        sys.stderr.write("Logboek: %s\n" % path)
        try:
            input("Druk op Enter om af te sluiten...")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
