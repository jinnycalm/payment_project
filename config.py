import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings      # 자동 형변환 및 타입 안정성 자동 검증

load_dotenv()

class Settings(BaseSettings):
    # OPEN AI KEY
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')

    # KAKAO API
    KAKAO_REST_KEY: str = os.getenv('VITE_KAKAO_REST_KEY')

    # Tavily
    TAVILY_API_KEY: str = os.getenv('TAVILY_API_KEY')

    # DB
    SSH_HOST: str = os.getenv('SSH_HOST')
    SSH_PORT: int = int(os.getenv('SSH_PORT'))
    SSH_USER: str = os.getenv('SSH_USER')
    SSH_KEY_PATH: str = os.getenv('SSH_KEY_PATH')

    RDS_HOST: str = os.getenv('RDS_HOST')
    RDS_PORT: int = int(os.getenv('RDS_PORT'))
    RDS_USER: str = os.getenv('RDS_USER')
    RDS_PASSWORD: str = os.getenv('RDS_PASSWORD')
    RDS_DB_NAME: str = os.getenv('RDS_DB_NAME')

settings = Settings()