# core/video_tools.py
from typing import List, Optional, Tuple
import os, pathlib, math
from moviepy.editor import (
    ImageClip, VideoFileClip, AudioFileClip, concatenate_videoclips,
    CompositeVideoClip, TextClip
)
from moviepy.video.fx.all import resize
from moviepy.audio.fx.all import audio_loop

DEFAULT_SIZE = (1080, 1920)  # вертикалка по умолчанию; можно менять на (1920,1080)
FPS = 30

def _norm_path(p: str) -> str:
    return str(pathlib.Path(p).expanduser().resolve())

def make_slideshow_from_images(
    images: List[str],
    out_path: str,
    duration_per_image: float = 2.0,
    kenburns: bool = True,
    captions: Optional[List[str]] = None,
    bgm_path: Optional[str] = None,
    size: Tuple[int,int] = DEFAULT_SIZE,
    fps: int = FPS
) -> str:
    """
    Собирает ролик из списка картинок.
    Ken Burns = плавный зум/панорама.
    captions[i] — подпись поверх i-й картинки (опционально).
    bgm_path — трек фоном (опционально).
    """
    clips = []
    for i, img in enumerate(images):
        img = _norm_path(img)
        base = ImageClip(img).resize(newsize=size)
        if kenburns:
            # Лёгкий "дыхательный" зум
            zoom_start = 1.05
            zoom_end = 1.0
            def zk(t):
                # линейный от 1.05 к 1.0
                z = zoom_start + (zoom_end - zoom_start) * (t / max(duration_per_image, 0.01))
                return z
            kb = base.fx(resize, zk)
            clip = kb.set_duration(duration_per_image)
        else:
            clip = base.set_duration(duration_per_image)

        if captions and i < len(captions) and captions[i]:
            try:
                txt = TextClip(captions[i], fontsize=48, color='white', font='Arial-Bold')
                txt = txt.on_color(size=(int(size[0]*0.9), None), color=(0,0,0), col_opacity=0.35)
                txt = txt.set_position(("center", int(size[1]*0.8))).set_duration(duration_per_image)
                clip = CompositeVideoClip([clip, txt], size=size).set_duration(duration_per_image)
            except Exception:
                # если нет шрифтов — молча без текста
                pass

        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    if bgm_path:
        bgm = AudioFileClip(_norm_path(bgm_path))
        if bgm.duration < video.duration:
            bgm = audio_loop(bgm, duration=video.duration)
        video = video.set_audio(bgm.volumex(0.8))

    out_path = _norm_path(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    video.write_videofile(out_path, fps=fps, codec="libx264", audio_codec="aac", bitrate="5000k")
    return out_path

def concat_videos(
    videos: List[str],
    out_path: str,
    size: Tuple[int,int] = DEFAULT_SIZE,
    fps: int = FPS
) -> str:
    """
    Склеивает видео разного размера с uniform-resize под размер.
    """
    clips = []
    for v in videos:
        v = _norm_path(v)
        vc = VideoFileClip(v)
        vc = vc.resize(newsize=size)
        clips.append(vc)
    video = concatenate_videoclips(clips, method="compose")
    out_path = _norm_path(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    video.write_videofile(out_path, fps=fps, codec="libx264", audio_codec="aac", bitrate="8000k")
    return out_path
