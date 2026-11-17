"""Writing Cinder world files (`cinder-world 1`) from Python.

    w = World("Dungeon demo")
    w.environment(exposure=0.9, ambient=0.4)
    w.add("sun", light=dict(kind="sun", direction=(-0.4, -1, -0.3), intensity=1.5, shadows=True))
    w.place("dungeon_wall", at=(0, 0, -5), yaw=90)             # a pack asset, standing in place
    w.place("gem", at=(0, 0, -3), spin=dict(speed=120), pickup=dict(points=10))
    text = w.text()

`place` knows each asset from the pack manifest: where its file is, how high its origin
sits when it stands on a floor at Y=0 (`rest_y`), and its body and collider. `at` is the
point on the floor under the asset; its Y adds to `rest_y`.
"""
from dataclasses import dataclass, field


def value(v):
    """One world-file value: number, bool, "string", [list] of numbers, or [names]."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, (list, tuple)):
        if v and all(isinstance(x, str) for x in v):
            return "[" + ",".join(v) + "]"                       # entity names
        return "[" + ",".join(f"{float(x):.5g}" for x in v) + "]"
    return f"{float(v):.5g}"


@dataclass
class World:
    title: str = "world"
    assets: dict = field(default_factory=dict)       # name -> manifest entry (file, rest_y, engine_use)
    settings: list = field(default_factory=list)
    entities: list = field(default_factory=list)
    counts: dict = field(default_factory=dict)

    def __post_init__(self):
        self.settings.append(("world", dict(title=self.title)))

    def environment(self, **fields):
        self.settings.append(("environment", fields))
        return self

    def add(self, name, **components):
        """An entity with the given components, each a dict of fields (or True for none)."""
        if any(e[0] == name for e in self.entities):
            raise ValueError(f"entity name '{name}' is used twice")
        self.entities.append((name, components))
        return name

    def place(self, asset, at=(0, 0, 0), yaw=0.0, name=None, body=True, **components):
        """Stand a pack asset at a floor point, turned `yaw` degrees about Y. body=False leaves
        it non-solid; a str picks the motion ("static", "dynamic", "kinematic")."""
        a = self.assets[asset]
        if name is None:
            n = self.counts[asset] = self.counts.get(asset, 0) + 1
            name = asset if n == 1 and asset not in [e[0] for e in self.entities] else f"{asset}_{n}"
        comps = dict(transform=dict(position=(at[0], at[1] + a.get("rest_y", 0.0), at[2])),
                     model=dict(path=a["file"]))
        if yaw:
            comps["transform"]["rotation"] = (0, yaw, 0)
        use = a.get("engine_use", {})
        if body and (use.get("body") or isinstance(body, str)):
            comps["body"] = dict(motion=body if isinstance(body, str) else use["body"],
                                 collider=use.get("collider", "auto"))
        comps.update(components)
        return self.add(name, **comps)

    def text(self):
        lines = ["cinder-world 1"]
        for comp, fields_ in self.settings:
            lines.append(comp + "".join(f" {k}={value(v)}" for k, v in fields_.items()))
        for name, comps in self.entities:
            lines.append(f"entity {name}")
            for comp, fields_ in comps.items():
                if fields_ is True:
                    fields_ = {}
                lines.append(f"  {comp}" + "".join(f" {k}={value(v)}" for k, v in fields_.items()))
        return "\n".join(lines) + "\n"
