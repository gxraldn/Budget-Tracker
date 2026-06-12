import streamlit as st
from supabase import create_client, Client

# ========= Supabase setup =========
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_client()

allowed_categories = [
    "Food", "Rent", "Transport", "Entertainment",
    "Utilities", "Health", "Education", "Other"
]

# ========= Data functions =========

def get_income():
    res = supabase.table("income").select("*").order("id", desc=True).limit(1).execute()
    if res.data:
        return float(res.data[0]["amount"])
    return 0.0


def set_income(amount):
    supabase.table("income").insert({"amount": amount}).execute()


def get_expenses():
    res = supabase.table("expenses").select("*").order("id", desc=False).execute()
    return res.data or []


def add_expense(category, amount):
    supabase.table("expenses").insert({"category": category, "amount": amount}).execute()


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


# ========= UI =========

st.set_page_config(page_title="Budget Tracker", page_icon="💰", layout="centered")
st.title("💰 Budget Tracker")

income = get_income()
expenses = get_expenses()

# --- Income ---
st.subheader("Income")
col1, col2 = st.columns([3, 1])
with col1:
    income_input = st.number_input("Monthly income", min_value=0.0, value=income, step=100.0, format="%.2f")
with col2:
    if st.button("Set / Update", use_container_width=True):
        if income_input > 0:
            set_income(income_input)
            st.success(f"Income set to ${income_input:.2f}")
            st.rerun()
        else:
            st.error("Income must be greater than 0.")

st.divider()

# --- Add Expense ---
st.subheader("Add Expense")
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    category = st.selectbox("Category", allowed_categories)
with col2:
    amount = st.number_input("Amount", min_value=0.0, step=1.0, format="%.2f", key="amount_input")
with col3:
    st.write("")
    st.write("")
    if st.button("Add", use_container_width=True):
        if amount > 0:
            add_expense(category, amount)
            st.success(f"Added {category} - ${amount:.2f}")
            st.rerun()
        else:
            st.error("Amount must be greater than 0.")

st.divider()

# --- Expenses Table ---
st.subheader("Expenses")
if expenses:
    for e in expenses:
        c1, c2, c3, c4 = st.columns([1, 3, 2, 1])
        c1.write(f"#{e['id']}")
        c2.write(e["category"])
        c3.write(f"${float(e['amount']):.2f}")
        if c4.button("🗑️", key=f"del_{e['id']}"):
            delete_expense(e["id"])
            st.rerun()
else:
    st.info("No expenses yet.")

st.divider()

# --- Summary ---
st.subheader("Summary")
total = total_spent(expenses)
remaining = income - total

tol = 0.01
if total < income - tol:
    status = "🟢 Under budget"
elif abs(income - total) <= tol:
    status = "🟡 On track"
else:
    status = "🔴 Over budget"

col1, col2, col3 = st.columns(3)
col1.metric("Total Spent", f"${total:.2f}")
col2.metric("Remaining", f"${remaining:.2f}")
col3.metric("Status", status)

if expenses:
    st.write("**Category Breakdown:**")
    cat_totals = compute_category_totals(expenses)
    for cat, amt in sorted(cat_totals.items(), key=lambda x: (-x[1], x[0])):
        st.write(f"- {cat}: ${amt:.2f}")

st.divider()

# --- Reset ---
if st.button("⚠️ Reset All Data"):
    reset_data()
    st.success("All data cleared.")
    st.rerun()
