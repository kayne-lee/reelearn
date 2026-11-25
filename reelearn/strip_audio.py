"""Copy an MP4 without its audio track (no re-encode).  python -m reelearn.strip_audio in.mp4 out.mp4"""
import sys

import av


def strip_audio(src: str, dst: str) -> None:
    with av.open(src) as inp, av.open(dst, "w") as out:
        v_in = inp.streams.video[0]
        v_out = out.add_stream_from_template(v_in)
        for packet in inp.demux(v_in):
            if packet.dts is None:
                continue
            packet.stream = v_out
            out.mux(packet)


if __name__ == "__main__":
    strip_audio(sys.argv[1], sys.argv[2])
