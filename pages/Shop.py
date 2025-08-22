import streamlit as st

from app import repositories as repo

st.set_page_config(page_title="Shop", layout="wide")

site_name = repo.get_setting("site_name", "Affiliate eShop") or "Affiliate eShop"
st.title(f"🛍️ {site_name} – Shop")

with st.sidebar:
    st.header("Filters")
    search = st.text_input("Search products")
    categories = repo.list_categories()
    category_options = ["All"] + [c["slug"] for c in categories]
    category_labels = {"All": "All"}
    for c in categories:
        category_labels[c["slug"]] = c["name"]
    selected_category_slug = st.selectbox(
        "Category",
        options=category_options,
        format_func=lambda v: category_labels.get(v, v),
    )
    st.markdown("---")
    st.subheader("Affiliate")
    affiliate_code = st.text_input("Affiliate code (optional)", value=st.session_state.get("affiliate_code", ""))
    st.session_state["affiliate_code"] = affiliate_code.strip()

if selected_category_slug == "All":
    products = repo.list_products(search=search or None, category_slug=None, active_only=True)
else:
    products = repo.list_products(search=search or None, category_slug=selected_category_slug, active_only=True)

cols = st.columns(3)
for idx, p in enumerate(products):
    with cols[idx % 3]:
        if p["image_url"]:
            st.image(p["image_url"], use_column_width=True)
        st.subheader(p["title"])
        price_text = f"{p['price']:.2f} {p['currency']}"
        st.caption((p["category_name"] or "") + (" · " if p["category_name"] else "") + price_text)
        st.write((p["description"] or "")[:160] + ("…" if p["description"] and len(p["description"]) > 160 else ""))
        # Track via Redirect page
        aff = st.session_state.get("affiliate_code", "")
        redirect_url = f"./Redirect?p={p['slug']}&a={aff}"
        st.link_button("Buy now", redirect_url)