FROM python:3.11-slim

WORKDIR /app

# تثبيت المتطلبات النظام
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# نسخ المتطلبات
COPY requirements.txt .

# تثبيت المكتبات Python
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الملفات
COPY . .

# تشغيل البوت
CMD ["python", "bot_main.py"]
