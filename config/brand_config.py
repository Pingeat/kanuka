import json
import os
from pathlib import Path


def load_brand_config():
    brand_id = os.getenv('BRAND_ID', 'kanuka_organics')
    config_path = Path(__file__).resolve().parent / 'brands' / f'{brand_id}.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


brand_config = load_brand_config()
