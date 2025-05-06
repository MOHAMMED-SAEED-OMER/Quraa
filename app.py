import streamlit as st

from sidebar import render_sidebar
from theme import configure_theme, apply_theme
from overview import overview
from edit import edit
from addgroup import add_group
from tracking import tracking
from visualization import visualization
from settings import settings
from admin import admin_panel  # NEW

# Authentication
from signin import signin
from signup import signup
from go_signin import google_signin

st.set_page_config(page_title="Quraa Management System", layout="wide")

def main():
    configure_theme()
    apply_theme()

    if not st.experimental_user.is_logged_in:
        _show_auth_interface()
        return

    user_info = google_signin()  # Returns dict with name, email, role
    _show_main_interface(user_info)

def _show_auth_interface():
    st.title("Quraa - Please Sign In or Sign Up")

    auth_choice = st.radio("Select an action:", ["Sign In (Email)", "Sign Up", "Sign In with Google"])
    if auth_choice == "Sign In (Email)":
        signin()
    elif auth_choice == "Sign Up":
        signup()
    else:
        google_signin()

def _show_main_interface(user_info):
    role = user_info["role"]
    st.sidebar.write(f"Logged in as: **{user_info['name']}** ({user_info['email']})")
    st.sidebar.write(f"**Role:** {role.title()}")

    if st.sidebar.button("Logout"):
        st.logout()
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
