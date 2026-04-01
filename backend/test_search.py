import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.hybrid_search_service import HybridSearchService
from database import SessionLocal

async def main():
    service = HybridSearchService()
    try:
        await service.initialize()
        results = await service.hybrid_search("BAI237972")
        print("Search successful, found results:", len(results))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
