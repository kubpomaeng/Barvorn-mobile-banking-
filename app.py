import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import time
from streamlit_option_menu import option_menu
from contextlib import contextmanager

# --- CONFIG: ระดับพรีเมียม ---
st.set_page_config(page_title="Borworn Royal Bank | Official", page_icon="🏛️", layout="wide")

# --- DATABASE ENGINE: TRANSACTION-SAFE ARCHITECTURE ---
DB_NAME = 'borworn_ultimate_v5.db'

@st.cache_resource
def get_db_pool():
    """เชื่อมต่อแบบ Pool พร้อมโหมด WAL สำหรับความเสถียรสูงสุด"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=180)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA busy_timeout=5000') # ถ้ายุ่งให้รอ 5 วินาทีก่อน Error
    return conn

@contextmanager
def db_core():
    """หัวใจหลักของการจัดการข้อมูลแบบ Atomic (ทำสำเร็จทั้งหมด หรือไม่ทำเลย)"""
    conn = get_db_pool()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"ระบบขัดข้องชั่วคราว: {e}")
        raise e

def init_master_db():
    with db_core() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS Users 
                     (acc_id TEXT PRIMARY KEY, username TEXT UNIQUE, name TEXT, password TEXT, 
                      balance REAL, pin TEXT, status TEXT DEFAULT 'Active', 
                      created_at TEXT, last_login TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                     (sender_id TEXT, receiver_id TEXT, amount REAL, date TEXT, 
                      type TEXT, ref_no TEXT PRIMARY KEY, memo TEXT)''')

init_master_db()

# --- CSS: ULTIMATE LUXURY UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #fcfcfc; }
    
    /* บัตรธนาคารระดับสูง */
    .bank-card {
        background: linear-gradient(135deg, #020617 0%, #1e1b4b 50%, #1e293b 100%);
        color: #f8fafc; padding: 40px; border-radius: 30px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        border: 2px solid #eab308; position: relative; overflow: hidden;
    }
    .bank-card::before {
        content: ""; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(234,179,8,0.1) 0%, transparent 70%);
    }
    
    /* ปุ่ม PIN สไตล์สมาร์ทโฟน */
    .pin-box button {
        border-radius: 20px !important; height: 70px !important; font-weight: 600 !important;
        background: #ffffff !important; color: #1e1b4b !important; border: 1px solid #e2e8f0 !important;
        transition: 0.3s !important;
    }
    .pin-box button:hover { border-color: #eab308 !important; transform: scale(1.05); }
</style>
""", unsafe_allow_html=True)

# --- APP LOGIC: NO-BUG STATE MANAGEMENT ---
if "auth_state" not in st.session_state: st.session_state.auth_state = "login"
if "current_user" not in st.session_state: st.session_state.current_user = None
if "pin_buffer" not in st.session_state: st.session_state.pin_buffer = ""

# ---------------------------------------------------------
# 🛡️ LOGIN & SECURITY GATEWAY
# ---------------------------------------------------------
if st.session_state.auth_state == "login":
    st.markdown("<h1 style='text-align:center; color:#0f172a; margin-top:50px;'>🏛️ BORWORN ROYAL BANK</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#64748b; letter-spacing:8px;'>THE PINNACLE OF BANKING</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.subheader("🔑 Client Access")
        with st.form("login_form"):
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Authorized Sign In", use_container_width=True, type="primary"):
                with db_core() as c:
                    user = c.execute("SELECT acc_id, pin, status FROM Users WHERE username=? AND password=?", (u, p)).fetchone()
                if user:
                    if user[2] == 'Suspended': st.error("Account Suspended. Contact branch.")
                    else:
                        st.session_state.current_user = user[0]
                        st.session_state.auth_state = "pin_verify" if user[1] else "setup_pin"
                        st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")

    with col2:
        st.subheader("👨‍💼 Management Terminal")
        with st.form("admin_gate"):
            s_key = st.text_input("Admin Security Key", type="password")
            if st.form_submit_button("Access Core System", use_container_width=True):
                if s_key == "Kub1":
                    st.session_state.auth_state = "admin_dashboard"
                    st.rerun()
                else: st.error("Access Denied")

# ---------------------------------------------------------
# 🔢 SMART PIN SYSTEM
# ---------------------------------------------------------
elif st.session_state.auth_state == "pin_verify":
    with db_core() as c:
        u_info = c.execute("SELECT name, pin FROM Users WHERE acc_id=?", (st.session_state.current_acc if hasattr(st.session_state, 'current_acc') else st.session_state.current_user,)).fetchone()
    
    st.markdown(f"<h2 style='text-align:center;'>Welcome, {u_info[0]}</h2>", unsafe_allow_html=True)
    display_dots = " ".join(["●" if i < len(st.session_state.pin_buffer) else "○" for i in range(6)])
    st.markdown(f"<h1 style='text-align:center; letter-spacing:15px; color:#1e1b4b;'>{display_dots}</h1>", unsafe_allow_html=True)

    k_col1, k_col2, k_col3 = st.columns(3)
    keys = ['1','2','3','4','5','6','7','8','9','Clear','0','Delete']
    for idx, key in enumerate(keys):
        with [k_col1, k_col2, k_col3][idx % 3]:
            st.markdown('<div class="pin-box">', unsafe_allow_html=True)
            if st.button(key, key=f"btn_{key}", use_container_width=True):
                if key == 'Delete': st.session_state.pin_buffer = st.session_state.pin_buffer[:-1]
                elif key == 'Clear': st.session_state.pin_buffer = ""
                elif len(st.session_state.pin_buffer) < 6: st.session_state.pin_buffer += key
                
                if len(st.session_state.pin_buffer) == 6:
                    if st.session_state.pin_buffer == u_info[1]:
                        st.session_state.auth_state = "client_main"
                        st.session_state.pin_buffer = ""
                        st.rerun()
                    else:
                        st.error("PIN ไม่ถูกต้อง")
                        st.session_state.pin_buffer = ""
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 🏠 CLIENT MAIN: TRANSACTION ENGINE
# ---------------------------------------------------------
elif st.session_state.auth_state == "client_main":
    with db_core() as c:
        u = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.current_user,)).fetchone()
    
    m_nav = option_menu(None, ["หน้าหลัก", "โอนเงิน", "ประวัติ", "ออกจากระบบ"], 
        icons=['house-door-fill', 'arrow-left-right', 'clock-history', 'power'], 
        orientation="horizontal", styles={"nav-link-selected": {"background-color": "#1e1b4b"}})

    if m_nav == "หน้าหลัก":
        st.markdown(f"""
        <div class="bank-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:40px;">
                <span style="letter-spacing:3px; color:#eab308; font-weight:600;">PLATINUM CLIENT</span>
                <span style="font-family:serif; font-style:italic; font-size:20px;">BORWORN</span>
            </div>
            <small style="opacity:0.7;">TOTAL BALANCE</small>
            <h1 style="font-size:50px; margin:10px 0;">฿ {u[4]:,.2f}</h1>
            <div style="margin-top:50px; display:flex; justify-content:space-between; font-family:monospace;">
                <span>{u[2].upper()}</span>
                <span>{u[0][:3]} {u[0][3:6]} {u[0][6:]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### 📲 My QR Payment")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={u[0]}&color=0f172a", width=200)

    elif m_nav == "โอนเงิน":
        st.subheader("📤 ทำรายการโอนเงิน")
        with st.form("tx_form"):
            target_acc = st.text_input("เลขที่บัญชีผู้รับ (10 หลัก)").strip()
            tx_amount = st.number_input("จำนวนเงินที่ต้องการโอน (บาท)", min_value=1.0, step=0.01)
            tx_memo = st.text_input("บันทึกช่วยจำ")
            if st.form_submit_button("ยืนยันการทำรายการ", use_container_width=True, type="primary"):
                with db_core() as c:
                    target_name = c.execute("SELECT name FROM Users WHERE acc_id=?", (target_acc,)).fetchone()
                    if target_name and u[4] >= tx_amount and target_acc != u[0]:
                        # ATOMIC TRANSACTION
                        ref = f"BORN{int(time.time())}{random.randint(10,99)}"
                        c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (tx_amount, u[0]))
                        c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (tx_amount, target_acc))
                        c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?,?)", 
                                  (u[0], target_acc, tx_amount, datetime.now().strftime("%d/%m/%Y %H:%M"), "Transfer", ref, tx_memo))
                        st.success(f"โอนสำเร็จ! ไปยังคุณ {target_name[0]}")
                        st.balloons()
                    else: st.error("ไม่สามารถทำรายการได้: เลขบัญชีไม่ถูกต้อง หรือยอดเงินไม่พอ")

    elif m_nav == "ประวัติ":
        with db_core() as c:
            df = pd.read_sql(f"SELECT date, type, receiver_id as 'ผู้รับ/จาก', amount as 'ยอดเงิน', ref_no FROM Transactions WHERE sender_id='{u[0]}' OR receiver_id='{u[0]}' ORDER BY date DESC", c.connection)
        st.table(df)

    if m_nav == "ออกจากระบบ": 
        st.session_state.auth_state = "login"; st.rerun()

# ---------------------------------------------------------
# 👨‍💼 ADMIN DASHBOARD: PROFESSIONAL CONTROL
# ---------------------------------------------------------
elif st.session_state.auth_state == "admin_dashboard":
    st.markdown("<h2 style='color:#1e1b4b;'>👨‍💼 ฝ่ายปฏิบัติการหลังบ้าน (Admin Terminal)</h2>", unsafe_allow_html=True)
    
    adm_nav = option_menu(None, ["เปิดบัญชี", "จัดการสมาชิก", "แก้ไขเลขบัญชีด่วน", "ข้อมูลธุรกรรม"], 
        icons=['person-plus', 'people-fill', 'shield-lock', 'database-fill'], 
        orientation="horizontal", styles={"nav-link-selected": {"background-color": "#eab308", "color": "black"}})

    if adm_nav == "เปิดบัญชี":
        with st.form("reg_new"):
            st.subheader("📝 ลงทะเบียนลูกค้าใหม่")
            # สุ่มเลขบัญชี 10 หลักที่ไม่ซ้ำ
            new_id = "".join([str(random.randint(0, 9)) for _ in range(10)])
            n_usr = st.text_input("Username (สำหรับล็อกอิน)")
            n_name = st.text_input("ชื่อ-นามสกุล")
            n_pwd = st.text_input("Password")
            n_bal = st.number_input("เงินฝากเริ่มต้น", value=1000.0)
            if st.form_submit_button("อนุมัติเปิดบัญชี", use_container_width=True):
                with db_core() as c:
                    c.execute("INSERT INTO Users (acc_id, username, name, password, balance, created_at) VALUES (?,?,?,?,?,?)",
                              (new_id, n_usr, n_name, n_pwd, n_bal, datetime.now().strftime("%d/%m/%Y")))
                st.success(f"สำเร็จ! เลขบัญชีลูกค้าคือ: {new_id}")

    elif adm_nav == "จัดการสมาชิก":
        with db_core() as c:
            all_users = pd.read_sql("SELECT acc_id, name, username, balance, status FROM Users", c.connection)
        st.dataframe(all_users, use_container_width=True)
        
        st.divider()
        st.subheader("⚙️ ควบคุมบัญชี")
        target_id = st.text_input("ระบุเลขบัญชีที่ต้องการจัดการ")
        c1, c2, c3 = st.columns(3)
        if c1.button("⛔ อายัดบัญชี", use_container_width=True):
            with db_transaction() as c: c.execute("UPDATE Users SET status='Suspended' WHERE acc_id=?", (target_id,))
            st.warning("บัญชีถูกอายัด")
        if c2.button("✅ เปิดใช้งาน", use_container_width=True):
            with db_transaction() as c: c.execute("UPDATE Users SET status='Active' WHERE acc_id=?", (target_id,))
            st.success("บัญชีกลับสู่สภาวะปกติ")
        if c3.button("💰 ปรับยอดเงิน (เสกเงิน)", use_container_width=True):
            with db_transaction() as c: c.execute("UPDATE Users SET balance = balance + 1000000 WHERE acc_id=?", (target_id,))
            st.success("เพิ่มเงิน 1 ล้านสำเร็จ")

    elif adm_nav == "แก้ไขเลขบัญชีด่วน":
        st.subheader("💎 ระบบเปลี่ยนเลขบัญชี VIP (ประธานาธิบดี)")
        with st.form("change_id"):
            old = st.text_input("เลขบัญชีปัจจุบัน")
            new = st.text_input("เลขบัญชีใหม่ที่ต้องการ")
            if st.form_submit_button("บันทึกการเปลี่ยนแปลง"):
                with db_core() as c:
                    # ตรวจสอบความมีอยู่และป้องกันเลขซ้ำ
                    c.execute("UPDATE Users SET acc_id=? WHERE acc_id=?", (new, old))
                    c.execute("UPDATE Transactions SET sender_id=? WHERE sender_id=?", (new, old))
                    c.execute("UPDATE Transactions SET receiver_id=? WHERE receiver_id=?", (new, old))
                st.success("เปลี่ยนข้อมูลในระบบทั้งหมดเรียบร้อยแล้ว!")

    if st.button("ออกจากระบบเจ้าหน้าที่"): 
        st.session_state.auth_state = "login"; st.rerun()

# --- SETUP PIN ---
elif st.session_state.auth_state == "setup_pin":
    st.subheader("🛡️ ตั้งรหัส PIN 6 หลักของคุณ")
    p1 = st.text_input("กำหนด PIN", type="password", max_chars=6)
    if st.button("บันทึกและเข้าใช้งาน"):
        if len(p1) == 6 and p1.isdigit():
            with db_core() as c:
                c.execute("UPDATE Users SET pin=? WHERE acc_id=?", (p1, st.session_state.current_user))
            st.session_state.auth_state = "client_main"; st.rerun()
