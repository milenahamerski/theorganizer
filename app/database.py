import mysql.connector
from mysql.connector import Error

import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "senha3099"),
    "database": os.getenv("DB_NAME", "bookdb")
}


def get_connection():
    """Abre conexão com o banco MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Cria o banco e a tabela se não existirem."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cur.close()
        conn.close()

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(255) NOT NULL,
                year INT
            )
        """)
        conn.commit()
        cur.close()
        conn.close()

    except Error as e:
        print("Erro ao inicializar o banco:", e)
