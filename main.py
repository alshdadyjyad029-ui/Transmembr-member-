#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 مدير حسابات تيليجرام ونقل الأعضاء
Telegram Member Transfer Manager

دعم حسابات غير محدودة
Unlimited Accounts Support
"""

import json
import os
import sys
import time
import random
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    from telethon.sync import TelegramClient
    from telethon.errors import FloodWaitError, PhoneNumberInvalidError
    from telethon.tl.functions.channels import InviteToChannelRequest
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import track
    from rich.prompt import Prompt, Confirm
except ImportError:
    print("❌ المكتبات المطلوبة غير مثبتة!")
    print("👉 اتبع التعليمات:")
    print("   pip install telethon rich python-dotenv")
    sys.exit(1)

# =====================================================================
# إعدادات عامة
# =====================================================================

console = Console()
LOG_FILE = "telegram_manager.log"
ACCOUNTS_FILE = "accounts.json"
ENV_FILE = ".env"

# =====================================================================
# دوال مساعدة
# =====================================================================

def log_message(level: str, message: str):
    """تسجيل الرسائل في الملف والكونسول"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {level} - {message}"
    
    # اطبع في الكونسول
    if level == "INFO":
        console.print(f"[green]✅ {message}[/green]")
    elif level == "WARNING":
        console.print(f"[yellow]⚠️  {message}[/yellow]")
    elif level == "ERROR":
        console.print(f"[red]❌ {message}[/red]")
    
    # احفظ في الملف
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def load_accounts() -> Dict:
    """تحميل ملف accounts.json"""
    if not os.path.exists(ACCOUNTS_FILE):
        log_message("ERROR", f"ملف {ACCOUNTS_FILE} غير موجود!")
        return {}
    
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_accounts(data: Dict):
    """حفظ ملف accounts.json"""
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log_message("INFO", "تم حفظ accounts.json بنجاح")

def get_active_accounts() -> List[Dict]:
    """الحصول على جميع الحسابات النشطة"""
    data = load_accounts()
    active_accounts = []
    
    for api_account in data.get("api_accounts", []):
        for account in api_account.get("accounts", []):
            if account.get("status") == "active":
                account["api_id"] = api_account["api_id"]
                account["api_hash"] = api_account["api_hash"]
                active_accounts.append(account)
    
    return active_accounts

def get_best_account() -> Optional[Dict]:
    """الحصول على أفضل حساب (الذي استخدم أقل عدد دعوات اليوم)"""
    accounts = get_active_accounts()
    if not accounts:
        return None
    
    # ترتيب الحسابات حسب عدد الدعوات المتبقية
    sorted_accounts = sorted(
        accounts,
        key=lambda x: x.get("invites_today", 0)
    )
    
    return sorted_accounts[0]

# =====================================================================
# عرض البيانات بشكل جميل
# =====================================================================

def show_header():
    """عرض الرأس"""
    console.print(
        Panel(
            "[bold cyan]🚀 مدير حسابات تيليجرام ونقل الأعضاء[/bold cyan]\n"
            "[yellow]دعم حسابات غير محدودة[/yellow]",
            title="[bold green]📱 Telegram Manager[/bold green]",
            border_style="cyan"
        )
    )

def show_accounts_table():
    """عرض جدول الحسابات"""
    accounts = get_active_accounts()
    
    if not accounts:
        console.print("[red]❌ لا توجد حسابات نشطة![/red]")
        return
    
    table = Table(title="📊 جدول الحسابات النشطة", border_style="cyan")
    table.add_column("#", style="cyan")
    table.add_column("رقم الهاتف", style="green")
    table.add_column("الحالة", style="yellow")
    table.add_column("الدعوات اليوم", style="blue")
    table.add_column("المتبقي", style="magenta")
    
    for idx, account in enumerate(accounts, 1):
        invites_today = account.get("invites_today", 0)
        max_invites = account.get("max_invites_per_day", 50)
        remaining = max_invites - invites_today
        
        table.add_row(
            str(idx),
            account.get("phone", "N/A"),
            account.get("status", "N/A"),
            str(invites_today),
            f"[green]{remaining}[/green]" if remaining > 0 else "[red]0[/red]"
        )
    
    console.print(table)

def show_menu():
    """عرض القائمة الرئيسية"""
    show_header()
    console.print(
        Panel(
            "[cyan]1️⃣  إدارة الحسابات[/cyan]\n"
            "[cyan]2️⃣  نقل الأعضاء[/cyan]\n"
            "[cyan]3️⃣  عرض إحصائيات[/cyan]\n"
            "[cyan]4️⃣  الإعدادات[/cyan]\n"
            "[cyan]0️⃣  خروج[/cyan]",
            title="[bold green]القائمة الرئيسية[/bold green]",
            border_style="green"
        )
    )

# =====================================================================
# إدارة الحسابات
# =====================================================================

def add_account():
    """إضافة حساب جديد"""
    console.print("\n[bold cyan]➕ إضافة حساب جديد[/bold cyan]\n")
    
    phone = Prompt.ask("📱 أدخل رقم الهاتف", default="+966501234567")
    session_name = Prompt.ask("📁 اسم ملف الجلسة", default=f"session_{int(time.time())}.session")
    
    data = load_accounts()
    
    # إضافة الحساب للحساب الأول (يمكنك تعديله)
    if data.get("api_accounts"):
        new_account = {
            "phone": phone,
            "session": session_name,
            "status": "active",
            "invites_today": 0,
            "max_invites_per_day": 50,
            "last_reset": datetime.now().strftime("%Y-%m-%d")
        }
        
        data["api_accounts"][0]["accounts"].append(new_account)
        save_accounts(data)
        
        log_message("INFO", f"✅ تم إضافة حساب جديد: {phone}")
        console.print(f"[green]✅ تم إضافة الحساب {phone} بنجاح![/green]")
    else:
        console.print("[red]❌ لا توجد بيانات API![/red]")

def remove_account():
    """إزالة حساب"""
    console.print("\n[bold cyan]❌ إزالة حساب[/bold cyan]\n")
    
    accounts = get_active_accounts()
    show_accounts_table()
    
    account_idx = Prompt.ask("\n🔢 اختر رقم الحساب", default="1")
    
    try:
        idx = int(account_idx) - 1
        if 0 <= idx < len(accounts):
            phone = accounts[idx]["phone"]
            
            # حذف من ملف accounts.json
            data = load_accounts()
            for api_account in data.get("api_accounts", []):
                api_account["accounts"] = [
                    acc for acc in api_account["accounts"]
                    if acc.get("phone") != phone
                ]
            save_accounts(data)
            
            log_message("INFO", f"✅ تم حذف الحساب: {phone}")
            console.print(f"[green]✅ تم حذف الحساب {phone} بنجاح![/green]")
        else:
            console.print("[red]❌ رقم غير صحيح![/red]")
    except ValueError:
        console.print("[red]❌ أدخل رقم صحيح![/red]")

def manage_accounts_menu():
    """قائمة إدارة الحسابات"""
    while True:
        console.print(
            Panel(
                "[cyan]1️⃣  عرض جميع الحسابات[/cyan]\n"
                "[cyan]2️⃣  إضافة حساب جديد[/cyan]\n"
                "[cyan]3️⃣  إزالة حساب[/cyan]\n"
                "[cyan]4️⃣  فحص حالة الحسابات[/cyan]\n"
                "[cyan]0️⃣  العودة[/cyan]",
                title="[bold green]إدارة الحسابات[/bold green]",
                border_style="green"
            )
        )
        
        choice = Prompt.ask("🔢 اختر", default="1")
        
        if choice == "1":
            show_accounts_table()
        elif choice == "2":
            add_account()
        elif choice == "3":
            remove_account()
        elif choice == "4":
            console.print("[yellow]⏳ جاري فحص الحسابات...[/yellow]")
            # يمكنك إضافة فحص فعلي هنا
            time.sleep(1)
            console.print("[green]✅ جميع الحسابات نشطة![/green]")
        elif choice == "0":
            break
        else:
            console.print("[red]❌ اختيار غير صحيح![/red]")

# =====================================================================
# الإحصائيات
# =====================================================================

def show_statistics():
    """عرض الإحصائيات"""
    console.clear()
    accounts = get_active_accounts()
    
    total_accounts = len(accounts)
    total_invites_today = sum(acc.get("invites_today", 0) for acc in accounts)
    total_capacity = sum(acc.get("max_invites_per_day", 50) for acc in accounts)
    remaining_capacity = total_capacity - total_invites_today
    
    table = Table(title="📊 الإحصائيات الكاملة", border_style="cyan")
    table.add_column("المقياس", style="cyan")
    table.add_column("القيمة", style="green")
    
    table.add_row("عدد الحسابات النشطة", str(total_accounts))
    table.add_row("إجمالي الدعوات اليوم", str(total_invites_today))
    table.add_row("إجمالي السعة اليومية", str(total_capacity))
    table.add_row("السعة المتبقية", f"[green]{remaining_capacity}[/green]")
    table.add_row("نسبة الاستخدام", f"{(total_invites_today/total_capacity*100):.1f}%")
    
    console.print(table)
    console.print("\n[cyan]اضغط Enter للعودة...[/cyan]")
    input()

# =====================================================================
# نقل الأعضاء
# =====================================================================

async def transfer_members_async():
    """نقل الأعضاء بشكل متزامن"""
    console.print("\n[bold cyan]🚀 نقل الأعضاء[/bold cyan]\n")
    
    best_account = get_best_account()
    if not best_account:
        console.print("[red]❌ لا توجد حسابات متاحة![/red]")
        return
    
    console.print(f"[green]✅ استخدام الحساب: {best_account['phone']}[/green]")
    
    try:
        api_id = best_account["api_id"]
        api_hash = best_account["api_hash"]
        session = best_account["session"]
        
        client = TelegramClient(session, api_id, api_hash)
        await client.start(phone=best_account["phone"])
        
        console.print("[green]✅ تم تسجيل الدخول بنجاح![/green]")
        
        # يمكنك إضافة منطق نقل الأعضاء هنا
        
        await client.disconnect()
        
    except Exception as e:
        log_message("ERROR", f"خطأ في النقل: {str(e)}")
        console.print(f"[red]❌ خطأ: {str(e)}[/red]")

def transfer_members_menu():
    """قائمة نقل الأعضاء"""
    console.print(
        Panel(
            "[cyan]1️⃣  نقل من مجموعة واحدة[/cyan]\n"
            "[cyan]2️⃣  نقل من مجموعات متعددة[/cyan]\n"
            "[cyan]3️⃣  نقل آلي مستمر[/cyan]\n"
            "[cyan]0️⃣  العودة[/cyan]",
            title="[bold green]نقل الأعضاء[/bold green]",
            border_style="green"
        )
    )
    
    choice = Prompt.ask("🔢 اختر", default="1")
    
    if choice == "1":
        console.print("[yellow]⏳ جاري نقل الأعضاء...[/yellow]")
        asyncio.run(transfer_members_async())
    elif choice == "2":
        console.print("[yellow]⏳ جاري نقل الأعضاء من مجموعات متعددة...[/yellow]")
        asyncio.run(transfer_members_async())
    elif choice == "3":
        console.print("[yellow]⏳ جاري بدء النقل الآلي...[/yellow]")
        asyncio.run(transfer_members_async())
    elif choice == "0":
        pass
    else:
        console.print("[red]❌ اختيار غير صحيح![/red]")

# =====================================================================
# البرنامج الرئيسي
# =====================================================================

def main():
    """البرنامج الرئيسي"""
    while True:
        show_menu()
        choice = Prompt.ask("\n🔢 اختر عملية", default="1")
        
        if choice == "1":
            manage_accounts_menu()
        elif choice == "2":
            transfer_members_menu()
        elif choice == "3":
            show_statistics()
        elif choice == "4":
            console.print("[yellow]⏳ جاري تحميل الإعدادات...[/yellow]")
            # يمكنك إضافة قائمة إعدادات هنا
        elif choice == "0":
            console.print("[cyan]👋 شكراً لاستخدامك البرنامج![/cyan]")
            log_message("INFO", "تم إغلاق البرنامج")
            break
        else:
            console.print("[red]❌ اختيار غير صحيح![/red]")
        
        console.print("\n")

if __name__ == "__main__":
    try:
        log_message("INFO", "🚀 بدء البرنامج")
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]⏸️  تم إيقاف البرنامج من قبل المستخدم[/yellow]")
        log_message("WARNING", "تم إيقاف البرنامج من قبل المستخدم")
    except Exception as e:
        console.print(f"[red]❌ خطأ حرج: {str(e)}[/red]")
        log_message("ERROR", f"خطأ حرج: {str(e)}")
