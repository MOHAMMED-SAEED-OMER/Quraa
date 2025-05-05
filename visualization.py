import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from db_handler import run_query
import plotly.express as px

def visualization():
    st.title("📊 Data Visualization Dashboard")

    # ────────────────────────────────────────────────
    # 📌 1. Overview Metrics
    # ────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    # Total Groups
    total_groups = run_query("SELECT COUNT(*) FROM groups")[0][0]
    col1.metric("Total Groups", total_groups)

    # Total Participants
    total_participants = run_query("SELECT COUNT(*) FROM participants")[0][0]
    col2.metric("Total Participants", total_participants)

    # Total Contributions Paid vs Unpaid
    paid_unpaid = run_query("SELECT COUNT(*) FILTER (WHERE paid_yesno='Yes'), COUNT(*) FILTER (WHERE paid_yesno='No') FROM contributions")[0]
    col3.metric("Total Paid Contributions", paid_unpaid[0])
    
    st.divider()

    # ────────────────────────────────────────────────
    # 📊 2. Groups vs Participants Bar Chart
    # ────────────────────────────────────────────────
    st.subheader("📊 Groups vs Participants")

    group_participant_data = run_query("""
        SELECT g.group_name, COUNT(p.participant_id) as participant_count
        FROM groups g
        LEFT JOIN participants p ON g.group_id = p.group_id
        GROUP BY g.group_name
    """)

    if group_participant_data:
        df_gp = pd.DataFrame(group_participant_data, columns=["Group Name", "Participants"])
        fig = px.bar(df_gp, x="Group Name", y="Participants", title="Participants per Group", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No groups or participants found.")

    st.divider()

    # ────────────────────────────────────────────────
    # 💰 3. Contributions Paid vs Unpaid (Stacked Bar)
    # ────────────────────────────────────────────────
    st.subheader("💰 Contributions Paid vs Unpaid (By Round)")

    round_contributions = run_query("""
        SELECT c.round_number, 
               COUNT(*) FILTER (WHERE c.paid_yesno='Yes') as paid,
               COUNT(*) FILTER (WHERE c.paid_yesno='No') as unpaid
        FROM contributions c
        GROUP BY c.round_number
        ORDER BY c.round_number
    """)

    if round_contributions:
        df_contrib = pd.DataFrame(round_contributions, columns=["Round", "Paid", "Unpaid"])
        fig = px.bar(df_contrib, x="Round", y=["Paid", "Unpaid"], barmode="stack", title="Paid vs Unpaid Contributions by Round")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No contributions found.")

    st.divider()

    # ────────────────────────────────────────────────
    # 🥧 4. Receivables Status (Pie Chart)
    # ────────────────────────────────────────────────
    st.subheader("🥧 Receivables Status")

    receivable_data = run_query("""
        SELECT COUNT(*) FILTER (WHERE received_yesno='Yes') as received,
               COUNT(*) FILTER (WHERE received_yesno='No') as not_received
        FROM receivables
    """)

    if receivable_data:
        df_recv = pd.DataFrame({"Status": ["Received", "Not Received"], "Count": list(receivable_data[0])})
        fig = px.pie(df_recv, names="Status", values="Count", title="Receivables Status")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No receivable data found.")

    st.divider()

    # ────────────────────────────────────────────────
    # 📅 5. Upcoming Rounds (Gantt Chart)
    # ────────────────────────────────────────────────
    st.subheader("📅 Upcoming Rounds")

    round_schedule = run_query("""
        SELECT g.group_name, r.round_number, r.round_date
        FROM rounds r
        JOIN groups g ON r.group_id = g.group_id
        WHERE r.round_date >= CURRENT_DATE
        ORDER BY r.round_date
    """)

    if round_schedule:
        df_rounds = pd.DataFrame(round_schedule, columns=["Group", "Round", "Round Date"])
        fig = px.timeline(df_rounds, x_start="Round Date", x_end="Round Date", y="Group", color="Round", title="Upcoming Rounds")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No upcoming rounds found.")

