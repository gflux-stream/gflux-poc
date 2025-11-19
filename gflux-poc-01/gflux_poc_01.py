import sys
import logging

import gi

gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gst, Gtk

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.DEBUG)


def main() -> int:
    Gst.init(None)

    # Producer: videotestsrc -> appsink
    producer_desc = (
        "videotestsrc pattern=smpte "
        "! appsink name=mysink emit-signals=true"
    )

    # Consumer: appsrc -> autovideosink
    # Caps are applied dynamically from the first sample arriving on appsink
    consumer_desc = (
        "appsrc name=mysrc is-live=true format=time do-timestamp=true "
        "! autovideosink"
    )

    producer = Gst.parse_launch(producer_desc)
    consumer = Gst.parse_launch(consumer_desc)

    appsink = producer.get_by_name("mysink")
    appsrc = consumer.get_by_name("mysrc")
    if appsink is None or appsrc is None:
        logging.error("Failed to create appsink/appsrc")
        return 1

    def on_new_sample(sink):
        sample = sink.emit("pull-sample")
        if sample is None:
            return Gst.FlowReturn.ERROR
        
        # Forward the buffer to appsrc
        return appsrc.emit("push-sample", sample)

    appsink.connect("new-sample", on_new_sample)

    def on_bus_message(bus: Gst.Bus, message: Gst.Message, user_data):
        mtype = message.type
        if mtype == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logging.error(f"ERROR from {message.src.get_name()}: {err}")
            if debug:
                logging.error(debug)
            Gtk.main_quit()
        elif mtype == Gst.MessageType.EOS:
            logging.info(f"EOS from {message.src.get_name()}")
            Gtk.main_quit()

    # Watch both pipelines' buses
    for pipe in (producer, consumer):
        bus = pipe.get_bus()
        bus.add_signal_watch()
        bus.connect("message", on_bus_message, None)

    # Start pipelines
    if producer.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
        logging.error("Failed to set producer to PLAYING")
        return 1
    if consumer.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
        logging.error("Failed to set consumer to PLAYING")
        return 1

    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
    finally:
        producer.set_state(Gst.State.NULL)
        consumer.set_state(Gst.State.NULL)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

