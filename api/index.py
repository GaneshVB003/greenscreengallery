# --- START OF FILE app.py ---

from flask import Flask, send_from_directory, jsonify, request
import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv
import os
import logging # Import logging

load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='.')

# Configure logging
logging.basicConfig(level=logging.INFO) # Log informational messages and above

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"), # Use env variables
    api_key=os.getenv("CLOUDINARY_API_KEY"),     # Use env variables
    api_secret=os.getenv("CLOUDINARY_API_SECRET") # Use env variables
)

# Verify Cloudinary config (optional but good practice)
if not all([cloudinary.config().cloud_name, cloudinary.config().api_key, cloudinary.config().api_secret]):
    logging.error("Cloudinary configuration is incomplete. Check your .env file.")
else:
    logging.info(f"Cloudinary configured for cloud: {cloudinary.config().cloud_name}")


@app.route("/")
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route("/videos")
def get_videos():
    try:
        # Fetching videos specifically from the 'gs_overlay/' folder
        response = cloudinary.api.resources(
            type="upload",
            resource_type="video",
            prefix="gs_overlay/", # Ensure only videos from this folder are fetched
            max_results=100 # Adjust as needed
        )
        # Log the number of resources found
        logging.info(f"Found {len(response.get('resources', []))} videos in Cloudinary folder 'gs_overlay/'.")
        return jsonify(response.get("resources", []))
    except Exception as e:
        # Use app logger for errors
        app.logger.error(f"ERROR fetching Cloudinary videos: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch videos", "details": str(e)}), 500


# --- CHANGE HERE: Use <path:public_id> ---
@app.route("/delete/<path:public_id>", methods=["DELETE"])
def delete_video(public_id):
    app.logger.info(f"Attempting to delete video with public_id: {public_id}") # Log received public_id
    try:
        # resource_type="video" is crucial for deleting videos
        result = cloudinary.uploader.destroy(public_id, resource_type="video")
        app.logger.info(f"Cloudinary delete result for {public_id}: {result}") # Log Cloudinary response

        # Check the result from Cloudinary
        if result.get("result") == "ok" or result.get("result") == "not found":
             # Consider "not found" as success client-side if the goal is removal
            return jsonify({"status": "success", "message": f"Video {public_id} deleted or already gone."})
        else:
            # If Cloudinary returns an error in the result
            app.logger.error(f"Cloudinary deletion failed for {public_id}: {result}")
            return jsonify({"status": "error", "message": "Cloudinary reported an issue deleting the video."}), 500

    except Exception as e:
        # Log the full exception details
        app.logger.error(f"ERROR deleting video {public_id}: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Server error during deletion.", "details": str(e)}), 500

if __name__ == "__main__":
    # Use 0.0.0.0 to make it accessible on the network if needed, otherwise 127.0.0.1
    # Turn off debug mode in production
    app.run(host='0.0.0.0', port=5000, debug=True) # Use port 5000 or another standard port
