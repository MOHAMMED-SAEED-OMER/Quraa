import streamlit as st
from theme import THEMES, apply_theme

def settings():
    """
    Render the Settings page to change app configurations like theme.
    """
    st.title("Settings")
    st.subheader("Theme Settings")

    # Fetch query params and validate the current theme
    query_params = st.query_params
    current_theme = query_params.get("theme", ["light"])[0]  # Default to "light"

    if current_theme not in THEMES:
        current_theme = "light"

    # Display radio buttons for theme selection
    selected_theme = st.radio(
        "Select App Theme:",
        options=list(THEMES.keys()),
        index=list(THEMES.keys()).index(current_theme),
    )

    # Update theme if selection changes
    if selected_theme != current_theme:
        # Update session state and query params
        st.session_state["theme"] = selected_theme

        # Apply the selected theme
        apply_theme()

        # Manually trigger a rerun by clearing cache
        st.stop()  # Stop execution, and Streamlit automatically reruns
