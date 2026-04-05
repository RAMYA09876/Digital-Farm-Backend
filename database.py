import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./digitalfarm.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# ✅ SAVE PREDICTION FUNCTION (ONLY HERE)
def save_prediction(dose, days, mrl, prediction, confidence, reason):
    conn = sqlite3.connect("digitalfarm.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dose REAL,
        days REAL,
        mrl REAL,
        result TEXT,
        confidence REAL,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    INSERT INTO predictions (dose, days, mrl, result, confidence, reason)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (dose, days, mrl, prediction, confidence, reason))

    conn.commit()
    conn.close()