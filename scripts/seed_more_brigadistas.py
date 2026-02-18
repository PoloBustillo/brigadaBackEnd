"""Add extra demo brigadistas and more assignments."""
import sys
import logging
from pathlib import Path

logging.disable(logging.CRITICAL)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.assignment import Assignment, AssignmentStatus
from app.models.survey import Survey
from app.core.security import get_password_hash

db = SessionLocal()

# ── Create extra brigadistas ──────────────────────────────────────────────
new_users = [
    ("María García López", "maria.garcia@brigada.com"),
    ("Carlos Hernández", "carlos.hernandez@brigada.com"),
    ("Ana Martínez Ruiz", "ana.martinez@brigada.com"),
    ("Luis Rodríguez Torres", "luis.rodriguez@brigada.com"),
]
created_ids = []
for name, email in new_users:
    existing = db.query(User).filter(User.email == email).first()
    if not existing:
        u = User(
            full_name=name,
            email=email,
            hashed_password=get_password_hash("brigada123"),
            role=UserRole.BRIGADISTA,
            is_active=True,
        )
        db.add(u)
        db.flush()
        created_ids.append((u.id, name))
        print(f"  + Created brigadista: {name} (id will be assigned)")
    else:
        created_ids.append((existing.id, name))
        print(f"  ✓ Exists: {name}")

db.commit()

# Reload to get IDs
all_brigadistas = (
    db.query(User)
    .filter(User.role == UserRole.BRIGADISTA, User.is_active == True)
    .all()
)
surveys = db.query(Survey).filter(Survey.is_active == True).all()

print(f"\nBrigadistas ({len(all_brigadistas)}): {[(u.id, u.full_name) for u in all_brigadistas]}")
print(f"Surveys ({len(surveys)}): {[s.id for s in surveys]}")

ZONES = [
    "Colonia Centro",
    "Colonia Reforma",
    "Fraccionamiento Las Palmas",
    "Zona Industrial Norte",
    "Barrio San Juan",
    "Colonia Miguel Hidalgo",
    "Unidad Habitacional Oriente",
    "Colonia Lomas del Sur",
    "Barrio Santa Rosa",
    "Colonia Jardines del Valle",
]

STATUSES = [
    AssignmentStatus.PENDING,
    AssignmentStatus.IN_PROGRESS,
    AssignmentStatus.COMPLETED,
    AssignmentStatus.PENDING,
    AssignmentStatus.IN_PROGRESS,
    AssignmentStatus.COMPLETED,
]

# Collect existing (user_id, survey_id) pairs to avoid duplicates
existing_pairs = set(
    db.query(Assignment.user_id, Assignment.survey_id).all()
)

added = 0
for i, user in enumerate(all_brigadistas):
    # Give each brigadista 2 surveys
    user_surveys = [surveys[(i * 2 + k) % len(surveys)] for k in range(2)]
    for j, survey in enumerate(user_surveys):
        if (user.id, survey.id) in existing_pairs:
            continue
        status = STATUSES[(i + j) % len(STATUSES)]
        db.add(Assignment(
            user_id=user.id,
            survey_id=survey.id,
            assigned_by=1,
            status=status,
            location=ZONES[(i * 2 + j) % len(ZONES)],
        ))
        existing_pairs.add((user.id, survey.id))
        added += 1

db.commit()
total = db.query(Assignment).count()
print(f"\n✅  Added {added} new assignments — total in DB: {total}")
db.close()
