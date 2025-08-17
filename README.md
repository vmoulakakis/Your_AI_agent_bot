# 🛍️ Affiliate eShop (Streamlit)

A minimal affiliate eShop MVP with:
- WordPress-like admin area (settings, product importer from JSON feed, blog, users)
- Public Shop page with affiliate link templating
- Blog page for SEO content
- Basic dashboard

### Run locally

1. Install requirements (user scope if needed):

```
python3 -m pip install -r requirements.txt --user --break-system-packages
```

2. Run the app:

```
streamlit run streamlit_app.py
```

Open the sidebar to switch pages: Shop, Blog, Dashboard, Admin. Default admin user is `admin`/`admin` (change it in Admin → Users).
