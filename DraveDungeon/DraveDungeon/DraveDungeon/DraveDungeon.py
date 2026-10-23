# -*- coding: utf-8 -*-
"""DraveDungeon - start hier."""
import os
import sys
import traceback


def _log_crash(exc_type, exc, tb):
    try:
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
        with open(os.path.join(base, "dravedungeon_fout.txt"), "w", encoding="utf-8") as f:
            f.write("DraveDungeon is vastgelopen.\n\n")
            traceback.print_exception(exc_type, exc, tb, file=f)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc, tb)


sys.excepthook = _log_crash

from game import main

if __name__ == "__main__":
    main()
