import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import time
from streamlit_option_menu import option_menu
from contextlib import contextmanager

# --- CONFIG ---
st.set_page_config(page_title="BORWORN ULTIMATE ADMIN", page_icon="👑", layout="wide")

# --- DATABASE ENGINE ---
DB_NAME = 'borworn_ultimate_system_v4.db' # ปรับเวอร์ชันฐานข้อมูลเพื่ออัปเดตเลขบัญชีใหม่

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
        
        # --- ข้อมูลบัญชีท่านประธาน (ปรับปรุงเลขบัญชีเป็น 2 ทั้งหมด) ---
        master_id = "2222222222"
        master_name = "ศ.ดร.ธงชัย สว่างวงศ์ ณ อยุธยา"
        master_user = "Tongchai"
        master_pass = "1q2w3e4r"
        
        c.execute("INSERT OR IGNORE INTO Users (acc_id, username, name, password, balance, role) VALUES (?,?,?,?,?,?)",
                  (master_id, master_user, master_name, master_pass, 999999999.0, 'Admin'))

init_db()

# --- CSS: LUXURY SPACE GREY & GOLD ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #020617; color: white; }
    .luxury-header {
        background: linear-gradient(135deg, #1e293b 0%, #020617 100%);
        padding: 40px; border-radius: 0 0 30px 30px; text-align: center;
        border-bottom: 3px solid #f59e0b; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    button[kind="primary"] { background: linear-gradient(90deg, #b45309, #f59e0b) !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "login"
if "user_id" not in st.session_state: st.session_state.user_id = None
if "user_role" not in st.session_state: st.session_state.user_role = "User"

# ---------------------------------------------------------
# 🛡️ LOGIN SYSTEM
# ---------------------------------------------------------
if st.session_state.page == "login":
    st.markdown('<div class="luxury-header"><h1>BORWORN PRIVATE BANK</h1><p style="color:#f59e0b; letter-spacing:3px;">PRESTIGE ACCESS</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("")
        with st.form("login_form"):
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.form_submit_button("เข้าสู่ระบบระบบรักษาความปลอดภัย", use_container_width=True):
                with db_core() as c:
                    res = c.execute("SELECT acc_id, role, status, name FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if res:
                    if res[2] == 'Active':
                        st.session_state.user_id = res[0]
                        st.session_state.user_role = res[1]
                        st.session_state.user_full_name = res[3]
                        st.session_state.page = "admin_dashboard" if res[1] == 'Admin' else "client_dashboard"
                        st.rerun()
                    else: st.error("บัญชีนี้ถูกระงับการใช้งาน")
                else: st.error("ข้อมูลไม่ถูกต้อง")

# ---------------------------------------------------------
# 👑 ADMIN DASHBOARD
# ---------------------------------------------------------
elif st.session_state.page == "admin_dashboard":
    st.markdown(f'<div class="luxury-header"><h3>ยินดีต้อนรับท่านประธาน</h3><h2>{st.session_state.user_full_name}</h2><p style="color:#f59e0b;">เลขบัญชี: {st.session_state.user_id}</p></div>', unsafe_allow_html=True)
    
    menu = option_menu(None, ["จัดการสมาชิก", "จัดการสิทธิ์ Admin", "เปิดบัญชีใหม่", "ออกจากระบบ"], 
                         icons=['grid-fill', 'shield-lock-fill', 'person-plus-fill', 'door-closed'], orientation="horizontal")

    if menu == "จัดการสมาชิก":
        with db_core() as c:
            df = pd.read_sql("SELECT acc_id, name, username, balance, role, status FROM Users", c.connection)
        
        st.subheader("📊 ตรวจสอบข้อมูลลูกค้า")
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("💰 ระบบเสกเงินระบุจำนวน")
        c1, c2 = st.columns(2)
        target = c1.text_input("ระบุเลขบัญชีเป้าหมาย")
        amt = c2.number_input("ระบุจำนวนเงิน (฿)", min_value=0.0)
        
        if st.button("✨ อนุมัติรายการ", use_container_width=True, type="primary"):
            if target:
                with db_core() as c:
                    c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amt, target))
                st.success(f"เพิ่มเงินสำเร็จ! บัญชี {target} ได้รับ ฿{amt:,.2f}")
                time.sleep(1); st.rerun()

    elif menu == "จัดการสิทธิ์ Admin":
        st.subheader("🛡️ แก้ไขระดับสิทธิ์การเข้าถึง")
        target_acc = st.text_input("ระบุเลขบัญชีที่ต้องการปรับสิทธิ์")
        col_1, col_2 = st.columns(2)
        
        if col_1.button("👑 ตั้งเป็นแอดมิน"):
            with db_core() as c: c.execute("UPDATE Users SET role='Admin' WHERE acc_id=?", (target_acc,))
            st.success(f"เปลี่ยนสิทธิ์ {target_acc} เป็น Admin แล้ว")
            
        if col_2.button("👤 ตั้งเป็นลูกค้าปกติ"):
            if target_acc == "2222222222": st.error("ไม่สามารถปรับสิทธิ์บัญชีท่านประธานได้")
            else:
                with db_core() as c: c.execute("UPDATE Users SET role='User' WHERE acc_id=?", (target_acc,))
                st.warning(f"เปลี่ยนสิทธิ์ {target_acc} เป็น User แล้ว")

    elif menu == "เปิดบัญชีใหม่":
        with st.form("create_user"):
            new_id = "".join([str(random.randint(0, 9)) for _ in range(10)])
            new_u = st.text_input("กำหนด Username")
            new_n = st.text_input("ระบุชื่อลูกค้า")
            new_p = st.text_input("กำหนดรหัสผ่าน")
            if st.form_submit_button("เปิดบัญชี"):
                with db_core() as c:
                    c.execute("INSERT INTO Users (acc_id, username, name, password, balance) VALUES (?,?,?,?,?)", (new_id, new_u, new_n, new_p, 0.0))
                st.success(f"สำเร็จ! เลขบัญชี: {new_id}")

    elif menu == "ออกจากระบบ":
        st.session_state.page = "login"; st.rerun()

# ---------------------------------------------------------
# 🏠 CLIENT DASHBOARD
# ---------------------------------------------------------
elif st.session_state.page == "client_dashboard":
    with db_core() as c:
        u = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.user_id,)).fetchone()
    st.markdown(f'<div class="luxury-header"><small>ยอดเงินคงเหลือ</small><h1 style="color:#f59e0b;">฿ {u[4]:,.2f}</h1></div>', unsafe_allow_html=True)
    st.write(f"สวัสดีคุณ: {u[2]} | เลขบัญชี: {u[0]}")
    if st.button("ออกจากระบบ"):
        st.session_state.page = "login"; st.rerun()
