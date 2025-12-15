import logging
from typing import List, Optional
from datetime import date
from fastapi import FastAPI, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, ConfigDict
from app.datamodel import Base, WeatherRecord, WeatherStats
from app.config import settings

DB_URL = settings.DATABASE_URL

# db setup
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class WeatherRecordResponse(BaseModel):
    file_station_id: str
    date: date
    max_temp_tenths_c: Optional[int]
    min_temp_tenths_c: Optional[int]
    precipitation_tenths_mm: Optional[int]

    model_config = ConfigDict(from_attributes=True)

class WeatherStatsResponse(BaseModel):
    file_station_id: str
    year: int
    avg_max_temp_c: Optional[float]
    avg_min_temp_c: Optional[float]
    total_precip_cm: Optional[float]

    model_config = ConfigDict(from_attributes=True)

#  API Application
app = FastAPI(
    title="Weather Data API",
    description="API for ingesting and analyzing historical weather data.",
    version="1.0.0"
)

# Endpoint /api/weather
@app.get("/api/weather", response_model=List[WeatherRecordResponse])
def get_weather_data(
    file_station_id: Optional[str] = None,
    date_str: Optional[date] = Query(None, alias="date"),
    page: int = 1,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(WeatherRecord)

    if file_station_id:
        query = query.filter(WeatherRecord.file_station_id == file_station_id)
    if date_str:
        query = query.filter(WeatherRecord.date == date_str)

    offset = (page - 1) * limit
    records = query.offset(offset).limit(limit).all()

    return records

# Endpoint : /api/weather/stats
@app.get("/api/weather/stats", response_model=List[WeatherStatsResponse])
def get_weather_stats(
    file_station_id: Optional[str] = None,
    year: Optional[int] = None,
    page: int = 1,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(WeatherStats)

    if file_station_id:
        query = query.filter(WeatherStats.file_station_id == file_station_id)
    if year:
        query = query.filter(WeatherStats.year == year)

    offset = (page - 1) * limit
    stats = query.offset(offset).limit(limit).all()

    return stats