import os
import logging
from flask import Flask, render_template, jsonify, send_from_directory
import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv

# —— Load env & configure Flask ——
load_dotenv()
app = Flask(
    __name__,
    static_url_path='/static',
    static_folder='static',
    template_folder='templates'
)

logging.basicConfig(level=logging.INFO)

# —— Cloudinary configuration ——
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

if not all([cloudinary.config().cloud_name,
            cloudinary.config().api_key,
            cloudinary.config().api_secret]):
    logging.error("Cloudinary configuration is incomplete. Check your .env file.")
else:
    logging.info(f"Cloudinary configured for cloud: {cloudinary.config().cloud_name}")

# —— Routes ——

@app.route("/")
def serve_index():
    return render_template('index.html')

@app.route("/videos")
def get_videos():
    try:
        resp = cloudinary.api.resources(
            type="upload",
            resource_type="video",
            prefix="gs_overlay/",
            max_results=100
        )
        logging.info(f"Found {len(resp.get('resources', []))} videos.")
        return jsonify(resp.get("resources", []))
    except Exception as e:
        app.logger.error("ERROR fetching videos", exc_info=True)
        return jsonify(error="Failed to fetch videos", details=str(e)), 500

@app.route("/delete/<path:public_id>", methods=["DELETE"])
def delete_video(public_id):
    app.logger.info(f"Deleting video: {public_id}")
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="video")
        app.logger.info(f"Delete result: {result}")
        status = result.get("result")
        if status in ("ok", "not found"):
            return jsonify(status="success", message=f"{public_id} deleted or not found")
        else:
            return jsonify(status="error", message="Cloudinary deletion issue"), 500
    except Exception as e:
        app.logger.error("ERROR deleting video", exc_info=True)
        return jsonify(status="error", message="Server error", details=str(e)), 500

@app.route("/sitemap.xml")
def sitemap():
    api_dir = os.path.dirname(__file__)
    return send_from_directory(
        directory=api_dir,
        filename="sitemap.xml",
        mimetype="application/xml"
    )

@app.route("/robots.txt")
def robots():
    api_dir = os.path.dirname(__file__)
    return send_from_directory(
        directory=api_dir,
        filename="robots.txt",
        mimetype="text/plain"
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
