import streamlit as st
import pandas as pd
from datetime import datetime
from db_handler import run_query, run_command

def tracking():
    """
    Quraa tracking page (DB-based):
      1) Alerts at top: show unpaid contributions & unreceived items for rounds <= today
      2) Two tabs: "Payments" (mark participants as paid), "Receivables" (mark participants as received)
    """

    st.title("Tracking: Payments & Receivables")

    # 1) Alerts Section
    alerts_for_unpaid()
    alerts_for_unreceived()

    # 2) Payment & Receivable Tabs
    tab_payments, tab_receivables = st.tabs(["Payments", "Receivables"])

    with tab_payments:
        payments_tab()

    with tab_receivables:
        receivables_tab()

# ─────────────────────────────────────────────────────────
# ALERTS FOR UNPAID CONTRIBUTIONS
# ─────────────────────────────────────────────────────────
def alerts_for_unpaid():
    st.subheader("Alerts for Unpaid Contributions")

    # We'll define "unpaid" as "paid_yesno='No'" in 'contributions'
    # and round_date <= today in 'rounds'.
    current_date = datetime.now().date()

    sql_unpaid = """
    SELECT g.group_name,
           p.participant_name,
           c.round_number,
           r.round_date
      FROM contributions c
      JOIN participants p ON c.participant_id = p.participant_id
      JOIN groups g ON c.group_id = g.group_id
      JOIN rounds r ON (r.group_id = c.group_id AND r.round_number = c.round_number)
     WHERE c.paid_yesno = 'No'
       AND r.round_date <= %s
     ORDER BY g.group_name, c.round_number, p.participant_name
    """
    rows = run_query(sql_unpaid, (current_date,))
    if not rows:
        st.info("All participants are up to date with their contributions.")
    else:
        df = pd.DataFrame(rows, columns=["Group Name", "Participant Name", "Round Number", "Round Date"])
        for gname in df["Group Name"].unique():
            sub = df[df["Group Name"] == gname]
            st.warning(f"**Group: {gname}** - Unpaid participants for past rounds:")
            st.dataframe(sub[["Participant Name", "Round Number", "Round Date"]])

# ─────────────────────────────────────────────────────────
# ALERTS FOR UNRECEIVED
# ─────────────────────────────────────────────────────────
def alerts_for_unreceived():
    st.subheader("Alerts for Unreceived Rounds")

    current_date = datetime.now().date()

    sql_unreceived = """
    SELECT g.group_name,
           p.participant_name,
           rcv.round_number,
           rd.round_date
      FROM receivables rcv
      JOIN participants p ON rcv.participant_id = p.participant_id
      JOIN groups g ON rcv.group_id = g.group_id
      JOIN rounds rd ON (rd.group_id = rcv.group_id AND rd.round_number = rcv.round_number)
     WHERE rcv.received_yesno = 'No'
       AND rd.round_date <= %s
     ORDER BY g.group_name, rcv.round_number, p.participant_name
    """
    rows = run_query(sql_unreceived, (current_date,))
    if not rows:
        st.info("All rounds have been received by participants.")
    else:
        df = pd.DataFrame(rows, columns=["Group Name", "Participant Name", "Round Number", "Round Date"])
        for gname in df["Group Name"].unique():
            gsub = df[df["Group Name"] == gname]
            for rnd in sorted(gsub["Round Number"].unique()):
                sub2 = gsub[gsub["Round Number"] == rnd]
                round_date = sub2["Round Date"].iloc[0]
                parts = sub2["Participant Name"].unique().tolist()
                st.error(f"**Group: {gname}**, Round {rnd} (on {round_date}) not received by: {parts}")

# ─────────────────────────────────────────────────────────
# PAYMENTS TAB
# ─────────────────────────────────────────────────────────
def payments_tab():
    st.subheader("Mark Payments")

    # 1) Choose group
    group_sql = "SELECT group_id, group_name FROM groups ORDER BY group_name;"
    group_rows = run_query(group_sql)
    if not group_rows:
        st.info("No groups found.")
        return

    # Convert to dict for selection
    id_to_name = {int(gid): gname for (gid, gname) in group_rows}
    name_to_id = {gname: int(gid) for (gid, gname) in group_rows}
    group_names = [row[1] for row in group_rows]

    selected_group_name = st.selectbox("Select Group (Payments)", group_names)
    if not selected_group_name:
        return
    group_id = int(name_to_id[selected_group_name])

    # 2) Choose round
    round_sql = """
    SELECT round_number
      FROM rounds
     WHERE group_id = %s
     ORDER BY round_number
    """
    rrows = run_query(round_sql, (group_id,))
    if not rrows:
        st.info(f"No rounds found for group '{selected_group_name}'.")
        return
    # ensure Python int
    round_numbers = [int(r[0]) for r in rrows]
    selected_round = st.selectbox("Select Round (Payments)", round_numbers)

    # 3) Show participants who haven't paid
    pay_sql = """
    SELECT p.participant_name,
           c.paid_yesno,
           c.participant_id
      FROM contributions c
      JOIN participants p ON c.participant_id = p.participant_id
     WHERE c.group_id = %s
       AND c.round_number = %s
     ORDER BY p.participant_name
    """
    pay_rows = run_query(pay_sql, (group_id, selected_round))
    if not pay_rows:
        st.info("No participants found for this round.")
        return

    df = pd.DataFrame(pay_rows, columns=["Participant Name", "PaidYesNo", "participant_id"])
    not_paid_df = df[df["PaidYesNo"] == "No"]
    if not_paid_df.empty:
        st.info("All participants have paid in this round.")
        return
    else:
        st.write("Participants who haven't paid yet:")
        unpaid_list = not_paid_df["Participant Name"].unique().tolist()
        pay_multi = st.multiselect("Select participants to mark as paid:", unpaid_list)

        if st.button("Confirm Payment"):
            if not pay_multi:
                st.info("No participants selected.")
            else:
                updated_any = False
                for pname in pay_multi:
                    row_ = df[df["Participant Name"] == pname]
                    if not row_.empty:
                        pid_ = int(row_["participant_id"].iloc[0])  # cast to Python int
                        update_sql = """
                        UPDATE contributions
                           SET paid_yesno='Yes', paid_date=%s
                         WHERE group_id=%s
                           AND round_number=%s
                           AND participant_id=%s
                           AND paid_yesno='No'
                        """
                        run_command(update_sql, (datetime.now().date(), group_id, selected_round, pid_))
                        updated_any = True

                if updated_any:
                    st.success("Marked selected participants as paid!")
                else:
                    st.info("No matching rows were updated.")

# ─────────────────────────────────────────────────────────
# RECEIVABLES TAB
# ─────────────────────────────────────────────────────────
def receivables_tab():
    st.subheader("Mark Receivables")

    # 1) Choose group
    group_sql = "SELECT group_id, group_name FROM groups ORDER BY group_name;"
    group_rows = run_query(group_sql)
    if not group_rows:
        st.info("No groups found for receivables.")
        return

    name_to_id = {gname: int(gid) for (gid, gname) in group_rows}
    group_names = [row[1] for row in group_rows]
    selected_group_name = st.selectbox("Select Group (Receivables)", group_names)
    if not selected_group_name:
        return
    group_id = int(name_to_id[selected_group_name])

    # 2) Choose round
    round_sql = """
    SELECT round_number
      FROM rounds
     WHERE group_id=%s
     ORDER BY round_number
    """
    rrows = run_query(round_sql, (group_id,))
    if not rrows:
        st.info(f"No rounds found for group '{selected_group_name}'.")
        return

    round_nums = [int(r[0]) for r in rrows]
    selected_round = st.selectbox("Select Round (Receivables)", round_nums)

    # 3) Show who hasn't received for that round
    rec_sql = """
    SELECT p.participant_name,
           r.received_yesno,
           r.participant_id
      FROM receivables r
      JOIN participants p ON r.participant_id = p.participant_id
     WHERE r.group_id = %s
       AND r.round_number = %s
     ORDER BY p.participant_name
    """
    rec_rows = run_query(rec_sql, (group_id, selected_round))
    if not rec_rows:
        st.info(f"No participants found for Group={selected_group_name}, Round={selected_round}.")
        return

    df = pd.DataFrame(rec_rows, columns=["Participant Name", "ReceivedYesNo", "participant_id"])
    not_received_df = df[df["ReceivedYesNo"] == "No"]
    if not_received_df.empty:
        st.info("All participants have received for this round.")
        return
    else:
        # Also block participants who have already received in any other round of this group
        block_sql = """
        SELECT r.participant_id
          FROM receivables r
         WHERE r.group_id = %s
           AND r.received_yesno='Yes'
        """
        block_rows = run_query(block_sql, (group_id,))
        already_received_ids = set(int(row[0]) for row in block_rows)

        can_receive_df = not_received_df[~not_received_df["participant_id"].isin(already_received_ids)]
        if can_receive_df.empty:
            st.info("No participants can receive now; either they've already received or no partial data.")
            return
        else:
            st.write("Participants who haven't received in this round and haven't received in any other round:")
            possible_names = can_receive_df["Participant Name"].unique().tolist()
            rec_sel = st.multiselect("Select participants to mark as received:", possible_names)

            if st.button("Confirm Receivables"):
                if not rec_sel:
                    st.info("No participants selected.")
                else:
                    updated_recv = False
                    for pname in rec_sel:
                        row_ = can_receive_df[can_receive_df["Participant Name"] == pname]
                        if not row_.empty:
                            pid_ = int(row_["participant_id"].iloc[0])  # cast to Python int
                            update_sql = """
                            UPDATE receivables
                               SET received_yesno='Yes', received_date=%s
                             WHERE group_id=%s
                               AND round_number=%s
                               AND participant_id=%s
                               AND received_yesno='No'
                            """
                            run_command(update_sql, (datetime.now().date(), group_id, selected_round, pid_))
                            updated_recv = True

                    if updated_recv:
                        st.success("Selected participants marked as received!")
                    else:
                        st.info("No matching rows were updated.")
