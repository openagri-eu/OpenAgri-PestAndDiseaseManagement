import logging

from core import settings

# Set to level specified in .env
logging.basicConfig(level=settings.LOGGING)

def get_logger(api_path_name: str):
    if settings.LOGGING:
        return logging.getLogger(api_path_name)

    return None