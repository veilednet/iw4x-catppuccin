"""
Catppuccin Macchiato theme builder for IW4x (classic x86 client).

Produces userraw/z_catppuccin.iwd containing:
  * images/*.iwi   - solid / transparent replacements for the menu background art,
                     and Catppuccin-tinted selection bars
  * ui_mp/**.menu  - recoloured copies of every menu (IW4x raw menus + stock menus
                     dumped with OpenAssetTools' Unlinker), which IW4x loads from disk
                     and swaps in by menu name
  * ui_mp/*.inc, ui/*.h - recoloured shared style includes used by the raw menus

Nothing in main/ or zone/ is modified; delete the .iwd to go back to stock.
"""
import colorsys, io, os, re, sys, zipfile, json
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from iwi import Index, decode, encode_argb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CTP_GAME_DIR", r"C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Modern Warfare 2")
WORK = os.environ.get("CTP_WORK", os.path.join(HERE, "work"))
RAW = os.path.join(WORK, "iw4x_raw")                 # ui/ + ui_mp/ extracted from main/iw4x/x86/iw4x_00.iwd
DUMPS = [os.path.join(WORK, "oat", d) for d in ("common_mp", "localized_ui_mp", "patch_mp")]  # later wins
OUT = os.environ.get("CTP_OUT", os.path.join(os.path.dirname(HERE), "userraw", "z_catppuccin.iwd"))  # package payload
TEST_HOOK = False
# stock menus whose expressions exceed the game's parser limits - keep the originals
EXCLUDE_STOCK = {"ui_mp/scorebar_hd.menu", "ui_mp/scorebar_sd.menu", "ui_mp/menu_challenges.menu"}
# IW4x re-parses every disk menu into the 11 MB hunk when a map loads, so only the screens people
# actually look at get a themed copy; the rest stay stock (they still get the solid backgrounds).
HEAVY_STOCK = re.compile(r"^ui_mp/(settings_quick_|page_|menu_playercard_|popup_(primary|secondary)_attachments|popup_challenge|"
                         r"menu_cas_popup|menu_challenge_details|menu_records|menu_xboxlive_teams|playercard_|xpbar_|perks_info|"
                         r"popup_cac_|streak_set|gear_|elevator_|settings_bonus_map|menu_systemlink|menu_gamesetup_systemlink|"
                         r"scriptmenus/|hud|ac130|killstreak|perk_|promotion|splash|youarehost|dirt_|defcon|minimap|compass|"
                         r"scorebar|missilecam|remote_chopper|safearea|victory_|dpad_|hold_breath|targetmap|weapon|objective|obituary|spectator|killcam|predator|javelin|stinger|uav|nightvision)")

def minify(text):
    """Collapse indentation/spacing outside strings - smaller sources parse with less hunk."""
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line: continue
        if '"' not in line: line = re.sub(r"[ \t]+", " ", line)
        out.append(line)
    return "\n".join(out)

SKIP_LISTS = {"menus.txt", "patch_mp_menus.txt", "ingame.txt", "hud_480.txt", "hud_720.txt", "code.txt"}

# ---------------------------------------------------------------- palette
HEX = dict(rosewater="f4dbd6", flamingo="f0c6c6", pink="f5bde6", mauve="c6a0f6", red="ed8796",
           maroon="ee99a0", peach="f5a97f", yellow="eed49f", green="a6da95", teal="8bd5ca",
           sky="91d7e3", sapphire="7dc4e4", blue="8aadf4", lavender="b7bdf8", text="cad3f5",
           subtext1="b8c0e0", subtext0="a5adcb", overlay2="939ab7", overlay1="8087a2",
           overlay0="6e738d", surface2="5b6078", surface1="494d64", surface0="363a4f",
           base="24273a", mantle="1e2030", crust="181926")
P = {k: tuple(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4)) for k, v in HEX.items()}
P8 = {k: tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) for k, v in HEX.items()}

NEUTRAL_RAMP = [(0.00, "crust"), (0.10, "mantle"), (0.20, "base"), (0.25, "surface0"), (0.35, "surface1"),
                (0.42, "surface2"), (0.50, "overlay0"), (0.58, "overlay1"), (0.65, "overlay2"),
                (0.72, "subtext0"), (0.85, "subtext1"), (1.00, "text")]

def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))

def neutral(l):
    l = max(0.0, min(1.0, l))
    for (l0, n0), (l1, n1) in zip(NEUTRAL_RAMP, NEUTRAL_RAMP[1:]):
        if l <= l1:
            return mix(P[n0], P[n1], (l - l0) / (l1 - l0) if l1 > l0 else 0)
    return P["text"]

EXPLICIT = {  # MW2/IW4x accent colours -> Catppuccin roles
    (0.25, 1.0, 0.45): "mauve",      # MW2 selection green (highlight_selected)
    (0.8, 0.95, 1.0): "sky",
    (1.0, 0.8, 0.4): "peach",        # gold titles
    (0.75, 1.0, 0.7): "green",
}

def map_rgb(r, g, b):
    key = (round(r, 3), round(g, 3), round(b, 3))
    if key in EXPLICIT:
        return P[EXPLICIT[key]]
    rc, gc, bc = (min(1.0, max(0.0, v)) for v in (r, g, b))
    if max(rc, gc, bc) - min(rc, gc, bc) <= 0.12:
        return neutral((rc + gc + bc) / 3)
    h, l, s = colorsys.rgb_to_hls(rc, gc, bc)
    h *= 360
    if h < 15 or h >= 340: acc = "red"
    elif h < 38: acc = "peach"
    elif h < 70: acc = "yellow"
    elif h < 160: acc = "green"
    elif h < 200: acc = "teal"
    elif h < 255: acc = "blue"
    elif h < 290: acc = "mauve"
    else: acc = "pink"
    target = P[acc]
    v = max(rc, gc, bc)
    if v < 0.6:  # dark variants stay dark
        target = mix(P["crust"], target, max(0.25, v / 0.6))
    return target

def fmt(x):
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"

# ---------------------------------------------------------------- menu recolouring
NUM = r"(-?\d*\.?\d+)"
QUAD = r"\s+".join([NUM] * 4)
KW_RE = re.compile(r"(?i)\b(forecolor|backcolor|bordercolor|outlinecolor|glowcolor|disablecolor|focuscolor)(\s+)" + QUAD)
SET_RE = re.compile(r"(?i)\b(setitemcolor\s+\S+\s+)(\w+)(\s+)" + QUAD)
DEF_RE = re.compile(r"(?im)^(\s*#define\s+\w*COLOR\w*\s+)" + QUAD)
BG_RE = re.compile(r'(?i)\bbackground\s+"?([\w$]+)"?')

SOLID_ART = {"mw2_main_background", "mw2_main_sp_image", "mw2_main_mp_image", "mw2_main_co_image",
             "animbg_blur_front", "animbg_blur_back", "animbg_blur_fogscroll", "mockup_bg_glow",
             "big_menu_lightfx", "small_box_lightfx", "imagearg"}
BAKED_BARS = re.compile(r"(?i)^(menu_button_selection_bar|menu_setting_selection_bar|menu_rules_selection_bar|"
                        r"popup_button_selection_bar\w*|ks_button_selection_bar)$")
CHROME = re.compile(r"(?i)^(white|black|gradient\w*|line_\w+|drop_shadow_\w+|button_highlight_end|highlight_selected|"
                    r"mw2_popup_bg_\w+|mockup_popup_bg_stencilfill|popup_button_selected_bar_bling|ks_button_selected_bar|"
                    r"xpbar_\w+|\w*_xpbar\w*|summary_xpbar\w*|shadow_inset|playercard\w*_bg|specialty_new_bg|"
                    r"challenge_name_bar|mod_header|server_hardware_header|objective_line|highlight_shader\w*|"
                    r"choice_highlight|choice_sep_background|newsticker_background|stencil_\w+|scanlines_stencil)$")

def item_spans(text):
    """(start, end, background) for every itemDef { ... } block."""
    spans = []
    for m in re.finditer(r"(?i)\bitemDef\b", text):
        i = text.find("{", m.end())
        if i < 0: continue
        depth, j = 0, i
        while j < len(text):
            c = text[j]
            if c == "{": depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        body = text[i:j]
        bg = BG_RE.search(body)
        dyn = re.search(r"(?i)\bexp\s+material\b", body)
        spans.append((i, j, (bg.group(1) if bg else ("$dynamic" if dyn else None))))
    return spans

def recolour(text, stats):
    spans = item_spans(text)

    def bg_at(pos):
        best = None
        for s, e, bg in spans:
            if s <= pos <= e and (best is None or s > best[0]): best = (s, bg)
        return best[1] if best else None

    def quad(groups, alpha_override=None):
        r, g, b, a = (float(x) for x in groups)
        nr, ng, nb = map_rgb(r, g, b)
        a = a if alpha_override is None else alpha_override
        return f"{fmt(nr)} {fmt(ng)} {fmt(nb)} {fmt(a)}"

    def kw(m):
        key, sp = m.group(1), m.group(2)
        bg = bg_at(m.start())
        lbg = (bg or "").lower()
        if key.lower() == "forecolor" and bg:
            if lbg == "mw2_main_cloud_overlay":
                stats["clouds"] += 1
                return f"{key}{sp}1 1 1 0"
            if lbg == "mw2_popup_bg_fogscroll":
                stats["popup"] += 1
                return f"{key}{sp}{' '.join(fmt(x) for x in P['surface0'])} {m.group(6)}"
            if lbg == "mw2_popup_bg_fogstencil":
                return f"{key}{sp}1 1 1 0.94"
            if lbg in SOLID_ART:
                return m.group(0)
            if not (CHROME.match(lbg) or BAKED_BARS.match(lbg)):        # icons, emblems, weapon art, HUD overlays, dynamic materials
                stats["kept_art"] += 1
                return m.group(0)
        stats["mapped"] += 1
        return f"{key}{sp}{quad(m.groups()[2:6])}"

    def setcol(m):
        stats["mapped"] += 1
        return f"{m.group(1)}{m.group(2)}{m.group(3)}{quad(m.groups()[3:7])}"

    def define(m):
        stats["mapped"] += 1
        return f"{m.group(1)}{quad(m.groups()[1:5])}"

    text = KW_RE.sub(kw, text)
    text = rebar(text, stats)
    text = SET_RE.sub(setcol, text)
    text = DEF_RE.sub(define, text)
    return text

EXP_LINE = re.compile(r"^(\s*exp\s+\w+(?:\s+[rgbaxywhRGBAXYWH](?=\s))?\s+)(.*?)\s*;\s*$")
WHEN_LINE = re.compile(r"^(\s*(?:visible|disabled)\s+when\s*\(.*\))\s*;\s*$", re.I)

def _wrapped(expr):
    """True if the whole expression is enclosed by one outer pair of parentheses."""
    if not (expr.startswith("(") and expr.endswith(")")): return False
    depth, in_str = 0, False
    for i, c in enumerate(expr):
        if c == '"' and (i == 0 or expr[i - 1] != "\\"): in_str = not in_str
        if in_str: continue
        if c == "(": depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0 and i != len(expr) - 1: return False
    return True

def normalise_stock(text, stats):
    """OAT dumps write `exp rect y a + b;` - the game's menu parser wants `exp rect y (a + b)`."""
    out = []
    for line in text.split("\n"):
        m = EXP_LINE.match(line)
        if m:
            expr = m.group(2).strip()
            line = m.group(1) + (expr if _wrapped(expr) else f"({expr})")
            stats["exp_fixed"] += 1
        else:
            m = WHEN_LINE.match(line)
            if m: line = m.group(1); stats["when_fixed"] += 1
        out.append(line)
    return "\n".join(out)

BAR_BG = re.compile(r'(?i)(\bbackground\s+)"?(menu_button_selection_bar|menu_setting_selection_bar|menu_rules_selection_bar|'
                    r'popup_button_selection_bar(?:_short|_flipped|_bling)?|ks_button_selection_bar)"?')
HILITE = P["mauve"]

def rebar(text, stats):
    """The MW2 selection-bar textures live inside the fastfile (not overridable), so draw the
    focus highlight with a gradient tinted Catppuccin mauve instead."""
    for s0, e0, bg in sorted(item_spans(text), key=lambda t: -t[0]):
        block = text[s0:e0]
        m = BAR_BG.search(block)
        if not m: continue
        has_fc = re.search(r"(?im)(^|[\s{])forecolor\s", block.replace("exp forecolor", "exp_fc"))
        rep = m.group(1) + '"gradient_fadein"'
        if not has_fc:
            rep += " forecolor " + " ".join(fmt(c) for c in HILITE) + " 0.8"
        block = block[:m.start()] + rep + block[m.end():]
        text = text[:s0] + block + text[e0:]
        stats["bars"] = stats.get("bars", 0) + 1
    return text

def menudef_names(text):
    names = []
    for m in re.finditer(r"(?i)\bmenuDef\b", text):
        n = re.search(r'(?i)\bname\s+"?([\w\-]+)"?', text[m.end():m.end() + 400])
        if n: names.append(n.group(1).lower())
    return names

def collect_menus():
    files = {}   # archive path -> (source path, origin)
    # stock dumps (later dumps win for identical paths, matching fastfile load order)
    for d in DUMPS:
        for dp, _, fs in os.walk(d):
            for f in fs:
                rel = os.path.relpath(os.path.join(dp, f), d).replace("\\", "/")
                if not rel.startswith("ui_mp/") or not rel.endswith(".menu"): continue
                if rel in EXCLUDE_STOCK or HEAVY_STOCK.match(rel): continue
                if "menudef" not in open(os.path.join(dp, f), encoding="latin1").read().lower(): continue  # loadMenu lists
                files[rel] = (os.path.join(dp, f), "stock")
    # IW4x's own raw files always win (they are what the client actually runs)
    iw4x_names = set()
    for dp, _, fs in os.walk(RAW):
        for f in fs:
            rel = os.path.relpath(os.path.join(dp, f), RAW).replace("\\", "/")
            if not (rel.startswith("ui_mp/") or rel.startswith("ui/")): continue
            if os.path.basename(rel) in SKIP_LISTS: continue
            files[rel] = (os.path.join(dp, f), "iw4x")
            if rel.endswith(".menu"):
                iw4x_names.update(menudef_names(open(os.path.join(dp, f), encoding="latin1").read()))
    # never let a stock dump shadow a menu IW4x replaced under a different file name
    dropped = []
    for rel, (src, origin) in list(files.items()):
        if origin == "stock":
            names = menudef_names(open(src, encoding="latin1").read())
            if any(n in iw4x_names for n in names):
                dropped.append(rel); del files[rel]
    return files, dropped

# ---------------------------------------------------------------- images
def solid(rgba, size=(32, 32)):
    return encode_argb(Image.new("RGBA", size, rgba), flags=0x173)

def tint_bar(idx, name, dark="surface0", light="mauve"):
    data, _ = idx.read(name)
    info, im = decode(data)
    px = im.load()
    out = Image.new("RGBA", im.size)
    o = out.load()
    d, l = P8[dark], P8[light]
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = px[x, y]
            t = (r + g + b) / 765
            o[x, y] = tuple(int(d[i] + (l[i] - d[i]) * t) for i in range(3)) + (a,)
    return encode_argb(out, flags=info["flags"] | 0x2)

def build_images():
    idx = Index(ROOT)
    base = P8["base"] + (255,)
    clear = (0, 0, 0, 0)
    imgs = {
        "menu_background": solid(base),            # mw2_main_background
        "bg_blur_back": solid(base),               # animbg_blur_back (opaque)
        "menu_cloud_overlay": solid((255, 255, 255, 255)),  # popup fill source; menu clouds are hidden via alpha 0
    }
    for n in ("menu_mp_image", "menu_sp_image", "menu_co_image", "mockup_bgglow", "bg_blur_front",
              "bg_blur_fogscroll", "big_menu_lightfx", "small_box_lightfx", "menu_soldier_band_blur"):
        imgs[n] = solid(clear)
    for n in ("mw2_selection_bar", "mw2_selection_bar_144", "mw2pc_setting_selection_bar", "mw2_popup_selection_bar",
              "mw2_popup_selection_bar_short", "mw2_popup_selection_bar_mirrored", "mw2_popup_selection_bar_bling",
              "mw2_ks_selection_bar"):
        try: imgs[n] = tint_bar(idx, n)
        except KeyError: print("  (no image)", n)
    return imgs

# ---------------------------------------------------------------- main
def main():
    files, dropped = collect_menus()
    stats = dict(mapped=0, kept_art=0, clouds=0, popup=0, exp_fixed=0, when_fixed=0)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for rel, (src, origin) in sorted(files.items()):
            text = open(src, encoding="latin1").read()
            if origin == "stock":
                text = normalise_stock(text, stats)
                text_is_stock = True
            else:
                text_is_stock = False
            if rel == "ui_mp/bg.inc":
                # IW4x hides the menu background whenever a mod is loaded (black menus) - always draw it
                text = re.sub(r'dvarString\(\s*"fs_game"\s*\)\s*[!=]=\s*""\s*&&\s*', "", text)
            if TEST_HOOK and rel == "ui_mp/main_text.menu":   # test builds only: run the screenshot script once the UI is up
                text = re.sub(r'(uiScript\s+"checkFirstLaunch";[ \t]*\\)', lambda m: m.group(1) + '\n\texec "exec ctp_test"; \\', text, count=1)
                assert "ctp_test" in text
            text = recolour(text, stats)
            if text_is_stock: text = minify(text)
            z.writestr(rel, text.encode("latin1"))
        for name, blob in build_images().items():
            z.writestr(f"images/{name}.iwi", blob)
    os.replace(tmp, OUT)
    n_stock = sum(1 for v in files.values() if v[1] == "stock")
    n_iw4x = len(files) - n_stock
    print(f"menus/includes: {n_iw4x} iw4x + {n_stock} stock  (dropped {len(dropped)} stock files shadowing IW4x menus)")
    print("colour edits:", stats)
    print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")

if __name__ == "__main__":
    main()
