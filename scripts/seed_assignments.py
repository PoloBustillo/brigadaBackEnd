"""Seed demo assignments linking brigadistas to surveys."""
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone

logging.disable(logging.CRITICAL)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models.assignment import Assignment, AssignmentStatus
from app.models.user import User, UserRole
from app.models.survey import Survey

db = SessionLocal()

# ── Fetch brigadistas and active surveys ──────────────────────────────────
brigadistas = (
    db.query(User)
    .filter(User.role == UserRole.BRIGADISTA, User.is_active == True)
    .all()
)
surveys = db.query(Survey).filter(Survey.is_active == True).all()

print(f"Brigadistas found : {len(brigadistas)} → {[(u.id, u.full_name) for u in brigadistas]}")
print(f"Active surveys    : {len(surveys)} → {[(s.id, s.title[:40]) for s in surveys]}")

if not brigadistas:
    print("❌  No brigadistas found — run seed_data.py first")
    db.close()
    sys.exit(1)

if not surveys:
    print("❌  No active surveys found")
    db.close()
    sys.exit(1)

now = datetime.now(tz=timezone.utc)

# ── Build assignment combos ───────────────────────────────────────────────
# Skip if assignments already exist
existing = db.query(Assignment).count()
if existing:
    print(f"ℹ️   {existing} assignments already exist — skipping seed")
    db.close()
    sys.exit(0)

# Distribute surveys across brigadistas:
# Each brigadista gets 2-4 surveys with different statuses
STATUSES = [
    AssignmentStatus.PENDING,
    AssignmentStatus.IN_PROGRESS,
    AssignmentStatus.COMPLETED,
    AssignmentStatus.PENDING,
    AssignmentStatus.IN_PROGRESS,
]

ZONES = [
    "Colonia Centro",
    "Colonia Reforma",
    "Fraccionamiento Las Palmas",
    "Zona Industrial Norte",
    "Barrio San Juan",
    "Colonia Miguel Hidalgo",
    "Unidad Habitacional Oriente",
    "Colonia Lomas del Sur",
]

assignments_created = 0
survey_cycle = list(surveys)  # cycle through surveys

for i, brigade_user in enumerate(brigadistas):
    # Give each brigadista 3 surveys (or all if fewer surveys available)
    n = min(3, len(survey_cycle))
    user_surveys = survey_cycle[i % len(survey_cycle) : i % len(survey_cycle) + n]
    # Wrap around if needed
    if len(user_surveys) < n:
        user_surveys += survey_cycle[: n - len(user_surveys)]

    for j, survey in enumerate(user_surveys):
        status = STATUSES[(i + j) % len(STATUSES)]
        due_days = 7 + (i * 3) + j
        due_date = now + timedelta(days=due_days) if status != AssignmentStatus.COMPLETED else None
        completed_at = (now - timedelta(days=j + 1)) if status == AssignmentStatus.COMPLETED else None

        db.add(Assignment(
            user_id=brigade_user.id,
            survey_id=survey.id,
            assigned_by=1,  # admin user
            status=status,
            location=ZONES[(i * 3 + j) % len(ZONES)],
        ))
        assignments_created += 1

db.commit()
print(f"\n✅  Seeded {assignments_created} assignments")
db.close()
