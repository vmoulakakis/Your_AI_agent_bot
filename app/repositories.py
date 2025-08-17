import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from .database import get_connection
from .utils import slugify, utc_now_iso


# -------------------- Users --------------------

def count_users() -> int:
    conn = get_connection()
    cur = conn.execute("SELECT COUNT(*) AS cnt FROM users")
    row = cur.fetchone()
    return int(row[0]) if row else 0


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cur.fetchone()


def list_users() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM users ORDER BY created_at DESC")
    return list(cur.fetchall())


def create_user(username: str, password_hash: str, is_admin: bool = False) -> int:
    conn = get_connection()
    conn.execute(
        "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?,?,?,?)",
        (username, password_hash, 1 if is_admin else 0, utc_now_iso()),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def set_user_password(username: str, password_hash: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (password_hash, username),
    )
    conn.commit()


# -------------------- Settings --------------------

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    conn = get_connection()
    cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    return row[0] if row else default


def set_setting(key: str, value: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


def list_settings() -> Dict[str, str]:
    conn = get_connection()
    cur = conn.execute("SELECT key, value FROM settings")
    result: Dict[str, str] = {}
    for row in cur.fetchall():
        result[row[0]] = row[1]
    return result


# -------------------- Categories --------------------

def list_categories() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM categories ORDER BY name ASC")
    return list(cur.fetchall())


def get_category_by_id(category_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
    return cur.fetchone()


def get_category_by_slug(slug: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM categories WHERE slug = ?", (slug,))
    return cur.fetchone()


def create_category(name: str, slug_value: Optional[str] = None) -> int:
    slug_value = slug_value or slugify(name)
    conn = get_connection()
    conn.execute(
        "INSERT INTO categories (name, slug) VALUES (?, ?)",
        (name, slug_value),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def update_category(category_id: int, name: str, slug_value: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE categories SET name = ?, slug = ? WHERE id = ?",
        (name, slug_value, category_id),
    )
    conn.commit()


def delete_category(category_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()


# -------------------- Products --------------------

def list_products(
    search: Optional[str] = None,
    category_slug: Optional[str] = None,
    active_only: bool = True,
) -> List[sqlite3.Row]:
    conn = get_connection()
    where = []
    params: List[Any] = []
    if search:
        where.append("(p.title LIKE ? OR p.description LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])
    if category_slug:
        where.append("c.slug = ?")
        params.append(category_slug)
    if active_only:
        where.append("p.active = 1")
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    sql = (
        "SELECT p.*, c.name AS category_name, c.slug AS category_slug FROM products p "
        "LEFT JOIN categories c ON p.category_id = c.id "
        + where_sql +
        " ORDER BY p.created_at DESC"
    )
    cur = conn.execute(sql, tuple(params))
    return list(cur.fetchall())


def get_product_by_id(product_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    return cur.fetchone()


def get_product_by_slug(slug_value: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM products WHERE slug = ?", (slug_value,))
    return cur.fetchone()


def _ensure_category_by_name(category_name: Optional[str]) -> Optional[int]:
    if not category_name:
        return None
    conn = get_connection()
    slug_value = slugify(category_name)
    cur = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug_value,))
    row = cur.fetchone()
    if row:
        return int(row[0])
    conn.execute("INSERT INTO categories (name, slug) VALUES (?, ?)", (category_name, slug_value))
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def create_product(
    title: str,
    description: str,
    price: float,
    currency: str,
    image_url: Optional[str],
    category_name: Optional[str],
    affiliate_url_template: Optional[str],
    active: bool = True,
) -> int:
    slug_value = slugify(title)
    category_id = _ensure_category_by_name(category_name)
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO products (title, slug, description, price, currency, image_url, category_id, affiliate_url_template, active, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            title,
            slug_value,
            description,
            float(price),
            currency or "USD",
            image_url,
            category_id,
            affiliate_url_template,
            1 if active else 0,
            utc_now_iso(),
        ),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def update_product(
    product_id: int,
    title: str,
    description: str,
    price: float,
    currency: str,
    image_url: Optional[str],
    category_name: Optional[str],
    affiliate_url_template: Optional[str],
    active: bool,
) -> None:
    slug_value = slugify(title)
    category_id = _ensure_category_by_name(category_name)
    conn = get_connection()
    conn.execute(
        """
        UPDATE products
        SET title = ?, slug = ?, description = ?, price = ?, currency = ?, image_url = ?, category_id = ?, affiliate_url_template = ?, active = ?
        WHERE id = ?
        """,
        (
            title,
            slug_value,
            description,
            float(price),
            currency or "USD",
            image_url,
            category_id,
            affiliate_url_template,
            1 if active else 0,
            product_id,
        ),
    )
    conn.commit()


def delete_product(product_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()


def upsert_product_by_slug(
    slug_value: str,
    data: Dict[str, Any],
) -> int:
    existing = get_product_by_slug(slug_value)
    if existing:
        update_product(
            existing["id"],
            title=data.get("title", existing["title"]),
            description=data.get("description", existing["description"]),
            price=float(data.get("price", existing["price"])),
            currency=data.get("currency", existing["currency"]),
            image_url=data.get("image_url", existing["image_url"]),
            category_name=data.get("category_name"),
            affiliate_url_template=data.get("affiliate_url_template", existing["affiliate_url_template"]),
            active=bool(data.get("active", existing["active"]))
        )
        return int(existing["id"])
    return create_product(
        title=data.get("title", slug_value),
        description=data.get("description", ""),
        price=float(data.get("price", 0)),
        currency=data.get("currency", "USD"),
        image_url=data.get("image_url"),
        category_name=data.get("category_name"),
        affiliate_url_template=data.get("affiliate_url_template"),
        active=bool(data.get("active", True)),
    )


# -------------------- Affiliates --------------------

def list_affiliates() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM affiliates ORDER BY created_at DESC")
    return list(cur.fetchall())


def get_affiliate_by_code(code: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM affiliates WHERE code = ?", (code,))
    return cur.fetchone()


def create_affiliate(name: str, code: str) -> int:
    conn = get_connection()
    conn.execute(
        "INSERT INTO affiliates (name, code, created_at) VALUES (?,?,?)",
        (name, code, utc_now_iso()),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


# -------------------- Orders --------------------

def create_order(
    product_id: int,
    affiliate_id: Optional[int],
    price: float,
    currency: str,
    status: str = "created",
) -> int:
    conn = get_connection()
    conn.execute(
        "INSERT INTO orders (product_id, affiliate_id, price, currency, status, created_at) VALUES (?,?,?,?,?,?)",
        (product_id, affiliate_id, float(price), currency, status, utc_now_iso()),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


# -------------------- Clicks --------------------

def log_click(product_id: int, affiliate_id: Optional[int], referrer: Optional[str]) -> int:
    conn = get_connection()
    conn.execute(
        "INSERT INTO clicks (product_id, affiliate_id, referrer, created_at) VALUES (?,?,?,?)",
        (product_id, affiliate_id, referrer, utc_now_iso()),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


# -------------------- Blog --------------------

def list_blog_posts(status: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_connection()
    where = []
    params: List[Any] = []
    if status:
        where.append("status = ?")
        params.append(status)
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    cur = conn.execute(
        "SELECT * FROM blog_posts" + where_sql + " ORDER BY created_at DESC",
        tuple(params),
    )
    return list(cur.fetchall())


def get_blog_post_by_slug(slug_value: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM blog_posts WHERE slug = ?", (slug_value,))
    return cur.fetchone()


def create_blog_post(title: str, content_md: str, status: str = "draft") -> int:
    conn = get_connection()
    conn.execute(
        "INSERT INTO blog_posts (title, slug, content_md, status, created_at, updated_at) VALUES (?,?,?,?,?,?)",
        (title, slugify(title), content_md, status, utc_now_iso(), utc_now_iso()),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def update_blog_post(
    post_id: int,
    title: str,
    content_md: str,
    status: str,
) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE blog_posts SET title = ?, slug = ?, content_md = ?, status = ?, updated_at = ? WHERE id = ?",
        (title, slugify(title), content_md, status, utc_now_iso(), post_id),
    )
    conn.commit()


# -------------------- Workflows --------------------

def list_workflows() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM workflows ORDER BY created_at DESC")
    return list(cur.fetchall())


def create_workflow(
    name: str,
    trigger_type: str,
    trigger_config: str,
    nodes_json: str,
    active: bool = True,
) -> int:
    conn = get_connection()
    conn.execute(
        "INSERT INTO workflows (name, active, trigger_type, trigger_config, nodes_json, created_at) VALUES (?,?,?,?,?,?)",
        (name, 1 if active else 0, trigger_type, trigger_config, nodes_json, utc_now_iso()),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def get_workflow_by_id(workflow_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
    return cur.fetchone()


def update_workflow(
    workflow_id: int,
    name: Optional[str] = None,
    trigger_type: Optional[str] = None,
    trigger_config: Optional[str] = None,
    nodes_json: Optional[str] = None,
    active: Optional[bool] = None,
) -> None:
    sets: List[str] = []
    params: List[Any] = []
    if name is not None:
        sets.append("name = ?")
        params.append(name)
    if trigger_type is not None:
        sets.append("trigger_type = ?")
        params.append(trigger_type)
    if trigger_config is not None:
        sets.append("trigger_config = ?")
        params.append(trigger_config)
    if nodes_json is not None:
        sets.append("nodes_json = ?")
        params.append(nodes_json)
    if active is not None:
        sets.append("active = ?")
        params.append(1 if active else 0)
    if not sets:
        return
    params.append(workflow_id)
    sql = "UPDATE workflows SET " + ", ".join(sets) + " WHERE id = ?"
    conn = get_connection()
    conn.execute(sql, tuple(params))
    conn.commit()