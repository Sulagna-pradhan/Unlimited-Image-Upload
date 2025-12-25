from flask import Flask, render_template, request, send_file, after_this_request
import instaloader
import zipfile
import os
import shutil
import re

app = Flask(__name__)

# Helper to extract username
def get_username(url):
    match = re.search(r'instagram\.com/([^/?]+)', url)
    return match.group(1) if match else None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    profile_url = request.form.get('url')
    limit = int(request.form.get('limit', 10))
    username = get_username(profile_url)
    
    # Securely get credentials from Koyeb Environment Variables
    IG_USERNAME = os.environ.get('IG_USERNAME')
    IG_PASSWORD = os.environ.get('IG_PASSWORD')

    if not username:
        return "Invalid Instagram URL", 400

    # Initialize Instaloader with "Next Level" settings
    L = instaloader.Instaloader(
        download_videos=False, 
        save_metadata=False, 
        download_geotags=False, 
        download_comments=False,
        post_metadata_txt_pattern=''
    )
    
    temp_dir = f"temp_{username}"
    zip_name = f"{username}_hd_pack.zip"

    # Ensure cleanup happens after the user downloads the file
    @after_this_request
    def cleanup(response):
        try:
            if os.path.exists(zip_name): os.remove(zip_name)
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        except Exception as e:
            app.logger.error(f"Cleanup error: {e}")
        return response

    try:
        # Step 1: Login to bypass the 401 Unauthorized error
        if IG_USERNAME and IG_PASSWORD:
            print(f"Logging in as {IG_USERNAME}...")
            L.login(IG_USERNAME, IG_PASSWORD)
        else:
            print("No credentials found, attempting guest download...")

        # Step 2: Fetch Profile
        profile = instaloader.Profile.from_username(L.context, username)
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # Step 3: Download High-Res Posts
        count = 0
        for post in profile.get_posts():
            if count >= limit:
                break
            L.download_post(post, target=temp_dir)
            count += 1
            
        # Step 4: Create the ZIP file
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(('.jpg', '.jpeg', '.png')):
                        zipf.write(os.path.join(root, file), arcname=file)
        
        return send_file(zip_name, as_attachment=True)

    except Exception as e:
        return f"Instagram blocked the request: {str(e)}. Tip: Ensure your IG_USERNAME and IG_PASSWORD are correct in Koyeb settings.", 500

if __name__ == '__main__':
    # Use the port Koyeb provides
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
