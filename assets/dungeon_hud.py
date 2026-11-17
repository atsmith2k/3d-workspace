"""Dungeon HUD: what the player sees while playing the Dungeon Kit level.

Spec:
  kind: ui
  frame: 1280 x 720
  panels: status (top left): gem count, key state, health as a slider used as a bar;
          objective (top centre): one line telling the player what to do next;
          hint (bottom centre): the control prompt, small and dim
  names: gems, keys, health, objective, hint (game code finds and updates these)
  type: labels at 20 px, the objective at 22 px, the hint at 15 px; warm accent for the bar
  use: built once in Game.start; set_text on gems, keys and objective as the game changes
  limits: Cinder 0.1.1 draws no images, so counts are words, not icons (icons are built ahead
          in hud_icons); a slider stands in for a health bar
"""
from cadkit.game.ui import *

KIND = "ui"
DESCRIPTION = "in-game HUD: gems, key, health, objective, control hint"
PARAMS = dict(gems_total=3)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["ui", "hud"])

THEME = Theme(font_size=20, text=(238, 232, 220, 255), panel=(16, 14, 12, 190), control=(58, 50, 44, 255),
              control_hot=(84, 72, 60, 255), control_active=(110, 94, 76, 255), accent=(226, 150, 62, 255),
              focus=(255, 214, 120, 255), padding=12.0, gap=6.0)


def checks(p):
    return [has("gems", "label"), has("keys", "label"), has("health", "slider"), has("objective", "label"),
            has("hint", "label"),
            custom("corners stay clear", lambda ctx: (
                ctx.rect("status") is not None and ctx.rect("status")["w"] < 360 and ctx.rect("status")["h"] < 160,
                "the status panel is under 360 x 160 px, a small part of the view"))]


def build(p):
    ui = Ui(THEME)
    status = ui.root("top_left", "status", offset=(16, 16))
    ui.label(status, f"GEMS  0 / {p.gems_total}", name="gems")
    ui.label(status, "KEY  none", name="keys", color=(200, 190, 170, 255))
    ui.slider(status, "HEALTH", 0.8, name="health")
    objective = ui.root("top", "objective_panel", offset=(0, 16))
    ui.label(objective, "Find the three gems and open the vault", name="objective", size=22)
    hint = ui.root("bottom", "hint_panel", offset=(0, 14), background=(16, 14, 12, 120))
    ui.label(hint, "WASD move    SPACE jump    ESC pause", name="hint", size=15, color=(190, 184, 170, 255))
    return UiSet(ui, notes="Icons for the counts are in hud_icons (built ahead: Cinder draws no UI images yet).")
