import logging
import time
from sqlalchemy import create_engine, func, extract
from sqlalchemy.orm import sessionmaker
from datamodel import Base, WeatherRecord, WeatherStats
from app.datamodel import Base, WeatherRecord, WeatherStats
from app.config import settings

DB_URL = settings.DATABASE_URL 

logging.basicConfig(level=logging.INFO, format='%(message)s')


def run_analysis():
    start_time = time.time()
    logging.info("--- Analysis Started ---")

    # Connect to Database
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()


    # This ensures if we re-run the analysis, we don't get duplicate key errors.
    session.query(WeatherStats).delete()
    session.commit()
    logging.info("Cleared existing analysis data.")
#  EXTRACT & AGGREGATE (SQL Side)
    year_field = extract('year', WeatherRecord.date).label('year')

    results = session.query(
        WeatherRecord.file_station_id,
        year_field,
        func.avg(WeatherRecord.max_temp_tenths_c),
        func.avg(WeatherRecord.min_temp_tenths_c),
        func.sum(WeatherRecord.precipitation_tenths_mm)
    ).group_by(
        WeatherRecord.file_station_id,
        year_field
    ).all()

    logging.info(f"Calculated stats for {len(results)} station-years.")

    # 4. Process Results & Insert
    stats_batch = []
    for row in results:
        file_station_id, year, avg_max, avg_min, total_precip = row

        # Unit Conversion Logic:
        # - Raw Temp is in tenths of degrees C -> Divide by 10 to get °C
        # - Raw Precip is in tenths of mm -> Divide by 100 to get cm (10mm = 1cm)
        # We also handle None values to prevent errors if data is missing.

        final_max = round(avg_max / 10.0, 2) if avg_max is not None else None
        final_min = round(avg_min / 10.0, 2) if avg_min is not None else None
        final_precip = round(total_precip / 100.0, 2) if total_precip is not None else 0.0
        # Create the ORM object
        stat_record = WeatherStats(
            file_station_id=file_station_id,
            year=int(year),
            avg_max_temp_c=final_max,
            avg_min_temp_c=final_min,
            total_precip_cm=final_precip
        )
        stats_batch.append(stat_record)

    # Bulk insert
    # bulk_save_objects is much faster than adding objects one by one for large datasets.
    session.bulk_save_objects(stats_batch)
    session.commit()

    session.close()

    elapsed = time.time() - start_time
    logging.info(f"--- Analysis Finished in {elapsed:.2f} seconds ---")
    logging.info(f"Total Stats Records Created: {len(stats_batch)}")


if __name__ == "__main__":
    run_analysis()
