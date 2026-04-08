# BidWise Brand Guide

## Purpose

This document consolidates the current BidWise visual identity as implemented in the app and reflected in existing product decisions. It is the reference point for future UI, PDF, and chart changes.

## Brand Personality

BidWise should feel:

- Analytical, not flashy
- Trustworthy, not aggressive
- Professional, but approachable
- Clean and structured, not overly decorated

The product is a decision-support tool for procurement professionals. The visual language should reinforce credibility, clarity, and calm control.

## Core Visual Direction

BidWise uses a blue-gray / petroleum-blue identity rather than bright SaaS blues or high-contrast startup colors.

- Primary impression: calm, technical, reliable
- Accent behavior: subtle emphasis, not loud CTA overload
- Surfaces: soft, desaturated, low-noise
- Borders: light and restrained
- Typography: simple and readable

## Color System

### Light Theme

Primary tokens currently implemented in [app.py](/C:/Users/henri/bidwise/app.py):

- `--primary-color`: `#6F8797`
- `--bw-brand`: `#4A90A4`
- `--bw-brand-subtitle`: `#3F4F5F`
- `--bw-accent`: `#6F8797`
- `--bw-accent-hover`: `#5F7686`
- `--bw-accent-soft`: `rgba(111, 135, 151, 0.16)`
- `--bw-accent-border`: `rgba(111, 135, 151, 0.40)`
- `--bw-text-primary`: `#1C2D3A`
- `--bw-text-secondary`: `#3F4F5F`
- `--bw-text-muted`: `#6B7E8A`
- `--bw-surface-subtle`: `rgba(74, 144, 164, 0.08)`
- `--bw-surface-card`: `rgba(74, 144, 164, 0.05)`
- `--bw-sidebar-bg`: `#F3F6FA`
- `--bw-border-subtle`: `rgba(196, 213, 223, 0.90)`
- `--bw-privacy-bg`: `#EBF1F6`
- `--bw-privacy-text`: `#1C2D3A`

Supporting colors used in the current UI:

- Market/info strip background: `#E8EFF6`
- Market/info strip text: `#24425A`
- Market/info strip border: `#C7D6E2`

### Dark Theme

Current dark-mode tokens in [app.py](/C:/Users/henri/bidwise/app.py):

- `--primary-color`: `#6F91A3`
- `--bw-brand`: `#5BAEC4`
- `--bw-brand-subtitle`: `#A8BFCC`
- `--bw-accent`: `#6F91A3`
- `--bw-accent-hover`: `#82A5B8`
- `--bw-accent-soft`: `rgba(111, 145, 163, 0.22)`
- `--bw-accent-border`: `rgba(130, 165, 184, 0.46)`
- `--bw-text-secondary`: `#A8BFCC`
- `--bw-text-muted`: `#6B8A9A`
- `--bw-surface-subtle`: `rgba(91, 174, 196, 0.10)`
- `--bw-surface-card`: `rgba(91, 174, 196, 0.05)`
- `--bw-sidebar-bg`: `#262730`
- `--bw-border-subtle`: `rgba(91, 174, 196, 0.22)`
- `--bw-privacy-bg`: `#0E1A24`
- `--bw-privacy-text`: `#E8F2F8`

## Theme Configuration

The global Streamlit theme is currently anchored in [.streamlit/config.toml](/C:/Users/henri/bidwise/.streamlit/config.toml):

```toml
[theme]
primaryColor = "#6F8797"
```

If additional theme keys are added later, they should stay aligned with the tokens in [app.py](/C:/Users/henri/bidwise/app.py), not diverge from them.

## Typography

Current tone and usage:

- Clear and functional
- No decorative type treatments
- Strong emphasis through weight and spacing, not gimmicks
- Large brand wordmark, restrained supporting copy

Header styling currently suggests:

- Brand wordmark: bold, large, high-confidence
- Subtitle: smaller and quieter
- Tagline: muted support text

## Component Style Rules

### Buttons

- Primary buttons use the accent blue-gray
- Hover states should darken slightly, not shift hue dramatically
- Buttons should feel solid and calm, not bright or promotional

### Cards and Panels

- Use soft tinted backgrounds
- Prefer subtle borders over hard shadows
- Round corners are welcome, but should remain professional

### Inputs and Focus States

- Focus should use accent-colored outlines and borders
- Avoid default red or unrelated framework colors
- Selected/active states should feel part of the same blue-gray system

### Sidebar

- Light, quiet background
- Content-first layout
- Minimal decorative treatment

## Product Layout Principles

From existing product decisions in [BIDWISE_DECISIONS_LOG 17-3-26 19h33.md](/C:/Users/henri/bidwise/BIDWISE_DECISIONS_LOG%2017-3-26%2019h33.md):

- Sidebar width: `420px`
- Main content order:
  1. Recommendation
  2. Parameters
  3. Saving Estimate + graph + PDF button
  4. Simulation
  5. Compare Scenarios
  6. Take to AI
  7. Theoretical Foundation
- Use dividers between sections
- Keep export actions inline instead of creating a separate export section

## Charts and Data Visualization

Current visual rules from the decisions log:

- Open blue circle = initial proposal
- Filled green diamond = realistic target
- Semi-transparent blue box = uncertainty range
- Labels should remain functional and easy to scan

Charts should prioritize legibility over flair.

## Brand Elements

### Wordmark

- Brand name: `BidWise`
- Tone: professional procurement intelligence
- The name should be visually prominent, but not theatrical

### Footer Attribution

Current footer direction:

- `Built by Henrique Silva — Strategic Sourcing Analyst`

### PDF Branding

The PDF should include BidWise branding in the header and preserve the same blue-gray identity as the app.

## Voice-to-Visual Alignment

Because the product explains complex sourcing strategy, the visual system should match the verbal tone:

- Calm
- Precise
- Rational
- Experienced

Avoid visuals that feel:

- Salesy
- Neon
- Over-gamified
- Overly startup-like
- Alarm-heavy unless the product is signaling a genuine risk

## Do / Don't

### Do

- Use blue-gray and petroleum-blue accents
- Keep surfaces soft and understated
- Make emphasis feel intentional
- Preserve a structured, analytical layout
- Prefer clarity over decoration

### Don’t

- Introduce random bright reds as default highlights
- Use purple as a brand accent
- Mix multiple unrelated accent colors in core UI controls
- Add noisy gradients or flashy visual effects
- Let Streamlit default colors leak into the interface

## Source of Truth

Today, the visual identity is derived from these files:

- [app.py](/C:/Users/henri/bidwise/app.py)
- [.streamlit/config.toml](/C:/Users/henri/bidwise/.streamlit/config.toml)
- [BIDWISE_DECISIONS_LOG 17-3-26 19h33.md](/C:/Users/henri/bidwise/BIDWISE_DECISIONS_LOG%2017-3-26%2019h33.md)

If visual decisions change, update this file together with the implementation.
