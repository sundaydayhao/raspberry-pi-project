#!/usr/bin/env python3
"""
树莓派 RTL-SDR FM 接收与 HDMI 屏显示程序

功能：
1. 使用 RTL-SDR 采集 IQ 数据
2. 对宽带 FM 广播频段进行频谱分析
3. 在 HDMI 屏上显示：
   - 当前中心频率
   - 采样率
   - 增益
   - 峰值频点
   - 实时频谱
   - 瀑布图

说明：
- 当前重点实现“接收 + FM 信息显示 + 瀑布图显示”
- 显示设备改为 HDMI 屏，不再依赖 SPI LCD 驱动
- 默认使用 pygame 创建全屏窗口输出到 HDMI
"""

from __future__ import annotations

import argparse
import ctypes
import os
import signal
import sys
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

class _MissingRtlSdrSymbol:
    def __init__(self, name: str) -> None:
        self.__name__ = name
        self.argtypes = []
        self.restype = ctypes.c_int

    def __call__(self, *args: object) -> int:
        return 0


def _load_rtlsdr() -> type:
    try:
        from rtlsdr import RtlSdr as imported_rtlsdr
        return imported_rtlsdr
    except ImportError as exc:
        raise SystemExit(
            "缂哄皯 pyrtlsdr 渚濊禆锛岃鍏堝畨瑁咃細pip install pyrtlsdr numpy pillow pygame"
        ) from exc
    except AttributeError as exc:
        if "rtlsdr_set_dithering" not in str(exc):
            raise SystemExit(f"鍔犺浇 pyrtlsdr 澶辫触: {exc}") from exc

        original_getattr = ctypes.CDLL.__getattr__

        def _compat_getattr(self: ctypes.CDLL, name: str):
            try:
                return original_getattr(self, name)
            except AttributeError:
                library_name = getattr(self, "_name", "")
                if name == "rtlsdr_set_dithering" and isinstance(library_name, str) and "librtlsdr" in library_name:
                    return _MissingRtlSdrSymbol(name)
                raise

        ctypes.CDLL.__getattr__ = _compat_getattr
        for module_name in list(sys.modules):
            if module_name == "rtlsdr" or module_name.startswith("rtlsdr."):
                sys.modules.pop(module_name, None)

        try:
            print(
                "[WARN] librtlsdr 缂哄皯 rtlsdr_set_dithering锛屽凡鍚敤鍏煎瀵煎叆銆?",
                file=sys.stderr,
            )
            from rtlsdr import RtlSdr as imported_rtlsdr
            return imported_rtlsdr
        except Exception as retry_exc:
            raise SystemExit(
                "绯荤粺 librtlsdr 杩囨棫锛屽苟涓旇嚜鍔ㄥ吋瀹瑰け璐ャ€?璇峰崌绾?librtlsdr锛屾垨闄嶇骇 pyrtlsdr銆?"
            ) from retry_exc
        finally:
            ctypes.CDLL.__getattr__ = original_getattr

try:
    import pygame
except ImportError as exc:
    raise SystemExit("缺少 pygame 依赖，请先安装：pip install pygame") from exc

try:
    RtlSdr = _load_rtlsdr()
except ImportError as exc:
    raise SystemExit(
        "缺少 pyrtlsdr 依赖，请先安装：pip install pyrtlsdr numpy pillow pygame"
    ) from exc


@dataclass
class AppConfig:
    center_freq_mhz: float = 98.0
    sample_rate: float = 2.4e6
    gain: str = "auto"
    fft_size: int = 1024
    frame_rate: int = 20
    screen_width: int = 800
    screen_height: int = 480
    ppm: int = 0
    device_index: int = 0
    fullscreen: bool = True
    save_frames: bool = False
    output_dir: str = "frames"


class WaterfallBuffer:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.buffer = np.zeros((height, width), dtype=np.uint8)

    def push(self, row: np.ndarray) -> None:
        if row.shape[0] != self.width:
            raise ValueError(f"row width {row.shape[0]} != expected {self.width}")
        self.buffer[:-1] = self.buffer[1:]
        self.buffer[-1] = row

    def as_image(self) -> Image.Image:
        rgb = self._apply_colormap(self.buffer)
        return Image.fromarray(rgb, mode="RGB")

    @staticmethod
    def _apply_colormap(gray: np.ndarray) -> np.ndarray:
        x = gray.astype(np.float32) / 255.0
        r = np.clip(4 * x - 1.5, 0, 1)
        g = np.clip(1.0 - (4 * np.abs(x - 0.5) - 1.0), 0, 1)
        b = np.clip(1.5 - 4 * x, 0, 1)
        rgb = np.stack([r, g, b], axis=-1)
        return (rgb * 255).astype(np.uint8)


class SpectrumAnalyzer:
    def __init__(self, fft_size: int) -> None:
        self.fft_size = fft_size
        self.window = np.hanning(fft_size)

    def compute_power_spectrum(self, samples: np.ndarray) -> np.ndarray:
        if len(samples) < self.fft_size:
            padded = np.zeros(self.fft_size, dtype=np.complex64)
            padded[: len(samples)] = samples
            samples = padded
        else:
            samples = samples[: self.fft_size]

        windowed = samples * self.window
        spectrum = np.fft.fftshift(np.fft.fft(windowed))
        power = 20 * np.log10(np.abs(spectrum) + 1e-12)
        return power.astype(np.float32)

    @staticmethod
    def normalize(power: np.ndarray, floor_db: float = -90.0, ceil_db: float = -10.0) -> np.ndarray:
        clipped = np.clip(power, floor_db, ceil_db)
        norm = (clipped - floor_db) / (ceil_db - floor_db)
        return (norm * 255).astype(np.uint8)


class HDMIRenderer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        pygame.init()
        flags = pygame.FULLSCREEN if config.fullscreen else 0
        self.screen = pygame.display.set_mode((config.screen_width, config.screen_height), flags)
        pygame.display.set_caption("RTL-SDR FM Monitor")
        self.font_small = ImageFont.load_default()
        self.font_large = ImageFont.load_default()

    def poll_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                return False
        return True

    def display(self, image: Image.Image) -> None:
        mode = image.mode
        size = image.size
        data = image.tobytes()
        surface = pygame.image.fromstring(data, size, mode)
        self.screen.blit(surface, (0, 0))
        pygame.display.flip()

        if self.config.save_frames:
            os.makedirs(self.config.output_dir, exist_ok=True)
            image.save(os.path.join(self.config.output_dir, "latest.png"))

    def close(self) -> None:
        pygame.quit()


class FMMonitorApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.sdr: Optional[RtlSdr] = None
        self.running = False
        self.spectrum = SpectrumAnalyzer(config.fft_size)
        self.header_height = 72
        self.spectrum_height = 120
        self.footer_height = 24
        self.waterfall_height = max(
            80, config.screen_height - self.header_height - self.spectrum_height - self.footer_height - 12
        )
        self.waterfall = WaterfallBuffer(config.screen_width, self.waterfall_height)
        self.renderer = HDMIRenderer(config)
        self.latest_power = np.zeros(config.fft_size, dtype=np.float32)
        self.last_peak_freq_mhz = config.center_freq_mhz
        self.last_peak_db = -120.0
        self.last_frame_time = 0.0

    def setup_sdr(self) -> None:
        self.sdr = RtlSdr(self.config.device_index)
        self.sdr.center_freq = self.config.center_freq_mhz * 1e6
        self.sdr.sample_rate = self.config.sample_rate
        if self.config.ppm:
            try:
                self.sdr.freq_correction = self.config.ppm
            except Exception as exc:
                print(
                    f"[WARN] Failed to apply frequency correction ({self.config.ppm} ppm): {exc}",
                    file=sys.stderr,
                )
        if self.config.gain == "auto":
            self.sdr.gain = "auto"
        else:
            self.sdr.gain = float(self.config.gain)

    def shutdown_sdr(self) -> None:
        if self.sdr is not None:
            try:
                self.sdr.close()
            except Exception:
                pass
            self.sdr = None
        self.renderer.close()

    def read_samples(self) -> np.ndarray:
        assert self.sdr is not None
        count = max(self.config.fft_size * 4, 16384)
        samples = self.sdr.read_samples(count)
        return np.asarray(samples, dtype=np.complex64)

    def update_metrics(self, power: np.ndarray) -> None:
        self.latest_power = power
        peak_idx = int(np.argmax(power))
        self.last_peak_db = float(power[peak_idx])

        freq_span = self.config.sample_rate / 1e6
        bin_ratio = peak_idx / max(len(power) - 1, 1)
        offset_mhz = (bin_ratio - 0.5) * freq_span
        self.last_peak_freq_mhz = self.config.center_freq_mhz + offset_mhz

    def build_spectrum_line(self, normalized: np.ndarray, width: int, height: int) -> list[Tuple[int, int]]:
        x_src = np.linspace(0, len(normalized) - 1, width)
        resized = np.interp(x_src, np.arange(len(normalized)), normalized)
        points = []
        for x, value in enumerate(resized):
            y = int((1.0 - value / 255.0) * (height - 1))
            points.append((x, y))
        return points

    def compose_frame(self) -> Image.Image:
        width = self.config.screen_width
        height = self.config.screen_height
        image = Image.new("RGB", (width, height), "black")
        draw = ImageDraw.Draw(image)

        spectrum_top = self.header_height
        waterfall_top = spectrum_top + self.spectrum_height + 6

        draw.rectangle((0, 0, width - 1, height - 1), outline=(50, 50, 50))

        draw.text((10, 8), "RTL-SDR FM Monitor", font=self.renderer.font_large, fill=(0, 255, 120))
        draw.text(
            (10, 26),
            f"Center: {self.config.center_freq_mhz:.1f} MHz    SampleRate: {self.config.sample_rate/1e6:.2f} Msps",
            font=self.renderer.font_small,
            fill=(220, 220, 220),
        )
        draw.text(
            (10, 44),
            f"Gain: {self.config.gain}    Peak: {self.last_peak_freq_mhz:.2f} MHz / {self.last_peak_db:.1f} dB",
            font=self.renderer.font_small,
            fill=(255, 220, 0),
        )

        normalized = self.spectrum.normalize(self.latest_power)
        spectrum_points = self.build_spectrum_line(normalized, width - 20, self.spectrum_height)
        translated_points = [(x + 10, y + spectrum_top) for x, y in spectrum_points]
        draw.rectangle(
            (8, spectrum_top - 2, width - 8, spectrum_top + self.spectrum_height + 2),
            outline=(70, 70, 70),
        )
        if len(translated_points) > 1:
            draw.line(translated_points, fill=(0, 255, 255), width=2)

        wf_height = height - waterfall_top - self.footer_height
        wf_image = self.waterfall.as_image().resize((width - 20, wf_height))
        image.paste(wf_image, (10, waterfall_top))
        draw.rectangle((8, waterfall_top - 2, width - 8, waterfall_top + wf_height + 2), outline=(70, 70, 70))
        draw.text((10, height - 20), "Q / ESC 退出", font=self.renderer.font_small, fill=(180, 180, 180))
        return image

    def run(self) -> None:
        self.setup_sdr()
        self.running = True
        frame_interval = 1.0 / max(self.config.frame_rate, 1)

        try:
            while self.running:
                if not self.renderer.poll_events():
                    self.stop()
                    continue

                now = time.time()
                if now - self.last_frame_time < frame_interval:
                    time.sleep(0.001)
                    continue

                samples = self.read_samples()
                power = self.spectrum.compute_power_spectrum(samples)
                self.update_metrics(power)

                normalized = self.spectrum.normalize(power)
                resized = np.interp(
                    np.linspace(0, len(normalized) - 1, self.config.screen_width),
                    np.arange(len(normalized)),
                    normalized,
                ).astype(np.uint8)
                self.waterfall.push(resized)

                frame = self.compose_frame()
                self.renderer.display(frame)
                self.last_frame_time = now
        finally:
            self.shutdown_sdr()

    def stop(self) -> None:
        self.running = False


def parse_args() -> AppConfig:
    parser = argparse.ArgumentParser(description="RTL-SDR FM HDMI Monitor")
    parser.add_argument("--freq", type=float, default=98.0, help="中心频率 MHz，例如 98.0")
    parser.add_argument("--sample-rate", type=float, default=2.4e6, help="采样率，默认 2.4e6")
    parser.add_argument("--gain", type=str, default="auto", help="增益，默认 auto")
    parser.add_argument("--fft-size", type=int, default=1024, help="FFT 点数")
    parser.add_argument("--frame-rate", type=int, default=20, help="屏幕刷新帧率")
    parser.add_argument("--width", type=int, default=800, help="HDMI 屏宽度")
    parser.add_argument("--height", type=int, default=480, help="HDMI 屏高度")
    parser.add_argument("--ppm", type=int, default=0, help="频偏校正")
    parser.add_argument("--device-index", type=int, default=0, help="RTL-SDR 设备编号")
    parser.add_argument("--windowed", action="store_true", help="窗口模式运行，而不是全屏")
    parser.add_argument("--save-frames", action="store_true", help="保存当前帧到本地")
    parser.add_argument("--output-dir", type=str, default="frames", help="保存帧目录")
    args = parser.parse_args()

    return AppConfig(
        center_freq_mhz=args.freq,
        sample_rate=args.sample_rate,
        gain=args.gain,
        fft_size=args.fft_size,
        frame_rate=args.frame_rate,
        screen_width=args.width,
        screen_height=args.height,
        ppm=args.ppm,
        device_index=args.device_index,
        fullscreen=not args.windowed,
        save_frames=args.save_frames,
        output_dir=args.output_dir,
    )


def install_signal_handlers(app: FMMonitorApp) -> None:
    def _handler(signum, frame) -> None:  # type: ignore[unused-argument]
        app.stop()

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def main() -> int:
    config = parse_args()
    app = FMMonitorApp(config)
    install_signal_handlers(app)

    try:
        app.run()
    except KeyboardInterrupt:
        app.stop()
    except Exception as exc:
        print(f"[ERROR] 运行失败: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
