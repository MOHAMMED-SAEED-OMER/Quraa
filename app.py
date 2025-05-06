import streamlit as st

from sidebar import render_sidebar
from theme import configure_theme, apply_theme
from overview import overview
from edit import edit
from addgroup import add_group
from tracking import tracking
from visualization import visualization
from settings import settings

# Email-based sign in and sign up
from signin import signin
from signup import signup

# Google Sign-In method
from go_signin import google_signin

# Page config
st.set_page_config(page_title="Quraa Management System", layout="wide")

# Main app entry
def main():
    configure_theme()
    apply_theme()

    if not st.experimental_user.is_logged_in:
        _show_auth_interface()
        return

    if 'user' not in st.session_state or 'role' not in st.session_state:
        user = google_signin()
        st.session_state.user = user
        st.session_state.role = user.get("role", "user")  # Default to "user"

    _show_main_interface()

def _show_auth_interface():
    st.title("Quraa - Please Sign In or Sign Up")

    choice = st.radio("Select an action:", ["Sign In (Email)", "Sign Up", "Sign In with Google"])

    if choice == "Sign In (Email)":
        signin()
    elif choice == "Sign Up":
        signup()
    else:
        user = google_signin()
        st.session_state.user = user
        st.session_state.role = user.get("role", "user")

def _show_main_interface():
    user = st.session_state.user
    role = st.session_state.role

    st.sidebar.write(f"Logged in as: **{user['name']}** ({user['email']})")
    st.sidebar.write(f"**Role:** {role.capitalize()}")

    if st.sidebar.button("Logout"):
        st.logout()
        st.success("You have been logged out.")
        st.stop()

    # Sidebar menu
    page = render_sidebar()

    # Role-based access logic
    if page == "Overview":
        overview()

    elif page == "Visualization":
        if role in ["participant", "admin"]:
            visualization()
        else:
            st.warning("Access Denied: Only participants and admins can view this page.")

    elif page in ["Add Group", "Edit", "Tracking", "Settings"]:
        if role == "admin":
            if page == "Add Group":
                add_group()
            elif page == "Edit":
                edit()
            elif page == "Tracking":
                tracking()
            elif page == "Settings":
                settings()
        else:
            st.warning("Access Denied: Only admins can view this page.")

    else:
        st.error("Page not found or not accessible.")

if __name__ == "__main__":
    main()
