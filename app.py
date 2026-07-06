import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="NR Bunker Monitor", page_icon="🚢", layout="wide")

# --- INISIALISASI DATABASE (CSV) ---
if not os.path.exists("logs.csv"):
    pd.DataFrame(columns=["ID", "Tanggal", "Kapal", "Aktivitas", "RH_ME", "RH_AE", "BBM", "ROB"]).to_csv("logs.csv", index=False)

if not os.path.exists("master.csv"):
    master_data = {
        "Kode": [0, 1, 2, 3, 4, 5, 6],
        "Aktivitas": ["Standby ME", "Standby", "Manouver", "Service", "Sailing", "Bunker", "Sailing dan Manouver"],
        "Remarks": ["Warming Up ME", "No Activities", "Assist Berthing/Unberthing", "Berthing di Lampung", "From NR1 to PGN MARINGGAI", "Bunker/Cuaca buruk", "Sailing dan Manouver hari yang sama"],
        "Konsumsi": [587.6, 250.3, 1243.1, 1970.5, 2844.5, 667.0, 4000.0]
    }
    pd.DataFrame(master_data).to_csv("master.csv", index=False)

if not os.path.exists("rob_awal.csv"):
    rob_data = {"Kapal": ["Medelin Partner", "Medelin Citra", "Aqua Harbour"], "ROB_Awal": [50000.0, 50000.0, 50000.0]}
    pd.DataFrame(rob_data).to_csv("rob_awal.csv", index=False)

# Memuat Data
df_logs = pd.read_csv("logs.csv")
df_master = pd.read_csv("master.csv")
df_rob = pd.read_csv("rob_awal.csv")

# --- FUNGSI KALKULASI ROB ---
def get_current_rob(kapal_name):
    inisial_rob = df_rob[df_rob["Kapal"] == kapal_name]["ROB_Awal"].values[0]
    total_konsumsi = df_logs[df_logs["Kapal"] == kapal_name]["BBM"].sum()
    return inisial_rob - total_konsumsi

# --- NAVBAR / SIDEBAR ---
st.sidebar.title("🚢 NR Bunker Monitor")
menu = st.sidebar.radio("Navigasi Menu", ["Dashboard", "Input Data Harian", "Master Data & Pengaturan"])

# ==========================================
# TAMPILAN 1: DASHBOARD
# ==========================================
if menu == "Dashboard":
    st.title("📊 Dashboard Konsumsi BBM Tugboat")
    st.markdown("---")
    
    kapal_list = ["Medelin Partner", "Medelin Citra", "Aqua Harbour"]
    cols = st.columns(3)
    
    # Menampilkan Kartu Metrik
    for i, kapal in enumerate(kapal_list):
        with cols[i]:
            total_bbm = df_logs[df_logs["Kapal"] == kapal]["BBM"].sum()
            sisa_rob = get_current_rob(kapal)
            st.info(f"**{kapal}**")
            st.metric(label="Total Konsumsi (Liter)", value=f"{total_bbm:,.1f}")
            st.metric(label="Sisa ROB (Liter)", value=f"{sisa_rob:,.1f}")
            
    st.markdown("---")
    
    # Grafik Konsumsi
    if not df_logs.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Konsumsi per Kapal")
            chart_kapal = df_logs.groupby("Kapal")["BBM"].sum()
            st.bar_chart(chart_kapal)
            
        with col_chart2:
            st.subheader("Konsumsi Berdasarkan Aktivitas")
            chart_act = df_logs.groupby("Aktivitas")["BBM"].sum()
            st.bar_chart(chart_act)
    else:
        st.warning("Belum ada data log untuk menampilkan grafik.")

# ==========================================
# TAMPILAN 2: INPUT DATA HARIAN
# ==========================================
elif menu == "Input Data Harian":
    st.title("📝 Form Log Harian")
    st.markdown("Masukkan data penggunaan BBM tugboat di bawah ini.")
    
    # Input interaktif (tanpa st.form agar auto-fill berfungsi real-time)
    tanggal = st.date_input("Tanggal", datetime.today())
    kapal = st.selectbox("Nama Kapal", ["Medelin Partner", "Medelin Citra", "Aqua Harbour"])
    aktivitas = st.selectbox("Kegiatan Kapal", df_master["Aktivitas"].tolist())
    
    col1, col2 = st.columns(2)
    with col1:
        rh_me = st.number_input("Running Hour Main Engine", min_value=0.0, step=0.1)
    with col2:
        rh_ae = st.number_input("Running Hour Aux Engine", min_value=0.0, step=0.1)
    
    # Logika Auto-fill konsumsi berdasarkan Master Data
    default_bbm = float(df_master[df_master["Aktivitas"] == aktivitas]["Konsumsi"].values[0])
    bbm_input = st.number_input("Konsumsi BBM (Liter)", value=default_bbm, step=0.1)
    
    # Hitung proyeksi sisa ROB
    rob_terkini = get_current_rob(kapal)
    sisa_rob_nanti = rob_terkini - bbm_input
    st.info(f"💡 **Proyeksi Sisa ROB:** {sisa_rob_nanti:,.1f} Liter")
    
    if st.button("💾 Simpan Data Log", type="primary"):
        new_log = pd.DataFrame([{
            "ID": int(datetime.now().timestamp()),
            "Tanggal": tanggal.strftime("%Y-%m-%d"),
            "Kapal": kapal,
            "Aktivitas": aktivitas,
            "RH_ME": rh_me,
            "RH_AE": rh_ae,
            "BBM": bbm_input,
            "ROB": sisa_rob_nanti
        }])
        
        # Simpan ke CSV
        df_logs = pd.concat([df_logs, new_log], ignore_index=True)
        df_logs.to_csv("logs.csv", index=False)
        st.success("Data berhasil disimpan!")

    st.markdown("---")
    st.subheader("Riwayat Data Log (Dapat Diedit)")
    # Menampilkan tabel interaktif yang bisa diedit/dihapus langsung
    edited_logs = st.data_editor(df_logs, num_rows="dynamic", use_container_width=True)
    if st.button("Simpan Perubahan Tabel Log"):
        edited_logs.to_csv("logs.csv", index=False)
        st.success("Tabel Log berhasil diperbarui!")

# ==========================================
# TAMPILAN 3: MASTER DATA
# ==========================================
elif menu == "Master Data & Pengaturan":
    st.title("⚙️ Master Data & Pengaturan")
    
    st.subheader("1. Pengaturan ROB Awal Bulan")
    st.markdown("Ubah nilai di kolom **ROB_Awal** lalu tekan tombol Simpan di bawahnya.")
    edited_rob = st.data_editor(df_rob, num_rows="fixed", hide_index=True, use_container_width=True)
    if st.button("Simpan ROB Awal"):
        edited_rob.to_csv("rob_awal.csv", index=False)
        st.success("ROB Awal Bulan diperbarui!")
        
    st.markdown("---")
    
    st.subheader("2. Standar Konsumsi BBM Aktivitas")
    st.markdown("Tambahkan, hapus, atau ubah rata-rata konsumsi per aktivitas.")
    edited_master = st.data_editor(df_master, num_rows="dynamic", hide_index=True, use_container_width=True)
    if st.button("Simpan Standar Aktivitas"):
        edited_master.to_csv("master.csv", index=False)
        st.success("Standar Konsumsi BBM diperbarui!")