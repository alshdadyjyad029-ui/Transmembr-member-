# 📖 دليل التثبيت الكامل

## المتطلبات الأساسية

### 1. Python 3.8+
```bash
python --version
```

### 2. تحميل المستودع
```bash
git clone https://github.com/alshdadyjyad029-ui/Transmembr-member-.git
cd Transmembr-member-
```

### 3. تثبيت المكتبات
```bash
pip install -r requirements.txt
```

---

## الإعداد

### 1. ملف `.env`
```bash
cp .env.example .env
```

عدّل `.env` مع بيانات تيليجرام الخاصة بك:
```
API_ID=38655746
API_HASH=ec48ce8332c461c86b2bdaa9061c3ec6
BOT_TOKEN=8831112396:AAGLobG5knnoA_JufuJtn7T-Hz_L59v4eDk
OWNER_ID=1516358968
```

### 2. ملف `accounts.json`
أضف حساباتك بالصيغة:
```json
{
  "api_accounts": [
    {
      "api_id": 38655746,
      "api_hash": "ec48ce8332c461c86b2bdaa9061c3ec6",
      "accounts": [
        {
          "phone": "+966501234567",
          "session": "session_1.session",
          "status": "active"
        }
      ]
    }
  ]
}
```

---

## التشغيل

### الطريقة 1: مباشرة
```bash
python bot_main.py
```

### الطريقة 2: Docker
```bash
docker-compose up -d
```

### الطريقة 3: بـ Screen (للخادم)
```bash
screen -S transmembr python bot_main.py
```

---

## التحقق من التشغيل

1. افتح Telegram
2. ابحث عن البوت بـ ID: `8831112396`
3. اكتب `/start`
4. يجب أن تظهر القائمة الرئيسية

---

## حل المشاكل الشائعة

### ❌ خطأ: ModuleNotFoundError
```bash
pip install --upgrade -r requirements.txt
```

### ❌ خطأ: Connection refused
- تأكد من الاتصال بالإنترنت
- تحقق من بيانات API

### ❌ خطأ: Phone number invalid
- استخدم رقم صحيح مع رمز الدولة (+966...)

---

## الدعم

📧 تواصل مع المطور للمساعدة

---

**© 2026 - Transmembr Project**
