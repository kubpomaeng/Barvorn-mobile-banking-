import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import time
from streamlit_option_menu import option_menu
from contextlib import contextmanager

# --- CONFIG ---
st.set_page_config(page_title="Borworn Royal Bank", page_icon="🏛️", layout="wide")

# --- DATABASE ENGINE: HIGH-CONCURRENCY ARCHITECTURE ---
DB_NAME = 'borworn_enterprise_v1.db'

@st.cache_resource
def get_connection_pool():
    """สร้างการเชื่อมต่อหลักเพียงครั้งเดียวเพื่อประหยัดทรัพยากรเครื่อง"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=120) # รอคิวได้นานถึง 2 นาที
    conn.execute('PRAGMA journal_mode=WAL') # โหมดที่เสถียรที่สุดสำหรับการอ่าน/เขียนพร้อมกัน
    conn.execute('PRAGMA synchronous=NORMAL') # เพิ่มความเร็วในการเขียนข้อมูล
    conn.execute('PRAGMA cache_size=-64000') # เพิ่ม Cache ขนาด 64MB ในหน่วยความจำ
    return conn

@contextmanager
def db_transaction():
    """Context Manager สำหรับการทำธุรกรรมที่ปลอดภัยและเร็วที่สุด"""
    conn = get_connection_pool()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Database Error: {e}")
        raise e
    # หมายเหตุ: ไม่ปิดการเชื่อมต่อที่นี่เพราะเราใช้ cache_resource (Pool)

def init_db():
    with db_transaction() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS Users 
                     (acc_id TEXT PRIMARY KEY, username TEXT, name TEXT, password TEXT, 
                      balance REAL, pin TEXT, status TEXT DEFAULT 'Active', 
                      created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                     (sender_id TEXT, receiver_id TEXT, amount REAL, date TEXT, 
                      type TEXT, ref_no TEXT, memo TEXT)''')

init_db()

# --- CSS: MODERN LUXURY ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f0f2f5; }
    .main-card {
        background: white; padding: 30px; border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 8px solid #1e1b4b;
    }
    .bank-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: white; padding: 30px; border-radius: 25px; margin-bottom: 20px;
        box-shadow: 0 15px 30px rgba(0,0,0,0.2); border: 1px solid #eab308;
    }
    .pin-btn button {
        border-radius: 50% !important; width: 70px !important; height: 70px !important;
        font-size: 22px !important; background: #ffffff !important; color: #1e1b4b !important;
        border: 1px solid #ddd !important; margin: 5px auto !important; display: block !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATES ---
for state in ['auth_page', 'user_acc', 'pin_in']:
    if state not in st.session_state:
        st.session_state[state] = "gateway" if state == 'auth_page' else (None if state == 'user_acc' else "")

# ---------------------------------------------------------
# 🛡️ GATEWAY
# ---------------------------------------------------------
if st.session_state.auth_page == "gateway":
    st.markdown("<h1 style='text-align:center;'>🏛️ BORWORN ROYAL BANK</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>ENTERPRISE PRIVATE BANKING</p>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.subheader("Client Login")
        with st.form("c_login", clear_on_submit=True):
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            if st.form_submit_button("Secure Access", use_container_width=True, type="primary"):
                with db_transaction() as c:
                    user = c.execute("SELECT acc_id, pin, status FROM Users WHERE username=? AND password=?", (u_input, p_input)).fetchone()
                if user:
                    if user[2] == 'Active':
                        st.session_state.user_acc = user[0]
                        st.session_state.auth_page = "pin_verify" if user[1] else "setup_pin"
                        st.rerun()
                    else: st.error("Account Suspended")
                else: st.error("Invalid Credentials")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.subheader("Staff System")
        with st.form("s_login"):
            s_key = st.text_input("Access Key", type="password")
            if st.form_submit_button("Enter Terminal", use_container_width=True):
                if s_key == "Kub1":
                    st.session_state.auth_page = "admin_dashboard"
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 🔢 PIN VERIFICATION
# ---------------------------------------------------------
elif st.session_state.auth_page == "pin_verify":
    with db_transaction() as c:
        info = c.execute("SELECT name, pin FROM Users WHERE acc_id=?", (st.session_state.user_acc,)).fetchone()
    
    st.markdown(f"<h3 style='text-align:center;'>Hello, {info[0]}</h3>", unsafe_allow_html=True)
    dots = " ".join(["●" if i < len(st.session_state.pin_in) else "○" for i in range(6)])
    st.markdown(f"<h1 style='text-align:center; letter-spacing:10px;'>{dots}</h1>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for i, k in enumerate(['1','2','3','4','5','6','7','8','9','C','0','Del']):
        with [c1, c2, c3][i % 3]:
            if st.button(k, key=f"k_{k}", use_container_width=True):
                if k == 'Del': st.session_state.pin_in = st.session_state.pin_in[:-1]
                elif k == 'C': st.session_state.pin_in = ""
                elif len(st.session_state.pin_in) < 6: st.session_state.pin_in += k
                
                if len(st.session_state.pin_in) == 6:
                    if st.session_state.pin_in == info[1]:
                        st.session_state.auth_page = "client_home"
                        st.rerun()
                    else:
                        st.error("Invalid PIN"); st.session_state.pin_in = ""

# ---------------------------------------------------------
# 🏠 CLIENT DASHBOARD
# ---------------------------------------------------------
elif st.session_state.auth_page == "client_home":
    with db_transaction() as c:
        u = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.user_acc,)).fetchone()
    
    nav = option_menu(None, ["Dashboard", "Transfer", "Activity", "Exit"], 
        icons=['house', 'send', 'clock', 'door-open'], orientation="horizontal")

    if nav == "Dashboard":
        st.markdown(f"""<div class="bank-card">
            <small>Available Balance</small>
            <h1 style="color:white; font-size:40px;">฿ {u[4]:,.2f}</h1>
            <p>ID: {u[0]} | Holder: {u[2]}</p>
        </div>""", unsafe_allow_html=True)
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={u[0]}", width=200)

    elif nav == "Transfer":
        with st.form("tx_form"):
            t_id = st.text_input("Receiver Account Number")
            amt = st.number_input("Amount (THB)", min_value=1.0)
            if st.form_submit_button("Execute Transfer", use_container_width=True, type="primary"):
                with db_transaction() as c:
                    recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (t_id,)).fetchone()
                    if recv and u[4] >= amt and t_id != u[0]:
                        c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (amt, u[0]))
                        c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amt, t_id))
                        c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?,?)", 
                                  (u[0], t_id, amt, datetime.now().strftime("%d/%m/%y %H:%M"), "Transfer", f"REF{random.randint(1000,9999)}", ""))
                        st.success("Success!"); st.balloons()
                    else: st.error("Check balance or recipient ID")

    elif nav == "Activity":
        with db_transaction() as c:
            df = pd.read_sql(f"SELECT date, receiver_id as 'To', amount FROM Transactions WHERE sender_id='{u[0]}' OR receiver_id='{u[0]}'", c.connection)
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    elif nav == "Exit":
        st.session_state.auth_page = "gateway"; st.session_state.user_acc = None; st.rerun()

# ---------------------------------------------------------
# 👨‍💼 ADMIN TERMINAL
# ---------------------------------------------------------
elif st.session_state.auth_page == "admin_dashboard":
    st.title("👨‍💼 Staff Terminal")
    a_nav = option_menu(None, ["Open Acc", "Controls"], orientation="horizontal")
    
    if a_nav == "Open Acc":
        with st.form("new_acc"):
            new_id = "".join([str(random.randint(0, 9)) for _ in range(10)])
            n_u = st.text_input("Username")
            n_n = st.text_input("Client Name")
            n_p = st.text_input("Password")
            n_b = st.number_input("Opening Balance", value=1000.0)
            if st.form_submit_button("Register Account"):
                with db_transaction() as c:
                    c.execute("INSERT INTO Users (acc_id, username, name, password, balance, created_at) VALUES (?,?,?,?,?,?)",
                              (new_id, n_u, n_n, n_p, n_b, datetime.now().strftime("%d/%m/%Y")))
                st.success(f"Registered: {new_id}")

    elif a_nav == "Controls":
        with db_transaction() as c:
            df_all = pd.read_sql("SELECT acc_id, name, balance, status FROM Users", c.connection)
        st.dataframe(df_all, use_container_width=True)
        tid = st.text_input("Enter Account ID to Suspend/Active")
        c1, c2 = st.columns(2)
        if c1.button("Suspend"):
            with db_transaction() as c: c.execute("UPDATE Users SET status='Suspended' WHERE acc_id=?", (tid,))
            st.rerun()
        if c2.button("Activate"):
            with db_transaction() as c: c.execute("UPDATE Users SET status='Active' WHERE acc_id=?", (tid,))
            st.rerun()

    if st.button("Close Terminal"): st.session_state.auth_page = "gateway"; st.rerun()

# --- SETUP PIN ---
elif st.session_state.auth_page == "setup_pin":
    p1 = st.text_input("New PIN (6-digits)", type="password", max_chars=6)
    if st.button("Save PIN"):
        if len(p1) == 6 and p1.isdigit():
            with db_transaction() as c:
                c.execute("UPDATE Users SET pin=? WHERE acc_id=?", (p1, st.session_state.user_acc))
            st.session_state.auth_page = "client_home"; st.rerun()
