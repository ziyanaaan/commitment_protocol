from app.core.database import engine, Base
import app.models  # 🔑 this line matters
from app.core.database import Base, engine
from app.models.user import User
from app.models.commitment import Commitment
from app.models.delivery import Delivery
from app.models.settlement import Settlement
from app.models.payment import Payment   # ← THIS MUST EXIST


print("Creating tables...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Done.")
