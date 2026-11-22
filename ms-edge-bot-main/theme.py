"""Visual system for the app: colors, type, icons, and the few widget styles the UI is built from.

Colors are (light, dark) pairs; CustomTkinter picks one based on the Windows theme.
"""

from __future__ import annotations

import os
from functools import lru_cache

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont

C = {
    "bg":        ("#E5E9EE", "#12171D"),
    "surface":   ("#F9FAFB", "#1A2027"),
    "card":      ("#EFF2F5", "#212830"),
    "line":      ("#D5DBE2", "#2C343D"),
    "track":     ("#D9DFE6", "#2E3740"),
    "ink":       ("#18222C", "#E6EAEE"),
    "muted":     ("#5B6774", "#8E99A5"),
    "faint":     ("#8C97A2", "#5E6974"),
    "accent":    ("#1F6F8B", "#58AECB"),
    "accent_hi": ("#175A71", "#7BC3DB"),
    "accent_bg": ("#DCEBF1", "#1C3440"),
    "on_accent": ("#FFFFFF", "#0D1A20"),
    "done":      ("#2E7A59", "#5DBE8E"),
    "done_bg":   ("#DDEFE6", "#1C3329"),
    "warn":      ("#94600F", "#E0A84A"),
    "warn_bg":   ("#F5E9D3", "#3A2F1B"),
    "danger":    ("#A3313A", "#E27A80"),
    "danger_hi": ("#8A2830", "#EB959A"),
    "disabled":  ("#A6B0BA", "#4F5A65"),
}

# Segoe Fluent Icons (Windows 11) code points.
ICONS = {
    "refresh": "\uE72C", "shield": "\uEA18", "close": "\uE711", "play": "\uE768",
    "stop": "\uE71A", "delete": "\uE74D", "add": "\uE710", "check": "\uE73E",
}
_ICON_FONTS = ("SegoeIcons.ttf", "segmdl2.ttf")  # Windows 11, then Windows 10


class Fonts:
    def __init__(self):
        ui, display, num = "Segoe UI Variable Text", "Segoe UI Variable Display", "Bahnschrift"
        self.title = ctk.CTkFont(num, 28, "bold")
        self.big = ctk.CTkFont(num, 34, "bold")
        self.count = ctk.CTkFont(num, 16)
        self.h2 = ctk.CTkFont(display, 15, "bold")
        self.name = ctk.CTkFont(display, 15, "bold")
        self.button = ctk.CTkFont(ui, 13, "bold")
        self.body = ctk.CTkFont(ui, 13)
        self.small = ctk.CTkFont(ui, 12)
        self.log = ctk.CTkFont("Cascadia Mono", 11)


@lru_cache(maxsize=None)
def _glyph(char: str, color: str, px: int) -> Image.Image:
    fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for name in _ICON_FONTS:
        try:
            font = ImageFont.truetype(os.path.join(fonts_dir, name), px)
            break
        except OSError:
            continue
    else:
        return Image.new("RGBA", (px, px))
    img = Image.new("RGBA", (px, px))
    ImageDraw.Draw(img).text((px / 2, px / 2), char, font=font, fill=color, anchor="mm")
    return img


def icon(name: str, color: str = "ink", size: int = 16) -> ctk.CTkImage:
    light, dark = C[color]
    px = size * 3  # oversample so it stays crisp at 125-200% display scaling
    return ctk.CTkImage(_glyph(ICONS[name], light, px), _glyph(ICONS[name], dark, px), (size, size))


# ── Widget styles ────────────────────────────────────────────────────────────

def panel(master, **kw) -> ctk.CTkFrame:
    return ctk.CTkFrame(master, fg_color=C["surface"], corner_radius=14,
                        border_width=1, border_color=C["line"], **kw)


def card(master, **kw) -> ctk.CTkFrame:
    return ctk.CTkFrame(master, fg_color=C["card"], corner_radius=12, **kw)


def primary_button(master, text, command, fonts, icon_name=None, **kw) -> ctk.CTkButton:
    style = dict(font=fonts.button, height=38, corner_radius=8, fg_color=C["accent"],
                 hover_color=C["accent_hi"], text_color=C["on_accent"],
                 text_color_disabled=C["disabled"], compound="left",
                 image=icon(icon_name, "on_accent", 14) if icon_name else None)
    return ctk.CTkButton(master, text=text, command=command, **{**style, **kw})


def quiet_button(master, text, command, fonts, icon_name=None, color="ink", **kw) -> ctk.CTkButton:
    """Low-emphasis button: no fill until hovered."""
    style = dict(font=fonts.body, height=34, corner_radius=8, fg_color="transparent",
                 hover_color=C["track"], text_color=C[color], text_color_disabled=C["disabled"],
                 compound="left", image=icon(icon_name, color, 15) if icon_name else None)
    return ctk.CTkButton(master, text=text, command=command, **{**style, **kw})


def segmented(master, values, fonts, command=None, height=34) -> ctk.CTkSegmentedButton:
    return ctk.CTkSegmentedButton(
        master, values=values, command=command, font=fonts.body, height=height, corner_radius=8,
        fg_color=C["track"], selected_color=C["surface"], selected_hover_color=C["surface"],
        unselected_color=C["track"], unselected_hover_color=C["line"],
        text_color=C["ink"], text_color_disabled=C["disabled"])


class Pill(ctk.CTkLabel):
    """Small rounded status label, e.g. "Done" or "Running"."""
    TONES = {"done": ("done_bg", "done"), "accent": ("accent_bg", "accent"),
             "warn": ("warn_bg", "warn"), "muted": ("track", "muted")}

    def __init__(self, master, fonts):
        super().__init__(master, text="", font=fonts.small, height=22, corner_radius=11)

    def show(self, text: str, tone: str = "muted"):
        bg, fg = self.TONES[tone]
        self.configure(text=f"  {text}  ", fg_color=C[bg], text_color=C[fg])
