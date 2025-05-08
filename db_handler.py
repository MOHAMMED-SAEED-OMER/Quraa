import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

def get_connection():
    conn = psycopg2.connect(st.secrets["neon"]["dsn"])
    return conn

def run_query(sql, params=None):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)  # ✅ USE RealDictCursor
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def run_command(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close()
    conn.close()

def run_command_returning(sql, params=None):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)  # ✅ USE RealDictCursor here too
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return rows
