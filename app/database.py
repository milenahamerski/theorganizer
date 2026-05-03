import pymysql
import os
import time

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "user": os.getenv("DB_USER", "theorganizer"),
    "password": os.getenv("DB_PASSWORD", "devops"),
    "database": os.getenv("DB_NAME", "theorganizer"),
    "port": 3306,
}


def get_connection():
    return pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        port=DB_CONFIG["port"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
        autocommit=True,
    )


def wait_db():
    print("[DB] aguardando MariaDB...")

    for i in range(40):
        try:
            conn = pymysql.connect(
                host=DB_CONFIG["host"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                port=DB_CONFIG["port"],
                cursorclass=pymysql.cursors.Cursor,
            )
            conn.close()

            print("[DB] MariaDB OK")
            return

        except Exception as e:
            print(f"[DB] tentativa {i+1}/40 - {e}")
            time.sleep(2)

    raise Exception("Banco não subiu")


def init_db():
    wait_db()

    # cria banco
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG["port"],
        autocommit=True,
    )

    cur = conn.cursor()

    cur.execute(f"""
        CREATE DATABASE IF NOT EXISTS {DB_CONFIG["database"]}
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_general_ci
    """)

    cur.close()
    conn.close()

    # cria tabela
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            year INT,
            image_url VARCHAR(500)
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
