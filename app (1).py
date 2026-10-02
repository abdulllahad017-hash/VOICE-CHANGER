import asyncio
import os
import tempfile

import edge_tts
import streamlit as st
from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips

VOICES = {
    "English (US) - Female": "en-US-JennyNeural",
    "English (US) - Male": "en-US-GuyNeural",
    "English (India) - Female": "en-IN-NeerjaNeural",
    "English (India) - Male": "en-IN-PrabhatNeural",
    "Hindi - Female": "hi-IN-SwaraNeural",
    "Hindi - Male": "hi-IN-MadhurNeural",
}


async def make_voice(text: str, voice: str, path: str) -> None:
    await edge_tts.Communicate(text, voice).save(path)


def build_video(clip_paths, audio_path, out_path, size=(1280, 720)):
    audio = AudioFileClip(audio_path)
    clips = [VideoFileClip(p).resized(size) for p in clip_paths]

    # Repeat the uploaded clips until the video is as long as the voice
    segments, total, i = [], 0.0, 0
    while total < audio.duration:
        clip = clips[i % len(clips)]
        segments.append(clip)
        total += clip.duration
        i += 1

    video = concatenate_videoclips(segments).subclipped(0, audio.duration)
    video = video.with_audio(audio)
    video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac")


st.title("Text to Voice Video Maker")

uploaded = st.file_uploader(
    "Upload video clips", type=["mp4", "mov", "mkv"], accept_multiple_files=True
)
text = st.text_area("Your script / text", height=200)
voice_label = st.selectbox("Voice", list(VOICES.keys()))

if st.button("Create video"):
    if not uploaded or not text.strip():
        st.error("Please upload at least one clip and enter some text.")
    else:
        with st.spinner("Making your video..."):
            workdir = tempfile.mkdtemp()

            clip_paths = []
            for f in uploaded:
                p = os.path.join(workdir, f.name)
                with open(p, "wb") as out:
                    out.write(f.read())
                clip_paths.append(p)

            audio_path = os.path.join(workdir, "voice.mp3")
            asyncio.run(make_voice(text, VOICES[voice_label], audio_path))

            out_path = os.path.join(workdir, "final.mp4")
            build_video(clip_paths, audio_path, out_path)

        st.success("Done!")
        st.video(out_path)
        with open(out_path, "rb") as v:
            st.download_button("Download video", v, file_name="final.mp4")
