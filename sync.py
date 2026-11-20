import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px


# ==========================================
# 1. KONFIGURASI WEBSITE
# ==========================================

st.set_page_config(
    page_title="SIM-PETANI SUMUT",
    page_icon="🌾",
    layout="wide"
)

st.markdown("""
<style>
.main {
    background-color: #f5f7fa;
}

[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. KONEKSI DATABASE DATA WAREHOUSE
# ==========================================

def get_database_url():

    try:
        return st.secrets["datawarehouse"]["url"]

    except KeyError:
        st.error(
            "Konfigurasi Data Warehouse tidak ditemukan. "
            "Periksa Secrets Streamlit Cloud: "
            "[datawarehouse] dan url."
        )
        st.stop()


def read_data(query, params=None):

    conn = None

    try:

        database_url = get_database_url()

        conn = psycopg2.connect(
            database_url,
            connect_timeout=20,
            sslmode="require",
            application_name="SIM_PETANI_SUMUT"
        )

        with conn.cursor() as cur:

            cur.execute(query, params)

            # Mendapatkan nama kolom
            columns = [
                description[0]
                for description in cur.description
            ]

            # Mengambil data
            rows = cur.fetchall()

            # Mengubah hasil menjadi Pandas DataFrame
            df = pd.DataFrame(
                rows,
                columns=columns
            )

        return df

    except psycopg2.Error as e:

        st.error(
            f"Database Error: {type(e).__name__}: {e}"
        )

        raise

    except Exception as e:

        st.error(
            f"Application Error: {type(e).__name__}: {e}"
        )

        raise

    finally:

        if conn is not None:
            conn.close()


# ==========================================
# 3. HEADER
# ==========================================

st.title("🌾 SIM-PETANI SUMATERA UTARA")

st.markdown("""
**Sistem Informasi Pemetaan Petani dan Penyuluh
Provinsi Sumatera Utara**

Government Agricultural Data Dashboard
""")

st.divider()


# ==========================================
# 4. AMBIL TANGGAL SNAPSHOT
# ==========================================

dates = read_data("""
    SELECT DISTINCT id_tanggal
    FROM dw.fact_petani_harian
    ORDER BY id_tanggal DESC
""")

if dates.empty:

    st.warning(
        "Belum terdapat data pada Data Warehouse."
    )

    st.stop()


date_options = dates["id_tanggal"].tolist()

selected_date = st.sidebar.selectbox(
    "Pilih Tanggal Snapshot",
    date_options
)


# ==========================================
# 5. SIDEBAR NAVIGASI
# ==========================================

menu = st.sidebar.radio(
    "MENU NAVIGASI",
    [
        "Dashboard Utama",
        "Statistik Kabupaten",
        "Statistik Komoditas",
        "Data Petani"
    ]
)


# ==========================================
# 6. DASHBOARD UTAMA
# ==========================================

if menu == "Dashboard Utama":

    summary = read_data("""
        SELECT
            COUNT(*) AS total_petani,
            COALESCE(SUM(luas_lahan), 0) AS total_luas,
            COUNT(DISTINCT wilayah_sumber) AS total_kabupaten,
            COUNT(DISTINCT id_komoditas) AS total_komoditas
        FROM dw.fact_petani_harian
        WHERE id_tanggal = %s
    """, (selected_date,))

    if summary.empty:
        st.warning("Data ringkasan tidak tersedia.")
        st.stop()

    r = summary.iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Petani",
        f"{int(r.total_petani):,}"
    )

    c2.metric(
        "Luas Lahan",
        f"{float(r.total_luas):,.2f} Ha"
    )

    c3.metric(
        "Kabupaten",
        int(r.total_kabupaten)
