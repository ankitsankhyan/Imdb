import logging
from flask import Blueprint, request, jsonify
from container.serviceContainer import upload_service

logger = logging.getLogger(__name__)
upload_routes = Blueprint("upload", __name__, url_prefix="/api/upload")


@upload_routes.route("/", methods=["POST"])
def upload_csv():
    """
    Upload a CSV file to import movies
    ---
    tags:
      - Upload
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: CSV file containing movie data
      - name: mode
        in: query
        type: string
        required: false
        default: insert
        enum: [upsert, insert]
        description: |
          Upload strategy:
          - **upsert** — matches each row on (original_title, release_date). Updates the document if it exists, inserts if it doesn't. Use this to add new movies or correct existing records. Slower on large files since every write requires a read against the unique index.
          - **insert** (default) — bulk inserts rows directly using InsertOne. Rows that already exist (duplicate key on original_title + release_date) are silently skipped. No read-before-write, so significantly faster for large files (1 GB+). Use this when the CSV has no duplicates or you only want to add new records without touching existing ones.
    responses:
      200:
        description: Upload complete
        schema:
          type: object
          properties:
            message:
              type: string
              example: Upload complete
            result:
              type: object
              properties:
                inserted:
                  type: integer
                  description: Number of new documents inserted
                updated:
                  type: integer
                  description: Number of existing documents updated (upsert mode only)
                skipped:
                  type: integer
                  description: Number of rows that failed to parse
                total_rows:
                  type: integer
                  description: Total rows read from CSV
      400:
        description: Bad request
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid mode. Allowed: upsert, insert"
      500:
        description: Internal server error
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        if not file.filename.endswith(".csv"):
            return jsonify({"error": "Only CSV files are allowed"}), 400

        mode = request.args.get("mode", "upsert")
        if mode not in ("upsert", "insert"):
            return jsonify({"error": "Invalid mode. Allowed: upsert, insert"}), 400

        result = upload_service.process_csv(file.stream, update_entry=(mode == "upsert"))
        return jsonify({"message": "Upload complete", "result": result}), 200
    except Exception as e:
        logger.error(f"Error uploading CSV: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
