# Phisherman

Game edukasi keamanan data (pygame) untuk PKM siswa SMA kelas 11. Pemain berperan sebagai peretas yang mencoba mengelabui AI pendeteksi phishing, sekaligus belajar mengenali pola pesan phishing.

## Menjalankan

```
pip install -r requirements.txt
python main.py
python main.py --model jalur/ke/svc_pipeline.pkl
```

## Model NLP

Model deteksi phishing ada di folder `model/`:
- `model/svc_pipeline.pkl`: pipeline scikit-learn (TF-IDF dan LinearSVC)
- `model/lemmatizer/`: lemmatizer spaCy bawaan tim (spaCy 3.8, en_core_web_sm)
- `model/svc_pipeline_updated.pkl`: dibuat otomatis setelah pelatihan ulang dan dipakai lebih dulu saat game dibuka lagi

Model hanya membaca Subject dan Body email. Teks dibersihkan lalu dilematisasi memakai lemmatizer tersebut (`game/nlp_features.py`), kemudian fitur tautan dalam isi email ikut dihitung seperti saat model dilatih. Skor SVC diubah menjadi probabilitas phishing lewat fungsi sigmoid. Nilai 50 persen atau lebih berarti phishing.

Pasang dependensi sekali saja:

```
pip install -r requirements.txt
```

Tanpa berkas model, game berjalan dalam "Mode demo" memakai penilai kata kunci sederhana agar tetap bisa dicoba.

## Alur permainan

1. Login di laut dalam: dua kertas lecek bertumpuk. Ketik nama pemain (tanpa kata sandi, minimal 3 huruf), lalu Start Mission. Player List membalik kertas belakang (animasi flip dari sudut kiri atas) dan menampilkan statistik serta tombol masuk. Leaderboard Top 5 muncul sebagai popup (tanpa podium bila belum ada pemain). Setelah Mulai Misi, kertas dilahap amplop yang tumbuh menjadi ikan, dikail, lalu ditarik ke permukaan menuju menu utama (klik atau tombol apa saja mempercepat animasi). Fitur flip kertas memakai numpy.
2. Menu utama: Story Mode dan Live Mode.
3. Story Mode: cerita pembuka, tutorial, lima email phishing berbahasa Inggris (subjek, pembuka, isi minimal 25 kata, penutup), lampiran file opsional, analisis AI, lalu ending.
4. Setelah ending: adegan gedung YuBeatEm, kantor keamanan, dan peninjauan lima email oleh analis. Label Phishing atau Legitimate dari pemain dipakai untuk melatih ulang model (human-in-the-loop).
5. Statistik akhir: skor, uang, rincian lima pesan, peringkat, dan tombol papan peringkat.

Penilaian per email:
- Lolos dan lampiran malware (gacha tersembunyi): +250 poin, +$175
- Lolos tanpa bonus: +100 poin, +$100
- Terdeteksi dan malware ikut ketahuan: -150 poin
- Terdeteksi tanpa malware: 0 poin, $0

Data pemain tersimpan di `data/players.json`.

## Mini game tersembunyi

Di menu utama, klik semua ikan amplop yang berenang di laut sampai menyelam. Setelah semuanya hilang, ikan amplop di kail kiri atas bisa diklik dan menarik pemain ke mini game memancing malam hari. Tangkap lima jenis fishmail dari yang umum sampai legendaris dengan menekan SPACE atau klik saat penanda merah berada di zona hijau. Ikan bisa dijual di kotak perkakas (ikon koper di kiri atas) untuk membeli skin border avatar dan spanduk profil yang tampil di Player List. Koleksi, uang, dan skin tersimpan per pemain di data/tackle_box.json.

## Mode uji rule-based (tanpa model)

Untuk menguji alur dan ending sebelum model jadi:

```
python main.py --demo
```

Penilai sementara berbasis aturan. Tambahkan tag ini di bagian mana saja dalam email:
- `#lolos` membuat AI menilai pesan normal (pesan lolos)
- `#tangkap` membuat AI menilai pesan phishing (pesan terdeteksi)
- Tanpa tag, penilaian memakai kata kunci seperti "urgent", "click", "password", atau "account"

Mode ini tidak menulis berkas apa pun ke `data/` atau `model/`, termasuk data pemain. Menang butuh minimal 3 email yang lolos.

## Pelatihan ulang

Pelatihan ulang terjadi saat analis (Story Mode) atau pemain (Live Mode, tombol "AI Wrong, Retrain") mengoreksi label. LinearSVC tidak punya `partial_fit` dan dataset asli tidak ikut dibawa, jadi game memperbarui bobot SVC langsung dengan langkah hinge online:
1. Contoh koreksi diubah menjadi vektor fitur memakai preprocessor model yang sama
2. Bobot dan intersep diperbarui berulang sampai contoh itu terklasifikasi benar, sambil mengulang koreksi sebelumnya dengan bobot lebih kecil agar tidak saling menimpa
3. Pipeline hasil pembaruan disimpan ke `model/svc_pipeline_updated.pkl` di latar belakang dan saat game ditutup
4. Jika pembaruan gagal, koreksi disimpan sebagai memori (pesan yang sangat mirip akan dikoreksi)

Kosakata TF-IDF tetap sama seperti model asli, jadi kata yang belum pernah dilihat model tidak berpengaruh. Setiap koreksi dicatat di `data/feedback.csv` (kolom `subject,body,label,time`) sehingga tim bisa melatih ulang model penuh dari awal bila perlu. Statistik performa disimpan di `data/model_stats.json`. Hapus `model/svc_pipeline_updated.pkl` untuk mengembalikan model ke kondisi awal.

## Kontrol

- Mouse untuk semua tombol, Ctrl+Enter untuk mengirim email, Tab berpindah antara Subject dan Body
- ESC membuka konfirmasi keluar (di layar statistik langsung ke menu utama, di Story Mode progres tidak disimpan)
- Di layar verifikasi: P untuk Phishing, L untuk Legitimate, panah atas dan bawah untuk berpindah email
- Tombol speaker di kiri atas membuka pengaturan suara: bisukan musik atau efek suara terpisah, dan geser slider volume (tersimpan di `data/settings.json`)
- F9 bisukan atau nyalakan semua suara

## Kredit musik

Musik latar: "Heat" oleh Zambolino, disediakan oleh Free To Use Music (https://freetouse.com). Berkas ada di `assets/music/heat.mp3`. Syarat lisensi Free To Use meminta pencantuman kredit, jadi kredit ini dicantumkan di sini dan harus ditampilkan pada materi publikasi game. Periksa kembali ketentuan lisensinya di freetouse.com sebelum game dipublikasikan atau didaftarkan HKI.

Musik mini game memancing: "The Fishing (Free Game Music)" oleh ammitmusics, berkas `assets/music/fishing.mp3`. Efek suara jingle tangkapan: "Memento Mancing Mania" dari QuickSounds.com, berkas `assets/music/mancing_mania.mp3`. Kedua berkas diberikan oleh pengembang game, jadi periksa ketentuan lisensi masing masing sebelum game dipublikasikan.

## Catatan

Semua ilustrasi, ikon, huruf piksel, dan suara dibuat lewat kode (tanpa berkas gambar atau audio luar), dengan satu pengecualian, yaitu musik latar "Heat" (lihat kredit di atas).

Catatan tampilan: seluruh tombol dan teks informasi memakai bahasa Inggris di semua menu, kecuali kotak narasi cerita dan tutorial yang tetap berbahasa Indonesia. ESC di menu utama kembali ke halaman login. Skor ditampilkan dengan ikon bintang di samping uang. Dasar laut di layar login berlapis (bukit jauh, tengah, pasir terdekat) dengan karang aneka bentuk dan rumput laut yang berakar pada tinggi tanah.
