from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
import secrets

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {"sub": user_id, "email": email, "role": role, "exp": datetime.now(timezone.utc) + timedelta(minutes=15), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])}, {"password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["_id"] = str(user["_id"])
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str

@api_router.post("/auth/register")
async def register(req: RegisterRequest, response: Response):
    email = req.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "name": req.name,
        "email": email,
        "phone": req.phone,
        "password_hash": hash_password(req.password),
        "role": "Cashier",
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email, "Cashier")
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {"id": user_id, "name": req.name, "email": email, "phone": req.phone, "role": "Cashier"}

@api_router.post("/auth/login")
async def login(req: LoginRequest, response: Response):
    email = req.email.lower()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email, user["role"])
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {"id": user_id, "name": user.get("name"), "email": email, "phone": user.get("phone"), "role": user["role"]}

@api_router.post("/auth/logout")
async def logout(response: Response, user: dict = Depends(get_current_user)):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user

class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int
    category: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None

@api_router.get("/products")
async def get_products(user: dict = Depends(get_current_user)):
    products = await db.products.find({}, {"_id": 0}).to_list(1000)
    return products

@api_router.post("/products")
async def create_product(product: ProductCreate, user: dict = Depends(get_current_user)):
    if user["role"] != "Owner":
        raise HTTPException(status_code=403, detail="Only owners can create products")
    
    product_doc = product.model_dump()
    product_doc["id"] = str(ObjectId())
    product_doc["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.products.insert_one(product_doc)
    product_doc.pop("_id", None)
    return product_doc

@api_router.put("/products/{product_id}")
async def update_product(product_id: str, product: ProductUpdate, user: dict = Depends(get_current_user)):
    if user["role"] != "Owner":
        raise HTTPException(status_code=403, detail="Only owners can update products")
    
    update_data = {k: v for k, v in product.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.products.update_one({"id": product_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    return updated

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, user: dict = Depends(get_current_user)):
    if user["role"] != "Owner":
        raise HTTPException(status_code=403, detail="Only owners can delete products")
    
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}

class BillItem(BaseModel):
    id: str
    name: str
    quantity: int
    price: float

class BillCreate(BaseModel):
    items: List[BillItem]
    total: float
    payment_type: str

@api_router.post("/bills")
async def create_bill(bill: BillCreate, user: dict = Depends(get_current_user)):
    bill_doc = bill.model_dump()
    bill_doc["id"] = str(ObjectId())
    bill_doc["created_by"] = user["id"]
    bill_doc["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.bills.insert_one(bill_doc)
    
    for item in bill.items:
        await db.products.update_one({"id": item.id}, {"$inc": {"stock": -item.quantity}})
    
    bill_doc.pop("_id", None)
    return bill_doc

@api_router.get("/bills")
async def get_bills(user: dict = Depends(get_current_user)):
    bills = await db.bills.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return bills

@api_router.get("/bills/{bill_id}")
async def get_bill(bill_id: str, user: dict = Depends(get_current_user)):
    bill = await db.bills.find_one({"id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    if user["role"] != "Owner":
        raise HTTPException(status_code=403, detail="Only owners can view dashboard")
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    bills_today = await db.bills.find({"created_at": {"$gte": today_start}}, {"_id": 0}).to_list(1000)
    total_sales_today = sum(bill["total"] for bill in bills_today)
    bills_count_today = len(bills_today)
    
    all_bills = await db.bills.find({}, {"_id": 0}).to_list(10000)
    total_revenue = sum(bill["total"] for bill in all_bills)
    
    item_counts = {}
    for bill in all_bills:
        for item in bill["items"]:
            if item["name"] in item_counts:
                item_counts[item["name"]] += item["quantity"]
            else:
                item_counts[item["name"]] = item["quantity"]
    
    top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_selling = [{"name": name, "quantity": qty} for name, qty in top_items]
    
    return {
        "total_sales_today": total_sales_today,
        "bills_count_today": bills_count_today,
        "total_revenue": total_revenue,
        "top_selling": top_selling
    }

class StaffCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

@api_router.get("/staff")
async def get_staff(user: dict = Depends(get_current_user)):
    if user["role"] != "Owner":
        raise HTTPException(status_code=403, detail="Only owners can view staff")
    
    staff = await db.users.find({"role": "Cashier"}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return staff

@api_router.post("/staff")
async def create_staff(staff: StaffCreate, user: dict = Depends(get_current_user)):
    if user["role"] != "Owner":
        raise HTTPException(status_code=403, detail="Only owners can create staff")
    
    email = staff.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    staff_doc = {
        "id": str(ObjectId()),
        "name": staff.name,
        "email": email,
        "phone": staff.phone,
        "password_hash": hash_password(staff.password),
        "role": "Cashier",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(staff_doc)
    staff_doc.pop("_id", None)
    staff_doc.pop("password_hash", None)
    return staff_doc

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await seed_admin()

async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "owner@pos.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        hashed = hash_password(admin_password)
        user_doc = {
            "id": str(ObjectId()),
            "email": admin_email,
            "password_hash": hashed,
            "name": "Owner",
            "role": "Owner",
            "phone": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        logger.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info(f"Admin password updated: {admin_email}")
    
    log_dir = os.environ.get("LOG_DIR", "./memory")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(log_dir, "test_credentials.md"), "w") as f:
        f.write("# Test Credentials\n\n")
        f.write("## Owner Account\n")
        f.write(f"- Email: {admin_email}\n")
        f.write(f"- Password: {admin_password}\n")
        f.write(f"- Role: Owner\n\n")
        f.write("## Auth Endpoints\n")
        f.write("- POST /api/auth/login\n")
        f.write("- POST /api/auth/register\n")
        f.write("- GET /api/auth/me\n")
        f.write("- POST /api/auth/logout\n")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()