"""Cinder probe: asks the Cinder engine questions the world kit cannot answer.

Built against the engine (it is not part of it) by `cad game probe build`. Two modes:

    cinder-probe ui <document.txt> <out.png> [font.ttf]
        Loads a UI document with the engine's own `Ui.from_text`, lays it out in a 1280 x 720
        headless frame, draws it, saves the frame, and prints one JSON object: every node's
        kind, name, text and rectangle, and the engine's own `to_text` of what it read (the
        round trip). With a font path, the interface is drawn in that font.

    cinder-probe font <font.ttf> <out.png>
        Parses a font through the engine's shim (stb_truetype), bakes its atlas at 24 pixels,
        and draws a line of sample text in it; prints the glyph count, atlas size and widths.

A document the engine rejects ends the program with the engine's own error on stderr.
"""
from std.sys import argv, exit

from cinder.app import App, AppConfig, Game
from cinder.core.fs import read_text
from cinder.core.image import save_png
from cinder.kit import JsonWriter
from cinder.ui import Font, FontCache, Ui, UiAnchor


struct ProbeGame(Game):
    """Puts the document's tree in `App.ui`, or builds a one-label tree for the font mode."""

    var document: String
    var sample: String
    var font_path: String

    def __init__(out self, document: String, sample: String, font_path: String):
        self.document = document
        self.sample = sample
        self.font_path = font_path

    def start(mut self, mut app: App) raises:
        if self.font_path.byte_length() > 0:
            # The UI renderer uploads a glyph atlas the first time a size is drawn and never again,
            # so the font must be in place before anything is drawn: make the renderer now and
            # give it the font under test while its atlas list is still empty.
            app._ensure_ui_renderer()
            var font = Font.from_file(app.lib.ptr(), self.font_path)
            app.ui_renderer.value().fonts = FontCache(font^)
        if self.document.byte_length() > 0:
            app.ui = Ui.from_text(self.document)
        else:
            var root = app.ui.root(UiAnchor.centre(), String("sample"))
            var a = app.ui.label(root, self.sample)
            app.ui.nodes[a].font_size = 48
            var b = app.ui.label(root, self.sample)
            app.ui.nodes[b].font_size = 24
            var c = app.ui.button(root, String("PLAY 0123456789"))
            app.ui.nodes[c].font_size = 18

    def fixed_update(mut self, mut app: App, dt: Float32) raises:
        return

    def update(mut self, mut app: App, dt: Float32) raises:
        return

    def draw_ui(mut self, mut app: App) raises:
        return


def _run(document: String, sample: String, png: String, font_path: String) raises:
    var config = AppConfig(String("cinder probe"), 1280, 720, True)
    config.audio = False
    config.render.msaa = 1
    config.debug_ui = False
    var app = App(config^)
    var game = ProbeGame(document, sample, font_path)
    _ = app.run_frame(game, 1.0 / 60.0)
    var w = JsonWriter()
    w.begin_object()
    if font_path.byte_length() > 0:
        # Measured on a second copy of the font, so the report does not depend on what was drawn.
        var font = Font.from_file(app.lib.ptr(), font_path)
        var atlas = font.bake(24)
        w.begin_object(String("font"))
        w.integer(String("glyphs"), len(atlas.glyphs))
        w.integer(String("atlas_width"), atlas.width)
        w.integer(String("atlas_height"), atlas.height)
        w.number(String("line_height"), Float64(atlas.line_height()))
        w.number(String("sample_width"), Float64(atlas.text_width(String("HELLO 0123"))))
        w.end_object()
    _ = app.run_frame(game, 1.0 / 60.0)
    _ = app.run_frame(game, 1.0 / 60.0)
    save_png(app.lib.ptr(), png, app.read_frame())
    w.boolean(String("ok"), True)
    w.integer(String("gpu_errors"), app.gpu_error_count())
    w.integer(String("width"), 1280)
    w.integer(String("height"), 720)
    w.begin_array(String("nodes"))
    for i in range(len(app.ui.nodes)):
        var r = app.ui.rect(i)
        w.begin_object()
        w.integer(String("id"), i)
        w.string(String("kind"), app.ui.nodes[i].kind.name())
        w.string(String("name"), app.ui.nodes[i].name)
        w.string(String("text"), app.ui.nodes[i].text)
        w.boolean(String("visible"), app.ui.nodes[i].visible)
        w.number(String("x"), Float64(r.x))
        w.number(String("y"), Float64(r.y))
        w.number(String("w"), Float64(r.w))
        w.number(String("h"), Float64(r.h))
        w.end_object()
    w.end_array()
    w.string(String("roundtrip"), app.ui.to_text())
    w.end_object()
    print(w.text)
    _ = game^
    _ = app^


def main() raises:
    var raw = argv()
    var args = List[String]()
    for i in range(1, len(raw)):
        args.append(String(raw[i]))
    if len(args) < 3:
        print("usage: cinder-probe ui <document.txt> <out.png> [font.ttf] | cinder-probe font <font.ttf> <out.png>")
        exit(2)
    if args[0] == "ui":
        var font = String()
        if len(args) > 3:
            font = args[3]
        _run(read_text(args[1]), String(), args[2], font)
    elif args[0] == "font":
        _run(String(), String("THE QUICK BROWN FOX 0123456789"), args[2], args[1])
    else:
        print("unknown mode")
        exit(2)
