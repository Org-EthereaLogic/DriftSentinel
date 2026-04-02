from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "source"
ICONS_DIR = ROOT / "icons"
VARIANTS_DIR = ROOT / "variants"
FAVICONS_DIR = ROOT / "favicons"
SOCIAL_DIR = ROOT / "social"

PALETTE = {
    "midnight": "#071824",
    "deep_slate": "#0B2233",
    "cloud": "#E6F1F6",
    "sentinel_cyan": "#20CFE0",
    "trust_teal": "#22C7A0",
    "drift_amber": "#F59E0B",
    "alert_coral": "#F97316",
    "gate_slate": "#8AA3B6",
    "mist": "#F4F8FA",
    "light_grid": "#D7E4EC",
}

POINTS_STABLE = [(96, 322), (150, 284), (204, 294), (252, 248), (304, 252), (340, 220)]
POINTS_DRIFT = [(340, 220), (388, 170), (426, 144)]

BOLD_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Avenir Next Demi Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]

REGULAR_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
]

FontType = ImageFont.FreeTypeFont | ImageFont.ImageFont


def rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    red, green, blue = ImageColor.getrgb(hex_color)
    return red, green, blue, alpha


def ensure_dirs() -> None:
    for path in (SOURCE_DIR, ICONS_DIR, VARIANTS_DIR, FAVICONS_DIR, SOCIAL_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_font(size: int, *, bold: bool) -> FontType:
    candidates = BOLD_FONT_CANDIDATES if bold else REGULAR_FONT_CANDIDATES
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def alpha_composite(base: Image.Image, overlay: Image.Image) -> Image.Image:
    return Image.alpha_composite(base.convert("RGBA"), overlay.convert("RGBA"))


def render_badge(size: int, mode: str) -> Image.Image:
    scale = 4
    canvas = 512 * scale
    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    overlay = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if mode == "dark":
        background = rgba(PALETTE["midnight"])
        ring = rgba(PALETTE["sentinel_cyan"], 170)
        sub_ring = rgba("#8BC8D8", 96)
        gate = rgba(PALETTE["gate_slate"], 138)
        grid = rgba("#13334A", 220)
    elif mode == "light":
        background = rgba(PALETTE["mist"])
        ring = rgba("#12758E", 190)
        sub_ring = rgba("#5E8195", 108)
        gate = rgba("#6D8091", 148)
        grid = rgba(PALETTE["light_grid"], 255)
    elif mode == "transparent":
        background = None
        ring = rgba("#12758E", 200)
        sub_ring = rgba("#567487", 138)
        gate = rgba("#6D8091", 160)
        grid = rgba("#D0DCE4", 120)
    else:
        msg = f"Unsupported badge mode: {mode}"
        raise ValueError(msg)

    if background is not None:
        inset = 20 * scale
        draw.rounded_rectangle(
            (inset, inset, canvas - inset, canvas - inset),
            radius=116 * scale,
            fill=background,
        )
        draw.ellipse(
            (44 * scale, 20 * scale, 454 * scale, 238 * scale),
            fill=rgba("#2E6075", 32 if mode == "dark" else 18),
        )

    arc_box = (76 * scale, 76 * scale, 436 * scale, 436 * scale)
    draw.arc(
        arc_box,
        start=300,
        end=359,
        fill=rgba(PALETTE["sentinel_cyan"], 120 if mode == "dark" else 92),
        width=18 * scale,
    )
    draw.arc(
        arc_box,
        start=0,
        end=28,
        fill=rgba(PALETTE["sentinel_cyan"], 120 if mode == "dark" else 92),
        width=18 * scale,
    )
    draw.ellipse(
        (76 * scale, 76 * scale, 436 * scale, 436 * scale),
        outline=ring,
        width=10 * scale,
    )
    draw.ellipse(
        (124 * scale, 124 * scale, 388 * scale, 388 * scale),
        outline=sub_ring,
        width=8 * scale,
    )
    draw.ellipse(
        (172 * scale, 172 * scale, 340 * scale, 340 * scale),
        outline=sub_ring,
        width=6 * scale,
    )
    draw.line((340 * scale, 96 * scale, 340 * scale, 416 * scale), fill=gate, width=14 * scale)

    draw.line(
        [(x * scale, y * scale) for x, y in POINTS_STABLE],
        fill=rgba(PALETTE["trust_teal"]),
        width=24 * scale,
        joint="curve",
    )
    draw.line(
        [(x * scale, y * scale) for x, y in POINTS_DRIFT],
        fill=rgba(PALETTE["drift_amber"]),
        width=24 * scale,
        joint="curve",
    )

    pivot = (340 * scale, 220 * scale)
    endpoint = (426 * scale, 144 * scale)
    draw.ellipse(
        (pivot[0] - 16 * scale, pivot[1] - 16 * scale, pivot[0] + 16 * scale, pivot[1] + 16 * scale),
        fill=rgba(PALETTE["cloud"] if mode == "dark" else PALETTE["deep_slate"], 220),
    )
    draw.ellipse(
        (
            endpoint[0] - 36 * scale,
            endpoint[1] - 36 * scale,
            endpoint[0] + 36 * scale,
            endpoint[1] + 36 * scale,
        ),
        outline=rgba(PALETTE["alert_coral"], 120),
        width=8 * scale,
    )
    draw.ellipse(
        (
            endpoint[0] - 18 * scale,
            endpoint[1] - 18 * scale,
            endpoint[0] + 18 * scale,
            endpoint[1] + 18 * scale,
        ),
        fill=rgba(PALETTE["alert_coral"]),
    )
    draw.line(
        (endpoint[0], endpoint[1] - 50 * scale, endpoint[0], endpoint[1] - 30 * scale),
        fill=grid,
        width=6 * scale,
    )
    draw.line(
        (endpoint[0] - 50 * scale, endpoint[1], endpoint[0] - 30 * scale, endpoint[1]),
        fill=grid,
        width=6 * scale,
    )

    image = alpha_composite(image, overlay)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def render_logo(width: int, height: int, mode: str) -> Image.Image:
    background = {
        "dark": rgba(PALETTE["midnight"]),
        "light": rgba("#FFFFFF"),
        "transparent": None,
    }[mode]
    text_primary = PALETTE["cloud"] if mode == "dark" else PALETTE["deep_slate"]
    text_secondary = PALETTE["sentinel_cyan"] if mode == "dark" else "#12758E"

    image = Image.new("RGBA", (width, height), background or (0, 0, 0, 0))
    badge_mode = "dark" if mode == "dark" else "light" if mode == "light" else "transparent"
    badge = render_badge(256, badge_mode)
    image.alpha_composite(badge, (48, (height - badge.height) // 2))

    draw = ImageDraw.Draw(image)
    title_font = load_font(120, bold=True)
    subtitle_font = load_font(34, bold=False)

    title_y = 82
    draw.text((352, title_y), "Drift", font=title_font, fill=text_primary)
    drift_bbox = draw.textbbox((352, title_y), "Drift", font=title_font)
    draw.text((drift_bbox[2] + 14, title_y), "Sentinel", font=title_font, fill=text_secondary)
    draw.text(
        (356, 224),
        "Unified drift monitoring for enterprise data trust",
        font=subtitle_font,
        fill=rgba(text_primary, 210),
    )

    return image


def write_svg_sources() -> None:
    mark_svg = "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">',
            "  <defs>",
            '    <linearGradient id="badge-bg" x1="0%" y1="0%" x2="100%" y2="100%">',
            f'      <stop offset="0%" stop-color="{PALETTE["deep_slate"]}"/>',
            f'      <stop offset="100%" stop-color="{PALETTE["midnight"]}"/>',
            "    </linearGradient>",
            '    <linearGradient id="mark-drift-line" x1="320" y1="230" x2="430" y2="140"',
            '      gradientUnits="userSpaceOnUse">',
            f'      <stop offset="0%" stop-color="{PALETTE["drift_amber"]}"/>',
            f'      <stop offset="100%" stop-color="{PALETTE["alert_coral"]}"/>',
            "    </linearGradient>",
            "  </defs>",
            '  <rect x="20" y="20" width="472" height="472" rx="116" fill="url(#badge-bg)"/>',
            '  <ellipse cx="252" cy="126" rx="204" ry="108" fill="#2E6075" opacity="0.13"/>',
            '  <path d="M 340 96 A 180 180 0 0 1 416 140" fill="none"',
            f'    stroke="{PALETTE["sentinel_cyan"]}" stroke-opacity="0.5" stroke-width="18"',
            '    stroke-linecap="round"/>',
            '  <circle cx="256" cy="256" r="180" fill="none"',
            f'    stroke="{PALETTE["sentinel_cyan"]}" stroke-opacity="0.7" stroke-width="10"/>',
            '  <circle cx="256" cy="256" r="132" fill="none"',
            '    stroke="#8BC8D8" stroke-opacity="0.35" stroke-width="8"/>',
            '  <circle cx="256" cy="256" r="84" fill="none"',
            '    stroke="#8BC8D8" stroke-opacity="0.35" stroke-width="6"/>',
            '  <path d="M 340 96 L 340 416" fill="none"',
            f'    stroke="{PALETTE["gate_slate"]}" stroke-opacity="0.54" stroke-width="14"',
            '    stroke-linecap="round"/>',
            '  <path d="M 96 322 L 150 284 L 204 294 L 252 248 L 304 252 L 340 220"',
            f'    fill="none" stroke="{PALETTE["trust_teal"]}" stroke-width="24"',
            '    stroke-linecap="round" stroke-linejoin="round"/>',
            '  <path d="M 340 220 L 388 170 L 426 144" fill="none"',
            '    stroke="url(#mark-drift-line)" stroke-width="24"',
            '    stroke-linecap="round" stroke-linejoin="round"/>',
            f'  <circle cx="340" cy="220" r="16" fill="{PALETTE["cloud"]}"/>',
            '  <circle cx="426" cy="144" r="36" fill="none"',
            f'    stroke="{PALETTE["alert_coral"]}" stroke-opacity="0.45" stroke-width="8"/>',
            f'  <circle cx="426" cy="144" r="18" fill="{PALETTE["alert_coral"]}"/>',
            '  <path d="M 426 94 L 426 114" fill="none" stroke="#D0DCE4"',
            '    stroke-opacity="0.75" stroke-width="6" stroke-linecap="round"/>',
            '  <path d="M 376 144 L 396 144" fill="none" stroke="#D0DCE4"',
            '    stroke-opacity="0.75" stroke-width="6" stroke-linecap="round"/>',
            "</svg>",
        ]
    )

    logo_svg = "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 320" width="1200" height="320">',
            "  <defs>",
            '    <linearGradient id="logo-badge-bg" x1="0%" y1="0%" x2="100%" y2="100%">',
            f'      <stop offset="0%" stop-color="{PALETTE["deep_slate"]}"/>',
            f'      <stop offset="100%" stop-color="{PALETTE["midnight"]}"/>',
            "    </linearGradient>",
            '    <linearGradient id="logo-drift-line" x1="320" y1="230" x2="430" y2="140"',
            '      gradientUnits="userSpaceOnUse">',
            f'      <stop offset="0%" stop-color="{PALETTE["drift_amber"]}"/>',
            f'      <stop offset="100%" stop-color="{PALETTE["alert_coral"]}"/>',
            "    </linearGradient>",
            "  </defs>",
            '  <g transform="translate(12 32) scale(0.5)">',
            '    <rect x="20" y="20" width="472" height="472" rx="116" fill="url(#logo-badge-bg)"/>',
            '    <ellipse cx="252" cy="126" rx="204" ry="108" fill="#2E6075" opacity="0.13"/>',
            '    <path d="M 340 96 A 180 180 0 0 1 416 140" fill="none"',
            f'      stroke="{PALETTE["sentinel_cyan"]}" stroke-opacity="0.5" stroke-width="18"',
            '      stroke-linecap="round"/>',
            '    <circle cx="256" cy="256" r="180" fill="none"',
            f'      stroke="{PALETTE["sentinel_cyan"]}" stroke-opacity="0.7" stroke-width="10"/>',
            '    <circle cx="256" cy="256" r="132" fill="none"',
            '      stroke="#8BC8D8" stroke-opacity="0.35" stroke-width="8"/>',
            '    <circle cx="256" cy="256" r="84" fill="none"',
            '      stroke="#8BC8D8" stroke-opacity="0.35" stroke-width="6"/>',
            '    <path d="M 340 96 L 340 416" fill="none"',
            f'      stroke="{PALETTE["gate_slate"]}" stroke-opacity="0.54" stroke-width="14"',
            '      stroke-linecap="round"/>',
            '    <path d="M 96 322 L 150 284 L 204 294 L 252 248 L 304 252 L 340 220"',
            f'      fill="none" stroke="{PALETTE["trust_teal"]}" stroke-width="24"',
            '      stroke-linecap="round" stroke-linejoin="round"/>',
            '    <path d="M 340 220 L 388 170 L 426 144" fill="none"',
            '      stroke="url(#logo-drift-line)" stroke-width="24"',
            '      stroke-linecap="round" stroke-linejoin="round"/>',
            f'    <circle cx="340" cy="220" r="16" fill="{PALETTE["cloud"]}"/>',
            '    <circle cx="426" cy="144" r="36" fill="none"',
            f'      stroke="{PALETTE["alert_coral"]}" stroke-opacity="0.45" stroke-width="8"/>',
            f'    <circle cx="426" cy="144" r="18" fill="{PALETTE["alert_coral"]}"/>',
            '    <path d="M 426 94 L 426 114" fill="none" stroke="#D0DCE4"',
            '      stroke-opacity="0.75" stroke-width="6" stroke-linecap="round"/>',
            '    <path d="M 376 144 L 396 144" fill="none" stroke="#D0DCE4"',
            '      stroke-opacity="0.75" stroke-width="6" stroke-linecap="round"/>',
            "  </g>",
            '  <text x="352" y="164" font-family="Avenir Next, Arial, Helvetica, sans-serif"',
            f'    font-size="120" font-weight="700" fill="{PALETTE["deep_slate"]}">Drift</text>',
            '  <text x="616" y="164" font-family="Avenir Next, Arial, Helvetica, sans-serif"',
            '    font-size="120" font-weight="700" fill="#12758E">Sentinel</text>',
            '  <text x="356" y="244" font-family="Avenir Next, Arial, Helvetica, sans-serif"',
            f'    font-size="34" fill="{PALETTE["deep_slate"]}" fill-opacity="0.82">',
            "    Unified drift monitoring for enterprise data trust",
            "  </text>",
            "</svg>",
        ]
    )

    pinned_tab_svg = "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">',
            '  <circle cx="256" cy="256" r="180" fill="none" stroke="#000000" stroke-width="34"/>',
            '  <circle cx="256" cy="256" r="132" fill="none" stroke="#000000"',
            '    stroke-width="24" opacity="0.72"/>',
            '  <path d="M 340 96 L 340 416" fill="none" stroke="#000000"',
            '    stroke-width="26" stroke-linecap="round"/>',
            '  <path d="M 96 322 L 150 284 L 204 294 L 252 248 L 304 252 L 340 220"',
            '    fill="none" stroke="#000000" stroke-width="36"',
            '    stroke-linecap="round" stroke-linejoin="round"/>',
            '  <path d="M 340 220 L 388 170 L 426 144" fill="none" stroke="#000000"',
            '    stroke-width="36" stroke-linecap="round" stroke-linejoin="round"/>',
            '  <circle cx="426" cy="144" r="28" fill="#000000"/>',
            "</svg>",
        ]
    )

    (SOURCE_DIR / "driftsentinel-mark-source.svg").write_text(mark_svg, encoding="utf-8")
    (SOURCE_DIR / "driftsentinel-logo-source.svg").write_text(logo_svg, encoding="utf-8")
    (SOURCE_DIR / "safari-pinned-tab.svg").write_text(pinned_tab_svg, encoding="utf-8")
    (FAVICONS_DIR / "safari-pinned-tab.svg").write_text(pinned_tab_svg, encoding="utf-8")


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_icons() -> None:
    for size in (128, 256, 512):
        save_png(render_badge(size, "dark"), ICONS_DIR / f"driftsentinel-mark-{size}.png")
    save_png(render_logo(1200, 320, "transparent"), ICONS_DIR / "driftsentinel-logo-1200x320.png")


def write_variants() -> None:
    save_png(render_badge(512, "dark"), VARIANTS_DIR / "mark-dark.png")
    save_png(render_badge(512, "light"), VARIANTS_DIR / "mark-light.png")
    save_png(render_badge(512, "transparent"), VARIANTS_DIR / "mark-transparent.png")
    save_png(render_logo(1200, 320, "dark"), VARIANTS_DIR / "logo-dark.png")
    save_png(render_logo(1200, 320, "light"), VARIANTS_DIR / "logo-light.png")
    save_png(render_logo(1200, 320, "transparent"), VARIANTS_DIR / "logo-transparent.png")


def write_favicons() -> None:
    favicon_sizes = {
        "favicon-16x16.png": 16,
        "favicon-32x32.png": 32,
        "favicon-48x48.png": 48,
        "apple-touch-icon.png": 180,
        "android-chrome-192x192.png": 192,
        "android-chrome-512x512.png": 512,
    }
    rendered: dict[str, Image.Image] = {}
    for filename, size in favicon_sizes.items():
        rendered[filename] = render_badge(size, "dark")
        save_png(rendered[filename], FAVICONS_DIR / filename)

    icon_path = FAVICONS_DIR / "favicon.ico"
    rendered["android-chrome-512x512.png"].save(
        icon_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )

    manifest = {
        "name": "DriftSentinel",
        "short_name": "DriftSentinel",
        "icons": [
            {"src": "android-chrome-192x192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "android-chrome-512x512.png", "sizes": "512x512", "type": "image/png"},
        ],
        "theme_color": PALETTE["midnight"],
        "background_color": PALETTE["midnight"],
        "display": "standalone",
    }
    (FAVICONS_DIR / "site.webmanifest").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def draw_pill(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, *, font: FontType) -> int:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    width = (right - left) + 52
    height = (bottom - top) + 26
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=height // 2,
        fill=rgba("#12334A", 228),
    )
    draw.text((x + 26, y + 10), text, font=font, fill=PALETTE["cloud"])
    return width


def render_social(width: int, height: int, platform: str) -> Image.Image:
    image = Image.new("RGBA", (width, height), rgba(PALETTE["midnight"]))
    draw = ImageDraw.Draw(image)
    title_font = load_font(max(54, height // 7), bold=True)
    subtitle_font = load_font(max(26, height // 18), bold=False)
    pill_font = load_font(max(20, height // 24), bold=False)

    draw.ellipse((-120, -80, width // 2, height + 80), fill=rgba("#0E2B41", 255))
    draw.ellipse((width // 2, -height // 2, width + 260, height // 2), fill=rgba("#10344B", 180))
    badge_size = int(height * 0.48)
    badge = render_badge(badge_size, "dark")
    image.alpha_composite(
        badge,
        (64, (height - badge_size) // 2 - (18 if platform == "linkedin" else 0)),
    )

    left = 64 + badge_size + 56
    title_top = max(56, int(height * 0.18))
    draw.text((left, title_top), "DriftSentinel", font=title_font, fill=PALETTE["cloud"])
    subtitle = "Unified drift monitoring for enterprise data trust"
    draw.text(
        (left, title_top + int(height * 0.19)),
        subtitle,
        font=subtitle_font,
        fill=rgba(PALETTE["cloud"], 214),
    )

    pill_y = title_top + int(height * 0.34)
    cursor = left
    for label in ("Intake certification", "Drift gating", "Control benchmarking"):
        cursor += draw_pill(draw, cursor, pill_y, label, font=pill_font) + 16

    accent_width = width - left - 72
    band_y = height - 74
    break_x = int(left + accent_width * 0.68)
    draw.line((left, band_y, break_x, band_y), fill=rgba(PALETTE["trust_teal"]), width=8)
    draw.line((break_x, band_y, width - 72, band_y - 24), fill=rgba(PALETTE["drift_amber"]), width=8)
    draw.ellipse((width - 96, band_y - 44, width - 48, band_y + 4), fill=rgba(PALETTE["alert_coral"]))

    return image


def write_social() -> None:
    save_png(render_social(1200, 630, "og"), SOCIAL_DIR / "og-image.png")
    save_png(render_social(1200, 600, "twitter"), SOCIAL_DIR / "twitter-card.png")
    save_png(render_social(1584, 396, "linkedin"), SOCIAL_DIR / "linkedin-banner.png")


def main() -> None:
    ensure_dirs()
    write_svg_sources()
    write_icons()
    write_variants()
    write_favicons()
    write_social()


if __name__ == "__main__":
    main()
