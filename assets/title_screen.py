"""Title screen: the game's name and a start menu, set in Block Caps.

Spec:
  kind: ui
  frame: 1280 x 720
  font: block_caps (the whole interface: cinder.ui has one font per renderer)
  panels: title (upper centre): the game's name at 72 px and a tag line at 22 px on a dark backing
          (the scene behind a title is unknown: pale text needs its own ground);
          menu (centre, below): four buttons; footer (bottom): version and credit, small
  names: title, tagline, play, continue_game, options, quit, footer
  size: buttons at least 300 x 48 px, all one width
  type: capitals throughout (the font has no lowercase); digits and punctuation in the footer
  use: the first screen; focus_first on `play`; `continue_game` is disabled until a save exists
"""
from cadkit.game.ui import *

KIND = "ui"
DESCRIPTION = "title screen and start menu in Block Caps"
PARAMS = dict(title="EMBER VAULT", tagline="THREE GEMS. ONE DOOR. NO MAP.")
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["ui", "menu", "title"])

THEME = Theme(font_size=24, text=(238, 232, 220, 255), panel=(16, 14, 12, 215), control=(58, 50, 44, 255),
              control_hot=(84, 72, 60, 255), control_active=(110, 94, 76, 255), accent=(226, 150, 62, 255),
              focus=(255, 214, 120, 255), padding=14.0, gap=10.0)
BUTTONS = (("play", "NEW GAME"), ("continue_game", "CONTINUE"), ("options", "OPTIONS"), ("quit", "QUIT"))


def checks(p):
    return [has("title", "label"), has("tagline", "label"), has("footer", "label")] + \
           [has(n, "button") for n, _ in BUTTONS] + [node_at_least(n, 300, 48) for n, _ in BUTTONS] + \
           [custom("title is the largest thing on screen", lambda ctx: (
               ctx.rect("title")["h"] >= 72 and ctx.rect("title")["w"] > 2 * ctx.rect("play")["w"] * 0.6,
               f"title {ctx.rect('title')['w']:.0f} x {ctx.rect('title')['h']:.0f} px")),
            custom("title above menu", lambda ctx: (
                ctx.rect("title")["y"] + ctx.rect("title")["h"] < ctx.rect("play")["y"],
                "the title sits above the first button")),
            custom("text has a ground", lambda ctx: (
                all(ctx.ui[ctx.ui.find(n)]["background"][3] >= 120 for n in ("title_panel", "menu", "footer_panel")),
                "every panel that holds text has a backing of alpha 120 or more, so it reads on any scene")),
            custom("continue starts disabled", lambda ctx: (
                ctx.ui[ctx.ui.find("continue_game")]["enabled"] is False, "continue_game is disabled until a save exists"))]


def build(p):
    ui = Ui(THEME)
    head = ui.root("top", "title_panel", offset=(0, 86), background=(16, 14, 12, 170), align=ALIGN["centre"],
                   gap=14.0, padding=22.0)
    ui.label(head, p.title, name="title", size=72, color=(226, 150, 62, 255))
    ui.label(head, p.tagline, name="tagline", size=22, color=(200, 190, 170, 255))
    menu = ui.root("centre", "menu", offset=(0, 90), align=ALIGN["stretch"], padding=22.0)
    for name, text in BUTTONS:
        ui.button(menu, text, name=name, min_size=(300, 50), enabled=(name != "continue_game"))
    foot = ui.root("bottom", "footer_panel", offset=(0, 14), background=(16, 14, 12, 170))
    ui.label(foot, "V0.1  *  BUILT ON CINDER  *  [ENTER] SELECT", name="footer", size=16, color=(150, 144, 132, 255))
    return UiSet(ui, font="block_caps")
