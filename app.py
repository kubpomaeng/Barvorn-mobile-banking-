import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import time
from streamlit_option_menu import option_menu
from contextlib import contextmanager

# --- CONFIG ---
st.set_page_config(page_title="BORWORN PRESTIGE", page_icon="🏛️", layout="wide")

# --- DATABASE ---
DB_NAME = 'borworn_ultimate_v7.db'

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=300)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

@contextmanager
def db_core():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Error: {e}")
        raise e

def init_db():
    with db_core() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS Users 
                     (acc_id TEXT PRIMARY KEY, username TEXT UNIQUE, name TEXT, password TEXT, 
                      balance REAL, pin TEXT, status TEXT DEFAULT 'Active', role TEXT DEFAULT 'User')''')
        c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                     (sender_id TEXT, receiver_id TEXT, amount REAL, date TEXT, 
                      type TEXT, ref_no TEXT PRIMARY KEY, memo TEXT)''')
        
        # บัญชีท่านประธาน ศ.ดร.ธงชัย (Master Account)
        c.execute("INSERT OR IGNORE INTO Users (acc_id, username, name, password, balance, role) VALUES (?,?,?,?,?,?)",
                  ('2222222222', 'Tongchai', 'ศ.ดร.ธงชัย สว่างวงศ์ ณ อยุธยา', '1q2w3e4r', 999999999.0, 'Admin'))

init_db()

# --- ULTRA REALISTIC & WHITE TEXT CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;300;400;500;600&display=swap');
    
    /* บังคับสีข้อความทั้งหมดเป็นสีขาว */
    html, body, [class*="st-"] {
        font-family: 'Kanit', sans-serif;
        color: #FFFFFF !important;
    }
    
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #020617);
    }

    /* ปรับแต่ง Label ของช่อง Input ให้เป็นสีขาว */
    .stTextInput label, .stNumberInput label, .stTextArea label {
        color: #FFFFFF !important;
        font-weight: 400 !important;
        font-size: 1.1rem !important;
    }

    /* ปรับแต่งช่องกรอกข้อมูลให้พื้นหลังเข้มขึ้นเพื่อให้ตัวหนังสือสีขาวเด่น */
    input {
        background-color: #0f172a !important;
        color: #FFFFFF !important;
        border: 1px solid #334155 !important;
    }

    .luxury-header {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.8) 0%, rgba(2, 6, 23, 1) 100%);
        padding: 50px 20px;
        border-radius: 0 0 50px 50px;
        text-align: center;
        border-bottom: 2px solid #f59e0b;
        box-shadow: 0 15px 35px rgba(0,0,0,0.6);
        margin-bottom: 30px;
    }

    .card-glass {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        border-radius: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-top: 20px;
    }

    .qr-frame {
        background: #FFFFFF;
        padding: 15px;
        border-radius: 20px;
        display: inline-block;
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
    }

    .gold-badge {
        background: linear-gradient(90deg, #b45309, #f59e0b);
        color: white !important;
        padding: 5px 15px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    /* ปุ่มสีทองโดดเด่น */
    button[kind="primary"] {
        background: linear-gradient(90deg, #b45309 0%, #f59e0b 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 15px !important;
        font-weight: 600 !important;
        height: 55px !important;
        transition: 0.3s !important;
    }
    
    button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(245, 158, 11, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "login"
if "user_id" not in st.session_state: st.session_state.user_id = None

# --- 🛡️ LOGIN PAGE ---
if st.session_state.page == "login":
    st.markdown('<div class="luxury-header"><h1>BORWORN PRIVATE BANK</h1><span class="gold-badge">Ultimate Prestige</span></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("")
        with st.form("login_gate"):
            u = st.text_input("Username / ชื่อผู้ใช้งาน")
            p = st.text_input("Password / รหัสผ่าน", type="password")
            if st.form_submit_button("UNLOCK SYSTEM", use_container_width=True, type="primary"):
                with db_core() as c:
                    res = c.execute("SELECT acc_id, role, name FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if res:
                    st.session_state.user_id, st.session_state.user_role, st.session_state.user_full_name = res
                    st.session_state.page = "main"
                    st.rerun()
                else: st.error("Access Denied: ข้อมูลไม่ถูกต้อง")

# --- 🏦 MAIN SYSTEM ---
elif st.session_state.page == "main":
    with db_core() as c:
        u_bal = c.execute("SELECT balance FROM Users WHERE acc_id=?", (st.session_state.user_id,)).fetchone()[0]
    
    st.markdown(f'''
    <div class="luxury-header">
        <p style="margin-bottom:0; opacity:0.8; font-weight:300;">PRESTIGE ACCOUNT HOLDER</p>
        <h2 style="margin-top:0; letter-spacing:1px;">{st.session_state.user_full_name}</h2>
        <h1 style="color:#f59e0b !important; font-size:3.5rem; margin:20px 0;">฿ {u_bal:,.2f}</h1>
        <span class="gold-badge">Account: {st.session_state.user_id}</span>
    </div>
    ''', unsafe_allow_html=True)

    menu_ops = ["ศูนย์ธุรกรรม", "ประวัติรายการ"]
    if st.session_state.user_role == 'Admin':
        menu_ops.append("แผงควบคุมแอดมิน")
    menu_ops.append("ออกจากระบบ")
    
    choice = option_menu(None, menu_ops, 
                         icons=['cash-coin', 'clock-history', 'shield-shaded', 'door-open'], 
                         orientation="horizontal",
                         styles={"container": {"background-color": "transparent"},
                                 "nav-link": {"color": "white", "--hover-color": "#334155"},
                                 "nav-link-selected": {"background-color": "#f59e0b"}})

    if choice == "ศูนย์ธุรกรรม":
        col_s, col_r = st.columns(2, gap="large")

        # --- ฝั่งส่งเงิน (โอนเงิน) ---
        with col_s:
            st.markdown('<div class="card-glass">', unsafe_allow_html=True)
            st.markdown('### 💸 โอนเงินไปยังบัญชีอื่น')
            with st.form("transfer_action"):
                t_acc = st.text_input("ระบุเลขบัญชีผู้รับ")
                t_amt = st.number_input("ระบุจำนวนเงินที่ต้องการโอน (฿)", min_value=0.0, step=500.0)
                t_memo = st.text_input("บันทึกช่วยจำ (ไม่บังคับ)")
                if st.form_submit_button("ยืนยันการโอนเงิน", use_container_width=True, type="primary"):
                    with db_core() as c:
                        recv_name = c.execute("SELECT name FROM Users WHERE acc_id=?", (t_acc,)).fetchone()
                        if recv_name and u_bal >= t_amt and t_acc != st.session_state.user_id:
                            c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (t_amt, st.session_state.user_id))
                            c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (t_amt, t_acc))
                            c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?,?)", 
                                      (st.session_state.user_id, t_acc, t_amt, datetime.now().strftime("%H:%M:%S | %d/%m/%Y"), "Transfer", f"REF{int(time.time())}", t_memo))
                            st.success(f"โอนสำเร็จไปยังคุณ {recv_name[0]}")
                            st.balloons(); time.sleep(1); st.rerun()
                        else: st.error("ตรวจสอบเลขบัญชีหรือยอดเงินคงเหลืออีกครั้ง")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- ฝั่งรับเงิน (QR & My Account) ---
        with col_r:
            st.markdown('<div class="card-glass" style="text-align:center;">', unsafe_allow_html=True)
            st.markdown('### 📥 รับเงินผ่าน QR Code')
            st.write("แชร์ QR Code นี้เพื่อให้ผู้อื่นโอนเงินเข้าบัญชีท่าน")
            
            qr_gen = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={st.session_state.user_id}&color=020617&bgcolor=ffffff"
            st.markdown(f'<div class="qr-frame"><img src="{qr_gen}"></div>', unsafe_allow_html=True)
            
            st.markdown(f'''
                <div style="margin-top:20px;">
                    <p style="margin:0; opacity:0.7;">เลขที่บัญชีรับเงิน</p>
                    <h2 style="color:#f59e0b !important;">{st.session_state.user_id}</h2>
                    <p style="margin:0; font-weight:300;">{st.session_state.user_full_name}</p>
                </div>
            ''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif choice == "แผงควบคุมแอดมิน":
        st.markdown('<div class="card-glass">', unsafe_allow_html=True)
        st.subheader("👑 Master Command Center")
        with db_core() as c:
            all_users = pd.read_sql("SELECT acc_id, name, balance, role, status FROM Users", c.connection)
        st.dataframe(all_users, use_container_width=True)
        
        st.divider()
        st.markdown("### 💉 คำสั่งฉีดสภาพคล่อง (เสกเงิน)")
        c_target, c_amt = st.columns(2)
        target_acc = c_target.text_input("เลขบัญชีเป้าหมาย")
        inject_amt = c_amt.number_input("จำนวนเงินที่ต้องการเสก (฿)", min_value=0.0)
        if st.button("EXECUTE MONEY INJECTION", use_container_width=True, type="primary"):
            with db_core() as c:
                c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (inject_amt, target_acc))
            st.success("Transaction Complete: เพิ่มยอดเงินเรียบร้อย")
            time.sleep(1); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif choice == "ออกจากระบบ":
        st.session_state.page = "login"; st.rerun()
