import csv
import io
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from pymongo import UpdateOne, InsertOne
from pymongo.errors import BulkWriteError
from config import AppConfig
from repository.upload_repository import UploadRepository

logger = logging.getLogger(__name__)


class UploadService:
    def __init__(self, upload_repo: UploadRepository):
        self.upload_repo = upload_repo
        self.batch_size = AppConfig.BATCH_SIZE
        self.max_workers = getattr(AppConfig, "UPLOAD_WORKERS", 4)


    def process_csv(self, file_stream, update_entry: bool = True) -> dict:
        byte_stream = io.BytesIO(file_stream.read())
        text = io.TextIOWrapper(byte_stream, encoding="utf-8", newline="")
        reader = csv.DictReader(text)
        logger.info(f"HEADERS: {reader.fieldnames}")
        total_rows = 0
        total_inserted = 0
        total_skipped = 0
        batch_num = 0
        futures = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            batch = []
            for row in reader:
                record = self._parse_row(row)
                total_rows += 1
                if record is None:
                    total_skipped += 1
                    continue
                batch.append(record)

                if len(batch) >= self.batch_size:
                    batch_num += 1
                    futures.append(executor.submit(self._flush, batch, batch_num, update_entry))
                    batch = []

                    # Backpressure: don't let parser run too far ahead of writers
                    if len(futures) >= self.max_workers * 2:
                        done, pending = self._drain_completed(futures)
                        for inserted, skipped in done:
                            total_inserted += inserted
                            total_skipped += skipped
                        futures = pending

            if batch:
                batch_num += 1
                futures.append(executor.submit(self._flush, batch, batch_num, update_entry))

            # Drain remaining
            for f in futures:
                inserted, skipped = f.result()
                total_inserted += inserted
                total_skipped += skipped
        
        return {"inserted": total_inserted, "skipped": total_skipped, "total_rows": total_rows, "updated": total_rows - total_inserted - total_skipped}

    def _drain_completed(self, futures):
        """Pull off any finished futures without blocking on the rest."""
        done_results = []
        still_pending = []
        for f in futures:
            if f.done():
                done_results.append(f.result())
            else:
                still_pending.append(f)
        # If nothing is done yet, block on the oldest one to make room
        if not done_results and still_pending:
            done_results.append(still_pending.pop(0).result())
        return done_results, still_pending

    def _flush(self, batch: list, batch_num: int, update_entry : bool = True) -> tuple:
        t = time.time()
        try:
            if update_entry:
                operations = [
                    UpdateOne(
                        {
                            "original_title": record["original_title"],
                            "release_date": record["release_date"],
                        },
                        {"$set": record},
                        upsert=True,
                    )
                    for record in batch
                ]   
            else:
                operations = [InsertOne(record) for record in batch]
            result = self.upload_repo.bulk_operation(operations)
            logger.info(f"Batch {batch_num} — {len(batch)} rows — {time.time() - t:.2f}s")
            return result, 0
        except BulkWriteError as e:
            # logger.error(f"Batch {batch_num} bulk upsert error: {e}", exc_info=True)
            inserted = e.details.get("nUpserted", 0) + e.details.get("nModified", 0) + e.details.get("nInserted", 0)
            return inserted, len(batch) - inserted


    def _parse_row(self, row: dict):
        try:
            release_date = row.get("release_date", "").strip()
            return {
                "homepage": row.get("homepage", "").strip() or None,
                "original_language": row.get("original_language", "").strip(),
                "original_title": row.get("original_title", "").strip(),
                "overview": row.get("overview", "").strip(),
                "release_date": release_date,
                # extract year from release_date for filtering
                "release_year": int(release_date[:4]) if release_date else None,
                "revenue": int(float(row["revenue"])) if row.get("revenue") else None,
                "runtime": int(float(row["runtime"])) if row.get("runtime") else None,
                "status": row.get("status", "").strip(),
                "title": row.get("title", "").strip(),
                "vote_average": float(row["vote_average"]) if row.get("vote_average") else None,
                "vote_count": int(float(row["vote_count"])) if row.get("vote_count") else None,
                "production_company_id": int(row["production_company_id"]) if row.get("production_company_id") else None,
                "genre_id": int(row["genre_id"]) if row.get("genre_id") else None,
                "languages": row.get("languages", "").strip(),
            }
        except (ValueError, KeyError):
            logger.error(f"Error parsing row: {row}", exc_info=True)
            return None