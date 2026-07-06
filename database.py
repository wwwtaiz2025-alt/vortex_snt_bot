import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import hashlib

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["Vortex_VTX"]

# --- دالة لإنشاء بصمة فريدة للجهاز (حماية من التكرار) ---
def generate_device_fingerprint(ip, user_agent, telegram_id):
    raw = f"{ip}_{user_agent}_{telegram_id}"
    return hashlib.sha256(raw.encode()).hexdigest()

# --- 1. تسجيل مستخدم جديد مع حماية صارمة ---
def register_user(telegram_id, username, ip, user_agent):
    # التحقق إذا كان مسجلاً مسبقاً
    if db.users.find_one({"telegram_id": telegram_id}):
        return False, "أنت مسجل مسبقاً"
    
    # بصمة الجهاز
    fingerprint = generate_device_fingerprint(ip, user_agent, telegram_id)
    if db.users.find_one({"device_fingerprint": fingerprint}):
        return False, "تم التسجيل من هذا الجهاز بحساب آخر مسبقاً"

    # التحقق من وصول العدد للـ 20,000
    total_users = db.counters.find_one({"_id": "total_users"})
    current_count = total_users["count"] if total_users else 0
    if current_count >= 20000:
        return False, "تم اكتمال العدد المطلوب، التعدين مفتوح الآن."

    # زيادة العداد الذري (Atomic Increment)
    new_count = db.counters.find_one_and_update(
        {"_id": "total_users"},
        {"$inc": {"count": 1}},
        upsert=True,
        return_document=True
    )["count"]

    # هيكل المستخدم الكامل
    db.users.insert_one({
        "telegram_id": telegram_id,
        "username": username,
        "device_fingerprint": fingerprint,
        "ip_address": ip,
        "points": 0,
        "max_clicks": 1000,          # الحد الأقصى للضغطات مدى الحياة
        "clicks_used": 0,            # عدد الضغطات المستخدمة
        "referral_code": None,       # كود الإحالة الخاص به
        "referred_by": None,         # من دعاه
        "role": "user",              # user, support, admin
        "is_banned": False,
        "created_at": datetime.utcnow()
    })

    # هل وصلنا لـ 20,000 لنفتح التعدين؟
    if new_count >= 20000:
        db.settings.update_one(
            {"_id": "main_config"},
            {"$set": {"mining_open": True}},
            upsert=True
        )
    return True, "تم التسجيل بنجاح"

# --- 2. دوال التعدين والضغط ---
def get_user(telegram_id):
    return db.users.find_one({"telegram_id": telegram_id})

def perform_click(telegram_id):
    user = get_user(telegram_id)
    if not user: return False, "غير مسجل"
    if user["is_banned"]: return False, "تم حظر حسابك"
    
    # هل وصل للحد الأقصى؟
    if user["clicks_used"] >= user["max_clicks"]:
        return False, "استنفذت كل ضغطاتك، قم بشراء هامش إضافي"
    
    # هل التعدين مفتوح؟
    settings = db.settings.find_one({"_id": "main_config"})
    if not settings or not settings.get("mining_open", False):
        return False, "التعدين لم يفتح بعد، انتظر اكتمال العدد"

    # تحديث النقاط والضغطات
    db.users.update_one(
        {"telegram_id": telegram_id},
        {
            "$inc": {"points": 1, "clicks_used": 1},
            "$set": {"last_click": datetime.utcnow()}
        }
    )
    return True, "تمت الإضافة"

# --- 3. دوال الإدارة والتحكم ---
def get_total_users():
    doc = db.counters.find_one({"_id": "total_users"})
    return doc["count"] if doc else 0

def is_mining_open():
    doc = db.settings.find_one({"_id": "main_config"})
    return doc.get("mining_open", False) if doc else False

def add_click_boost(telegram_id, extra_clicks):
    """إضافة هامش تعدين (شراء حزمة)"""
    db.users.update_one(
        {"telegram_id": telegram_id},
        {"$inc": {"max_clicks": extra_clicks}}
    )
    return True

# --- 4. دوال دعم العملاء والإشعارات ---
def send_broadcast(message):
    """تخزين رسالة للإرسال الجماعي (سننفذها في main.py)"""
    db.broadcasts.insert_one({
        "message": message,
        "sent_at": datetime.utcnow(),
        "status": "pending"
    })

def deduct_points_manually(telegram_id, amount, reason):
    """خصم رصيد يدوي (للمخالفين)"""
    db.users.update_one(
        {"telegram_id": telegram_id},
        {"$inc": {"points": -amount}}
    )
    # تسجيل عملية الخصم في سجل خاص
    db.deduction_logs.insert_one({
        "telegram_id": telegram_id,
        "amount": amount,
        "reason": reason,
        "deducted_by": "admin",
        "timestamp": datetime.utcnow()
    })
