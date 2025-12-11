# ============================================
# FILE 2: Login.py (Main Login Page)
# ============================================
"""
Place this as: Login.py (root level, not in pages/)
"""

import streamlit as st
from auth_db import AuthDatabase

st.set_page_config(
    page_title="Login",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide sidebar on login page
st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Initialize database
db = AuthDatabase()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# If already logged in, redirect to homepage
if st.session_state.logged_in:
    st.switch_page("pages/1_🏠_Homepage.py")

# Login UI
st.title("🔐 Login")
st.markdown("---")

# Create tabs for Login and Register
tab1, tab2 = st.tabs(["Login", "Register"])

with tab1:
    with st.form("login_form"):
        st.subheader("Sign In")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
        with col2:
            forgot_password = st.form_submit_button("Forgot Password?", use_container_width=True)
        
        if submit:
            if username and password:
                is_valid, message, user_info = db.verify_user(username, password)
                
                if is_valid:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user_info
                    st.success(f"Welcome back, {user_info['full_name']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.warning("Please enter both username and password")
        
        if forgot_password:
            st.info("Please contact your administrator to reset your password.")

with tab2:
    with st.form("register_form"):
        st.subheader("Create Account")
        new_username = st.text_input("Username", key="reg_username")
        new_email = st.text_input("Email", key="reg_email")
        new_full_name = st.text_input("Full Name", key="reg_fullname")
        new_password = st.text_input("Password", type="password", key="reg_password")
        new_password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")
        
        submit_register = st.form_submit_button("Create Account", use_container_width=True, type="primary")
        
        if submit_register:
            if not all([new_username, new_email, new_full_name, new_password, new_password_confirm]):
                st.warning("Please fill in all fields")
            elif new_password != new_password_confirm:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                success, message = db.create_user(
                    username=new_username,
                    password=new_password,
                    email=new_email,
                    full_name=new_full_name,
                    role='user'
                )
                
                if success:
                    st.success("✅ Account created successfully! Please login.")
                else:
                    st.error(f"❌ {message}")


