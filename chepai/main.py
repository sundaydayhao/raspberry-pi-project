#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lightweight license plate recognition for Raspberry Pi 3B+."
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--image", help="Recognize a single image file.")
    input_group.add_argument(
        "--camera", action="store_true", help="Recognize from a live camera stream."
    )

    parser.add_argument(
        "--camera-engine",
        default="auto",
        choices=("auto", "opencv", "picamera2"),
        help="Camera backend for live recognition.",
    )
    parser.add_argument(
        "--camera-index", type=int, default=0, help="OpenCV camera device index."
    )
    parser.add_argument("--width", type=int, default=640, help="Capture width.")
    parser.add_argument("--height", type=int, default=480, help="Capture height.")
    parser.add_argument(
        "--every-n-frames",
        type=int,
        default=3,
        help="Run recognition every N frames to reduce Pi CPU usage.",
    )
    parser.add_argument(
        "--top-k", type=int, default=3, help="Maximum number of plates to keep."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Exit after the first successful recognition.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display a preview window with recognition overlays.",
    )
    parser.add_argument(
        "--output",
        help="Write annotated image to a file. In camera mode, saves the last frame.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print results in JSON format.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        import cv2  # noqa: F401
        from lpr.camera import CameraStream  # noqa: F401
        from lpr.pipeline import LicensePlateRecognizer
    except ModuleNotFoundError as exc:
        print(
            "missing runtime dependency: "
            f"{exc.name}. Run 'sudo bash install.sh' first."
        )
        return 1

    recognizer = LicensePlateRecognizer()

    if args.image:
        return run_image_mode(recognizer, args)
    return run_camera_mode(recognizer, args)


def run_image_mode(recognizer: Any, args: argparse.Namespace) -> int:
    import cv2

    image_path = Path(args.image)
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"failed to read image: {image_path}")
        return 1

    results = recognizer.recognize(image, top_k=args.top_k)
    emit_image_results(image_path, results, args.json)

    annotated = recognizer.draw_results(image, results)
    if args.output:
        cv2.imwrite(args.output, annotated)
        if not args.json:
            print(f"annotated image saved: {args.output}")

    if args.show:
        cv2.imshow("plate-recognition", annotated)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return 0 if results else 2


def run_camera_mode(recognizer: Any, args: argparse.Namespace) -> int:
    import cv2
    from lpr.camera import CameraStream

    camera = CameraStream(
        engine=args.camera_engine,
        camera_index=args.camera_index,
        width=args.width,
        height=args.height,
    )
    seen_texts = set()
    last_results: List[Any] = []
    last_frame = None

    try:
        camera.open()
        frame_index = 0
        while True:
            frame = camera.read()
            last_frame = frame.copy()
            frame_index += 1

            if frame_index % max(args.every_n_frames, 1) == 0:
                last_results = recognizer.recognize(frame, top_k=args.top_k)
                fresh_results = [item for item in last_results if item.text not in seen_texts]
                if fresh_results:
                    emit_results(fresh_results, args.json)
                    seen_texts.update(item.text for item in fresh_results)
                    if args.once:
                        if args.output:
                            annotated = recognizer.draw_results(frame, last_results)
                            cv2.imwrite(args.output, annotated)
                        return 0

            preview = recognizer.draw_results(frame, last_results)
            if args.show:
                cv2.imshow("plate-recognition", preview)
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    break
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        if args.output and last_frame is not None:
            annotated = recognizer.draw_results(last_frame, last_results)
            cv2.imwrite(args.output, annotated)
        camera.close()
        if args.show:
            cv2.destroyAllWindows()

    return 0 if seen_texts else 2


def emit_results(results: List[Any], as_json: bool) -> None:
    if as_json:
        payload = [
            {
                "text": item.text,
                "score": round(item.score, 4),
                "ocr_confidence": round(item.ocr_confidence, 2),
                "bbox": list(item.bbox),
                "source": item.source,
            }
            for item in results
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if not results:
        print("no license plate recognized")
        return

    for item in results:
        print(
            f"plate={item.text} score={item.score:.2f} "
            f"ocr_conf={item.ocr_confidence:.1f} source={item.source}"
        )


def emit_image_results(image_path: Path, results: List[Any], as_json: bool) -> None:
    if as_json:
        emit_results(results, as_json=True)
        return

    print(f"image: {image_path}")
    print(f"recognized plates: {len(results)}")
    if not results:
        print("no license plate recognized")
        return

    for index, item in enumerate(results, start=1):
        print(
            f"[{index}] plate={item.text} score={item.score:.2f} "
            f"ocr_conf={item.ocr_confidence:.1f} source={item.source}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
