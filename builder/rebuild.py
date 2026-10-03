r"""Regenerate userraw/z_catppuccin.iwd from a game install's *current* IW4x + MW2 files.

    python builder/rebuild.py "C:\...\Call of Duty Modern Warfare 2"

Run it after an IW4x update: the theme ships recoloured copies of IW4x's own menus, and stale
copies would hide any menu changes an update brings. Requires Python 3 + Pillow, and the
Unlinker.exe that the IW4x launcher installs into the game folder.
"""
import os, shutil, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
game = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CTP_GAME_DIR", "")
if not os.path.isfile(os.path.join(game, "iw4x.exe")):
    sys.exit("usage: python rebuild.py <path to the Call of Duty Modern Warfare 2 folder with IW4x installed>")
os.environ["CTP_GAME_DIR"] = game

WORK = os.path.join(HERE, "work")
shutil.rmtree(WORK, ignore_errors=True)
with zipfile.ZipFile(os.path.join(game, "main", "iw4x", "x86", "iw4x_00.iwd")) as z:
    for n in z.namelist():
        if n.replace("\\", "/").startswith(("ui/", "ui_mp/")) and not n.endswith("/"):
            z.extract(n, os.path.join(WORK, "iw4x_raw"))
for zone in ("common_mp", "localized_ui_mp", "patch_mp"):
    ff = os.path.join(game, "zone", "iw4x", "x86", "english", zone + ".ff")
    subprocess.run([os.path.join(game, "Unlinker.exe"), "--legacy-menus", "--include-assets", "menu,menulist",
                    "-o", os.path.join(WORK, "oat", zone), ff], check=True, cwd=game, stdout=subprocess.DEVNULL)

sys.path.insert(0, HERE)
import build_theme
build_theme.main()
shutil.rmtree(WORK, ignore_errors=True)
