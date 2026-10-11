#!/usr/bin/env python3
"""Static guard for *identified* Sega FILM/Cinepak assets (stdlib only).

Use only after confirming this profile on the unmodified target CPK. A
successful result proves structure, NOT gameplay or Saturn playback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


class CPKError(ValueError):
    """An independently actionable FILM/CPK contract violation."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise CPKError(reason)


def u24(buf: bytes, at: int) -> int:
    return int.from_bytes(buf[at : at + 3], "big")


@dataclass(frozen=True)
class Packet:
    offset: int
    size: int
    pts: int
    duration: int
    raw: bytes
    geometry: tuple

    @property
    def audio(self) -> bool:
        return self.pts == 0xFFFFFFFF


@dataclass(frozen=True)
class Film:
    data: bytes
    header_size: int
    fdsc: bytes
    timescale: int
    packets: tuple[Packet, ...]


def parse(raw: bytes, label: str, alignment: int = 4, size_bias: int = 8) -> Film:
    require(len(raw) >= 64 and raw[:4] == b"FILM", f"{label}: not FILM")
    head = int.from_bytes(raw[4:8], "big")
    require(64 <= head <= len(raw), f"{label}: invalid header boundary")
    fdsc = raw.find(b"FDSC", 8, head)
    stab = raw.find(b"STAB", 8, head)
    require(fdsc >= 0 and stab >= 0, f"{label}: missing FDSC or STAB")
    fsize = int.from_bytes(raw[fdsc + 4:fdsc + 8], "big")
    ssize, clock, count = struct.unpack_from(">III", raw, stab + 4)
    require(fsize >= 8 and fdsc + fsize <= head, f"{label}: FDSC range")
    require(ssize == 16 + 16 * count and stab + ssize <= head,
            f"{label}: STAB entry table bounds/size")
    require(clock > 0 and 0 < count < 100000, f"{label}: invalid timescale/count")
    packets = []
    prev_end = 0
    for index in range(count):
        off, size, pts, dur = struct.unpack_from(">IIII", raw, stab + 16 + 16 * index)
        tag = f"{label}: STAB[{index}]"
        require(size > 0 and off + size <= len(raw) - head, f"{tag}: out of bounds")
        require(off % alignment == 0 and size % alignment == 0,
                f"{tag}: unaligned offset/size (required {alignment})")
        require(off >= prev_end, f"{tag}: overlapping or reversed packet")
        require(dur > 0, f"{tag}: zero duration")
        payload = raw[head + off : head + off + size]
        geometry = ()
        if pts != 0xFFFFFFFF:
            require(len(payload) >= 24, f"{tag}: short Cinepak packet")
            require(len(payload) - u24(payload, 1) == size_bias,
                    f"{tag}: unexpected Sega Cinepak size bias")
            require(payload[10:12] == b"\0\0", f"{tag}: unexpected Sega two-byte prefix")
            nstrips = int.from_bytes(payload[8:10], "big")
            require(1 <= nstrips <= 64, f"{tag}: invalid strip count")
            pos, rects = 12, []
            for strip in range(nstrips):
                require(pos + 12 <= len(payload), f"{tag}: strip {strip} header overrun")
                stop = pos + u24(payload, pos + 1)
                require(stop > pos + 12 and stop <= len(payload),
                        f"{tag}: strip {strip} size invalid")
                require((stop - pos) % alignment == 0,
                        f"{tag}: strip {strip} is not {alignment}-byte aligned")
                rects.append(bytes(payload[pos + 4 : pos + 12]))
                cursor = pos + 12
                while cursor < stop:
                    require(cursor + 4 <= stop, f"{tag}: truncated Cinepak chunk")
                    length = int.from_bytes(payload[cursor + 2 : cursor + 4], "big")
                    require(length >= 4 and cursor + length <= stop,
                            f"{tag}: codebook/vector chunk overrun")
                    require(length % alignment == 0,
                            f"{tag}: unaligned Cinepak codebook/vector chunk")
                    cursor += length
                require(cursor == stop, f"{tag}: incomplete strip")
                pos = stop
            require(pos == len(payload), f"{tag}: unaccounted Cinepak tail")
            require(bool(pts & 0x80000000) == bool(payload[0] & 1),
                    f"{tag}: STAB key/delta flag disagrees with Cinepak packet")
            geometry = tuple(rects)
        packets.append(Packet(off, size, pts, dur, payload, geometry))
        prev_end = off + size
    return Film(raw, head, raw[fdsc : fdsc + fsize], clock, tuple(packets))


def compare(original: Film, candidate: Film) -> dict:
    require(len(original.data) == len(candidate.data),
            "Fixed ISO extent changed: output length must equal source length")
    require(original.header_size == candidate.header_size,
            "FILM payload start changed")
    require(original.fdsc == candidate.fdsc, "FDSC/codec/audio format changed")
    require(original.timescale == candidate.timescale, "FILM clock changed")
    require(len(original.packets) == len(candidate.packets), "STAB entry count changed")
    audio = video = 0
    for index, (a, b) in enumerate(zip(original.packets, candidate.packets)):
        require(a.audio == b.audio, f"STAB[{index}]: audio/video interleave changed")
        require(a.duration == b.duration and (a.pts & 0x7FFFFFFF) == (b.pts & 0x7FFFFFFF),
                f"STAB[{index}]: original timing changed")
        if a.audio:
            require(a.raw == b.raw, f"STAB[{index}]: original PCM bytes changed")
            audio += 1
        else:
            require(a.geometry == b.geometry,
                    f"STAB[{index}]: strip count/geometry changed")
            video += 1
    return {"source_sha256": hashlib.sha256(original.data).hexdigest(),
            "candidate_sha256": hashlib.sha256(candidate.data).hexdigest(),
            "video_frames": video, "pcm_packets_byte_exact": audio,
            "all_packet_strip_chunk_offsets_aligned": True,
            "original_timeline_and_geometry_preserved": True,
            "runtime": "NOT_TESTED"}


def fixture() -> bytes:
    # Two strips of 108 pixels high, one 4-byte vector chunk per strip.
    def strip() -> bytes:
        return b"\x10\x00\x00\x10" + struct.pack(">HHHH", 0, 0, 108, 288) + b"\x22\x00\x00\x04"
    video = bytearray(b"\x00\x00\x00\x24" + struct.pack(">HHH", 288, 216, 2) + b"\0\0")
    video.extend(strip() + strip())
    assert len(video) == 44
    fdsc = b"FDSC" + struct.pack(">I", 32) + b"\0" * 24
    stab = b"STAB" + struct.pack(">III", 48, 30, 2)
    stab += struct.pack(">IIII", 0, 44, 0, 2)
    stab += struct.pack(">IIII", 44, 4, 0xFFFFFFFF, 2)
    header = b"FILM" + struct.pack(">I", 96) + b"\0" * 8 + fdsc + stab
    assert len(header) == 96
    return header + video + b"\x11\x22\x33\x44"


def self_test() -> None:
    good = fixture()
    valid = parse(good, "fixture")
    compare(valid, valid)
    # Test individual, specifically diagnosed failure modes.
    tests = [
        ("STAB unaligned offset", 96 - 32 + 0, None),  # overwritten below
    ]
    cases = []
    off = 48 + 16
    for where, value, expected in (
        (off + 3, 1, "unaligned"),                 # first STAB offset
        (off + 7, 43, "unaligned"),            # first packet length
        (96 + 12 + 3, 17, "strip"),           # first strip 24-bit size low byte
        (96 + 12 + 12 + 3, 5, "chunk"),       # first 16-bit chunk length low byte
        (96 + 1 + 2, 35, "size bias"),        # Cinepak declared size low byte
    ):
        tmp = bytearray(good)
        tmp[where] = value
        cases.append((bytes(tmp), expected))
    for item, expected in cases:
        try:
            parse(item, "bad")
        except CPKError as exc:
            require(expected in str(exc), f"wrong rejection: {exc} != {expected}")
        else:
            raise AssertionError(f"accepted invalid {expected}")
    tmp = bytearray(good)
    tmp[-1] ^= 1
    try:
        compare(valid, parse(bytes(tmp), "mutated PCM"))
    except CPKError as exc:
        require("PCM" in str(exc), f"unexpected rejection: {exc}")
    else:
        raise AssertionError("changed PCM was accepted")
    print("SELF-TEST PASS: valid FILM; misaligned STAB, strip, chunk, bias, PCM rejected")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", nargs="?", type=Path)
    parser.add_argument("--original", type=Path, help="required for PCM/timing/source-size QA")
    parser.add_argument("--alignment", type=int, default=4)
    parser.add_argument("--size-bias", type=int, default=8)
    parser.add_argument("--self-test", action="store_true")
    opt = parser.parse_args()
    if opt.self_test:
        self_test()
        return 0
    require(opt.candidate is not None, "candidate CPK required")
    require(opt.alignment > 0 and opt.alignment & (opt.alignment - 1) == 0,
            "alignment must be a positive power of two")
    candidate = parse(opt.candidate.read_bytes(), str(opt.candidate),
                      opt.alignment, opt.size_bias)
    if opt.original:
        src = parse(opt.original.read_bytes(), str(opt.original), opt.alignment,
                    opt.size_bias)
        result = compare(src, candidate)
    else:
        result = {"warning": "No --original: PCM, geometry, size and timing not checked",
                  "video_frames": sum(not p.audio for p in candidate.packets),
                  "runtime": "NOT_TESTED"}
    print(json.dumps({"status": "STATIC_QA_PASS_RUNTIME_NOT_TESTED", **result},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (CPKError, AssertionError, OSError) as exc:
        print(f"STATIC_QA_FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
