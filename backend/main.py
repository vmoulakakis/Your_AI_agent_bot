from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import os

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt

from app import repositories as repo
from app.auth import verify_password, hash_password, ensure_default_admin
from app.workflows import import_products_from_json_feed

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"

app = FastAPI(title="Affiliate eShop API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    username: str
    is_admin: bool


class SettingUpdate(BaseModel):
    site_name: Optional[str] = None


class CategoryIn(BaseModel):
    name: str
    slug: Optional[str] = None


class ProductIn(BaseModel):
    title: str
    description: Optional[str] = ""
    price: float
    currency: str = "USD"
    image_url: Optional[str] = None
    category_name: Optional[str] = None
    affiliate_url_template: Optional[str] = None
    active: bool = True


class BlogPostIn(BaseModel):
    title: str
    content_md: str
    status: str = "draft"


class ImportRequest(BaseModel):
    feed_url: str


class AffiliateIn(BaseModel):
    name: str
    code: str


class OrderIn(BaseModel):
    product_id: int
    affiliate_code: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None


class ClickIn(BaseModel):
    product_id: int
    affiliate_code: Optional[str] = None
    referrer: Optional[str] = None


class UserCreateIn(BaseModel):
    username: str
    password: str
    is_admin: bool = False


# ---------------- Auth helpers ----------------

def create_access_token(data: Dict[str, Any], expires_delta: timedelta = timedelta(hours=12)) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInfo:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        username: str = payload.get("sub")
        is_admin: bool = bool(payload.get("is_admin", False))
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return UserInfo(username=username, is_admin=is_admin)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ---------------- Startup ----------------

@app.on_event("startup")
def startup() -> None:
    ensure_default_admin()


# ---------------- Health ----------------

@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


# ---------------- Auth ----------------

@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = repo.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user["username"], "is_admin": bool(user["is_admin"])})
    return Token(access_token=token)


# ---------------- Settings ----------------

@app.get("/api/settings")
def get_settings() -> Dict[str, str]:
    return repo.list_settings()


@app.put("/api/settings")
def update_settings(body: SettingUpdate, user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    if body.site_name is not None:
        repo.set_setting("site_name", body.site_name)
    return repo.list_settings()


# ---------------- Categories ----------------

@app.get("/api/categories")
def list_categories():
    return [dict(r) for r in repo.list_categories()]


@app.post("/api/categories")
def create_category(body: CategoryIn, user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    category_id = repo.create_category(body.name, slug_value=body.slug)
    return {"id": category_id}


# ---------------- Products ----------------

@app.get("/api/products")
def list_products(search: Optional[str] = None, category: Optional[str] = None, active_only: bool = True):
    rows = repo.list_products(search=search, category_slug=category, active_only=active_only)
    return [dict(r) for r in rows]


@app.post("/api/products")
def create_product(body: ProductIn, user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    pid = repo.create_product(
        title=body.title,
        description=body.description or "",
        price=body.price,
        currency=body.currency or "USD",
        image_url=body.image_url,
        category_name=body.category_name,
        affiliate_url_template=body.affiliate_url_template,
        active=body.active,
    )
    return {"id": pid}


@app.put("/api/products/{product_id}")
def update_product(product_id: int, body: ProductIn, user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    repo.update_product(
        product_id,
        title=body.title,
        description=body.description or "",
        price=body.price,
        currency=body.currency or "USD",
        image_url=body.image_url,
        category_name=body.category_name,
        affiliate_url_template=body.affiliate_url_template,
        active=body.active,
    )
    return {"ok": True}


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    repo.delete_product(product_id)
    return {"ok": True}


@app.post("/api/products:import")
def import_products(body: ImportRequest, user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    created, updated = import_products_from_json_feed(body.feed_url)
    return {"created": created, "updated": updated}


@app.get("/api/products/slug/{slug}")
def get_product_by_slug(slug: str):
    row = repo.get_product_by_slug(slug)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return dict(row)


# ---------------- Blog ----------------

@app.get("/api/blog")
def list_blog(status: Optional[str] = "published"):
    rows = repo.list_blog_posts(status=status)
    return [dict(r) for r in rows]


@app.get("/api/blog/{slug}")
def get_blog(slug: str):
    row = repo.get_blog_post_by_slug(slug)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return dict(row)


@app.post("/api/blog")
def create_blog_post(body: BlogPostIn, user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    pid = repo.create_blog_post(body.title, body.content_md, body.status)
    return {"id": pid}


@app.put("/api/blog/{post_id}")
def update_blog_post(post_id: int, body: BlogPostIn, user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    repo.update_blog_post(post_id, body.title, body.content_md, body.status)
    return {"ok": True}


# ---------------- Affiliates ----------------

@app.get("/api/affiliates")
def list_affiliates():
    return [dict(r) for r in repo.list_affiliates()]


@app.post("/api/affiliates")
def create_affiliate(body: AffiliateIn, user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    aid = repo.create_affiliate(body.name, body.code)
    return {"id": aid}


# ---------------- Orders & Clicks ----------------

@app.post("/api/orders")
def create_order(body: OrderIn):
    aff_id = None
    if body.affiliate_code:
        aff = repo.get_affiliate_by_code(body.affiliate_code)
        aff_id = aff["id"] if aff else None
    prod = repo.get_product_by_id(body.product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    price = body.price if body.price is not None else float(prod["price"])
    currency = body.currency or prod["currency"] or "USD"
    oid = repo.create_order(body.product_id, aff_id, price, currency)
    return {"id": oid}


@app.post("/api/clicks")
def log_click(body: ClickIn):
    aff_id = None
    if body.affiliate_code:
        aff = repo.get_affiliate_by_code(body.affiliate_code)
        aff_id = aff["id"] if aff else None
    repo.log_click(body.product_id, aff_id, body.referrer)
    return {"ok": True}


# ---------------- Users (admin) ----------------

@app.get("/api/users")
def list_users(user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    return [
        {"username": u["username"], "is_admin": bool(u["is_admin"]), "created_at": u["created_at"]}
        for u in repo.list_users()
    ]


@app.post("/api/users")
def create_user(body: UserCreateIn, user: UserInfo = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    repo.create_user(body.username, hash_password(body.password), is_admin=body.is_admin)
    return {"ok": True}