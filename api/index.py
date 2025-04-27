from flask import Flask, render_template, jsonify, request
import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv
import os
import logging

load_dotenv()

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')

logging.basicConfig(level=logging.INFO)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

if not all([cloudinary.config().cloud_name, cloudinary.config().api_key, cloudinary.config().api_secret]):
    logging.error("Cloudinary configuration is incomplete. Check your .env file.")
else:
    logging.info(f"Cloudinary configured for cloud: {cloudinary.config().cloud_name}")

@app.route("/")
def serve_index():
    return render_template('index.html')

@app.route("/videos")
def get_videos():
    try:
        response = cloudinary.api.resources(
            type="upload",
            resource_type="video",
            prefix="gs_overlay/",
            max_results=100
        )
        logging.info(f"Found {len(response.get('resources', []))} videos in Cloudinary folder 'gs_overlay/'.")
        return jsonify(response.get("resources", []))
    except Exception as e:
        app.logger.error(f"ERROR fetching Cloudinary videos: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch videos", "details": str(e)}), 500

@app.route("/delete/<path:public_id>", methods=["DELETE"])
def delete_video(public_id):
    app.logger.info(f"Attempting to delete video with public_id: {public_id}")
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="video")
        app.logger.info(f"Cloudinary delete result for {public_id}: {result}")
        if result.get("result") == "ok" or result.get("result") == "not found":
            return jsonify({"status": "success", "message": f"Video {public_id} deleted or already gone."})
        else:
            app.logger.error(f"Cloudinary deletion failed for {public_id}: {result}")
            return jsonify({"status": "error", "message": "Cloudinary reported an issue deleting the video."}), 500
    except Exception as e:
        app.logger.error(f"ERROR deleting video {public_id}: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Server error during deletion.", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
