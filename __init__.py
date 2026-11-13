"""
MingLayoutCaption — drop-in replacement for the 339:* regex/loop subgraph.

Turns the Ideogram JSON prompt (node 93) + the bounding boxes (node 91, output 2)
into Ming's Figma-style caption, the same string 339:249 used to build, without
string round-trips or regex parsing.

Injection points (all optional, empty = off):
  boxes_json        JSON array that replaces the linked boxes. Accepts either
                    91's editor_state format ({x, y, width, height, metadata})
                    in pixels, or the bbox format ({"bbox": [ymin, xmin, ymax, xmax]}
                    on a 0-1000 scale).
  ideogram_json     JSON object that replaces the linked Ideogram dict.
  caption_override  Full caption string; returned as-is, upstream not evaluated.

Lazy inputs: when an override is set, the linked input it replaces is never
requested, so the upstream node is skipped (unless something else needs it).

Install: copy this folder into ComfyUI/custom_nodes/ and restart.
"""

import json
import math


class _AnyType(str):
    """Socket type that accepts any link (classic ComfyUI wildcard trick)."""
    def __ne__(self, other):
        return False


ANY = _AnyType("*")

BASE_RELATION = "Base layer: fills the whole canvas, behind every other layer."
LAYER_RELATION = "Sits above the layers listed before it."
BASE_COORDS = "cx: 0.500, cy: 0.500, w: 1.000, h: 1.000"


# ---------- helpers ----------

def _load(value):
    """Accept a dict/list, a JSON string, or a ComfyUI {"__value__": ...} wrapper."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        value = json.loads(value)
    if isinstance(value, dict) and set(value.keys()) == {"__value__"}:
        value = value["__value__"]
    return value


def _find(d, *keys):
    """Top-level key first, then breadth-first through nested dicts (not lists,
    so per-element fields in the Ideogram dict never shadow the top-level ones)."""
    queue = [d]
    while queue:
        cur = queue.pop(0)
        if not isinstance(cur, dict):
            continue
        for k in keys:
            v = cur.get(k)
            if v not in (None, "") and not isinstance(v, dict):
                return v
        queue.extend(v for v in cur.values() if isinstance(v, dict))
    return None


def _unwrap(v):
    if isinstance(v, dict) and "__value__" in v:
        return v["__value__"]
    return v


def _normalize_box(b, W, H):
    """Return (ymin, xmin, ymax, xmax) on 0-1000, text, desc, palette."""
    b = _load(b) if isinstance(b, str) else b
    md = b.get("metadata") if isinstance(b.get("metadata"), dict) else b

    bbox = b.get("bbox") or b.get("box_2d")
    if bbox is not None:
        y1, x1, y2, x2 = (float(v) for v in bbox)
    elif "x" in b:
        x, y = float(b["x"]), float(b["y"])
        w, h = float(b["width"]), float(b["height"])
        # same integer grid 91 emits, so captions stay identical
        x1, x2 = round(x / W * 1000), round((x + w) / W * 1000)
        y1, y2 = round(y / H * 1000), round((y + h) / H * 1000)
    else:
        raise ValueError(f"box has neither 'bbox' nor x/y/width/height: {b!r}")

    clamp = lambda v: max(0.0, min(1000.0, v))
    y1, x1, y2, x2 = clamp(y1), clamp(x1), clamp(y2), clamp(x2)
    if y2 < y1:
        y1, y2 = y2, y1
    if x2 < x1:
        x1, x2 = x2, x1

    palette = _unwrap(md.get("color_palette", md.get("palette", []))) or []
    return (y1, x1, y2, x2), str(md.get("text", "") or ""), str(md.get("desc", "") or ""), list(palette)


def _dump(obj):
    return json.dumps(obj, ensure_ascii=False)


def build_caption(ideogram, boxes, width, height):
    """Pure function — importable for tests without ComfyUI."""
    d = _load(ideogram) or {}
    bx = _load(boxes) or []
    W, H = int(width), int(height)

    g = math.gcd(W, H) or 1
    medium = _find(d, "medium") or ""
    style = _find(d, "art_style", "photo") or ""
    aesthetics = _find(d, "aesthetics") or ""
    canvas = {
        "aspect_ratio": f"{W // g}:{H // g}, {W} × {H} px",
        "ambient_lighting": _find(d, "lighting") or "",
        "image_style": f"{medium}; {style}; aesthetics: {aesthetics}",
    }

    base_palette = _unwrap(d.get("color_palette")) or _unwrap(_find(d, "color_palette")) or []
    hld = _find(d, "high_level_description") or ""
    bg = _find(d, "background") or ""
    layers = [{
        "description": f"{hld} {bg}",
        "coordinates": BASE_COORDS,
        "hierarchy_and_relation": BASE_RELATION,
        "color_specs": list(base_palette),
    }]

    norm = []
    for b in bx:
        (y1, x1, y2, x2), text, desc, palette = _normalize_box(b, W, H)
        if x2 - x1 <= 0 or y2 - y1 <= 0:
            continue  # zero-area box: nothing to place
        norm.append({"bbox": [y1, x1, y2, x2], "text": text, "desc": desc, "color_palette": palette})
        prefix = f'Text layer reading "{text}". ' if text else ""
        layers.append({
            "description": prefix + desc,
            "coordinates": (f"cx: {(x1 + x2) / 2000:.3f}, cy: {(y1 + y2) / 2000:.3f}, "
                            f"w: {(x2 - x1) / 1000:.3f}, h: {(y2 - y1) / 1000:.3f}"),
            "hierarchy_and_relation": LAYER_RELATION,
            "color_specs": palette,
        })

    body = ",\n".join("  " + _dump(layer) for layer in layers)
    caption = f'{{"canvas_settings": {_dump(canvas)}, "layers": [\n{body}\n]}}'
    return caption, norm


# ---------- ComfyUI node ----------

class MingLayoutCaption:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"forceInput": True}),
                "height": ("INT", {"forceInput": True}),
            },
            "optional": {
                "boxes": (ANY, {"lazy": True}),
                "ideogram": (ANY, {"lazy": True}),
                "boxes_json": ("STRING", {"multiline": True, "default": ""}),
                "ideogram_json": ("STRING", {"multiline": True, "default": ""}),
                "caption_override": ("STRING", {"multiline": True, "default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("caption", "boxes_normalized", "layer_count")
    FUNCTION = "build"
    CATEGORY = "ming"

    def check_lazy_status(self, width=None, height=None, boxes=None, ideogram=None,
                          boxes_json="", ideogram_json="", caption_override=""):
        if (caption_override or "").strip():
            return []
        need = []
        if not (boxes_json or "").strip() and boxes is None:
            need.append("boxes")
        if not (ideogram_json or "").strip() and ideogram is None:
            need.append("ideogram")
        return need

    def build(self, width, height, boxes=None, ideogram=None,
              boxes_json="", ideogram_json="", caption_override=""):
        if (caption_override or "").strip():
            return (caption_override, "[]", 0)
        src_boxes = boxes_json if (boxes_json or "").strip() else boxes
        src_ideo = ideogram_json if (ideogram_json or "").strip() else ideogram
        caption, norm = build_caption(src_ideo, src_boxes, width, height)
        return (caption, _dump(norm), len(norm) + 1)


NODE_CLASS_MAPPINGS = {"MingLayoutCaption": MingLayoutCaption}
NODE_DISPLAY_NAME_MAPPINGS = {"MingLayoutCaption": "Ming Layout Caption (boxes + Ideogram → Ming)"}
