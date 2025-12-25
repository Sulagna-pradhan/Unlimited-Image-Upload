from flask import Flask, render_template, request, send_file, after_this_request
import instaloader
import zipfile
import os
import shutil
import re

app = Flask(__name__)

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
    
    if not username:
        return "Invalid Instagram URL", 400

    L = instaloader.Instaloader(
        download_videos=False, 
        save_metadata=False, 
        download_geotags=False, 
        download_comments=False,
        dirname_pattern='temp_{target}'
    )
    
    temp_dir = f"temp_{username}"
    zip_name = f"{username}_hd_pack.zip"

    @after_this_request
    def cleanup(response):
        try:
            if os.path.exists(zip_name): os.remove(zip_name)
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error cleaning up: {e}")
        return response

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        count = 0
        for post in profile.get_posts():
            if count >= limit: break
            L.download_post(post, target=temp_dir)
            count += 1
            
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(('.jpg', '.jpeg', '.png')):
                        zipf.write(os.path.join(root, file), arcname=file)
        
        return send_file(zip_name, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)