"""
=====================================================================
 JATI.AI - Jaringan Asisten Tani dan Iklim
 chatbot_console.py -> versi terminal / console (syarat utama tugas)

 Jalankan dengan:   python chatbot_console.py

 Perintah khusus:
   /keluar   /exit     -> keluar dari chatbot
   /baru     /clear    -> hapus riwayat, mulai percakapan baru
   /simpan   /save     -> simpan percakapan ke folder riwayat/ (JSON)
   /muat     /load     -> muat percakapan lama dan lanjutkan
   /statistik /stats   -> tampilkan statistik percakapan
   /suhu <angka>       -> ubah temperature (0.0 - 1.5)
   /bantuan  /help     -> tampilkan daftar perintah
=====================================================================
"""

from jati_core import (
    JatiError,
    MODEL_DEFAULT,
    TAGLINE,
    TEMPERATURE_DEFAULT,
    daftar_riwayat,
    muat_riwayat,
    reset_history,
    simpan_riwayat,
    statistik,
    stream_jawaban,
)

# --- Warna terminal (ANSI) supaya tampilan console enak dibaca ---
HIJAU = "\033[38;5;29m"
SAGE = "\033[38;5;151m"
TEAL = "\033[38;5;30m"
TANAH = "\033[38;5;173m"
ABU = "\033[38;5;245m"
TEBAL = "\033[1m"
RESET = "\033[0m"

GARIS = ABU + "-" * 62 + RESET

LOGO = f"""{HIJAU}{TEBAL}
        ,-.
       (   )     J A T I . A I
        `-|
          |      {RESET}{SAGE}Jaringan Asisten Tani dan Iklim{RESET}{HIJAU}{TEBAL}
      `.__|
{RESET}"""


def tampilkan_sambutan(temperature, model):
    print(LOGO)
    print(f"  {TEAL}{TAGLINE}{RESET}")
    print(GARIS)
    print(f"  Model      : {model}")
    print(f"  Temperature: {temperature}")
    print(f"  Ketik {TEBAL}/bantuan{RESET} untuk melihat daftar perintah.")
    print(GARIS + "\n")


def tampilkan_bantuan():
    print(f"\n{TEBAL}Daftar perintah:{RESET}")
    print(f"  {TEAL}/keluar{RESET}     keluar dari chatbot")
    print(f"  {TEAL}/baru{RESET}       hapus riwayat dan mulai percakapan baru")
    print(f"  {TEAL}/simpan{RESET}     simpan percakapan ke file JSON")
    print(f"  {TEAL}/muat{RESET}       muat percakapan lama lalu lanjutkan")
    print(f"  {TEAL}/statistik{RESET}  ringkasan percakapan sesi ini")
    print(f"  {TEAL}/suhu 0.8{RESET}   ubah temperature (0.0 = konsisten, 1.5 = kreatif)")
    print(f"  {TEAL}/bantuan{RESET}    tampilkan pesan ini\n")


def tampilkan_statistik(messages):
    s = statistik(messages)
    if s["pertanyaan"] == 0:
        print(f"\n{ABU}Belum ada percakapan untuk dihitung.{RESET}\n")
        return

    print(f"\n{TEBAL}Statistik percakapan{RESET}")
    print(f"  Pertanyaan kamu        : {s['pertanyaan']}")
    print(f"  Jawaban JATI           : {s['jawaban']}")
    print(f"  Kata yang kamu tulis   : {s['kata_ditulis_pengguna']}")
    print(f"  Kata jawaban JATI      : {s['kata_dijawab_jati']}")
    print(f"  Rata-rata jawaban      : {s['rata_rata_panjang_jawaban']} kata")
    print(f"  Topik paling sering    : {s['topik_utama']}")
    rincian = ", ".join(f"{k}: {v}" for k, v in s["skor_topik"].items())
    print(f"  {ABU}Rincian topik          : {rincian}{RESET}\n")


def pilih_file_riwayat():
    """Menampilkan daftar file riwayat lalu meminta pengguna memilih salah satu."""
    files = daftar_riwayat()
    if not files:
        print(f"\n{ABU}Belum ada riwayat tersimpan di folder riwayat/.{RESET}\n")
        return None

    print(f"\n{TEBAL}Riwayat tersimpan:{RESET}")
    for i, f in enumerate(files[:10], start=1):
        print(f"  [{i}] {f.name}")

    pilihan = input("Pilih nomor (Enter untuk batal): ").strip()
    if not pilihan.isdigit() or not (1 <= int(pilihan) <= len(files[:10])):
        print(f"{ABU}Dibatalkan.{RESET}\n")
        return None
    return files[int(pilihan) - 1]


def main():
    messages = reset_history()
    temperature = TEMPERATURE_DEFAULT

    tampilkan_sambutan(temperature, MODEL_DEFAULT)

    while True:
        try:
            user_input = input(f"{TEBAL}Anda  {RESET}> ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{HIJAU}Sampai jumpa. Semoga panennya berkah.{RESET}\n")
            break

        if not user_input:
            print(f"{ABU}Silakan tulis pertanyaanmu tentang tani, iklim, atau alam.{RESET}\n")
            continue

        perintah = user_input.lower()

        # ---------- PERINTAH KHUSUS ----------
        if perintah in ("/keluar", "/exit", "keluar", "exit"):
            if len([m for m in messages if m["role"] == "user"]) > 0:
                path = simpan_riwayat(messages)
                print(f"{ABU}Percakapan disimpan ke {path}{RESET}")
            print(f"\n{HIJAU}Sampai jumpa. Semoga panennya berkah.{RESET}\n")
            break

        if perintah in ("/baru", "/clear", "/reset"):
            messages = reset_history()
            print(f"\n{ABU}Riwayat dihapus. Percakapan baru dimulai.{RESET}\n")
            continue

        if perintah in ("/simpan", "/save"):
            path = simpan_riwayat(messages)
            print(f"\n{ABU}Percakapan disimpan ke {path}{RESET}\n")
            continue

        if perintah in ("/muat", "/load"):
            path = pilih_file_riwayat()
            if path:
                messages = muat_riwayat(path)
                jumlah = len([m for m in messages if m["role"] == "user"])
                print(f"\n{ABU}Riwayat dimuat ({jumlah} pertanyaan). "
                      f"Percakapan bisa dilanjutkan.{RESET}\n")
            continue

        if perintah in ("/statistik", "/stats"):
            tampilkan_statistik(messages)
            continue

        if perintah in ("/bantuan", "/help"):
            tampilkan_bantuan()
            continue

        if perintah.startswith("/suhu") or perintah.startswith("/temp"):
            bagian = perintah.split()
            try:
                nilai = float(bagian[1])
                if not 0.0 <= nilai <= 1.5:
                    raise ValueError
                temperature = nilai
                print(f"\n{ABU}Temperature diubah menjadi {temperature}.{RESET}\n")
            except (IndexError, ValueError):
                print(f"\n{TANAH}Format salah. Contoh: /suhu 0.8 (rentang 0.0 - 1.5){RESET}\n")
            continue

        if perintah.startswith("/"):
            print(f"\n{TANAH}Perintah tidak dikenal. Ketik /bantuan untuk daftar perintah.{RESET}\n")
            continue

        # ---------- KIRIM KE LLM ----------
        messages.append({"role": "user", "content": user_input})

        print(f"\n{HIJAU}{TEBAL}JATI  {RESET}> ", end="", flush=True)
        jawaban = ""
        try:
            for potongan in stream_jawaban(messages, temperature=temperature):
                print(potongan, end="", flush=True)
                jawaban += potongan
            print("\n")
        except JatiError as e:
            # Request gagal -> buang pertanyaan tadi supaya history tidak rusak
            messages.pop()
            print(f"\n{TANAH}{e}{RESET}\n")
            continue
        except KeyboardInterrupt:
            print(f"\n{ABU}Jawaban dihentikan.{RESET}\n")
            messages.pop()
            continue

        if jawaban.strip():
            # Simpan jawaban ke history supaya jadi konteks giliran berikutnya
            messages.append({"role": "assistant", "content": jawaban})
        else:
            messages.pop()
            print(f"{TANAH}JATI tidak memberi jawaban. Coba ulangi pertanyaanmu.{RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except JatiError as e:
        print(f"\n{TANAH}{e}{RESET}\n")
