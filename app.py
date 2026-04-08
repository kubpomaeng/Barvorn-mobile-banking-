import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu
import random

# --- CONFIG ---
st.set_page_config(page_title="Borworn Bank", page_icon="🏦", layout="centered")

# --- DATABASE SETUP ---
conn = sqlite3.connect('borworn_bank_final_v1.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS Users 
                 (acc_id TEXT PRIMARY KEY, name TEXT, username TEXT, password TEXT, 
                  balance REAL, pin TEXT, branch TEXT DEFAULT 'สำนักงานใหญ่')''')
    c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                 (sender TEXT, receiver TEXT, amount REAL, date TEXT, type TEXT, ref_no TEXT)''')
    conn.commit()

init_db()

# --- CUSTOM UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    html, body, [class*="st-"] { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f4f7f6; }
    .bank-card {
        background: linear-gradient(135deg, #0047ba 0%, #002d72 100%);
        color: white; padding: 25px; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,71,186,0.2); margin-bottom: 20px;
    }
    .slip-container {
        background: white; border-top: 8px solid #0047ba;
        padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "auth_status" not in st.session_state: st.session_state.auth_status = "login_page"
if "user_session" not in st.session_state: st.session_state.user_session = None
if "pin_input" not in st.session_state: st.session_state.pin_input = ""

# ---------------------------------------------------------
# 🛡️ SECURITY SYSTEM (หน้า Login & Admin ลับ)
# ---------------------------------------------------------

if st.session_state.auth_status == "login_page":
    st.markdown("<h1 style='text-align:center; color:#0047ba;'>BORWORN BANK</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 เข้าสู่ระบบ", "⚙️ สำหรับเจ้าหน้าที่"])
    
    with tab1:
        st.markdown('<div style="background:white; padding:20px; border-radius:15px;">', unsafe_allow_html=True)
        u_in = st.text_input("ชื่อผู้ใช้งาน")
        p_in = st.text_input("รหัสผ่าน", type="password")
        if st.button("ตกลง", use_container_width=True, type="primary"):
            user = c.execute("SELECT * FROM Users WHERE username=? AND password=?", (u_in, p_in)).fetchone()
            if user:
                st.session_state.user_session = user[0]
                st.session_state.auth_status = "pin_page" if user[5] else "set_pin_page"
                st.rerun()
            else: st.error("ไม่พบข้อมูลผู้ใช้งาน")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.caption("เฉพาะเจ้าหน้าที่ธนาคารเท่านั้น")
        adm_code = st.text_input("กรอกรหัสพนักงาน", type="password", key="staff_key")
        if adm_code == "Kub1":
            st.success("เข้าสู่โหมดจัดการระบบ")
            with st.expander("➕ เพิ่มบัญชีลูกค้าใหม่", expanded=True):
                new_id = st.text_input("เลขบัญชี (เช่น 123-456)")
                new_nm = st.text_input("ชื่อ-นามสกุล")
                new_us = st.text_input("ตั้ง Username")
                new_pw = st.text_input("ตั้ง Password")
                new_bl = st.number_input("เงินฝากเริ่มต้น", value=500.0)
                if st.button("ยืนยันการสร้างบัญชี"):
                    try:
                        c.execute("INSERT INTO Users (acc_id, name, username, password, balance) VALUES (?,?,?,?,?)",
                                  (new_id, new_nm, new_us, new_pw, new_bl))
                        conn.commit()
                        st.success(f"สร้างบัญชี {new_nm} สำเร็จ! ไปที่หน้า Login ได้เลย")
                    except: st.error("เลขบัญชีนี้มีอยู่ในระบบแล้ว")

# ---------------------------------------------------------
# 🔢 หน้าใส่ PIN (Numeric Keypad)
# ---------------------------------------------------------
elif st.session_state.auth_status == "pin_page":
    user_info = c.execute("SELECT name, pin FROM Users WHERE acc_id=?", (st.session_state.user_session,)).fetchone()
    st.markdown(f"<h3 style='text-align:center;'>สวัสดี, {user_info[0]}</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>กรุณาใส่รหัส PIN 6 หลัก</p>", unsafe_allow_html=True)
    
    display_dots = " ".join(["●" if i < len(st.session_state.pin_input) else "○" for i in range(6)])
    st.markdown(f"<h1 style='text-align:center; color:#0047ba;'>{display_dots}</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    btns = ['1','2','3','4','5','6','7','8','9','ลบ','0','ล้าง']
    for i, b in enumerate(btns):
        with [col1, col2, col3][i % 3]:
            if st.button(b, key=f"p_{b}", use_container_width=True):
                if b == 'ลบ': st.session_state.pin_input = st.session_state.pin_input[:-1]
                elif b == 'ล้าง': st.session_state.pin_input = ""
                elif len(st.session_state.pin_input) < 6: st.session_state.pin_input += b
                
                if len(st.session_state.pin_input) == 6:
                    if st.session_state.pin_input == user_info[1]:
                        st.session_state.auth_status = "main_app"
                        st.rerun()
                    else:
                        st.error("PIN ผิด")
                        st.session_state.pin_input = ""

# ---------------------------------------------------------
# 🏠 หน้าตั้ง PIN ครั้งแรก
# ---------------------------------------------------------
elif st.session_state.auth_status == "set_pin_page":
    st.subheader("🔢 ตั้งรหัส PIN 6 หลัก")
    p1 = st.text_input("ตั้ง PIN", type="password", max_chars=6)
    p2 = st.text_input("ยืนยัน PIN", type="password", max_chars=6)
    if st.button("ตกลง"):
        if len(p1) == 6 and p1 == p2:
            c.execute("UPDATE Users SET pin=? WHERE acc_id=?", (p1, st.session_state.user_session))
            conn.commit()
            st.session_state.auth_status = "main_app"
            st.rerun()

# ---------------------------------------------------------
# 🏦 MAIN APP
# ---------------------------------------------------------
elif st.session_state.auth_status == "main_app":
    u_data = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.user_session,)).fetchone()
    
    menu = option_menu(None, ["หน้าหลัก", "โอนเงิน", "ประวัติ", "โปรไฟล์"], 
        icons=['house-fill', 'send-fill', 'clock-history', 'person-circle'], 
        orientation="horizontal", styles={"nav-link-selected": {"background-color": "#0047ba"}})

    if menu == "หน้าหลัก":
        st.markdown(f"""
        <div class="bank-card">
            <p style="margin:0; font-size:14px; opacity:0.8;">ยอดเงินในบัญชี</p>
            <h1 style="color:white; margin:10px 0;">฿ {u_data[4]:,.2f}</h1>
            <p style="margin:0;">{u_data[0]} | {u_data[1]}</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("📲 สแกน QR รับเงิน")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={u_data[0]}")

    elif menu == "โอนเงิน":
        to_acc = st.text_input("เลขบัญชีผู้รับ")
        amt = st.number_input("จำนวนเงิน", min_value=1.0)
        if st.button("โอนเงิน", type="primary", use_container_width=True):
            recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (to_acc,)).fetchone()
            if recv and u_data[4] >= amt:
                ref = f"REF{random.randint(1000,9999)}"
                c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (amt, u_data[0]))
                c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amt, to_acc))
                c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?)", (u_data[0], to_acc, amt, datetime.now().strftime("%d/%m/%y %H:%M"), "โอนเงิน", ref))
                conn.commit()
                st.success("สำเร็จ!")
                st.markdown(f'<div class="slip-container"><b>โอนเงินสำเร็จ</b><br>ไปที่: {recv[0]}<br>จำนวน: ฿{amt:,.2f}<br><small>Ref: {ref}</small></div>', unsafe_allow_html=True)
            else: st.error("ตรวจสอบข้อมูลอีกครั้ง")

    elif menu == "ประวัติ":
        df = pd.read_sql(f"SELECT * FROM Transactions WHERE sender='{u_data[0]}' OR receiver='{u_data[0]}'", conn)
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    elif menu == "โปรไฟล์":
        if st.button("ออกจากระบบ"):
            st.session_state.auth_status = "login_page"
            st.rerun()
