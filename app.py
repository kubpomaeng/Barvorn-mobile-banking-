import streamlit as st
import pandas as pd
from datetime import datetime
import random
import time
from supabase import create_client, Client

# --- 🔗 SUPABASE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("⚠️ กรุณาตั้งค่า Secrets ใน Streamlit Cloud ก่อนใช้งาน")
    st.stop()

# --- CONFIG ---
st.set_page_config(page_title="สุริยพาณิชย์ - SURIYA PANICH", page_icon="☀️", layout="centered")

# --- LUXURY CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;300;400;500;600&display=swap');
    html, body, [class*="st-"] { font-family: 'Kanit', sans-serif; color: white !important; }
    .stApp { background: #020617; }
    
    .main-header {
        background: linear-gradient(90deg, #1e293b, #0f172a);
        padding: 20px; border-radius: 15px; border-left: 5px solid #f59e0b;
        margin-bottom: 20px;
    }
    .balance-text { color: #f59e0b; font-size: 32px; font-weight: 600; margin: 0; }
    
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #f59e0b; }
    
    .stButton>button { width: 100%; border-radius: 10px; border: 1px solid #f59e0b !important; background: transparent; color: white; transition: 0.3s; }
    .stButton>button:hover { background: #f59e0b !important; color: #020617 !important; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "login"

# --- 🔐 LOGIN ---
if st.session_state.page == "login":
    st.markdown('<div style="text-align:center; padding:50px 0;"><h1>☀️ สุริยพาณิชย์</h1><p>SURIYA PANICH PRIVATE BANKING</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            u_in = st.text_input("Username")
            p_in = st.text_input("Password", type="password")
            if st.form_submit_button("เข้าสู่ระบบ"):
                # แก้เป็น users (ตัวเล็ก)
                res = supabase.table("users").select("*").eq("username", u_in).eq("password", p_in).execute()
                if res.data:
                    user = res.data[0]
                    if user['status'] == 'Banned': st.error("บัญชีถูกอายัด")
                    else:
                        st.session_state.user = user
                        st.session_state.page = "main"; st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")

# --- 🏦 MAIN APP ---
elif st.session_state.page == "main":
    # Refresh User Data - แก้เป็น users (ตัวเล็ก)
    u_res = supabase.table("users").select("*").eq("acc_id", st.session_state.user['acc_id']).execute()
    u = u_res.data[0]

    with st.sidebar:
        st.markdown(f"### ☀️ {u['name']}")
        st.caption(f"ตำแหน่ง: {u['role']}")
        st.divider()
        menu = st.radio("เมนูการใช้งาน", ["หน้าหลัก", "รับเงิน", "โอนเงิน", "บัญชี"])
        st.divider()
        if st.button("🚪 ออกจากระบบ"):
            st.session_state.page = "login"; st.rerun()

    if menu == "หน้าหลัก":
        st.markdown(f'''<div class="main-header">
            <small>ยอดเงินที่ใช้ได้ในสุริยวงศ์</small>
            <p class="balance-text">฿ {u['balance']:,.2f}</p>
            <p>เลขบัญชี: {u['acc_id']}</p>
        </div>''', unsafe_allow_html=True)
        
        st.write("🕒 **ธุรกรรมล่าสุด**")
        # แก้เป็น transactions (ตัวเล็ก)
        tx_res = supabase.table("transactions").select("*").or_(f"sender_id.eq.{u['acc_id']},receiver_id.eq.{u['acc_id']}").order("id", desc=True).limit(5).execute()
        if not tx_res.data: st.caption("ยังไม่มีรายการเดินบัญชี")
        else:
            df = pd.DataFrame(tx_res.data)[['sender_id', 'receiver_id', 'amount', 'timestamp']]
            st.dataframe(df, use_container_width=True)

    elif menu == "รับเงิน":
        st.subheader("QR Code รับเงิน")
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={u['acc_id']}&color=020617&bgcolor=ffffff"
        st.image(qr, use_container_width=True)
        st.info(f"เลขบัญชี: {u['acc_id']}")

    elif menu == "โอนเงิน":
        st.subheader("โอนเงินผ่านระบบ")
        with st.form("t_form"):
            target = st.text_input("เลขบัญชีปลายทาง")
            amt = st.number_input("จำนวนเงิน (฿)", min_value=0.01)
            if st.form_submit_button("ตกลงโอนเงิน"):
                # แก้เป็น users (ตัวเล็ก)
                recv_res = supabase.table("users").select("*").eq("acc_id", target).execute()
                if not recv_res.data: st.error("ไม่พบเลขบัญชี")
                elif u['balance'] < amt: st.error("เงินไม่พอ")
                else:
                    supabase.table("users").update({"balance": u['balance'] - amt}).eq("acc_id", u['acc_id']).execute()
                    supabase.table("users").update({"balance": recv_res.data[0]['balance'] + amt}).eq("acc_id", target).execute()
                    # แก้เป็น transactions (ตัวเล็ก)
                    supabase.table("transactions").insert({"sender_id": u['acc_id'], "receiver_id": target, "amount": amt, "timestamp": datetime.now().strftime("%H:%M")}).execute()
                    st.success(f"โอนสำเร็จไปยัง {recv_res.data[0]['name']}"); time.sleep(1); st.rerun()

    elif menu == "บัญชี":
        st.subheader("ข้อมูลบัญชี")
        st.info(f"ชื่อ: {u['name']}\n\nเลขบัญชี: {u['acc_id']}\n\nสถานะ: {u['status']}")
        
        if u['role'] == 'Admin':
            st.divider()
            st.subheader("👑 ศูนย์ควบคุมสุริยพาณิชย์")
            opt = st.selectbox("เลือกฟังก์ชัน", ["สร้างบัญชีใหม่", "จัดการเงิน (เสกเงิน/ลดเงิน)", "ตรวจสอบสมาชิก"])
            
            if opt == "สร้างบัญชีใหม่":
                with st.form("a1"):
                    un, pw, nm = st.text_input("Username"), st.text_input("Password"), st.text_input("ชื่อจริง")
                    if st.form_submit_button("สร้างบัญชี"):
                        new_id = str(random.randint(1000000000, 9999999999))
                        # แก้เป็น users (ตัวเล็ก)
                        supabase.table("users").insert({"acc_id": new_id, "username": un, "password": pw, "name": nm, "balance": 0.0, "status": "Active", "role": "User", "created_at": datetime.now().strftime("%d/%m/%Y")}).execute()
                        st.success(f"สร้างสำเร็จ! เลขบัญชี: {new_id}")

            elif opt == "จัดการเงิน (เสกเงิน/ลดเงิน)":
                sid = st.text_input("เลขบัญชีลูกค้า")
                samt = st.number_input("จำนวนเงิน (฿)", min_value=0.0)
                col1, col2 = st.columns(2)
                
                if col1.button("✨ เพิ่มเงิน (เสกเงิน)"):
                    target_u = supabase.table("users").select("balance").eq("acc_id", sid).execute()
                    if target_u.data:
