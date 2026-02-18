# 🤖 Bot Berita Nasional Indonesia — Azure Functions

Bot Telegram otomatis berbasis **Azure Functions Timer Trigger** (Consumption Plan) yang mengirim berita terbaru dari **17 RSS Feed** sumber berita Indonesia, mencakup: Nasional, Politik, Hukum, Teknologi, Ekonomi, Pendidikan, dan Startup.

> ✅ Scale to zero — tidak ada biaya saat tidak berjalan  
> ✅ Anti-duplikat via Azure Table Storage (persisten)  
> ✅ Dipanggil otomatis setiap 15 menit oleh Azure  

---

## 📰 Sumber Berita (17 Feed)

| Sumber | Kategori |
|---|---|
| 🇮🇩 Antara - Top News | Nasional |
| 🏛️ Antara - Politik | Politik |
| ⚖️ Antara - Hukum | Hukum |
| 📰 Antara - Terkini | Terkini |
| 💻 Antara - Tekno | Teknologi |
| 🎓 Antara - Humaniora | Pendidikan |
| 🌐 CNN Indonesia - Nasional | Nasional |
| 💻 CNN Indonesia - Teknologi | Teknologi |
| 📊 CNBC Indonesia - News | Ekonomi |
| 📈 CNBC Indonesia - Market | Pasar/Saham |
| 🔬 CNBC Indonesia - Tech | Ekonomi Digital |
| ⏰ Tempo - Nasional | Nasional |
| 📋 Republika - Nasional | Nasional |
| 🔴 Detik - Berita Utama | Nasional |
| 📱 Suara.com - Tekno | Teknologi |
| 🚀 DailySocial | Startup & Tech |
| 💰 Kontan - Keuangan | Keuangan |
| 🎓 Okezone - Edukasi | Pendidikan |

---

## 📁 Struktur File

```
nationalInformation/
├── function_app.py       ← Entry point Azure Functions (Timer Trigger)
├── config.py             ← Semua konfigurasi & RSS feeds
├── fetcher.py            ← Parser RSS + ekstrak gambar
├── database.py           ← Azure Table Storage (anti-duplikat)
├── bot.py                ← Runner lokal (opsional, bukan untuk Azure)
├── host.json             ← Konfigurasi Azure Functions runtime
├── local.settings.json   ← Konfigurasi lokal (JANGAN di-commit)
├── requirements.txt
├── .env.example          ← Template variabel lingkungan
├── .gitignore
└── README.md
```

---

## 🚀 Deploy ke Azure Functions

### Prasyarat

```bash
# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login Azure
az login
```

### Langkah 1 — Buat Resources di Azure Portal

1. **Storage Account**: Portal Azure → Storage Accounts → Create  
   _Tier: Standard, Redundancy: LRS (termurah)_

2. **Function App**: Portal Azure → Function App → Create  
   - **Hosting**: **Consumption** ✅  
   - **Runtime stack**: Python 3.11  
   - **Region**: Southeast Asia (terdekat ke Indonesia)  
   - **Storage Account**: gunakan yang dibuat di atas

3. Setelah Function App dibuat, catat:
   - **Connection String** Storage Account: `Portal → Storage Account → Access keys → Connection string`

### Langkah 2 — Set Application Settings di Azure

Di Portal Azure → Function App → **Configuration** → **Application settings**, tambahkan:

| Key | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | `token dari @BotFather` |
| `TELEGRAM_CHANNEL_ID` | `@nama_channel` |
| `AZURE_STORAGE_CONNECTION_STRING` | `connection string storage account` |
| `TABLE_NAME` | `SentArticles` |
| `MAX_ARTICLES_PER_FEED` | `3` |

Klik **Save**.

### Langkah 3 — Deploy via VS Code (Cara Termudah)

1. Install ekstensi **Azure Functions** di VS Code
2. Login ke Azure di VS Code (ikon Azure di sidebar)
3. Klik kanan pada folder project → **Deploy to Function App...**
4. Pilih Function App yang sudah dibuat

### Langkah 3 (Alternatif) — Deploy via Azure CLI

```bash
cd /home/fahmi/Documents/nationalInformation

# Install dependencies ke folder local
pip install -r requirements.txt --target=".python_packages/lib/site-packages"

# Deploy
func azure functionapp publish NAMA_FUNCTION_APP_ANDA --python
```

---

## 🧪 Test Lokal

### Install dependencies

```bash
pip install -r requirements.txt
```

### Isi konfigurasi lokal

Edit `local.settings.json`:
```json
{
  "Values": {
    "TELEGRAM_BOT_TOKEN": "token_anda",
    "TELEGRAM_CHANNEL_ID": "@channel_anda",
    "AZURE_STORAGE_CONNECTION_STRING": "connection_string_anda",
    "TABLE_NAME": "SentArticles"
  }
}
```

### Jalankan lokal

```bash
func start
```

---

## ⚙️ Variabel Konfigurasi

| Variable | Wajib | Default | Keterangan |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Token dari @BotFather |
| `TELEGRAM_CHANNEL_ID` | ✅ | — | ID channel/group tujuan |
| `AZURE_STORAGE_CONNECTION_STRING` | ✅ | — | Dari Storage Account → Access keys |
| `TABLE_NAME` | — | `SentArticles` | Nama tabel Azure Table Storage |
| `MAX_ARTICLES_PER_FEED` | — | `3` | Maks artikel baru per feed per siklus |

---

## 📊 Estimasi Biaya Azure (Consumption Plan)

| Komponen | Estimasi |
|---|---|
| Azure Functions | **Gratis** (1 juta invocation/bulan gratis) |
| Azure Storage (Table) | < **$0.01/bulan** (data kecil) |
| **Total** | **Hampir $0** |

Dengan interval 15 menit → ~2.880 invocation/bulan, masih jauh di bawah kuota gratis.

