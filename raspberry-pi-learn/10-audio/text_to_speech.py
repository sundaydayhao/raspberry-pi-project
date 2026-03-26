#!/usr/bin/env python3
"""
文字转语音 (TTS)
将文字转换为语音输出

安装依赖:
  pip3 install pyttsx3
  sudo apt install espeak espeak-data libespeak1

或使用 Google TTS:
  pip3 install gtts
  sudo apt install mpg123

学习要点:
  - TTS 引擎使用
  - 语音参数调整
  - 中英文语音合成
"""

import os
import sys
import time

# 尝试导入 TTS 库
TTS_ENGINE = None

try:
    import pyttsx3
    TTS_ENGINE = 'pyttsx3'
    print("使用 pyttsx3 引擎")
except ImportError:
    pass

if TTS_ENGINE is None:
    try:
        from gtts import gTTS
        TTS_ENGINE = 'gtts'
        print("使用 gTTS 引擎")
    except ImportError:
        pass

if TTS_ENGINE is None:
    print("未找到 TTS 库，使用系统 espeak")
    TTS_ENGINE = 'espeak'

def speak_pyttsx3(text, lang='zh', rate=150, volume=1.0):
    """使用 pyttsx3 朗读"""
    engine = pyttsx3.init()
    engine.setProperty('rate', rate)
    engine.setProperty('volume', volume)

    # 设置中文语音
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break

    engine.say(text)
    engine.runAndWait()

def speak_gtts(text, lang='zh-cn', slow=False):
    """使用 gTTS 朗读（需要网络）"""
    tts = gTTS(text=text, lang=lang, slow=slow)
    filename = '/tmp/tts_output.mp3'
    tts.save(filename)

    # 播放音频
    if os.system('which mpg123 > /dev/null 2>&1') == 0:
        os.system(f'mpg123 -q {filename}')
    elif os.system('which mpg321 > /dev/null 2>&1') == 0:
        os.system(f'mpg321 -q {filename}')
    else:
        os.system(f'omxplayer {filename}')

    os.remove(filename)

def speak_espeak(text, lang='zh', speed=150, pitch=50):
    """使用 espeak 朗读"""
    cmd = f'espeak -v {lang} -s {speed} -p {pitch} "{text}"'
    os.system(cmd)

def speak(text, lang='zh'):
    """统一的朗读接口"""
    print(f"  朗读: {text}")

    if TTS_ENGINE == 'pyttsx3':
        speak_pyttsx3(text)
    elif TTS_ENGINE == 'gtts':
        speak_gtts(text, lang='zh-cn')
    elif TTS_ENGINE == 'espeak':
        speak_espeak(text)

def demo_tts():
    """TTS 演示"""
    texts = [
        ("你好，我是树莓派！", "zh"),
        ("Hello, I am Raspberry Pi!", "en"),
        ("今天天气真好！", "zh"),
        ("The temperature is 25 degrees.", "en"),
    ]

    print("\nTTS 演示:")
    for text, lang in texts:
        print(f"\n  [{lang}] {text}")
        speak(text, lang)
        time.sleep(0.5)

def interactive_tts():
    """交互式 TTS"""
    print("\n交互式语音合成")
    print("输入文字进行朗读，输入 'q' 退出\n")

    while True:
        try:
            text = input("输入文字: ").strip()
            if text.lower() == 'q':
                break
            if text:
                speak(text)
        except KeyboardInterrupt:
            break

def weather_report(temp=25, humidity=60, weather="晴天"):
    """天气播报"""
    report = f"当前天气播报：温度{temp}摄氏度，湿度{humidity}百分比，天气{weather}。"
    print(f"\n天气播报: {report}")
    speak(report)

def alarm_voice(message="报警！检测到异常！"):
    """语音报警"""
    for _ in range(3):
        speak(message)
        time.sleep(0.5)

def main():
    print("=" * 40)
    print("🔊 文字转语音 (TTS)")
    print("=" * 40)
    print(f"TTS 引擎: {TTS_ENGINE}")
    print()

    print("选择模式:")
    print("1. TTS 演示")
    print("2. 交互式朗读")
    print("3. 天气播报示例")
    print("4. 语音报警示例")

    choice = input("\n请选择 (1-4): ").strip()

    if choice == '1':
        demo_tts()
    elif choice == '2':
        interactive_tts()
    elif choice == '3':
        weather_report(25, 65, "晴天")
    elif choice == '4':
        alarm_voice()
    else:
        demo_tts()

if __name__ == "__main__":
    main()