"""Pause menu: resume, settings and quit, driven by mouse, keyboard or gamepad.

Spec:
  kind: ui
  frame: 1280 x 720
  panels: one, centred: a title, three buttons, then settings: two sliders and two toggles,
          and a line of navigation help
  names: resume, restart, quit (buttons); music_volume, sfx_volume (sliders 0..1);
         invert_look, show_hints (toggles); title
  type: title 34 px, controls 20 px, help 14 px
  size: every button at least 260 px wide and 40 px high (easy to hit with a mouse; the
        engine's navigation moves focus between them with the d-pad or arrows)
  use: hidden with Ui.set_visible until the player pauses; focus_first on open; back closes it
  limits: no scrolling or wrapping in Cinder 0.1.1, so everything fits one column
"""
from cadkit.game.ui import *

KIND = "ui"
DESCRIPTION = "pause menu: resume, restart, quit, volume and options"
PARAMS = dict(title="PAUSED")
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["ui", "menu", "pause"])

THEME = Theme(font_size=20, text=(238, 232, 220, 255), panel=(16, 14, 12, 232), control=(58, 50, 44, 255),
              control_hot=(84, 72, 60, 255), control_active=(110, 94, 76, 255), accent=(226, 150, 62, 255),
              focus=(255, 214, 120, 255), padding=12.0, gap=8.0)
BUTTONS = ("resume", "restart", "quit")


def checks(p):
    return [has("title", "label")] + [has(b, "button") for b in BUTTONS] + \
           [node_at_least(b, 260, 40) for b in BUTTONS] + \
           [has("music_volume", "slider"), has("sfx_volume", "slider"), has("invert_look", "toggle"),
            has("show_hints", "toggle"),
            custom("one column, centred", lambda ctx: (
                ctx.rect("menu") is not None and abs(ctx.rect("menu")["x"] + ctx.rect("menu")["w"] / 2 - 640) < 2,
                "the menu panel is centred on the frame")),
            custom("buttons are one width", lambda ctx: (
                len({round(ctx.rect(b)["w"]) for b in BUTTONS}) == 1,
                "resume, restart and quit are the same width: " + str(round(ctx.rect("resume")["w"])) + " px"))]


def build(p):
    ui = Ui(THEME)
    menu = ui.root("centre", "menu", align=ALIGN["stretch"], padding=28.0)
    ui.label(menu, p.title, name="title", size=34, color=(226, 150, 62, 255))
    for name, text in zip(BUTTONS, ("Resume", "Restart level", "Quit to title")):
        ui.button(menu, text, name=name, min_size=(260, 44))
    ui.label(menu, "SETTINGS", size=15, color=(170, 162, 148, 255))
    ui.slider(menu, "Music", 0.7, name="music_volume")
    ui.slider(menu, "Effects", 0.9, name="sfx_volume")
    ui.toggle(menu, "Invert look", False, name="invert_look")
    ui.toggle(menu, "Show hints", True, name="show_hints")
    ui.label(menu, "arrows / d-pad move    Enter / A select    Esc / B back", size=14, color=(150, 144, 132, 255))
    return UiSet(ui)
