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

No app screenshots or image-based evidence visuals are currently checked into
`assets/`, `docs/`, or `report/`.

## Missing Assets

| Missing Asset | Why It Is Missing | Owner / Next Step |
| --- | --- | --- |
| Databricks App hero screenshot | No repository-backed screenshot artifact exists for the current App deployment | operator capture required from a running app deployment |
| Databricks App detail screenshots for Registry, Run Status, Evidence Explorer, and Analytics | Marketplace gallery assets are not stored in the repo today | operator capture required from a running app deployment |
| Marketplace-specific thumbnail or banner crop | Existing social graphics are reusable, but no Marketplace-dimension export is defined | operator decision required, then export from source assets |
| Evidence-gallery screenshot | Repository evidence is text-first; no image snapshot of evidence review exists | operator capture required if the listing needs a visual evidence example |

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
