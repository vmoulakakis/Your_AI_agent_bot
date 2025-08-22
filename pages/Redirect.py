import streamlit as st
from urllib.parse import urlparse, parse_qs

from app import repositories as repo

st.set_page_config(page_title="Redirect", layout="centered")

params = st.experimental_get_query_params()
product_slug = (params.get("p") or [""])[0]
affiliate_code = (params.get("a") or [""])[0]
ref = (params.get("ref") or [""])[0]

product = repo.get_product_by_slug(product_slug)

if not product:
    st.error("Product not found")
else:
    template = product["affiliate_url_template"] or "#"
    target = template.replace("{affiliate_code}", affiliate_code) if affiliate_code else template
    st.write("Redirecting to:")
    st.markdown(f"[{target}]({target})")
    repo.log_click(product["id"], None, ref)
    st.markdown(f"<meta http-equiv='refresh' content='0;url={target}'>", unsafe_allow_html=True)