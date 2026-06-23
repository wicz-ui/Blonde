import os
import sqlite3
from pathlib import Path
from flask import g

from .config import DATABASE


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, timeout=30, isolation_level=None)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
