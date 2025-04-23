import os
import subprocess

def get_audio_format(video_path):
    """获取视频的音频编码格式"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_name",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def extract_audio(video_path, output_dir):
    """使用 ffmpeg 提取音频并保存到指定目录"""
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # 检查是否有音频流
    audio_format = get_audio_format(video_path)
    if not audio_format:
        print(f"No audio stream found in {video_path}, skipping...")
        return

    # 根据音频编码选择扩展名
    format_map = {
        "aac": "m4a",
        "mp3": "mp3",
        "opus": "opus",
        "vorbis": "ogg",
        "flac": "flac",
    }
    ext = format_map.get(audio_format, "m4a")  # 默认 m4a（AAC）
    audio_output_path = os.path.join(output_dir, f"{video_name}.{ext}")

    # 构造 ffmpeg 命令（直接复制音频流）
    ffmpeg_command = [
        "ffmpeg",
        "-i", video_path,
        "-map", "0:a",
        "-c:a", "copy",  # 直接复制，不转码
        "-vn",
        audio_output_path
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Audio extracted: {audio_output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to extract audio from {video_path}: {e}")

def main():
    current_dir = os.getcwd()
    audio_dir = os.path.join(current_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    video_extensions = [".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv"]
    for root, _, files in os.walk(current_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_path = os.path.join(root, file)
                extract_audio(video_path, audio_dir)

if __name__ == "__main__":
    main()
