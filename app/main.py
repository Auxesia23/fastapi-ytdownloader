from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
import tempfile
import os
from pytubefix import YouTube
import urllib.parse

app = FastAPI()

@app.get("/download")
async def download_video(youtube_url: str):
    if not youtube_url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")

    try:
        # Fetch the YouTube video
        yt = YouTube(youtube_url)
        video_stream = yt.streams.get_highest_resolution()

        if video_stream is None:
            raise HTTPException(status_code=404, detail="No available stream found for the video.")

        # Create a temporary file with delete=True
        temp_file = tempfile.NamedTemporaryFile(delete=True, suffix=".mp4")
        temp_filename = temp_file.name
        
        # Download the video to the temporary file
        video_stream.download(output_path=os.path.dirname(temp_filename), filename=os.path.basename(temp_filename))

        # Percent-encode the filename to handle special characters
        encoded_filename = urllib.parse.quote(f"{yt.title}.mp4")

        # Rewind the file to the beginning so it can be read from the start
        temp_file.seek(0)

        # Return a StreamingResponse using the temporary file
        return StreamingResponse(
            temp_file,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
