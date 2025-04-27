import os
import logging
from flask import Flask, render_template, jsonify, send_from_directory, request
import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv

# Load environment variables\load_dotenv()

# Determine the directory containing this file
api_dir = os.path.dirname(__file__)

# Initialize Flask, pointing to api/templates for HTML and api/static for assets
app = Flask(
    __name__,
    static_url_path='/static',
    static_folder=os.path.join(api_dir, 'static'),
    template_folder=os.path.join(api_dir, 'templates')
)

# Configure logging\logging.basicConfig(level=logging.INFO)

# Configure Cloudinary from environment
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
if not all([cloudinary.config().cloud_name, cloudinary.config().api_key, cloudinary.config().api_secret]):
    logging.error("Cloudinary configuration is incomplete. Check your .env file.")
else:
    logging.info(f"Cloudinary configured for cloud: {cloudinary.config().cloud_name}")

# Routes

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
        return jsonify(resp.get('resources', []))
    except Exception as e:
        logging.error("ERROR fetching videos", exc_info=True)
        return jsonify(error="Failed to fetch videos", details=str(e)), 500

@app.route("/delete/<path:public_id>", methods=["DELETE"])
def delete_video(public_id):
    logging.info(f"Deleting video: {public_id}")
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="video")
        logging.info(f"Delete result: {result}")
        if result.get("result") in ("ok", "not found"):
            return jsonify(status="success", message=f"{public_id} deleted or not found")
        return jsonify(status="error", message="Cloudinary deletion issue"), 500
    except Exception as e:
        logging.error("ERROR deleting video", exc_info=True)
        return jsonify(status="error", message="Server error", details=str(e)), 500

@app.route("/sitemap.xml")
def sitemap():
    # Serve sitemap from api/sitemap.xml
    return send_from_directory(
        directory=api_dir,
        filename="sitemap.xml",
        mimetype="application/xml"
    )

@app.route("/robots.txt")
def robots():
    # Serve robots.txt from api/robots.txt
    return send_from_directory(
        directory=api_dir,
        filename="robots.txt",
        mimetype="text/plain"
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
