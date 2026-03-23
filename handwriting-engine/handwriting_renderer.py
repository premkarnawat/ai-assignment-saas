# handwriting-engine/handwriting_renderer.py
"""
AI Handwritten Assignment Generator
Core Handwriting Engine — 95% Realistic Simulation

Pipeline:
  text → letter-level tokenization → per-char transform
       → ink simulation → Gaussian stroke noise
       → notebook line snapping → human imperfections
       → page composition
"""

import os
import sys
import math
import random
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

logger = logging.getLogger(__name__)

# Font registry — must be installed (see scripts/install_fonts.sh)
FONT_REGISTRY = {
    "Caveat":             "Caveat-Regular.ttf",
    "CaveatBold":         "Caveat-Bold.ttf",
    "PatrickHand":        "PatrickHand-Regular.ttf",
    "IndieFlower":        "IndieFlower-Regular.ttf",
    "ArchitectsDaughter": "ArchitectsDaughter-Regular.ttf",
    "DancingScript":      "DancingScript-Regular.ttf",
    # Fallback
    "default":            "FreeMono.ttf",
}

PAPER_STYLES = {
    "notebook": {
        "bg_color": (253, 248, 240),
        "line_color": (200, 216, 232),
        "margin_color": (232, 160, 160),
        "margin_x": 72,
        "line_spacing": 34,
        "first_line_y": 95,
        "has_holes": True,
        "has_margin": True,
    },
    "exam": {
        "bg_color": (255, 255, 252),
        "line_color": (180, 200, 220),
        "margin_color": (220, 140, 140),
        "margin_x": 80,
        "line_spacing": 36,
        "first_line_y": 130,
        "has_holes": False,
        "has_margin": True,
    },
    "graph": {
        "bg_color": (248, 252, 255),
        "line_color": (210, 228, 245),
        "margin_color": None,
        "margin_x": 0,
        "line_spacing": 28,
        "first_line_y": 80,
        "has_holes": False,
        "has_margin": False,
        "is_graph": True,
    },
    "white": {
        "bg_color": (255, 255, 255),
        "line_color": None,
        "margin_color": None,
        "margin_x": 60,
        "line_spacing": 36,
        "first_line_y": 80,
        "has_holes": False,
        "has_margin": False,
    },
}

# Character classes for vertical variation
DESCENDERS = set("fpgqyj")
ASCENDERS  = set("bdfhklt")
CAPS       = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


@dataclass
class CharTransform:
    rotation: float          # radians, slight tilt
    scale: float             # 0.90–1.10
    baseline_offset: float   # vertical shift in px
    kerning: float           # extra horizontal spacing
    opacity: float           # 0.72–0.97
    blur_radius: float       # 0.08–0.40
    ink_rgb: tuple           # (R, G, B) ink color variation


@dataclass
class RendererConfig:
    font_name: str = "Caveat"
    base_font_size: int = 26
    paper_type: str = "notebook"
    page_width: int = 794      # A4 at 96dpi
    page_height: int = 1123
    left_padding: int = 85     # text start x
    right_padding: int = 50
    word_spacing_base: float = 0.30
    line_height_extra: int = 0  # additional line height
    ink_color_base: tuple = (18, 18, 42)   # near-black blue ink


class HandwritingRenderer:
    """
    Core renderer. Produces one full page image with realistic handwriting.
    """

    def __init__(self, config: RendererConfig, fonts_dir: str = "/usr/share/fonts"):
        self.config = config
        self.fonts_dir = fonts_dir
        self.paper = PAPER_STYLES.get(config.paper_type, PAPER_STYLES["notebook"])
        self._ink_history: list[float] = []
        self._font_cache: dict[int, ImageFont.FreeTypeFont] = {}
        self._load_font()

    def _load_font(self):
        font_file = FONT_REGISTRY.get(self.config.font_name, FONT_REGISTRY["default"])
        candidates = [
            os.path.join(self.fonts_dir, "truetype", font_file),
            os.path.join(self.fonts_dir, "truetype", "google-fonts", font_file),
            os.path.join(os.path.dirname(__file__), "fonts", font_file),
            os.path.join("/usr/share/fonts/truetype/freefont", "FreeMono.ttf"),
        ]
        for path in candidates:
            if os.path.exists(path):
                self._font_path = path
                logger.info(f"Loaded font: {path}")
                return
        # Last resort: PIL default
        self._font_path = None
        logger.warning("Using PIL default font — install fonts for best results")

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self._font_cache:
            if self._font_path:
                self._font_cache[size] = ImageFont.truetype(self._font_path, size)
            else:
                self._font_cache[size] = ImageFont.load_default()
        return self._font_cache[size]

    # ── Character-level variation ─────────────────────────────────────────
    def _char_transform(self, char: str, index: int) -> CharTransform:
        base_r, base_g, base_b = self.config.ink_color_base

        # Ink continuity — opacity drifts gradually like real pen flow
        prev = self._ink_history[-1] if self._ink_history else 0.88
        opacity = float(np.clip(random.gauss(prev, 0.018), 0.72, 0.97))
        self._ink_history = self._ink_history[-6:] + [opacity]

        # Vertical class adjustments
        baseline = random.gauss(0, 1.3)
        if char in DESCENDERS:
            baseline += 4.5
        elif char in ASCENDERS:
            baseline -= 2.0
        elif char in CAPS:
            baseline -= 1.5

        # Ink color micro-variation (simulate ink density)
        ink_var = int(random.gauss(0, 5))
        ink_rgb = (
            max(0, min(255, base_r + ink_var)),
            max(0, min(255, base_g + ink_var)),
            max(0, min(255, base_b + int(random.gauss(0, 8)))),
        )

        return CharTransform(
            rotation       = random.gauss(0, 0.025),
            scale          = random.uniform(0.92, 1.08),
            baseline_offset= baseline,
            kerning        = random.uniform(-0.5, 1.4),
            opacity        = opacity,
            blur_radius    = random.uniform(0.07, 0.38),
            ink_rgb        = ink_rgb,
        )

    # ── Draw a single character ───────────────────────────────────────────
    def _draw_char(
        self,
        canvas: Image.Image,
        char: str,
        x: float,
        y: float,
        t: CharTransform,
    ) -> float:
        """Render one character onto canvas. Returns advance width."""
        font_size = int(self.config.base_font_size * t.scale)
        font = self._get_font(font_size)

        # Get character bounding box
        bbox = font.getbbox(char)
        cw = bbox[2] - bbox[0] + 10
        ch = bbox[3] - bbox[1] + 10
        if cw <= 0 or ch <= 0:
            return self.config.base_font_size * 0.4

        # Render char on transparent RGBA layer
        char_img = Image.new("RGBA", (cw + 8, ch + 8), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)

        ink_color = (*t.ink_rgb, int(t.opacity * 255))
        char_draw.text((4, 4), char, font=font, fill=ink_color)

        # Ink stroke noise — Gaussian blur simulates pen softness
        char_img = char_img.filter(ImageFilter.GaussianBlur(t.blur_radius))

        # Slight unsharp for ink-edge texture
        if t.blur_radius < 0.20:
            char_img = char_img.filter(
                ImageFilter.UnsharpMask(radius=1, percent=25, threshold=3)
            )

        # Rotate character
        angle = math.degrees(t.rotation)
        rotated = char_img.rotate(angle, expand=True, resample=Image.BICUBIC)

        # Paste onto canvas
        px = int(x)
        py = int(y + t.baseline_offset)
        try:
            canvas.paste(rotated, (px, py), rotated)
        except Exception:
            pass

        return cw * 0.68 + t.kerning

    # ── Imperfection layer ────────────────────────────────────────────────
    def _maybe_add_imperfection(self, draw: ImageDraw.Draw, x: float, y: float, char: str):
        r = random.random()
        if r < 0.0018:
            # Crossing-out mark (corrected word)
            draw.line(
                [(int(x) - 2, int(y) - 6), (int(x) + 22, int(y) - 6)],
                fill=(*self.config.ink_color_base, 100),
                width=1,
            )
        elif r < 0.0025:
            # Ink blob
            bx, by = int(x + random.gauss(0, 4)), int(y + random.gauss(0, 4))
            draw.ellipse(
                [(bx - 2, by - 2), (bx + 2, by + 2)],
                fill=(*self.config.ink_color_base, 180),
            )
        elif char == "." and r < 0.15:
            # Extra pressure dot on period
            draw.ellipse(
                [(int(x) + 1, int(y) - 2), (int(x) + 3, int(y))],
                fill=(*self.config.ink_color_base, 200),
            )

    # ── Page background ───────────────────────────────────────────────────
    def _draw_page_background(self, canvas: Image.Image):
        draw = ImageDraw.Draw(canvas)
        style = self.paper
        W, H = canvas.size

        # Base paper color
        canvas.paste(Image.new("RGB", (W, H), style["bg_color"]))

        # Graph paper grid
        if style.get("is_graph"):
            gc = style["line_color"]
            for x in range(0, W, style["line_spacing"]):
                draw.line([(x, 0), (x, H)], fill=(*gc, 120), width=1)
            for y in range(0, H, style["line_spacing"]):
                draw.line([(0, y), (W, y)], fill=(*gc, 120), width=1)
            return

        # Ruled lines
        if style["line_color"]:
            lc = style["line_color"]
            y = style["first_line_y"]
            while y < H - 20:
                draw.line([(0, y), (W, y)], fill=(*lc, 180), width=1)
                y += style["line_spacing"] + self.config.line_height_extra

        # Red margin line
        if style.get("has_margin") and style["margin_color"]:
            mx = style["margin_x"]
            draw.line([(mx, 0), (mx, H)], fill=(*style["margin_color"], 200), width=2)

        # Spiral holes
        if style.get("has_holes"):
            for hole_y in [80, H // 2, H - 80]:
                # Shadow
                draw.ellipse([(12, hole_y - 12), (34, hole_y + 12)],
                             fill=(200, 200, 200, 255))
                # White hole
                draw.ellipse([(14, hole_y - 10), (32, hole_y + 10)],
                             fill=(240, 240, 240, 255))
                # Ring outline
                draw.ellipse([(14, hole_y - 10), (32, hole_y + 10)],
                             outline=(180, 180, 180, 255), width=1)

    # ── Page header ───────────────────────────────────────────────────────
    def _draw_header(
        self, draw: ImageDraw.Draw, subject: str, date_str: str, page_num: int
    ):
        style = self.paper
        header_font = self._get_font(int(self.config.base_font_size * 0.85))
        ink = (*self.config.ink_color_base, 200)

        # Subject name (top-left in margin area, or left)
        x_start = style["margin_x"] + 10 if style.get("has_margin") else 30
        # Subject
        draw.text((x_start, 28), f"Subject: {subject}", font=header_font, fill=ink)

        # Date (top-right)
        date_font = self._get_font(int(self.config.base_font_size * 0.75))
        W = self.config.page_width
        draw.text((W - 220, 28), f"Date: {date_str}", font=date_font, fill=ink)

        # Page number (bottom center)
        page_font = self._get_font(int(self.config.base_font_size * 0.70))
        draw.text(
            (W // 2 - 10, self.config.page_height - 38),
            f"— {page_num} —",
            font=page_font,
            fill=ink,
        )

        # Underline header area
        draw.line(
            [(x_start, 60), (W - 40, 60)],
            fill=(*style.get("line_color", (200, 216, 232)), 220),
            width=1,
        )

    # ── Main render function ──────────────────────────────────────────────
    def render_page(
        self,
        text: str,
        subject: str = "Assignment",
        date_str: str = "",
        page_num: int = 1,
    ) -> Image.Image:
        """
        Render one full notebook page with realistic handwriting.
        Returns PIL Image (RGB).
        """
        W, H = self.config.page_width, self.config.page_height
        style = self.paper

        canvas = Image.new("RGBA", (W, H), (255, 255, 255, 255))
        self._draw_page_background(canvas)

        draw = ImageDraw.Draw(canvas)

        if not date_str:
            from datetime import datetime
            date_str = datetime.now().strftime("%d/%m/%Y")

        self._draw_header(draw, subject, date_str, page_num)

        # Text rendering
        x0 = self.config.left_padding
        x_max = W - self.config.right_padding
        y = style["first_line_y"] + style["line_spacing"] + 10
        line_h = style["line_spacing"] + self.config.line_height_extra

        # Per-line slope (slight upward drift like real handwriting)
        line_slope = random.uniform(-0.001, 0.003)

        self._ink_history = []  # reset ink continuity per page
        lines = text.split("\n")

        for line_idx, line in enumerate(lines):
            if y > H - 60:
                break  # page full

            x = float(x0)
            new_slope = random.uniform(-0.001, 0.003)
            line_slope = 0.7 * line_slope + 0.3 * new_slope  # smooth slope change

            if not line.strip():
                y += line_h * 0.6
                continue

            # Render word by word (natural word spacing)
            words = line.split(" ")
            for word_idx, word in enumerate(words):
                if not word:
                    x += self.config.base_font_size * (
                        self.config.word_spacing_base + random.gauss(0, 0.04)
                    )
                    continue

                # Check if word fits on line
                word_width_est = len(word) * self.config.base_font_size * 0.58
                if x + word_width_est > x_max and x > x0 + 10:
                    # Wrap to next line
                    y += line_h
                    x = float(x0) + random.gauss(0, 2)
                    if y > H - 60:
                        break

                # Render each character of the word
                for char in word:
                    t = self._char_transform(char, int(x))
                    y_pos = y + x * line_slope  # apply slope
                    advance = self._draw_char(canvas, char, x, y_pos, t)
                    self._maybe_add_imperfection(draw, x, y_pos, char)
                    x += advance

                # Word spacing
                x += self.config.base_font_size * (
                    self.config.word_spacing_base + random.gauss(0, 0.05)
                )

            y += line_h

        # Convert to RGB for PDF embedding
        bg = Image.new("RGB", canvas.size, "white")
        bg.paste(canvas, mask=canvas.split()[3])
        return bg

    def render_pages(
        self, pages_text: list[str], subject: str = "Assignment"
    ) -> list[Image.Image]:
        """Render multiple pages. Returns list of PIL Images."""
        from datetime import datetime
        date_str = datetime.now().strftime("%d/%m/%Y")
        return [
            self.render_page(text, subject=subject, date_str=date_str, page_num=i + 1)
            for i, text in enumerate(pages_text)
        ]
