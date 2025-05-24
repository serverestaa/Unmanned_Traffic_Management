import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

async def wait_for_db():
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/postgres")
    engine = create_async_engine(db_url)
    
    while True:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                print("Database is ready!")
                return
        except Exception as e:
            print(f"Waiting for database... ({str(e)})")
            await asyncio.sleep(5)

async def main():
    # Wait for database to be ready
    await wait_for_db()
    
    # Run hex grid population
    print("Populating hex grid...")
    from scripts.populate_hex_grid import populate_hex_grid
    await populate_hex_grid()
    
    # Start the main application
    print("Starting main application...")
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    asyncio.run(main()) 