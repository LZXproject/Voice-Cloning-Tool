import os
import time
import threading
from pathlib import Path
from datetime import datetime

import numpy as np
import soundcard as sc
import soundfile as sf
import noisereduce as nr
from scipy.signal import butter, sosfiltfilt

import tkinter as tk
from tkinter import messagebox


# =========================
# 基础配置
# =========================

SAMPLE_RATE = 48000          # 高质量采样率
CHANNELS = 2                 # 立体声
BLOCK_SIZE = 2048            # 每次读取帧数
OUTPUT_DIR = Path("recordings")

# 降噪强度：0.45 比较自然，0.65 比较明显，0.85 可能损伤音乐细节
DENOISE_STRENGTH = 0.65

# 是否做轻微高通滤波，去掉极低频杂音
ENABLE_HIGH_PASS = True
HIGH_PASS_FREQ = 35.0

# 导出 wav 格式
WAV_SUBTYPE = "PCM_24"


class SystemAudioRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("电脑声音录音器")
        self.root.geometry("430x250")
        self.root.resizable(False, False)

        self.is_recording = False
        self.stop_event = threading.Event()
        self.record_thread = None
        self.audio_chunks = []
        self.start_time = None

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        self.build_ui()
        self.update_timer()

    def build_ui(self):
        title = tk.Label(
            self.root,
            text="电脑系统声音录音器",
            font=("Microsoft YaHei", 17, "bold")
        )
        title.pack(pady=15)

        self.status_label = tk.Label(
            self.root,
            text="状态：未录制",
            font=("Microsoft YaHei", 11)
        )
        self.status_label.pack(pady=5)

        self.time_label = tk.Label(
            self.root,
            text="录制时长：00:00",
            font=("Microsoft YaHei", 11)
        )
        self.time_label.pack(pady=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)

        self.start_btn = tk.Button(
            btn_frame,
            text="开始录制",
            width=14,
            height=2,
            font=("Microsoft YaHei", 11),
            command=self.start_recording
        )
        self.start_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = tk.Button(
            btn_frame,
            text="结束录制",
            width=14,
            height=2,
            font=("Microsoft YaHei", 11),
            state=tk.DISABLED,
            command=self.stop_recording
        )
        self.stop_btn.grid(row=0, column=1, padx=10)

        tip = tk.Label(
            self.root,
            text="说明：仅录制电脑正在播放的声音，不录麦克风。",
            font=("Microsoft YaHei", 9),
            fg="#666666"
        )
        tip.pack(pady=8)

    def set_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def set_buttons(self, recording):
        def update():
            if recording:
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
            else:
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)

        self.root.after(0, update)

    def start_recording(self):
        if self.is_recording:
            return

        self.audio_chunks = []
        self.stop_event.clear()
        self.is_recording = True
        self.start_time = time.time()

        self.set_buttons(True)
        self.set_status("状态：正在录制电脑声音...")

        self.record_thread = threading.Thread(
            target=self.record_worker,
            daemon=True
        )
        self.record_thread.start()

    def stop_recording(self):
        if not self.is_recording:
            return

        self.set_status("状态：正在结束录制，请稍等...")
        self.stop_event.set()
        self.set_buttons(False)

    def find_loopback_device(self):
        """
        获取默认扬声器对应的 loopback 录音设备。
        这样录到的是系统播放声音，而不是麦克风。
        """
        speaker = sc.default_speaker()

        try:
            loopback = sc.get_microphone(
                id=speaker.name,
                include_loopback=True
            )
            return loopback
        except Exception:
            pass

        microphones = sc.all_microphones(include_loopback=True)

        loopbacks = [
            m for m in microphones
            if getattr(m, "isloopback", False)
        ]

        if not loopbacks:
            raise RuntimeError(
                "没有找到系统声音 loopback 设备。"
                "请确认你的系统支持 WASAPI Loopback，或检查声卡驱动。"
            )

        speaker_name = speaker.name.lower()

        for m in loopbacks:
            if speaker_name in m.name.lower() or m.name.lower() in speaker_name:
                return m

        return loopbacks[0]

    def record_worker(self):
        try:
            loopback = self.find_loopback_device()

            self.set_status(f"状态：正在录制：{loopback.name}")

            with loopback.recorder(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                blocksize=BLOCK_SIZE
            ) as recorder:

                while not self.stop_event.is_set():
                    data = recorder.record(numframes=BLOCK_SIZE)

                    if data is None:
                        continue

                    data = np.asarray(data, dtype=np.float32)

                    if data.ndim == 1:
                        data = data.reshape(-1, 1)

                    if data.shape[1] == 1 and CHANNELS == 2:
                        data = np.repeat(data, 2, axis=1)

                    self.audio_chunks.append(data)

            self.is_recording = False

            if not self.audio_chunks:
                self.set_status("状态：没有录到音频")
                messagebox.showwarning("提示", "没有录到任何声音。")
                return

            self.set_status("状态：正在降噪处理...")

            audio = np.concatenate(self.audio_chunks, axis=0)

            if len(audio) < SAMPLE_RATE // 2:
                self.set_status("状态：录制时间太短")
                messagebox.showwarning("提示", "录制时间太短，建议至少录制 1 秒以上。")
                return

            processed = self.process_audio(audio)

            filename = datetime.now().strftime("system_audio_%Y%m%d_%H%M%S.wav")
            output_path = OUTPUT_DIR / filename

            sf.write(
                file=str(output_path),
                data=processed,
                samplerate=SAMPLE_RATE,
                subtype=WAV_SUBTYPE
            )

            self.set_status(f"状态：保存完成：{output_path}")
            messagebox.showinfo(
                "录制完成",
                f"音频已保存：\n{output_path.resolve()}"
            )

        except Exception as e:
            self.is_recording = False
            self.set_status("状态：录制失败")
            messagebox.showerror("错误", str(e))

        finally:
            self.is_recording = False
            self.set_buttons(False)

    def process_audio(self, audio):
        """
        降噪 + 去极低频 + 防削波 + 归一化。
        """
        audio = np.asarray(audio, dtype=np.float32)

        audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)

        # 防止极端音量爆掉
        audio = np.clip(audio, -1.0, 1.0)

        # 去掉 DC 偏移
        audio = audio - np.mean(audio, axis=0, keepdims=True)

        # 轻微高通滤波，减少低频轰鸣
        if ENABLE_HIGH_PASS:
            audio = self.high_pass_filter(audio, SAMPLE_RATE, HIGH_PASS_FREQ)

        # noisereduce 对每个声道分别处理
        reduced_channels = []

        for ch in range(audio.shape[1]):
            channel_data = audio[:, ch]

            try:
                reduced = nr.reduce_noise(
                    y=channel_data,
                    sr=SAMPLE_RATE,
                    stationary=False,
                    prop_decrease=DENOISE_STRENGTH
                )
            except Exception:
                reduced = channel_data

            reduced_channels.append(reduced.astype(np.float32))

        processed = np.stack(reduced_channels, axis=1)

        # 再次清理异常值
        processed = np.nan_to_num(processed, nan=0.0, posinf=0.0, neginf=0.0)

        # 峰值归一化，保留一点余量，避免爆音
        peak = float(np.max(np.abs(processed)))

        if peak > 0:
            processed = processed / peak * 0.96

        processed = np.clip(processed, -1.0, 1.0)

        return processed.astype(np.float32)

    def high_pass_filter(self, audio, sr, cutoff):
        try:
            sos = butter(
                N=4,
                Wn=cutoff,
                btype="highpass",
                fs=sr,
                output="sos"
            )

            filtered = np.zeros_like(audio, dtype=np.float32)

            for ch in range(audio.shape[1]):
                filtered[:, ch] = sosfiltfilt(sos, audio[:, ch]).astype(np.float32)

            return filtered

        except Exception:
            return audio

    def update_timer(self):
        if self.is_recording and self.start_time is not None:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.time_label.config(
                text=f"录制时长：{minutes:02d}:{seconds:02d}"
            )
        else:
            if not self.is_recording:
                self.time_label.config(text="录制时长：00:00")

        self.root.after(500, self.update_timer)


def main():
    root = tk.Tk()
    app = SystemAudioRecorder(root)
    root.mainloop()


if __name__ == "__main__":
    main()