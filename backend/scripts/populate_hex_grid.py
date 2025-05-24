import os
import sys
import asyncio

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.monitoring.scripts.populate_hex_grid import populate_hex_grid

if __name__ == "__main__":
    asyncio.run(populate_hex_grid()) 