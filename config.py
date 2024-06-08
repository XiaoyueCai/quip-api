import yaml


def load_config(config_path: str) -> dict:
    # 读取 YAML 文件
    with open(config_path, 'r') as file:
        _config = yaml.safe_load(file)

    return _config


config = load_config('config.yaml')
logging_config = load_config('logging_config.yaml')
