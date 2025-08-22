import time
import streamlit as st
import requests

from app import repositories as repo
from app.workflows import import_products_from_json_feed

st.set_page_config(page_title="Trends", layout="wide")

st.title("📈 Internet Trends")

TAB_HN, TAB_REDDIT = st.tabs(["Hacker News", "Reddit"]) 

with TAB_HN:
    st.caption("Top stories from Hacker News")
    try:
        top = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=20).json()[:20]
        items = []
        for sid in top:
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=20).json()
            if not item:
                continue
            items.append({
                "id": sid,
                "title": item.get("title"),
                "url": item.get("url") or f"https://news.ycombinator.com/item?id={sid}",
                "score": item.get("score"),
                "by": item.get("by"),
            })
        for it in items:
            st.subheader(it["title"]) 
            st.caption(f"score: {it['score']} by {it['by']}")
            st.markdown(f"[Open]({it['url']})")
            if st.button("Add as product", key=f"hn_add_{it['id']}"):
                repo.create_product(
                    title=it["title"],
                    description=f"Trending on HN (by {it['by']}). Auto-imported.",
                    price=0.0,
                    currency="USD",
                    image_url=None,
                    category_name="trending",
                    affiliate_url_template=it["url"],
                    active=True,
                )
                st.success("Added to products")
    except Exception as e:
        st.error(f"Failed to fetch HN: {e}")

with TAB_REDDIT:
    st.caption("Hot posts from /r/deals and /r/BuyItForLife")
    subreddits = ["deals", "BuyItForLife"]
    for sub in subreddits:
        st.subheader(f"r/{sub}")
        try:
            headers = {"User-Agent": "affiliate-eshop/1.0"}
            resp = requests.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=15", headers=headers, timeout=20)
            data = resp.json()
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                title = post.get("title")
                url = post.get("url_overridden_by_dest") or ("https://reddit.com" + post.get("permalink", ""))
                st.write(f"- {title} → [link]({url})")
                if st.button("Add as product", key=f"rd_add_{post.get('id')}"):
                    repo.create_product(
                        title=title or "Reddit item",
                        description=f"Trending on r/{sub}. Auto-imported.",
                        price=0.0,
                        currency="USD",
                        image_url=None,
                        category_name="trending",
                        affiliate_url_template=url,
                        active=True,
                    )
                    st.success("Added to products")
        except Exception as e:
            st.error(f"Failed to fetch r/{sub}: {e}")

st.markdown("---")
st.subheader("Import products from a JSON URL")
feed_url = st.text_input("Feed URL (JSON)")
if st.button("Import feed") and feed_url:
    try:
        created, updated = import_products_from_json_feed(feed_url)
        st.success(f"Imported. Created: {created}, Updated: {updated}")
    except Exception as e:
        st.error(f"Import failed: {e}")