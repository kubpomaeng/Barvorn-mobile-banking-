import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- การจัดการฐานข้อมูล ---
DB_FILE = 'imaginary_bank_v3.json'

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: return json.load(f)
    return {"users": {}, "transactions": [], "next_id": 1}

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- ปรับแต่ง UI ให้เหมือนแอปมือถือ ---
st.set_page_config(page_title="ImagineBank Pro", page_icon="🏦", layout="centered")

st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .bank-card {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white; padding: 25px; border-radius: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3); margin-bottom: 25px;
    }
    .stRadio > div {
        flex-direction: row; justify-content: space-around;
        background: white; padding: 10px; border-radius: 50px;
        position: fixed; bottom: 20px; z-index: 100; width: 100%; max-width: 400px;
    }
    .slip {
        background: white; border: 1px solid #eee; padding: 20px;
        border-radius: 15px; text-align: center; color: #333;
        border-top: 10px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

data = load_data()

if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# --- หน้า Login / Register ---
if st.session_state.user_id is None:
    st.title("🏦 Imagine National Bank")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        u_id = st.text_input("เลขบัญชี (เช่น 0001)")
        u_pass = st.text_input("รหัสผ่าน", type="password", key="l_pass")
        if st.button("เข้าสู่ระบบ"):
            if u_id in data["users"] and data["users"][u_id]['password'] == u_pass:
                st.session_state.user_id = u_id
                st.rerun()
            else:
                st.error("เลขบัญชีหรือรหัสผ่านไม่ถูกต้อง")
                
    with tab2:
        new_name = st.text_input("ชื่อ-นามสกุล")
        new_user = st.text_input("ชื่อผู้ใช้ (Username)")
        new_pass = st.text_input("ตั้งรหัสผ่าน", type="password", key="r_pass")
        if st.button("ลงทะเบียน"):
            if new_name and new_pass:
                acc_id = str(data["next_id"]).zfill(4)
                data["users"][acc_id] = {
                    "name": new_name, "username": new_user,
                    "password": new_pass, "balance": 1000.0
                }
                data["next_id"] += 1
                save_data(data)
                st.success(f"ลงทะเบียนสำเร็จ! เลขบัญชีคือ {acc_id}")

# --- หน้าหลักแอป ---
else:
    uid = st.session_state.user_id
    user = data["users"][uid]
    st.markdown(f"**สวัสดี, {user['name']}**")
    
    menu = st.radio("", ["🏠 หน้าหลัก", "💸 โอนเงิน", "📜 ประวัติ", "⚙️ ออกจากระบบ"], label_visibility="collapsed")

    if menu == "🏠 หน้าหลัก":
        st.markdown(f"""
        <div class="bank-card">
            <p style="font-size: 0.8em; opacity: 0.8;">ยอดเงินคงเหลือ</p>
            <h1 style="letter-spacing: 2px;">฿ {user['balance']:,}</h1>
            <br><br>
            <p style="margin:0; font-family: monospace;">**** **** **** {uid}</p>
            <p style="margin:0; font-size: 0.9em;">{user['name'].upper()}</p>
        </div>
        """, unsafe_allow_html=True)

    elif menu == "💸 โอนเงิน":
        st.subheader("โอนเงิน")
        target = st.text_input("เลขบัญชีผู้รับ (4 หลัก)")
        amount = st.number_input("จำนวนเงิน", min_value=1.0)
        if st.button("ยืนยันการโอน"):
            if target in data["users"] and target != uid:
                if user['balance'] >= amount:
                    data["users"][uid]['balance'] -= amount
                    data["users"][target]['balance'] += amount
                    now = datetime.now().strftime("%d %b %Y - %H:%M")
                    data["transactions"].append({
                        "from": uid, "from_name": user['name'],
                        "to": target, "to_name": data["users"][target]['name'],
                        "amount": amount, "date": now
                    })
                    save_data(data)
                    st.balloons()
                    st.markdown(f"""
                    <div class="slip">
                        <p style="color: #4CAF50; font-weight: bold;">โอนเงินสำเร็จ</p>
                        <h2 style="margin: 0;">฿ {amount:,}</h2>
                        <hr>
                        <p style="text-align: left;">จาก: {user['name']}</p>
                        <p style="text-align: left;">ไปที่: {data['users'][target]['name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("เงินไม่พอ")
            else:
                st.error("ไม่พบเลขบัญชี")

    elif menu == "📜 ประวัติ":
        st.subheader("รายการล่าสุด")
        my_history = [t for t in data["transactions"] if t['from'] == uid or t['to'] == uid]
        for t in reversed(my_history):
            is_out = t['from'] == uid
            color = "#ff4b4b" if is_out else "#00c853"
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #eee;">
                <div>{'โอนไป' if is_out else 'รับจาก'} {t['to_name'] if is_out else t['from_name']}<br><small>{t['date']}</small></div>
                <div style="color: {color}; font-weight: bold;">{'-' if is_out else '+'} {t['amount']:,}</div>
            </div>
            """, unsafe_allow_html=True)

    elif menu == "⚙️ ออกจากระบบ":
        st.session_state.user_id = None
        st.rerun()
