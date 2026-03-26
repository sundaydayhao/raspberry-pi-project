#!/usr/bin/env python3
"""
LCD1602 I2C 液晶显示屏
通过 I2C 接口控制 LCD 显示文字

硬件连接:
  VCC ── 5V
  GND ── GND
  SDA ── GPIO2 (SDA)
  SCL ── GPIO3 (SCL)

安装依赖:
  pip3 install RPLCD smbus2

查找 I2C 地址:
  sudo i2cdetect -y 1

学习要点:
  - I2C LCD 控制
  - 自定义字符
  - 滚动显示
"""

import time
import sys

try:
    from RPLCD.i2c import CharLCD
    LCD_AVAILABLE = True
except ImportError:
    LCD_AVAILABLE = False
    print("⚠️  未找到 RPLCD 库，使用模拟模式")
    print("   安装: pip3 install RPLCD smbus2")

LCD_ADDRESS = 0x27  # 常见地址: 0x27 或 0x3F
LCD_COLS = 16
LCD_ROWS = 2

class MockLCD:
    """模拟 LCD（用于测试）"""
    def __init__(self):
        self.display = [[' '] * LCD_COLS for _ in range(LCD_ROWS)]
        self.cursor_pos = (0, 0)
        self.backlight = True

    def write_string(self, text):
        row, col = self.cursor_pos
        for char in text:
            if char == '\n':
                row += 1
                col = 0
            elif col < LCD_COLS and row < LCD_ROWS:
                self.display[row][col] = char
                col += 1
        self.cursor_pos = (row, col)
        self._render()

    def cursor_pos_setter(self, pos):
        self.cursor_pos = pos

    def clear(self):
        self.display = [[' '] * LCD_COLS for _ in range(LCD_ROWS)]
        self.cursor_pos = (0, 0)
        self._render()

    def _render(self):
        print("\n┌" + "─" * LCD_COLS + "┐")
        for row in self.display:
            print("│" + "".join(row) + "│")
        print("└" + "─" * LCD_COLS + "┘")

    def close(self, clear=True):
        if clear:
            self.clear()

def create_lcd():
    """创建 LCD 实例"""
    if LCD_AVAILABLE:
        try:
            lcd = CharLCD(
                i2c_expander='PCF8574',
                address=LCD_ADDRESS,
                port=1,
                cols=LCD_COLS,
                rows=LCD_ROWS,
                dotsize=8
            )
            return lcd
        except Exception as e:
            print(f"LCD 初始化失败: {e}")
            print("使用模拟模式")
    return MockLCD()

def display_hello(lcd):
    """显示欢迎信息"""
    lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string("Hello, Pi!")
    lcd.cursor_pos = (1, 0)
    lcd.write_string("Learning Kit v1.0")
    time.sleep(3)

def display_time(lcd, duration=30):
    """显示实时时钟"""
    print(f"显示时钟 ({duration}秒)")
    end_time = time.time() + duration

    try:
        while time.time() < end_time:
            now = time.localtime()
            date_str = time.strftime("%Y-%m-%d", now)
            time_str = time.strftime("%H:%M:%S", now)

            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string(date_str)
            lcd.cursor_pos = (1, 0)
            lcd.write_string(time_str)
            time.sleep(1)
    except KeyboardInterrupt:
        pass

def scroll_text(lcd, text, row=0, delay=0.3):
    """滚动显示长文本"""
    if len(text) <= LCD_COLS:
        lcd.cursor_pos = (row, 0)
        lcd.write_string(text.ljust(LCD_COLS))
        return

    # 添加空格使文字从右侧滚入
    padded = ' ' * LCD_COLS + text + ' ' * LCD_COLS

    for i in range(len(padded) - LCD_COLS + 1):
        lcd.cursor_pos = (row, 0)
        lcd.write_string(padded[i:i + LCD_COLS])
        time.sleep(delay)

def display_sensor_data(lcd, temp, humidity):
    """显示传感器数据"""
    lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string(f"Temp: {temp:.1f}C")
    lcd.cursor_pos = (1, 0)
    lcd.write_string(f"Humi: {humidity:.1f}%")

def menu_demo(lcd):
    """菜单演示"""
    items = ["1.温度监控", "2.时钟显示", "3.系统信息", "4.传感器数据"]
    current = 0

    print("菜单演示 (按 Enter 切换，输入 'q' 退出)")

    while True:
        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string(f"> {items[current][:14]}")
        next_item = items[(current + 1) % len(items)]
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"  {next_item[:14]}")

        inp = input(f"\n当前: {items[current]} (Enter/q): ").strip()
        if inp.lower() == 'q':
            break
        current = (current + 1) % len(items)

def main():
    print("=" * 40)
    print("📺 LCD1602 I2C 显示屏")
    print("=" * 40)
    print(f"I2C 地址: 0x{LCD_ADDRESS:02X}")
    print()

    lcd = create_lcd()

    print("选择演示:")
    print("1. 欢迎信息")
    print("2. 实时时钟")
    print("3. 滚动文字")
    print("4. 菜单演示")

    choice = input("\n请选择 (1-4): ").strip()

    try:
        if choice == '1':
            display_hello(lcd)
        elif choice == '2':
            display_time(lcd)
        elif choice == '3':
            lcd.clear()
            scroll_text(lcd, "Raspberry Pi Learning Kit - 树莓派学习套件!", row=0)
            scroll_text(lcd, "Hello World! 你好世界!", row=1)
        elif choice == '4':
            menu_demo(lcd)
        else:
            display_hello(lcd)
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        lcd.clear()
        print("LCD 已清空")

if __name__ == "__main__":
    main()