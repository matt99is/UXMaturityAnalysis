"""
Screenshot Annotation Tool

Adds visual annotations to screenshots highlighting key findings:
- Green boxes for strengths/advantages
- Red boxes for vulnerabilities/issues
- Yellow boxes for areas of interest
- Text labels explaining findings
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont


class ScreenshotAnnotator:
    """
    Annotates screenshots with visual indicators for analysis findings.
    """

    def __init__(self):
        # Color scheme for annotations
        self.colors = {
            "advantage": "#48bb78",  # Green
            "vulnerability": "#f56565",  # Red
            "parity": "#4299e1",  # Blue
            "highlight": "#fbbf24",  # Yellow
        }

        # Try to load a system font, fall back to default
        self.font = self._load_font()

    def _load_font(self, size: int = 24) -> ImageFont:
        """Load system font or fall back to default."""
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    pass

        # Fall back to default
        return ImageFont.load_default()

    def annotate_screenshot(
        self, screenshot_path: str, annotations: List[Dict[str, Any]], output_path: str = None
    ) -> str:
        """
        Add annotations to a screenshot.

        Args:
            screenshot_path: Path to original screenshot
            annotations: List of annotation dicts with:
                - type: 'advantage', 'vulnerability', 'parity', or 'highlight'
                - region: tuple of (x, y, width, height) or None for overall badge
                - label: text label to display
            output_path: Optional output path, defaults to {original}_annotated.png

        Returns:
            Path to annotated image
        """
        # Load image
        img = Image.open(screenshot_path)
        draw = ImageDraw.Draw(img, "RGBA")

        # Calculate scaling for mobile vs desktop
        is_mobile = img.width < 500
        scale = 0.6 if is_mobile else 1.0

        # Add overall badges at top
        badge_y = 20
        for annotation in annotations:
            if annotation.get("region") is None:
                # This is an overall badge
                self._draw_badge(
                    draw,
                    img,
                    annotation.get("label", ""),
                    annotation.get("type", "highlight"),
                    20,
                    badge_y,
                    scale,
                )
                badge_y += int(60 * scale)

        # Add region-specific annotations
        for annotation in annotations:
            if annotation.get("region"):
                x, y, w, h = annotation["region"]
                ann_type = annotation.get("type", "highlight")
                label = annotation.get("label", "")

                # Draw bounding box
                self._draw_box(
                    draw, (x, y, x + w, y + h), self.colors[ann_type], width=int(4 * scale)
                )

                # Draw label
                if label:
                    self._draw_label(
                        draw, label, x, y - int(35 * scale), self.colors[ann_type], scale
                    )

        # Save annotated image
        if output_path is None:
            path = Path(screenshot_path)
            output_path = str(path.parent / f"{path.stem}_annotated{path.suffix}")

        img.save(output_path, "PNG", optimize=True)
        return output_path

    def _draw_box(
        self, draw: ImageDraw, coords: Tuple[int, int, int, int], color: str, width: int = 4
    ):
        """Draw a colored bounding box."""
        # Convert hex to RGB
        rgb = self._hex_to_rgb(color)

        # Draw rectangle with transparency
        for i in range(width):
            draw.rectangle(
                [coords[0] + i, coords[1] + i, coords[2] - i, coords[3] - i],
                outline=rgb + (200,),  # Add alpha
                width=1,
            )

    def _draw_label(
        self, draw: ImageDraw, text: str, x: int, y: int, color: str, scale: float = 1.0
    ):
        """Draw text label with background."""
        rgb = self._hex_to_rgb(color)
        font_size = int(20 * scale)
        font = self._load_font(font_size)

        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding = int(8 * scale)

        # Draw background rectangle
        draw.rectangle(
            [x, y, x + text_width + padding * 2, y + text_height + padding * 2],
            fill=rgb + (230,),  # Semi-transparent background
            outline=rgb + (255,),
        )

        # Draw text
        draw.text((x + padding, y + padding), text, fill=(255, 255, 255, 255), font=font)

    def _draw_badge(
        self,
        draw: ImageDraw,
        img: Image,
        text: str,
        badge_type: str,
        x: int,
        y: int,
        scale: float = 1.0,
    ):
        """Draw an overall badge (not tied to specific region)."""
        color = self.colors.get(badge_type, self.colors["highlight"])
        rgb = self._hex_to_rgb(color)

        font_size = int(18 * scale)
        font = self._load_font(font_size)

        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding_x = int(15 * scale)
        padding_y = int(10 * scale)

        width = text_width + padding_x * 2
        height = text_height + padding_y * 2

        # Draw rounded rectangle background
        radius = int(8 * scale)
        self._draw_rounded_rectangle(
            draw,
            [(x, y), (x + width, y + height)],
            radius,
            fill=rgb + (240,),
            outline=rgb + (255,),
            width=2,
        )

        # Draw text
        draw.text((x + padding_x, y + padding_y), text, fill=(255, 255, 255, 255), font=font)

    def _draw_rounded_rectangle(
        self, draw: ImageDraw, coords: List[Tuple[int, int]], radius: int, **kwargs
    ):
        """Draw a rounded rectangle."""
        x1, y1 = coords[0]
        x2, y2 = coords[1]

        # Draw main rectangle
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], **kwargs)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], **kwargs)

        # Draw corners
        draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, **kwargs)
        draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, **kwargs)
        draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, **kwargs)
        draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, **kwargs)

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def create_annotations_from_analysis(
        self, criteria_scores: List[Dict[str, Any]], top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Auto-generate annotations from analysis results.

        Args:
            criteria_scores: List of criterion scores from analysis
            top_n: Number of top strengths/weaknesses to annotate

        Returns:
            List of annotation dicts
        """
        annotations = []

        # Sort by competitive status
        advantages = [c for c in criteria_scores if c.get("competitive_status") == "advantage"]
        vulnerabilities = [
            c for c in criteria_scores if c.get("competitive_status") == "vulnerability"
        ]

        # Add top advantages as badges
        for criterion in sorted(advantages, key=lambda x: x.get("score", 0), reverse=True)[:top_n]:
            annotations.append(
                {
                    "type": "advantage",
                    "region": None,  # Overall badge
                    "label": f"✓ {criterion['criterion_name']}: {criterion['score']:.1f}/10",
                }
            )

        # Add top vulnerabilities as badges
        for criterion in sorted(vulnerabilities, key=lambda x: x.get("score", 0))[:top_n]:
            annotations.append(
                {
                    "type": "vulnerability",
                    "region": None,
                    "label": f"✗ {criterion['criterion_name']}: {criterion['score']:.1f}/10",
                }
            )

        return annotations
