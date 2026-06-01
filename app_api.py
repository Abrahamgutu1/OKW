from flask import Flask, request, jsonify
import oracledb
import base64
import os

app = Flask(__name__)

# Database Configuration (match your Streamlit dashboard credentials)
DB_USER = "system"
DB_PASSWORD = "your_password"
DB_DSN = "localhost:1521/FREEPDB1"

@app.route('/api/upload_inspection', methods=['POST'])
def upload_inspection():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Missing JSON payload"}), 400

        # Extract values sent by the iOS app
        service_line_id = data.get("service_line_id")
        evidence_id = data.get("evidence_id")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        accuracy = data.get("accuracy")
        image_base64 = data.get("image_base64") # The captured photo

        if not service_line_id or not evidence_id or not image_base64:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # Connect and insert into Oracle 23ai
        conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        cursor = conn.cursor()
        
        # Adjust SQL columns to match your exact schema layout
        cursor.execute("""
            INSERT INTO EVIDENCE (
                EVIDENCE_ID, SERVICE_LINE_ID, GPS_LATITUDE, GPS_LONGITUDE, 
                GPS_ACCURACY, BASE64_IMAGE, USER_VERIFIED_STATUS
            ) VALUES (:1, :2, :3, :4, :5, :6, 'UNVERIFIED')
        """, (int(evidence_id), int(service_line_id), float(latitude), float(longitude), float(accuracy), image_base64))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": f"Evidence EV-{evidence_id} successfully synced to database."}), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Run on port 5001 so it doesn't conflict with Oracle or Streamlit ports
    app.run(host='0.0.0.0', port=5001, debug=True)