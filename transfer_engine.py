#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 محرك النقل الذكي
Transfer Engine for Transmembr
"""

import asyncio
import random
import time
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.functions.channels import InviteToChannelRequest

logger = logging.getLogger(__name__)

class TransferEngine:
    """محرك النقل الذكي"""
    
    def __init__(self, accounts_file: str = "accounts.json"):
        self.accounts_file = accounts_file
        self.clients: Dict[str, TelegramClient] = {}
        self.account_stats = {}
        self.load_accounts()
    
    def load_accounts(self):
        """تحميل الحسابات من الملف"""
        try:
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for api_account in data.get("api_accounts", []):
                api_id = api_account["api_id"]
                api_hash = api_account["api_hash"]
                
                for account in api_account.get("accounts", []):
                    if account.get("status") == "active":
                        phone = account["phone"]
                        session = account["session"]
                        
                        # إنشاء عميل Telegram
                        client = TelegramClient(
                            session,
                            api_id,
                            api_hash
                        )
                        
                        self.clients[phone] = client
                        self.account_stats[phone] = {
                            "invites_today": account.get("invites_today", 0),
                            "max_invites": account.get("max_invites_per_day", 50),
                            "last_reset": account.get("last_reset", str(datetime.now().date())),
                            "status": "active"
                        }
            
            logger.info(f"✅ تم تحميل {len(self.clients)} حساب")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الحسابات: {e}")
    
    def get_best_account(self) -> Optional[Tuple[str, TelegramClient]]:
        """الحصول على أفضل حساب متاح"""
        best_phone = None
        best_remaining = -1
        
        for phone, stats in self.account_stats.items():
            if stats["status"] == "active":
                remaining = stats["max_invites"] - stats["invites_today"]
                if remaining > best_remaining:
                    best_remaining = remaining
                    best_phone = phone
        
        if best_phone:
            return best_phone, self.clients[best_phone]
        return None
    
    async def connect_client(self, phone: str) -> bool:
        """الاتصال بـ Telegram باستخدام حساب"""
        try:
            client = self.clients[phone]
            if not client.is_connected():
                await client.connect()
            logger.info(f"✅ تم الاتصال بـ {phone}")
            return True
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بـ {phone}: {e}")
            self.account_stats[phone]["status"] = "inactive"
            return False
    
    async def get_group_members(
        self,
        phone: str,
        group_identifier: str
    ) -> List:
        """الحصول على قائمة أعضاء المجموعة"""
        try:
            client = self.clients[phone]
            entity = await client.get_entity(group_identifier)
            members = await client.get_participants(entity)
            logger.info(f"✅ تم الحصول على {len(members)} عضو من المجموعة")
            return members
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على الأعضاء: {e}")
            return []
    
    async def invite_member(
        self,
        phone: str,
        member_id: int,
        destination_group: str
    ) -> bool:
        """دعوة عضو إلى مجموعة"""
        try:
            client = self.clients[phone]
            destination = await client.get_entity(destination_group)
            
            # محاولة دعوة العضو
            await client(InviteToChannelRequest(
                destination,
                [member_id]
            ))
            
            # تحديث الإحصائيات
            self.account_stats[phone]["invites_today"] += 1
            
            logger.info(f"✅ تم دعوة العضو {member_id} بواسطة {phone}")
            return True
        
        except FloodWaitError as e:
            logger.warning(f"⏳ FloodWait: انتظر {e.seconds} ثانية")
            await asyncio.sleep(e.seconds)
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في دعوة العضو: {e}")
            return False
    
    async def transfer_members(
        self,
        source_group: str,
        destination_group: str,
        member_count: int = 100,
        delay_min: int = 10,
        delay_max: int = 30
    ) -> Dict:
        """نقل أ��ضاء من مجموعة إلى أخرى"""
        stats = {
            "total": member_count,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": datetime.now(),
            "end_time": None
        }
        
        try:
            # الحصول على أفضل حساب
            account_info = self.get_best_account()
            if not account_info:
                logger.error("❌ لا توجد حسابات متاحة")
                return stats
            
            best_phone, client = account_info
            
            # الاتصال بـ Telegram
            if not await self.connect_client(best_phone):
                return stats
            
            # الحصول على الأعضاء
            members = await self.get_group_members(best_phone, source_group)
            if not members:
                return stats
            
            # تحديد عدد الأعضاء
            members_to_transfer = members[:member_count]
            
            # نقل الأعضاء
            for idx, member in enumerate(members_to_transfer):
                # اختيار حساب
                account_info = self.get_best_account()
                if not account_info:
                    logger.warning("⚠️ لا توجد حسابات متاحة")
                    stats["skipped"] += 1
                    continue
                
                phone, _ = account_info
                
                # دعوة العضو
                success = await self.invite_member(
                    phone,
                    member.id,
                    destination_group
                )
                
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                
                # تأخير عشوائي
                delay = random.uniform(delay_min, delay_max)
                await asyncio.sleep(delay)
                
                # طباعة التقدم
                progress = ((idx + 1) / len(members_to_transfer)) * 100
                logger.info(f"📊 التقدم: {progress:.1f}% ({idx + 1}/{len(members_to_transfer)})")
        
        except Exception as e:
            logger.error(f"❌ خطأ في نقل الأعضاء: {e}")
        
        finally:
            stats["end_time"] = datetime.now()
            # حساب الوقت
            duration = (stats["end_time"] - stats["start_time"]).total_seconds()
            stats["duration"] = duration
            
            logger.info(
                f"\n📈 نتائج النقل:\n"
                f"   ✅ نجح: {stats['success']}\n"
                f"   ❌ فشل: {stats['failed']}\n"
                f"   ⏭️ تم تخطيه: {stats['skipped']}\n"
                f"   ⏱️ الوقت: {duration:.1f} ثانية"
            )
        
        return stats
    
    async def auto_transfer(
        self,
        source_group: str,
        destination_group: str,
        interval: int = 3600  # ساعة واحدة
    ):
        """نقل آلي مستمر"""
        logger.info("🔄 بدء النقل الآلي المستمر")
        
        while True:
            try:
                await self.transfer_members(
                    source_group,
                    destination_group,
                    member_count=50  # 50 عضو في كل جولة
                )
                
                logger.info(f"⏳ انتظر {interval} ثانية قبل الجولة التالية")
                await asyncio.sleep(interval)
            
            except KeyboardInterrupt:
                logger.info("⏹️ تم إيقاف النقل الآلي")
                break
            except Exception as e:
                logger.error(f"❌ خطأ في النقل الآلي: {e}")
                await asyncio.sleep(60)  # انتظر دقيقة قبل المحاولة مجدداً
    
    async def disconnect_all(self):
        """قطع جميع الاتصالات"""
        for phone, client in self.clients.items():
            try:
                if client.is_connected():
                    await client.disconnect()
                logger.info(f"✅ تم قطع الاتصال بـ {phone}")
            except Exception as e:
                logger.error(f"❌ خطأ في قطع الاتصال: {e}")
    
    def get_stats(self) -> Dict:
        """الحصول على الإحصائيات"""
        total_capacity = 0
        total_used = 0
        active_accounts = 0
        
        for phone, stats in self.account_stats.items():
            if stats["status"] == "active":
                active_accounts += 1
                total_capacity += stats["max_invites"]
                total_used += stats["invites_today"]
        
        return {
            "total_accounts": len(self.clients),
            "active_accounts": active_accounts,
            "total_capacity": total_capacity,
            "total_used": total_used,
            "remaining": total_capacity - total_used,
            "usage_percentage": (total_used / total_capacity * 100) if total_capacity > 0 else 0
        }


# =====================================================================
# مثال للاستخدام
# =====================================================================

if __name__ == "__main__":
    import logging
    
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    async def main():
        engine = TransferEngine()
        
        # الإحصائيات
        stats = engine.get_stats()
        print(f"\n📊 الإحصائيات: {stats}")
        
        # نقل الأعضاء
        # result = await engine.transfer_members(
        #     source_group="@source",
        #     destination_group="@destination",
        #     member_count=100
        # )
        # print(f"\n✅ النتائج: {result}")
        
        # قطع الاتصالات
        # await engine.disconnect_all()
    
    asyncio.run(main())
