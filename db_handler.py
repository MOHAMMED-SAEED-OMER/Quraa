# db_handler.py

import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

def get_connection():
    conn = psycopg2.connect(st.secrets["neon"]["dsn"])
    return conn

def run_query(sql, params=None):
    """
    For SELECT statements (returns rows as dictionaries).
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)  # Use dictionary cursor
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def run_command(sql, params=None):
    """
    For non-returning commands like UPDATE/DELETE.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close()
    conn.close()

def run_command_returning(sql, params=None):
    """
    For INSERT ... RETURNING.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)  # Use dictionary cursor here too
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return rows
