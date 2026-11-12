# How Bottle Spray Works

Animasi pompa atomizer (spray botol) yang dibuat dari foto exploded view. Setiap komponen dipotong langsung dari foto, lalu dianimasikan: dirakit, ditekan, menyemprot, dan diurai lagi. Ada juga mode cutaway yang membuat rumah pompa tembus pandang, sehingga bola katup, piston, dan pegas di dalamnya kelihatan bekerja.

Gerakan yang kamu klik di halaman bisa direkam lalu diekspor jadi video overlay transparan (ProRes 4444 `.mov`, 1080×1920) dengan [HyperFrames](https://hyperframes.heygen.com).

## Kebutuhan

- Python 3
- Node.js (untuk `npx hyperframes`)
- ffmpeg (dipakai HyperFrames saat render)

## Cara pakai (Windows)

1. Klik dua kali **`Buka Atomizer.bat`**. Browser terbuka di `http://localhost:8770`. Biarkan jendela hitamnya tetap terbuka.
2. Klik **Rekam**, mainkan animasinya (Rakit, Tekan, Lepas, Semprot 1x, Cutaway, Urai), lalu klik **Stop**.
3. Pilih **Dengan label** atau tidak, lalu klik **Ekspor video**. Progres render ditampilkan di layar.
4. Hasil `.mov` tersimpan di `renders/`, dan catatan rekamannya di `rekaman/`.

Di sistem lain, jalankan `python server.py`.

### Shortcut keyboard

| Tombol | Aksi |
| --- | --- |
| `A` | Rakit |
| `E` | Urai |
| `T` | Tekan |
| `L` | Lepas |
| `Spasi` | Semprot 1x |
| `C` | Foto / Cutaway |

## Render ulang dari catatan rekaman

```bash
python build.py rekaman/contoh.json            # tambah --no-label untuk video tanpa label
npx hyperframes render --format mov --output renders/contoh.mov
```

`build.py` mengubah catatan rekaman jadi `index.html`, yaitu komposisi HyperFrames yang memutar ulang klikmu frame demi frame. Karena itu hasil rendernya selalu sama persis.

## Isi folder

| Path | Isi |
| --- | --- |
| `src/template.html` | Halaman animasi: tombol, mode cutaway, perekam |
| `src/parts.json` | Potongan 10 komponen dari foto (PNG base64) |
| `build.py` | Catatan rekaman → komposisi video |
| `server.py`, `Buka Atomizer.bat` | Server lokal dengan tombol Ekspor video |
| `rekaman/` | Catatan rekaman (`.json`) |
| `renders/` | Hasil video (tidak masuk git) |
