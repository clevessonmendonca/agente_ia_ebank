# app/api/endpoints/flow_manager_simple.py
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import json
import logging
from typing import Dict, Any
import shutil
from datetime import datetime
from pathlib import Path

from app.utils.file_utils import load_json_file, save_json_file, get_json_file_path

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/flow", tags=["flow"])

# JSON filename
FLOW_FILENAME = "projeto_asas_menu_templates.json"

@router.get("")
async def get_flow():
    """Get the current menu flow"""
    logger.info("Retrieving current menu flow")
    
    # Try to load the file
    data = load_json_file(FLOW_FILENAME)
    
    if data is None:
        # If file doesn't exist, create an empty template
        logger.warning(f"Flow file not found, creating empty template")
        empty_template = {
            "menus": {
                "inicial": {
                    "title": "Menu Inicial",
                    "content": "Bem-vindo ao menu inicial",
                    "options": {
                        "menu_type": "text"
                    },
                    "extra_actions": []
                },
                "privacidade": {
                    "title": "Política de Privacidade",
                    "content": "Esta é a nossa política de privacidade",
                    "options": {
                        "menu_type": "text"
                    },
                    "extra_actions": []
                }
            }
        }
        
        # Save the empty template
        if save_json_file(FLOW_FILENAME, empty_template):
            return empty_template
        else:
            raise HTTPException(status_code=500, detail="Failed to create flow template")
    
    return data

@router.post("")
async def save_flow(data: Dict[str, Any]):
    """Save the menu flow"""
    logger.info("Saving menu flow")
    
    # Validate data structure
    if "menus" not in data:
        logger.error("Invalid flow data: missing 'menus' key")
        raise HTTPException(status_code=400, detail="Invalid flow data: missing 'menus' key")
    
    # Validate required menus
    if "inicial" not in data["menus"]:
        logger.error("Invalid flow data: missing 'inicial' menu")
        raise HTTPException(status_code=400, detail="Invalid flow data: missing 'inicial' menu")
    
    if "privacidade" not in data["menus"]:
        logger.error("Invalid flow data: missing 'privacidade' menu")
        raise HTTPException(status_code=400, detail="Invalid flow data: missing 'privacidade' menu")
    
    # Create backup
    file_path = get_json_file_path(FLOW_FILENAME)
    if file_path.exists():
        backup_file = file_path.with_suffix(f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        try:
            shutil.copy2(file_path, backup_file)
            logger.info(f"Created backup at {backup_file}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {str(e)}")
    
    # Save file
    if save_json_file(FLOW_FILENAME, data):
        logger.info("Flow saved successfully")
        return {"status": "success", "message": "Flow saved successfully"}
    else:
        logger.error("Failed to save flow")
        raise HTTPException(status_code=500, detail="Failed to save flow")

@router.post("/validate")
async def validate_flow(data: Dict[str, Any]):
    """Validate the menu flow without saving"""
    logger.info("Validating menu flow")
    
    errors = []
    
    # Check basic structure
    if "menus" not in data:
        errors.append("Invalid flow data: missing 'menus' key")
    
    # Check required menus
    if "menus" in data:
        if "inicial" not in data["menus"]:
            errors.append("Invalid flow data: missing 'inicial' menu")
        
        if "privacidade" not in data["menus"]:
            errors.append("Invalid flow data: missing 'privacidade' menu")
        
        # Check for invalid references
        for menu_id, menu_data in data["menus"].items():
            if "options" in menu_data:
                options = menu_data["options"]
                
                # Check buttons
                if "menu_type" in options and options["menu_type"] == "button" and "buttons" in options:
                    for button in options["buttons"]:
                        if "next_menu" in button and button["next_menu"] and button["next_menu"] not in data["menus"]:
                            errors.append(f"Menu '{menu_id}' button '{button.get('title', 'unnamed')}' references non-existent menu '{button['next_menu']}'")
    
    if errors:
        logger.warning(f"Validation failed with {len(errors)} errors")
        return {"valid": False, "errors": errors}
    
    logger.info("Validation successful")
    return {"valid": True}

@router.post("/import")
async def import_flow(file: UploadFile = File(...)):
    """Import a flow from a JSON file"""
    logger.info(f"Importing flow from file {file.filename}")
    
    # Read file content
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("Invalid JSON file")
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    
    # Validate data
    if "menus" not in data:
        logger.error("Invalid flow data: missing 'menus' key")
        raise HTTPException(status_code=400, detail="Invalid flow data: missing 'menus' key")
    
    # Create backup
    file_path = get_json_file_path(FLOW_FILENAME)
    if file_path.exists():
        backup_file = file_path.with_suffix(f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        try:
            shutil.copy2(file_path, backup_file)
            logger.info(f"Created backup at {backup_file}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {str(e)}")
    
    # Save file
    if save_json_file(FLOW_FILENAME, data):
        logger.info("Flow imported successfully")
        return {"status": "success", "message": "Flow imported successfully"}
    else:
        logger.error("Failed to import flow")
        raise HTTPException(status_code=500, detail="Failed to import flow")

@router.get("/export")
async def export_flow():
    """Export the current flow"""
    logger.info("Exporting current flow")
    
    data = load_json_file(FLOW_FILENAME)
    
    if data is None:
        logger.error("Flow file not found")
        raise HTTPException(status_code=404, detail="Flow file not found")
    
    return 

@router.get("/test")
async def test_connection():
    """Test endpoint to verify connectivity"""
    return {"status": "ok", "message": "Flow manager API is working"}