"""Visual system for the dashboard: tokens, global CSS, and small HTML components.

Design idea: a banknote and a bank statement. Light paper, dark green ink, tabular figures so money lines
up, and one signature element (the guilloche pattern behind the net-worth hero, like the engraved lines on a
banknote). Everything else stays quiet.

Security: every string that comes from data (merchant names, account names, alerts) goes through
html.escape before it is placed in HTML, so a hostile merchant name can't inject markup.
"""
from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from html import escape
from typing import TYPE_CHECKING
from urllib.parse import quote

import altair as alt
import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from app.schemas import Account, CreditCard
    from app.services.alerts import Alert
    from app.services.subscriptions import Subscription

Formatter = Callable[[float], str]

# ---------------------------------------------------------------------------------------------- tokens
PAPER = "#F3F6F4"     # page background: cool mint-grey, like note paper
SURFACE = "#FFFFFF"   # panels
INK = "#10241C"       # body text: green-black ink
MUTED = "#5B6E66"     # secondary text
RULE = "#D9E2DD"      # hairlines and borders
NOTE = "#1F5E46"      # primary: banknote green
NOTE_SOFT = "#E3EEE8"
GAIN = "#1F7A4D"      # money in / good
LOSS = "#A3333D"      # money out / bad
BRASS = "#9A7425"     # needs attention

FONT = "Schibsted Grotesk"
FONT_STACK = f"{FONT}, system-ui, -apple-system, Segoe UI, sans-serif"

# Card faces: flat ink tones, no gradients. Cycled by index.
CARD_FACES = ["#1F3B32", "#3A3550", "#4A3B2A", "#26404F"]

# Category bars use tints of one hue, ordered by size, so the chart reads as one quantity, not a rainbow.
CATEGORY_SHADES = ["#1F5E46", "#2F7258", "#45876C", "#5F9B82", "#7DB09A", "#9DC4B2", "#BDD8CB"]


@dataclass(frozen=True)
class Tone:
    """Semantic color for a status (used by alerts, utilization, cash flow)."""
    fg: str
    bg: str


GOOD = Tone(GAIN, "#E4F1EA")
WARN = Tone(BRASS, "#F6EFDF")
BAD = Tone(LOSS, "#F6E4E6")
NEUTRAL = Tone(MUTED, "#ECF0EE")
PLAIN = Tone(INK, SURFACE)  # ordinary amounts


# ---------------------------------------------------------------------------------------------- guilloche
def _guilloche_svg(width: int = 720, height: int = 220, strands: int = 14) -> str:
    """Interleaved sine strands, the engraved security pattern on banknotes. Built once at import."""
    paths = []
    for k in range(strands):
        phase = k * math.pi / strands
        pts = []
        for x in range(0, width + 1, 6):
            t = x / width * 4 * math.pi
            y = height / 2 + (height * 0.36) * math.sin(t + phase) * math.cos(t / 2.3 - phase / 2)
            pts.append(f"{x},{y:.1f}")
        paths.append(f'<polyline points="{" ".join(pts)}"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" preserveAspectRatio="none">'
           f'<g fill="none" stroke="{NOTE}" stroke-width="0.7" opacity="0.2">{"".join(paths)}</g></svg>')
    # st.html strips inline <svg>, so the pattern ships as a CSS background image instead.
    return "data:image/svg+xml;utf8," + quote(svg)


GUILLOCHE_URL = _guilloche_svg()

# ---------------------------------------------------------------------------------------------- css
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;500;600;700;800&display=swap');

html, body, .stApp, .stMarkdown, button, input, textarea, select, [data-testid="stSidebar"] {{
  font-family: '{FONT}', system-ui, sans-serif !important;
}}
.stApp {{ background: {PAPER}; color: {INK}; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {RULE}; }}
.block-container {{ padding-top: 2.2rem; max-width: 1180px; }}

h1, h2, h3, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {{
  color: {INK}; font-weight: 700; letter-spacing: -0.01em;
}}
[data-testid="stHeading"] h3 {{ font-size: 1.15rem; margin-top: .4rem; }}

/* numbers line up in columns everywhere */
.stApp {{ font-variant-numeric: tabular-nums; }}

/* tabs: a plain underline, the selected tab in note green */
.stTabs [role="tablist"] {{ gap: 22px; border-bottom: 1px solid {RULE}; }}
.stTabs [role="tab"] {{ padding: 10px 0; height: auto; background: none; }}
.stTabs [role="tab"] p {{ font-weight: 600; font-size: .95rem; color: {MUTED}; }}
.stTabs [role="tab"][aria-selected="true"] p {{ color: {NOTE}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background: {NOTE}; height: 2px; }}

/* buttons */
.stButton button, [data-testid="stFormSubmitButton"] button {{ border-radius: 8px; font-weight: 600; }}
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button {{
  background: {NOTE}; border: 1px solid {NOTE}; color: #fff;
}}
.stButton button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button:hover {{
  background: #174A37; border-color: #174A37; color: #fff;
}}
.stButton button[kind="secondary"] {{ background: {SURFACE}; border: 1px solid {RULE}; color: {INK}; }}
.stButton button[kind="secondary"]:hover {{ border-color: {NOTE}; color: {NOTE}; }}
button:focus-visible, [role="tab"]:focus-visible {{ outline: 2px solid {NOTE}; outline-offset: 2px; }}

[data-testid="stProgress"] [role="progressbar"] > div > div > div {{ background: {NOTE} !important; }}
[data-testid="stMetric"] {{ background: {SURFACE}; border: 1px solid {RULE}; border-radius: 10px; padding: 12px 16px; }}
[data-testid="stDataFrame"] {{ border: 1px solid {RULE}; border-radius: 10px; overflow: hidden; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 10px; }}
[data-testid="stChatMessage"] {{ background: {SURFACE}; border: 1px solid {RULE}; border-radius: 12px; }}

/* ---------- hero: net worth over a guilloche band ---------- */
.hero {{
  position: relative; overflow: hidden; background: {SURFACE}; border: 1px solid {RULE}; border-radius: 14px;
  padding: 26px 30px; display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 32px;
}}
.hero {{ background-image: url("{GUILLOCHE_URL}"); background-size: max(100%, 720px) 230px;
  background-position: left 62%; background-repeat: no-repeat; }}
.hero .brand {{ font-weight: 700; color: {NOTE}; font-size: 1rem; }}
.hero .tagline {{ color: {MUTED}; font-size: .92rem; margin-top: 2px; max-width: 46ch; }}
.hero .nw-label {{ margin-top: 26px; color: {MUTED}; font-size: .95rem; }}
.hero .nw {{ font-size: clamp(2.6rem, 6vw, 4.2rem); font-weight: 800; letter-spacing: -0.03em; line-height: 1.02;
  color: {INK}; }}
.hero .source {{ margin-top: 12px; display: inline-block; font-size: .8rem; color: {MUTED};
  border: 1px solid {RULE}; background: {PAPER}; border-radius: 6px; padding: 3px 9px; }}

/* statement: label ..... amount */
.ledger {{ align-self: end; background: rgba(255,255,255,.88); border-radius: 10px; padding: 6px 4px; }}
.ledger .row {{ display: grid; grid-template-columns: auto 1fr auto; align-items: baseline; column-gap: 8px;
  padding: 9px 12px; }}
.ledger .row + .row {{ border-top: 1px solid {RULE}; }}
.ledger .lbl {{ color: {INK}; font-weight: 500; white-space: nowrap; }}
.ledger .lead {{ flex: 1; border-bottom: 1px dotted #A9B8B1; transform: translateY(-4px); min-width: 12px; }}
.ledger .amt {{ font-weight: 700; white-space: nowrap; }}
.ledger .note {{ grid-column: 1 / -1; color: {MUTED}; font-size: .78rem; text-align: right; }}

@media (max-width: 760px) {{
  .hero {{ grid-template-columns: 1fr; gap: 14px; padding: 22px 18px; }}
}}

/* ---------- lists ---------- */
.panel {{ background: {SURFACE}; border: 1px solid {RULE}; border-radius: 12px; overflow: hidden; }}
.item {{ display: flex; align-items: center; gap: 12px; padding: 12px 16px; }}
.item + .item {{ border-top: 1px solid {RULE}; }}
.item .main {{ min-width: 0; }}
.item .name {{ font-weight: 600; color: {INK}; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.item .sub {{ color: {MUTED}; font-size: .84rem; }}
.item .amt {{ margin-left: auto; font-weight: 700; white-space: nowrap; }}
.item .tag {{ font-size: .75rem; font-weight: 600; border-radius: 5px; padding: 2px 7px; white-space: nowrap; }}

/* alerts: a colored rule on the left says how serious */
.alert {{ border-left: 3px solid var(--fg); background: var(--bg); border-radius: 8px; padding: 12px 14px;
  margin-bottom: 8px; }}
.alert .t {{ font-weight: 650; color: {INK}; }}
.alert .d {{ color: {MUTED}; font-size: .9rem; margin-top: 2px; }}

/* ---------- credit card ---------- */
.cc {{ border-radius: 14px; padding: 18px 20px; color: #F2F5F3; min-height: 178px; margin-bottom: 14px;
  display: flex; flex-direction: column; gap: 6px; }}
.cc .top {{ display: flex; justify-content: space-between; gap: 10px; font-weight: 600; font-size: .92rem; }}
.cc .top span:last-child {{ opacity: .7; font-weight: 500; }}
.cc .bal {{ font-size: 1.7rem; font-weight: 800; margin-top: 10px; letter-spacing: -0.02em; }}
.cc .of {{ font-size: .84rem; opacity: .78; }}
.cc .bar {{ height: 4px; border-radius: 4px; background: rgba(255,255,255,.2); margin: 8px 0 6px; overflow: hidden; }}
.cc .bar > div {{ height: 100%; background: var(--util); }}
.cc .meta {{ display: flex; gap: 14px; flex-wrap: wrap; font-size: .8rem; opacity: .85; margin-top: auto; }}

/* small summary figures (cards / subscriptions tabs) */
.figures {{ display: flex; gap: 34px; flex-wrap: wrap; margin: 6px 0 18px; }}
.figure .v {{ font-size: 1.6rem; font-weight: 800; color: {INK}; letter-spacing: -0.02em; }}
.figure .l {{ color: {MUTED}; font-size: .86rem; }}

@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; animation: none !important; }} }}
</style>
"""


def inject_css() -> None:
    st.html(CSS)


# ---------------------------------------------------------------------------------------------- components
@dataclass(frozen=True)
class LedgerRow:
    label: str
    amount: str
    tone: Tone = NEUTRAL
    note: str = ""


def hero(brand: str, tagline: str, net_worth: str, source: str, rows: Sequence[LedgerRow]) -> None:
    ledger = "".join(
        f'<div class="row"><span class="lbl">{escape(r.label)}</span><span class="lead"></span>'
        f'<span class="amt" style="color:{r.tone.fg}">{escape(r.amount)}</span>'
        + (f'<span class="note">{escape(r.note)}</span>' if r.note else "")
        + "</div>"
        for r in rows)
    st.html(f"""
    <section class="hero" aria-label="Net worth summary">
      <div>
        <div class="brand">{escape(brand)}</div>
        <div class="tagline">{escape(tagline)}</div>
        <div class="nw-label">Net worth</div>
        <div class="nw">{escape(net_worth)}</div>
        <span class="source">{escape(source)}</span>
      </div>
      <div class="ledger">{ledger}</div>
    </section>""")


def figures(items: Iterable[tuple[str, str]]) -> None:
    """A row of big numbers with a plain label underneath: [(value, label), ...]."""
    body = "".join(f'<div class="figure"><div class="v">{escape(v)}</div><div class="l">{escape(lbl)}</div></div>'
                   for v, lbl in items)
    st.html(f'<div class="figures">{body}</div>')


def alert_list(alerts: Sequence[Alert]) -> None:
    if not alerts:
        st.html(f'<div class="alert" style="--fg:{GOOD.fg};--bg:{GOOD.bg}"><div class="t">Nothing needs your attention'
                '</div><div class="d">No unusual charges, upcoming due dates, or high utilization.</div></div>')
        return
    out = []
    for a in alerts:
        tone = WARN if a.level == "warning" else NEUTRAL
        out.append(f'<div class="alert" style="--fg:{tone.fg};--bg:{tone.bg}">'
                   f'<div class="t">{escape(a.title)}</div><div class="d">{escape(a.detail)}</div></div>')
    st.html("".join(out))


LIABILITY_TYPES = ("credit", "loan")


def account_list(accounts: Sequence[Account], money: Formatter) -> None:
    rows = []
    for a in accounts:
        owed = a.type in LIABILITY_TYPES
        amt = -a.balance if owed else a.balance
        kind = (a.subtype or a.type).replace("_", " ").capitalize()
        rows.append(f'<div class="item"><div class="main"><div class="name">{escape(a.name)}</div>'
                    f'<div class="sub">{escape(a.institution)}, {escape(kind)}</div></div>'
                    f'<div class="amt" style="color:{LOSS if owed else INK}">{escape(money(amt))}</div></div>')
    st.html(f'<div class="panel">{"".join(rows)}</div>')


def short_date(d: date) -> str:
    """Nov 4. Built by hand because strftime's %-d doesn't work on Windows."""
    return f"{d:%b} {d.day}"


def utilization_tone(pct: float) -> Tone:
    return GOOD if pct < 10 else WARN if pct < 30 else BAD


def credit_card(c: CreditCard, idx: int, money: Formatter) -> None:
    face = CARD_FACES[idx % len(CARD_FACES)]
    pct = c.utilization_pct or 0
    util_color = {GOOD: "#8FD3AE", WARN: "#E6C677", BAD: "#EF9AA2"}[utilization_tone(pct)]
    meta = []
    if c.apr is not None:
        meta.append(f"APR {c.apr:.2f}%")
        meta.append(f"about {money(c.balance * c.apr / 100 / 12)} interest a month")
    if c.minimum_payment is not None:
        meta.append(f"Minimum {money(c.minimum_payment)}")
    if c.next_due_date:
        meta.append(f"Due {short_date(c.next_due_date)}")
    st.html(f"""
    <div class="cc" style="background:{face};--util:{util_color}">
      <div class="top"><span>{escape(c.name)}</span><span>Credit</span></div>
      <div class="bal">{escape(money(c.balance))}</div>
      <div class="of">{pct:.1f}% of {escape(money(c.limit or 0))} limit</div>
      <div class="bar" role="img" aria-label="{pct:.0f}% utilization"><div style="width:{min(pct, 100):.1f}%"></div></div>
      <div class="meta">{''.join(f'<span>{escape(m)}</span>' for m in meta)}</div>
    </div>""")


def subscription_list(subs: Sequence[Subscription], money: Formatter, pretty: Callable[[str], str]) -> None:
    rows = []
    for s in subs:
        rows.append(f'<div class="item"><div class="main"><div class="name">{escape(s.merchant)}</div>'
                    f'<div class="sub">{escape(pretty(s.category))}, next charge '
                    f'{escape(short_date(date.fromisoformat(s.next_expected)))}</div></div>'
                    f'<div class="amt">{escape(money(s.amount))}<span class="sub"> a month</span></div></div>')
    st.html(f'<div class="panel">{"".join(rows)}</div>')


# ---------------------------------------------------------------------------------------------- charts
def _style(chart: alt.Chart) -> alt.Chart:
    return (chart.properties(background="transparent")
            .configure_view(stroke=None)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor=RULE, domain=False, tickColor="transparent",
                            labelFontSize=12, labelLimit=220, labelFont=FONT_STACK)
            .configure_text(font=FONT_STACK))


def category_chart(by_category: dict[str, float], pretty: Callable[[str], str]) -> None:
    df = pd.DataFrame({"Category": [pretty(c) for c in by_category], "Spent": list(by_category.values())})
    shades = [CATEGORY_SHADES[min(i, len(CATEGORY_SHADES) - 1)] for i in range(len(df))]
    bars = alt.Chart(df).mark_bar(cornerRadiusEnd=3, height=18).encode(
        y=alt.Y("Category:N", sort="-x", title=None),
        x=alt.X("Spent:Q", title=None, axis=alt.Axis(format="$,.0f")),
        color=alt.Color("Category:N", scale=alt.Scale(domain=df["Category"].tolist(), range=shades), legend=None),
        tooltip=[alt.Tooltip("Category:N"), alt.Tooltip("Spent:Q", format="$,.2f")],
    ).properties(height=max(160, 34 * len(df)))
    st.altair_chart(_style(bars), width="stretch")


def daily_chart(daily: pd.DataFrame) -> None:
    df = daily.reset_index()
    df["Date"] = pd.to_datetime(df["Date"])
    bar_px = max(2, min(18, int(560 / max(len(df), 1) * 0.6)))  # thicker bars for shorter ranges
    bars = alt.Chart(df).mark_bar(color=NOTE, size=bar_px, cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
        x=alt.X("Date:T", title=None, axis=alt.Axis(format="%b %-d")),
        y=alt.Y("Spent:Q", title=None, axis=alt.Axis(format="$,.0f")),
        tooltip=[alt.Tooltip("Date:T", format="%a %b %-d"), alt.Tooltip("Spent:Q", format="$,.2f")],
    ).properties(height=200)
    st.altair_chart(_style(bars), width="stretch")


CARD_LINE_COLORS = [NOTE, BRASS, "#3A6FA0", LOSS, "#6B5B95", "#2F8F83"]


def payoff_chart(plans: dict[str, dict[str, list[float]]]) -> None:
    """One panel per strategy, one line per card, so you can see which card hits $0 first under each plan."""
    rows = [{"Plan": plan, "Card": card, "Month": m, "Owed": v}
            for plan, cards in plans.items() for card, values in cards.items() for m, v in enumerate(values)]
    df = pd.DataFrame(rows)
    cards = list(dict.fromkeys(df["Card"]))
    lines = alt.Chart(df).mark_line(strokeWidth=2.5).encode(
        x=alt.X("Month:Q", title="Months from now", axis=alt.Axis(tickMinStep=1, format="d")),
        y=alt.Y("Owed:Q", title=None, axis=alt.Axis(format="$,.0f")),
        color=alt.Color("Card:N", scale=alt.Scale(domain=cards, range=CARD_LINE_COLORS[:len(cards)] or [NOTE]),
                        legend=alt.Legend(title=None, orient="top")),
        tooltip=[alt.Tooltip("Plan:N"), alt.Tooltip("Card:N"), alt.Tooltip("Month:Q"),
                 alt.Tooltip("Owed:Q", format="$,.2f")],
    ).properties(height=210, width=360).facet(
        column=alt.Column("Plan:N", title=None, sort=list(plans),
                          header=alt.Header(labelFontSize=14, labelFontWeight=600, labelColor=INK, labelFont=FONT_STACK)),
    )
    st.altair_chart(_style(lines), width="stretch")
