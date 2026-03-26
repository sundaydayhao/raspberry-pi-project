#!/usr/bin/env python3
"""
GPIO 基础测试
测试 Raspberry Pi GPIO 引脚的基本功能
"""

import time
import sys

# 尝试导入 GPIO 库
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    print("✅ RPi.GPIO 库加载成功")
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️  RPi.GPIO 未安装，使用模拟模式")
    print("   安装命令: pip3 install RPi.GPIO")

try:
    from gpiozero import LED, Button
    GPIOZERO_AVAILABLE = True
    print("✅ gpiozero 库加载成功")
except ImportError:
    GPIOZERO_AVAILABLE = False
    print("⚠️  gpiozero 未安装")
    print("   安装命令: pip3 install gpiozero")

# 测试引脚配置
TEST_LED_PIN = 18      # BCM 编号
TEST_BUTTON_PIN = 17   # BCM 编号

def test_gpio_output():
    """测试 GPIO 输出（LED 闪烁）"""
    if not GPIO_AVAILABLE:
        print("\n[模拟] GPIO 输出测试:")
        for i in range(3):
            print(f"  GPIO {TEST_LED_PIN} -> HIGH (LED 亮)")
            time.sleep(0.5)
            print(f"  GPIO {TEST_LED_PIN} -> LOW  (LED 灭)")
            time.sleep(0.5)
        return
    
    print(f"\n测试 GPIO 输出 (引脚 {TEST_LED_PIN})...")
    print("请在 GPIO18 引脚连接 LED（通过 330Ω 电阻接 GND）")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TEST_LED_PIN, GPIO.OUT)
    
    try:
        for i in range(5):
            GPIO.output(TEST_LED_PIN, GPIO.HIGH)
            print(f"  第{i+1}次: LED 亮")
            time.sleep(0.5)
            GPIO.output(TEST_LED_PIN, GPIO.LOW)
            print(f"  第{i+1}次: LED 灭")
            time.sleep(0.5)
        print("✅ GPIO 输出测试完成")
    finally:
        GPIO.cleanup()

def test_gpio_input():
    """测试 GPIO 输入（按钮检测）"""
    if not GPIO_AVAILABLE:
        print("\n[模拟] GPIO 输入测试:")
        print("  等待按钮按下... (模拟3秒后检测到)")
        time.sleep(3)
        print("  检测到按钮按下!")
        return
    
    print(f"\n测试 GPIO 输入 (引脚 {TEST_BUTTON_PIN})...")
    print("请在 GPIO17 引脚连接按钮（另一端接 GND）")
    print("等待按钮按下... (10秒超时)")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TEST_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    start_time = time.time()
    pressed = False
    
    try:
        while time.time() - start_time < 10:
            if GPIO.input(TEST_BUTTON_PIN) == GPIO.LOW:
                print("✅ 检测到按钮按下!")
                pressed = True
                time.sleep(0.2)  # 防抖
                break
            time.sleep(0.05)
        
        if not pressed:
            print("⏱️  超时，未检测到按钮按下")
    finally:
        GPIO.cleanup()

def test_pwm():
    """测试 PWM 输出"""
    if not GPIO_AVAILABLE:
        print("\n[模拟] PWM 测试:")
        for duty in [0, 25, 50, 75, 100]:
            print(f"  占空比: {duty}%")
            time.sleep(0.3)
        return
    
    print(f"\n测试 PWM 输出 (引脚 {TEST_LED_PIN})...")
    print("LED 亮度将从暗到亮再到暗变化")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TEST_LED_PIN, GPIO.OUT)
    
    pwm = GPIO.PWM(TEST_LED_PIN, 100)  # 100Hz
    pwm.start(0)
    
    try:
        # 渐亮
        print("  渐亮...")
        for duty in range(0, 101, 5):
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.05)
        
        # 渐灭
        print("  渐灭...")
        for duty in range(100, -1, -5):
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.05)
        
        print("✅ PWM 测试完成")
    finally:
        pwm.stop()
        GPIO.cleanup()

def check_gpio_permissions():
    """检查 GPIO 权限"""
    import os
    
    print("\n检查 GPIO 权限...")
    
    # 检查用户组
    try:
        result = os.popen('groups').read().strip()
        groups = result.split()
        
        if 'gpio' in groups:
            print("✅ 用户已在 gpio 组中")
        else:
            print("⚠️  用户不在 gpio 组中")
            print("   运行: sudo usermod -a -G gpio $USER")
            print("   然后重新登录")
        
        if 'i2c' in groups:
            print("✅ 用户已在 i2c 组中")
        
        if 'spi' in groups:
            print("✅ 用户已在 spi 组中")
            
    except Exception as e:
        print(f"检查失败: {e}")
    
    # 检查设备文件
    devices = ['/dev/gpiomem', '/dev/i2c-1', '/dev/spidev0.0']
    for dev in devices:
        if os.path.exists(dev):
            print(f"✅ {dev} 存在")
        else:
            print(f"⚠️  {dev} 不存在（可能未启用）")

def main():
    """主测试函数"""
    print("=" * 50)
    print("🔧 Raspberry Pi GPIO 测试工具")
    print("=" * 50)
    
    # 检查权限
    check_gpio_permissions()
    
    print("\n选择测试项目:")
    print("1. GPIO 输出测试 (LED 闪烁)")
    print("2. GPIO 输入测试 (按钮检测)")
    print("3. PWM 测试 (LED 渐变)")
    print("4. 全部测试")
    print("0. 退出")
    
    choice = input("\n请输入选项: ").strip()
    
    if choice == '1':
        test_gpio_output()
    elif choice == '2':
        test_gpio_input()
    elif choice == '3':
        test_pwm()
    elif choice == '4':
        test_gpio_output()
        test_gpio_input()
        test_pwm()
    elif choice == '0':
        print("退出")
        sys.exit(0)
    else:
        print("无效选项")

if __name__ == "__main__":
    main()