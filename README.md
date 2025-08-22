# AI Affiliate eShop (Streamlit)

A responsive, elegant affiliate eShop with:
- Product catalog, categories, affiliate link tracking
- Admin area for settings, products, blog
- Blog with Markdown posts
- AI shopping assistant (LLM) with persistent memory
- Trend discovery (Hacker News, Reddit) with one-click product import

## Quick start

1) Create and activate Python virtual env (if needed):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install requirements:

```bash
pip install -r requirements.txt
```

3) Run the app:

```bash
streamlit run streamlit_app.py
```

Open the URL shown in the terminal.

## Configuration

- OpenAI API key: Set environment variable `OPENAI_API_KEY` or go to `Admin -> Settings` and save the key.
- Database: SQLite file at `data/app.db` is created automatically.

## Pages

- Home: Overview
- Shop: Browse products, filter by category, tracked Buy with redirect
- Blog: Read published posts
- Trends: View HN/Reddit trends and import as products
- Chat: AI assistant with memory
- Admin: Settings, product import, product CRUD, blog, users

## Importing products

- Admin -> Products -> "Import products from JSON feed": Provide a URL or local file path to a JSON with either top-level list or `{ "products": [...] }` shape.
- Trends page has quick-add buttons from HN/Reddit.

## Security

- Default admin user `admin` with password `admin` is created automatically on first run; change it in Admin.

## Notes

- This app stores AI memories and chat history for each session.
- For production, consider adding authentication for Admin, rate limiting, and a WAF/CDN.
