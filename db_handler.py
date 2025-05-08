# db_handler.py

import psycopg2
import streamlit as st
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(st.secrets["neon"]["dsn"])

def run_query(sql, params=None):
    """Run SELECT queries and return result as list of dicts."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def run_command(sql, params=None):
    """Run INSERT/UPDATE/DELETE commands (no return)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()

def run_command_returning(sql, params=None):
    """Run INSERT ... RETURNING queries and return rows."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            conn.commit()
            return rows
