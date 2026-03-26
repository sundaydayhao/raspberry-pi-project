#!/usr/bin/env python3
"""
语音命令识别与控制
使用 speech_recognition 库识别语音命令，联动 GPIO 控制硬件

安装依赖:
  pip3 install SpeechRecognition pyaudio
  sudo apt install portaudio19-dev python3-pyaudio

  # 离线识别（推荐树莓派，无需网络）
  pip3 install vosk
  # 下载中文模型: https://alphacephei.com/vosk/models
  # 推荐: vosk-model-small-cn-0.22

学习要点:
  - 麦克风音频采集
  - 在线/离线语音识别
  - 命令关键词匹配
  - 语音→GPIO 动作映射
"""

import os
import time
import threading
import queue

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("⚠️  未找到 SpeechRecognition，请安装: pip3 install SpeechRecognition")

try:
    from vosk import Model, KaldiRecognizer
    import json as _json
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False

# ── 语音命令→GPIO 动作映射 ────────────────────────────────────────────────────
VOICE_COMMANDS = {
    # 关键词列表: (GPIO引脚, 动作描述, 动作类型)
    ("开灯", "打开灯", "灯开"):         (17, "打开 LED", "high"),
    ("关灯", "关闭灯", "灯关"):         (17, "关闭 LED", "low"),
    ("闪烁", "闪灯", "blink"):          (17, "LED 闪烁", "blink"),
    ("报警", "警报", "alarm"):          (18, "蜂鸣器报警", "beep"),
    ("拍照", "截图", "photo"):          (None, "拍照", "photo"),
    ("停止", "关闭", "stop", "退出"):   (None, "停止程序", "stop"),
}

# ── Vosk 模型路径 ─────────────────────────────────────────────────────────────
VOSK_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "vosk-model-small-cn-0.22")

# ── 语音识别语言 ──────────────────────────────────────────────────────────────
LANGUAGE = "zh-CN"   # 中文（Google API）


# ─────────────────────────────────────────────────────────────────────────────
# GPIO 控制
# ─────────────────────────────────────────────────────────────────────────────

_gpio_pins = set()

def setup_gpio():
    if RPI_AVAILABLE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for keywords, (pin, _, _) in VOICE_COMMANDS.items():
            if pin is not None:
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
                _gpio_pins.add(pin)

def execute_action(action_type, pin, description):
    """执行 GPIO 动作"""
    print(f"  ⚡ 执行: {description}")
    if not RPI_AVAILABLE:
        print(f"  [模拟] GPIO{pin} → {description}")

    if action_type == "high":
        if RPI_AVAILABLE and pin:
            GPIO.output(pin, GPIO.HIGH)
    elif action_type == "low":
        if RPI_AVAILABLE and pin:
            GPIO.output(pin, GPIO.LOW)
    elif action_type == "blink":
        def _blink():
            for _ in range(5):
                if RPI_AVAILABLE and pin:
                    GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.2)
                if RPI_AVAILABLE and pin:
                    GPIO.output(pin, GPIO.LOW)
                time.sleep(0.2)
        threading.Thread(target=_blink, daemon=True).start()
    elif action_type == "beep":
        def _beep():
            for _ in range(3):
                if RPI_AVAILABLE and pin:
                    GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.1)
                if RPI_AVAILABLE and pin:
                    GPIO.output(pin, GPIO.LOW)
                time.sleep(0.1)
        threading.Thread(target=_beep, daemon=True).start()
    elif action_type == "photo":
        print("  📷 拍照（模拟）")
    elif action_type == "stop":
        return True  # 信号停止
    return False

def cleanup_gpio():
    if RPI_AVAILABLE:
        GPIO.cleanup()


# ─────────────────────────────────────────────────────────────────────────────
# 命令匹配
# ─────────────────────────────────────────────────────────────────────────────

def match_command(text):
    """
    在识别文本中匹配命令关键词
    返回: (pin, description, action_type) 或 None
    """
    text = text.lower().strip()
    for keywords, action in VOICE_COMMANDS.items():
        for kw in keywords:
            if kw in text:
                return action
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 在线识别（Google Speech API）
# ─────────────────────────────────────────────────────────────────────────────

def run_online_recognition():
    """使用 Google Speech API 进行在线语音识别（需要网络）"""
    if not SR_AVAILABLE:
        print("❌ 需要安装: pip3 install SpeechRecognition pyaudio")
        return

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    setup_gpio()
    print("\n🎤 在线语音识别（Google API，需要网络）")
    print("  说出命令: 开灯、关灯、闪烁、报警、拍照、停止")
    print("  按 Ctrl+C 退出\n")

    try:
        with sr.Microphone() as source:
            print("  校准环境噪音...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("  ✅ 就绪，请说话...\n")

            while True:
                try:
                    print("  🎙️  监听中...")
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)

                    print("  🔄 识别中...")
                    text = recognizer.recognize_google(audio, language=LANGUAGE)
                    print(f"  📝 识别结果: 「{text}」")

                    action = match_command(text)
                    if action:
                        pin, description, action_type = action
                        should_stop = execute_action(action_type, pin, description)
                        if should_stop:
                            break
                    else:
                        print("  ❓ 未匹配到命令")

                except sr.WaitTimeoutError:
                    print("  ⏱️  等待超时，继续监听...")
                except sr.UnknownValueError:
                    print("  ❓ 无法识别语音")
                except sr.RequestError as e:
                    print(f"  ❌ API 请求失败: {e}")

    except KeyboardInterrupt:
        print("\n  已停止")
    finally:
        cleanup_gpio()


# ─────────────────────────────────────────────────────────────────────────────
# 离线识别（Vosk）
# ─────────────────────────────────────────────────────────────────────────────

def run_offline_recognition():
    """使用 Vosk 进行离线语音识别（无需网络）"""
    if not VOSK_AVAILABLE:
        print("❌ 需要安装 Vosk: pip3 install vosk")
        print("   下载中文模型: https://alphacephei.com/vosk/models")
        print(f"   解压到: {VOSK_MODEL_PATH}")
        return

    if not os.path.exists(VOSK_MODEL_PATH):
        print(f"❌ 模型目录不存在: {VOSK_MODEL_PATH}")
        print("   请下载 vosk-model-small-cn-0.22 并解压到 models/ 目录")
        return

    try:
        import pyaudio
    except ImportError:
        print("❌ 需要安装 pyaudio: pip3 install pyaudio")
        return

    model = Model(VOSK_MODEL_PATH)
    rec = KaldiRecognizer(model, 16000)

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8000,
    )
    stream.start_stream()

    setup_gpio()
    print("\n🎤 离线语音识别（Vosk，无需网络）")
    print("  说出命令: 开灯、关灯、闪烁、报警、拍照、停止")
    print("  按 Ctrl+C 退出\n")
    print("  ✅ 就绪，请说话...\n")

    try:
        while True:
            data = stream.read(4000, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                result = _json.loads(rec.Result())
                text = result.get("text", "").strip()
                if text:
                    print(f"  📝 识别结果: 「{text}」")
                    action = match_command(text)
                    if action:
                        pin, description, action_type = action
                        should_stop = execute_action(action_type, pin, description)
                        if should_stop:
                            break
                    else:
                        print("  ❓ 未匹配到命令")
            else:
                partial = _json.loads(rec.PartialResult())
                partial_text = partial.get("partial", "")
                if partial_text:
                    print(f"  🔄 识别中: {partial_text}", end="\r")

    except KeyboardInterrupt:
        print("\n  已停止")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        cleanup_gpio()


# ─────────────────────────────────────────────────────────────────────────────
# 关键词唤醒（简化版）
# ─────────────────────────────────────────────────────────────────────────────

class WakeWordDetector:
    """
    简单的关键词唤醒检测
    先检测唤醒词（如"小派"），再识别命令
    """

    WAKE_WORDS = ["小派", "树莓派", "hey pi", "raspberry"]

    def __init__(self, recognizer):
        self.recognizer = recognizer
        self.is_awake = False
        self.awake_timeout = 5.0
        self.awake_since = 0

    def check_wake(self, text):
        """检查是否包含唤醒词"""
        text_lower = text.lower()
        for word in self.WAKE_WORDS:
            if word in text_lower:
                return True
        return False

    def update(self, text):
        """
        更新唤醒状态
        返回: (is_command, text_without_wake_word)
        """
        now = time.time()

        # 超时自动休眠
        if self.is_awake and (now - self.awake_since) > self.awake_timeout:
            self.is_awake = False
            print("  💤 已休眠（超时）")

        if self.check_wake(text):
            self.is_awake = True
            self.awake_since = now
            print("  👂 已唤醒！请说命令...")
            # 移除唤醒词，提取命令部分
            for word in self.WAKE_WORDS:
                text = text.replace(word, "").strip()
            return True, text

        if self.is_awake:
            return True, text

        return False, text


# ─────────────────────────────────────────────────────────────────────────────
# 演示模式
# ─────────────────────────────────────────────────────────────────────────────

def demo_mode():
    """演示模式（无需麦克风）"""
    print("\n📖 语音命令识别演示")
    print("─" * 40)
    print("  模拟语音命令序列:\n")

    setup_gpio()

    demo_commands = [
        "小派，开灯",
        "请帮我闪烁一下",
        "报警",
        "拍照",
        "关灯",
        "停止",
    ]

    for cmd in demo_commands:
        print(f"  🎤 模拟语音: 「{cmd}」")
        action = match_command(cmd)
        if action:
            pin, description, action_type = action
            should_stop = execute_action(action_type, pin, description)
            if should_stop:
                print("  🛑 收到停止命令")
                break
        else:
            print("  ❓ 未匹配到命令")
        time.sleep(1.0)

    print()
    print("  支持的命令关键词:")
    print("  " + "─" * 35)
    for keywords, (pin, desc, _) in VOICE_COMMANDS.items():
        kw_str = " / ".join(keywords)
        gpio_str = f"GPIO{pin}" if pin else "软件"
        print(f"  {kw_str:<20s} → {gpio_str} {desc}")

    print()
    print("  💡 推荐方案:")
    print("  • 有网络: Google Speech API（识别率高）")
    print("  • 无网络: Vosk 离线模型（树莓派友好）")
    print("  • 低延迟: 关键词检测 + 命令识别两阶段")

    cleanup_gpio()


def main():
    print("=" * 50)
    print("🎤 语音命令识别（AI/ML）")
    print("=" * 50)

    print("\n选择模式:")
    print("1. 在线识别（Google API，需要网络）")
    print("2. 离线识别（Vosk，需要下载模型）")
    print("3. 演示模式（无需麦克风）")

    choice = input("\n请选择 (1-3, 默认3): ").strip() or "3"

    if choice == "1":
        run_online_recognition()
    elif choice == "2":
        run_offline_recognition()
    else:
        demo_mode()


if __name__ == "__main__":
    main()