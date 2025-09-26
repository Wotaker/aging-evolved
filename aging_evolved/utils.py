from typing import Dict, Any

import yaml

def load_config(config_path) -> Dict[str, Any]:
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

