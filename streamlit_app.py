import streamlit as st
from time import sleep
from navigation import make_sidebar

# 사이드바 생성
make_sidebar()

# CSS 및 스타일 설정
st.markdown(
    """
    <style>
    @font-face {
        font-family: 'STUNNING-Bd';
        src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/2410-2@1.0/STUNNING-Bd.woff2') format('woff2');
        font-weight: normal;
        font-style: normal;
    }
    
    body {
        background-color: #f0f8ff;
    }
    .login-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 25px;
        width: 100%;
        max-width: 400px;
        margin: auto;
        box-shadow: 2px 2px 12px rgba(0, 0, 0, 0.1);
        font-family: 'STUNNING-Bd', sans-serif;
    }
    .login-title {
        font-size: 2.5rem;
        color: #1e90ff;
        text-align: center;
        margin-bottom: 0.5rem;
        font-family: 'STUNNING-Bd', sans-serif;
    }
    .login-subtitle {
        font-size: 1.8rem;
        color: #4682b4;
        text-align: center;
        margin-bottom: 1.5rem;
        font-family: 'STUNNING-Bd', sans-serif;
    }
    .stButton > button {
        width: 100%;
        padding: 0.75rem;
        background-color: #1e90ff;
        color: #ffffff;
        border: none;
        border-radius: 10px;
        font-size: 1rem;
        font-family: 'STUNNING-Bd', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 로그인 페이지 UI

st.markdown("<div class='login-title'>🦆 Welcome 🦆</div>", unsafe_allow_html=True)
st.markdown("<div class='login-subtitle'>Duck Dal</div>", unsafe_allow_html=True)

username = st.text_input("Username:")
password = st.text_input("Password:", type="password")

if st.button("Log in"):
    if username == "test" and password == "test":
        st.session_state.logged_in = True
        st.success("Logged in successfully!")
        sleep(0.5)
        st.switch_page("pages/page1.py")
    else:
        st.error("❌ Incorrect username or password. Please try again.")

st.markdown("</div>", unsafe_allow_html=True)
