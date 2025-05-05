import streamlit as st
import pandas as pd
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
from db_handler import run_query

def overview():
    """
    Display an overview of participants and contributions for a selected group,
    using data fetched from the DB via db_handler.py.
    """

    st.sidebar.subheader("Today's Date")
    st.sidebar.write(datetime.now().strftime("%Y-%m-%d"))

    # 1) Fetch list of group names from the DB
    #    We'll query the 'groups' table to get distinct group_name
    group_rows = run_query("SELECT group_name FROM groups ORDER BY group_name;")
    if not group_rows:
        st.warning("No groups found in the database.")
        return

    group_names = [row[0] for row in group_rows]
    selected_group = st.selectbox("Select a group to view details", group_names)

    if not selected_group:
        st.info("Please select a group.")
        return

    # 2) Query data for this group using a multi-table JOIN
    #    We'll join participants + contributions + (optionally) receivables
    #    to replicate your merged_data approach.
    #    Adjust table/column names as needed. Example below:
    sql = """
    SELECT
        g.group_name,
        p.participant_name,
        c.contribution_id,
        c.round_number,
        c.paid_yesno AS contribution_paid,
        c.paid_date,
        p.contribution,
        p.share_fraction,
        r.received_yesno AS receivable_status,
        r.received_amount,
        r.received_date
    FROM participants p
    JOIN groups g ON p.group_id = g.group_id
    LEFT JOIN contributions c ON c.participant_id = p.participant_id
                               AND c.group_id = p.group_id
    LEFT JOIN receivables r ON r.participant_id = p.participant_id
                             AND r.group_id = p.group_id
                             AND r.round_number = c.round_number
    WHERE g.group_name = %s
    ORDER BY p.participant_name, c.round_number
    """

    rows = run_query(sql, (selected_group,))
    if not rows:
        st.warning(f"No data found for group '{selected_group}'.")
        return

    # 3) Convert the result to a DataFrame
    #    Adjust the column list to match your SELECT fields
    columns = [
        "Group Name", "Participant Name", "Contribution ID",
        "Round Number", "Contribution Paid", "Paid Date",
        "Contribution", "Share Fraction", "Receivable Status",
        "Received Amount", "Received Date"
    ]
    df = pd.DataFrame(rows, columns=columns)

    # 4) Participant Overview Aggregation
    #    We'll replicate your old aggregator logic:
    #    Group by participant, sum contribution, count paid/unpaid, etc.
    st.subheader("Participant Overview")

    # Some columns might be None if the DB has partial data. Fill or adjust as needed.
    df["Contribution"] = df["Contribution"].fillna(0)
    df["Contribution Paid"] = df["Contribution Paid"].fillna("No")
    df["Receivable Status"] = df["Receivable Status"].fillna("No")
    df["Round Number"] = df["Round Number"].fillna(0)

    # Group by participant name
    group_cols = ["Participant Name"]
    aggs = {
        "Contribution": "sum",
        "Contribution Paid": lambda x: (x == "Yes").sum(),  # paid rounds
        "Round Number": "count",  # total rounds in which participant has data
        "Receivable Status": lambda x: (x == "Yes").any()  # whether participant received
    }

    summary = df.groupby(group_cols).agg(aggs).reset_index()

    # Rename columns
    summary.rename(columns={
        "Contribution": "Total Contribution",
        "Contribution Paid": "Paid Rounds",
        "Round Number": "Total Rounds",
        "Receivable Status": "Received"
    }, inplace=True)

    # Compute Unpaid rounds = total rounds - paid rounds
    summary["Unpaid Rounds"] = summary["Total Rounds"] - summary["Paid Rounds"]
    # Convert boolean Received to "Yes"/"No"
    summary["Received"] = summary["Received"].apply(lambda x: "Yes" if x else "No")

    # Final reorder
    summary = summary[[
        "Participant Name",
        "Total Contribution",
        "Paid Rounds",
        "Unpaid Rounds",
        "Total Rounds",
        "Received"
    ]]

    st.table(summary)

    # 5) Round Contribution Details with AgGrid
    st.subheader("Round Contribution Details")
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, filter=True, sortable=True)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    grid_options = gb.build()

    AgGrid(
        df,
        gridOptions=grid_options,
        height=400,
        fit_columns_on_grid_load=True,
        theme="streamlit"
    )
