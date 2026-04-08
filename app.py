import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu
import random
import hashlib

# --- CONFIG ---
st.set_page_config(page_title="Borworn Bank", page_icon="🏦", layout="centered")

# --- DATABASE SETUP (ใช้ชื่อใหม่เพื่อป้องกันโครงสร้างเก่าพัง) ---
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

# --- CUSTOM UI (BANKING THEME) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    html, body, [class*="st-"] { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f4f7f6; }
    
    /* Bank Card Visual */
    .bank-card {
        background: linear-gradient(135deg, #0047ba 0%, #002d72 100%);
        color: white; padding: 30px; border-radius: 25px;
        box-shadow: 0 15px 35px rgba(0,71,186,0.2); margin-bottom: 25px;
    }
    
    /* Slip Style */
    .slip-container {
        background: white; border-top: 8px solid #0047ba;
        padding: 20px; border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Numeric Pad for PIN */
    .stButton>button { border-radius: 12px; font-weight: 500; }
    .num-btn>button { border-radius: 50% !important; width: 65px; height: 65px; background: white !important; color: #333 !important; border: 1px solid #eee !important; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "auth_status" not in st.session_state: st.session_state.auth_status = "login_page"
if "user_session" not in st.session_state: st.session_state.user_session = None
if "pin_input" not in st.session_state: st.session_state.pin_input = ""

# ---------------------------------------------------------
# 🛡️ SECURITY SYSTEM
# ---------------------------------------------------------

# 1. หน้า Login หลัก
if st.session_state.auth_status == "login_page":
    st.markdown("<h1 style='text-align:center; color:#0047ba;'>BORWORN BANK</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="background:white; padding:30px; border-radius:20px;">', unsafe_allow_html=True)
        user_in = st.text_input("ชื่อผู้ใช้งาน (Username)")
        pass_in = st.text_input("รหัสผ่าน (Password)", type="password")
        if st.button("เข้าสู่ระบบ", use_container_width=True):
            user = c.execute("SELECT * FROM Users WHERE username=? AND password=?", (user_in, pass_in)).fetchone()
            if user:
                st.session_state.user_session = user[0]
                st.session_state.auth_status = "pin_page" if user[5] else "set_pin_page"
                st.rerun()
            else: st.error("ข้อมูลไม่ถูกต้อง")
        st.markdown('</div>', unsafe_allow_html=True)

# 2. หน้าใส่ PIN (Numeric Pad)
elif st.session_state.auth_status == "pin_page":
    user_info = c.execute("SELECT name, pin FROM Users WHERE acc_id=?", (st.session_state.user_session,)).fetchone()
    st.markdown(f"<h3 style='text-align:center;'>สวัสดี, {user_info[0]}</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>กรุณาใส่รหัส PIN 6 หลัก</p>", unsafe_allow_html=True)
    
    # แสดงจุดรหัส
    display_dots = " ".join(["●" if i < len(st.session_state.pin_input) else "○" for i in range(6)])
    st.markdown(f"<h1 style='text-align:center; color:#0047ba;'>{display_dots}</h1>", unsafe_allow_html=True)
    
    # สร้างคีย์แพด
    col1, col2, col3 = st.columns([1,1,1])
    btns = ['1','2','3','4','5','6','7','8','9','ลบ','0','ล้าง']
    for i, b in enumerate(btns):
        target_col = [col1, col2, col3][i % 3]
        if target_col.button(b, key=f"pin_{b}", use_container_width=True):
            if b == 'ลบ': st.session_state.pin_input = st.session_state.pin_input[:-1]
            elif b == 'ล้าง': st.session_state.pin_input = ""
            elif len(st.session_state.pin_input) < 6: st.session_state.pin_input += b
            
            if len(st.session_state.pin_input) == 6:
                if st.session_state.pin_input == user_info[1]:
                    st.session_state.auth_status = "main_app"
                    st.rerun()
                else:
                    st.error("รหัส PIN ไม่ถูกต้อง")
                    st.session_state.pin_input = ""

# 3. หน้าตั้ง PIN ครั้งแรก
elif st.session_state.auth_status == "set_pin_page":
    st.subheader("🔢 ตั้งรหัส PIN 6 หลัก")
    st.info("ใช้สำหรับเข้าแอปในครั้งถัดไปโดยไม่ต้องใส่รหัสผ่าน")
    p1 = st.text_input("ตั้งรหัส PIN", type="password", max_chars=6)
    p2 = st.text_input("ยืนยันรหัส PIN", type="password", max_chars=6)
    if st.button("บันทึก PIN"):
        if len(p1) == 6 and p1 == p2 and p1.isdigit():
            c.execute("UPDATE Users SET pin=? WHERE acc_id=?", (p1, st.session_state.user_session))
            conn.commit()
            st.session_state.auth_status = "main_app"
            st.rerun()
        else: st.error("กรุณากรอกตัวเลข 6 หลักให้ตรงกัน")

# ---------------------------------------------------------
# 🏠 MAIN APP CONTENT
# ---------------------------------------------------------
elif st.session_state.auth_status == "main_app":
    # ดึงข้อมูลล่าสุด
    u_data = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.user_session,)).fetchone()
    
    menu = option_menu(None, ["หน้าหลัก", "โอนเงิน", "ประวัติ", "โปรไฟล์"], 
        icons=['house-fill', 'send-fill', 'clock-history', 'person-circle'], 
        orientation="horizontal", styles={"nav-link-selected": {"background-color": "#0047ba"}})

    if menu == "หน้าหลัก":
        st.markdown(f"""
        <div class="bank-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <p style="margin:0; font-weight:300;">เงินในบัญชี (ออมทรัพย์)</p>
                <img src="https://img.icons8.com/color/48/visa.png" width="40">
            </div>
            <h1 style="color:white; margin:15px 0;">฿ {u_data[4]:,.2f}</h1>
            <p style="margin:0; letter-spacing:2px;">{u_data[0]}</p>
            <p style="margin:0; font-size:14px; opacity:0.8;">{u_data[1]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📲 รับเงินด้วย QR Code"):
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={u_data[0]}")
            st.caption("ให้เพื่อนสแกนเพื่อโอนเงินเข้าบัญชีนี้")

    elif menu == "โอนเงิน":
        st.subheader("💸 โอนเงิน")
        to_acc = st.text_input("เลขบัญชีผู้รับ")
        amount = st.number_input("จำนวนเงิน (บาท)", min_value=1.0)
        memo = st.text_input("บันทึกช่วยจำ")
        
        if st.button("ยืนยันการโอนเงิน", type="primary", use_container_width=True):
            receiver = c.execute("SELECT name FROM Users WHERE acc_id=?", (to_acc,)).fetchone()
            if not receiver: st.error("ไม่พบเลขบัญชีผู้รับ")
            elif u_data[4] < amount: st.error("ยอดเงินไม่เพียงพอ")
            elif to_acc == u_data[0]: st.warning("ไม่สามารถโอนให้ตัวเองได้")
            else:
                ref = f"REF{random.randint(1000000, 9999999)}"
                # Process Transfer
                c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (amount, u_data[0]))
                c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amount, to_acc))
                c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?)", 
                          (u_data[0], to_acc, amount, datetime.now().strftime("%d/%b/%y %H:%M"), memo if memo else "โอนเงิน", ref))
                conn.commit()
                st.success("โอนเงินสำเร็จ!")
                # SLIP
                st.markdown(f"""
                <div class="slip-container">
                    <h4 style="text-align:center; color:#0047ba;">โอนเงินสำเร็จ</h4>
                    <p style="text-align:center; color:gray; font-size:12px;">{datetime.now().strftime('%d %b %Y %H:%M')}</p>
                    <hr>
                    <p><b>จาก:</b> {u_data[1]}</p>
                    <p><b>ไปที่:</b> {receiver[0]} ({to_acc})</p>
                    <h2 style="text-align:center;">฿ {amount:,.2f}</h2>
                    <p style="text-align:center; font-size:10px; color:gray;">เลขที่อ้างอิง: {ref}</p>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()

    elif menu == "ประวัติ":
        st.subheader("📜 รายการล่าสุด")
        hist = pd.read_sql(f"SELECT * FROM Transactions WHERE sender='{u_data[0]}' OR receiver='{u_data[0]}'", conn)
        for i, r in hist.sort_index(ascending=False).iterrows():
            is_out = r['sender'] == u_data[0]
            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:12px; margin-bottom:10px; border-left:5px solid {'#ff4d4d' if is_out else '#27ae60'}">
                <div style="display:flex; justify-content:space-between">
                    <b>{r['type']}</b>
                    <b style="color:{'#ff4d4d' if is_out else '#27ae60'}">{' -' if is_out else ' +'} ฿{r['amount']:,.2f}</b>
                </div>
                <small style="color:gray;">{r['date']} | Ref: {r['ref_no']}</small>
            </div>
            """, unsafe_allow_html=True)

    elif menu == "โปรไฟล์":
        st.subheader("⚙️ การตั้งค่า")
        if st.button("ออกจากระบบ", type="primary", use_container_width=True):
            st.session_state.auth_status = "login_page"
            st.rerun()
            
        st.divider()
        # --- ADMIN SECTION ---
        adm = st.text_input("เจ้าหน้าที่ (รหัสลับ)", type="password")
        if adm == "Kub1":
            st.info("🛠️ ระบบจัดการเจ้าหน้าที่")
            with st.form("add_user"):
                c1, c2 = st.columns(2)
                a_id = c1.text_input("เลขบัญชี")
                a_nm = c2.text_input("ชื่อลูกค้า")
                a_us = c1.text_input("Username")
                a_pw = c2.text_input("Password")
                a_ba = st.number_input("เงินฝาก", value=1000.0)
                if st.form_submit_button("สร้างบัญชี"):
                    c.execute("INSERT INTO Users (acc_id, name, username, password, balance) VALUES (?,?,?,?,?)",
                              (a_id, a_nm, a_us, a_pw, a_ba))
                    conn.commit()
                    st.success("สร้างสำเร็จ!")
