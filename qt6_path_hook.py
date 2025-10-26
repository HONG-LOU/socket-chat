import os, sys
from pathlib import Path
def add(p):
    try: os.add_dll_directory(str(p))
    except Exception: os.environ["PATH"]=str(p)+os.pathsep+os.environ.get("PATH","")
base=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))
qtbin=base/"PyQt6"/"Qt6"/"bin"; qtplugins=base/"PyQt6"/"Qt6"/"plugins"
if qtbin.exists(): add(qtbin)
if qtplugins.exists(): os.environ["QT_PLUGIN_PATH"]=str(qtplugins)
