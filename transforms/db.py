from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = "kairos"
DB_PASSWORD = "kairos_pass"
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = "kairos_db"


def get_engine():
    conn_str = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    print(conn_str)
    return create_engine(conn_str)
