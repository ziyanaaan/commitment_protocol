from app.core.database import engine, Base
import app.models  # 🔑 this line matters

print("Creating tables...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Done.")
