# استخدم صورة Python خفيفة وآمنة
FROM python:3.10-slim

# عشان تمنع المشاكل في locale (خاصة مع التعامل مع الملفات)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# إنشاء مجلد التطبيق وتحديده كـ working dir
WORKDIR /app

# نسخ requirements فقط أولاً لتحسين caching
COPY requirements.txt .

# تثبيت التبعيات مع إزالة الكاش
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# فتح البورت المطلوب
EXPOSE 8000

# أمر التشغيل
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
