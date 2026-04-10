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
    st.error("⚠️ กรุณาตั้งค่า Secrets ใน Streamlit Cloud (SUPABASE_URL และ SUPABASE_KEY)")
    st.stop()

# --- CONFIG ---
st.set_page_config(page_title="สุริยพาณิชย์ - SURIYA PANICH", page_icon="☀️", layout="centered")

# --- LUXURY CSS (ธีมน้ำเงิน-ทอง สไตล์สุริยวงศ์) ---
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
    
    .stTextInput>div>div>input { background-color: #1e293b !important; color: white !important; border: 1px solid #334155 !important; }
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
                res = supabase.table("users").select("*").eq("username", u_in).eq("password", p_in).execute()
                if res.data:
                    user_data = res.data[0]
                    if user_data['status'] == 'Banned': st.error("บัญชีถูกอายัด")
                    else:
                        st.session_state.user = user_data
                        st.session_state.page = "main"; st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")

# --- 🏦 MAIN APP (SIDEBAR MENU) ---
elif st.session_state.page == "main":
    # Refresh User Data จาก Supabase
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

    # --- CONTENT AREA ---
    if menu == "หน้าหลัก":
        st.markdown(f'''<div class="main-header">
            <small>ยอดเงินที่ใช้ได้ในสุริยวงศ์</small>
            <p class="balance-text">฿ {u['balance']:,.2f}</p>
            <p>เลขบัญชี: {u['acc_id']}</p>
        </div>''', unsafe_allow_html=True)
        
        st.write("🕒 **ธุรกรรมล่าสุดของคุณ**")
        tx_res = supabase.table("transactions").select("*").or_(f"sender_id.eq.{u['acc_id']},receiver_id.eq.{u['acc_id']}").order("id", desc=True).limit(5).execute()
        
        if not tx_res.data: st.caption("ยังไม่มีรายการเดินบัญชี")
        else:
            df_tx = pd.DataFrame(tx_res.data)[['sender_id', 'receiver_id', 'amount', 'timestamp']]
            st.dataframe(df_tx, use_container_width=True)

    elif menu == "รับเงิน":
        st.subheader("QR Code สำหรับรับเงิน")
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={u['acc_id']}&color=020617&bgcolor=ffffff"
        st.image(qr, use_container_width=True)
        st.info(f"เลขบัญชี: {u['acc_id']}")

    elif menu == "โอนเงิน":
        st.subheader("โอนเงินผ่านระบบ")
        with st.form("t_form"):
            target = st.text_input("ระบุเลขบัญชีปลายทาง")
            amt = st.number_input("จำนวนเงิน (฿)", min_value=0.01)
            if st.form_submit_button("ตกลงโอนเงิน"):
                recv_res = supabase.table("users").select("*").eq("acc_id", target).execute()
                if not recv_res.data: st.error("ไม่พบเลขบัญชีปลายทาง")
                elif u['balance'] < amt: st.error("เงินในบัญชีไม่พอ")
                else:
                    # ประมวลผล
                    supabase.table("users").update({"balance": u['balance'] - amt}).eq("acc_id", u['acc_id']).execute()
                    supabase.table("users").update({"balance": recv_res.data[0]['balance'] + amt}).eq("acc_id", target).execute()
                    supabase.table("transactions").insert({
                        "sender_id": u['acc_id'], "receiver_id": target, "amount": amt, 
                        "timestamp": datetime.now().strftime("%H:%M")
                    }).execute()
                    st.success(f"โอนสำเร็จไปยัง {recv_res.data[0]['name']}"); time.sleep(1); st.rerun()

    elif menu == "บัญชี":
        st.subheader("ข้อมูลบัญชีผู้ใช้งาน")
        st.markdown(f'''<div style="background:rgba(255,255,255,0.05); padding:20px; border-radius:15px;">
            <b>ชื่อ:</b> {u['name']} <br>
            <b>เลขบัญชี:</b> {u['acc_id']} <br>
            <b>สถานะ:</b> {u['status']}
        </div>''', unsafe_allow_html=True)
        
        new_n = st.text_input("เปลี่ยนชื่อ-นามสกุล", value=u['name'])
        if st.button("บันทึกชื่อใหม่"):
            supabase.table("users").update({"name": new_n}).eq("acc_id", u['acc_id']).execute()
            st.success("เปลี่ยนชื่อสำเร็จ"); st.rerun()

        # --- 👑 ADMIN SECTION ---
        if u['role'] == 'Admin':
            st.divider()
            st.subheader("👑 ระบบควบคุมแอดมินสุริยพาณิชย์")
            opt = st.selectbox("เลือกฟังก์ชัน", ["1. สร้างบัญชีใหม่", "2. อายัด/ปลดอายัด", "3. ข้อมูลผู้ใช้ทั้งหมด", "4. ข้อมูลธุรกรรมทั้งหมด", "5. เปลี่ยนเลขบัญชี", "6. จัดการเงิน (เสกเงิน/ลดเงิน)", "7. มอบสิทธิ์ Admin"])
            
            if opt == "1. สร้างบัญชีใหม่":
                with st.form("a1"):
                    un = st.text_input("Username")
                    pw = st.text_input("Password")
                    nm = st.text_input("ชื่อจริง")
                    if st.form_submit_button("สร้างบัญชี (สุ่มเลข)"):
                        new_id = str(random.randint(1000000000, 9999999999))
                        supabase.table("users").insert({
                            "acc_id": new_id, "username": un, "name": nm, "password": pw, 
                            "balance": 0.0, "status": "Active", "role": "User", 
                            "created_at": datetime.now().strftime("%H:%M")
                        }).execute()
                        st.success(f"สร้างสำเร็จ! เลขบัญชี: {new_id}")

            elif opt == "2. อายัด/ปลดอายัด":
                tid = st.text_input("เลขบัญชีที่ต้องการจัดการ")
                ca, cb = st.columns(2)
                if ca.button("🔴 อายัด"):
                    supabase.table("users").update({"status": "Banned"}).eq("acc_id", tid).execute()
                    st.warning("อายัดแล้ว")
                if cb.button("🟢 ปลด"):
                    supabase.table("users").update({"status": "Active"}).eq("acc_id", tid).execute()
                    st.success("ปลดแล้ว")

            elif opt == "3. ข้อมูลผู้ใช้ทั้งหมด":
                all_u = supabase.table("users").select("*").execute()
                st.dataframe(pd.DataFrame(all_u.data), use_container_width=True)

            elif opt == "4. ข้อมูลธุรกรรมทั้งหมด":
                all_t = supabase.table("transactions").select("*").execute()
                st.dataframe(pd.DataFrame(all_t.data), use_container_width=True)

            elif opt == "5. เปลี่ยนเลขบัญชี":
                oid = st.text_input("เลขเดิม")
                nid = st.text_input("เลขใหม่")
                if st.button("เปลี่ยนเลข"):
                    supabase.table("users").update({"acc_id": nid}).eq("acc_id", oid).execute()
                    st.success("เปลี่ยนเลขสำเร็จ")

            elif opt == "6. จัดการเงิน (เสกเงิน/ลดเงิน)":
                sid = st.text_input("เลขบัญชีลูกค้า")
                samt = st.number_input("จำนวนเงินจัดการ", min_value=0.01)
                col_a, col_b = st.columns(2)
                
                if col_a.button("✨ เสกเงิน"):
                    target_u = supabase.table("users").select("balance").eq("acc_id", sid).execute()
                    if target_u.data:
                        new_bal = target_u.data[0]['balance'] + samt
                        supabase.table("users").update({"balance": new_bal}).eq("acc_id", sid).execute()
                        st.success("เสกเงินสำเร็จ!"); time.sleep(1); st.rerun()

                if col_b.button("📉 ลดเงิน"):
                    target_u = supabase.table("users").select("balance").eq("acc_id", sid).execute()
                    if target_u.data:
                        new_bal = max(0, target_u.data[0]['balance'] - samt)
                        supabase.table("users").update({"balance": new_bal}).eq("acc_id", sid).execute()
                        st.warning("ลดเงินสำเร็จ!"); time.sleep(1); st.rerun()

            elif opt == "7. มอบสิทธิ์ Admin":
                mid = st.text_input("เลขบัญชีที่จะให้สิทธิ์")
                if st.button("Grant Admin Role"):
                    supabase.table("users").update({"role": "Admin"}).eq("acc_id", mid).execute()
                    st.success("มอบสิทธิ์สำเร็จ")
