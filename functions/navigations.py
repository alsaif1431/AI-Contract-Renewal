import streamlit as st

def navigation():
    st.markdown(
        """
    <style>
    .stButton>button {
        width: 100%;
        height: 3em;
        background-color: #f0f2f6;
        color: #31333F;
        border: none;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .stButton>button:hover {
        background-color: #00A67E;
        color: white;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    pages = [
        "📊 Dashboard",
        "📁 Contract Upload",
        "🔔 Reminder Management",
        "📈 Analytics",
        "📚 Documentation",
    ]
    for i, page in enumerate(pages):
        with cols[i]:
            if st.button(f"{page}"):
                st.session_state.page = page


if "page" not in st.session_state:
    st.session_state.page = "📊 Dashboard"