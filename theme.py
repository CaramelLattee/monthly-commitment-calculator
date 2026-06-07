import customtkinter as ctk

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]

MONO = "Consolas"
UI   = "Segoe UI"

_THEMES = {
    "dark": dict(
        BG="#090e1c", PANEL="#0d1526", STRIP="#111d30", BORDER="#1c2d47",
        BLUE="#3d8bff", BLUE_D="#1a5fd4",
        PINK="#ff3d82", PINK_D="#cc1060",
        TEXT="#cfe0ff", MUTED="#3a5575",
        GREEN="#00d98b", AMBER="#ffaa00",
    ),
    "light": dict(
        BG="#f0f4ff", PANEL="#ffffff", STRIP="#e6eeff", BORDER="#b8cdf0",
        BLUE="#1a6aff", BLUE_D="#0a4abf",
        PINK="#e8006a", PINK_D="#aa0050",
        TEXT="#0a1530", MUTED="#7090b0",
        GREEN="#007a50", AMBER="#b07000",
    ),
}

BG = PANEL = STRIP = BORDER = BLUE = BLUE_D = PINK = PINK_D = TEXT = MUTED = GREEN = AMBER = ""


def _apply_theme(name: str):
    global BG, PANEL, STRIP, BORDER, BLUE, BLUE_D, PINK, PINK_D, TEXT, MUTED, GREEN, AMBER
    t = _THEMES[name]
    BG, PANEL, STRIP, BORDER = t["BG"], t["PANEL"], t["STRIP"], t["BORDER"]
    BLUE, BLUE_D = t["BLUE"], t["BLUE_D"]
    PINK, PINK_D = t["PINK"], t["PINK_D"]
    TEXT, MUTED  = t["TEXT"], t["MUTED"]
    GREEN, AMBER = t["GREEN"], t["AMBER"]
    ctk.set_appearance_mode("dark" if name == "dark" else "light")


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
_apply_theme("dark")
