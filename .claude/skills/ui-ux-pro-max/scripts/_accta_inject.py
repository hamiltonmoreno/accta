#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACCTA brand injector (idempotent UPSERT).

Seeds ACCTA-brand-locked rows into the UI/UX Pro Max CSV datasets so the
BM25 + reasoning engine resolves every ACCTA query to the ACCTA design system:
NEUTRAL-LED foundation (white / #F5F5F5, Grafite #3A3A3A text) with a SINGLE
restrained Carmesim #C7202F accent, Open Sans, NO dark mode, shadcn/ui.

The token "accta" is unique to these rows -> very high IDF -> any query that
contains "accta" ranks these rows #1 across product/color/typography/landing.

Upsert by sentinel: the sentinel string identifies this skill's own row in
each file (it never appears in the header nor in any stock row), so the line
that contains it is replaced. Every other line — including any pre-existing
malformed stock row — is preserved byte-for-byte. Re-running is safe.
Run:  python scripts/_accta_inject.py
"""

import csv
import io
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# (filename, sentinel uniquely identifying THIS row in THAT file, row_dict)
ROWS = [
    ("products.csv", "ACCTA Portal", {
        "No": "97",
        "Product Type": "ACCTA Portal",
        "Keywords": ("accta, portal, associacao, associação, socios, sócios, "
                     "financeiro, moderador, admin, carteira, mural, "
                     "transparencia, transparência, eventos, votacao, votação, "
                     "dashboard, member portal, institutional, non-profit"),
        "Primary Style Recommendation": "Swiss Modernism + Flat Design",
        "Secondary Styles": "Minimalism, Glassmorphism (sparingly)",
        "Landing Page Pattern": "ACCTA Portal Pattern",
        "Dashboard Style (if applicable)": "Data-Dense + Stat Cards + Activity Feed",
        "Color Palette Focus": ("Neutral foundation (white/#F5F5F5, Grafite #3A3A3A) "
                                "+ single restrained Carmesim #C7202F accent. NO dark mode."),
        "Key Considerations": ("ACCTA brand-locked, neutral-led. Carmesim ONLY on the one "
                               "primary CTA/active/links-on-white/destructive — never every "
                               "button, never red text on dark. Open Sans, shadcn/ui, light "
                               "mode only, WCAG AA. Canonical: /frontend-design."),
    }),
    ("colors.csv", "ACCTA Portal", {
        "No": "97",
        "Product Type": "ACCTA Portal",
        "Primary (Hex)": "#C7202F",
        "Secondary (Hex)": "#3A3A3A",
        "CTA (Hex)": "#C7202F",
        "Background (Hex)": "#FFFFFF",
        "Text (Hex)": "#3A3A3A",
        "Border (Hex)": "#E5E7EB",
        # Keep concise: BM25 length-normalizes, so a bloated Notes field sinks
        # this row in the color domain. Full rationale lives in /frontend-design.
        "Notes": ("ACCTA brand-locked. accta portal associacao socios. Neutral-led: "
                  "white #FFFFFF / #F5F5F5 surfaces, Grafite #3A3A3A text, muted "
                  "#6B7280 min. Carmesim #C7202F = single accent (hover #A51B27): "
                  "only one primary CTA/active/links-on-white/destructive. Never red "
                  "on dark, never every button red. No dark mode. See /frontend-design."),
    }),
    ("typography.csv", "ACCTA Open Sans", {
        "No": "58",
        "Font Pairing Name": "ACCTA Open Sans",
        "Category": "Sans + Sans",
        "Heading Font": "Open Sans",
        "Body Font": "Open Sans",
        "Mood/Style Keywords": ("accta, portal, professional, institutional, clean, "
                                "readable, associacao, socios, corporate, trustworthy"),
        "Best For": "ACCTA Portal, associacao dashboards, member portals, institutional apps",
        "Google Fonts URL": "https://fonts.google.com/share?selection.family=Open+Sans:wght@300;400;500;600;700;800",
        "CSS Import": ("@import url('https://fonts.googleapis.com/css2?family=Open+Sans:"
                       "wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');"),
        "Tailwind Config": "fontFamily: { sans: ['Open Sans', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] }",
        "Notes": ("ACCTA brand-locked. accta portal. Open Sans for headings + body "
                  "(max 2 weights per section). JetBrains Mono for code/monospace only."),
    }),
    ("ui-reasoning.csv", "ACCTA Portal", {
        "No": "101",
        "UI_Category": "ACCTA Portal",
        "Recommended_Pattern": "Dashboard Stat Cards + Charts + Activity Feed",
        "Style_Priority": "Swiss Modernism + Flat Design + Minimalism",
        "Color_Mood": ("Neutral foundation (white/#F5F5F5, Grafite #3A3A3A) + single "
                       "restrained Carmesim #C7202F accent (max 1 primary per view)"),
        "Typography_Mood": "Open Sans clean hierarchy + max 2 weights",
        "Key_Effects": ("Framer Motion fadeIn+slideUp (y:20->0, 0.3s) + staggerChildren "
                        "0.05 + hover scale 1.02 (0.2s) + visible focus-visible ring + subtle"),
        "Decision_Rules": ('{"always": "neutral-led-single-accent", "never": "dark-mode", '
                           '"never2": "red-text-on-dark", "primitives": "shadcn-ui", '
                           '"canonical": "frontend-design-skill"}'),
        "Anti_Patterns": ("Dark mode + Red text on dark or colored backgrounds + Every "
                          "button red + Flat black backgrounds + Off-brand colors + "
                          "Accent on large surfaces + Text lighter than #6B7280 + "
                          "Color-only status + Custom UI primitives + More than 2 font "
                          "weights per section + Inadimplente status"),
        "Severity": "CRITICAL",
    }),
    ("landing.csv", "ACCTA Portal Pattern", {
        "No": "31",
        "Pattern Name": "ACCTA Portal Pattern",
        "Keywords": "accta, portal, associacao, socios, member, dashboard, institutional, transparencia",
        "Section Order": ("1. Topbar + sidebar nav (light), 2. Page header with actions, "
                          "3. Stat cards grid, 4. Charts + tables, 5. Activity feed / empty state"),
        "Primary CTA Placement": "Page header — single Carmesim #C7202F button; other actions neutral",
        "Color Strategy": ("Neutral-led: white #FFFFFF / #F5F5F5 surfaces, Grafite "
                           "#3A3A3A text. Carmesim #C7202F ONLY for the one primary "
                           "action + active state. Secondary buttons neutral "
                           "(border #D1D5DB). Navy #1e3a5f marketing hero only, white "
                           "text. NEVER red on dark. No dark mode."),
        "Recommended Effects": ("Framer Motion fadeIn+slideUp, staggerChildren 0.05, "
                                "hover scale 1.02, shadow-sm to shadow-lg, visible focus ring"),
        "Conversion Optimization": ("Internal portal: clarity over conversion, strict "
                                    "hierarchy (one accent). shadcn/ui primitives, toast "
                                    "feedback, audit-logged admin actions."),
    }),
]


def header_fields(path: Path) -> list:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


def csv_line(path: Path, row: dict) -> str:
    fields = header_fields(path)
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow([row.get(c, "") for c in fields])
    return buf.getvalue()


def upsert(path: Path, sentinel: str, row: dict) -> str:
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")
    header, body = lines[0], lines[1:]
    removed = sum(1 for ln in body if ln != "" and sentinel in ln)
    # Keep every stock row byte-for-byte; drop only our prior row + the blank tail.
    kept = [ln for ln in body if ln != "" and sentinel not in ln]
    new_line = csv_line(path, row).rstrip("\n")
    out = "\n".join([header] + kept + [new_line]) + "\n"
    path.write_text(out, encoding="utf-8")
    action = "replaced" if removed else "inserted"
    return f"{path.name}: ACCTA row {action} ({len(kept) + 1} data rows)"


if __name__ == "__main__":
    for fname, sentinel, row in ROWS:
        print(upsert(DATA / fname, sentinel, row))
