# services/brand_service.py
import json
import os
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger("brand_service")

class BrandService:
    def __init__(self):
        self.settings = Settings()
    
    def get_brand_config(self, brand_id: str) -> dict:
        """Load brand configuration from file system"""
        config_path = os.path.join(
            self.settings.BRAND_CONFIG_PATH, 
            f"{brand_id}.json"
        )
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded config for brand: {brand_id}")
            return config
        except FileNotFoundError:
            logger.error(f"Brand config not found: {brand_id}")
            raise ValueError("Invalid brand selection")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in brand config: {brand_id}")
            raise ValueError("Brand configuration error")
    
    def get_available_brands(self) -> list:
        """List all available brands from config directory"""
        brands = []
        for filename in os.listdir(self.settings.BRAND_CONFIG_PATH):
            if filename.endswith(".json"):
                brand_id = filename[:-5]
                try:
                    config = self.get_brand_config(brand_id)
                    brands.append({
                        "id": brand_id,
                        "name": config.get("name", brand_id),
                        "logo": config.get("logo_url")
                    })
                except:
                    continue
        return brands