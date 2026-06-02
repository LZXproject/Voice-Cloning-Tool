# System Audio Recorder

A simple desktop tool for recording system audio from your computer.

This project provides a lightweight graphical interface for recording the sound currently playing on your computer. It does not record microphone input. After recording, the audio is automatically processed with noise reduction, optional high-pass filtering, clipping protection, and peak normalization, then saved as a high-quality WAV file.

## Features

- Simple graphical interface built with Tkinter
- Records system playback audio only
- Does not record microphone input
- Automatically detects the default speaker loopback device
- Stereo recording support
- 48 kHz sample rate by default
- Automatic noise reduction after recording
- Optional high-pass filtering to reduce low-frequency rumble
- Peak normalization to reduce clipping risk
- Exports high-quality 24-bit PCM WAV files
- Automatically saves recordings with timestamped filenames
- Creates a `recordings` folder automatically

## Use Cases

This tool is useful for:

- Recording audio played by a web browser
- Recording online courses, lectures, or tutorials
- Capturing audio from media players
- Saving system playback audio as WAV files
- Creating clean audio samples for personal projects
- Recording computer audio without capturing microphone noise

> Please use this tool responsibly. Make sure you comply with all applicable laws, platform rules, and copyright restrictions when recording audio.

## Requirements

Recommended environment:

- Windows 10 or Windows 11
- Python 3.9 or later
- A system audio device that supports WASAPI loopback recording

This project is mainly designed for Windows system audio recording.  
If no loopback device is found, please check your audio driver, default playback device, and system sound settings.

## Installation

Install the required Python packages:

```bash
pip install numpy soundcard soundfile noisereduce scipy
```

Tkinter is also required for the graphical interface.  
On most official Windows Python installations, Tkinter is already included.

## Quick Start

Save the script as:

```text
system_audio_recorder.py
```

Run it with Python:

```bash
python system_audio_recorder.py
```

A small recording window will appear.

Basic workflow:

1. Click **Start Recording**
2. Play the audio on your computer
3. Click **Stop Recording**
4. Wait for the post-processing step to finish
5. Find the exported WAV file in the `recordings` folder

## Output

Recorded files are saved to:

```text
recordings/
```

Example filename:

```text
system_audio_20260602_153012.wav
```

Default output format:

```text
WAV / PCM_24 / 48000 Hz / Stereo
```

## Configuration

You can adjust the main settings at the top of the script:

```python
SAMPLE_RATE = 48000
CHANNELS = 2
BLOCK_SIZE = 2048
OUTPUT_DIR = Path("recordings")

DENOISE_STRENGTH = 0.65

ENABLE_HIGH_PASS = True
HIGH_PASS_FREQ = 35.0

WAV_SUBTYPE = "PCM_24"
```

### Configuration Details

| Option | Description |
| --- | --- |
| `SAMPLE_RATE` | Recording sample rate. Default: `48000` |
| `CHANNELS` | Number of channels. Default: `2` for stereo |
| `BLOCK_SIZE` | Number of frames read per audio block |
| `OUTPUT_DIR` | Output directory for recordings |
| `DENOISE_STRENGTH` | Noise reduction strength |
| `ENABLE_HIGH_PASS` | Enables or disables high-pass filtering |
| `HIGH_PASS_FREQ` | High-pass filter cutoff frequency |
| `WAV_SUBTYPE` | WAV output subtype |

## Noise Reduction Strength

The default value is:

```python
DENOISE_STRENGTH = 0.65
```

Suggested values:

| Value | Recommended Use |
| --- | --- |
| `0.45` | More natural sound, better for music |
| `0.65` | Balanced default setting |
| `0.85` | Stronger noise reduction, better for speech but may affect details |

For music recording, `0.45` to `0.65` is usually recommended.  
For voice, lectures, and tutorials, `0.65` to `0.85` may work better.

## Troubleshooting

### No loopback device was found

Possible causes:

- Your audio driver does not expose a loopback device
- Your default playback device is not configured correctly
- Your system audio device is disabled
- Your audio driver is outdated
- You are using a special virtual or Bluetooth audio device

Possible solutions:

- Make sure your speaker or headphones are set as the default playback device
- Update your audio driver
- Restart the program
- Try switching to another playback device
- Make sure your computer is actually playing audio

### The recording is silent

Please check:

- Whether audio was playing during recording
- Whether the system volume was muted or too low
- Whether the correct playback device was selected
- Whether a virtual audio device is interfering with the loopback source

### The recorded music sounds distorted

Try lowering the noise reduction strength:

```python
DENOISE_STRENGTH = 0.45
```

You can also disable high-pass filtering:

```python
ENABLE_HIGH_PASS = False
```

### The recording is too short

The script checks whether the recorded audio is long enough before saving.  
It is recommended to record for at least one second.

## Suggested Project Structure

```text
system-audio-recorder/
├── system_audio_recorder.py
├── README.md
├── LICENSE
└── recordings/
```

You may want to ignore generated audio files in Git:

```gitignore
recordings/
*.wav
```

## License

This project is recommended to be released under the MIT License.

The MIT License allows others to use, modify, distribute, and build upon this project, including for commercial purposes, as long as the original copyright notice and license text are preserved.

## Disclaimer

This project is intended for educational, research, and lawful personal recording purposes only.

Users are responsible for ensuring that any recorded content complies with local laws, platform terms, and copyright regulations. The author is not responsible for any misuse of this software.
