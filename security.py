#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔒 نظام الأمان والتفويض
Security & Authorization System
"""

import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class APIKeyManager:
    """مدير مفاتيح API"""
    
    def __init__(self, keys_file: str = "api_keys.json"):
        self.keys_file = keys_file
        self.keys = self.load_keys()
    
    def load_keys(self) -> Dict:
        """تحميل المفاتيح"""
        try:
            with open(self.keys_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"keys": {}}
    
    def save_keys(self):
        """حفظ المفاتيح"""
        with open(self.keys_file, 'w', encoding='utf-8') as f:
            json.dump(self.keys, f, ensure_ascii=False, indent=2)
    
    def generate_key(self, user_id: int, name: str) -> str:
        """إنشاء مفتاح API جديد"""
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        self.keys["keys"][key_hash] = {
            "user_id": user_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "usage_count": 0,
            "status": "active"
        }
        
        self.save_keys()
        logger.info(f"✅ تم إنشاء مفتاح جديد للمستخدم {user_id}")
        
        return key
    
    def verify_key(self, key: str) -> Optional[Dict]:
        """التحقق من صحة المفتاح"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash in self.keys["keys"]:
            key_data = self.keys["keys"][key_hash]
            if key_data["status"] == "active":
                # تحديث آخر استخدام
                key_data["last_used"] = datetime.now().isoformat()
                key_data["usage_count"] += 1
                self.save_keys()
                return key_data
        
        logger.warning("⚠️ محاولة استخدام مفتاح غير صحيح")
        return None
    
    def revoke_key(self, key: str) -> bool:
        """إلغاء مفتاح"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash in self.keys["keys"]:
            self.keys["keys"][key_hash]["status"] = "revoked"
            self.save_keys()
            logger.info("✅ تم إلغاء المفتاح")
            return True
        
        return False

class RateLimiter:
    """محدد سرعة الطلبات"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window  # بالثواني
        self.requests = {}  # {user_id: [(timestamp, count)]}
    
    def is_allowed(self, user_id: int) -> bool:
        """التحقق من السماح بالطلب"""
        now = datetime.now()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # تنظيف الطلبات القديمة
        self.requests[user_id] = [
            timestamp for timestamp in self.requests[user_id]
            if (now - timestamp).total_seconds() < self.time_window
        ]
        
        # التحقق من الحد الأقصى
        if len(self.requests[user_id]) >= self.max_requests:
            logger.warning(f"⚠️ تجاوز المستخدم {user_id} الحد الأقصى للطلبات")
            return False
        
        # إضافة الطلب الجديد
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: int) -> int:
        """الحصول على عدد الطلبات المتبقية"""
        if user_id not in self.requests:
            return self.max_requests
        
        return max(0, self.max_requests - len(self.requests[user_id]))

class UserValidator:
    """التحقق من المستخدمين"""
    
    @staticmethod
    def validate_telegram_id(user_id: str) -> bool:
        """التحقق من صحة معرف Telegram"""
        try:
            int(user_id)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_group_identifier(identifier: str) -> bool:
        """التحقق من صحة معرف المجموعة"""
        # يمكن أن يكون اسم المجموعة أو رقم
        return len(identifier) > 0
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """التحقق من صحة رقم الهاتف"""
        # يجب أن يبدأ برمز الدولة (+)
        if not phone.startswith('+'):
            return False
        
        # يجب أن يكون بقية الأرقام أرقام فقط
        try:
            int(phone[1:])
            return len(phone) >= 10  # حد أدنى للطول
        except ValueError:
            return False

class AuditLogger:
    """تسجيل العمليات"""
    
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
    
    def log_action(self, user_id: int, action: str, details: Dict = None):
        """تسجيل عملية"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "action": action,
            "details": details or {}
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"📝 تم تسجيل: {action} من المستخدم {user_id}")
    
    def log_transfer(self, user_id: int, source: str, destination: str, count: int):
        """تسجيل عملية نقل"""
        self.log_action(user_id, "transfer", {
            "source": source,
            "destination": destination,
            "count": count
        })
    
    def log_error(self, user_id: int, error_type: str, message: str):
        """تسجيل خطأ"""
        self.log_action(user_id, "error", {
            "error_type": error_type,
            "message": message
        })

# =====================================================================
# استخدام
# =====================================================================

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # إنشاء مدير المفاتيح
    key_manager = APIKeyManager()
    
    # إنشاء مفتاح جديد
    new_key = key_manager.generate_key(1234567, "my_app")
    print(f"المفتاح الجديد: {new_key}")
    
    # التحقق من المفتاح
    verified = key_manager.verify_key(new_key)
    print(f"التحقق: {verified is not None}")
    
    # محدد السرعة
    limiter = RateLimiter(max_requests=10)
    for i in range(12):
        allowed = limiter.is_allowed(1)
        remaining = limiter.get_remaining(1)
        print(f"الطلب {i+1}: {'مسموح' if allowed else 'مرفوض'} - متبقي: {remaining}")
