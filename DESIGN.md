---
name: Vortex Tech-Noir
colors:
  surface: '#131314'
  surface-dim: '#131314'
  surface-bright: '#3a393a'
  surface-container-lowest: '#0e0e0f'
  surface-container-low: '#1c1b1c'
  surface-container: '#201f20'
  surface-container-high: '#2a2a2b'
  surface-container-highest: '#353436'
  on-surface: '#e5e2e3'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#e5e2e3'
  inverse-on-surface: '#313031'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#ffe083'
  on-secondary: '#3c2f00'
  secondary-container: '#eec200'
  on-secondary-container: '#645000'
  tertiary: '#bec6e0'
  on-tertiary: '#283044'
  tertiary-container: '#8990a8'
  on-tertiary-container: '#22293d'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#ffe083'
  secondary-fixed-dim: '#eec200'
  on-secondary-fixed: '#231b00'
  on-secondary-fixed-variant: '#574500'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#131314'
  on-background: '#e5e2e3'
  surface-variant: '#353436'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  title-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  mono-label:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  margin-mobile: 20px
  gutter-mobile: 12px
---

## Brand & Style
The design system embodies a "Tech-Noir" aesthetic tailored for a premium Telegram Mini App experience. It targets a sophisticated, tech-native audience that values speed, precision, and high-fidelity visuals within a mobile interface.

The style is a hybrid of **Minimalism** and **Glassmorphism**, utilizing deep obsidian surfaces punctuated by "electric" energy. The emotional response is one of exclusivity, power, and high-tech efficiency. Key visual drivers include:
- **Atmospheric Depth:** Layers are defined by light-bleed and transparency rather than heavy solid colors.
- **Kinetic Energy:** Subtle neon glows and high-contrast accents suggest a living, breathing system.
- **Haptic Precision:** Visual elements are sized and spaced to feel physically responsive to touch.

## Colors
The palette is rooted in the "Deepest Charcoal" (#0A0A0B) to ensure maximum contrast for OLED mobile displays. 

- **Primary (Electric Indigo):** Used for primary actions, active states, and core branding elements. It should feel like it's emitting light.
- **Secondary (Cyber Gold):** Reserved for high-value highlights, rare achievements, or critical warnings that require immediate visual attention.
- **Surface Strategy:** Backgrounds remain pure black or charcoal. Overlays use semi-transparent glass layers to maintain context of the depth beneath.
- **Glows:** Primary and Secondary colors should be used as soft, low-opacity radial gradients (10-15% opacity) behind key components to simulate a neon aura.

## Typography
The typography system balances the warmth of **Plus Jakarta Sans** with the technical rigor of **JetBrains Mono**.

- **Hierarchical Contrast:** Use Plus Jakarta Sans for all UI prose and headers to maintain readability and a premium feel. 
- **Technical Accents:** Use JetBrains Mono exclusively for data strings, transaction IDs, timestamps, and small labels. This reinforces the "tech-noir" developer-adjacent aesthetic.
- **Scale:** On mobile, avoid font sizes smaller than 12px for accessibility. Headlines should be bold and tightly spaced to feel impactful within the limited horizontal space of a Telegram Mini App.

## Layout & Spacing
This design system utilizes a **Mobile-First Fluid Grid** optimized for the Telegram Webview container.

- **Rhythm:** A 4px baseline grid ensures vertical consistency. 
- **Margins:** A standard 20px side margin is used to keep content away from the edges of the mobile screen, providing breathing room.
- **Safe Areas:** Account for the Telegram header (Close/More buttons) and the bottom "Main Button" area common in Mini Apps.
- **Touch Targets:** No interactive element should have a touch area smaller than 44x44px, regardless of its visual size.

## Elevation & Depth
Depth is expressed through **Glassmorphism** and **Tonal Stacking**. 

- **Level 0 (Base):** #0A0A0B (Pure Background).
- **Level 1 (Card/Surface):** rgba(255, 255, 255, 0.03) with a 1px solid stroke of rgba(255, 255, 255, 0.08). Apply a 12px Backdrop Blur.
- **Level 2 (Modals/Popovers):** rgba(255, 255, 255, 0.06) with a 20px Backdrop Blur and a subtle Electric Indigo outer glow (blur: 20px, opacity: 0.1).
- **Shadows:** Avoid traditional black shadows. Instead, use "Glow Shadows" where the shadow color matches the element's primary color at very low opacities to simulate light emission.

## Shapes
The shape language is "Smooth-Tech." Elements use a 0.5rem (8px) base radius to feel modern but structured.

- **Standard Elements:** 8px (rounded).
- **Large Containers/Cards:** 16px (rounded-lg).
- **Interactive Inputs:** 12px.
- **Buttons:** Fully pill-shaped (rounded-xl) to maximize the ergonomic feel for thumb-driven navigation.

## Components
Consistent implementation of the Tech-Noir aesthetic across core components:

- **Buttons:** 
  - *Primary:* Solid Electric Indigo fill with white text. High-contrast and haptic-responsive.
  - *Secondary:* Glass background with Electric Indigo border and text.
  - *Glow State:* On press, the button should increase its outer glow intensity.
- **Input Fields:** 
  - Darker-than-base background (#050505).
  - 1px border that transitions from neutral grey to Electric Indigo on focus.
  - Mono-spaced font for input text if data-heavy.
- **Chips/Status Indicators:** 
  - Small, pill-shaped with a subtle background tint and a high-contrast dot (e.g., Cyber Gold for "Pending").
- **Cards:** 
  - Utilize the Level 1 glass elevation. 
  - Top-left labels in JetBrains Mono for a "system readout" look.
- **Haptics:** 
  - Every button press and toggle switch should trigger a "Light" or "Medium" Telegram Haptic impact to reinforce the tactile nature of the UI.