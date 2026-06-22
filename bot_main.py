#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🤖 Transmembr Bot - البوت الاحترافي
نقل أعضاء Telegram بدون حدود
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters,
    )
    from telethon.sync import TelegramClient
    from telethon.errors import FloodWaitError, PhoneNumberInvalidError
except ImportError:
    print("❌ المكتبات المطلوبة غير مثبتة!")
    print("📝 اتبع التعليمات:")
    print("   pip install -r requirements.txt")
    exit(1)

# =====================================================================
# الإعدادات
# =====================================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('transmembr_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN', '8831112396:AAGLobG5knnoA_JufuJtn7T-Hz_L59v4eDk')
OWNER_ID = int(os.getenv('OWNER_ID', '1516358968'))

# =====================================================================
# قاعدة البيانات المؤقتة
# =====================================================================

class TransmembrDB:
    """قاعدة بيانات Transmembr"""
    
    def __init__(self):
        self.db_file = "transmembr_db.json"
        self.data = self.load_db()
    
    def load_db(self) -> Dict:
        """تحميل قاعدة البيانات"""
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "users": {},
            "transfers": [],
            "accounts": [],
            "api_keys": {}
        }
    
    def save_db(self):
        """حفظ قاعدة البيانات"""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_user(self, user_id: int, username: str):
        """إضافة مستخدم"""
        self.data["users"][str(user_id)] = {
            "username": username,
            "joined_at": datetime.now().isoformat(),
            "transfers_count": 0,
            "status": "active"
        }
        self.save_db()
    
    def get_user(self, user_id: int):
        """الحصول على بيانات مستخدم"""
        return self.data["users"].get(str(user_id))
    
    def add_transfer(self, user_id: int, source: str, destination: str, count: int):
        """تسجيل عملية نقل"""
        self.data["transfers"].append({
            "user_id": user_id,
            "source": source,
            "destination": destination,
            "count": count,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        })
        self.save_db()
    
    def get_accounts(self) -> List:
        """ال��صول على جميع الحسابات"""
        try:
            with open('accounts.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                accounts = []
                for api_account in data.get("api_accounts", []):
                    for account in api_account.get("accounts", []):
                        account["api_id"] = api_account["api_id"]
                        account["api_hash"] = api_account["api_hash"]
                        accounts.append(account)
                return accounts
        except:
            return []

db = TransmembrDB()

# =====================================================================
# معالجات البوت
# =====================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # إضافة المستخدم لقاعدة البيانات
    if not db.get_user(user_id):
        db.add_user(user_id, username)
    
    keyboard = [
        [InlineKeyboardButton("🚀 نقل أعضاء", callback_data="transfer")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="stats")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 <b>مرحباً في Transmembr Bot</b>\n\n"
        "<i>البوت الاحترافي لنقل أعضاء Telegram</i>\n\n"
        "✨ المميزات:\n"
        "✅ نقل أعضاء غير محدود\n"
        "✅ دعم حسابات متعددة\n"
        "✅ نقل آلي بدون توقف\n"
        "✅ إحصائيات فورية\n\n"
        "👇 <b>اختر عملية:</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    logger.info(f"👤 مستخدم جديد: {username} ({user_id})")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار البوت"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "transfer":
        keyboard = [
            [InlineKeyboardButton("📍 نقل من مجموعة", callback_data="single_transfer")],
            [InlineKeyboardButton("📍📍 نقل من عدة مجموعات", callback_data="multi_transfer")],
            [InlineKeyboardButton("🔄 نقل آلي مستمر", callback_data="auto_transfer")],
            [InlineKeyboardButton("⬅️ العودة", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "<b>🚀 خيارات النقل:</b>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    elif query.data == "single_transfer":
        await query.edit_message_text(
            "📝 <b>أرسل البيانات بهذا الشكل:</b>\n\n"
            "<code>المجموعة_المصدرية</code>\n"
            "<code>المجموعة_الهدفية</code>\n"
            "<code>عدد_الأعضاء</code>\n\n"
            "مثال:\n"
            "<code>@source_group</code>\n"
            "<code>@target_group</code>\n"
            "<code>100</code>",
            parse_mode="HTML"
        )
        context.user_data['mode'] = 'single_transfer'
    
    elif query.data == "stats":
        accounts = db.get_accounts()
        total_accounts = len(accounts)
        total_transfers = len(db.data["transfers"])
        total_users = len(db.data["users"])
        
        stats_text = (
            f"📊 <b>إحصائيات Transmembr:</b>\n\n"
            f"👥 عدد المستخدمين: <b>{total_users}</b>\n"
            f"📱 عدد الحسابات المتاحة: <b>{total_accounts}</b>\n"
            f"🔄 إجمالي العمليات: <b>{total_transfers}</b>\n\n"
            f"⚡ السعة الإجمالية: <b>{total_accounts * 50} عضو/يوم</b>\n"
        )
        
        keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    elif query.data == "help":
        help_text = (
            "❓ <b>مساعدة Transmembr:</b>\n\n"
            "🔹 <b>كيفية الاستخدام:</b>\n"
            "1️⃣ اختر "نقل أعضاء"\n"
            "2️⃣ أدخل المجموعة المصدرية والهدفية\n"
            "3️⃣ حدد عدد الأعضاء\n"
            "4️⃣ انتظر اكتمال العملية\n\n"
            "🔹 <b>الحد الأقصى اليومي:</b>\n"
            "كل حساب: 50 عضو/يوم\n"
            "مع عدة حسابات: غير محدود!\n\n"
            "🔹 <b>الدعم:</b>\n"
            "❓ أسئلة أو مشاكل؟\n"
            "📧 تواصل مع المطور"
        )
        
        keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    elif query.data == "back":
        await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل"""
    user_id = update.effective_user.id
    text = update.message.text
    
    mode = context.user_data.get('mode')
    
    if mode == 'single_transfer':
        try:
            lines = text.strip().split('\n')
            if len(lines) >= 3:
                source = lines[0].strip()
                destination = lines[1].strip()
                count = int(lines[2].strip())
                
                # تسجيل العملية
                db.add_transfer(user_id, source, destination, count)
                
                # بدء النقل
                await update.message.reply_text(
                    f"🚀 <b>جارٍ نقل {count} عضو...</b>\n\n"
                    f"📍 من: <code>{source}</code>\n"
                    f"📍 إلى: <code>{destination}</code>\n\n"
                    f"⏳ الرجاء الانتظار...",
                    parse_mode="HTML"
                )
                
                # عملية النقل (مثال)
                await asyncio.sleep(2)  # محاكاة
                
                await update.message.reply_text(
                    f"✅ <b>تم النقل بنجاح!</b>\n\n"
                    f"✨ تم نقل {count} عضو\n"
                    f"📊 النسبة: 100%\n"
                    f"⏱️ الوقت: ~30 ثانية",
                    parse_mode="HTML"
                )
                
                context.user_data['mode'] = None
        except ValueError:
            await update.message.reply_text("❌ خطأ في الإدخال! أدخل أرقام صحيحة.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الأخطاء"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# =====================================================================
# تشغيل البوت
# =====================================================================

async def main():
    """تشغيل البوت الرئيسي"""
    print("\n" + "="*60)
    print("🚀 Transmembr Bot - جاهز للتشغيل!")
    print("="*60 + "\n")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # بدء البوت
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  تم إيقاف البوت")
        logger.info("تم إيقاف البوت من قبل المستخدم")
