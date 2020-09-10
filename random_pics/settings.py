import pathlib
import yaml

BASE_DIR = pathlib.Path(__file__).parent.parent
config_path = BASE_DIR / 'config' / 'random_pics.yaml'
logger_config_path = BASE_DIR / 'config' / 'logger.yaml'

def get_config(path):
    with open(path) as f:
        config = yaml.safe_load(f)
    return config


config = get_config(config_path)
logger_config = get_config(logger_config_path)
