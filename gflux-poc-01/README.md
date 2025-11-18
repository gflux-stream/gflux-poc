# gflux-poc-01

### Goal
Programmatically transfer buffers from appsink to appsrc.

### Approach
1. Create gstreamer pipelines as follows:
    ```
    videotestsrc  -->  appsink
    appsrc        -->  autovideosink
    ```
2. In the appsink's "new-sample" callback, push received buffers into appsrc.
3. Set appsrc caps based on the first buffer received from appsink.
4. Set both pipelines to PLAYING and run main loop.
5. On EOS/error stop and clean up.

### Run

- Prerequisites (macOS/Homebrew):
        - `brew install gstreamer gobject-introspection pygobject3`

- Run the demo:

```zsh
python3 gflux_poc_01.py
```

You should see the test video rendered via `autovideosink`. Buffers are produced by `videotestsrc`, received on `appsink`, then immediately pushed into `appsrc` and displayed.
