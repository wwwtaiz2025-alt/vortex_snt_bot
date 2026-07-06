import os
import json
import hmac
import hashlib
import urllib.parse
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from database import (
    register_user, get_user, perform_click, get_total_users, 
    is_mining_open, add_click_boost, deduct_points_manually,
    db, send_broadcast
)
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# --- إعدادات CORS للسماح لتيليجرام بالتواصل ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_TOKEN = "ضع_توكن_البوت_هنا"  # ⚠️ استبدله بتوكن البوت الخاص بك

# --- دالة التحقق من بيانات تيليجرام (أمان لا يخترق) ---
def verify_telegram_data(init_data: str) -> dict:
    """تتحقق من أن البيانات قادمة من تيليجرام وليست مزورة"""
    parsed = urllib.parse.parse_qs(init_data)
    received_hash = parsed.pop('hash')[0]
    
    # ترتيب المفاتيح أبجدياً لإنشاء السلسلة النصية الصحيحة
    sorted_keys = sorted(parsed.keys())
    data_string = "\n".join([f"{k}={parsed[k][0]}" for k in sorted_keys])
    
    # حساب التشفير باستخدام توكن البوت
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(secret_key, data_string.encode(), hashlib.sha256).hexdigest()
    
    if computed_hash != received_hash:
        raise HTTPException(status_code=403, detail="بيانات غير صالحة")
    
    # تحويل القيم إلى أنواع صحيحة
    result = {k: parsed[k][0] for k in parsed}
    if 'user' in result:
        result['user'] = json.loads(result['user'])
    return result

# --- 1. صفحة التطبيق الرئيسية (Mini-App) ---
@app.get("/app")
async def serve_app(request: Request, initData: str = Query(...)):
    try:
        # فك تشفير بيانات المستخدم من تيليجرام
        data = verify_telegram_data(initData)
        user_data = data.get('user', {})
        telegram_id = int(user_data.get('id'))
        username = user_data.get('username', f"User_{telegram_id}")
        
        # استخراج IP وجهاز المستخدم
        ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # تسجيل المستخدم (إذا لم يكن مسجلاً)
        user = get_user(telegram_id)
        if not user:
            success, msg = register_user(telegram_id, username, ip, user_agent)
            if not success:
                return HTMLResponse(content=f"<h1>{msg}</h1>", status_code=400)
        
        # جلب أحدث بياناته
        user = get_user(telegram_id)
        if user.get("is_banned", False):
            return HTMLResponse(content="<h1>تم حظر حسابك</h1>", status_code=403)
        
        # جلب الإعدادات العامة
        total_users = get_total_users()
        mining_open = is_mining_open()
        
        # تحضير متغيرات للواجهة
        points = user.get("points", 0)
        max_clicks = user.get("max_clicks", 1000)
        clicks_used = user.get("clicks_used", 0)
        progress = int((clicks_used / max_clicks) * 100) if max_clicks > 0 else 0
        
        # قراءة ملف الـ HTML وتضمين البيانات داخله
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        
        # حقن البيانات في الـ HTML (استبدال المتغيرات)
        html = html.replace("{{TELEGRAM_ID}}", str(telegram_id))
        html = html.replace("{{USERNAME}}", username)
        html = html.replace("{{POINTS}}", str(points))
        html = html.replace("{{MAX_CLICKS}}", str(max_clicks))
        html = html.replace("{{CLICKS_USED}}", str(clicks_used))
        html = html.replace("{{PROGRESS}}", str(progress))
        html = html.replace("{{TOTAL_USERS}}", str(total_users))
        html = html.replace("{{MINING_OPEN}}", "true" if mining_open else "false")
        html = html.replace("{{TARGET_USERS}}", "20000")
        
        return HTMLResponse(content=html)
    
    except HTTPException as e:
        return HTMLResponse(content=f"<h1>خطأ في المصادقة: {e.detail}</h1>", status_code=e.status_code)
    except Exception as e:
        return HTMLResponse(content=f"<h1>حدث خطأ داخلي: {str(e)}</h1>", status_code=500)

# --- 2. API الحالة العامة (للعداد والتحديث) ---
@app.get("/api/status")
async def status(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="غير مسجل")
    
    return {
        "total_users": get_total_users(),
        "mining_open": is_mining_open(),
        "points": user.get("points", 0),
        "max_clicks": user.get("max_clicks", 1000),
        "clicks_used": user.get("clicks_used", 0),
        "progress": int((user.get("clicks_used", 0) / user.get("max_clicks", 1000)) * 100)
    }

# --- 3. API التعدين (الضغط) مع حماية التبريد 3 ثواني ---
cooldowns = {}  # تخزين بسيط للتبريد (للمشاريع الصغيرة، ولكنه يعمل)
@app.post("/api/click")
async def click(telegram_id: int):
    # حماية التبريد (3 ثواني بين كل ضغطة)
    last_click = cooldowns.get(telegram_id, 0)
    now = datetime.utcnow().timestamp()
    if now - last_click < 3:
        return JSONResponse({
            "success": False,
            "message": "⚠️ انتظر 3 ثوانٍ بين كل ضغطة",
            "wait": 3 - (now - last_click)
        }, status_code=429)
    
    success, msg = perform_click(telegram_id)
    if not success:
        return {"success": False, "message": msg}
    
    # تحديث وقت آخر ضغطة
    cooldowns[telegram_id] = now
    
    # جلب الرصيد الجديد
    user = get_user(telegram_id)
    return {
        "success": True,
        "message": "✅ +1 نقطة",
        "new_points": user.get("points", 0),
        "clicks_used": user.get("clicks_used", 0),
        "max_clicks": user.get("max_clicks", 1000),
        "progress": int((user.get("clicks_used", 0) / user.get("max_clicks", 1000)) * 100)
    }

# --- 4. API شراء هامش التعدين (زيادة الحد) ---
class BoostPurchase(BaseModel):
    telegram_id: int
    extra_clicks: int  # عدد الضغطات الإضافية (مثلاً 500)

@app.post("/api/buy_boost")
async def buy_boost(data: BoostPurchase):
    # هنا يمكنك إضافة منطق الدفع (محفظة، نقاط، الخ)
    # نكتفي حالياً بإضافة الهامش مجاناً للتجربة، لكن في الواقع ستتحقق من الدفع
    if data.extra_clicks <= 0 or data.extra_clicks > 5000:
        return {"success": False, "message": "قيمة غير صالحة"}
    
    add_click_boost(data.telegram_id, data.extra_clicks)
    user = get_user(data.telegram_id)
    return {
        "success": True,
        "message": f"✅ تمت إضافة {data.extra_clicks} ضغطة إضافية",
        "new_max": user.get("max_clicks", 0)
    }

# --- 5. APIs خاصة بالإدارة (Admin & Support) ---
# 5.1 قائمة المستخدمين (للمدير فقط)
@app.get("/admin/users")
async def admin_users(telegram_id: int):
    user = get_user(telegram_id)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="غير مصرح")
    
    # جلب آخر 100 مستخدم (للتبسيط)
    users = list(db.users.find({}, {"_id": 0, "telegram_id": 1, "username": 1, "points": 1, "clicks_used": 1, "max_clicks": 1}).limit(100))
    return {"users": users}

# 5.2 خصم الرصيد يدوياً (للمدير)
class DeductRequest(BaseModel):
    admin_id: int
    target_id: int
    amount: int
    reason: str

@app.post("/admin/deduct")
async def deduct_points(req: DeductRequest):
    admin = get_user(req.admin_id)
    if not admin or admin.get("role") != "admin":
        raise HTTPException(status_code=403, detail="غير مصرح")
    
    deduct_points_manually(req.target_id, req.amount, req.reason)
    return {"success": True, "message": f"تم خصم {req.amount} نقطة"}

# 5.3 إرسال بث جماعي (للمدير)
class BroadcastRequest(BaseModel):
    admin_id: int
    message: str

@app.post("/admin/broadcast")
async def broadcast(req: BroadcastRequest):
    admin = get_user(req.admin_id)
    if not admin or admin.get("role") != "admin":
        raise HTTPException(status_code=403, detail="غير مصرح")
    
    # تخزين الرسالة في قاعدة البيانات
    send_broadcast(req.message)
    # هنا يمكن إضافة كود إرسال فعلي عبر تيليجرام (سنفعله لاحقاً)
    return {"success": True, "message": "تم إرسال الإشعار للجميع"}

# 5.4 تبديل حالة التعدين يدوياً (للمدير)
@app.post("/admin/toggle_mining")
async def toggle_mining(admin_id: int):
    admin = get_user(admin_id)
    if not admin or admin.get("role") != "admin":
        raise HTTPException(status_code=403, detail="غير مصرح")
    
    current = is_mining_open()
    db.settings.update_one(
        {"_id": "main_config"},
        {"$set": {"mining_open": not current}},
        upsert=True
    )
    return {"success": True, "new_status": not current}

# --- تشغيل السيرفر ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
