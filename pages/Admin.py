import json
import streamlit as st

from app import repositories as repo
from app.auth import ensure_default_admin, hash_password
from app.workflows import import_products_from_json_feed

st.set_page_config(page_title="Admin", layout="wide")

ensure_default_admin()

st.title("⚙️ Admin Area")

TAB_SETTINGS, TAB_PRODUCTS, TAB_BLOG, TAB_USERS = st.tabs([
    "Settings",
    "Products",
    "Blog",
    "Users",
])

with TAB_SETTINGS:
    st.subheader("Site Settings")
    site_name = st.text_input("Site name", value=repo.get_setting("site_name", "Affiliate eShop") or "Affiliate eShop")
    openai_api_key = st.text_input("OpenAI API key (stored securely in DB)", type="password", value=repo.get_setting("openai_api_key", "") or "")
    if st.button("Save settings"):
        repo.set_setting("site_name", site_name)
        if openai_api_key:
            repo.set_setting("openai_api_key", openai_api_key)
        st.success("Settings saved")

with TAB_PRODUCTS:
    st.subheader("Import products from JSON feed")
    feed_url = st.text_input("Feed URL")
    if st.button("Import now") and feed_url:
        try:
            created, updated = import_products_from_json_feed(feed_url)
            st.success(f"Imported products. Created: {created}, Updated: {updated}")
        except Exception as e:
            st.error(f"Import failed: {e}")
    st.markdown("---")
    st.subheader("Existing products")
    products = repo.list_products(active_only=False)
    for p in products:
        with st.expander(p["title"]):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_title = st.text_input("Title", value=p["title"], key=f"title_{p['id']}")
                new_desc = st.text_area("Description", value=p["description"] or "", key=f"desc_{p['id']}")
                new_price = st.number_input("Price", value=float(p["price"]), key=f"price_{p['id']}")
                new_currency = st.text_input("Currency", value=p["currency"], key=f"currency_{p['id']}")
                new_image = st.text_input("Image URL", value=p["image_url"] or "", key=f"img_{p['id']}")
                new_category = st.text_input("Category", value=p["category_name"] or "", key=f"cat_{p['id']}")
                new_template = st.text_input("Affiliate URL template", value=p["affiliate_url_template"] or "", key=f"tmpl_{p['id']}")
                new_active = st.checkbox("Active", value=bool(p["active"]), key=f"act_{p['id']}")
            with col2:
                if p["image_url"]:
                    st.image(p["image_url"], use_column_width=True)
            if st.button("Save", key=f"save_{p['id']}"):
                repo.update_product(
                    p["id"],
                    title=new_title,
                    description=new_desc,
                    price=float(new_price),
                    currency=new_currency,
                    image_url=new_image or None,
                    category_name=new_category or None,
                    affiliate_url_template=new_template or None,
                    active=new_active,
                )
                st.success("Saved")
            if st.button("Delete", key=f"del_{p['id']}"):
                repo.delete_product(p["id"])
                st.warning("Deleted. Reload the page to refresh list.")

with TAB_BLOG:
    st.subheader("Write a blog post")
    title = st.text_input("Title")
    content_md = st.text_area("Content (Markdown)")
    status = st.selectbox("Status", ["draft", "published"]) 
    if st.button("Publish"):
        if not title:
            st.error("Title required")
        else:
            repo.create_blog_post(title, content_md, status)
            st.success("Post saved")
    st.markdown("---")
    st.subheader("Existing posts")
    posts = repo.list_blog_posts()
    for p in posts:
        with st.expander(p["title"]):
            e_title = st.text_input("Title", value=p["title"], key=f"pt_{p['id']}")
            e_content = st.text_area("Content", value=p["content_md"], key=f"pc_{p['id']}")
            e_status = st.selectbox("Status", ["draft", "published"], index=0 if p["status"]=="draft" else 1, key=f"ps_{p['id']}")
            if st.button("Save post", key=f"psv_{p['id']}"):
                repo.update_blog_post(p["id"], e_title, e_content, e_status)
                st.success("Saved")

with TAB_USERS:
    st.subheader("Users")
    users = repo.list_users()
    for u in users:
        st.write(f"{u['username']} (admin: {'yes' if u['is_admin'] else 'no'})")
    st.markdown("---")
    st.subheader("Create user")
    new_username = st.text_input("Username")
    new_password = st.text_input("Password", type="password")
    is_admin = st.checkbox("Is admin")
    if st.button("Create user"):
        if not new_username or not new_password:
            st.error("Username and password required")
        else:
            repo.create_user(new_username, hash_password(new_password), is_admin=is_admin)
            st.success("User created")