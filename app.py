from flask import Flask, render_template, request, send_file, after_this_request
import instaloader
import zipfile
import os
import shutil
import re
import time
import random
from instaloader.exceptions import TooManyRequestsException, ConnectionException, BadResponseException

app = Flask(__name__)

# CONFIG from your script
BATCH_SIZE = 10  # Reduced for web use to prevent timeouts
IMAGE_DELAY = (10, 15)  # Seconds between images

def get_username(url):
    match = re.search(r'instagram\.com/([^/?]+)', url)
    return match.group(1) if match else None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    profile_url = request.form.get('url')
    # Limit is capped at BATCH_SIZE for no-login safety
    limit = min(int(request.form.get('limit', 10)), BATCH_SIZE)
    username = get_username(profile_url)

    if not username:
        return "Invalid Instagram URL", 400

    # L is configured with your stealth settings
    L = instaloader.Instaloader(
        download_videos=False,
        download_video_thumbnails=False,
        save_metadata=False,
        compress_json=False,
        quiet=True
    )
    # Set a Mobile User-Agent to look like a real phone
    L.context.user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'

    temp_dir = f"temp_{username}_{random.randint(1000, 9999)}"
    zip_name = f"{username}_batch.zip"

    @after_this_request
    def cleanup(response):
        try:
            if os.path.exists(zip_name): os.remove(zip_name)
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Cleanup error: {e}")
        return response

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        downloaded = 0
        for post in profile.get_posts():
            if downloaded >= limit:
                break
            
            # Skip non-images
            if post.typename not in ["GraphImage", "GraphSidecar"]:
                continue

            try:
                L.download_post(post, target=temp_dir)
                downloaded += 1
                # Wait between images to mimic human browsing
                time.sleep(random.uniform(*IMAGE_DELAY))
            except TooManyRequestsException:
                return "Instagram rate-limited this server. Try again in 1 hour.", 429
            except Exception as e:
                print(f"Skipping post: {e}")
                continue

        # Zip the results
        with zipfile.ZipFile(zip_name, 'w') as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(('.jpg', '.jpeg', '.png')):
                        zipf.write(os.path.join(root, file), arcname=file)

        return send_file(zip_name, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
