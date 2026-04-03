# DriftSentinel Marketplace Asset Manifest

This manifest records which repository-managed visuals are immediately reusable
for Marketplace preparation and which collateral still requires operator
capture. It does not imply that a live Marketplace listing already exists.

## Available Assets

| Asset | Marketplace Use | Status | Source Path |
| --- | --- | --- | --- |
| Primary wordmark | Provider or listing logo | available now | `assets/driftsentinel-brand-system/icons/driftsentinel-logo-1200x320.png` |
| Square product mark | Provider icon or square thumbnail | available now | `assets/driftsentinel-brand-system/icons/driftsentinel-mark-512.png` |
| Light and dark logo variants | Alternate light/dark backgrounds | available now | `assets/driftsentinel-brand-system/variants/logo-light.png`, `assets/driftsentinel-brand-system/variants/logo-dark.png` |
| Transparent logo and mark variants | Flexible compositing on Marketplace backgrounds | available now | `assets/driftsentinel-brand-system/variants/logo-transparent.png`, `assets/driftsentinel-brand-system/variants/mark-transparent.png` |
| Source SVG logo and mark | Regeneration or derivative exports | available now | `assets/driftsentinel-brand-system/source/driftsentinel-logo-source.svg`, `assets/driftsentinel-brand-system/source/driftsentinel-mark-source.svg` |
| Social preview graphics | Stopgap marketing collateral while Marketplace-specific screenshots are missing | available now | `assets/driftsentinel-brand-system/social/og-image.png`, `assets/driftsentinel-brand-system/social/twitter-card.png`, `assets/driftsentinel-brand-system/social/linkedin-banner.png` |
| Favicon set | Small-icon fallback set | available now | `assets/driftsentinel-brand-system/favicons/` |

## App Screenshots (Captured 2026-04-03)

Four retina-quality (2x device scale) screenshots captured from the live Gradio
dashboard in dark mode with populated data:

| Screenshot | Tab | Path |
| --- | --- | --- |
| `01-registry.png` | Registry — 2 datasets registered | `screenshots/01-registry.png` |
| `02-run-status.png` | Run Status — 48 artifacts with verdict breakdown | `screenshots/02-run-status.png` |
| `03-evidence-explorer.png` | Evidence Explorer — drift artifact JSON detail | `screenshots/03-evidence-explorer.png` |
| `04-analytics.png` | Analytics — verdict bar, kind donut, volume, health trend | `screenshots/04-analytics.png` |

## Missing Assets

| Missing Asset | Why It Is Missing | Owner / Next Step |
| --- | --- | --- |
| Marketplace-specific thumbnail or banner crop | Existing social graphics are reusable, but no Marketplace-dimension export is defined | operator decision required, then export from source assets |

## Source Paths

| Surface | Path |
| --- | --- |
| Brand system root | `assets/driftsentinel-brand-system/` |
| Wordmark PNG | `assets/driftsentinel-brand-system/icons/driftsentinel-logo-1200x320.png` |
| Square mark PNG | `assets/driftsentinel-brand-system/icons/driftsentinel-mark-512.png` |
| Source SVGs | `assets/driftsentinel-brand-system/source/` |
| Logo and mark variants | `assets/driftsentinel-brand-system/variants/` |
| Social graphics | `assets/driftsentinel-brand-system/social/` |
| Favicon exports | `assets/driftsentinel-brand-system/favicons/` |
| Marketplace screenshots | `assets/driftsentinel-brand-system/marketplace/screenshots/` |
