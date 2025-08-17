import streamlit as st

from app import repositories as repo

st.set_page_config(page_title="Blog", layout="wide")

site_name = repo.get_setting("site_name", "Affiliate eShop") or "Affiliate eShop"
st.title(f"📰 {site_name} – Blog")

params = st.experimental_get_query_params()
slug = (params.get("post") or [None])[0]

if slug:
    post = repo.get_blog_post_by_slug(slug)
    if not post or post["status"] != "published":
        st.error("Post not found or not published")
    else:
        st.subheader(post["title"])
        st.markdown(post["content_md"])
        st.markdown("[← Back to all posts](./Blog)")
else:
    posts = repo.list_blog_posts(status="published")
    if not posts:
        st.info("No blog posts yet.")
    for p in posts:
        st.subheader(p["title"])
        st.caption(p["created_at"])
        excerpt = (p["content_md"] or "").split("\n\n")[0]
        st.write(excerpt[:240] + ("…" if len(excerpt) > 240 else ""))
        st.markdown(f"[Read more](./Blog?post={p['slug']})")