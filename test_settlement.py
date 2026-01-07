from app.core.database import SessionLocal
from app.services.settlement import settle_commitment
from app.models.settlement import Settlement

db = SessionLocal()

# Always fetch existing settlement if it exists
existing = db.query(Settlement).filter(Settlement.commitment_id == 1).first()
if existing:
    print("Settlement already exists:", existing.id)
else:
    settlement = settle_commitment(db, commitment_id=1)
    print("Settlement created:", settlement.id)

db.close()
