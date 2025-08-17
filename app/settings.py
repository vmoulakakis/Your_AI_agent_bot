import os


def get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_data_dir() -> str:
    data_dir = os.path.join(get_project_root(), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_db_path() -> str:
    return os.path.join(get_data_dir(), "app.db")


def get_default_site_name() -> str:
    return "Affiliate eShop"