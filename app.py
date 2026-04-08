import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu
import random
import time
import os

# --- CONFIG ---
st.set_page_config(page_title="Borworn Private Banking", page_icon="🏛️", layout="centered")

# --- DATABASE SETUP ---
conn = sqlite3.connect('borworn_master_v4.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS Users 
                 (acc_id TEXT PRIMARY KEY, username TEXT, name TEXT, password TEXT, 
                  balance REAL, pin TEXT, status TEXT DEFAULT 'Active')''')
    c.execute('''CREATE TABLE IF NOT EXISTS Transactions 
                 (sender_id TEXT, receiver_id TEXT, amount REAL, date TEXT, type TEXT, ref_no TEXT)''')
    conn.commit()

init_db()

# --- CSS: LUXURY UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;400;500&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #fcfcfc; }
    .bank-card {
        background: linear-gradient(135deg, #020617 0%, #1e1b4b 100%);
        color: #f8fafc; padding: 30px; border-radius: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(234, 179, 8, 0.3);
    }
    .pin-box button {
        border-radius: 50% !important; width: 80px !important; height: 80px !important;
        font-size: 26px !important; background: #ffffff !important; color: #1e1b4b !important;
        border: 1px solid #e2e8f0 !important; margin: 10px auto !important;
    }
</style>
""", unsafe_allow_html=True)

# --- PERSISTENT LOGIN LOGIC (แก้ปัญหารีเฟรชแล้วหลุด) ---
# ใช้รหัสประจำตัวชั่วคราวเพื่อจำลองการจำ User ค้างไว้ใน Session
if "page" not in st.session_state: 
    st.session_state.page = "login"
if "current_acc" not in st.session_state: 
    st.session_state.current_acc = None
if "pin_input" not in st.session_state: 
    st.session_state.pin_input = ""
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False

# ---------------------------------------------------------
# 🏛️ GATEWAY
# ---------------------------------------------------------
if not st.session_state.is_authenticated:
    if st.session_state.page == "login":
        st.markdown("<h1 style='text-align:center; color:#1e1b4b;'>🏛️ BORWORN</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#64748b; letter-spacing:2px;'>PRIVATE BANKING</p>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["Client Access", "Staff Only"])
        
        with t1:
            with st.form("login_form"):
                usr = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                    user = c.execute("SELECT acc_id, pin FROM Users WHERE username=? AND password=?", (usr, pwd)).fetchone()
                    if user:
                        st.session_state.current_acc = user[0]
                        st.session_state.page = "pin_verify" if user[1] else "setup_pin"
                        st.rerun()
                    else: st.error("ข้อมูลไม่ถูกต้อง")
        
        with t2:
            if st.text_input("Staff Key", type="password") == "Kub1":
                st.info("เปิดบัญชีใหม่ได้ที่นี่")
                with st.form("admin_reg"):
                    new_id = "".join([str(random.randint(0, 9)) for _ in range(10)])
                    n_u = st.text_input("Username")
                    n_n = st.text_input("ชื่อลูกค้า")
                    n_p = st.text_input("Password")
                    n_b = st.number_input("เงินเริ่มต้น", value=1000.0)
                    if st.form_submit_button("บันทึกข้อมูล"):
                        c.execute("INSERT INTO Users (acc_id, username, name, password, balance) VALUES (?,?,?,?,?)", (new_id, n_u, n_n, n_p, n_b))
                        conn.commit(); st.success(f"สร้างสำเร็จ! เลขบัญชี: {new_id}")

    elif st.session_state.page == "pin_verify":
        u_data = c.execute("SELECT name, pin FROM Users WHERE acc_id=?", (st.session_state.current_acc,)).fetchone()
        st.markdown(f"<h3 style='text-align:center;'>Welcome, {u_data[0]}</h3>", unsafe_allow_html=True)
        
        stars = " ".join(["●" if i < len(st.session_state.pin_input) else "○" for i in range(6)])
        st.markdown(f"<h1 style='text-align:center; color:#1e1b4b; letter-spacing:8px;'>{stars}</h1>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        nums = ['1','2','3','4','5','6','7','8','9','C','0','Del']
        for i, n in enumerate(nums):
            with [col1, col2, col3][i % 3]:
                st.markdown('<div class="pin-box">', unsafe_allow_html=True)
                if st.button(n, key=f"p_{n}"):
                    if n == 'Del': st.session_state.pin_input = st.session_state.pin_input[:-1]
                    elif n == 'C': st.session_state.pin_input = ""
                    elif len(st.session_state.pin_input) < 6: st.session_state.pin_input += n
                    
                    if len(st.session_state.pin_input) == 6:
                        if st.session_state.pin_input == u_data[1]:
                            st.session_state.is_authenticated = True
                            st.session_state.page = "main"
                            st.rerun()
                        else:
                            st.error("PIN ผิดพลาด")
                            st.session_state.pin_input = ""
                st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.page == "setup_pin":
        st.subheader("🛡️ ตั้งรหัส PIN 6 หลักของคุณ")
        p1 = st.text_input("กำหนด PIN", type="password", max_chars=6)
        p2 = st.text_input("ยืนยัน PIN", type="password", max_chars=6)
        if st.button("บันทึกและเข้าใช้งาน"):
            if len(p1) == 6 and p1 == p2:
                c.execute("UPDATE Users SET pin=? WHERE acc_id=?", (p1, st.session_state.current_acc))
                conn.commit()
                st.session_state.is_authenticated = True
                st.session_state.page = "main"
                st.rerun()

# ---------------------------------------------------------
# 🏠 MAIN DASHBOARD (เมื่อล็อกอินสำเร็จแล้ว)
# ---------------------------------------------------------
else:
    u = c.execute("SELECT * FROM Users WHERE acc_id=?", (st.session_state.current_acc,)).fetchone()
    
    menu = option_menu(None, ["หน้าหลัก", "โอนเงิน", "ประวัติ", "ออกจากระบบ"], 
        icons=['grid-fill', 'send', 'clock', 'door-open'], 
        orientation="horizontal", styles={"nav-link-selected": {"background-color": "#1e1b4b"}})

    if menu == "หน้าหลัก":
        st.markdown(f"""
        <div class="bank-card">
            <small style="opacity:0.6;">Wealth Balance</small>
            <h1 style="color:white; margin:5px 0; font-size:35px;">฿ {u[4]:,.2f}</h1>
            <div style="margin-top:20px; border-top:1px solid rgba(255,255,255,0.1); padding-top:15px; display:flex; justify-content:space-between; font-size:14px;">
                <span>{u[2]}</span>
                <span style="font-family:monospace;">{u[0]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={u[0]}", width=200)

    elif menu == "โอนเงิน":
        target = st.text_input("เลขบัญชีผู้รับ")
        amt = st.number_input("จำนวนเงิน (บาท)", min_value=1.0)
        if st.button("ยืนยันการโอน", type="primary", use_container_width=True):
            recv = c.execute("SELECT name FROM Users WHERE acc_id=?", (target,)).fetchone()
            if recv and u[4] >= amt and target != u[0]:
                c.execute("UPDATE Users SET balance = balance - ? WHERE acc_id=?", (amt, u[0]))
                c.execute("UPDATE Users SET balance = balance + ? WHERE acc_id=?", (amt, target))
                c.execute("INSERT INTO Transactions VALUES (?,?,?,?,?,?)", (u[0], target, amt, datetime.now().strftime("%H:%M | %d/%m/%y"), "Transfer", f"REF{random.randint(1000,9999)}"))
                conn.commit(); st.success("โอนสำเร็จ!"); st.balloons()
            else: st.error("ข้อมูลผิดพลาดหรือเงินไม่พอ")

    elif menu == "ประวัติ":
        df = pd.read_sql(f"SELECT * FROM Transactions WHERE sender_id='{u[0]}' OR receiver_id='{u[0]}'", conn)
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    elif menu == "ออกจากระบบ":
        st.session_state.is_authenticated = False
        st.session_state.page = "login"
        st.session_state.current_acc = None
        st.rerun()
