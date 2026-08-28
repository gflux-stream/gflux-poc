Webcam to file (ingest)
```
gst-launch-1.0 -e \
    autovideosrc ! videoconvert ! videoscale \
        ! video/x-raw,width=1920,height=1080,framerate=25/1 \
        ! queue ! x264enc tune=zerolatency  ! queue ! mux. \
    autoaudiosrc ! queue ! audioconvert ! audioresample \
        ! faac ! queue ! mux. \
    mp4mux name=mux ! filesink location=file.mp4
```

Webcam to RTMP stream (YouTube)
```
gst-launch-1.0 \
    autovideosrc \
        ! videoconvert \
        ! "video/x-raw,width=1920,height=1080,framerate=30/1" \
        ! queue \
        ! x264enc tune=zerolatency cabac=1 bframes=2 ref=1 \
        ! "video/x-h264,profile=main" \
        ! queue ! flvmux streamable=true name=mux \
        ! rtmpsink location="${RTMP_DST} live=1" \
    autoaudiosrc \
        ! faac bitrate=128000 \
        ! queue ! mux.
```

SRT to RTMP stream (YouTube) without reencoding
```
gst-launch-1.0 srtsrc uri="${SRT_SRC}" \
        ! tsdemux name=d \
    d. ! queue ! h264parse ! queue ! mux. \
    d. ! queue ! aacparse ! queue ! mux. \
    flvmux name=mux streamable=true ! \
    rtmpsink location="${RTMP_DST} live=1"
```
