# db_handler.py

import psycopg2
import streamlit as st

def get_connection():
    conn = psycopg2.connect(st.secrets["neon"]["dsn"])
    return conn

def run_query(sql, params=None):
    """
    For SELECT statements (no auto-commit).
    Returns fetched rows.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def run_command(sql, params=None):
    """
    For non-returning commands like UPDATE/DELETE, or
    INSERT without needing returned rows.
    Commits changes automatically.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close()
    conn.close()

def run_command_returning(sql, params=None):
    """
    For INSERT ... RETURNING or similar statements that both write data
    and return newly generated rows. We do a commit to ensure the data is
    fully written for subsequent queries.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    rows = cur.fetchall()  # get the RETURNING rows
    conn.commit()
    cur.close()
    conn.close()
    return rows
