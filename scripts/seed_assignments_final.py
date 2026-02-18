"""Seed assignments for all active non-admin users across surveys."""
import sys
import logging
from pathlib import Path

logging.disable(logging.CRITICAL)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models.assignment import Assignment, AssignmentStatus
from app.models.user import User, UserRole
from app.models.survey import Survey

db = SessionLocal()

users = (
    db.query(User)
    .filter(User.is_active == True, User.role != UserRole.ADMIN)
    .all()
)
surveys = db.query(Survey).filter(Survey.is_active == True).all()

print(f"Users   : {[(u.id, u.role.value, u.full_name) for u in users]}")
print(f"Surveys : {[s.id for s in surveys]}")

# Wipe old assignments
deleted = db.query(Assignment).delete()
db.commit()
print(f"Deleted {deleted} old assignments")

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
NOTES = [
    "Llevar credencial de identificación. Aplicar en casas verdes del sector.",
    "Registrar solo familias con 3 o más integrantes.",
    "Priorizar adultos mayores.",
    None,
    "Visitar en horario matutino.",
    None,
]
STATUSES = [
    AssignmentStatus.PENDING,
    AssignmentStatus.IN_PROGRESS,
    AssignmentStatus.COMPLETED,
    AssignmentStatus.PENDING,
    AssignmentStatus.IN_PROGRESS,
    AssignmentStatus.COMPLETED,
]

added = 0
for i, user in enumerate(users):
    n_surveys = min(2, len(surveys))
    for j in range(n_surveys):
        s = surveys[(i * 2 + j) % len(surveys)]
        db.add(Assignment(
            user_id=user.id,
            survey_id=s.id,
            assigned_by=1,
            status=STATUSES[(i + j) % len(STATUSES)],
            location=ZONES[(i * 2 + j) % len(ZONES)],
            notes=NOTES[(i + j) % len(NOTES)],
        ))
        added += 1

db.commit()
total = db.query(Assignment).count()
print(f"\nSeeded {added} assignments — total in DB: {total}")
db.close()
