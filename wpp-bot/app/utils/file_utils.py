# app/utils/file_utils.py
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_json_file_path(filename: str) -> Path:
    """Get the absolute path to a JSON file in the utils directory."""
    # Get the base directory from the current file
    base_dir = Path(__file__).resolve().parent.parent.parent
    file_path = base_dir / "app" / "utils" / filename
    
    logger.info(f"JSON file path resolved to: {file_path}")
    return file_path

def load_json_file(filename: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file from the utils directory."""
    file_path = get_json_file_path(filename)
    
    if not file_path.exists():
        logger.error(f"JSON file not found: {file_path}")
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded JSON file: {filename}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON file {filename}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def save_json_file(filename: str, data: Dict[str, Any]) -> bool:
    """Save data to a JSON file in the utils directory."""
    file_path = get_json_file_path(filename)
    
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved JSON file: {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file {filename}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False