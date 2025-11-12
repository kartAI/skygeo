from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings"""
    data_directory: Path = Path("./data")
    catalog_title: str = "STAC Catalog"
    catalog_description: str = "Dynamic STAC catalog for geospatial data"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directory exists
        if not self.data_directory.exists():
            self.data_directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
