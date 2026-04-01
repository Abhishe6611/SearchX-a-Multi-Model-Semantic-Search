"""
Path utility functions for normalizing file paths to URL-friendly format
"""
import os
from pathlib import Path
from config import settings


def normalize_path_for_url(file_path: str) -> str:
    """
    Convert Windows file path to URL-friendly format
    
    Example:
        Input:  "storage/files\\abc.jpg" or "C:\\...\\storage\\files\\abc.jpg"
        Output: "/storage/files/abc.jpg"
    
    Args:
        file_path: Full or relative file path (Windows or Unix style)
    
    Returns:
        URL-friendly path starting with /storage/
    """
    # Convert to Path object for cross-platform handling
    path = Path(file_path)
    
    # Get absolute path for comparison
    abs_path = path.absolute()
    base_dir = settings.BASE_DIR.absolute()
    
    # Try to make relative to base directory
    try:
        rel_path = abs_path.relative_to(base_dir)
    except ValueError:
        # Path is not relative to base_dir, try to extract storage part
        if 'storage' in str(path):
            parts = Path(file_path).parts
            storage_idx = parts.index('storage') if 'storage' in parts else -1
            if storage_idx >= 0:
                rel_path = Path(*parts[storage_idx:])
            else:
                rel_path = path
        else:
            rel_path = path
    
    # Convert to forward slashes and add leading slash
    url_path = '/' + str(rel_path).replace('\\', '/')
    
    # Ensure it starts with /storage/
    if not url_path.startswith('/storage/'):
        # Try to fix it
        if 'storage' in url_path:
            idx = url_path.index('storage')
            url_path = '/' + url_path[idx:]
        else:
            # Last resort: assume it's a filename and prepend /storage/files/
            url_path = '/storage/files/' + os.path.basename(file_path)
    
    return url_path


def get_physical_path(url_path: str) -> str:
    """
    Convert URL path back to physical file system path
    
    Example:
        Input:  "/storage/files/abc.jpg"
        Output: "C:\\...\\backend\\storage\\files\\abc.jpg"
    
    Args:
        url_path: URL path starting with /storage/
    
    Returns:
        Absolute file system path
    """
    # Remove leading slash
    rel_path = url_path.lstrip('/')
    
    # Convert to OS-specific path
    physical_path = settings.BASE_DIR / rel_path
    
    return str(physical_path)
