import streamlit as st
from app import repositories as repo

st.set_page_config(page_title="Dashboard", layout="wide")

st.title("📊 Dashboard")

st.caption("Basic analytics snapshot")

products = repo.list_products(active_only=False)
posts = repo.list_blog_posts()
affiliates = repo.list_affiliates()

col1, col2, col3 = st.columns(3)
col1.metric("Products", len(products))
col2.metric("Blog posts", len(posts))
col3.metric("Affiliates", len(affiliates))