#!/usr/bin/env python3
"""
树莓派 RTL-SDR ADS-B 接收与 HDMI 屏显示程序

实现方式：
1. 通过外部 ADS-B 解码器（优先 dump1090-fa / dump1090 / readsb）调用 RTL-SDR 采集 1090MHz 数据
2. 周期性读取 aircraft.json
3. 在 HDMI 屏上显示飞机列表、航班号、高度、速度、航向、距离等信息
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Optional

try:
    import pygame
except ImportError as exc:
    raise SystemExit("缺少 pygame 依赖，请先安装：pip install pygame") from exc


@dataclass
class AppConfig:
    json_path: str = "/run/dump1090-fa/aircraft.json"
    refresh_hz: int = 2
    screen_width: int = 800
    screen_height: int = 480
    fullscreen: bool = True
    dump1090_cmd: str = "auto"
    gain: str = "auto"
    device_index: int = 0
    interactive_rows: int = 12
    home_lat: Optional[float] = None
    home_lon: Optional[float] = None


class ADSBSource:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.process: Optional[subprocess.Popen[str]] = None
        self.started_cmd: Optional[list[str]] = None

    def _candidate_commands(self) -> list[list[str]]:
        json_dir = os.path.dirname(self.config.json_path)
        return [
            [
                "dump1090-fa",
                "--device-index",
                str(self.config.device_index),
                "--gain",
                str(self.config.gain),
                "--write-json",
                json_dir,
            ],
            [
                "dump1090",
                "--device-index",
                str(self.config.device_index),
                "--gain",
                str(self.config.gain),
                "--write-json",
                json_dir,
            ],
            [
                "readsb",
                "--device",
                f"type=rtlsdr,serial={self.config.device_index}",
                "--gain",
                str(self.config.gain),
                "--write-json",
                json_dir,
            ],
        ]

    def start(self) -> None:
        os.makedirs(os.path.dirname(self.config.json_path), exist_ok=True)

        if self.config.dump1090_cmd != "auto":
            cmd = self.config.dump1090_cmd.split()
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            self.started_cmd = cmd
            return

        for cmd in self._candidate_commands():
            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                self.started_cmd = cmd
                time.sleep(1.0)
                if self.process.poll() is None:
                    return
            except FileNotFoundError:
                continue

        raise RuntimeError(
            "未找到可用 ADS-B 解码器，请安装 dump1090-fa、dump1090 或 readsb"
        )

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None


class AircraftDataStore:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.aircraft: list[dict[str, Any]] = []
        self.last_update_text = "N/A"

    def load(self) -> None:
        try:
            with open(self.config.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.aircraft = []
            self.last_update_text = "waiting json..."
            return
        except json.JSONDecodeError:
            self.aircraft = []
            self.last_update_text = "json error"
            return

        now = data.get("now")
        if isinstance(now, (int, float)):
            age = max(0.0, time.time() - float(now))
            self.last_update_text = f"{age:.1f}s ago"
        else:
            self.last_update_text = "unknown"

        rows = []
        for ac in data.get("aircraft", []):
            hex_id = ac.get("hex")
            if not hex_id:
                continue
            rows.append(ac)

        rows.sort(
            key=lambda item: (
                item.get("flight") or "",
                -(item.get("seen_pos") is None),
                -(item.get("alt_baro") is None),
            )
        )
        self.aircraft = rows

    def top_rows(self, limit: int) -> list[dict[str, Any]]:
        return self.aircraft[:limit]


class HDMIRenderer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        pygame.init()
        flags = pygame.FULLSCREEN if config.fullscreen else 0
        self.screen = pygame.display.set_mode((config.screen_width, config.screen_height), flags)
        pygame.display.set_caption("RTL-SDR ADS-B Monitor")
        self.font_title = pygame.font.SysFont("consolas", 28)
        self.font_head = pygame.font.SysFont("consolas", 20)
        self.font_row = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 16)

    def poll_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                return False
        return True

    def render(self, store: AircraftDataStore, started_cmd: Optional[list[str]]) -> None:
        width = self.config.screen_width
        height = self.config.screen_height
        self.screen.fill((0, 0, 0))

        title = self.font_title.render("RTL-SDR ADS-B Monitor", True, (0, 255, 120))
        self.screen.blit(title, (14, 10))

        cmd_text = "Decoder: " + (" ".join(started_cmd) if started_cmd else "not started")
        info1 = self.font_small.render(cmd_text, True, (180, 180, 180))
        info2 = self.font_small.render(
            f"JSON: {self.config.json_path}    Updated: {store.last_update_text}    Aircraft: {len(store.aircraft)}",
            True,
            (220, 220, 0),
        )
        self.screen.blit(info1, (14, 48))
        self.screen.blit(info2, (14, 68))

        header_y = 110
        columns = [
            ("HEX", 14),
            ("FLIGHT", 90),
            ("ALT", 210),
            ("SPD", 300),
            ("HDG", 380),
            ("LAT", 460),
            ("LON", 560),
            ("SEEN", 690),
        ]
        for name, x in columns:
            txt = self.font_head.render(name, True, (0, 200, 255))
            self.screen.blit(txt, (x, header_y))

        pygame.draw.line(self.screen, (60, 60, 60), (14, header_y + 28), (width - 14, header_y + 28), 1)

        rows = store.top_rows(self.config.interactive_rows)
        y = header_y + 38
        for ac in rows:
            hex_id = str(ac.get("hex", "")).upper()
            flight = str(ac.get("flight", "")).strip() or "-"
            alt = self._fmt_int(ac.get("alt_baro") or ac.get("alt_geom"))
            spd = self._fmt_int(ac.get("gs"))
            hdg = self._fmt_int(ac.get("track"))
            lat = self._fmt_float(ac.get("lat"))
            lon = self._fmt_float(ac.get("lon"))
            seen = self._fmt_float(ac.get("seen"))

            values = [
                (hex_id, 14),
                (flight, 90),
                (alt, 210),
                (spd, 300),
                (hdg, 380),
                (lat, 460),
                (lon, 560),
                (seen, 690),
            ]
            for text, x in values:
                surf = self.font_row.render(text, True, (230, 230, 230))
                self.screen.blit(surf, (x, y))
            y += 26

        footer = self.font_small.render("Q / ESC 退出", True, (150, 150, 150))
        self.screen.blit(footer, (14, height - 24))
        pygame.display.flip()

    @staticmethod
    def _fmt_int(value: Any) -> str:
        if value is None:
            return "-"
        try:
            return str(int(float(value)))
        except (TypeError, ValueError):
            return "-"

    @staticmethod
    def _fmt_float(value: Any) -> str:
        if value is None:
            return "-"
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return "-"

    def close(self) -> None:
        pygame.quit()


class ADSBMonitorApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.source = ADSBSource(config)
        self.store = AircraftDataStore(config)
        self.renderer = HDMIRenderer(config)
        self.running = False

    def run(self) -> None:
        self.source.start()
        self.running = True
        interval = 1.0 / max(self.config.refresh_hz, 1)

        try:
            while self.running:
                if not self.renderer.poll_events():
                    self.stop()
                    continue

                self.store.load()
                self.renderer.render(self.store, self.source.started_cmd)
                time.sleep(interval)
        finally:
            self.source.stop()
            self.renderer.close()

    def stop(self) -> None:
        self.running = False


def parse_args() -> AppConfig:
    parser = argparse.ArgumentParser(description="RTL-SDR ADS-B HDMI Monitor")
    parser.add_argument("--json-path", type=str, default="/run/dump1090-fa/aircraft.json", help="aircraft.json 路径")
    parser.add_argument("--refresh-hz", type=int, default=2, help="刷新频率")
    parser.add_argument("--width", type=int, default=800, help="HDMI 屏宽度")
    parser.add_argument("--height", type=int, default=480, help="HDMI 屏高度")
    parser.add_argument("--windowed", action="store_true", help="窗口模式")
    parser.add_argument("--dump1090-cmd", type=str, default="auto", help="自定义 dump1090/readsb 启动命令")
    parser.add_argument("--gain", type=str, default="auto", help="RTL 增益")
    parser.add_argument("--device-index", type=int, default=0, help="RTL-SDR 设备编号")
    parser.add_argument("--rows", type=int, default=12, help="显示飞机条数")
    args = parser.parse_args()

    return AppConfig(
        json_path=args.json_path,
        refresh_hz=args.refresh_hz,
        screen_width=args.width,
        screen_height=args.height,
        fullscreen=not args.windowed,
        dump1090_cmd=args.dump1090_cmd,
        gain=args.gain,
        device_index=args.device_index,
        interactive_rows=args.rows,
    )


def install_signal_handlers(app: ADSBMonitorApp) -> None:
    def _handler(signum, frame) -> None:  # type: ignore[unused-argument]
        app.stop()

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def main() -> int:
    config = parse_args()
    app = ADSBMonitorApp(config)
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