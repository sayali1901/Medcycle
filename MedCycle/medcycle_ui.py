# ============================================================
#  MEDCYCLE BOT UI — Streamlit Frontend
#  Run with:
#       streamlit run medcycle_ui.py
# ============================================================

import streamlit as st
import pandas as pd
from datetime import datetime
from medcycle_demo import (
    create_inventory,
    create_sites,
    Orchestrator
)

# ------------------------------------------------------------
# INITIALIZE BACKEND ENGINE IN SESSION STATE
# ------------------------------------------------------------
if "inventory" not in st.session_state:
    st.session_state.inventory = create_inventory(30)
    st.session_state.sites = create_sites()
    st.session_state.orch = Orchestrator(
        st.session_state.inventory, 
        st.session_state.sites
    )
    st.session_state.audit = []

st.set_page_config(page_title="MedCycle Bot", layout="wide")

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("MedCycle 2.1 — Autonomous Redistribution Bot")
st.write("Ask questions about batches, transfers, or trigger the redistribution engine.")

st.divider()

# ------------------------------------------------------------
# SIDEBAR CONTROLS
# ------------------------------------------------------------
st.sidebar.header("Controls")

if st.sidebar.button("Run Redistribution Now"):
    audit = st.session_state.orch.run()
    st.session_state.audit = audit
    st.sidebar.success("✅ Redistribution executed")

if st.sidebar.button("Reset System"):
    st.session_state.inventory = create_inventory(30)
    st.session_state.sites = create_sites()
    st.session_state.orch = Orchestrator(
        st.session_state.inventory,
        st.session_state.sites
    )
    st.session_state.audit = []
    st.sidebar.warning("System reset to fresh synthetic data.")

# ------------------------------------------------------------
# CHAT BOT
# ------------------------------------------------------------
st.subheader("💬 MedCycle Bot")

user_query = st.text_input("Ask me something:")

def answer(query):
    query_lower = query.lower()

    if "inventory" in query_lower:
        return "Here is the full inventory displayed below."

    if "near expiry" in query_lower or "expiring" in query_lower:
        df = st.session_state.inventory[st.session_state.inventory.days_to_expiry <= 30]
        st.dataframe(df)
        return f"I found {len(df)} batches expiring in ≤30 days."

    if "sites" in query_lower or "clinics" in query_lower:
        st.dataframe(st.session_state.sites)
        return "These are the registered recipient sites."

    if "audit" in query_lower or "transfers" in query_lower:
        df = pd.DataFrame(st.session_state.audit)
        st.dataframe(df)
        return "Here is your audit log."

    if "impact" in query_lower:
        rep = st.session_state.orch.reporter.summarize(st.session_state.audit)
        return f"Value saved: ₹{rep['value_saved']}, CO₂ avoided: {rep['co2_saved_kg']} kg"

    if "run" in query_lower or "redistribute" in query_lower:
        audit = st.session_state.orch.run()
        st.session_state.audit = audit
        return "Redistribution executed."

    return "I can show inventory, sites, audit logs, impact, or run redistribution. Try asking: 'show near expiry items'."

if user_query:
    bot_reply = answer(user_query)
    st.write(f"**Bot:** {bot_reply}")

st.divider()

# ------------------------------------------------------------
# DATA PANELS (AUTO DISPLAY WHEN RELEVANT)
# ------------------------------------------------------------
st.subheader("Current Inventory")
st.dataframe(st.session_state.inventory)

st.subheader("Recipient Sites")
st.dataframe(st.session_state.sites)

st.subheader("Audit Log")
st.dataframe(pd.DataFrame(st.session_state.audit))

st.subheader("Impact Summary")
impact = st.session_state.orch.reporter.summarize(st.session_state.audit)
st.write(impact)
