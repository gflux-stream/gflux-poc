#!/usr/bin/env python3
# gapless_playback_concat.py
#
# Usage:
#   python3 gapless_playback_concat.py first.mp4 second.mp4
#
# macOS/Homebrew example:
#   brew install gstreamer gst-plugins-base gst-plugins-good pygobject3
#
# Linux example:
#   sudo apt install python3-gi gir1.2-gstreamer-1.0 \
#       gstreamer1.0-plugins-base gstreamer1.0-plugins-good

import pathlib
import sys

import gi
gi.require_version("Gst", "1.0")
gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gst, Gtk

Gst.init(None)


class GaplessConcat:
    def __init__(self, filenames):
        self.pipeline = Gst.Pipeline.new("gapless-av-concat")

        self.audio_concat = Gst.ElementFactory.make("concat", "audio-concat")
        self.video_concat = Gst.ElementFactory.make("concat", "video-concat")
        self.sync = Gst.ElementFactory.make("streamsynchronizer", "sync")

        # Convert before output so different source formats are accepted.
        self.audio_convert = Gst.ElementFactory.make("audioconvert", "aconv")
        self.audio_resample = Gst.ElementFactory.make("audioresample", "aresample")
        self.audio_sink = Gst.ElementFactory.make("autoaudiosink", "asink")

        self.video_convert = Gst.ElementFactory.make("videoconvert", "vconv")
        self.video_sink = Gst.ElementFactory.make("autovideosink", "vsink")

        self.audio_concat.set_property("adjust-base", False)
        self.video_concat.set_property("adjust-base", False)

        elements = [
            self.audio_concat, self.video_concat, self.sync,
            self.audio_convert, self.audio_resample, self.audio_sink,
            self.video_convert, self.video_sink,
        ]
        if not all(elements):
            raise RuntimeError("Required GStreamer plugins are not installed")

        for element in elements:
            self.pipeline.add(element)

        # Request synchronizer pads in a known order: audio=0, video=1.
        self.sync_audio_sink = self.sync.request_pad_simple("sink_%u")
        self.sync_video_sink = self.sync.request_pad_simple("sink_%u")

        self._link_pads(
            self.audio_concat.get_static_pad("src"),
            self.sync_audio_sink,
            "audio concat -> streamsynchronizer",
        )
        self._link_pads(
            self.video_concat.get_static_pad("src"),
            self.sync_video_sink,
            "video concat -> streamsynchronizer",
        )

        # These corresponding src pads appear once the sync sink pads exist.
        sync_audio_src = self.sync.get_static_pad("src_0")
        sync_video_src = self.sync.get_static_pad("src_1")
        if not sync_audio_src or not sync_video_src:
            raise RuntimeError("streamsynchronizer did not create output pads")

        self._link_pads(
            sync_audio_src,
            self.audio_convert.get_static_pad("sink"),
            "sync audio -> audioconvert",
        )
        self._link_pads(
            sync_video_src,
            self.video_convert.get_static_pad("sink"),
            "sync video -> videoconvert",
        )

        self.audio_convert.link(self.audio_resample)
        self.audio_resample.link(self.audio_sink)

        self.video_convert.link(self.video_sink)

        self.decode_bins = []

        # Add one uridecodebin per input program.
        for index, filename in enumerate(filenames):
            if '://' in filename:
                uri = filename
            else:
                uri = pathlib.Path(filename).expanduser().resolve().as_uri()

            decode = Gst.ElementFactory.make("uridecodebin", f"decode-{index}")
            if not decode:
                raise RuntimeError("uridecodebin is unavailable")

            self.decode_bins.append(decode)

            decode.set_property("uri", uri)
            decode.connect("pad-added", self.on_decode_pad_added, index)
            self.pipeline.add(decode)

        

    @staticmethod
    def _link_pads(src_pad, sink_pad, description):
        result = src_pad.link(sink_pad)
        if result != Gst.PadLinkReturn.OK:
            raise RuntimeError(f"Failed to link {description}: {result.value_nick}")

    def on_decode_pad_added(self, decode, pad, file_index):
        caps = pad.get_current_caps() or pad.query_caps(None)
        structure = caps.get_structure(0)
        media_type = structure.get_name()

        if media_type.startswith("audio/"):
            concat = self.audio_concat
        elif media_type.startswith("video/"):
            concat = self.video_concat
        else:
            return  # Ignore subtitles, metadata, etc.

        # A queue creates a separate streaming thread and prevents one branch
        # from stalling the other while concat prepares the following item.
        queue = Gst.ElementFactory.make(
            "queue", f"{media_type.split('/')[0]}-queue-{file_index}"
        )
        self.pipeline.add(queue)
        queue.sync_state_with_parent()

        self._link_pads(
            pad, queue.get_static_pad("sink"), f"{decode.get_name()} -> queue"
        )

        concat_sink = concat.request_pad_simple("sink_%u")
        self._link_pads(
            queue.get_static_pad("src"), concat_sink, "queue -> concat"
        )

    def run(self):
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_bus_message)

        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            Gtk.main()
        finally:
            self.pipeline.set_state(Gst.State.NULL)

    def on_bus_message(self, _bus, message):
        if message.type == Gst.MessageType.ERROR:
            error, debug = message.parse_error()
            print(f"ERROR: {error.message}", file=sys.stderr)
            if debug:
                print(debug, file=sys.stderr)
            Gtk.main_quit()
        elif message.type == Gst.MessageType.EOS:
            Gtk.main_quit()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} FIRST_MEDIA SECOND_MEDIA [MORE_MEDIA ...]")
        raise SystemExit(2)

    GaplessConcat(sys.argv[1:]).run()