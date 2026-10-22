# Babi Bergerak dan Bersuara — OINKY si Babi Lumpur (Python + Web)

Tugas Individu 4 Sistem Multimedia (UTS mirip): membuat proyek multimedia
dari karakter hewan yang ditentukan — **babi** — dengan alur proses
Gambar (Visual), Suara (Audio), dan Gerak (Animasi). Tema: **hujan dan
lumpur**, dengan gerak khas babi **guling-guling di genangan lumpur**.

**Halaman tugas (GitHub Pages):** https://wisnunot.github.io/babi-bergerak/

Tampilan halamannya bertema **Minecraft** (font pixel Press Start 2P, latar tanah/dirt, tombol blok 3D ala GUI Minecraft, panel status ala hearts/XP bar, kartu penjelasan bata batu 2 kolom, bingkai panggung grass block) — sementara karakter, animasi, dan dunianya tetap babi hujan & lumpur.

Halamannya interaktif: babi berjalan santai di tengah hujan, klik babinya
atau tekan `Spasi` untuk bersuara "oink", tombol **Guling-guling** (`G`)
membuatnya berputar 360° di genangan lumpur — setiap putaran menambah
Meter Kotor, Meter Bahagia, dan penghitung gulingan sampai jadi
"Babi Lumpur Legendaris". Ada juga tombol Petir (`P`), tombol Mandikan
(`M`), slider kecepatan, intensitas hujan (turunkan ke 0% untuk melihat
pelangi), dan volume. Suara babinya adalah **rekaman babi asli** — klip
“Pig Oinking” dari SoundBible.com (lisensi Attribution 3.0), dengusan
ganda jarak dekat yang jernih — yang **tertanam sebagai data URI di dalam
`index.html`**, jadi tidak tergantung file terpisah (file `oink.mp3`-nya
tetap disertakan untuk versi Python dan unduhan). Rekaman diputar lewat
HTML5 Audio yang dihubungkan ke Web Audio API (MediaElementSource), jadi
equalizer di pojok panggung tetap bergerak mengikuti suara lewat
AnalyserNode, dan hujan otomatis diredupkan sesaat setiap oink berbunyi.
Suara cuaca (hujan, cipratan, petir) disintesis langsung dengan Web Audio API.

Di halaman yang sama ada juga versi video MP4 hasil program Python.

Isi repo:
- `index.html` — halaman GitHub Pages interaktif (babi digambar sebagai SVG berlapis)
- `oink.mp3` — suara oink: rekaman “Pig Oinking” (SoundBible.com, Attribution 3.0); juga tertanam sebagai data URI di `index.html`
- `jerit.mp3` — jerit bahagia: potongan rekaman yang sama, dinaikkan nadanya; juga tertanam di `index.html`
- `buat_babi_bergerak.py` — program Python pembuat video
- `babi_bergerak.mp4` — video hasil program Python (11 detik, 720p)
- `babi_suara.wav` — trek suara video: hujan/petir/cipratan disintesis NumPy + oink asli dari `oink.mp3`
- `poster.jpg` — gambar sampul pemutar video

Menjalankan ulang program video:
```
pip install pillow numpy
python buat_babi_bergerak.py
```
(FFmpeg harus terinstall.)

Wisnu Septa Harianto Putra — NIM 242502040041 — Kelas 3TI01
