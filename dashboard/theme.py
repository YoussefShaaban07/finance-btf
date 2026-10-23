"""Colors, CSS, and colorful HTML components for the dashboard.

Every piece of text that comes from data (merchant names, goal names, alerts) is passed through
html.escape before it goes into HTML, so a sneaky merchant name can't inject markup (Event 4!).
"""
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

VIOLET, PINK, ORANGE, AMBER = "#8B5CF6", "#EC4899", "#FB923C", "#FBBF24"
GREEN, CYAN, BLUE, RED = "#34D399", "#22D3EE", "#60A5FA", "#F87171"

CATEGORY_COLORS = {
    "GENERAL_MERCHANDISE": PINK, "RENT_AND_UTILITIES": VIOLET, "FOOD_AND_DRINK": ORANGE,
    "TRANSPORTATION": CYAN, "ENTERTAINMENT": AMBER, "GENERAL_SERVICES": BLUE, "PERSONAL_CARE": GREEN,
    "TRAVEL": "#A78BFA", "MEDICAL": RED, "LOAN_PAYMENTS": "#94A3B8", "INCOME": GREEN,
}
FALLBACK = [VIOLET, PINK, CYAN, ORANGE, GREEN, AMBER, BLUE, RED]
CATEGORY_ICONS = {
    "GENERAL_MERCHANDISE": "🛍️", "RENT_AND_UTILITIES": "🏠", "FOOD_AND_DRINK": "🍔", "TRANSPORTATION": "🚗",
    "ENTERTAINMENT": "🎬", "GENERAL_SERVICES": "🧾", "PERSONAL_CARE": "💪", "TRAVEL": "✈️", "MEDICAL": "🩺",
    "INCOME": "💰",
}
CARD_GRADIENTS = [
    ("#7C3AED", "#2563EB"),  # violet → blue
    ("#DB2777", "#F97316"),  # pink → orange
    ("#0891B2", "#10B981"),  # cyan → green
    ("#9333EA", "#EC4899"),  # purple → pink
]


def cat_color(cat: str, i: int = 0) -> str:
    return CATEGORY_COLORS.get(cat, FALLBACK[i % len(FALLBACK)])


def cat_icon(cat: str) -> str:
    return CATEGORY_ICONS.get(cat, "💳")


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, .stApp, .stMarkdown, button, input, textarea, select {{ font-family: 'Plus Jakarta Sans', sans-serif !important; }}
.stApp {{
  background:
    radial-gradient(1100px 520px at 0% -10%, rgba(139,92,246,.28), transparent 60%),
    radial-gradient(900px 480px at 100% 0%, rgba(236,72,153,.20), transparent 60%),
    radial-gradient(800px 500px at 50% 110%, rgba(34,211,238,.12), transparent 60%),
    #0B1020;
}}
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #1C1147 0%, #111733 60%, #0B1020 100%);
  border-right: 1px solid rgba(139,92,246,.35);
}}
[data-testid="stHeader"] {{ background: transparent; }}

/* headings get a gradient */
[data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {{
  background: linear-gradient(90deg, {CYAN}, {VIOLET} 50%, {PINK});
  -webkit-background-clip: text; background-clip: text; color: transparent !important; font-weight: 800;
}}

/* pill tabs */
.stTabs [role="tablist"] {{ gap: 8px; flex-wrap: wrap; border-bottom: none; }}
.stTabs [role="tab"] {{
  background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.08);
  border-radius: 999px; padding: 8px 16px; height: auto; transition: all .15s ease;
}}
.stTabs [role="tab"]:hover {{ border-color: {VIOLET}; }}
.stTabs [role="tab"][aria-selected="true"] {{
  background: linear-gradient(90deg, {VIOLET}, {PINK}); border-color: transparent; color: #fff !important;
  box-shadow: 0 6px 20px rgba(236,72,153,.35);
}}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"],
.stTabs [role="tablist"] + div:empty {{ display: none; }}
.stTabs [role="tab"] p {{ font-weight: 600; }}

/* buttons */
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button {{
  background: linear-gradient(90deg, {VIOLET}, {PINK}); border: none; color: #fff; font-weight: 700;
  box-shadow: 0 6px 18px rgba(139,92,246,.35);
}}
.stButton button[kind="secondary"] {{
  border: 1px solid rgba(139,92,246,.45); background: rgba(139,92,246,.08);
}}
.stButton button[kind="secondary"]:hover {{ border-color: {PINK}; color: {PINK}; }}

/* progress bars: rainbow fill */
[data-testid="stProgress"] [role="progressbar"] > div > div > div {{
  background: linear-gradient(90deg, {CYAN}, {VIOLET}, {PINK}) !important;
}}

/* leftover st.metric boxes */
[data-testid="stMetric"] {{
  background: linear-gradient(160deg, rgba(139,92,246,.16), rgba(236,72,153,.08));
  border: 1px solid rgba(139,92,246,.35); border-radius: 16px; padding: 14px 18px;
}}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 18px; }}
[data-testid="stDataFrame"] {{ border-radius: 14px; overflow: hidden; border: 1px solid rgba(139,92,246,.25); }}
[data-testid="stChatMessage"] {{
  background: rgba(255,255,255,.04); border: 1px solid rgba(139,92,246,.22); border-radius: 18px;
}}
[data-testid="stChatInput"] textarea {{ border-radius: 14px; }}

/* ---------- custom components ---------- */
.hero {{
  background: linear-gradient(120deg, #7C3AED 0%, #DB2777 55%, #F97316 100%);
  border-radius: 26px; padding: 28px 32px; color: #fff; position: relative; overflow: hidden;
  display: flex; justify-content: space-between; align-items: center; gap: 24px; flex-wrap: wrap;
  box-shadow: 0 20px 50px rgba(219,39,119,.30);
}}
.hero::after {{
  content: ""; position: absolute; right: -60px; top: -60px; width: 240px; height: 240px; border-radius: 50%;
  background: rgba(255,255,255,.12);
}}
.hero h1 {{ font-size: 2.3rem; font-weight: 800; margin: 0; color: #fff; padding: 0; line-height: 1.1; }}
.hero p {{ margin: 6px 0 0; opacity: .9; }}
.hero .chip {{ display: inline-block; margin-top: 12px; padding: 4px 12px; border-radius: 999px;
  background: rgba(0,0,0,.22); font-size: .78rem; font-weight: 600; }}
.hero .nw {{ text-align: right; z-index: 1; }}
.hero .nw .label {{ font-size: .8rem; text-transform: uppercase; letter-spacing: .12em; opacity: .85; font-weight: 700; }}
.hero .nw .value {{ font-size: 2.8rem; font-weight: 800; line-height: 1.1; }}

.stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin: 18px 0 8px; }}
.stat {{
  background: #131A33; border-radius: 18px; padding: 16px 18px; position: relative; overflow: hidden;
  border: 1px solid rgba(255,255,255,.06);
}}
.stat::before {{ content: ""; position: absolute; inset: 0 0 auto 0; height: 4px; background: var(--c); }}
.stat::after {{ content: ""; position: absolute; right: -30px; bottom: -30px; width: 110px; height: 110px;
  border-radius: 50%; background: var(--c); opacity: .13; }}
.stat .icon {{ font-size: 1.4rem; }}
.stat .label {{ color: #A9B1D6; font-size: .78rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; margin-top: 4px; }}
.stat .value {{ color: #fff; font-size: 1.6rem; font-weight: 800; }}
.stat .sub {{ color: var(--c); font-size: .82rem; font-weight: 700; }}

.alert-card {{
  border-radius: 16px; padding: 14px 16px; margin-bottom: 10px; display: flex; gap: 12px; align-items: flex-start;
  background: linear-gradient(90deg, color-mix(in srgb, var(--c) 22%, transparent), rgba(255,255,255,.02));
  border: 1px solid color-mix(in srgb, var(--c) 55%, transparent);
}}
.alert-card .icon {{ font-size: 1.4rem; }}
.alert-card .t {{ font-weight: 800; color: #fff; }}
.alert-card .d {{ color: #D5D9EE; font-size: .9rem; }}

.acct {{ display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 14px;
  background: rgba(255,255,255,.035); margin-bottom: 8px; border-left: 4px solid var(--c); }}
.acct .icon {{ font-size: 1.3rem; }}
.acct .name {{ font-weight: 700; color: #fff; }}
.acct .kind {{ color: #A9B1D6; font-size: .78rem; }}
.acct .amt {{ margin-left: auto; font-weight: 800; color: var(--c); }}

.cc {{
  border-radius: 22px; padding: 20px 22px; color: #fff; min-height: 190px; position: relative; overflow: hidden;
  box-shadow: 0 14px 34px rgba(0,0,0,.35); margin-bottom: 14px;
}}
.cc::after {{ content: ""; position: absolute; right: -40px; top: -40px; width: 170px; height: 170px;
  border-radius: 50%; background: rgba(255,255,255,.14); }}
.cc .top {{ display: flex; justify-content: space-between; font-weight: 700; z-index: 1; position: relative; }}
.cc .chipimg {{ width: 38px; height: 28px; border-radius: 6px; margin: 14px 0 8px;
  background: linear-gradient(135deg, #FDE68A, #F59E0B); }}
.cc .bal {{ font-size: 1.8rem; font-weight: 800; }}
.cc .of {{ opacity: .85; font-size: .85rem; }}
.cc .bar {{ height: 8px; border-radius: 99px; background: rgba(255,255,255,.25); margin: 10px 0 8px; overflow: hidden; }}
.cc .bar > div {{ height: 100%; border-radius: 99px; background: #fff; }}
.cc .meta {{ display: flex; gap: 14px; flex-wrap: wrap; font-size: .82rem; opacity: .95; }}

.sub-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }}
.sub-card {{ border-radius: 18px; padding: 16px; background: #131A33; border: 1px solid rgba(255,255,255,.06);
  border-top: 4px solid var(--c); }}
.sub-card .m {{ font-weight: 800; color: #fff; }}
.sub-card .p {{ font-size: 1.5rem; font-weight: 800; color: var(--c); }}
.sub-card .y {{ color: #A9B1D6; font-size: .82rem; }}
</style>
"""


def inject_css() -> None:
    st.html(CSS)


def hero(title: str, tagline: str, net_worth: str, chip: str) -> None:
    st.html(f"""
    <div class="hero">
      <div style="z-index:1">
        <h1>💸 {escape(title)}</h1>
        <p>{escape(tagline)}</p>
        <span class="chip">{escape(chip)}</span>
      </div>
      <div class="nw"><div class="label">Net worth</div><div class="value">{escape(net_worth)}</div></div>
    </div>""")


def stat_cards(items: list[tuple[str, str, str, str, str]]) -> None:
    """items: (icon, label, value, sub, color)"""
    cards = "".join(
        f'<div class="stat" style="--c:{c}"><div class="icon">{i}</div><div class="label">{escape(lbl)}</div>'
        f'<div class="value">{escape(v)}</div><div class="sub">{escape(s)}</div></div>'
        for i, lbl, v, s, c in items)
    st.html(f'<div class="stat-grid">{cards}</div>')


def alert_cards(alerts) -> None:
    if not alerts:
        st.html(f'<div class="alert-card" style="--c:{GREEN}"><div class="icon">✅</div>'
                '<div><div class="t">All clear</div><div class="d">Nothing unusual right now.</div></div></div>')
        return
    out = []
    for a in alerts:
        warn = a.level == "warning"
        icon = "🚨" if "Unusual" in a.title else ("📅" if "due" in a.title else "💡")
        out.append(f'<div class="alert-card" style="--c:{ORANGE if warn else CYAN}"><div class="icon">{icon}</div>'
                   f'<div><div class="t">{escape(a.title)}</div><div class="d">{escape(a.detail)}</div></div></div>')
    st.html("".join(out))


ACCOUNT_STYLE = {"depository": ("🏦", GREEN), "investment": ("📈", CYAN), "credit": ("💳", PINK), "loan": ("🚗", ORANGE)}


def account_list(accounts, money) -> None:
    rows = []
    for a in accounts:
        icon, color = ACCOUNT_STYLE.get(a.type, ("💼", VIOLET))
        amt = -a.balance if a.type in ("credit", "loan") else a.balance
        rows.append(f'<div class="acct" style="--c:{color}"><div class="icon">{icon}</div><div>'
                    f'<div class="name">{escape(a.name)}</div><div class="kind">{escape(a.institution)} · '
                    f'{escape((a.subtype or a.type).title())}</div></div><div class="amt">{escape(money(amt))}</div></div>')
    st.html("".join(rows))


def credit_card(c, idx: int, money) -> None:
    g1, g2 = CARD_GRADIENTS[idx % len(CARD_GRADIENTS)]
    pct = c.utilization_pct or 0
    health = "🟢 great" if pct < 10 else "🟡 okay" if pct < 30 else "🔴 high"
    meta = []
    if c.apr is not None:
        meta.append(f"APR {c.apr:.2f}%")
        meta.append(f"~{money(c.balance * c.apr / 100 / 12)}/mo interest")
    if c.minimum_payment is not None:
        meta.append(f"Min {money(c.minimum_payment)}")
    if c.next_due_date:
        meta.append(f"Due {c.next_due_date:%b %d}")
    st.html(f"""
    <div class="cc" style="background: linear-gradient(135deg, {g1}, {g2})">
      <div class="top"><span>{escape(c.name)}</span><span>💳 Credit</span></div>
      <div class="chipimg"></div>
      <div class="bal">{escape(money(c.balance))}</div>
      <div class="of">of {escape(money(c.limit or 0))} limit · {pct:.1f}% used {health}</div>
      <div class="bar"><div style="width:{min(pct, 100):.1f}%"></div></div>
      <div class="meta">{''.join(f'<span>{escape(m)}</span>' for m in meta)}</div>
    </div>""")


def subscription_cards(subs, money, pretty) -> None:
    cards = []
    for i, s in enumerate(subs):
        c = cat_color(s.category, i)
        cards.append(f'<div class="sub-card" style="--c:{c}"><div class="m">{cat_icon(s.category)} {escape(s.merchant)}</div>'
                     f'<div class="p">{escape(money(s.amount))}<span style="font-size:.85rem;color:#A9B1D6">/mo</span></div>'
                     f'<div class="y">{escape(money(s.yearly_cost))}/yr · next {escape(s.next_expected)}</div></div>')
    st.html(f'<div class="sub-grid">{"".join(cards)}</div>')


def _style(chart: alt.Chart) -> alt.Chart:
    return (chart.properties(background="transparent")
            .configure_view(stroke=None)
            .configure_axis(labelColor="#C7CCE6", titleColor="#C7CCE6", gridColor="rgba(255,255,255,.07)",
                            domain=False, tickColor="transparent", labelFontSize=12, labelLimit=220,
                            labelFont="Plus Jakarta Sans, Helvetica, Arial, sans-serif"))


def category_chart(by_category: dict, pretty) -> None:
    cats = list(by_category)
    df = pd.DataFrame({"Category": [f"{cat_icon(c)} {pretty(c)}" for c in cats], "Spent": list(by_category.values())})
    colors = [cat_color(c, i) for i, c in enumerate(cats)]
    chart = alt.Chart(df).mark_bar(cornerRadiusEnd=8, height=22).encode(
        y=alt.Y("Category:N", sort="-x", title=None),
        x=alt.X("Spent:Q", title=None, axis=alt.Axis(format="$,.0f")),
        color=alt.Color("Category:N", scale=alt.Scale(domain=df["Category"].tolist(), range=colors), legend=None),
        tooltip=[alt.Tooltip("Category:N"), alt.Tooltip("Spent:Q", format="$,.2f")],
    ).properties(height=max(180, 40 * len(df)))
    st.altair_chart(_style(chart), width="stretch")


def daily_chart(daily: pd.DataFrame) -> None:
    df = daily.reset_index()
    df["Date"] = pd.to_datetime(df["Date"])
    area = alt.Chart(df).mark_area(
        interpolate="monotone",
        line={"color": PINK, "strokeWidth": 2.5},
        color=alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0,
                           stops=[alt.GradientStop(color="rgba(139,92,246,0.05)", offset=0),
                                  alt.GradientStop(color="rgba(236,72,153,0.65)", offset=1)]),
    ).encode(
        x=alt.X("Date:T", title=None, axis=alt.Axis(format="%b %d")),
        y=alt.Y("Spent:Q", title=None, axis=alt.Axis(format="$,.0f")),
        tooltip=[alt.Tooltip("Date:T", format="%a %b %d"), alt.Tooltip("Spent:Q", format="$,.2f")],
    ).properties(height=220)
    st.altair_chart(_style(area), width="stretch")
