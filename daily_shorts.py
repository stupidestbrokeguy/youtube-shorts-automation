"""
Daily Picture to YouTube Shorts - Static Thumbnail + Animated Video
Thumbnail: Full image stretched (static, no animation)
Video: Smooth sliding animation from bottom to top
"""

import os
import sys
import json
import pickle
import socket
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ========== CONFIGURATION ==========
VIDEO_TITLE = "Stupid Broke Money, What Happened? - Stupid Orange, Stupidest Broke Guy, Creative Daily"
HASHTAGS = "#stupidorange #creativedaily #stupidestbrokeguy #Dubai #UAE #fyp"
VIDEO_DURATION = 15
IMAGES_FOLDER = "daily_images"
STATE_FILE = "shorts_state.json"
# ===================================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        print(f"📂 Loaded state: last used {state.get('last_image', 'none')}")
        return state
    return {'last_index': 0, 'last_date': None, 'last_image': None}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"💾 State saved")

def get_next_image():
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
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except socket.error:
                continue
    return 8080

def create_thumbnail_from_image(image_path, output_path=None):
    """
    Create a STATIC thumbnail (full image stretched, NO animation)
    This is what users see before clicking play
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
        print(f"   📐 Stretching to: {target_width}x{target_height} (full frame, static)")

        # Stretch to fill entire frame (no animation, just the image)
        try:
            img_resized = pil_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        except AttributeError:
            try:
                img_resized = pil_img.resize((target_width, target_height), Image.LANCZOS)
            except:
                img_resized = pil_img.resize((target_width, target_height))

        img_resized.save(output_path, quality=90)
        print(f"   ✅ Static thumbnail created (full screen, no animation)")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def create_shorts_video(image_path, output_path=None, slide_duration=15):
    """
    Create ANIMATED video (sliding from bottom to top when played)
    This is what users see AFTER clicking play
    """
    if output_path is None:
        base = os.path.splitext(image_path)[0]
        output_path = f"{base}_shorts.mp4"

    print(f"\n🎬 Creating ANIMATED video (what plays after clicking)...")

    try:
        from moviepy import ImageClip, CompositeVideoClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
    except ImportError:
        try:
            from moviepy.editor import ImageClip, CompositeVideoClip, AudioFileClip
        except ImportError as e:
            print(f"❌ moviepy import failed: {e}")
            return None

    screen_width, screen_height = 1080, 1920

    try:
        from PIL import Image
        
        pil_img = Image.open(image_path)
        img_width, img_height = pil_img.size
        
        print(f"   📸 Original: {img_width}x{img_height}")
        
        # Make image 30% larger for sliding animation
        stretch_scale = 1.3
        new_width = int(screen_width * stretch_scale)
        new_height = int(screen_height * stretch_scale)
        
        print(f"   📐 Stretching to: {new_width}x{new_height} (for smooth sliding)")

        # Stretch image
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
        
        # SLIDING ANIMATION - starts from bottom, moves up smoothly
        start_y = screen_height  # Start completely at bottom
        end_y = -new_height + screen_height * 0.1  # End position (image mostly visible)
        
        print(f"   📍 SLIDING ANIMATION: from bottom (y={start_y}) to top (y={end_y:.0f})")
        print(f"   ⏱️  Duration: {slide_duration} seconds")

        def image_slide_position(t):
            progress = min(1.0, t / slide_duration)
            # Smooth easing function (starts slow, speeds up, ends slow)
            eased = progress * progress * (3 - 2 * progress)
            y = start_y + (end_y - start_y) * eased
            return ('center', y)

        image_clip = image_clip.with_position(image_slide_position)
        
        # No background needed - image fills everything as it slides
        final_clip = image_clip

        # Try to add audio
        audio_files = ["background_music.mp3", "shorts_music.mp3", "audio.mp3", "music.mp3"]
        for audio in audio_files:
            if os.path.exists(audio):
                try:
                    audio_clip = AudioFileClip(audio)
                    if audio_clip.duration < slide_duration:
                        loops = int(slide_duration / audio_clip.duration) + 1
                        audio_clip = audio_clip.loop(loops)
                    audio_clip = audio_clip.subclipped(0, slide_duration)
                    try:
                        audio_clip = audio_clip.with_volume_scaled(0.3)
                    except:
                        try:
                            audio_clip = audio_clip.volumex(0.3)
                        except:
                            pass
                    final_clip = final_clip.with_audio(audio_clip)
                    print(f"   🎵 Added audio: {audio}")
                    break
                except Exception as e:
                    print(f"   ⚠️ Could not add {audio}: {e}")

        print(f"   💾 Rendering animated video...")
        audio_codec = 'aac' if any(os.path.exists(a) for a in audio_files) else None

        try:
            final_clip.write_videofile(output_path, codec='libx264', audio_codec=audio_codec, fps=30, bitrate="5000k", preset='medium', logger=None)
        except TypeError:
            final_clip.write_videofile(output_path, codec='libx264', audio_codec=audio_codec, fps=30, bitrate="5000k", preset='medium')

        final_clip.close()
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)

        print(f"   ✅ ANIMATED video created with sliding effect!")
        return output_path
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def upload_to_youtube(video_path, thumbnail_path=None):
    print(f"\n📤 Uploading to YouTube...")

    video_description = f"""{VIDEO_TITLE}

{HASHTAGS}
Welcome to the Stupid Orange world where stories are turned to royalties. We ask strangers to share
their stupid broke moments and we design nice t-shirts from the inspiration, earning the responded
a royalty share for the shirt. Please feel free to go ahead, participate, connect and share the movement.

Share your Stupid Broke Moment and stand a chance to be Today's Winner - (https://www.stupidorange.com/share-moment/)

VIew our Hall of fame of Daily Winners Of the Stupid Orange Challenge - (https://www.stupidorange.com/interviews/)

Connect with Us On Social.

-Youtube connect here  - (https://www.youtube.com/@stupidestbrokeguy)
-Tiktok connect here - (https://www.tiktok.com/@stupidestbrokeguy)

Platforms Links.

- Help someone fastract to collecting their first royalty, join Stupid Solom Fashion Line Waiting List - (stupidorange.com)
- Friday Mondays show, we judge one Artist to evaluate whether overrated or not while deepdiving into creative ecomony - (fridaymondays.stupidorange.club)
- Secure the system that is helping random broke people earn their first royalty, - (creativedaily.stupidorange.com)

✨ Stupid Orange - Helping people start collecting royalties from their creativity.

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

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
                credentials = flow.run_local_server(port=find_free_port())
            with open("token.pickle", 'wb') as f:
                pickle.dump(credentials, f)

        youtube = build('youtube', 'v3', credentials=credentials)

        body = {
            'snippet': {
                'title': VIDEO_TITLE[:100],
                'description': video_description[:5000],
                'tags': ['stupidorange', 'creativedaily', 'shorts'],
                'categoryId': '22'
            },
            'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        response = request.execute()
        
        video_url = f"https://youtube.com/shorts/{response['id']}"
        print(f"   ✅ Uploaded! URL: {video_url}")

        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                print(f"   🖼️ Uploading STATIC thumbnail...")
                youtube.thumbnails().set(videoId=response['id'], media_body=MediaFileUpload(thumbnail_path)).execute()
                print(f"   ✅ Static thumbnail uploaded!")
            except Exception as e:
                print(f"   ⚠️ Thumbnail error: {e}")

        return {'status': 'success', 'video_url': video_url}
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return {'status': 'failed', 'error': str(e)}

def main():
    print("="*60)
    print("🎬 DAILY PICTURE TO YOUTUBE SHORTS")
    print("📸 STATIC Thumbnail + 🎬 ANIMATED Video")
    print("="*60)

    image_path, image_num, state = get_next_image()
    if image_path is None:
        sys.exit(0)

    print(f"\n🎯 Processing: {os.path.basename(image_path)}")
    
    # Create STATIC thumbnail (what users see before clicking)
    thumbnail_path = create_thumbnail_from_image(image_path)
    
    # Create ANIMATED video (what plays after clicking)
    video_path = create_shorts_video(image_path, slide_duration=VIDEO_DURATION)
    
    if video_path is None:
        print("❌ Video creation failed!")
        sys.exit(1)

    result = upload_to_youtube(video_path, thumbnail_path)
    
    if result and result['status'] == 'success':
        state['last_index'] = image_num
        state['last_date'] = datetime.now().strftime("%Y-%m-%d")
        state['last_image'] = os.path.basename(image_path)
        save_state(state)
        print(f"\n✅ SUCCESS! {result['video_url']}")
        print(f"\n📌 Note: Thumbnail is STATIC (full image)")
        print(f"🎬 Video has SLIDING ANIMATION from bottom to top")
    else:
        print(f"\n❌ FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
