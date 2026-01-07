from app.core.database import engine, Base
from app.models.user import User
from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.models.settlement import Settlement

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
