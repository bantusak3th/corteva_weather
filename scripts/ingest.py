import logging
import requests
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import from the new structure
from app.datamodel import Base, WeatherRecord 
from app.config import settings # Use the new config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_and_clean(value):
    """Helper to convert -9999 to None."""
    try:
        val = int(value)
        return val if val != -9999 else None
    except ValueError:
        return None

def ingest_data():
    start_time = datetime.now()
    logger.info(f"--- Ingestion Started at {start_time} ---")

    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    http = requests.Session()
    total_inserted = 0

    try:
        # 1. Get list of files from GitHub API
        resp = http.get(settings.GITHUB_API_URL)
        resp.raise_for_status()
        files = resp.json()

        for file_info in files:
            filename = file_info['name']
            if not filename.endswith(".txt"):
                continue

            station_id = filename.replace(".txt", "")
            download_url = file_info['download_url']
            logger.info(f"Processing station: {station_id}...")
            
            # Optimization: Get existing dates to avoid hitting UNIQUE constraint error
            existing_dates = {
                r[0] for r in session.query(WeatherRecord.date)
                .filter(WeatherRecord.file_station_id == station_id)
                .all()
            }

            new_records = []
            file_response = http.get(download_url)
            file_response.raise_for_status()
            
            for line in file_response.text.splitlines():
                parts = line.strip().split()
                if len(parts) != 4: continue

                date_str, tmax, tmin, precip = parts
                current_date = datetime.strptime(date_str, "%Y%m%d").date()

                if current_date in existing_dates:
                    continue

                record = WeatherRecord(
                    file_station_id=station_id,
                    date=current_date,
                    max_temp_tenths_c=parse_and_clean(tmax),
                    min_temp_tenths_c=parse_and_clean(tmin),
                    precipitation_tenths_mm=parse_and_clean(precip)
                )
                new_records.append(record)

            if new_records:
                session.bulk_save_objects(new_records)
                session.commit()
                total_inserted += len(new_records)
                logger.info(f"  -> Inserted {len(new_records)} records.")
            else:
                logger.info(f"  -> No new records.")
                
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        session.rollback()
    finally:
        session.close()

    end_time = datetime.now()
    logger.info(f"--- Finished at {end_time}. Total Records Ingested: {total_inserted} ---")

if __name__ == "__main__":
    ingest_data()