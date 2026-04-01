import asyncio
import logging
from config import settings
from services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)

async def test():
    print(f"Testing MPNet & CLIP model loading...")
    service = EmbeddingService()
    await service.initialize()
    print("Models initialized successfully!")
    
    # Test text
    text_emb = await service.generate_clip_text_embedding("red shirt")
    print(f"CLIP Text embedding generated. Shape: {text_emb.shape}")
    
    print("Test passed.")

if __name__ == "__main__":
    asyncio.run(test())
