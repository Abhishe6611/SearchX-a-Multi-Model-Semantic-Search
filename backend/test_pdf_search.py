"""
Test search on newly OCR'd PDF
"""
import asyncio
from services.search_service import SearchService

async def test_pdf_search():
    print("\n" + "="*60)
    print("TESTING SEARCH ON OCR'd PDF")
    print("="*60)
    
    search_service = SearchService()
    await search_service.initialize()
    
    test_queries = [
        "CBSE",
        "ABHISHEK",
        "examination certificate",
        "2021",
        "SWAMI VIVEKANANDA",
        "CENTRAL BOARD",
        "secondary school"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)
        
        try:
            results = await search_service.search(query, limit=5)
            
            if results:
                print(f"   Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. {result['original_filename']}")
                    print(f"      Score: {result['relevance_score']:.4f}")
                    print(f"      Type: {result['file_type']}")
            else:
                print(f"   No results found")
                
        except Exception as e:
            print(f"   ERROR: {str(e)}")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(test_pdf_search())
