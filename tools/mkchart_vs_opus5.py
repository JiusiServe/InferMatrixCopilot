"""Render the arm-vs-Opus-5 comparison as a static SVG for the PR description.

GitHub serves repo SVGs through its image proxy, so the output uses presentation
attributes only -- no <style> block, no script, no external font -- and paints an
explicit background so it stays legible under both GitHub themes.
"""
import html

# (label, sublabel, group, n, dr, drlo, drhi, dp, dplo, dphi, mark)
ROWS = [
    # --- this PR's pipeline, Composer 2.5, train n=10 ---
    ("v17cb", "Composer 2.5 on v17",              "ver", 10, -0.052, -0.165,  0.061, -0.097, -0.215,  0.021, ""),
    ("v19cb", "dedupe + anchor fix",              "ver", 10, -0.092, -0.193,  0.009,  0.060, -0.053,  0.172, ""),
    ("v20cb", "merge-richest",                    "ver", 10, -0.005, -0.176,  0.167,  0.046, -0.083,  0.175, "champion"),
    ("v21cb", "claim headlines",                  "ver", 10, -0.093, -0.178, -0.007,  0.079, -0.006,  0.164, "reverted"),
    ("v22cb", "mechanism depth",                  "ver", 10, -0.082, -0.153, -0.011,  0.040, -0.084,  0.163, "reverted"),
    ("v23cb", "breadth sweep lens",               "ver", 10, -0.093, -0.191,  0.004,  0.024, -0.073,  0.122, "reverted"),
    # --- other generators, same pipeline family, same judge ---
    ("DeepSeek v4-pro", "v17 clean · train",      "mod", 10,  0.024, -0.030,  0.077,  0.016, -0.061,  0.093, ""),
    ("DeepSeek + dsh",  "v18 native tools · val", "mod",  5,  0.038, -0.055,  0.131,  0.023, -0.096,  0.142, "best recall"),
    ("DeepSeek v4-pro", "v13 · wave-2",           "mod", 10, -0.115, -0.225, -0.004,  0.040,  0.000,  0.080, ""),
    ("grok-4.6",        "wave-2",                 "mod", 10, -0.080, -0.189,  0.029,  0.004, -0.059,  0.067, ""),
    ("Composer 2.5",    "wave-2 standalone",      "mod", 10, -0.127, -0.203, -0.050, -0.048, -0.103,  0.007, ""),
    ("grok-4.5",        "wave-2",                 "mod", 10, -0.164, -0.271, -0.057,  0.030, -0.024,  0.085, ""),
    ("MiMo v2.5",       "wave-2",                 "mod", 10, -0.212, -0.358, -0.067, -0.084, -0.175,  0.007, ""),
]

RES_R, RES_P = 0.099, 0.115          # 95% half-width at n=10, from observed item sd
INK, INK2, MUTED = "#14171A", "#454D52", "#6B747A"
RULE, BAND, PAPER, PANEL = "#E1E5E4", "#ECEFF1", "#FFFFFF", "#FAFBFA"
ABOVE, BELOW, CHAMP = "#00897B", "#B34A2F", "#7A5AA8"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

LAB, PAN, GAP, RH = 208, 250, 58, 30
TOP, BOT, PADX = 116, 56, 22
RPAD = 58                                   # value labels live here
HDR = 38                                    # group header height
n_hdr = 2
W = PADX * 2 + LAB + PAN * 2 + GAP + RPAD
H = TOP + len(ROWS) * RH + n_hdr * HDR + BOT
LO, HI = -0.40, 0.26

o = []
A = o.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
  f'viewBox="0 0 {W} {H}" font-family="{MONO}" role="img" '
  f'aria-label="Paired recall and precision differences against the Claude Code plus Opus 5 baseline">')
A(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')

A(f'<text x="{PADX}" y="30" font-size="15" font-weight="700" fill="{INK}">'
  'Strict PR review — paired &#916; vs Claude Code + Opus 5</text>')
A(f'<text x="{PADX}" y="49" font-size="10.5" fill="{MUTED}">'
  'blind judge claude-sonnet-5 &#183; 3 replicates &#183; paired inside each verdict, '
  'clustered by item &#183; whisker = 95% CI</text>')
A(f'<text x="{PADX}" y="64" font-size="10.5" fill="{MUTED}">'
  'shaded band = effects this dataset cannot resolve at n=10 '
  '(&#177;0.099 recall, &#177;0.115 precision, from the observed item-level spread)</text>')


def panx(i):
    return PADX + LAB + i * (PAN + GAP)


def sx(v, i):
    return panx(i) + (v - LO) / (HI - LO) * PAN


plot_h = len(ROWS) * RH + n_hdr * HDR
for i, (title, res) in enumerate((("&#916; RECALL", RES_R), ("&#916; PRECISION", RES_P))):
    A(f'<rect x="{panx(i)}" y="{TOP-12}" width="{PAN}" height="{plot_h+4}" fill="{PANEL}"/>')
    A(f'<rect x="{sx(-res,i):.1f}" y="{TOP-12}" width="{sx(res,i)-sx(-res,i):.1f}" '
      f'height="{plot_h+4}" fill="{BAND}"/>')
    A(f'<text x="{panx(i)}" y="{TOP-26}" font-size="10.5" letter-spacing="1.3" '
      f'fill="{MUTED}" font-weight="600">{title}</text>')
    for v in (-0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2):
        x, zero = sx(v, i), v == 0
        A(f'<line x1="{x:.1f}" y1="{TOP-12}" x2="{x:.1f}" y2="{TOP+plot_h-8}" '
          f'stroke="{"#8A9299" if zero else RULE}" stroke-width="{1.4 if zero else 0.8}"/>')
        A(f'<text x="{x:.1f}" y="{TOP+plot_h+14}" font-size="9" fill="{MUTED}" '
          f'text-anchor="middle">{"0" if zero else f"{v:.1f}"}</text>')

y = TOP
groups = {"ver": "THIS PR &#183; PIPELINE VERSIONS (Composer 2.5, train n=10)",
          "mod": "OTHER GENERATORS (same pipeline family, same judge)"}
seen = set()
for (lab, sub, grp, n, dr, drl, drh, dp, dpl, dph, mark) in ROWS:
    if grp not in seen:
        seen.add(grp)
        A(f'<text x="{PADX}" y="{y+26}" font-size="9.5" letter-spacing="1.1" '
          f'font-weight="700" fill="{MUTED}">{groups[grp]}</text>')
        A(f'<line x1="{PADX}" y1="{y+32}" x2="{W-PADX}" y2="{y+32}" stroke="{RULE}" stroke-width="1"/>')
        y += HDR
    cy = y + RH / 2
    champ = mark == "champion"
    A(f'<text x="{PADX}" y="{cy-1:.1f}" font-size="11.5" font-weight="{700 if champ else 600}" '
      f'fill="{CHAMP if champ else INK}">{html.escape(lab)}'
      f'{" &#9733;" if champ else " &#8629;" if mark == "reverted" else ""}</text>')
    A(f'<text x="{PADX}" y="{cy+11:.1f}" font-size="9" fill="{MUTED}">'
      f'{html.escape(sub)}  n={n}{"  &#183; " + mark if mark and not champ else ""}</text>')
    for k, (v, a, b) in enumerate(((dr, drl, drh), (dp, dpl, dph))):
        col = CHAMP if champ else (ABOVE if v >= 0 else BELOW)
        A(f'<line x1="{sx(a,k):.1f}" y1="{cy:.1f}" x2="{sx(b,k):.1f}" y2="{cy:.1f}" '
          f'stroke="{col}" stroke-width="2" stroke-linecap="round" opacity="0.5"/>')
        for t in (a, b):
            A(f'<line x1="{sx(t,k):.1f}" y1="{cy-4:.1f}" x2="{sx(t,k):.1f}" y2="{cy+4:.1f}" '
              f'stroke="{col}" stroke-width="2" opacity="0.5"/>')
        A(f'<circle cx="{sx(v,k):.1f}" cy="{cy:.1f}" r="4.4" fill="{col}" '
          f'stroke="{PANEL}" stroke-width="1.6"/>')
        A(f'<text x="{panx(k)+PAN+7}" y="{cy+3.5:.1f}" font-size="9.5" fill="{INK2}">'
          f'{v:+.3f}</text>')
    y += RH

ly = H - 26
A(f'<circle cx="{PADX+5}" cy="{ly-3}" r="4.4" fill="{ABOVE}"/>')
A(f'<text x="{PADX+16}" y="{ly}" font-size="9.5" fill="{MUTED}">above baseline</text>')
A(f'<circle cx="{PADX+128}" cy="{ly-3}" r="4.4" fill="{BELOW}"/>')
A(f'<text x="{PADX+139}" y="{ly}" font-size="9.5" fill="{MUTED}">below baseline</text>')
A(f'<circle cx="{PADX+251}" cy="{ly-3}" r="4.4" fill="{CHAMP}"/>')
A(f'<text x="{PADX+262}" y="{ly}" font-size="9.5" fill="{MUTED}">current champion</text>')
A(f'<rect x="{PADX+390}" y="{ly-9}" width="17" height="11" fill="{BAND}" stroke="{RULE}"/>')
A(f'<text x="{PADX+413}" y="{ly}" font-size="9.5" fill="{MUTED}">unresolvable at this n</text>')
A('</svg>')

out = "\n".join(o)
open("doc/assets/strict-review-vs-opus5.svg", "w", encoding="utf-8").write(out)
print("wrote doc/assets/strict-review-vs-opus5.svg", len(out), "bytes;", len(ROWS), "rows")
