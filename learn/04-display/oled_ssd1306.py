#!/usr/bin/env python3
"""
OLED SSD1306 显示屏 (128x64)
通过 I2C 接口显示图形和文字

硬件连接:
  VCC ── 3.3V
  GND ── GND
  SDA ── GPIO2 (SDA)
  SCL ── GPIO3 (SCL)

安装依赖:
  pip3 install adafruit-circuitpython-ssd1306 Pillow

学习要点:
  - OLED 图形显示
  - PIL/Pillow 图像处理
  - 自定义图形绘制
"""

import time
import sys
import math

try:
    import board
    import busio
    import adafruit_ssd1306
    from PIL import Image, ImageDraw, ImageFont
    OLED_AVAILABLE = True
    print("✅ OLED 库加载成功")
except ImportError:
    OLED_AVAILABLE = False
    print("⚠️  未找到 OLED 库，使用模拟模式")
    print("   安装: pip3 install adafruit-circuitpython-ssd1306 Pillow")

WIDTH = 128
HEIGHT = 64

class MockOLED:
    """模拟 OLED（用于测试）"""
    def __init__(self):
        self.image = None

    def show_image(self, image):
        print("[OLED 模拟] 显示图像")

    def fill(self, color):
        pass

    def show(self):
        pass

def create_oled():
    """创建 OLED 实例"""
    if OLED_AVAILABLE:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)
            oled.fill(0)
            oled.show()
            print("✅ OLED 初始化成功")
            return oled
        except Exception as e:
            print(f"OLED 初始化失败: {e}")
    return None

def draw_text(oled, text_lines, font_size=12):
    """在 OLED 上显示文字"""
    if not OLED_AVAILABLE or oled is None:
        print("[OLED 模拟] 显示文字:")
        for line in text_lines:
            print(f"  {line}")
        return

    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    y = 0
    for line in text_lines:
        draw.text((0, y), line, font=font, fill=255)
        y += font_size + 2

    oled.image(image)
    oled.show()

def draw_clock(oled):
    """绘制模拟时钟"""
    if not OLED_AVAILABLE or oled is None:
        print("[OLED 模拟] 显示时钟")
        return

    cx, cy = 32, 32  # 时钟中心
    r = 28  # 半径

    print("显示模拟时钟 (Ctrl+C 退出)")
    try:
        while True:
            image = Image.new("1", (WIDTH, HEIGHT))
            draw = ImageDraw.Draw(image)

            # 绘制表盘
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=255)

            # 绘制刻度
            for i in range(12):
                angle = math.radians(i * 30 - 90)
                x1 = cx + int((r-3) * math.cos(angle))
                y1 = cy + int((r-3) * math.sin(angle))
                x2 = cx + int(r * math.cos(angle))
                y2 = cy + int(r * math.sin(angle))
                draw.line([x1, y1, x2, y2], fill=255)

            # 获取当前时间
            now = time.localtime()
            h, m, s = now.tm_hour % 12, now.tm_min, now.tm_sec

            # 秒针
            angle = math.radians(s * 6 - 90)
            draw.line([cx, cy,
                       cx + int((r-2) * math.cos(angle)),
                       cy + int((r-2) * math.sin(angle))], fill=255)

            # 分针
            angle = math.radians((m + s/60) * 6 - 90)
            draw.line([cx, cy,
                       cx + int((r-6) * math.cos(angle)),
                       cy + int((r-6) * math.sin(angle))], fill=255, width=2)

            # 时针
            angle = math.radians((h + m/60) * 30 - 90)
            draw.line([cx, cy,
                       cx + int((r-12) * math.cos(angle)),
                       cy + int((r-12) * math.sin(angle))], fill=255, width=3)

            # 数字时间
            time_str = time.strftime("%H:%M:%S")
            draw.text((70, 10), time_str, fill=255)
            draw.text((70, 25), time.strftime("%m/%d"), fill=255)

            oled.image(image)
            oled.show()
            time.sleep(1)

    except KeyboardInterrupt:
        pass

def draw_bar_chart(oled, values, labels=None):
    """绘制柱状图"""
    if not OLED_AVAILABLE or oled is None:
        print("[OLED 模拟] 显示柱状图:", values)
        return

    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    max_val = max(values) if values else 1
    bar_width = WIDTH // len(values) - 2
    chart_height = HEIGHT - 15

    for i, val in enumerate(values):
        bar_height = int(val / max_val * chart_height)
        x = i * (bar_width + 2) + 1
        y = chart_height - bar_height

        draw.rectangle([x, y, x + bar_width, chart_height], fill=255)

        if labels and i < len(labels):
            draw.text((x, chart_height + 2), labels[i][:2], fill=255)

    oled.image(image)
    oled.show()

def system_monitor(oled):
    """系统监控显示"""
    import subprocess

    print("系统监控模式 (Ctrl+C 退出)")

    try:
        while True:
            # 获取系统信息
            try:
                result = subprocess.run(['vcgencmd', 'measure_temp'],
                                        capture_output=True, text=True)
                temp = result.stdout.replace('temp=', '').replace("'C\n", '')
            except Exception:
                temp = "N/A"

            try:
                with open('/proc/loadavg') as f:
                    load = f.read().split()[0]
            except Exception:
                load = "N/A"

            lines = [
                "System Monitor",
                f"CPU Temp: {temp}C",
                f"Load: {load}",
                time.strftime("%H:%M:%S"),
            ]
            draw_text(oled, lines, font_size=11)
            time.sleep(2)

    except KeyboardInterrupt:
        pass

def main():
    print("=" * 40)
    print("📺 OLED SSD1306 显示屏")
    print("=" * 40)

    oled = create_oled()

    print("\n选择演示:")
    print("1. 显示文字")
    print("2. 模拟时钟")
    print("3. 柱状图")
    print("4. 系统监控")

    choice = input("\n请选择 (1-4): ").strip()

    try:
        if choice == '1':
            draw_text(oled, [
                "Hello, OLED!",
                "Raspberry Pi",
                "Learning Kit",
                time.strftime("%H:%M:%S")
            ])
            time.sleep(5)
        elif choice == '2':
            draw_clock(oled)
        elif choice == '3':
            import random
            values = [random.randint(10, 100) for _ in range(8)]
            labels = [str(i) for i in range(8)]
            draw_bar_chart(oled, values, labels)
            time.sleep(5)
        elif choice == '4':
            system_monitor(oled)
        else:
            draw_text(oled, ["Hello, OLED!"])
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        if oled and OLED_AVAILABLE:
            oled.fill(0)
            oled.show()
        print("OLED 已清空")

if __name__ == "__main__":
    main()