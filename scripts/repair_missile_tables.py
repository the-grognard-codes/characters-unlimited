"""Rebuild the visually verified RUE missile charts (PDF 366 / printed 363)."""
import re
from repair_source_passages import ROOT, load, replace, save_repairs


def chart(title, rows):
    return "## " + title + "\n\n" + "\n".join([
        "| Warhead | Mega-Damage | Speed | Maximum Range | Blast Radius | M.D.C. |",
        "| --- | --- | --- | --- | --- | --- |",
        *("| " + " | ".join(row) + " |" for row in rows),
    ])


def main():
    short = [
        ("High Explosive (light)", "2D4x10", "500 mph (804 kmph)", "5 miles (8 km)", "10 ft (3 m)", "5"),
        ("High Explosive (medium)", "2D6x10", "500 mph (804 kmph)", "5 miles (8 km)", "15 ft (4.6 m)", "5"),
        ("Fragmentation (light)", "2D4x10", "450 mph (724 kmph)", "3 miles (4.8 km)", "20 ft (6.1 m)", "5"),
        ("Armor Piercing (medium)", "2D6x10", "650 mph (1045 kmph)", "5 miles (8 km)", "5 ft (1.5 m)", "5"),
        ("Plasma/Napalm (medium)", "2D6x10", "500 mph (804 kmph)", "3 miles (4.8 km)", "15 ft (4.6 m)", "5"),
        ("Tear Gas", "None", "200 mph (321 kmph)", "1/2 mile (0.8 km)", "10 ft (3 m)", "5"),
        ("Knock-Out Gas", "None", "200 mph (321 kmph)", "1/2 mile (0.8 km)", "10 ft (3 m)", "5"),
        ("Smoke (colors available)", "None", "300 mph (482.7 kmph)", "1 mile (1.6 km)", "20 ft (6.1 m)", "5"),
        ("Fire Retardent", "None", "200 mph (321 kmph)", "1/2 mile (0.8 km)", "20 ft (6.1 m)", "5"),
    ]
    medium = [
        ("High Explosive (light)", "2D4x10", "1200 mph (1929 kmph)", "50 miles (80.4 km)", "20 ft (6.1 m)", "10"),
        ("High Explosive (medium)", "2D6x10", "1200 mph (1929 kmph)", "40 miles (64.3 km)", "20 ft (6.1 m)", "10"),
        ("High Explosive (heavy)", "3D6x10", "1200 mph (1929 kmph)", "40 miles (64.3 m)", "30 ft (9.1 m)", "10"),
        ("Fragmentation (light)", "2D6x10", "1000 mph (1608 kmph)", "40 miles (64.3 km)", "40 ft (12.2 m)", "10"),
        ("Armor Piercing (medium)", "3D6x10", "1600 mph (2571 kmph)", "60 miles (96.5 km)", "20 ft (6.1 m)", "10"),
        ("Plasma/Napalm (medium)", "4D6x10", "1400 mph (2251 kmph)", "40 miles (64.3 km)", "40 ft (12.2 m)", "10"),
        ("Multi-Warhead*", "5D6x10", "1200 mph (1929 kmph)", "80 miles (128.7 km)", "20 ft (6.1 m)", "10"),
        ("Smoke (colors available)", "None", "1000 mph (1608 kmph)", "40 miles (64.3 km)", "40 ft (12.2 m)", "10"),
    ]
    long = [
        ("High Explosive (medium)", "3D6x10", "2010 mph (Mach 3)", "500 miles (804 km)", "30 ft (9.1 m)", "20"),
        ("High Explosive (heavy)", "4D6x10", "2010 mph (Mach 3)", "500 miles (804 m)", "40 ft (12.2 m)", "20"),
        ("Fragmentation (light)", "2D6x10", "1400 mph (2251 kmph)", "400 miles (643 km)", "80 ft (24.4 m)", "20"),
        ("Armor Piercing (medium)", "3D6x10", "2010 mph (Mach 3)", "800 miles (1286 km)", "30 ft (9.1 m)", "20"),
        ("Plasma/Heat (medium)", "4D6x10", "1400 mph (2251 kmph)", "500 miles (804 km)", "40 ft (12.2 m)", "20"),
        ("Plasma/Heat (medium)*", "5D6x10", "1400 mph (2251 kmph)", "500 miles (804 km)", "50 ft (15.2 m)", "20"),
        ("Proton Torpedo (heavy)*", "6D6x10", "2010 mph (Mach 3)", "1200 miles (1928 km)", "50 ft (15.2 m)", "25"),
        ("Nuclear (medium)*", "1D4x100", "2010 mph (Mach 3)", "1000 miles (1608 km)", "40 ft (12.2 m)", "20"),
        ("Nuclear (heavy)*", "1D6x100", "2010 mph (Mach 3)", "1000 miles (1608 km)", "50 ft (15.2 m)", "20"),
        ("Nuclear Multi-warhead*", "2D4x100", "2010 mph (Mach 3)", "1800 miles (2893 km)", "50 ft (15.2 m)", "25"),
    ]
    mini = [
        ("High Explosive", "5D6", "500 mph (804 kmph)", "1 mile (1.6 km)", "5 ft (1.5 m)", "1"),
        ("Fragmentation", "5D6", "500 mph (804 kmph)", "1/2 mile (0.8 km)", "20 ft (6.1 m)", "1"),
        ("Armor Piercing", "1D4x10", "1400 mph (2251 kmph)", "1 mile (1.6 km)", "3 ft (0.9 m)", "2"),
        ("Plasma/Napalm (medium)", "1D6x10", "1200 mph (1929 kmph)", "1 mile (1.6 km)", "15 ft (1.5 m)", "1"),
        ("Smoke (colors available)", "None", "500 mph (804 kmph)", "1/2 mile (0.8 km)", "20 ft (6.1 m)", "1"),
    ]
    name = "Rifts - Ultimate Edition.md"
    matches = [m.group().rstrip("\n") for m in re.finditer(r"(?m)^\|[^\n]+\n(?:\|[^\n]*\n?)+", load(name)) if "Short Range Missiles" in m.group()]
    assert len(matches) == 1
    after = "\n\n".join(chart(t,r) for t,r in [("Short Range Missiles",short), ("Medium Range Missiles",medium), ("Long Range Missiles",long), ("Mini Missiles and Special Armaments",mini)])
    after += "\n\n\\* Available as smart bombs. +5 to strike."
    replace(name, matches[0], after, 366, 363, "Rebuilt a collapsed header-only table into four charts, 32 rows and 192 cells; visually checked every entry. Printed unit inconsistencies (64.3 m, 804 m, mini plasma 1.5 m) deliberately retained for source fidelity.")
    save_repairs(ROOT / "reports/ocr-review/source-repairs-05.json")


if __name__ == "__main__":
    main()
