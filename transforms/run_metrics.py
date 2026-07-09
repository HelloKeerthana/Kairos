from sqlalchemy import text
from transforms.db import get_engine

def main():
    with open("transforms/metrics.sql", "r") as f:
        sql = f.read()

    engine = get_engine()
    with engine.connect() as conn:
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        conn.commit()
    print("Metric views created.")

if __name__ == "__main__":
    main()