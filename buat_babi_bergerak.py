"""
TUGAS SISTEM MULTIMEDIA - GAMBAR MENJADI BERGERAK DAN BERSUARA
==============================================================
Hewan  : Babi (Sus scrofa domesticus) - karakter "OINKY"
Tema   : Hujan dan lumpur
Input  : oink.mp3            -> rekaman dengusan babi asli "Pig Oinking"
                                (SoundBible.com, Attribution 3.0)
         (tidak ada file gambar - babi digambar prosedural dengan Pillow)
Output : babi_bergerak.mp4  -> video gambar bergerak + bersuara
         babi_suara.wav      -> trek suara rakitan (hujan, petir, dan
                                cipratan disintesis NumPy + oink asli)
         poster.jpg          -> gambar sampul pemutar video

Alur cerita video (11 detik):
  1. Detik 0,0-3,0 : babi BERJALAN di tengah hujan menuju genangan
     lumpur. Kakinya berayun bergantian (walk cycle sederhana),
     badan naik-turun halus mengikuti langkah.
  2. Detik 3,0-9,0 : babi GULING-GULING 360 derajat di dalam
     genangan lumpur. Seluruh lapisan gambar babi diputar pada
     poros tengahnya, posisi bergeser kiri-kanan di genangan,
     cipratan lumpur beterbangan, dan bercak lumpur di badannya
     bertambah setiap putaran.
  3. Detik 9,0-11,0: babi berhenti tegak, belepotan lumpur, lalu
     bersuara "OINK! OINK!" (gelembung teks muncul) dan video
     memudar selesai.

Teknik suara (trek dirakit dengan NumPy):
  - Hujan   : white noise disaring low-pass (one-pole) terus-menerus.
  - Petir   : noise low-pass sangat rendah + gelombang sinus 52 Hz
              yang meluruh, mulai di detik 1,4.
  - Cipratan: burst noise pendek berulang selama fase guling.
  - Oink    : REKAMAN BABI ASLI dari file oink.mp3 (klip "Pig
              Oinking", SoundBible.com), dibaca lewat FFmpeg lalu
              ditempel pada detik 9,15 dan diulang pelan pada 10,2.
              Sintesis gigi gergaji hanya dipakai sebagai cadangan
              bila file tidak ada.

Kebutuhan:
  pip install pillow numpy
  Program FFmpeg harus terinstall (perintah: ffmpeg)

Jalankan:
  python buat_babi_bergerak.py
"""

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Konfigurasi
# ---------------------------------------------------------------------------
FOLDER = Path(__file__).parent
FILE_VIDEO = FOLDER / "babi_bergerak.mp4"
FILE_SUARA = FOLDER / "babi_suara.wav"
FILE_POSTER = FOLDER / "poster.jpg"
FILE_OINK = FOLDER / "oink.mp3"

LEBAR, TINGGI = 1280, 720      # resolusi video (HD 720p)
FPS = 24                       # frame per detik
DURASI = 11                    # durasi video (detik)
TOTAL_FRAME = FPS * DURASI

AKHIR_JALAN = 3.0              # babi berjalan sampai detik ini
AKHIR_GULING = 9.0             # guling-guling sampai detik ini
KECEPATAN_GULING = 190.0       # derajat per detik (sama seperti versi web)

INK = (59, 43, 47)
PINK = (255, 179, 194)
PINK_TUA = (255, 143, 171)
PINK_KAKI_JAUH = (232, 122, 149)
LUMPUR = (124, 74, 33)
LUMPUR_GELAP = (111, 69, 31)

try:
    FONT_GELEMBUNG = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
except OSError:
    FONT_GELEMBUNG = ImageFont.load_default()


# ---------------------------------------------------------------------------
# Langkah 1 - Sintesis suara (WAV) dengan NumPy
# ---------------------------------------------------------------------------
def lowpass(x, alpha):
    """Filter low-pass one-pole sederhana."""
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def buat_suara(path_wav):
    sr = 22050
    n = sr * DURASI
    rng = np.random.default_rng(20261022)
    audio = np.zeros(n, dtype=np.float64)
    t = np.arange(n) / sr

    # Hujan terus-menerus: white noise low-pass pelan
    hujan = lowpass(rng.uniform(-1, 1, n), 0.10) * 0.55
    audio += hujan

    def tambah(segmen, mulai_detik):
        mulai = int(mulai_detik * sr)
        akhir = min(n, mulai + len(segmen))
        if mulai < n:
            audio[mulai:akhir] += segmen[:akhir - mulai]

    # Petir di detik 1,4: gemuruh rendah 2 detik
    dur = int(2.0 * sr)
    tt = np.arange(dur) / sr
    gemuruh = lowpass(rng.uniform(-1, 1, dur), 0.02) * np.exp(-tt * 2.2) * 2.4
    gemuruh += np.sin(2 * np.pi * 52 * tt) * np.exp(-tt * 2.6) * 0.5
    tambah(gemuruh, 1.4)

    # Cipratan lumpur selama guling: burst tiap 0,5 detik mulai 3,2
    dur_c = int(0.16 * sr)
    tt_c = np.arange(dur_c) / sr
    for mulai_c in np.arange(3.2, 8.9, 0.5):
        burst = lowpass(rng.uniform(-1, 1, dur_c), 0.30) * np.exp(-tt_c * 22) * 1.1
        tambah(burst, float(mulai_c))

    # Oink: rekaman babi asli (oink.mp3) dibaca lewat FFmpeg menjadi PCM
    def muat_oink():
        if not FILE_OINK.exists():
            return None
        hasil = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(FILE_OINK),
             "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
            capture_output=True)
        if hasil.returncode != 0 or not hasil.stdout:
            return None
        return np.frombuffer(hasil.stdout, dtype=np.float32).astype(np.float64)

    klip_oink = muat_oink()
    if klip_oink is not None:
        tambah(klip_oink * 0.95, 9.15)   # "OINK! OINK!" utama
        tambah(klip_oink * 0.7, 10.2)    # pengulangan pelan sebelum fade-out
    else:
        # Cadangan bila oink.mp3 tidak ada: oink sintesis sawtooth anjlok
        def oink_sintesis(mulai_o, nada_awal):
            dur_o = int(0.17 * sr)
            tt_o = np.arange(dur_o) / sr
            freq = nada_awal * np.exp(np.log(90 / nada_awal) * tt_o / 0.16)
            fase = np.cumsum(2 * np.pi * freq / sr)
            gelombang = 2 * (fase / (2 * np.pi) - np.floor(fase / (2 * np.pi) + 0.5))
            env = np.exp(-tt_o * 14) * np.minimum(1, tt_o * 60)
            tambah(lowpass(gelombang, 0.45) * env * 0.9, mulai_o)

        oink_sintesis(9.15, 258)
        oink_sintesis(9.42, 292)
        oink_sintesis(10.15, 258)

    # Normalisasi dan simpan sebagai WAV 16-bit
    puncak = np.max(np.abs(audio))
    if puncak > 0:
        audio = audio / puncak * 0.85
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(str(path_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    print(f"Suara ditulis: {path_wav.name} ({DURASI} detik, {sr} Hz)")


# ---------------------------------------------------------------------------
# Langkah 2 - Gambar babi sebagai satu lapisan RGBA
# Koordinat mengikuti viewBox SVG versi web (380 x 270), diskala 1,5x.
# ---------------------------------------------------------------------------
SKALA = 1.5


def s(v):
    return v * SKALA


def gambar_kaki(warna, kuku):
    """Satu kaki sebagai gambar kecil, siap diputar pada pangkalnya."""
    img = Image.new("RGBA", (int(s(36)), int(s(66))), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([s(4), 0, s(31), s(52)], radius=s(12), fill=warna)
    d.rounded_rectangle([s(2), s(46), s(33), s(60)], radius=s(6), fill=kuku)
    return img


def tempel_kaki(base, kaki_img, x_poros, y_poros, sudut_deg):
    """Tempel kaki dengan poros putar di pangkal atas kaki.

    Kaki ditempel dulu pada lapisan transparan sebesar badan, lalu
    lapisan itu diputar dengan titik pusat persis di pangkal kaki -
    cara yang sama seperti memutar kaki boneka animasi 2D.
    """
    lapisan = Image.new("RGBA", base.size, (0, 0, 0, 0))
    lapisan.alpha_composite(kaki_img, (int(x_poros - kaki_img.width / 2),
                                       int(y_poros)))
    lapisan = lapisan.rotate(sudut_deg, resample=Image.BICUBIC,
                             center=(x_poros, y_poros))
    base.alpha_composite(lapisan)


def gambar_babi(sudut_kaki=0.0, tingkat_lumpur=10, senang=False):
    """Gambar babi utuh (tanpa rotasi guling) sebagai lapisan RGBA."""
    W, H = int(s(380)), int(s(270))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    kaki_jauh = gambar_kaki(PINK_KAKI_JAUH, (93, 64, 55))
    kaki_dekat = gambar_kaki(PINK_TUA, (78, 52, 46))

    # Kaki jauh (belakang badan)
    tempel_kaki(img, kaki_jauh, s(110), s(184), -sudut_kaki)
    tempel_kaki(img, kaki_jauh, s(242), s(184), sudut_kaki)

    # Ekor keriting
    d.arc([s(18), s(62), s(62), s(116)], start=90, end=430,
          fill=PINK_KAKI_JAUH, width=int(s(7)))
    d.line([s(56), s(112), s(66), s(118)], fill=PINK_KAKI_JAUH, width=int(s(7)))

    # Badan
    d.ellipse([s(57), s(58), s(313), s(222)], fill=PINK, outline=INK, width=5)

    # Kaki dekat (di depan badan)
    tempel_kaki(img, kaki_dekat, s(143), s(190), sudut_kaki)
    tempel_kaki(img, kaki_dekat, s(273), s(190), -sudut_kaki)

    # Bercak lumpur di badan (muncul bertahap sesuai tingkat_lumpur)
    bercak = [
        (5, 120, 168, 26, 14), (25, 205, 102, 20, 11), (45, 168, 182, 30, 15),
        (65, 96, 122, 17, 10), (82, 238, 152, 24, 13),
    ]
    for ambang, cx, cy, rx, ry in bercak:
        if tingkat_lumpur >= ambang:
            d.ellipse([s(cx - rx), s(cy - ry), s(cx + rx), s(cy + ry)],
                      fill=LUMPUR + (225,))

    # Telinga
    d.polygon([(s(262), s(48)), (s(300), s(24)), (s(306), s(44)),
               (s(284), s(54)), (s(276), s(66))],
              fill=PINK_TUA, outline=INK, width=4)

    # Kepala
    d.ellipse([s(232), s(38), s(352), s(158)], fill=PINK, outline=INK, width=5)
    if tingkat_lumpur >= 55:
        d.ellipse([s(249), s(58), s(275), s(74)], fill=LUMPUR + (225,))

    # Pipi
    d.ellipse([s(261), s(109), s(283), s(123)], fill=(255, 157, 180, 200))

    # Mata: titik biasa, atau lengkung senang saat guling/oink
    if senang:
        d.arc([s(279), s(74), s(303), s(94)], start=200, end=340,
              fill=INK, width=6)
    else:
        d.ellipse([s(285), s(78), s(298), s(91)], fill=INK)

    # Moncong + lubang hidung
    d.ellipse([s(305), s(87), s(359), s(129)], fill=PINK_TUA, outline=INK, width=5)
    d.ellipse([s(320), s(103), s(329), s(112)], fill=(161, 61, 85))
    d.ellipse([s(336), s(103), s(345), s(112)], fill=(161, 61, 85))
    return img


# ---------------------------------------------------------------------------
# Langkah 3 - Latar panggung (digambar sekali, dipakai ulang)
# ---------------------------------------------------------------------------
def gambar_latar():
    # Gradasi langit badai (vertikal) dengan NumPy
    atas = np.array([95, 124, 166], dtype=float)
    bawah = np.array([168, 191, 151], dtype=float)
    grad = np.linspace(0, 1, TINGGI)[:, None, None]
    susunan = (atas * (1 - grad) + bawah * grad).astype(np.uint8)
    susunan = np.repeat(susunan, LEBAR, axis=1)
    img = Image.fromarray(susunan, "RGB").convert("RGBA")
    d = ImageDraw.Draw(img)

    # Awan badai (tumpukan lingkaran supaya terlihat mengembang)
    for cx, cy, w in [(210, 84, 300), (760, 56, 380), (1130, 106, 260)]:
        awan = (84, 104, 127)
        d.ellipse([cx - w // 2, cy - 26, cx + w // 2, cy + 30], fill=awan)
        d.ellipse([cx - w // 3, cy - 56, cx - w // 12, cy + 6], fill=awan)
        d.ellipse([cx - w // 10, cy - 68, cx + w // 5, cy + 2], fill=awan)
        d.ellipse([cx + w // 7, cy - 46, cx + w // 3, cy + 8], fill=awan)

    # Pagar kayu
    d.rectangle([0, 512, LEBAR, 526], fill=(164, 113, 58))
    d.rectangle([0, 545, LEBAR, 559], fill=(164, 113, 58))
    for x in [90, 420, 750, 1080]:
        d.rectangle([x, 492, x + 26, 582], fill=(181, 127, 69))

    # Rumput
    d.rectangle([0, 576, LEBAR, TINGGI], fill=(96, 128, 66))
    d.rectangle([0, 576, LEBAR, 596], fill=(125, 160, 94))

    # Genangan lumpur besar
    d.ellipse([166, 566, 1114, 706], fill=LUMPUR_GELAP)
    d.ellipse([196, 576, 1084, 694], fill=(138, 90, 43))
    d.ellipse([330, 596, 950, 678], fill=(160, 106, 53))
    return img


def gambar_hujan(d, frame):
    """Tetesan hujan miring; posisi y bergeser tiap frame (jatuh)."""
    rng = np.random.default_rng(7)
    xs = rng.integers(0, LEBAR, 120)
    ys = rng.integers(0, 560, 120)
    for x, y0 in zip(xs, ys):
        y = (int(y0) + frame * 30) % 580
        d.line([x, y, x - 5, y + 17], fill=(215, 238, 255, 210), width=3)


def gambar_cipratan(d, frame, cx):
    """Lumpur beterbangan di sekitar genangan selama guling."""
    rng = np.random.default_rng(frame * 3 + 11)
    for _ in range(16):
        x = cx + rng.integers(-300, 300)
        y = 622 + rng.integers(-38, 30)
        r = int(rng.integers(3, 10))
        d.ellipse([x - r, y - r, x + r, y + r], fill=LUMPUR + (230,))


# ---------------------------------------------------------------------------
# Langkah 4 - Render semua frame -> MP4 lewat FFmpeg
# ---------------------------------------------------------------------------
def render_video():
    latar = gambar_latar()
    perintah = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{LEBAR}x{TINGGI}", "-r", str(FPS), "-i", "-",
        "-i", str(FILE_SUARA),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(FILE_VIDEO),
    ]
    proses = subprocess.Popen(perintah, stdin=subprocess.PIPE,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    poster_disimpan = False
    try:
        for frame in range(TOTAL_FRAME):
            t = frame / FPS
            kanvas = latar.copy()
            d = ImageDraw.Draw(kanvas, "RGBA")
            gambar_hujan(d, frame)

            if t < AKHIR_JALAN:
                # Fase jalan: masuk dari kiri ke tengah genangan
                kemajuan = t / AKHIR_JALAN
                cx = 300 + (640 - 300) * (1 - (1 - kemajuan) ** 2)
                ayun = math.sin(t * 7) * 22
                babi = gambar_babi(sudut_kaki=ayun, tingkat_lumpur=10)
                bob = -abs(math.sin(t * 7)) * 7
                kanvas.alpha_composite(babi, (int(cx - babi.width / 2), int(352 + bob)))
            elif t < AKHIR_GULING:
                # Fase guling-guling di lumpur
                tg = t - AKHIR_JALAN
                sudut = tg * KECEPATAN_GULING
                rad = math.radians(sudut)
                putaran = sudut / 360
                lumpur = min(96, 10 + int(putaran * 30))
                babi = gambar_babi(sudut_kaki=math.sin(t * 26) * 26,
                                   tingkat_lumpur=lumpur, senang=True)
                muter = babi.rotate(-sudut, resample=Image.BICUBIC,
                                    center=(babi.width / 2, babi.height / 2))
                cx = 640 + math.sin(rad) * 46
                bob = -abs(math.sin(rad)) * 13
                kanvas.alpha_composite(muter, (int(cx - muter.width / 2), int(352 + bob)))
                gambar_cipratan(d, frame, 640)
            else:
                # Fase oink: tegak, belepotan, gelembung teks
                babi = gambar_babi(sudut_kaki=0, tingkat_lumpur=96, senang=True)
                kanvas.alpha_composite(babi, (640 - babi.width // 2, 352))
                if t > 9.1:
                    d.rounded_rectangle([338, 168, 700, 248], radius=26,
                                        fill=(255, 255, 255), outline=INK, width=5)
                    d.polygon([(430, 248), (452, 248), (446, 276)], fill=(255, 255, 255))
                    d.text((368, 186), "OINK! OINK!", font=FONT_GELEMBUNG, fill=INK)

            # Fade-out 0,7 detik terakhir
            if t > DURASI - 0.7:
                alpha = int(255 * (t - (DURASI - 0.7)) / 0.7)
                hitam = Image.new("RGBA", (LEBAR, TINGGI), (0, 0, 0, alpha))
                kanvas.alpha_composite(hitam)

            rgb = kanvas.convert("RGB")
            if not poster_disimpan and t >= 6.0:
                rgb.save(FILE_POSTER, quality=90)
                poster_disimpan = True
            proses.stdin.write(rgb.tobytes())
            if frame % 48 == 0:
                print(f"  frame {frame}/{TOTAL_FRAME}")
    finally:
        proses.stdin.close()
        proses.wait()
    print(f"Video ditulis: {FILE_VIDEO.name}")


def main():
    if subprocess.run(["ffmpeg", "-version"], capture_output=True).returncode != 0:
        sys.exit("FFmpeg tidak ditemukan. Install dulu: https://ffmpeg.org")
    buat_suara(FILE_SUARA)
    render_video()
    print("Selesai!")


if __name__ == "__main__":
    main()
