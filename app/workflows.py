import json
from typing import Any, Dict, List, Tuple

import requests
from urllib.parse import urlparse

from .utils import slugify
from . import repositories as repo


def _normalize_product_record(item: Dict[str, Any]) -> Dict[str, Any]:
    title = str(
        item.get("title")
        or item.get("name")
        or item.get("product_name")
        or item.get("id")
        or "Untitled"
    )
    price_value = item.get("price") or item.get("amount") or item.get("price_cents")
    if isinstance(price_value, str):
        try:
            price_value = float(price_value)
        except Exception:
            price_value = 0
    if isinstance(price_value, int):
        # if looks like cents, convert to dollars if large
        price_value = price_value / 100.0 if price_value > 1000 else float(price_value)
    currency = item.get("currency") or item.get("ccy") or "USD"
    image_url = item.get("image_url") or item.get("image") or item.get("thumbnail")
    category_name = item.get("category") or item.get("category_name")
    slug_value = item.get("slug") or slugify(title)
    description = (
        item.get("description")
        or item.get("summary")
        or item.get("content")
        or ""
    )
    affiliate_url_template = (
        item.get("affiliate_url_template")
        or item.get("buy_url")
        or item.get("url")
    )
    if affiliate_url_template and "{affiliate_code}" not in affiliate_url_template:
        # Best effort: append placeholder
        join_char = "&" if "?" in affiliate_url_template else "?"
        affiliate_url_template = f"{affiliate_url_template}{join_char}aff={{affiliate_code}}"
    return {
        "title": title,
        "slug": slug_value,
        "description": description,
        "price": float(price_value or 0),
        "currency": str(currency),
        "image_url": image_url,
        "category_name": category_name,
        "affiliate_url_template": affiliate_url_template,
        "active": True,
    }


def _load_json_from_source(feed_url: str) -> Any:
    parsed = urlparse(feed_url)
    if parsed.scheme in ("http", "https"):
        resp = requests.get(feed_url, timeout=20)
        resp.raise_for_status()
        return resp.json()
    if parsed.scheme == "file":
        path = parsed.path
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Treat as local filesystem path
    try:
        with open(feed_url, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Unsupported or not found feed source: {feed_url}")


def import_products_from_json_feed(feed_url: str) -> Tuple[int, int]:
    if not feed_url:
        return (0, 0)
    data = _load_json_from_source(feed_url)
    products: List[Dict[str, Any]]
    if isinstance(data, dict) and "products" in data:
        products = data["products"]  # type: ignore
    elif isinstance(data, list):
        products = data  # type: ignore
    else:
        # Try nested common shapes
        for key in ["items", "data", "results"]:
            if isinstance(data, dict) and key in data and isinstance(data[key], list):
                products = data[key]  # type: ignore
                break
        else:
            products = []
    created = 0
    updated = 0
    for item in products:
        normalized = _normalize_product_record(item)
        slug_value = normalized.get("slug") or slugify(normalized.get("title", ""))
        existing = repo.get_product_by_slug(slug_value)
        repo.upsert_product_by_slug(slug_value, normalized)
        if existing:
            updated += 1
        else:
            created += 1
    return (created, updated)