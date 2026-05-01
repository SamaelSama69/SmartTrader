"""
SQLite database for persistent, concurrent-safe storage
Replaces JSON files for better querying and multi-process access
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import threading


class Database:
    """SQLite-backed storage for SmartTrader"""

    def __init__(self, db_path: str = "smart_trader.db"):
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self):
        """Get a thread-local connection"""
        return sqlite3.connect(str(self.db_path), check_same_thread=False)

    def _init_db(self):
        """Initialize database tables"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Predictions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    outcome_recorded INTEGER DEFAULT 0
                )
            ''')

            # Outcomes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    correct INTEGER,
                    timestamp TEXT NOT NULL
                )
            ''')

            # Trade logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    side TEXT NOT NULL,
                    shares INTEGER,
                    price REAL,
                    timestamp TEXT NOT NULL,
                    pnl REAL
                )
            ''')

            conn.commit()
            conn.close()

    def save_prediction(self, pred: Dict):
        """Save a prediction to database"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO predictions (id, ticker, prediction, timestamp, outcome_recorded) VALUES (?, ?, ?, ?, ?)",
                (
                    pred['id'],
                    pred['ticker'],
                    json.dumps(pred['prediction']),
                    pred['timestamp'],
                    1 if pred.get('outcome_recorded') else 0
                )
            )
            conn.commit()
            conn.close()

    def get_predictions(self, ticker: Optional[str] = None) -> List[Dict]:
        """Get predictions, optionally filtered by ticker"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            if ticker:
                cursor.execute("SELECT * FROM predictions WHERE ticker = ?", (ticker,))
            else:
                cursor.execute("SELECT * FROM predictions")

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'id': row[0],
                    'ticker': row[1],
                    'prediction': json.loads(row[2]),
                    'timestamp': row[3],
                    'outcome_recorded': bool(row[4])
                }
                for row in rows
            ]

    def log_trade(self, ticker: str, side: str, shares: int, price: float, pnl: float = 0):
        """Log a trade to database"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO trade_logs (ticker, side, shares, price, timestamp, pnl) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    ticker, side, shares, price,
                    datetime.now().isoformat(),
                    pnl
                )
            )
            conn.commit()
            conn.close()
