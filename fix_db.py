from sqlalchemy import create_engine, text
# Replace the connection string below with your actual database details!
# format: postgresql://username:password@localhost:5432/databasename
engine = create_engine("postgresql://postgres:5849@localhost:5432/hotspotpay")

with engine.connect() as conn:
    conn.execute(text("DROP TYPE IF EXISTS paymentstatus CASCADE;"))
    conn.commit()
print("Successfully destroyed paymentstatus!")
