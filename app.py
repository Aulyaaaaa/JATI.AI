"""
JATI.AI - Jaringan Asisten Tani dan Iklim
Versi Streamlit (UI dirapikan)
"""

import inspect
import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from jati_core import (
    JatiError,
    MODEL_DEFAULT,
    MODEL_TERSEDIA,
    TAGLINE,
    TEMPERATURE_DEFAULT,
    daftar_riwayat,
    muat_riwayat,
    reset_history,
    simpan_riwayat,
    statistik,
    stream_jawaban,
)



# KONFIGURASI


BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"
LOGO_PNG = ASSET_DIR / "logo.png"

st.set_page_config(
    page_title="JATI.AI | Teman Cerdas untuk Tani, Iklim, dan Alam",
    page_icon=str(LOGO_PNG) if LOGO_PNG.exists() else "🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Kompatibel dengan Streamlit lama (use_container_width) dan baru (width="stretch")
STRETCH = (
    {"width": "stretch"}
    if "width" in inspect.signature(st.button).parameters
    else {"use_container_width": True}
)


def html(teks: str):
    """
    Render HTML/CSS lewat st.markdown dengan aman.
    Menghapus indentasi dan baris kosong supaya Markdown
    tidak salah menganggapnya sebagai code block.
    """
    bersih = "\n".join(b.strip() for b in teks.splitlines() if b.strip())
    st.markdown(bersih, unsafe_allow_html=True)



# CSS


html(
    """
    <style>
    :root {
        --forest: #173F2F;
        --forest-light: #285E49;
        --leaf: #6F8F5F;
        --sage: #DCE8D4;
        --sage-light: #EEF5EA;
        --ivory: #F7F5EE;
        --white: #FFFFFF;
        --ink: #22332B;
        --muted: #738078;
        --line: #E2E1D8;
        --teal: #2F6F73;
    }

    /* ---------- FONT (tidak menyentuh ikon & kode) ---------- */
    .stApp, .stApp p, .stApp li, .stApp label, .stApp button,
    .stApp input, .stApp textarea, .stApp h1, .stApp h2, .stApp h3,
    .stApp h4, .stApp h5, .stApp h6 {
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif !important;
    }
    .stApp [data-testid="stIconMaterial"],
    .stApp .material-icons,
    .stApp .material-symbols-rounded {
        font-family: "Material Symbols Rounded", "Material Icons" !important;
    }
    .stApp code, .stApp pre {
        font-family: "Cascadia Code", Consolas, monospace !important;
    }

    /* ---------- GLOBAL ---------- */
    .stApp { background: var(--ivory); color: var(--ink); }

    #MainMenu, footer, .stAppDeployButton,
    [data-testid="stStatusWidget"], [data-testid="stDecoration"] {
        visibility: hidden;
        display: none;
    }
    [data-testid="stHeader"] { background: transparent; }

    .block-container {
        max-width: 1180px !important;
        padding: 2rem 2rem 7rem 2rem !important;
    }

    /* ---------- SIDEBAR ---------- */
    [data-testid="stSidebar"] {
        background: var(--forest);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    [data-testid="stSidebarHeader"] {
        padding: 0.6rem 1rem 0 1rem !important;
        min-height: 0 !important;
        height: auto !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding: 0.25rem 1rem 1.5rem 1rem !important;
    }

    /* logo di atas tile terang agar terlihat di latar hijau */
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        background: var(--ivory);
        border-radius: 14px;
        padding: 6px;
        box-sizing: border-box;
    }

    .sidebar-title {
        color: #FFFFFF !important;
        font-size: 1.2rem;
        font-weight: 800;
        line-height: 1.15;
    }
    .sidebar-subtitle {
        color: var(--sage) !important;
        font-size: 0.76rem;
        line-height: 1.4;
        margin-top: 2px;
    }
    .sidebar-heading {
        color: #FFFFFF !important;
        font-size: 0.95rem;
        font-weight: 700;
        margin: 4px 0 10px 0;
    }

    [data-testid="stSidebar"] hr {
        border: none;
        border-top: 1px solid rgba(220, 232, 212, 0.18);
        margin: 1rem 0;
    }

    /* tombol sidebar */
    [data-testid="stSidebar"] .stButton,
    [data-testid="stSidebar"] .stDownloadButton { margin-bottom: 6px; }

    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stDownloadButton > button {
        width: 100%;
        height: auto;
        min-height: 42px;
        background: rgba(255, 255, 255, 0.045) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(220, 232, 212, 0.20) !important;
        border-radius: 12px !important;
        padding: 0.6rem 0.8rem !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button p,
    [data-testid="stSidebar"] .stDownloadButton > button p {
        color: #FFFFFF !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        line-height: 1.4 !important;
        text-align: left !important;
        white-space: normal !important;
        margin: 0 !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] .stDownloadButton > button:hover {
        background: rgba(111, 143, 95, 0.55) !important;
        border-color: rgba(220, 232, 212, 0.55) !important;
    }

    /* tombol utama (percakapan baru) */
    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
        background: #2A674F !important;
        border-color: #55866B !important;
        justify-content: center !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] p,
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] p {
        font-weight: 700 !important;
        text-align: center !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: #34775B !important;
    }

    /* expander sidebar */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border: 1px solid rgba(220, 232, 212, 0.18) !important;
        border-radius: 14px !important;
        background: rgba(255, 255, 255, 0.035) !important;
        margin-bottom: 8px !important;
        overflow: hidden;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] details {
        border: none !important;
        background: transparent !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] label,
    [data-testid="stSidebar"] [data-testid="stExpander"] small,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: #E9F0E5 !important;
    }
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #C8D7C2 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 1.05rem;
    }
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] p {
        color: #C8D7C2 !important;
    }
    [data-testid="stSidebar"] [data-testid="stTickBarMin"],
    [data-testid="stSidebar"] [data-testid="stTickBarMax"],
    [data-testid="stSidebar"] [data-testid="stSliderThumbValue"] {
        color: #E9F0E5 !important;
    }

    /* ---------- HEADER UTAMA ---------- */
    .main-title {
        color: var(--forest) !important;
        font-size: 1.65rem;
        font-weight: 800;
        line-height: 1.1;
        margin: 0;
    }
    .main-subtitle {
        color: var(--teal) !important;
        font-size: 0.86rem;
        font-weight: 500;
        margin-top: 3px;
    }

    /* ---------- WELCOME ---------- */
    .welcome-box {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1.65rem 1.7rem;
        margin: 1rem 0 1.2rem 0;
        box-shadow: 0 4px 18px rgba(23, 63, 47, 0.04);
    }
    .welcome-title {
        color: var(--forest) !important;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.55rem;
    }
    .welcome-text {
        color: #506057 !important;
        font-size: 0.91rem;
        line-height: 1.75;
    }

    /* ---------- PERTANYAAN CONTOH ---------- */
    .suggest-title {
        color: var(--muted) !important;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.4px;
        text-transform: uppercase;
        margin: 1rem 0 0.55rem 0;
    }
    .st-key-suggestions .stButton > button {
        width: 100%;
        height: auto;
        min-height: 54px;
        background: #FFFFFF !important;
        border: 1px solid #DDE4D8 !important;
        border-radius: 14px !important;
        padding: 0.7rem 0.9rem !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
    }
    .st-key-suggestions .stButton > button p {
        color: var(--forest) !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        line-height: 1.4 !important;
        text-align: left !important;
        white-space: normal !important;
        margin: 0 !important;
    }
    .st-key-suggestions .stButton > button:hover {
        background: var(--sage-light) !important;
        border-color: #AFC3A3 !important;
    }

    /* ---------- CHAT ---------- */
    [data-testid="stChatMessage"] {
        border-radius: 18px !important;
        padding: 0.7rem 1rem !important;
        margin: 0.5rem 0 !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
    }
    .role-user-marker, .role-jati-marker { display: none !important; }

    [data-testid="stChatMessage"]:has(.role-user-marker) {
        background: var(--forest) !important;
        border-color: var(--forest) !important;
    }
    [data-testid="stChatMessage"]:has(.role-jati-marker) {
        background: #FFFFFF !important;
        border-color: var(--line) !important;
    }
    [data-testid="stChatMessage"]:has(.role-user-marker) p,
    [data-testid="stChatMessage"]:has(.role-user-marker) li,
    [data-testid="stChatMessage"]:has(.role-user-marker) strong,
    [data-testid="stChatMessage"]:has(.role-user-marker) em {
        color: #FFFFFF !important;
    }
    [data-testid="stChatMessage"]:has(.role-jati-marker) p,
    [data-testid="stChatMessage"]:has(.role-jati-marker) li {
        color: var(--ink) !important;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li { line-height: 1.7 !important; }

    /* ---------- CHAT INPUT ---------- */
    [data-testid="stBottom"] > div { background: var(--ivory) !important; }
    [data-testid="stChatInput"] { margin-top: 0.5rem; }
    [data-testid="stChatInput"] > div {
        background: #FFFFFF !important;
        border: 1px solid #DAD9CF !important;
        border-radius: 18px !important;
        box-shadow: 0 5px 22px rgba(23, 63, 47, 0.06) !important;
    }
    [data-testid="stChatInput"] textarea { font-size: 0.9rem !important; }
    [data-testid="stChatInput"] > div:focus-within {
        border-color: var(--leaf) !important;
        box-shadow: 0 0 0 3px rgba(111, 143, 95, 0.12) !important;
    }

    /* ---------- FOOTER ---------- */
    .footer-text {
        color: #839087 !important;
        font-size: 0.72rem;
        line-height: 1.6;
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid var(--line);
    }

    /* ---------- RESPONSIVE ---------- */
    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .main-title { font-size: 1.4rem; }
        .welcome-box { padding: 1.2rem; }
    }
    </style>
    """
)



# SESSION STATE


if "messages" not in st.session_state:
    st.session_state.messages = reset_history()

if "temperature" not in st.session_state:
    st.session_state.temperature = TEMPERATURE_DEFAULT

if "model" not in st.session_state:
    st.session_state.model = MODEL_DEFAULT

if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 1200

if "pertanyaan_masuk" not in st.session_state:
    st.session_state.pertanyaan_masuk = None



# AVATAR


AVATAR_JATI = str(LOGO_PNG) if LOGO_PNG.exists() else "🌱"
AVATAR_USER = "🧑‍🌾"



# KATEGORI


KATEGORI = {
    "🌾 Tani": [
        "Cara alami mengendalikan hama wereng pada padi",
        "Bagaimana membuat pupuk kompos dari jerami?",
        "Kapan waktu terbaik memupuk tanaman cabai?",
    ],
    "🌦️ Iklim": [
        "Bagaimana menyesuaikan jadwal tanam saat musim hujan mundur?",
        "Apa dampak El Nino bagi petani padi di Jawa?",
        "Cara menghadapi kekeringan di lahan tadah hujan",
    ],
    "🌿 Alam": [
        "Cara memperbaiki tanah yang sudah mengeras dan tandus",
        "Apa itu agroforestri dan apa untungnya bagi petani?",
        "Bagaimana mengolah limbah kandang agar tidak mencemari sungai?",
    ],
}



# CALLBACK


def ajukan(pertanyaan: str):
    """Dipakai sebagai on_click; Streamlit otomatis rerun setelahnya."""
    st.session_state.pertanyaan_masuk = pertanyaan


def percakapan_baru():
    st.session_state.messages = reset_history()
    st.session_state.pertanyaan_masuk = None



# SIDEBAR


with st.sidebar:

    # ---------- BRAND ----------
    kolom_logo, kolom_teks = st.columns(
        [0.30, 0.70],
        vertical_alignment="center",
        gap="small",
    )

    with kolom_logo:
        if LOGO_PNG.exists():
            st.image(str(LOGO_PNG), width=56)
        else:
            st.markdown("## 🌱")

    with kolom_teks:
        html('<div class="sidebar-title">JATI.AI</div>')
        html('<div class="sidebar-subtitle">Jaringan Asisten Tani dan Iklim</div>')

    st.write("")

    st.button(
        "✦  Mulai percakapan baru",
        type="primary",
        on_click=percakapan_baru,
        **STRETCH,
    )

    st.markdown("---")

    # ---------- TOPIK ----------
    html('<div class="sidebar-heading">Jelajah topik</div>')

    for nama_kategori, contoh in KATEGORI.items():
        with st.expander(nama_kategori, expanded=False):
            for i, pertanyaan in enumerate(contoh):
                st.button(
                    pertanyaan,
                    key=f"k_{nama_kategori}_{i}",
                    on_click=ajukan,
                    args=(pertanyaan,),
                    **STRETCH,
                )

    # ---------- RIWAYAT ----------
    with st.expander("🕘 Riwayat percakapan", expanded=False):

        st.download_button(
            "Unduh percakapan ini (JSON)",
            data=json.dumps(
                st.session_state.messages,
                ensure_ascii=False,
                indent=2,
            ),
            file_name=f"jati_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            **STRETCH,
        )

        if st.button("Simpan ke folder riwayat/", **STRETCH):
            path = simpan_riwayat(st.session_state.messages)
            st.success(f"Tersimpan: {path.name}")

        files = daftar_riwayat()

        if files:
            peta_file = {f.name: f for f in files}

            pilihan = st.selectbox(
                "Buka percakapan lama",
                list(peta_file.keys()),
                index=0,
            )

            if st.button("Muat percakapan", **STRETCH):
                st.session_state.messages = muat_riwayat(peta_file[pilihan])
                st.rerun()
        else:
            st.caption("Belum ada percakapan tersimpan.")

    # ---------- PENGATURAN ----------
    with st.expander("⚙️ Pengaturan jawaban", expanded=False):

        model_keys = list(MODEL_TERSEDIA.keys())

        if st.session_state.model not in model_keys:
            st.session_state.model = model_keys[0]

        st.session_state.model = st.selectbox(
            "Model",
            model_keys,
            index=model_keys.index(st.session_state.model),
            format_func=lambda m: MODEL_TERSEDIA[m],
        )

        st.session_state.temperature = st.slider(
            "Gaya jawaban",
            min_value=0.0,
            max_value=1.2,
            value=float(st.session_state.temperature),
            step=0.1,
            help="Nilai kecil = lebih konsisten. Nilai besar = lebih kreatif.",
        )

        st.session_state.max_tokens = st.slider(
            "Panjang jawaban maksimal",
            min_value=400,
            max_value=2000,
            value=int(st.session_state.max_tokens),
            step=100,
        )

    # ---------- STATISTIK ----------
    s = statistik(st.session_state.messages)

    if s["pertanyaan"]:
        with st.expander("📊 Statistik percakapan", expanded=False):
            kol1, kol2 = st.columns(2)
            kol1.metric("Pertanyaan", s["pertanyaan"])
            kol2.metric("Jawaban", s["jawaban"])
            st.caption(f"Topik paling sering: **{s['topik_utama']}**")
            st.caption(
                f"Rata-rata panjang jawaban: {s['rata_rata_panjang_jawaban']} kata"
            )



# HEADER UTAMA


header_col1, header_col2 = st.columns(
    [0.08, 0.92],
    vertical_alignment="center",
)

with header_col1:
    if LOGO_PNG.exists():
        st.image(str(LOGO_PNG), width=55)
    else:
        st.markdown("## 🌱")

with header_col2:
    html('<div class="main-title">JATI.AI</div>')
    html(f'<div class="main-subtitle">{TAGLINE}</div>')

st.divider()



# PERCAKAPAN


percakapan = [
    m for m in st.session_state.messages if m.get("role") != "system"
]



# HALAMAN AWAL


if not percakapan:

    html(
        """
        <div class="welcome-box">
        <div class="welcome-title">Selamat datang di JATI.AI 🌱</div>
        <div class="welcome-text">
        Tanyakan apa saja seputar budidaya tanaman, cuaca dan musim,
        kesehatan tanah, serta pengelolaan lingkungan. Jawaban dibuat
        sesederhana mungkin agar mudah dipahami dan diterapkan.
        </div>
        </div>
        """
    )

    html('<div class="suggest-title">Coba tanyakan</div>')

    contoh_awal = [
        "Padi saya menguning di ujung daun, apa penyebabnya?",
        "Tanaman apa yang cocok ditanam saat kemarau panjang?",
        "Bagaimana cara mengurangi penggunaan pupuk kimia?",
        "Apa tanda-tanda tanah kebun saya sudah tidak sehat?",
    ]

    with st.container(key="suggestions"):
        kolom = st.columns(2, gap="small")

        for i, contoh in enumerate(contoh_awal):
            with kolom[i % 2]:
                st.button(
                    contoh,
                    key=f"awal_{i}",
                    on_click=ajukan,
                    args=(contoh,),
                    **STRETCH,
                )



# TAMPILKAN CHAT


for pesan in percakapan:

    role = pesan.get("role")
    content = pesan.get("content", "")

    if role == "user":
        with st.chat_message("user", avatar=AVATAR_USER):
            html('<span class="role-user-marker"></span>')
            st.markdown(content)

    elif role == "assistant":
        with st.chat_message("assistant", avatar=AVATAR_JATI):
            html('<span class="role-jati-marker"></span>')
            st.markdown(content)



# INPUT


prompt = st.chat_input("Tanya JATI tentang tani, iklim, atau alam...")

if st.session_state.pertanyaan_masuk:
    prompt = st.session_state.pertanyaan_masuk
    st.session_state.pertanyaan_masuk = None



# PROSES PERTANYAAN


if prompt:

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar=AVATAR_USER):
        html('<span class="role-user-marker"></span>')
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR_JATI):
        html('<span class="role-jati-marker"></span>')

        wadah = st.empty()
        wadah.markdown("*JATI sedang menyiapkan jawaban…*")
        jawaban = ""

        try:
            for potongan in stream_jawaban(
                st.session_state.messages,
                model=st.session_state.model,
                temperature=st.session_state.temperature,
                max_tokens=st.session_state.max_tokens,
            ):
                jawaban += potongan
                wadah.markdown(jawaban + " ▌")

            if jawaban.strip():
                wadah.markdown(jawaban)
            else:
                wadah.warning("JATI belum mengirim jawaban. Silakan coba lagi.")

        except JatiError as e:
            wadah.warning(str(e))
            jawaban = ""

    if jawaban.strip():
        st.session_state.messages.append(
            {"role": "assistant", "content": jawaban}
        )
        st.rerun()

    elif (
        st.session_state.messages
        and st.session_state.messages[-1].get("role") == "user"
    ):
        st.session_state.messages.pop()



# FOOTER


html(
    """
    <div class="footer-text">
    JATI.AI dapat keliru. Untuk keputusan penting di lahan, tetap
    pertimbangkan kondisi lokal dan konsultasikan dengan penyuluh
    pertanian setempat atau sumber cuaca resmi.
    </div>
    """
)