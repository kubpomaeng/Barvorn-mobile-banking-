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

# --- DATABASE ENGINE ---
DB_NAME = 'borworn_enterprise_v2.db'

@st.cache_resource
def get_connection_pool():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=120)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    return conn

@contextmanager
def db_transaction():
    conn = get_connection_pool()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"ข้อผิดพลาดฐานข้อมูล: {e}")
        raise e

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

# --- CSS: LUXURY THAI UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f8fafc; }
    .main-card {
        background: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 5px solid #1e1b4b;
    }
    .admin-card {
        background: #ffffff; padding: 20px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-bottom: 15px;
    }
    .bank-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: white; padding: 30px; border-radius: 25px; margin-bottom: 20px;
        box-shadow: 0 15px 30px rgba(0,0,0,0.2); border: 1px solid #eab308;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATES ---
if "auth_page" not in st.session_state: st.session_state.auth_page = "gateway"
if "user_acc" not in st.session_state: st.session_state.user_acc = None
if "pin_in" not in st.session_state: st.session_state.pin_in = ""

# ---------------------------------------------------------
# 🛡️ GATEWAY
# ---------------------------------------------------------
if st.session_state.auth_page == "gateway":
    st.markdown("<h1 style='text-align:center;'>🏛️ BORWORN ROYAL BANK</h1>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.subheader("🔑 เข้าสู่ระบบลูกค้า")
        with st.form("c_login", clear_on_submit=True):
            u_input = st.text_input("ชื่อผู้ใช้งาน (Username)")
            p_input = st.text_input("รหัสผ่าน (Password)", type="password")
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True, type="primary"):
                with db_transaction() as c:
                    user = c.execute("SELECT acc_id, pin, status FROM Users WHERE username=? AND password=?", (u_input, p_input)).fetchone()
                if user:
                    if user[2] == 'Active':
                        st.session_state.user_acc = user[0]
                        st.session_state.auth_page = "pin_verify" if user[1] else "setup_pin"
                        st.rerun()
                    else: st.error("บัญชีนี้ถูกระงับการใช้งาน")
                else: st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.subheader("👨‍💼 ระบบเจ้าหน้าที่")
        with st.form("s_login"):
            s_key = st.text_input("รหัสผ่านเจ้าหน้าที่", type="password")
            if st.form_submit_button("เข้าสู่ระบบจัดการ", use_container_width=True):
                if s_key == "Kub1":
                    st.session_state.auth_page = "admin_dashboard"
                    st.rerun()
                else: st.error("รหัสผ่านไม่ถูกต้อง")
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 🔢 PIN VERIFICATION
# ---------------------------------------------------------
elif st.session_state.auth_page == "pin_verify":
    with db_transaction() as c:
        info = c.execute("SELECT name, pin FROM Users WHERE acc_id=?", (st.session_state.user_acc,)).fetchone()
    
    st.markdown(f"<h3 style='text-align:center;'>ยินดีต้อนรับคุณ {info[0]}</h3>", unsafe_allow_html=True)
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
                        st.error("รหัส PIN ไม่ถูกต้อง"); st.session_state.pin_in = ""

# ---------------------------------------------------------
# 🏠 CLIENT DASHBOARD (ตัดสั้นเพื่อความกระชับ)
# ---------------------------------------------------------
elif st.session_state.auth_page == "client_home":
    with db_transaction() as c:
        u = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.user_acc,)).fetchone()
    
    nav = option_menu(None, ["หน้าหลัก", "โอนเงิน", "ประวัติ", "ออกจากระบบ"], 
        icons=['house', 'send', 'clock', 'door-open'], orientation="horizontal")

    if nav == "หน้าหลัก":
        st.markdown(f"""<div class="bank-card">
            <small>ยอดเงินที่ใช้ได้</small>
            <h1 style="color:white; font-size:40px;">฿ {u[4]:,.2f}</h1>
            <p>เลขบัญชี: {u[0]} | ชื่อบัญชี: {u[2]}</p>
        </div>""", unsafe_allow_html=True)
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={u[0]}", width=200)

    elif nav == "โอนเงิน":
        with st.form("tx"):
            t_id = st.text_input("เลขบัญชีผู้รับ")
            amt = st.number_input("จำนวนเงิน (บาท)", min_value=1.0)
            if st.form_submit_button("ยืนยันการโอน", use_container_width=True, type="primary"):
                with db_transaction() as c:
                    recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (t_id,)).fetchone()
                    if recv and u[4] >= amt and t_id != u[0]:
                        c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (amt, u[0]))
                        c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amt, t_id))
                        c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?,?)", (u[0], t_id, amt, datetime.now().strftime("%d/%m/%y %H:%M"), "โอนเงิน", f"REF{random.randint(1000,9999)}", ""))
                        st.success(f"โอนสำเร็จไปยังคุณ {recv[0]}!"); st.balloons()
                    else: st.error("ข้อมูลไม่ถูกต้องหรือเงินไม่พอ")

    elif nav == "ประวัติ":
        with db_transaction() as c:
            df = pd.read_sql(f"SELECT date as 'วัน/เวลา', type as 'ประเภท', receiver_id as 'ผู้รับ', amount as 'จำนวน' FROM Transactions WHERE sender_id='{u[0]}' OR receiver_id='{u[0]}'", c.connection)
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    elif nav == "ออกจากระบบ":
        st.session_state.auth_page = "gateway"; st.session_state.user_acc = None; st.rerun()

# ---------------------------------------------------------
# 👨‍💼 STAFF SYSTEM (เมนูภาษาไทย + เปลี่ยนเลขบัญชี)
# ---------------------------------------------------------
elif st.session_state.auth_page == "admin_dashboard":
    st.markdown("<h2 style='color:#1e1b4b;'>👨‍💼 ศูนย์ควบคุมเจ้าหน้าที่อาวุโส</h2>", unsafe_allow_html=True)
    
    a_nav = option_menu(None, ["เปิดบัญชีใหม่", "จัดการสมาชิก", "แก้ไขเลขบัญชี", "ธุรกรรมทั้งหมด"], 
        icons=['person-plus', 'people', 'pencil-square', 'file-earmark-text'], 
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={"nav-link-selected": {"background-color": "#eab308", "color": "black"}})
    
    if a_nav == "เปิดบัญชีใหม่":
        with st.form("new_acc"):
            st.subheader("📝 ลงทะเบียนลูกค้าใหม่")
            # ระบบสุ่มเลขบัญชี 10 หลัก
            suggested_id = "".join([str(random.randint(0, 9)) for _ in range(10)])
            n_u = st.text_input("ตั้งชื่อล็อกอิน (Username)")
            n_n = st.text_input("ชื่อ-นามสกุล ลูกค้า")
            n_p = st.text_input("รหัสผ่าน (Password)")
            n_b = st.number_input("เงินฝากเริ่มต้น", value=1000.0)
            st.info(f"ระบบจะใช้เลขบัญชีสุ่ม: {suggested_id}")
            
            if st.form_submit_button("สร้างบัญชีทันที", use_container_width=True, type="primary"):
                with db_transaction() as c:
                    c.execute("INSERT INTO Users (acc_id, username, name, password, balance, created_at) VALUES (?,?,?,?,?,?)",
                              (suggested_id, n_u, n_n, n_p, n_b, datetime.now().strftime("%d/%m/%Y")))
                st.success(f"สร้างบัญชีเรียบร้อย! เลขบัญชีคือ: {suggested_id}")

    elif a_nav == "จัดการสมาชิก":
        st.subheader("👥 รายชื่อลูกค้าในระบบ")
        with db_transaction() as c:
            df_all = pd.read_sql("SELECT acc_id as 'เลขบัญชี', name as 'ชื่อลูกค้า', balance as 'ยอดเงิน', status as 'สถานะ' FROM Users", c.connection)
        st.dataframe(df_all, use_container_width=True)
        
        st.divider()
        tid = st.text_input("กรอกเลขบัญชีที่ต้องการจัดการ (อายัด/เปิด)")
        c1, c2 = st.columns(2)
        if c1.button("⛔ อายัดบัญชี (Suspend)", use_container_width=True):
            with db_transaction() as c: c.execute("UPDATE Users SET status='Suspended' WHERE acc_id=?", (tid,))
            st.warning(f"บัญชี {tid} ถูกอายัดแล้ว")
        if c2.button("✅ เปิดใช้งานบัญชี (Active)", use_container_width=True):
            with db_transaction() as c: c.execute("UPDATE Users SET status='Active' WHERE acc_id=?", (tid,))
            st.success(f"บัญชี {tid} กลับมาใช้งานได้ปกติ")

    elif a_nav == "แก้ไขเลขบัญชี":
        st.subheader("🛡️ ระบบเปลี่ยนเลขบัญชีด่วน (VIP Only)")
        st.warning("⚠️ คำเตือน: การเปลี่ยนเลขบัญชีจะส่งผลต่อการค้นหาข้อมูลเดิม กรุณาตรวจสอบให้แน่ใจก่อนดำเนินการ")
        
        with st.form("change_acc_id"):
            old_id = st.text_input("เลขบัญชีเดิม")
            new_id = st.text_input("เลขบัญชีใหม่ที่ต้องการ (เช่น เลขมงคล หรือเลขท่านประธานาธิบดี)")
            
            if st.form_submit_button("ยืนยันการเปลี่ยนเลขบัญชี", use_container_width=True):
                if old_id and new_id:
                    with db_transaction() as c:
                        # ตรวจสอบว่ามีบัญชีเดิมจริงไหม
                        exists = c.execute("SELECT name FROM Users WHERE acc_id=?", (old_id,)).fetchone()
                        if exists:
                            # ตรวจสอบว่าเลขใหม่ซ้ำไหม
                            duplicate = c.execute("SELECT name FROM Users WHERE acc_id=?", (new_id,)).fetchone()
                            if not duplicate:
                                # เริ่มการอัปเดต (ต้องอัปเดตทั้งตาราง Users และ Transactions เพื่อให้ประวัติไม่หาย)
                                c.execute("UPDATE Users SET acc_id=? WHERE acc_id=?", (new_id, old_id))
                                c.execute("UPDATE Transactions SET sender_id=? WHERE sender_id=?", (new_id, old_id))
                                c.execute("UPDATE Transactions SET receiver_id=? WHERE receiver_id=?", (new_id, old_id))
                                st.success(f"เปลี่ยนเลขบัญชีของคุณ {exists[0]} สำเร็จ! จาก {old_id} เป็น {new_id}")
                            else: st.error("เลขบัญชีใหม่นี้มีคนใช้แล้ว")
                        else: st.error("ไม่พบเลขบัญชีเดิมในระบบ")
                else: st.error("กรุณากรอกข้อมูลให้ครบถ้วน")

    elif a_nav == "ธุรกรรมทั้งหมด":
        with db_transaction() as c:
            df_tx = pd.read_sql("SELECT * FROM Transactions ORDER BY date DESC", c.connection)
        st.dataframe(df_tx, use_container_width=True)

    if st.button("ออกจากระบบเจ้าหน้าที่"): 
        st.session_state.auth_page = "gateway"; st.rerun()

# --- SETUP PIN ---
elif st.session_state.auth_page == "setup_pin":
    st.subheader("🛡️ ตั้งรหัส PIN 6 หลักเพื่อความปลอดภัย")
    p1 = st.text_input("ตั้งรหัส PIN", type="password", max_chars=6)
    if st.button("บันทึกรหัส PIN"):
        if len(p1) == 6 and p1.isdigit():
            with db_transaction() as c:
                c.execute("UPDATE Users SET pin=? WHERE acc_id=?", (p1, st.session_state.user_acc))
            st.session_state.auth_page = "client_home"; st.rerun()
        else: st.error("รหัสต้องเป็นตัวเลข 6 หลัก")
