import os

class Settings:
    # Use environment variables for secrets/paths, providing simple defaults
    # This makes the code runnable anywhere without modification.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./weather_data.db")
    GITHUB_API_URL: str = "https://api.github.com/repos/corteva/code-challenge-template/contents/wx_data"

settings = Settings()