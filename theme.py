import streamlit as st

THEMES = {
    "light": {
        "background_color": "#FAFAFA",
        "text_color": "#0E1117",
    },
    "dark": {
        "background_color": "#0E1117",
        "text_color": "#FAFAFA",
    },
}

def configure_theme():
    """
    Initialize the theme from the URL query param (if any)
    using experimental_get_query_params, to avoid conflict
    with st.experimental_set_query_params in go_signin.py.
    """
    # Use the same “experimental” approach
    query_params = st.experimental_get_query_params()
    
    # If you store ?theme=dark or ?theme=light in the URL
    if "theme" in query_params:
        picked = query_params["theme"][0]  # theme is a list
        st.session_state["theme"] = picked
    else:
        # default to "light" or read from session if we have it
        st.session_state["theme"] = st.session_state.get("theme", "light")

def apply_theme():
    """
    Apply the selected theme by injecting CSS.
    """
    theme_key = st.session_state.get("theme", "light")
    theme = THEMES.get(theme_key, THEMES["light"])

    background_color = theme["background_color"]
    text_color = theme["text_color"]

    # Inject CSS
    st.markdown(
        f"""
        <style>
        body {{
            background-color: {background_color};
            color: {text_color};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
