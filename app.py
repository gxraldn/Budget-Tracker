import streamlit as st
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
 
# ========= Page Config =========
st.set_page_config(
    page_title="Budget Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)
 
# ========= Custom CSS =========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
 
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
 
    /* Main background */
    .stApp {
        background-color: #0f1117;
        color: #e8eaf0;
    }
 
    /* Hide default streamlit header padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }
 
    /* Title styling */
    h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
 
    h2, h3 {
        font-weight: 600 !important;
        color: #c9ccd6 !important;
    }
 
    /* Metric cards */
    [data-testid="metric-container"] {
        background: #1a1d27;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1rem 1.2rem !important;
    }
 
    [data-testid="metric-container"] label {
        color: #7b7f8e !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
 
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }
 
    /* Inputs */
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] > div {
        background-color: #1a1d27 !important;
        border-color: #2a2d3a !important;
        color: #e8eaf0 !important;
        border-radius: 8px !important;
    }
 
    /* Buttons */
    .stButton > button {
        background-color: #4f6ef7 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.45rem 1.2rem !important;
        transition: background 0.2s ease;
    }
 
    .stButton > button:hover {
        background-color: #3a56d4 !important;
    }
 
    /* Danger button */
    .danger-btn button {
        background-color: #3a1a1a !important;
        color: #f87171 !important;
        border: 1px solid #5a2020 !important;
    }
 
    .danger-btn button:hover {
        background-color: #5a2020 !important;
    }
 
    /* Divider */
    hr {
        border-color: #2a2d3a !important;
        margin: 1.5rem 0 !important;
    }
 
    /* Expense row card */
    .expense-row {
        background: #1a1d27;
        border: 1px solid #2a2d3a;
        border-radius: 10px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
 
    /* Progress bar */
    .budget-bar-bg {
        background: #2a2d3a;
        border-radius: 8px;
        height: 12px;
        width: 100%;
        overflow: hidden;
    }
 
    .budget-bar-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 0.4s ease;
    }
 
    /* Info/success/error */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
    }
 
    /* Section headers */
    .section-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #4f6ef7;
        margin-bottom: 0.8rem;
    }
 
    /* Badge */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
    }
 
    /* Tab styling */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: #1a1d27;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #2a2d3a;
    }
 
    [data-testid="stTabs"] [data-baseweb="tab"] {
        border-radius: 7px !important;
        color: #7b7f8e !important;
        font-weight: 500 !important;
    }
 
    [data-testid="stTabs"] [aria-selected="true"] {
        background-color: #4f6ef7 !important;
        color: white !important;
    }
 
    /* Plotly chart backgrounds */
    .js-plotly-plot .plotly .bg {
        fill: transparent !important;
    }
</style>
""", unsafe_allow_html=True)
 
# ========= Supabase setup =========
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
 
@st.cache_resource
def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)
 
supabase = get_client()
 
CATEGORY_ICONS = {
    "Food": "🍽️",
    "Rent": "🏠",
    "Transport": "🚗",
    "Entertainment": "🎮",
    "Utilities": "⚡",
    "Health": "🏥",
    "Education": "📚",
    "Other": "📦",
}
CATEGORY_COLORS = {
    "Food": "#f97316",
    "Rent": "#8b5cf6",
    "Transport": "#06b6d4",
    "Entertainment": "#ec4899",
    "Utilities": "#eab308",
    "Health": "#22c55e",
    "Education": "#3b82f6",
    "Other": "#6b7280",
}
allowed_categories = list(CATEGORY_ICONS.keys())
 
# ========= Data functions =========
def get_income():
    res = supabase.table("income").select("*").order("id", desc=True).limit(1).execute()
    return float(res.data[0]["amount"]) if res.data else 0.0
 
def set_income(amount):
    supabase.table("income").insert({"amount": amount}).execute()
 
def get_expenses():
    res = supabase.table("expenses").select("*").order("id", desc=False).execute()
    return res.data or []
 
def add_expense(category, amount):
    supabase.table("expenses").insert({
        "category": category,
        "amount": amount,
    }).execute()
 
def delete_expense(expense_id):
    supabase.table("expenses").delete().eq("id", expense_id).execute()
 
def reset_data():
    supabase.table("expenses").delete().neq("id", 0).execute()
    supabase.table("income").delete().neq("id", 0).execute()
 
def total_spent(expenses):
    return sum(float(e["amount"]) for e in expenses)
 
def compute_category_totals(expenses):
    totals = {}
    for e in expenses:
        cat = e.get("category", "Other")
        totals[cat] = totals.get(cat, 0.0) + float(e["amount"])
    return totals
 
# ========= Load Data =========
income = get_income()
expenses = get_expenses()
total = total_spent(expenses)
remaining = income - total
pct_used = (total / income * 100) if income > 0 else 0
 
tol = 0.01
if total < income - tol:
    status_label = "Under Budget"
    status_color = "#22c55e"
    status_icon = "🟢"
elif abs(income - total) <= tol:
    status_label = "On Track"
    status_color = "#eab308"
    status_icon = "🟡"
else:
    status_label = "Over Budget"
    status_color = "#ef4444"
    status_icon = "🔴"
 
bar_color = status_color
bar_pct = min(pct_used, 100)
 
# ========= Header =========
col_title, col_date = st.columns([3, 1])
with col_title:
    st.markdown("## 💰 Budget Tracker")
with col_date:
    st.markdown(f"<p style='text-align:right; color:#7b7f8e; font-size:0.85rem; padding-top:0.6rem'>{datetime.now().strftime('%B %Y')}</p>", unsafe_allow_html=True)
 
st.divider()
 
# ========= Summary Metrics =========
c1, c2, c3, c4 = st.columns(4)
c1.metric("Monthly Income", f"₱{income:,.2f}")
c2.metric("Total Spent", f"₱{total:,.2f}", delta=f"-₱{total:,.2f}" if total > 0 else None, delta_color="inverse")
c3.metric("Remaining", f"₱{remaining:,.2f}", delta_color="normal")
c4.metric("Status", f"{status_icon} {status_label}")
 
# Budget progress bar
if income > 0:
    st.markdown(f"""
    <div style='margin-top:1rem; margin-bottom:0.3rem;'>
        <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
            <span style='font-size:0.78rem; color:#7b7f8e; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;'>Budget Used</span>
            <span style='font-size:0.85rem; color:{bar_color}; font-weight:700;'>{pct_used:.1f}%</span>
        </div>
        <div class='budget-bar-bg'>
            <div class='budget-bar-fill' style='width:{bar_pct}%; background:{bar_color};'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
st.divider()
 
# ========= Tabs =========
tab1, tab2, tab3 = st.tabs(["  📋 Overview  ", "  ➕ Add Entry  ", "  ⚙️ Settings  "])
 
# ──────────────────────────────────────────────
# TAB 1: OVERVIEW
# ──────────────────────────────────────────────
with tab1:
    if not expenses:
        st.markdown("""
        <div style='text-align:center; padding:3rem 0; color:#7b7f8e;'>
            <div style='font-size:3rem;'>📊</div>
            <div style='font-size:1rem; margin-top:0.5rem;'>No expenses yet — add your first one in <strong>Add Entry</strong>.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        cat_totals = compute_category_totals(expenses)
 
        left, right = st.columns([1.2, 1], gap="large")
 
        with left:
            st.markdown("<p class='section-label'>Spending by Category</p>", unsafe_allow_html=True)
            df_pie = pd.DataFrame(
                [(cat, amt) for cat, amt in cat_totals.items()],
                columns=["Category", "Amount"]
            )
            colors = [CATEGORY_COLORS.get(c, "#6b7280") for c in df_pie["Category"]]
            fig = go.Figure(data=[go.Pie(
                labels=df_pie["Category"],
                values=df_pie["Amount"],
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#0f1117", width=2)),
                textinfo="label+percent",
                textfont=dict(color="#e8eaf0", size=12),
                hovertemplate="<b>%{label}</b><br>₱%{value:,.2f}<br>%{percent}<extra></extra>",
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=280,
                annotations=[dict(
                    text=f"<b>₱{total:,.0f}</b><br><span style='font-size:10px'>total</span>",
                    x=0.5, y=0.5, font_size=16, showarrow=False,
                    font=dict(color="#ffffff")
                )]
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
 
        with right:
            st.markdown("<p class='section-label'>Category Breakdown</p>", unsafe_allow_html=True)
            for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1]):
                icon = CATEGORY_ICONS.get(cat, "📦")
                color = CATEGORY_COLORS.get(cat, "#6b7280")
                pct = (amt / total * 100) if total > 0 else 0
                st.markdown(f"""
                <div style='margin-bottom:0.7rem;'>
                    <div style='display:flex; justify-content:space-between; margin-bottom:4px;'>
                        <span style='font-size:0.88rem; font-weight:500;'>{icon} {cat}</span>
                        <span style='font-size:0.88rem; color:{color}; font-weight:600;'>₱{amt:,.2f}</span>
                    </div>
                    <div class='budget-bar-bg' style='height:6px;'>
                        <div class='budget-bar-fill' style='width:{pct:.1f}%; background:{color};'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
 
        st.divider()
 
        # Expense list
        st.markdown("<p class='section-label'>All Expenses</p>", unsafe_allow_html=True)
 
        # Filter by category
        filter_options = ["All"] + sorted(set(e["category"] for e in expenses))
        selected_filter = st.selectbox("Filter by category", filter_options, label_visibility="collapsed")
 
        filtered = expenses if selected_filter == "All" else [e for e in expenses if e["category"] == selected_filter]
 
        for e in reversed(filtered):
            cat = e.get("category", "Other")
            icon = CATEGORY_ICONS.get(cat, "📦")
            color = CATEGORY_COLORS.get(cat, "#6b7280")
 
            col_info, col_amt, col_del = st.columns([4, 2, 1])
            with col_info:
                st.markdown(f"""
                <div style='padding:0.5rem 0;'>
                    <span style='background:{color}22; color:{color}; border-radius:6px; padding:2px 8px; font-size:0.75rem; font-weight:600;'>{icon} {cat}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_amt:
                st.markdown(f"<p style='padding-top:0.5rem; font-weight:600; color:#e8eaf0;'>₱{float(e['amount']):,.2f}</p>", unsafe_allow_html=True)
            with col_del:
                if st.button("✕", key=f"del_{e['id']}", help="Delete this expense"):
                    delete_expense(e["id"])
                    st.rerun()
 
# ──────────────────────────────────────────────
# TAB 2: ADD ENTRY
# ──────────────────────────────────────────────
with tab2:
    col_form, col_tip = st.columns([1.2, 1], gap="large")
 
    with col_form:
        st.markdown("<p class='section-label'>Set Income</p>", unsafe_allow_html=True)
        inc_col1, inc_col2 = st.columns([3, 1])
        with inc_col1:
            income_input = st.number_input(
                "Monthly income", min_value=0.0, value=income,
                step=500.0, format="%.2f", label_visibility="collapsed",
                placeholder="Monthly income (₱)"
            )
        with inc_col2:
            if st.button("Save", use_container_width=True):
                if income_input > 0:
                    set_income(income_input)
                    st.success("Income updated!")
                    st.rerun()
                else:
                    st.error("Must be > 0")
 
        st.divider()
 
        st.markdown("<p class='section-label'>Add Expense</p>", unsafe_allow_html=True)
 
        cat_col, amt_col = st.columns(2)
        with cat_col:
            category = st.selectbox(
                "Category", allowed_categories,
                format_func=lambda c: f"{CATEGORY_ICONS[c]} {c}",
                label_visibility="collapsed"
            )
        with amt_col:
            amount = st.number_input(
                "Amount", min_value=0.0, step=10.0,
                format="%.2f", key="amount_input",
                label_visibility="collapsed", placeholder="Amount (₱)"
            )
 
        if st.button("➕ Add Expense", use_container_width=True):
            if amount > 0:
                add_expense(category, amount)
                st.success(f"{CATEGORY_ICONS[category]} {category} — ₱{amount:,.2f} added!")
                st.rerun()
            else:
                st.error("Amount must be greater than 0.")
 
    with col_tip:
        st.markdown("<p class='section-label'>Quick Stats</p>", unsafe_allow_html=True)
        if expenses:
            # Highest category
            cat_totals = compute_category_totals(expenses)
            top_cat = max(cat_totals, key=cat_totals.get)
            top_icon = CATEGORY_ICONS.get(top_cat, "📦")
            st.markdown(f"""
            <div style='background:#1a1d27; border:1px solid #2a2d3a; border-radius:10px; padding:1rem; margin-bottom:0.8rem;'>
                <div style='font-size:0.72rem; text-transform:uppercase; letter-spacing:0.5px; color:#7b7f8e; margin-bottom:0.3rem;'>Highest Spending</div>
                <div style='font-size:1.1rem; font-weight:700;'>{top_icon} {top_cat}</div>
                <div style='color:#f97316; font-weight:600;'>₱{cat_totals[top_cat]:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
 
            st.markdown(f"""
            <div style='background:#1a1d27; border:1px solid #2a2d3a; border-radius:10px; padding:1rem; margin-bottom:0.8rem;'>
                <div style='font-size:0.72rem; text-transform:uppercase; letter-spacing:0.5px; color:#7b7f8e; margin-bottom:0.3rem;'>Total Transactions</div>
                <div style='font-size:1.5rem; font-weight:700;'>{len(expenses)}</div>
            </div>
            """, unsafe_allow_html=True)
 
            avg = total / len(expenses) if expenses else 0
            st.markdown(f"""
            <div style='background:#1a1d27; border:1px solid #2a2d3a; border-radius:10px; padding:1rem;'>
                <div style='font-size:0.72rem; text-transform:uppercase; letter-spacing:0.5px; color:#7b7f8e; margin-bottom:0.3rem;'>Avg per Transaction</div>
                <div style='font-size:1.5rem; font-weight:700;'>₱{avg:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Add your income and first expense to see stats here.")
 
# ──────────────────────────────────────────────
# TAB 3: SETTINGS
# ──────────────────────────────────────────────
with tab3:
    st.markdown("<p class='section-label'>Danger Zone</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#1a0f0f; border:1px solid #5a2020; border-radius:10px; padding:1rem 1.2rem; margin-bottom:1rem;'>
        <div style='font-weight:600; color:#f87171; margin-bottom:0.3rem;'>⚠️ Reset All Data</div>
        <div style='font-size:0.85rem; color:#7b7f8e;'>This will permanently delete all income records and expenses. This action cannot be undone.</div>
    </div>
    """, unsafe_allow_html=True)
 
    confirm = st.checkbox("I understand this will delete all my data")
    if confirm:
        with st.container():
            st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
            if st.button("🗑️ Reset All Data", use_container_width=False):
                reset_data()
                st.success("All data has been cleared.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
