import os
import subprocess
import librosa
import numpy as np

def extract_audio_from_video(video_path, audio_path="temp_audio.wav"):
    """步骤 1：从视频中提取单声道音频，降低采样率以加快处理速度"""
    print(f"正在从视频中提取音轨: {video_path}...")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-ac", "1", "-ar", "22050",
        "-y", audio_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return audio_path

def detect_bat_hits(audio_path, threshold=0.4, min_interval=3.0):
    """步骤 2：利用 Librosa 检测打击瞬间的音频峰值（Onset）"""
    print("正在进行音频频谱分析与峰值检测...")
    y, sr = librosa.load(audio_path, sr=22050)
    
    # 计算音频的包络与打击乐/瞬时强度 (Onset Strength)
    # 击球瞬间在频谱上表现为突发的高频能量
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    
    # 寻找峰值点
    peaks = librosa.util.peak_pick(
        onset_env, 
        pre_max=5, 
        post_max=5, 
        pre_avg=5, 
        post_avg=5, 
        delta=threshold, 
        wait=int(sr / 512 * min_interval) # 限制两次击球之间的最小间隔（秒），防止连续误判
    )
    
    # 将帧索引转换为具体的时间戳（秒）
    timestamps = librosa.frames_to_time(peaks, sr=sr, hop_length=512)
    return timestamps

def batch_cut_videos(video_path, timestamps, output_dir="output_clips", pre_time=3.0, post_time=4.0):
    """步骤 3：根据时间戳批量切分视频片段"""
    os.makedirs(output_dir, exist_ok=True)
    print(f"共检测到 {len(timestamps)} 个击球瞬间，开始切分视频...")
    
    for i, t in enumerate(timestamps):
        # 计算每个片段的开始时间和持续时间
        start_time = max(0, t - pre_time)
        duration = pre_time + post_time
        
        output_filename = os.path.join(output_dir, f"hit_{i+1:03d}_t_{t:.1f}s.mp4")
        
        # 使用 ffmpeg 剪辑：-ss 指定起点，-t 指定持续时间
        # 采用 libx264 重新编码确保切片精准，不产生黑屏或卡顿
        cmd = [
            "ffmpeg", "-ss", str(start_time),
            "-i", video_path,
            "-t", str(duration),
            "-c:v", "libx264", "-c:a", "aac",
            "-y", output_filename
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"已生成切片: {output_filename} (发生于 {t:.2f}s)")

# === 主流程执行入口 ===
if __name__ == "__main__":
    VIDEO_FILE = "match_recording.mp4" # 替换为你的 2 小时比赛视频路径
    TEMP_AUDIO = "temp_match_audio.wav"
    
    if os.path.exists(VIDEO_FILE):
        audio_file = extract_audio_from_video(VIDEO_FILE, TEMP_AUDIO)
        
        # threshold（阈值）和 min_interval（最小间隔）可根据现场噪音大小进行微调
        hit_times = detect_bat_hits(audio_file, threshold=0.45, min_interval=4.0)
        
        # 执行切分（例如：截取击球前 3 秒到击球后 4 秒的完整打席过程）
        batch_cut_videos(VIDEO_FILE, hit_times, output_dir="baseball_hits", pre_time=3.0, post_time=5.0)
        
        # 清理临时音频文件
        if os.path.exists(TEMP_AUDIO):
            os.remove(TEMP_AUDIO)
        print("所有视频片段切分完成！")
    else:
        print(f"未找到视频文件: {VIDEO_FILE}")