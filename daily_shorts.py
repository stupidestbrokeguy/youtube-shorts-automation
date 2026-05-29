"""
Daily Picture to YouTube Shorts - Creative Daily Style Animation
Features:
- 60% zoom for better readability
- Yellow background
- Smooth sliding animation from bottom to top
- Static thumbnail (full image, no yellow background)
- Audio support with looping
- Auto-commits state to GitHub using SET secret
"""

import os
import sys
import json
import pickle
import socket
import time
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ========== CONFIGURATION ==========
VIDEO_TITLE = "Stupid Broke Money, What Happened? - Stupid Orange, Stupidest Broke Guy, Creative Daily"
HASHTAGS = "#stupidorange #creativedaily #stupidestbrokeguy #Dubai #UAE #fyp"
VIDEO_DURATION = 18
IMAGES_FOLDER = "daily_images"
STATE_FILE = "shorts_state.json"
# ===================================

def load_state():
    """Load the state file to know which image to use next"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        print(f"📂 Loaded state: last used {state.get('last_image', 'none')}")
        return state
    return {'last_index': 0, 'last_date': None, 'last_image': None}

def save_state(state):
    """Save current state locally"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"💾 State saved locally")

def commit_and_push_state():
    """Commit and push shorts_state.json back to GitHub using SET secret"""
    print(f"\n📤 Committing state changes to GitHub...")
    
    try:
        # Check if we're in a git repository
        if not os.path.exists('.git'):
            print(f"   ⚠️ Not a git repository, skipping commit")
            return False
        
        # Configure git user
        if os.environ.get('GITHUB_ACTIONS'):
            # Running in GitHub Actions
            subprocess.run(['git', 'config', '--global', 'user.name', 'github-actions[bot]'], capture_output=True)
            subprocess.run(['git', 'config', '--global', 'user.email', 'github-actions[bot]@users.noreply.github.com'], capture_output=True)
            
            # Use SET secret for authentication
            github_token = os.environ.get('GIT_TOKEN') or os.environ.get('SET')
            if github_token:
                repo_url = f"https://{github_token}@github.com/{os.environ.get('GITHUB_REPOSITORY')}.git"
                subprocess.run(['git', 'remote', 'set-url', 'origin', repo_url], capture_output=True)
                print(f"   🔑 Using SET token for authentication")
        else:
            # Running locally
            subprocess.run(['git', 'config', 'user.name', 'Daily-Shorts-Bot'], capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'bot@localhost'], capture_output=True)
        
        # Pull latest changes first (to avoid conflicts)
        pull_result = subprocess.run(['git', 'pull', '--rebase'], capture_output=True, text=True)
        if pull_result.returncode == 0:
            print(f"   📥 Pulled latest changes")
        
        # Add the state file
        subprocess.run(['git', 'add', STATE_FILE], check=True, capture_output=True)
        
        # Check if there are changes to commit
        status_result = subprocess.run(['git', 'status', '--porcelain', STATE_FILE], capture_output=True, text=True)
        
        if status_result.stdout.strip():
            # Commit the change
            commit_msg = f"Update shorts_state.json - posted image for {datetime.now().strftime('%Y-%m-%d')}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True, capture_output=True)
            print(f"   ✅ Committed state")
            
            # Push to remote
            push_result = subprocess.run(['git', 'push'], capture_output=True, text=True)
            if push_result.returncode == 0:
                print(f"   ✅ State pushed to GitHub")
            else:
                print(f"   ⚠️ Push failed: {push_result.stderr}")
        else:
            print(f"   ℹ️ No changes to commit")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️ Git command failed: {e}")
        return False
    except Exception as e:
        print(f"   ⚠️ Could not commit state: {e}")
        return False

def get_next_image():
    """Determine which image to use today"""
    state = load_state()
    
    today = datetime.now().strftime("%Y-%m-%d")
    if state.get('last_date') == today:
        print(f"⚠️ Already posted today ({today})")
        return None, None, state

    if not os.path.exists(IMAGES_FOLDER):
        print(f"❌ Images folder not found: {IMAGES_FOLDER}")
        return None, None, state

    available_images = []
    for i in range(1, 16):
        for ext in ['.png', '.jpg', '.jpeg']:
            img_path = os.path.join(IMAGES_FOLDER, f"{i}{ext}")
            if os.path.exists(img_path):
                available_images.append((i, img_path))
                break

    if not available_images:
        print(f"❌ No images found")
        return None, None, state

    last_index = state.get('last_index', 0)
    next_position = last_index % len(available_images)
    next_num, next_image = available_images[next_position]

    print(f"🖼️ Selected image #{next_num}")
    return next_image, next_num, state

def find_free_port(start_port=8080, end_port=8090):
    """Find a free port for OAuth callback"""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except socket.error:
                continue
    return 8080

def create_static_thumbnail(image_path, output_path=None):
    """
    Create STATIC thumbnail (full image stretched, NO yellow background)
    This is what users see BEFORE clicking play
    """
    print(f"\n🎬 Creating STATIC thumbnail (what users see before playing)...")
    
    if output_path is None:
        base = os.path.splitext(image_path)[0]
        output_path = f"{base}_thumbnail.png"

    try:
        pil_img = Image.open(image_path)
        img_width, img_height = pil_img.size
        
        target_width, target_height = 1080, 1920
        
        print(f"   📸 Original: {img_width}x{img_height}")
        print(f"   📐 Stretching to: {target_width}x{target_height} (full frame, no background)")

        try:
            img_resized = pil_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        except AttributeError:
            try:
                img_resized = pil_img.resize((target_width, target_height), Image.LANCZOS)
            except:
                img_resized = pil_img.resize((target_width, target_height))

        img_resized.save(output_path, quality=90)
        print(f"   ✅ Static thumbnail created")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def create_animated_video(image_path, output_path=None, slide_duration=18, audio_file=None):
    """
    Create ANIMATED video with 60% zoom, yellow background, smooth sliding
    This is what plays AFTER clicking play
    """
    if output_path is None:
        base = os.path.splitext(image_path)[0]
        output_path = f"{base}_shorts.mp4"

    print(f"\n🎬 Creating ANIMATED video (what plays after clicking)...")
    print(f"   📷 Image: {os.path.basename(image_path)}")
    print(f"   ⏱️  Duration: {slide_duration} seconds")
    print(f"   🎨 Background: YELLOW")
    print(f"   🔍 Zoom: 60%")

    try:
        from moviepy import ImageClip, CompositeVideoClip, ColorClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
    except ImportError:
        try:
            from moviepy.editor import ImageClip, CompositeVideoClip, ColorClip, AudioFileClip
        except ImportError as e:
            print(f"❌ moviepy import failed: {e}")
            return None

    # YouTube Shorts dimensions
    screen_width, screen_height = 1080, 1920

    try:
        from PIL import Image
        
        pil_img = Image.open(image_path)
        img_width, img_height = pil_img.size
        print(f"   📸 Original: {img_width}x{img_height}")
        
        # 60% ZOOM for larger, readable text (Creative Daily style)
        fit_scale = min(screen_width / img_width, screen_height / img_height)
        zoom_factor = 1.6  # 60% zoom
        scale = fit_scale * zoom_factor
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        print(f"   🔍 Fit scale: {fit_scale:.4f}")
        print(f"   🔍 Zoom factor: {zoom_factor}")
        print(f"   🔍 Final scale: {scale:.4f}")
        print(f"   📐 Resized: {new_width}x{new_height}")

        # High quality resize
        try:
            img_resized = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except AttributeError:
            try:
                img_resized = pil_img.resize((new_width, new_height), Image.LANCZOS)
            except:
                img_resized = pil_img.resize((new_width, new_height))

        temp_img_path = base + "_temp.png"
        img_resized.save(temp_img_path)

        # Create image clip
        image_clip = ImageClip(temp_img_path, duration=slide_duration)
        
        # SMOOTH SLIDING ANIMATION (Creative Daily style)
        start_y_original = screen_height
        end_y_original = -new_height + screen_height * 0.2
        progress_at_4_8s = 4.8 / slide_duration
        eased_at_4_8s = progress_at_4_8s * progress_at_4_8s * (3 - 2 * progress_at_4_8s)
        y_at_4_8s = start_y_original + (end_y_original - start_y_original) * eased_at_4_8s
        
        new_start_y = y_at_4_8s
        new_end_y = end_y_original
        
        print(f"   📍 Animation:")
        print(f"      Start Y: {new_start_y:.1f}")
        print(f"      End Y: {new_end_y:.1f}")

        def image_slide_position(t):
            progress = min(1.0, t / slide_duration)
            eased = progress * progress * (3 - 2 * progress)
            y = new_start_y + (new_end_y - new_start_y) * eased
            return ('center', y)

        image_clip = image_clip.with_position(image_slide_position)
        
        # YELLOW BACKGROUND (Creative Daily style)
        background = ColorClip(size=(screen_width, screen_height), color=(255, 215, 0), duration=slide_duration)
        
        # Composite
        final_clip = CompositeVideoClip([background, image_clip], size=(screen_width, screen_height))
        
        print(f"   ✅ Yellow background + sliding animation set")

        # ========== AUDIO HANDLING ==========
        audio_added = False
        
        def add_audio_to_clip(clip, audio_path, volume=0.25):
            try:
                if not os.path.exists(audio_path):
                    return clip, False
                
                audio = AudioFileClip(audio_path)
                if audio.duration < slide_duration:
                    loops = int(slide_duration / audio.duration) + 1
                    audio = audio.loop(loops)
                audio = audio.subclipped(0, slide_duration)
                
                try:
                    audio = audio.with_volume_scaled(volume)
                except AttributeError:
                    try:
                        audio = audio.volumex(volume)
                    except:
                        pass
                
                return clip.with_audio(audio), True
            except Exception as e:
                print(f"   ⚠️ Audio error: {e}")
                return clip, False

        # Try audio files
        if audio_file:
            final_clip, audio_added = add_audio_to_clip(final_clip, audio_file, 0.25)
        
        if not audio_added:
            common_audio = ["background_music.mp3", "shorts_music.mp3", "audio.mp3", "music.mp3", "bgm.mp3"]
            for audio in common_audio:
                if os.path.exists(audio):
                    final_clip, audio_added = add_audio_to_clip(final_clip, audio, 0.25)
                    if audio_added:
                        break
        
        if not audio_added:
            print(f"   ℹ️ No audio added - video will be silent")

        # Render video
        print(f"   💾 Rendering video...")
        audio_codec = 'aac' if audio_added else None

        try:
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec=audio_codec,
                fps=30,
                bitrate="5000k",
                preset='medium',
                logger=None
            )
        except TypeError:
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec=audio_codec,
                fps=30,
                bitrate="5000k",
                preset='medium'
            )

        final_clip.close()
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)

        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   ✅ Video created: {file_size_mb:.1f} MB")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def upload_to_youtube(video_path, thumbnail_path=None):
    """Upload video to YouTube as Short"""
    print(f"\n📤 Uploading to YouTube...")

    video_description = f"""{VIDEO_TITLE}

{HASHTAGS}
Welcome to the Stupid Orange world where stories are turned to royalties.

Share your Stupid Broke Moment: https://www.stupidorange.com/share-moment/

#stupidorange #creativedaily #stupidestbrokeguy #Dubai #UAE #fyp
"""

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        credentials = None

        if os.path.exists("token.pickle"):
            with open("token.pickle", 'rb') as f:
                credentials = pickle.load(f)
            print(f"   📂 Loaded saved credentials")

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print("   🔄 Refreshing token...")
                credentials.refresh(Request())
            else:
                if not os.path.exists("client_secrets.json"):
                    print(f"   ❌ No client_secrets.json found!")
                    return {'status': 'skipped', 'error': 'No credentials'}
                
                print("   🔐 Opening browser for authentication...")
                flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
                try:
                    credentials = flow.run_local_server(port=find_free_port(), open_browser=True)
                except OSError:
                    credentials = flow.run_local_server(open_browser=True)
            
            with open("token.pickle", 'wb') as f:
                pickle.dump(credentials, f)
                print(f"   💾 Saved credentials")

        youtube = build('youtube', 'v3', credentials=credentials)
        print(f"   ✅ YouTube service built")

        body = {
            'snippet': {
                'title': VIDEO_TITLE[:100],
                'description': video_description[:5000],
                'tags': ['stupidorange', 'creativedaily', 'shorts'],
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        
        retry_count = 0
        response = None
        while retry_count < 3 and response is None:
            try:
                response = request.execute()
            except Exception as e:
                retry_count += 1
                print(f"   ⚠️ Attempt {retry_count} failed: {e}")
                if retry_count >= 3:
                    raise
                time.sleep(5)
        
        video_id = response['id']
        video_url = f"https://youtube.com/shorts/{video_id}"
        print(f"   ✅ Uploaded! URL: {video_url}")

        # Upload static thumbnail
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                print(f"   🖼️ Uploading static thumbnail...")
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                print(f"   ✅ Static thumbnail uploaded!")
            except Exception as e:
                print(f"   ⚠️ Thumbnail error: {e}")

        return {'status': 'success', 'video_url': video_url}

    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'failed', 'error': str(e)}

def main():
    print("="*60)
    print("🎬 DAILY YOUTUBE SHORTS - CREATIVE DAILY STYLE")
    print("📸 Static thumbnail + 🎬 Yellow background + Sliding animation")
    print("="*60)

    image_path, image_num, state = get_next_image()
    if image_path is None:
        sys.exit(0)

    print(f"\n🎯 Processing: {os.path.basename(image_path)}")
    
    # Create STATIC thumbnail (what users see before clicking)
    thumbnail_path = create_static_thumbnail(image_path)
    
    # Create ANIMATED video with yellow background and sliding
    video_path = create_animated_video(image_path, slide_duration=VIDEO_DURATION)
    
    if video_path is None:
        print("❌ Video creation failed!")
        sys.exit(1)

    # Upload to YouTube
    result = upload_to_youtube(video_path, thumbnail_path)
    
    if result and result['status'] == 'success':
        # Update state
        state['last_index'] = image_num
        state['last_date'] = datetime.now().strftime("%Y-%m-%d")
        state['last_image'] = os.path.basename(image_path)
        save_state(state)
        
        # Commit and push the state file to GitHub
        commit_and_push_state()
        
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print(f"   📸 Thumbnail: Static (full image, no background)")
        print(f"   🎬 Video: Yellow background + 60% zoom + sliding animation")
        print(f"   🔗 URL: {result['video_url']}")
        print(f"   📁 State saved and pushed to GitHub")
        print("="*60)
    else:
        print(f"\n❌ FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
