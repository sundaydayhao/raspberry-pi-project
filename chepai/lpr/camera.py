from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


class CameraStream:
    def __init__(
        self,
        engine: str = "auto",
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
    ) -> None:
        self.engine = engine
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self._opencv_capture: Optional[cv2.VideoCapture] = None
        self._picamera2 = None
        self.active_engine: Optional[str] = None

    def open(self) -> None:
        if self.engine in ("auto", "picamera2"):
            try:
                self._open_picamera2()
                self.active_engine = "picamera2"
                return
            except Exception:
                if self.engine == "picamera2":
                    raise

        self._open_opencv()
        self.active_engine = "opencv"

    def read(self) -> np.ndarray:
        if self.active_engine == "picamera2":
            frame = self._picamera2.capture_array()
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        if self._opencv_capture is None:
            raise RuntimeError("camera is not open")

        ok, frame = self._opencv_capture.read()
        if not ok or frame is None:
            raise RuntimeError("failed to read frame from camera")
        return frame

    def close(self) -> None:
        if self._opencv_capture is not None:
            self._opencv_capture.release()
            self._opencv_capture = None
        if self._picamera2 is not None:
            self._picamera2.stop()
            self._picamera2.close()
            self._picamera2 = None
        self.active_engine = None

    def _open_opencv(self) -> None:
        capture = cv2.VideoCapture(self.camera_index)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        capture.set(cv2.CAP_PROP_FPS, 30)
        if not capture.isOpened():
            raise RuntimeError("failed to open camera with OpenCV")
        self._opencv_capture = capture

    def _open_picamera2(self) -> None:
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_preview_configuration(
            main={"size": (self.width, self.height)}
        )
        camera.configure(config)
        camera.start()
        self._picamera2 = camera
