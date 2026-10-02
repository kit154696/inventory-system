# StockApp — ระบบทะเบียนคุมวัสดุ (Desktop Edition)

แอปพลิเคชัน Desktop สำหรับ Windows ที่พอร์ตมาจากระบบทะเบียนคุมวัสดุเวอร์ชันเว็บ (Node.js + PostgreSQL) ให้ทำงาน **แบบ Offline 100%** โดยใช้ SQLite เป็นฐานข้อมูลภายในเครื่อง ไม่ต้องพึ่งพา Server หรือ Internet

## เทคโนโลยี

- Python 3.11+
- PySide6 (GUI)
- SQLite (ผ่าน `sqlite3` มาตรฐานของ Python)
- PyInstaller (Build เป็น `.exe`)

## โครงสร้างโปรเจกต์

```text
app/
├── main.py                 # จุดเริ่มต้นโปรแกรม
├── database/
│   ├── database.py         # การเชื่อมต่อ SQLite + transaction helper
│   ├── models.py           # Repository (Item/Transaction/Report/Settings)
│   ├── migrations.py       # สร้างตาราง + seed ข้อมูลเริ่มต้น (17 ประเภท, 433 รายการ)
│   └── seed_data.py        # ข้อมูลตั้งต้น (พอร์ตจาก init-db.js เดิม)
├── ui/
│   ├── main_window.py      # Sidebar + หน้าหลัก
│   ├── dialogs/            # หน้าต่าง เพิ่ม/แก้ไข วัสดุ, บันทึกเอกสาร, เลือกวัสดุ
│   └── widgets/            # หน้า Dashboard/ทะเบียนวัสดุ/เอกสาร/รายงาน/ตั้งค่า
├── utils/
│   ├── paths.py            # หาตำแหน่ง %APPDATA% แบบไม่ผูกเครื่อง
│   └── validators.py       # กฎตรวจสอบข้อมูล (พอร์ตจาก validators.js เดิม)
├── services/
│   ├── backup_service.py   # สร้าง/กู้คืน Snapshot ฐานข้อมูล + จำกัดจำนวนไฟล์สำรอง
│   ├── export_service.py   # Export เป็น ZIP / JSON / CSV
│   └── import_service.py   # ตรวจสอบ + นำเข้าไฟล์ Backup (10 ขั้นตอนตามสเปก)
├── assets/fonts/           # ฟอนต์ไทย TH Sarabun ที่ฝังไปกับโปรแกรม
├── data/                   # ใช้เฉพาะตอนรันจาก source บนเครื่อง dev (ไม่ใช่ตำแหน่งจริงของ DB)
├── packaging/
│   └── stockapp.iss        # Inno Setup script สำหรับสร้าง Windows Installer (ทางเลือก)
├── requirements.txt
├── build.bat
└── README.md
```

## ตำแหน่งฐานข้อมูล

โปรแกรมที่ Build แล้วจะเก็บฐานข้อมูลไว้ที่ `%APPDATA%\StockApp\data\app.db` เสมอ (ไม่เก็บไว้ในโฟลเดอร์เดียวกับ `.exe`) เพื่อเลี่ยงปัญหา Permission ของ Windows และให้สามารถ Backup/ย้ายเครื่องได้ในอนาคต (ดูหัวข้อ Phase 2)

## การรันบนเครื่อง Dev

```powershell
cd app
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## การ Build เป็น .exe (Windows เท่านั้น)

```powershell
cd app
build.bat
```

ผลลัพธ์: `dist\StockApp\StockApp.exe` (แบบ One-Folder — เลือกแบบนี้เพราะเปิดเร็วกว่าและ debug ง่ายกว่า One-File ซึ่งต้อง extract ไฟล์ใหม่ทุกครั้งที่เปิดโปรแกรม)

> **หมายเหตุ**: สคริปต์นี้ถูกเตรียมไว้ให้ แต่ยังไม่ได้ทดสอบการ build จริงบน Windows (พัฒนาบน macOS) — กรุณารัน `build.bat` บนเครื่อง Windows 10/11 เพื่อยืนยันว่า build ผ่านและ `.exe` เปิดได้ปกติ

## ฟอนต์ภาษาไทย

โฟลเดอร์ `assets/fonts/` มีฟอนต์ TH Sarabun (Regular/Bold/Italic/BoldItalic) ฝังไปกับโปรแกรมแล้ว โหลดผ่าน `QFontDatabase.addApplicationFont()` ใน `main.py` — ไม่ต้องพึ่งฟอนต์ไทยที่ติดตั้งในเครื่อง Windows

## Phase 1

- ฐานข้อมูล SQLite + Migration ที่ seed 17 ประเภทวัสดุ และ 433 รายการวัสดุตั้งต้น (พอร์ตจากเว็บเดิม)
- CRUD ทะเบียนคุมวัสดุ พร้อมค้นหา/กรองตามประเภท
- บันทึกเอกสารรับเข้า/เบิกจ่าย พร้อมสร้างเลขที่เอกสารอัตโนมัติ (`IN-0001/69` ตามปีงบประมาณไทย)
- ระบบเบิกจ่ายจะ**ปฏิเสธ**รายการที่ทำให้ยอดคงเหลือติดลบ (ตรวจสอบก่อนบันทึกเสมอ)
- รายงานคงเหลือ + บัตรคุมวัสดุ (Stockcard) รายตัว
- Dashboard สรุปภาพรวม (จำนวนวัสดุ, มูลค่ารวม, รายการใกล้หมด, เอกสารปีงบประมาณนี้)

## Phase 2

เข้าถึงได้จากหน้า **ตั้งค่า** ในโปรแกรม:

- **Export ข้อมูล** — เลือกได้ 3 รูปแบบ:
  - **ZIP Backup** (`stockapp_backup_YYYY-MM-DD.zip`) — มี `database.db` + `metadata.json` (app_name, version, database_version, export_date, format_version) + `README.txt` — ใช้สำหรับย้ายข้อมูลไปเครื่องอื่นหรือกู้คืนทั้งหมด
  - **JSON** — ข้อมูลทั้งฐาน (settings/categories/items/transactions พร้อม lines) ในไฟล์เดียว
  - **CSV** — แยกไฟล์ตามตาราง (`categories.csv`, `items.csv`, `transactions.csv`, `transaction_lines.csv`, `settings.csv`)
- **Import ข้อมูล** — เลือกไฟล์ ZIP Backup แล้วระบบจะ:
  1. ตรวจว่าเป็นไฟล์ Backup ของโปรแกรมนี้จริง (ชื่อแอป, format_version)
  2. ตรวจโครงสร้างตารางและความสมบูรณ์ของฐานข้อมูล (`PRAGMA integrity_check`, `foreign_key_check`)
  3. แสดงตัวอย่างจำนวนข้อมูลที่จะนำเข้า ให้ผู้ใช้ยืนยันก่อนเขียนทับ
  4. สำรองข้อมูลปัจจุบันไว้อัตโนมัติก่อนนำเข้าเสมอ
  5. หากเกิดข้อผิดพลาดระหว่างนำเข้า จะกู้คืนข้อมูลเดิมให้อัตโนมัติ
  6. หลังนำเข้าสำเร็จ โปรแกรมจะปิดตัวลง (ให้เปิดใหม่เพื่อโหลดข้อมูลล่าสุด)
- **สำรองข้อมูลทันที** — สร้างไฟล์ Snapshot ที่ `%APPDATA%\StockApp\backup\auto_backup_<เวลา>.db` เก็บย้อนหลังสูงสุด 10 ไฟล์ล่าสุด (เก่ากว่านั้นลบอัตโนมัติ) — ดูรายการและกู้คืนได้จากหน้าตั้งค่า (คลิกขวาที่รายการ)

**ความเข้ากันได้ระหว่างเครื่อง**: ไฟล์ Export ทั้งหมดไม่มีการอ้างอิงชื่อเครื่อง, ชื่อผู้ใช้ Windows, drive letter หรือ path เฉพาะเครื่องใดๆ — สามารถคัดลอกไปเครื่องอื่นแล้ว Import ได้ทันที

## Windows Installer (ทางเลือก)

`packaging/stockapp.iss` เป็นสคริปต์ [Inno Setup](https://jrsoftware.org/isinfo.php) สำหรับสร้างตัวติดตั้ง — ต้องติดตั้ง Inno Setup บนเครื่อง build เอง (ไม่ได้รวมมาใน `build.bat` เพราะเป็นเครื่องมือคนละตัว):

```powershell
cd app
build.bat
iscc packaging\stockapp.iss
```

ผลลัพธ์: `packaging\output\StockAppSetup.exe` — ตัวติดตั้งจะไม่ลบข้อมูลใน `%APPDATA%\StockApp` ตอน Uninstall เพื่อให้ข้อมูลและไฟล์สำรองยังอยู่หากติดตั้งใหม่ในอนาคต

> **หมายเหตุ**: ส่วน Export/Import/Backup และ `.iss` นี้ทดสอบ logic ผ่าน Python โดยตรงบน macOS แล้ว (ครอบคลุมทุก validation path) แต่ยังไม่เคยรันจริงผ่าน Inno Setup หรือบนเครื่อง Windows — กรุณาทดสอบอีกครั้งบนเครื่อง Windows จริง
