from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import tempfile
import os
from pytubefix import YouTube
import urllib.parse
from moviepy.editor import VideoFileClip, AudioFileClip
import shutil

app = FastAPI()

def clean_up_temp_dir(temp_dir: str):
    """Function to clean up the temporary directory after streaming."""
    try:
        shutil.rmtree(temp_dir)
        print(f"Temporary directory {temp_dir} has been removed.")
    except Exception as e:
        print(f"Error cleaning up temporary directory: {str(e)}")

@app.get("/download")
async def download_video(youtube_url: str, background_tasks: BackgroundTasks):
    if not youtube_url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")

    try:
        # Fetch the YouTube video
        yt = YouTube(youtube_url)
        
        # Get highest resolution video stream (without audio)
        video_stream = yt.streams.filter(file_extension='mp4', res='1080p', only_video=True).first()
        
        # Get the audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()

        if video_stream is None or audio_stream is None:
            raise HTTPException(status_code=404, detail="No available video or audio stream found for the video.")

        # Create a temporary directory for storing video and audio files
        temp_dir = tempfile.mkdtemp()

        # Download the video and audio to temporary files
        video_file_path = os.path.join(temp_dir, "video.mp4")
        audio_file_path = os.path.join(temp_dir, "audio.mp4")

        video_stream.download(output_path=temp_dir, filename="video.mp4")
        audio_stream.download(output_path=temp_dir, filename="audio.mp4")

        # Use moviepy to combine video and audio
        video_clip = VideoFileClip(video_file_path)
        audio_clip = AudioFileClip(audio_file_path)

        # Set the audio to the video
        video_clip = video_clip.set_audio(audio_clip)

        # Create a temporary file for the final output
        final_video_path = os.path.join(temp_dir, "final_video.mp4")
        video_clip.write_videofile(final_video_path, codec='libx264', audio_codec='aac')

        # Percent-encode the filename to handle special characters
        encoded_filename = urllib.parse.quote(f"{yt.title}.mp4")

        # Open the final video file for streaming
        final_video_file = open(final_video_path, "rb")

        # Register the background task to clean up the temporary directory
        background_tasks.add_task(clean_up_temp_dir, temp_dir)

        # Return a StreamingResponse using the final video file
        return StreamingResponse(
            final_video_file,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
