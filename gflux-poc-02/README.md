# gflux-poc-02

## Goal
Play multiple media streams back-to-back in gapless manner using concat and streamsynchronizer elements.

## Current Implementation
The script in [gapless_playback_concat.py](gapless_playback_concat.py) builds a single pipeline with:

1. One `uridecodebin` per input file.
2. Two concat branches: `audio-concat` and `video-concat`.
3. A `streamsynchronizer` between concat outputs and final converters/sinks.
4. Dynamic per-stream `queue` elements created on each decode pad to prevent branch stalling.
5. `audioconvert ! audioresample ! autoaudiosink` and `videoconvert ! autovideosink` output chains.

The script accepts 2 or more media inputs from CLI and exits on EOS or pipeline error.

## Usage
Run from workspace root:

```bash
python3 gflux-poc-02/gapless_playback_concat.py clips/clip1.mp4 clips/clip2.mp4
```

You can pass media URLs also:

```bash
python3 gflux-poc-02/gapless_playback_concat.py clips/clip1.mp4 https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm
```

## Dependencies
- Python 3
- PyGObject (`gi`)
- GStreamer 1.0
- GStreamer base and good plugins (for `concat`, `uridecodebin`, sinks, converters)

Examples:

```bash
# macOS (Homebrew)
brew install gstreamer gst-plugins-base gst-plugins-good pygobject3

# Ubuntu/Debian
sudo apt install python3-gi gir1.2-gstreamer-1.0 \
	gstreamer1.0-plugins-base gstreamer1.0-plugins-good
```




