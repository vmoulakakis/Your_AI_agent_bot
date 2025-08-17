import streamlit as st

from app.auth import ensure_default_admin
from app import repositories as repo

st.set_page_config(page_title="Affiliate eShop", layout="wide")

ensure_default_admin()

site_name = repo.get_setting("site_name", "Affiliate eShop") or "Affiliate eShop"

st.title(f"{site_name}")

st.write(
    "Welcome to your affiliate eShop. Use the sidebar to navigate: Shop, Blog, Dashboard, Admin."
)

st.markdown(
    """
- Shop: Browse products and generate affiliate links
- Blog: Publish SEO content
- Dashboard: View basic stats
- Admin: Manage settings, import products, edit content, users
    """
)
