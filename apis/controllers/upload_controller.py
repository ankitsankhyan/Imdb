from flask import request, jsonify
from services.upload_service import UploadService


def upload_csv(upload_service: UploadService, update_entry : bool = True):
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if not file.filename.endswith(".csv") or not file.mimetype != "text/csv":
        return jsonify({"error": "Only CSV files are allowed"}), 400

    result = upload_service.process_csv(file.stream, update_entry)
    return jsonify({"message": "Upload complete", "result": result}), 200
