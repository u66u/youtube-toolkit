from pydub import AudioSegment
from moviepy.editor import AudioFileClip, ImageClip, VideoFileClip, concatenate_videoclips
import yt_dlp as youtube_dl
import os
import re
import requests
from io import BytesIO
from PIL import Image
import mimetypes

def get_youtube_video_id(url):
    pattern = r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def download_video(url: str, output_path: str = "temp"):
    ydl_opts = {'outtmpl': f'{output_path}/%(id)s.%(ext)s'}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        info_dict = ydl.extract_info(url, download=False)
        return f"{output_path}/{info_dict['id']}.{info_dict['ext']}"

def download_file(url: str, output_path: str = "temp"):
    response = requests.get(url)
    file_name = url.split("/")[-1]
    file_path = os.path.join(output_path, file_name)
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path

def merge_audios(video_paths: list[str]):
    audio_clips = [AudioSegment.from_file(path) for path in video_paths]
    combined = AudioSegment.empty()
    for audio in audio_clips:
        combined += audio
    combined.export("temp/merged_audio.mp3", format='mp3')
    return "temp/merged_audio.mp3"

def is_gif_or_video(file_url: str) -> bool:
    mimetype, _ = mimetypes.guess_type(file_url)
    if mimetype:
        return mimetype.startswith(('video', 'image/gif'))
    return False

def generate_video(audio_path: str, image_url: str, output_path: str, loop: bool = False):
    audio = AudioFileClip(audio_path)
    if loop and is_gif_or_video(image_url):
        file_path = download_file(image_url)
        img_clip = VideoFileClip(file_path)
        img_clip = img_clip.set_fps(24)
        loops_required = int(audio.duration / img_clip.duration) + 1
        img_clip = concatenate_videoclips([img_clip]*loops_required, method='compose')
    else:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        img.save("temp/image.png")
        img_clip = ImageClip("temp/image.png")

    img_clip.set_duration(audio.duration).set_audio(audio).write_videofile(output_path, codec='libx264', fps=24)