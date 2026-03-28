# handwriting-engine/handwriting_renderer.py
"""
AI Handwritten Assignment Generator
Core Handwriting Engine — 95% Realistic Simulation

Template matches real Indian assignment notebook:
  - A4 size page
  - Blue horizontal ruled lines
  - Red vertical margin line on left
  - Header: Name / Subject / Assignment No
  - No holes, no branding
  - Realistic handwriting with ink variation, slope, imperfections
"""

import os
import math
import random
import logging
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

logger = logging.getLogger(__name__)

# ── Font Registry ─────────────────────────────────────────────────────────────
FONT_REGISTRY = {
    "Caveat":             "Caveat-Regular.ttf",
    "CaveatBold":         "Caveat-Bold.ttf",
    "PatrickHand":        "PatrickHand-Regular.ttf",
    "IndieFlower":        "IndieFlower-Regular.ttf",
    "ArchitectsDaughter": "ArchitectsDaughter-Regular.ttf",
    "DancingScript":      "DancingScript-Regular.ttf",
    "default":            "FreeMono.ttf",
}

# ── Paper Style — Single notebook style matching your reference image ─────────
NOTEBOOK_STYLE = {
    "bg_color":     (253, 251, 245),   # Slightly warm off-white — real notebook
    "line_color":   (173, 208, 230),   # Blue ruled lines
    "margin_color": (210, 80,  80),    # Red margin line
    "margin_x":     148,               # Red line x position (px at 96dpi)
    "line_spacing": 34,                # Gap between ruled lines
    "first_line_y": 88,                # First ruled line y position
}

# ── Character classes for vertical variation ──────────────────────────────────
DESCENDERS = set("fpgqyj")
ASCENDERS  = set("bdfhklt")
CAPS       = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


@dataclass
class CharTransform:
    rotation:        float
    scale:           float
    baseline_offset: float
    kerning:         float
    opacity:         float
    blur_radius:     float
    ink_rgb:         tuple


@dataclass
class RendererConfig:
    font_name:          str   = "Caveat"
    base_font_size:     int   = 26
    paper_type:         str   = "notebook"
    page_width:         int   = 794       # A4 at 96 DPI
    page_height:        int   = 1123
    left_padding:       int   = 162       # Text starts just right of margin
    right_padding:      int   = 48
    word_spacing_base:  float = 0.30
    line_height_extra:  int   = 0
    ink_color_base:     tuple = field(default_factory=lambda: (18, 18, 42))


class HandwritingRenderer:
    """
    Renders realistic handwritten assignment pages in the style of
    Indian notebook assignments — blue lines, red margin, Name/Subject header.
    """

    def __init__(self, config: RendererConfig, fonts_dir: str = "/usr/share/fonts"):
        self.config    = config
        self.fonts_dir = fonts_dir
        self._ink_history:  list[float] = []
        self._font_cache:   dict[int, ImageFont.FreeTypeFont] = {}
        self._load_font()

    # ── Font loading ──────────────────────────────────────────────────────────
    def _load_font(self):
        font_file  = FONT_REGISTRY.get(self.config.font_name, FONT_REGISTRY["default"])
        candidates = [
            # Linux system fonts (Render server)
            os.path.join(self.fonts_dir, "truetype", font_file),
            os.path.join(self.fonts_dir, "truetype", "google-fonts", font_file),
            os.path.join("/usr/share/fonts/truetype/freefont", "FreeMono.ttf"),
            # Alongside this script
            os.path.join(os.path.dirname(__file__), "fonts", font_file),
            # macOS
            f"/Library/Fonts/{font_file}",
            f"/System/Library/Fonts/{font_file}",
            # Windows
            f"C:/Windows/Fonts/{font_file}",
        ]
        for path in candidates:
            if os.path.exists(path):
                self._font_path = path
                logger.info(f"Loaded font: {path}")
                return
        self._font_path = None
        logger.warning("No handwriting font found — install fonts for best results")

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self._font_cache:
            if self._font_path:
                self._font_cache[size] = ImageFont.truetype(self._font_path, size)
            else:
                try:
                    self._font_cache[size] = ImageFont.load_default(size=size)
                except Exception:
                    self._font_cache[size] = ImageFont.load_default()
        return self._font_cache[size]

    # ── Character-level variation (7-layer pipeline) ──────────────────────────
    def _char_transform(self, char: str, x_pos: int) -> CharTransform:
        base_r, base_g, base_b = self.config.ink_color_base

        # Layer 3 — Ink continuity (opacity drifts like real pen)
        prev    = self._ink_history[-1] if self._ink_history else 0.88
        opacity = float(np.clip(random.gauss(prev, 0.018), 0.72, 0.97))
        self._ink_history = self._ink_history[-6:] + [opacity]

        # Layer 5 — Baseline offset per character class
        baseline = random.gauss(0, 1.3)
        if char in DESCENDERS:
            baseline += 4.5
        elif char in ASCENDERS:
            baseline -= 2.0
        elif char in CAPS:
            baseline -= 1.5

        # Layer 3 — Ink color micro-variation
        ink_var = int(random.gauss(0, 5))
        ink_rgb = (
            max(0, min(255, base_r + ink_var)),
            max(0, min(255, base_g + ink_var)),
            max(0, min(255, base_b + int(random.gauss(0, 8)))),
        )

        return CharTransform(
            rotation        = random.gauss(0, 0.025),       # Layer 1
            scale           = random.uniform(0.92, 1.08),   # Layer 2
            baseline_offset = baseline,                      # Layer 5
            kerning         = random.uniform(-0.5, 1.4),    # Layer 1
            opacity         = opacity,                       # Layer 3
            blur_radius     = random.uniform(0.07, 0.38),   # Layer 4
            ink_rgb         = ink_rgb,                       # Layer 3
        )

    # ── Draw one character ────────────────────────────────────────────────────
    def _draw_char(
        self,
        canvas: Image.Image,
        char:   str,
        x:      float,
        y:      float,
        t:      CharTransform,
    ) -> float:
        """Render one character onto canvas. Returns advance width."""
        font_size = int(self.config.base_font_size * t.scale)
        font      = self._get_font(font_size)

        bbox = font.getbbox(char)
        cw   = bbox[2] - bbox[0] + 10
        ch   = bbox[3] - bbox[1] + 10
        if cw <= 0 or ch <= 0:
            return self.config.base_font_size * 0.4

        # Render char on transparent layer
        char_img  = Image.new("RGBA", (cw + 8, ch + 8), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)
        ink_color = (*t.ink_rgb, int(t.opacity * 255))
        char_draw.text((4, 4), char, font=font, fill=ink_color)

        # Layer 4 — Gaussian stroke noise (pen softness)
        char_img = char_img.filter(ImageFilter.GaussianBlur(t.blur_radius))
        if t.blur_radius < 0.20:
            char_img = char_img.filter(
                ImageFilter.UnsharpMask(radius=1, percent=25, threshold=3)
            )

        # Layer 1 — Rotation
        angle   = math.degrees(t.rotation)
        rotated = char_img.rotate(angle, expand=True, resample=Image.BICUBIC)

        px, py = int(x), int(y + t.baseline_offset)
        try:
            canvas.paste(rotated, (px, py), rotated)
        except Exception:
            pass

        return cw * 0.68 + t.kerning

    # ── Layer 6 — Human imperfections ────────────────────────────────────────
    def _maybe_add_imperfection(
        self, draw: ImageDraw.Draw, x: float, y: float, char: str
    ):
        r = random.random()
        if r < 0.0018:
            # Correction cross-out
            draw.line(
                [(int(x) - 2, int(y) - 6), (int(x) + 22, int(y) - 6)],
                fill=(*self.config.ink_color_base, 100),
                width=1,
            )
        elif r < 0.0025:
            # Ink blob
            bx = int(x + random.gauss(0, 4))
            by = int(y + random.gauss(0, 4))
            draw.ellipse(
                [(bx - 2, by - 2), (bx + 2, by + 2)],
                fill=(*self.config.ink_color_base, 180),
            )
        elif char == "." and r < 0.15:
            # Extra pressure on period
            draw.ellipse(
                [(int(x) + 1, int(y) - 2), (int(x) + 3, int(y))],
                fill=(*self.config.ink_color_base, 200),
            )

    # ── Layer 7 — Page composition ────────────────────────────────────────────
    def _draw_page_background(self, canvas: Image.Image):
        """Draw ruled lines and red margin line."""
        draw = ImageDraw.Draw(canvas)
        W, H = canvas.size
        s    = NOTEBOOK_STYLE

        # Fill background
        canvas.paste(Image.new("RGB", (W, H), s["bg_color"]))

        # Blue horizontal ruled lines
        lc = s["line_color"]
        y  = s["first_line_y"]
        while y < H - 20:
            draw.line([(0, y), (W, y)], fill=(*lc, 185), width=1)
            y += s["line_spacing"] + self.config.line_height_extra

        # Red vertical margin line
        mx = s["margin_x"]
        draw.line([(mx, 0), (mx, H)], fill=(*s["margin_color"], 210), width=2)

    def _draw_assignment_header(
        self,
        draw:          ImageDraw.Draw,
        name:          str = "",
        subject:       str = "",
        assignment_no: str = "",
    ):
        """
        Draw the 3-line assignment header at the top of the first page.

        Name          : ___________
        Subject       : ___________
        Assignment No : ___________

        Followed by a separator line.
        """
        s         = NOTEBOOK_STYLE
        font_h    = self._get_font(int(self.config.base_font_size * 0.95))
        ink       = (*self.config.ink_color_base, 215)
        label_x   = s["margin_x"] + 10
        colon_x   = label_x + 310
        value_x   = colon_x + 28
        line_end  = self.config.page_width - 40

        # ── Row 1: Name ───────────────────────────────────────────────────────
        y1 = 14
        draw.text((label_x, y1), "Name", font=font_h, fill=ink)
        draw.text((colon_x, y1), ":", font=font_h, fill=ink)
        if name:
            draw.text((value_x, y1), name, font=font_h, fill=ink)
        else:
            draw.line([(value_x, y1 + 26), (line_end, y1 + 26)],
                      fill=(190, 190, 190, 180), width=1)

        # ── Row 2: Subject ────────────────────────────────────────────────────
        y2 = y1 + s["line_spacing"] + 2
        draw.text((label_x, y2), "Subject", font=font_h, fill=ink)
        draw.text((colon_x, y2), ":", font=font_h, fill=ink)
        if subject:
            draw.text((value_x, y2), subject, font=font_h, fill=ink)
        else:
            draw.line([(value_x, y2 + 26), (line_end, y2 + 26)],
                      fill=(190, 190, 190, 180), width=1)

        # ── Row 3: Assignment No ──────────────────────────────────────────────
        y3 = y2 + s["line_spacing"] + 2
        draw.text((label_x, y3), "Assignment No", font=font_h, fill=ink)
        draw.text((colon_x, y3), ":", font=font_h, fill=ink)
        if assignment_no:
            draw.text((value_x, y3), assignment_no, font=font_h, fill=ink)
        else:
            draw.line([(value_x, y3 + 26), (line_end, y3 + 26)],
                      fill=(190, 190, 190, 180), width=1)

        # ── Separator line under header ────────────────────────────────────────
        sep_y = y3 + s["line_spacing"] + 8
        draw.line(
            [(s["margin_x"], sep_y), (self.config.page_width - 30, sep_y)],
            fill=(*s["line_color"], 230),
            width=2,
        )

        return sep_y  # returns where content should start below

    def _draw_page_number(self, draw: ImageDraw.Draw, page_num: int):
        """Draw page number at bottom center."""
        font  = self._get_font(int(self.config.base_font_size * 0.70))
        ink   = (*self.config.ink_color_base, 160)
        W     = self.config.page_width
        H     = self.config.page_height
        draw.text(
            (W // 2 - 10, H - 36),
            f"— {page_num} —",
            font=font,
            fill=ink,
        )

    # ── Main public method ────────────────────────────────────────────────────
    def render_page(
        self,
        text:          str,
        subject:       str  = "",
        page_num:      int  = 1,
        name:          str  = "",
        assignment_no: str  = "",
        is_first_page: bool = True,
    ) -> Image.Image:
        """
        Render one full A4 notebook page with handwritten text.

        Args:
            text:          Content to write on the page
            subject:       Subject name shown in header
            page_num:      Page number shown at bottom
            name:          Student name in header (first page only)
            assignment_no: Assignment number in header (first page only)
            is_first_page: Whether to draw the Name/Subject/Asgmt header

        Returns:
            PIL Image (RGB) — ready to be added to PDF
        """
        W, H   = self.config.page_width, self.config.page_height
        s      = NOTEBOOK_STYLE
        canvas = Image.new("RGBA", (W, H), (255, 255, 255, 255))

        # Layer 7 — Draw page background (lines + margin)
        self._draw_page_background(canvas)
        draw = ImageDraw.Draw(canvas)

        # ── Header ────────────────────────────────────────────────────────────
        if is_first_page:
            header_bottom = self._draw_assignment_header(
                draw,
                name=name,
                subject=subject,
                assignment_no=assignment_no,
            )
            # First text line starts after header
            content_start_y = header_bottom + 10
        else:
            content_start_y = s["first_line_y"] + 6

        # Snap content_start_y to nearest ruled line
        line_h      = s["line_spacing"] + self.config.line_height_extra
        lines_down  = math.ceil((content_start_y - s["first_line_y"]) / line_h)
        y           = s["first_line_y"] + lines_down * line_h + 4

        # ── Text rendering ────────────────────────────────────────────────────
        x0      = self.config.left_padding
        x_max   = W - self.config.right_padding
        self._ink_history = []   # reset ink per page

        # Per-line slope (text drifts slightly — real handwriting)
        line_slope = random.uniform(-0.001, 0.003)

        all_lines = text.split("\n")

        for raw_line in all_lines:
            if y > H - 60:
                break

            # Smooth slope variation line by line
            new_slope  = random.uniform(-0.001, 0.003)
            line_slope = 0.7 * line_slope + 0.3 * new_slope

            if not raw_line.strip():
                y += line_h * 0.55
                continue

            x     = float(x0)
            words = raw_line.split(" ")

            for word in words:
                if not word:
                    x += self.config.base_font_size * (
                        self.config.word_spacing_base + random.gauss(0, 0.04)
                    )
                    continue

                # Estimate word width to check wrapping
                word_w_est = len(word) * self.config.base_font_size * 0.58
                if x + word_w_est > x_max and x > x0 + 10:
                    y += line_h
                    x  = float(x0) + random.gauss(0, 2)
                    if y > H - 60:
                        break

                # Render each character
                for char in word:
                    t     = self._char_transform(char, int(x))
                    y_pos = y + x * line_slope
                    adv   = self._draw_char(canvas, char, x, y_pos, t)
                    self._maybe_add_imperfection(draw, x, y_pos, char)
                    x += adv

                # Word spacing
                x += self.config.base_font_size * (
                    self.config.word_spacing_base + random.gauss(0, 0.05)
                )

            y += line_h

        # Page number at bottom
        self._draw_page_number(draw, page_num)

        # Convert RGBA → RGB for PDF
        bg = Image.new("RGB", canvas.size, "white")
        bg.paste(canvas, mask=canvas.split()[3])
        return bg

    def render_pages(
        self,
        pages_text:    list[str],
        subject:       str = "",
        name:          str = "",
        assignment_no: str = "",
    ) -> list[Image.Image]:
        """
        Render multiple pages. First page gets the full header.
        Subsequent pages just have ruled lines and page number.

        Args:
            pages_text:    List of text strings, one per page
            subject:       Subject for header
            name:          Student name for header
            assignment_no: Assignment number for header

        Returns:
            List of PIL Images, one per page
        """
        images = []
        for i, page_text in enumerate(pages_text):
            img = self.render_page(
                text          = page_text,
                subject       = subject,
                page_num      = i + 1,
                name          = name,
                assignment_no = assignment_no,
                is_first_page = (i == 0),
            )
            images.append(img)
        return images
