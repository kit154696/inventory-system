# 🏛️ ระบบทะเบียนคุมวัสดุ (Inventory Management System)

ระบบจัดการพัสดุสำหรับหน่วยงานราชการ มี 2 เวอร์ชัน:

1. **🖥️ Desktop App** (Python + PySide6 + SQLite) — **แนะนำ** สำหรับงานราชการทั่วไป ใช้งาน Offline 100%
2. **🌐 Web App** (Node.js + Express + PostgreSQL) — สำหรับ Deploy บน Railway/Render

---

## 📱 Desktop App (Windows) — ใช้งาน Offline

### ⚙️ ความต้องการระบบ
- Windows 10 หรือ 11
- Python 3.11 หรือสูงกว่า → [ดาวน์โหลด Python](https://www.python.org/downloads/)
  - ⚠️ ตอนติดตั้ง Python ให้ติ๊กช่อง **"Add Python to PATH"**

---

### 🚀 วิธีติดตั้งและรัน (Windows)

#### **ขั้นตอนที่ 1: ดาวน์โหลดโปรเจกต์**

**วิธีที่ 1 — ใช้ Git** (แนะนำ)
```cmd
git clone https://github.com/kit154696/inventory-system.git
cd inventory-system\app
```

**วิธีที่ 2 — ดาวน์โหลด ZIP**
1. ไปที่ https://github.com/kit154696/inventory-system
2. กดปุ่ม **Code** (สีเขียว) → **Download ZIP**
3. แตกไฟล์ → เปิด Command Prompt → `cd` เข้าไปในโฟลเดอร์ `inventory-system\app`

---

#### **ขั้นตอนที่ 2: สร้าง Virtual Environment**
```cmd
python -m venv .venv
```

---

#### **ขั้นตอนที่ 3: เปิดใช้งาน Virtual Environment**
```cmd
.venv\Scripts\activate
```
> หลังรันคำสั่งนี้จะเห็น `(.venv)` ขึ้นหน้าบรรทัด

---

#### **ขั้นตอนที่ 4: ติดตั้ง Dependencies**
```cmd
pip install -r requirements.txt
```
> จะติดตั้ง PySide6 (GUI) และ openpyxl (Excel export)

---

#### **ขั้นตอนที่ 5: รันโปรแกรม**
```cmd
python main.py
```

✅ **เสร็จแล้ว!** โปรแกรมจะเปิดขึ้นมา

**ครั้งแรกที่เปิด:**
- จะสร้างฐานข้อมูล SQLite อัตโนมัติที่ `C:\Users\<ชื่อคุณ>\AppData\Roaming\StockApp\data\app.db`
- พร้อม seed ข้อมูลเริ่มต้น **17 ประเภทวัสดุ** และ **433 รายการวัสดุ**

---

### 📦 Build เป็น EXE (ไม่ต้องติดตั้ง Python)

ถ้าต้องการแจกจ่ายให้คนอื่นใช้ โดยไม่ต้องติดตั้ง Python:

```cmd
cd app
build.bat
```

**ผลลัพธ์:** ไฟล์ `.exe` จะอยู่ที่ `dist\StockApp\StockApp.exe`

**วิธีแจกจ่าย:**
- Copy **ทั้งโฟลเดอร์** `dist\StockApp` ไปวางบนเครื่องอื่น
- ดับเบิลคลิก `StockApp.exe` ใช้งานได้เลย (ไม่ต้องติดตั้งอะไรเพิ่ม)

---

### ✨ ฟีเจอร์ Desktop App

#### **Phase 1 — ระบบหลัก**
- ✅ ทะเบียนคุมวัสดุ (เพิ่ม/แก้ไข/ลบ)
- ✅ ค้นหา กรอง เรียงลำดับ
- ✅ บันทึกเอกสารรับเข้า/เบิกจ่าย
- ✅ สร้างเลขที่เอกสารอัตโนมัติ (เช่น `IN-0001/69`)
- ✅ ป้องกันเบิกเกินสต็อก (hard block)
- ✅ รายงานคงเหลือ + บัตรคุมวัสดุ
- ✅ Dashboard สรุปภาพรวม

#### **Phase 2 — Export/Import/Backup**
- ✅ Export ข้อมูล 3 รูปแบบ: **ZIP** (full backup), **JSON**, **CSV**
- ✅ Import พร้อมตรวจสอบความถูกต้อง 10 ขั้นตอน
- ✅ Auto-backup ก่อน Import (เก็บ 10 ฉบับล่าสุด)
- ✅ Restore จาก backup เดิม

#### **Phase 2b — รายงานและการพิมพ์**
- ✅ รายงานรับจ่ายพัสดุประจำปีงบประมาณ (Thai fiscal year)
- ✅ Export Excel พร้อม styling
- ✅ พิมพ์เอกสาร 4 แบบ:
  - บัตรคุมวัสดุ
  - ใบรับพัสดุ
  - ใบเบิกพัสดุ (พร้อมกรอบลงชื่อ)
  - รายงานประจำปี (แนวนอน)
- ✅ Print to PDF ผ่าน "Microsoft Print to PDF"
- ✅ Pagination 50 รายการ/หน้า

#### **UI/UX**
- ✅ ธีมราชการคลาสสิก (น้ำเงิน-ทอง)
- ✅ ฟอนต์ไทย **TH SarabunPSK** ฝังมากับโปรแกรม
- ✅ ขนาดตัวอักษร 12pt อ่านง่าย

---

## 🌐 Web App (Deploy บน Railway/Render)

### ⚙️ ความต้องการ
- Node.js 18+
- PostgreSQL 14+

### 🚀 ติดตั้ง Local

```bash
npm install
cp .env.example .env
# แก้ไข .env ใส่ DATABASE_URL และ SESSION_SECRET
node init-db.js
npm start
```

เปิดเว็บที่ `http://localhost:3000`

### ☁️ Deploy บน Railway

1. สร้าง Project ใหม่บน [Railway](https://railway.app)
2. เลือก **Deploy from GitHub Repo**
3. เพิ่ม **PostgreSQL Database**
4. Add Reference Variable: `DATABASE_URL`
5. Generate Domain → เข้าใช้งาน

**ครั้งแรกเปิด:** ระบบจะสร้างตารางและ seed ข้อมูล 433 รายการอัตโนมัติ

---

## 📂 โครงสร้างโปรเจกต์

```
inventory-system/
├── app/                     # 🖥️ Desktop App (Python/PySide6/SQLite)
│   ├── main.py             # จุดเริ่มต้น
│   ├── requirements.txt    # PySide6==6.10.1, openpyxl==3.1.5
│   ├── build.bat           # Build เป็น .exe
│   ├── database/           # Models, Migrations, Seed data
│   ├── ui/                 # GUI (main_window, dialogs, widgets, theme)
│   ├── services/           # Export, Import, Backup, Print, Report
│   ├── utils/              # Validators, Paths, Thai Date
│   ├── assets/fonts/       # TH SarabunPSK (4 styles)
│   └── packaging/          # stockapp.iss (Inno Setup installer)
│
├── server.js               # 🌐 Web App (Node.js/Express/PostgreSQL)
├── init-db.js              # PostgreSQL schema + seed
├── validators.js           # Validation rules
├── public/                 # Web frontend
│   ├── index.html          # Single-page app
│   ├── login.html
│   └── security-test.html
├── package.json
├── Procfile                # Railway deployment
└── README.md               # คู่มือนี้
```

---

## 🔐 ความปลอดภัยข้อมูล

### Desktop App
- ✅ SQLite **WAL mode** + Foreign Keys enforcement
- ✅ Transaction-based writes (validate → begin → commit/rollback)
- ✅ ฐานข้อมูลอยู่ที่ `%APPDATA%` ไม่ผูกกับโฟลเดอร์โปรแกรม
- ✅ Backup/Export **ไม่มี** hardcoded path, username, computer name
- ✅ **ย้ายเครื่องได้** โดย Export → Import backup file

### Web App
- ✅ bcrypt password hashing
- ✅ express-session
- ✅ Input validation + sanitization
- ✅ SQL injection protection (parameterized queries)

---

## 🆘 แก้ปัญหาที่พบบ่อย

### Desktop App

**Q: กด `python main.py` แล้วขึ้น "python is not recognized"**  
A: ยังไม่ได้ติดตั้ง Python หรือไม่ได้ติ๊ก "Add Python to PATH" ตอนติดตั้ง → ติดตั้ง Python ใหม่แล้วติ๊กช่องนั้น

**Q: กด `.venv\Scripts\activate` แล้วขึ้น error**  
A: ใช้ PowerShell แทน CMD หรือรันคำสั่งนี้ใน CMD:
```cmd
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Q: โปรแกรมเปิดแล้วตัวอักษรไทยแสดงเป็นกล่อง □□□**  
A: ปกติไม่ควรเกิด เพราะโปรแกรมฝังฟอนต์ TH SarabunPSK มาแล้ว — ถ้าเจอให้ปิดโปรแกรมแล้วเปิดใหม่

**Q: ต้องการลบข้อมูลทั้งหมดเริ่มใหม่**  
A: ลบไฟล์ `C:\Users\<ชื่อคุณ>\AppData\Roaming\StockApp\data\app.db` แล้วเปิดโปรแกรมใหม่

---

## 📞 ติดต่อ / รายงานปัญหา

- **GitHub Issues:** https://github.com/kit154696/inventory-system/issues
- **Desktop App README เพิ่มเติม:** `app/README.md`

---

## 📜 License

สำหรับการศึกษาและใช้งานในหน่วยงานราชการ

---

## 🙏 Credits

- Developed with **Claude Code** (Anthropic)
- Thai Font: **TH SarabunPSK** by TLWG
- UI Framework: **PySide6** (Qt for Python)
