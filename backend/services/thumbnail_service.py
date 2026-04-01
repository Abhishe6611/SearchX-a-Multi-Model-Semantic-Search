"""
Thumbnail generation service
"""
import os
from PIL import Image
import logging
from pathlib import Path
import fitz  # PyMuPDF for PDF thumbnails
from config import settings
from utils.path_utils import normalize_path_for_url

logger = logging.getLogger(__name__)


class ThumbnailService:
    """Handles thumbnail generation for images and documents"""
    
    def __init__(self):
        self.size = settings.THUMBNAIL_SIZE
        self.quality = settings.THUMBNAIL_QUALITY
        self.thumbnails_dir = settings.THUMBNAILS_DIR
    
    async def generate_thumbnail(self, file_path: str, file_type: str, stored_filename: str) -> str:
        """
        Generate thumbnail for image or document
        Returns path to thumbnail
        """
        try:
            thumbnail_filename = f"thumb_{stored_filename}"
            
            if file_type in settings.ALLOWED_IMAGE_TYPES:
                return await self._generate_image_thumbnail(file_path, thumbnail_filename)
            elif file_type == "application/pdf":
                return await self._generate_pdf_thumbnail(file_path, thumbnail_filename)
            elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]:
                return await self._generate_document_icon(thumbnail_filename, file_type)
            else:
                raise ValueError(f"Unsupported file type for thumbnail: {file_type}")
                
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {str(e)}")
            raise
    
    async def _generate_image_thumbnail(self, image_path: str, thumbnail_filename: str) -> str:
        """Generate thumbnail for image files"""
        try:
            # Change extension to .jpg for thumbnail
            thumbnail_filename = os.path.splitext(thumbnail_filename)[0] + '.jpg'
            thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_filename)
            
            # Open and resize image
            with Image.open(image_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize maintaining aspect ratio
                img.thumbnail(self.size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=self.quality, optimize=True)
            
            logger.info(f"🖼️ Generated image thumbnail: {thumbnail_path}")
            return normalize_path_for_url(thumbnail_path)
            
        except Exception as e:
            logger.error(f"Image thumbnail failed: {str(e)}")
            raise
    
    async def _generate_pdf_thumbnail(self, pdf_path: str, thumbnail_filename: str) -> str:
        """Generate thumbnail from first page of PDF"""
        try:
            thumbnail_filename = os.path.splitext(thumbnail_filename)[0] + '.jpg'
            thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_filename)
            
            # Open PDF and get first page
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                raise ValueError("PDF has no pages")
            
            page = doc[0]
            
            # Render page to image
            mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Resize to thumbnail
            img.thumbnail(self.size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, 'JPEG', quality=self.quality, optimize=True)
            
            doc.close()
            
            logger.info(f"📄 Generated PDF thumbnail: {thumbnail_path}")
            return normalize_path_for_url(thumbnail_path)
            
        except Exception as e:
            logger.error(f"PDF thumbnail failed: {str(e)}")
            raise
    
    async def _generate_document_icon(self, thumbnail_filename: str, file_type: str) -> str:
        """Generate icon placeholder for document files"""
        try:
            thumbnail_filename = os.path.splitext(thumbnail_filename)[0] + '.jpg'
            thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_filename)
            
            # Create simple colored icon
            img = Image.new('RGB', self.size, color=(230, 240, 250))
            
            # You can add text or icon overlay here using PIL ImageDraw
            # For now, just a colored rectangle
            
            img.save(thumbnail_path, 'JPEG', quality=self.quality)
            
            logger.info(f"📄 Generated document icon: {thumbnail_path}")
            return normalize_path_for_url(thumbnail_path)
            
        except Exception as e:
            logger.error(f"Document icon generation failed: {str(e)}")
            raise
