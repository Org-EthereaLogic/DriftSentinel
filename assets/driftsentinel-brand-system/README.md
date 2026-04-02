# DriftSentinel Brand System

Brand asset package for DriftSentinel.

## Visual Direction

The mark uses a monitored signal that stays stable through most of the trace
and then breaks into an amber deviation at the control gate. The composition is
intended to read as:

- continuous data monitoring
- explicit drift detection
- operator-visible gate decisions

## Brand Colors

| Name | Hex | Use |
| --- | --- | --- |
| Midnight | `#071824` | Primary background |
| Deep Slate | `#0B2233` | Secondary dark surface |
| Cloud | `#E6F1F6` | Light text and light surface |
| Sentinel Cyan | `#20CFE0` | Monitoring rings and radar cue |
| Trust Teal | `#22C7A0` | Stable signal path |
| Drift Amber | `#F59E0B` | Drift path and gate breach |
| Alert Coral | `#F97316` | Beacon endpoint accent |
| Gate Slate | `#8AA3B6` | Control gate line (structural) |
| Mist | `#F4F8FA` | Light-mode badge background (structural) |
| Light Grid | `#D7E4EC` | Light-mode grid and crosshair (structural) |

## Directory Structure

```text
driftsentinel-brand-system/
├── README.md
├── generate_brand_assets.py
├── source/
│   ├── driftsentinel-mark-source.svg
│   ├── driftsentinel-logo-source.svg
│   └── safari-pinned-tab.svg
├── icons/
│   ├── driftsentinel-logo-1200x320.png
│   ├── driftsentinel-mark-128.png
│   ├── driftsentinel-mark-256.png
│   └── driftsentinel-mark-512.png
├── variants/
│   ├── mark-dark.png
│   ├── mark-light.png
│   ├── mark-transparent.png
│   ├── logo-dark.png
│   ├── logo-light.png
│   └── logo-transparent.png
├── favicons/
│   ├── android-chrome-192x192.png
│   ├── android-chrome-512x512.png
│   ├── apple-touch-icon.png
│   ├── favicon-16x16.png
│   ├── favicon-32x32.png
│   ├── favicon-48x48.png
│   ├── favicon.ico
│   ├── safari-pinned-tab.svg
│   └── site.webmanifest
└── social/
    ├── linkedin-banner.png
    ├── og-image.png
    └── twitter-card.png
```

## Regeneration

Run the generator from the repository root:

```bash
python assets/driftsentinel-brand-system/generate_brand_assets.py
```

The generator writes deterministic source SVGs and the exported raster assets in
place. It uses Pillow plus a best-effort system font lookup for the wordmark
and social text. If no preferred font exists, it falls back to Pillow's default
font.

## Usage Guide

- Use `source/driftsentinel-mark-source.svg` when a scalable vector mark is
  required.
- Use `icons/driftsentinel-mark-*.png` for app icon or repository badge
  contexts.
- Use `favicons/` for browser and PWA favicon wiring.
- Use `social/og-image.png` for Open Graph previews.
- Use `variants/logo-transparent.png` or `variants/logo-light.png` on light
  surfaces.
- Use `variants/logo-dark.png` on dark surfaces.
