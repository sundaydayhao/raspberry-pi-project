#!/usr/bin/env python3

from __future__ import annotations

import ctypes
import ctypes.util
from ctypes import POINTER, byref, c_int, c_uint32, c_ubyte, c_void_p

import numpy as np


def _check(result: int, func_name: str) -> None:
    if result != 0:
        raise OSError(f"{func_name} failed with error code {result}")


def _load_library() -> ctypes.CDLL:
    candidates = [
        "librtlsdr.so.0",
        "librtlsdr.so",
        ctypes.util.find_library("rtlsdr"),
    ]
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            return ctypes.CDLL(candidate)
        except OSError:
            continue
    raise OSError("Unable to load librtlsdr shared library")


_LIB = _load_library()

_LIB.rtlsdr_open.argtypes = [POINTER(c_void_p), c_uint32]
_LIB.rtlsdr_open.restype = c_int
_LIB.rtlsdr_close.argtypes = [c_void_p]
_LIB.rtlsdr_close.restype = c_int
_LIB.rtlsdr_set_center_freq.argtypes = [c_void_p, c_uint32]
_LIB.rtlsdr_set_center_freq.restype = c_int
_LIB.rtlsdr_set_sample_rate.argtypes = [c_void_p, c_uint32]
_LIB.rtlsdr_set_sample_rate.restype = c_int
_LIB.rtlsdr_set_freq_correction.argtypes = [c_void_p, c_int]
_LIB.rtlsdr_set_freq_correction.restype = c_int
_LIB.rtlsdr_set_tuner_gain_mode.argtypes = [c_void_p, c_int]
_LIB.rtlsdr_set_tuner_gain_mode.restype = c_int
_LIB.rtlsdr_set_tuner_gain.argtypes = [c_void_p, c_int]
_LIB.rtlsdr_set_tuner_gain.restype = c_int
_LIB.rtlsdr_reset_buffer.argtypes = [c_void_p]
_LIB.rtlsdr_reset_buffer.restype = c_int
_LIB.rtlsdr_read_sync.argtypes = [c_void_p, c_void_p, c_int, POINTER(c_int)]
_LIB.rtlsdr_read_sync.restype = c_int


class RtlSdr:
    def __init__(self, device_index: int = 0) -> None:
        self._dev = c_void_p()
        _check(_LIB.rtlsdr_open(byref(self._dev), c_uint32(device_index)), "rtlsdr_open")
        self._buffer_reset = False
        self._center_freq = 0
        self._sample_rate = 0
        self._freq_correction = 0
        self._gain: str | float = "auto"

    @property
    def center_freq(self) -> int:
        return self._center_freq

    @center_freq.setter
    def center_freq(self, value: float) -> None:
        hz = int(value)
        _check(_LIB.rtlsdr_set_center_freq(self._dev, c_uint32(hz)), "rtlsdr_set_center_freq")
        self._center_freq = hz
        self._buffer_reset = False

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value: float) -> None:
        rate = int(value)
        _check(_LIB.rtlsdr_set_sample_rate(self._dev, c_uint32(rate)), "rtlsdr_set_sample_rate")
        self._sample_rate = rate
        self._buffer_reset = False

    @property
    def freq_correction(self) -> int:
        return self._freq_correction

    @freq_correction.setter
    def freq_correction(self, value: int) -> None:
        ppm = int(value)
        if ppm == 0:
            self._freq_correction = 0
            return
        _check(_LIB.rtlsdr_set_freq_correction(self._dev, ppm), "rtlsdr_set_freq_correction")
        self._freq_correction = ppm
        self._buffer_reset = False

    @property
    def gain(self) -> str | float:
        return self._gain

    @gain.setter
    def gain(self, value: str | float) -> None:
        if value == "auto":
            _check(_LIB.rtlsdr_set_tuner_gain_mode(self._dev, 0), "rtlsdr_set_tuner_gain_mode")
            self._gain = "auto"
            return

        gain_db = float(value)
        _check(_LIB.rtlsdr_set_tuner_gain_mode(self._dev, 1), "rtlsdr_set_tuner_gain_mode")
        _check(_LIB.rtlsdr_set_tuner_gain(self._dev, int(round(gain_db * 10))), "rtlsdr_set_tuner_gain")
        self._gain = gain_db

    def read_samples(self, count: int) -> np.ndarray:
        if not self._buffer_reset:
            _check(_LIB.rtlsdr_reset_buffer(self._dev), "rtlsdr_reset_buffer")
            self._buffer_reset = True

        byte_count = max(2, int(count) * 2)
        buffer = (c_ubyte * byte_count)()
        bytes_read = c_int()
        _check(
            _LIB.rtlsdr_read_sync(self._dev, buffer, byte_count, byref(bytes_read)),
            "rtlsdr_read_sync",
        )

        raw = np.ctypeslib.as_array(buffer, shape=(bytes_read.value,)).astype(np.float32, copy=False)
        if raw.size < 2:
            return np.zeros(0, dtype=np.complex64)
        if raw.size % 2:
            raw = raw[:-1]

        i_samples = (raw[0::2] - 127.5) / 127.5
        q_samples = (raw[1::2] - 127.5) / 127.5
        return (i_samples + 1j * q_samples).astype(np.complex64)

    def close(self) -> None:
        if self._dev:
            _check(_LIB.rtlsdr_close(self._dev), "rtlsdr_close")
            self._dev = c_void_p()
