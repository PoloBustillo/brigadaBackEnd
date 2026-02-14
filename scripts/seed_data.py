"""Seed database with initial test data."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole

def seed_users():
    """Create initial test users."""
    db = SessionLocal()
    
    try:
        # Check if users already exist
        if db.query(User).first():
            print("Users already exist. Skipping seed.")
            return
        
        # Create test users
        users = [
            User(
                email="admin@brigada.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Admin User",
                role=UserRole.ADMIN,
                phone="+1234567890"
            ),
            User(
                email="encargado@brigada.com",
                hashed_password=get_password_hash("encargado123"),
                full_name="Encargado User",
                role=UserRole.ENCARGADO,
                phone="+1234567891"
            ),
            User(
                email="brigadista@brigada.com",
                hashed_password=get_password_hash("brigadista123"),
                full_name="Brigadista User",
                role=UserRole.BRIGADISTA,
                phone="+1234567892"
            ),
        ]
        
        db.add_all(users)
        db.commit()
        
        print("✅ Seeded test users:")
        print("  - admin@brigada.com (password: admin123)")
        print("  - encargado@brigada.com (password: encargado123)")
        print("  - brigadista@brigada.com (password: brigadista123)")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Seed data
    seed_users()
