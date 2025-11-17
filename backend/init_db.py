"""
Initialize database tables
Run this inside the container: docker-compose exec backend python init_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_db

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("✓ Database initialized successfully!")
