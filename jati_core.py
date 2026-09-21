"""
=====================================================================
 JATI.AI - Jaringan Asisten Tani dan Iklim
 "Teman Cerdas untuk Tani, Iklim, dan Alam"
---------------------------------------------------------------------
 jati_core.py -> OTAK dari chatbot.

 File ini berisi semua logika inti yang dipakai bersama oleh:
   - chatbot_console.py  (versi terminal / console)
   - app.py              (versi web Streamlit)

 Isi modul:
   1. Konfigurasi & pemuatan API key (aman, lewat .env)
   2. System prompt (kepribadian JATI.AI)
   3. Pengelolaan conversation history
   4. Fungsi kirim pesan ke Groq API (biasa & streaming) + error handling
   5. Simpan / muat riwayat percakapan (JSON)
   6. Statistik percakapan
=====================================================================
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# ---------------------------------------------------------------------
# 1. KONFIGURASI DASAR
# ---------------------------------------------------------------------

# Muat variabel dari file .env (GROQ_API_KEY=...)
load_dotenv()

# Model produksi Groq. Model Llama lama (llama-3.3-70b-versatile) masih ada,
# tapi default kita pakai gpt-oss-120b seperti contoh di kelas.
# Daftar model terbaru: https://console.groq.com/docs/models
MODEL_DEFAULT = "openai/gpt-oss-120b"

MODEL_TERSEDIA = {
    "openai/gpt-oss-120b": "GPT OSS 120B - paling pintar (default)",
    "openai/gpt-oss-20b": "GPT OSS 20B - lebih ringan & cepat",
    "llama-3.3-70b-versatile": "Llama 3.3 70B - alternatif",
}

TEMPERATURE_DEFAULT = 0.6   # cukup luwes, tapi tetap konsisten untuk info teknis
MAX_TOKENS_DEFAULT = 1200   # batas panjang jawaban

# Berapa banyak pesan terakhir yang dikirim ulang ke API.
# LLM tidak punya memori, jadi seluruh history harus dikirim ulang setiap request.
# Supaya token tidak cepat habis, history lama dipangkas (system prompt selalu ikut).
MAX_PESAN_KONTEKS = 12

FOLDER_RIWAYAT = Path("riwayat")

# Palet warna identitas JATI.AI (dipakai oleh app.py dan console)
WARNA = {
    "forest_green": "#173F2F",
    "leaf_green": "#6F8F5F",
    "sage_light": "#DCE8D4",
    "warm_ivory": "#F6F4EC",
    "climate_teal": "#2F6F73",
    "earth_accent": "#D98E5B",
    "dark_text": "#22332B",
    "white": "#FFFFFF",
}

TAGLINE = "Teman Cerdas untuk Tani, Iklim, dan Alam"


class JatiError(Exception):
    """Error khusus JATI.AI supaya pesan error ke pengguna tetap ramah."""


# ---------------------------------------------------------------------
# 2. API KEY & CLIENT
# ---------------------------------------------------------------------

def muat_api_key() -> str:
    """
    Mengambil GROQ_API_KEY dari environment variable / file .env.

    API key TIDAK PERNAH ditulis di dalam kode supaya aman saat di-push
    ke GitHub (file .env sudah masuk .gitignore).
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise JatiError(
            "GROQ_API_KEY tidak ditemukan.\n"
            "Buat file bernama .env di folder project, lalu isi dengan:\n\n"
            "    GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx\n\n"
            "Ambil API key di https://console.groq.com/keys"
        )
    return api_key


_client = None


def get_client() -> Groq:
    """
    Membuat (sekali saja) objek client Groq.
    Client adalah 'gerbang' komunikasi antara kode Python dan server Groq.
    """
    global _client
    if _client is None:
        _client = Groq(api_key=muat_api_key())
    return _client


# ---------------------------------------------------------------------
# 3. SYSTEM PROMPT - kepribadian JATI.AI
# ---------------------------------------------------------------------

SYSTEM_PROMPT = """Kamu adalah JATI.AI (Jaringan Asisten Tani dan Iklim), asisten digital berbahasa Indonesia.
Tagline kamu: "Teman Cerdas untuk Tani, Iklim, dan Alam".

SIAPA PENGGUNAMU
- Pengguna utama: petani, penyuluh, dan pelaku sektor agrikultur di Indonesia. Banyak dari mereka
  tidak punya latar belakang teknis, jadi jawabanmu harus mudah dipahami dan langsung bisa dipraktikkan.
- Pengguna sekunder: masyarakat umum yang ingin jawaban konkret soal lingkungan, iklim, dan alam.

TOPIK YANG KAMU LAYANI
1. Tani  : budidaya tanaman, pemilihan varietas, pengolahan tanah, pemupukan, hama & penyakit,
           irigasi, pasca panen, pertanian organik/regeneratif, hitungan biaya sederhana.
2. Iklim : musim hujan & kemarau, El Nino/La Nina, kalender tanam, adaptasi cuaca ekstrem,
           kekeringan, banjir, emisi gas rumah kaca dari pertanian.
3. Alam  : keberlanjutan lingkungan, kesehatan tanah, air, keanekaragaman hayati, agroforestri,
           pengelolaan sampah organik, konservasi, restorasi lahan.

CARA KAMU MENJAWAB
- Selalu gunakan Bahasa Indonesia yang sederhana dan ramah, seperti penyuluh pertanian yang sabar.
- Hindari istilah teknis. Kalau terpaksa dipakai, beri penjelasan singkat dalam kurung.
  Contoh: "pH tanah (tingkat keasaman tanah)".
- Jawaban singkat dan padat: 2-5 paragraf pendek, atau poin-poin bernomor bila berupa langkah.
- Selalu beri langkah konkret: takaran, waktu, alat, atau urutan kerja yang bisa langsung dilakukan.
- Gunakan konteks Indonesia: komoditas lokal (padi, jagung, cabai, bawang, kopi, sawit, hortikultura),
  musim hujan/kemarau, BMKG, penyuluh pertanian/BPP, kelompok tani.
- Kalau pertanyaan kurang jelas (lokasi, komoditas, luas lahan, fase tanam), berikan dulu jawaban
  umum yang berguna, lalu tutup dengan maksimal 1-2 pertanyaan singkat untuk memperdalam.
- Tutup jawaban dengan satu saran lanjutan praktis bila relevan.

BATASAN YANG HARUS KAMU PATUHI
- Kamu TIDAK punya akses data cuaca real-time, harga pasar hari ini, atau citra satelit.
  Kalau ditanya prakiraan cuaca/harga terkini, katakan terus terang dan arahkan ke sumber resmi
  seperti BMKG, Dinas Pertanian setempat, atau penyuluh di wilayah pengguna.
- Jangan mengarang angka statistik, nama peraturan, atau hasil penelitian. Kalau tidak yakin,
  katakan tidak yakin dan sarankan cara memverifikasinya.
- Untuk pestisida, herbisida, atau pupuk kimia: selalu ingatkan penggunaan alat pelindung diri,
  dosis sesuai label kemasan, dan masa tunggu sebelum panen. Jangan menyarankan bahan aktif
  yang dilarang, dan utamakan solusi terpadu (pencegahan, musuh alami, rotasi tanaman) lebih dulu.
- Kalau pertanyaannya di luar topik tani, iklim, dan alam (misalnya tugas kuliah umum, gosip,
  coding), tolak dengan sopan dalam satu kalimat, lalu tawarkan bantuan yang masih di ranahmu.
- Jangan memakai emoji berlebihan. Maksimal satu emoji per jawaban, dan hanya bila benar-benar pas.
- Jangan menyebut dirimu sebagai model bahasa milik perusahaan tertentu. Kamu adalah JATI.AI.
"""


def reset_history() -> list:
    """Mengembalikan conversation history ke kondisi awal (hanya system prompt)."""
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def potong_history(messages: list, max_pesan: int = MAX_PESAN_KONTEKS) -> list:
    """
    Memangkas history supaya hemat token.
    System prompt selalu dipertahankan, sisanya diambil N pesan terakhir.
    """
    system = messages[0:1]
    percakapan = messages[1:]
    if len(percakapan) > max_pesan:
        percakapan = percakapan[-max_pesan:]
    return system + percakapan


# ---------------------------------------------------------------------
# 4. KIRIM PESAN KE GROQ API
# ---------------------------------------------------------------------

def _pesan_error(e: Exception) -> str:
    """Menerjemahkan error teknis menjadi pesan yang mudah dipahami pengguna."""
    teks = str(e).lower()
    if "authentication" in teks or "invalid api key" in teks or "401" in teks:
        return "API key ditolak. Periksa kembali isi file .env kamu."
    if "rate limit" in teks or "429" in teks:
        return "Kuota permintaan sedang penuh. Tunggu sekitar satu menit, lalu coba lagi."
    if "connection" in teks or "timeout" in teks or "network" in teks:
        return "Koneksi internet bermasalah. Periksa jaringan lalu kirim ulang pertanyaanmu."
    if "model" in teks and ("not found" in teks or "decommissioned" in teks):
        return ("Model yang dipilih sudah tidak tersedia di Groq. "
                "Ganti MODEL_DEFAULT di jati_core.py dengan model terbaru "
                "dari https://console.groq.com/docs/models")
    return f"Terjadi gangguan saat menghubungi server Groq: {e}"


def kirim_pesan(messages: list,
                model: str = MODEL_DEFAULT,
                temperature: float = TEMPERATURE_DEFAULT,
                max_tokens: int = MAX_TOKENS_DEFAULT) -> str:
    """
    Mengirim seluruh riwayat percakapan ke Groq API, mengembalikan jawaban lengkap.
    Melempar JatiError bila gagal, supaya history tidak ikut rusak.
    """
    try:
        response = get_client().chat.completions.create(
            model=model,
            messages=potong_history(messages),
            temperature=temperature,
            max_completion_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        raise JatiError(_pesan_error(e)) from e


def stream_jawaban(messages: list,
                   model: str = MODEL_DEFAULT,
                   temperature: float = TEMPERATURE_DEFAULT,
                   max_tokens: int = MAX_TOKENS_DEFAULT):
    """
    Versi streaming: jawaban dikirim potongan demi potongan (generator),
    sehingga teks muncul bertahap seperti sedang diketik.

    Cara pakai:
        for potongan in stream_jawaban(messages):
            print(potongan, end="", flush=True)
    """
    try:
        stream = get_client().chat.completions.create(
            model=model,
            messages=potong_history(messages),
            temperature=temperature,
            max_completion_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            potongan = chunk.choices[0].delta.content or ""
            if potongan:
                yield potongan
    except Exception as e:
        raise JatiError(_pesan_error(e)) from e


# ---------------------------------------------------------------------
# 5. SIMPAN & MUAT RIWAYAT PERCAKAPAN
# ---------------------------------------------------------------------

def simpan_riwayat(messages: list, filename=None) -> Path:
    """Menyimpan seluruh percakapan ke file JSON di folder riwayat/."""
    FOLDER_RIWAYAT.mkdir(exist_ok=True)

    if filename is None:
        filename = f"jati_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    path = FOLDER_RIWAYAT / filename
    data = {
        "aplikasi": "JATI.AI",
        "disimpan_pada": datetime.now().isoformat(timespec="seconds"),
        "jumlah_pesan": len(messages) - 1,  # system prompt tidak dihitung
        "messages": messages,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def muat_riwayat(path) -> list:
    """Memuat kembali percakapan dari file JSON, lalu melanjutkannya."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Mendukung dua format: dict (format JATI.AI) atau list biasa
    messages = data["messages"] if isinstance(data, dict) else data

    # Pastikan system prompt terbaru yang dipakai
    if messages and messages[0]["role"] == "system":
        messages[0] = {"role": "system", "content": SYSTEM_PROMPT}
    else:
        messages = reset_history() + messages
    return messages


def daftar_riwayat() -> list:
    """Mengembalikan daftar file riwayat, dari yang paling baru."""
    if not FOLDER_RIWAYAT.exists():
        return []
    return sorted(FOLDER_RIWAYAT.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


# ---------------------------------------------------------------------
# 6. STATISTIK PERCAKAPAN
# ---------------------------------------------------------------------

KATA_KUNCI_KATEGORI = {
    "Tani": ["tanam", "padi", "jagung", "cabai", "bawang", "pupuk", "hama", "panen",
             "benih", "bibit", "sawah", "lahan", "kebun", "tanah", "irigasi", "ternak",
             "kopi", "sayur", "buah", "gulma", "pestisida", "kompos"],
    "Iklim": ["cuaca", "iklim", "hujan", "kemarau", "musim", "banjir", "kekeringan",
              "suhu", "panas", "angin", "el nino", "la nina", "emisi", "karbon", "bmkg"],
    "Alam": ["lingkungan", "sampah", "limbah", "air", "sungai", "hutan", "pohon",
             "konservasi", "biodiversitas", "ekosistem", "keberlanjutan", "daur ulang",
             "erosi", "mangrove", "satwa"],
}


def statistik(messages: list) -> dict:
    """Menghitung statistik sederhana dari percakapan yang sedang berjalan."""
    pesan_user = [m for m in messages if m["role"] == "user"]
    pesan_jati = [m for m in messages if m["role"] == "assistant"]

    kata_user = sum(len(m["content"].split()) for m in pesan_user)
    kata_jati = sum(len(m["content"].split()) for m in pesan_jati)

    teks_user = " ".join(m["content"].lower() for m in pesan_user)
    skor = {}
    for kategori, kata_kunci in KATA_KUNCI_KATEGORI.items():
        skor[kategori] = sum(len(re.findall(k, teks_user)) for k in kata_kunci)

    topik_utama = max(skor, key=skor.get) if any(skor.values()) else "Belum terdeteksi"

    return {
        "pertanyaan": len(pesan_user),
        "jawaban": len(pesan_jati),
        "kata_ditulis_pengguna": kata_user,
        "kata_dijawab_jati": kata_jati,
        "rata_rata_panjang_jawaban": round(kata_jati / len(pesan_jati)) if pesan_jati else 0,
        "skor_topik": skor,
        "topik_utama": topik_utama,
    }
