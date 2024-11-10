from yacs.config import CfgNode as CN

cfg = CN()

# Data configs
cfg.DATA = CN()
cfg.DATA.STORAGE_PATH = ""

# Embedding configs
cfg.EMBEDDING = CN()
cfg.EMBEDDING.MODEL = ""
cfg.EMBEDDING.STORAGE_PATH = ""

# Chunking configs
cfg.CHUNKING = CN()
cfg.CHUNKING.MODEL = ""
cfg.CHUNKING.SIZE = 0
cfg.CHUNKING.OVERLAP = 0

# Chatting configs
cfg.CHAT = CN()
cfg.CHAT.MODEL = ""


def load_config(yaml_file="./config.yml"):
    """
    Load configuration from a YAML file and merge it with the default config.
    """
    config = cfg.clone()

    if yaml_file:
        config.merge_from_file(yaml_file)

    return config

