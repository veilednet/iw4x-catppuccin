# Generates userraw/ctp_classes.cfg - run in-game with:  exec ctp_classes
import os
# (slot, name, primary(weapon, att1, att2, camo), secondary(weapon, att1, att2, camo), equipment, special, perk1, perk2, perk3, deathstreak, blurb)
C = [
 # ---------------- trickshot / quickscope ----------------
 (0, "^:Rainbow Snipe",   ("cheytac","fmj","none","blue_tiger"), ("model1887","akimbo","none","none"), "throwingknife_mp", "concussion_grenade", "specialty_fastreload","specialty_lightweight","specialty_extendedmelee","specialty_copycat", "Intervention FMJ + Akimbo 1887s, SoH / Lightweight / Commando"),
 (1, "^5Quickscope God",  ("cheytac","fmj","none","digital"),    ("usp","tactical","none","none"),     "throwingknife_mp", "flash_grenade",      "specialty_fastreload","specialty_bulletdamage","specialty_extendedmelee","specialty_copycat", "Intervention FMJ, SoH / Stopping Power / Commando"),
 (2, "^HCoD4 R700 Flicks",("iw3_remington700","none","none","none"), ("usp","tactical","none","none"),  "throwingknife_mp", "flash_grenade",      "specialty_marathon","specialty_lightweight","specialty_extendedmelee","specialty_copycat", "CoD4 R700 + Tac Knife, Marathon / Lightweight / Commando"),
 (3, "^IBarrett Bounces", ("barrett","fmj","none","orange_fall"), ("spas12","none","none","none"),     "throwingknife_mp", "smoke_grenade",      "specialty_fastreload","specialty_lightweight","specialty_extendedmelee","specialty_combathigh", "Barrett FMJ + SPAS, SoH / Lightweight / Commando"),
 (4, "^GWA2000 Snaps",    ("wa2000","fmj","none","red_tiger"),    ("usp","tactical","none","none"),     "specialty_tacticalinsertion", "concussion_grenade", "specialty_fastreload","specialty_lightweight","specialty_extendedmelee","specialty_copycat", "WA2000 FMJ + Tac Knife + Tac Insert"),
 (5, "^<OMA Canswap",     ("cheytac","fmj","none","arctic"),      ("onemanarmy","none","none","none"),  "throwingknife_mp", "concussion_grenade", "specialty_onemanarmy","specialty_lightweight","specialty_extendedmelee","specialty_copycat", "Intervention + One Man Army for class-swap tricks"),
 # ---------------- tryhard / meta ----------------
 (6, "^KUMP Silent Rush", ("ump45","silencer","rof","red_urban"), ("spas12","grip","none","none"),     "semtex_mp",        "flash_grenade",      "specialty_marathon","specialty_lightweight","specialty_heartbreaker","specialty_combathigh", "UMP45 Silencer/Rapid Fire, Marathon / Lightweight / Ninja"),
 (7, "^JACR Laser Beam",  ("masada","eotech","fmj","digital"),    ("usp","fmj","none","none"),          "frag_grenade_mp",  "flash_grenade",      "specialty_scavenger","specialty_bulletdamage","specialty_heartbreaker","specialty_copycat", "ACR Holo/FMJ, Scavenger / Stopping Power / Ninja"),
 (8, "^:Tube Tryhard",    ("m4","gl","silencer","red_tiger"),     ("onemanarmy","none","none","none"),  "semtex_mp",        "concussion_grenade", "specialty_onemanarmy","specialty_explosivedamage","specialty_extendedmelee","specialty_grenadepulldeath", "M4 Tube + OMA, Danger Close / Commando / Martyrdom"),
 (9, "^GAkimbo 1887s",    ("riotshield","none","none","none"),    ("model1887","akimbo","none","none"), "throwingknife_mp", "flash_grenade",      "specialty_marathon","specialty_lightweight","specialty_extendedmelee","specialty_combathigh", "Akimbo 1887s with a riot shield on your back"),
 (10,"^ITac Knife Ninja", ("mp5k","rof","silencer","none"),       ("usp","tactical","none","none"),     "throwingknife_mp", "concussion_grenade", "specialty_marathon","specialty_lightweight","specialty_extendedmelee","specialty_copycat", "Tac Knife lunges, Marathon / Lightweight / Commando"),
]
lines = ["// Catppuccin class pack - generated. In-game console:  exec ctp_classes",
         "// Overwrites custom class slots 0-10. Slots 11-14 are left untouched.", ""]
for slot, name, pri, sec, eq, special, p1, p2, p3, ds, blurb in C:
    assert len(name) <= 20, name
    b = f"setPlayerData customClasses {slot}"
    lines.append(f"// slot {slot}: {blurb}")
    lines.append(f'{b} name "{name}^7"' if len(name) <= 18 else f'{b} name "{name}"')
    lines.append(f"{b} inUse 1")
    for i, (w, a1, a2, camo) in enumerate((pri, sec)):
        lines += [f"{b} weaponSetups {i} weapon {w}", f"{b} weaponSetups {i} attachment 0 {a1}",
                  f"{b} weaponSetups {i} attachment 1 {a2}", f"{b} weaponSetups {i} camo {camo}"]
    for i, p in enumerate((eq, p1, p2, p3, ds)): lines.append(f"{b} perks {i} {p}")
    lines.append(f"{b} specialGrenade {special}"); lines.append("")
lines += ["uploadstats", 'echo "^HCatppuccin class pack loaded ^7- open Create-a-Class to see them"']
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "userraw", "ctp_classes.cfg")
open(out, "w", newline="\n").write("\n".join(lines) + "\n")
print("wrote", out, "-", len(C), "classes")
