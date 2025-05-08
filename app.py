import streamlit as st

from sidebar import render_sidebar
from theme import configure_theme, apply_theme
from overview import overview
from edit import edit
from addgroup import add_group
from tracking import tracking
from visualization import visualization
from settings import settings
from admin import admin_panel

# Google Sign-In only
from go_signin import google_signin

st.set_page_config(page_title="Quraa Management System", layout="wide")

def main():
    configure_theme()
    apply_theme()

    user_info = google_signin()  # Returns dict with name, email, role
    if not user_info:
        st.stop()  # Stop rendering if login failed or user is not authenticated

    _show_main_interface(user_info)

def _show_main_interface(user_info):
    role = user_info["role"]
    st.sidebar.write(f"Logged in as: **{user_info['name']}** ({user_info['email']})")
    st.sidebar.write(f"**Role:** {role.title()}")

    if st.sidebar.button("Logout"):
        st.session_state.clear()  # Clear all session state
        st.success("You have been logged out.")
        st.stop()

    # Navigation
    page = render_sidebar(role)

    if page == "Overview":
        overview()

    elif page == "Visualization" and role in ["participant", "admin"]:
        visualization()

    elif page == "Add Group" and role == "admin":
        add_group()

    elif page == "Edit" and role == "admin":
        edit()

    elif page == "Tracking" and role == "admin":
        tracking()

    elif page == "Settings" and role == "admin":
        settings()

    elif page == "Admin Panel" and role == "admin":
        admin_panel()

    else:
        st.warning("🚫 You do not have access to this page.")

if __name__ == "__main__":
    main()
