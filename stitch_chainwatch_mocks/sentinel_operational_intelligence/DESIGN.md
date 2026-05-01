---
name: Sentinel Operational Intelligence
colors:
  surface: '#fcf8fa'
  surface-dim: '#dcd9db'
  surface-bright: '#fcf8fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f5'
  surface-container: '#f0edef'
  surface-container-high: '#eae7e9'
  surface-container-highest: '#e4e2e4'
  on-surface: '#1b1b1d'
  on-surface-variant: '#45464d'
  inverse-surface: '#303032'
  inverse-on-surface: '#f3f0f2'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#006a61'
  on-secondary: '#ffffff'
  secondary-container: '#86f2e4'
  on-secondary-container: '#006f66'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#271901'
  on-tertiary-container: '#98805d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#89f5e7'
  secondary-fixed-dim: '#6bd8cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#fcdeb5'
  tertiary-fixed-dim: '#dec29a'
  on-tertiary-fixed: '#271901'
  on-tertiary-fixed-variant: '#574425'
  background: '#fcf8fa'
  on-background: '#1b1b1d'
  surface-variant: '#e4e2e4'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-main:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  data-tabular:
    fontFamily: Work Sans
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-caps:
    fontFamily: Work Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  sidebar-width: 260px
  header-height: 64px
---

## Brand & Style

The design system is anchored in the concept of "Operational Calm." As a risk intelligence platform, the interface must act as a stabilizing force during high-stress decision-making periods. The style is **Corporate Modern** with a lean towards **Minimalism**, stripping away decorative elements to prioritize data density and clarity.

The target audience consists of retail operations managers and security analysts who require a "heads-up display" of their entire infrastructure. The UI evokes a sense of control and reliability through high-contrast layouts, structured information architecture, and a disciplined use of color where saturation is reserved strictly for signal and status.

## Colors

This design system utilizes a high-contrast light mode palette to ensure maximum readability in well-lit operational centers. 

- **Primary & Secondary:** Deep Navy (#0F172A) provides a grounded, authoritative foundation for navigation, while Teal (#0D9488) acts as the primary action color.
- **Risk Scale:** A 5-step semantic ramp. Note that "Guarded" shifts toward a cooler blue-green to distinguish it from the "Fresh" status green.
- **Data Freshness:** Used for system heartbeats and timestamp indicators. These are secondary to risk levels and should be rendered as small pips or subtle text labels.
- **Neutrals:** The background uses a very light slate gray (#F8FAFC) to allow white cards to "pop" without relying on heavy shadows.

## Typography

The typography system prioritizes functional hierarchy. **Inter** is used for the majority of the UI to maintain a clean, neutral SaaS aesthetic. For data-heavy contexts—specifically tables, risk scores, and timestamps—**Work Sans** is employed with tabular figures enabled. This ensures that columns of numbers align perfectly, allowing for rapid scanning of values.

- **Headlines:** Use tight letter spacing and bold weights to establish clear section starts.
- **Labels:** Uppercase Work Sans is used for table headers and small metadata labels to create a distinct visual texture compared to body copy.

## Layout & Spacing

The layout follows a **Fixed-Fluid hybrid** model. The left sidebar and top header are fixed, while the main content area utilizes a fluid 12-column grid. 

- **Sidebar:** Dark-themed to visually separate navigation from the workspace.
- **Information Density:** A 4px baseline grid governs all spacing. For data tables, a "Compact" vertical rhythm is used (8px cell padding), while dashboard cards use "Relaxed" padding (24px) to provide mental breathing room between different data modules.
- **Modules:** Content is organized into cards with 16px gutters between them.

## Elevation & Depth

This design system uses **Tonal Layering** and **Low-contrast Outlines** rather than heavy shadows. 

- **Level 0 (Canvas):** The base background (#F8FAFC).
- **Level 1 (Cards/Surface):** Pure white (#FFFFFF) with a 1px border (#E2E8F0). No shadow.
- **Level 2 (Overlays/Dropdowns):** Pure white with a subtle, diffused shadow (0px 4px 12px rgba(0,0,0,0.05)) to indicate interactivity and temporary state.
- **Level 3 (Modals):** High-contrast modal surfaces with a 20% black backdrop blur to maintain focus on the task at hand.

## Shapes

The shape language is **Soft** and professional. A consistent 4px (0.25rem) corner radius is applied to buttons, input fields, and small badges. Larger containers, such as dashboard cards, use an 8px (0.5rem) radius. This subtle rounding maintains a modern feel without appearing too "playful" or consumer-oriented, preserving the platform’s serious operational tone.

## Components

- **Buttons:** Primary buttons use the Teal secondary color with white text. Secondary buttons use a Slate ghost style (border only).
- **Status Badges:** Use a "pill" shape with a subtle background tint (10% opacity of the semantic color) and high-contrast bold text of the same color for maximum accessibility.
- **Data Tables:** Should include fixed headers, hover states for rows, and integrated sparkline charts for "Trend" columns.
- **Cards:** Every card must feature a standard header with a title and an optional "Context Menu" (three dots) for settings or export.
- **Risk Indicators:** A large, numerical score (1-5) paired with a vertical color bar on the left side of the component to immediately signal severity.
- **System Status (Header):** A global "Heartbeat" indicator in the top right, using the Fresh/Cached/Stale color logic to show data latency.