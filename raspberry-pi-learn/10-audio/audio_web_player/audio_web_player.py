#!/usr/bin/env python3
"""
网页音频控制中心
Web Audio Control Center

功能：
- 网页远程播放/暂停/停止音频文件
- 音量控制（滑块）
- 播放列表管理（上传/删除音频文件）
- 文字转语音（TTS）远程输入文字，树莓派朗读
- 蜂鸣器音乐（网页选择曲目，树莓派蜂鸣器演奏）
- 录音（网页触发，保存到服务器）
- 播放进度显示

依赖安装：
  pip3 install flask
  sudo apt install mpg123 espeak ffmpeg -y

访问地址：http://<树莓派IP>:5006
"""

import os
import time
import threading
import subprocess
from datetime import datetime
from collections import deque
from flask import Flask, render_template, jsonify, request, send_from_directory

# ==================== 配置 ====================
AUDIO_DIR = 'audio_files'   # 音频文件目录
RECORD_DIR = 'recordings'   # 录音保存目录
BUZZER_PIN = 18             # 蜂鸣器GPIO引脚（无源蜂鸣器）
MAX_VOLUME = 100
DEFAULT_VOLUME = 70

# 支持的音频格式
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.m4a'}

# ==================== 蜂鸣器音乐曲库 ====================
SONGS = {
    '生日快乐': [
        (262, 0.3), (262, 0.3), (294, 0.6), (262, 0.6),
        (349, 0.6), (330, 1.2), (262, 0.3), (262, 0.3),
        (294, 0.6), (262, 0.6), (392, 0.6), (349, 1.2),
        (262, 0.3), (262, 0.3), (523, 0.6), (440, 0.6),
        (349, 0.6), (330, 0.6), (294, 1.2), (466, 0.3),
        (466, 0.3), (440, 0.6), (349, 0.6), (392, 0.6), (349, 1.2),
    ],
    '两只老虎': [
        (262, 0.4), (294, 0.4), (330, 0.4), (262, 0.4),
        (262, 0.4), (294, 0.4), (330, 0.4), (262, 0.4),
        (330, 0.4), (349, 0.4), (392, 0.8),
        (330, 0.4), (349, 0.4), (392, 0.8),
        (392, 0.3), (440, 0.3), (392, 0.3), (349, 0.3), (330, 0.4), (262, 0.4),
        (392, 0.3), (440, 0.3), (392, 0.3), (349, 0.3), (330, 0.4), (262, 0.4),
        (262, 0.4), (196, 0.4), (262, 0.8),
        (262, 0.4), (196, 0.4), (262, 0.8),
    ],
    '小星星': [
        (262, 0.5), (262, 0.5), (392, 0.5), (392, 0.5),
        (440, 0.5), (440, 0.5), (392, 1.0),
        (349, 0.5), (349, 0.5), (330, 0.5), (330, 0.5),
        (294, 0.5), (294, 0.5), (262, 1.0),
        (392, 0.5), (392, 0.5), (349, 0.5), (349, 0.5),
        (330, 0.5), (330, 0.5), (294, 1.0),
        (392, 0.5), (392, 0.5), (349, 0.5), (349, 0.5),
        (330, 0.5), (330, 0.5), (294, 1.0),
        (262, 0.5), (262, 0.5), (392, 0.5), (392, 0.5),
        (440, 0.5), (440, 0.5), (392, 1.0),
        (349, 0.5), (349, 0.5), (330, 0.5), (330, 0.5),
        (294, 0.5), (294, 0.5), (262, 1.0),
    ],
    '欢乐颂': [
        (330, 0.4), (330, 0.4), (349, 0.4), (392, 0.4),
        (392, 0.4), (349, 0.4), (330, 0.4), (294, 0.4),
        (262, 0.4), (262, 0.4), (294, 0.4), (330, 0.4),
        (330, 0.6), (294, 0.2), (294, 0.8),
        (330, 0.4), (330, 0.4), (349, 0.4), (392, 0.4),
        (392, 0.4), (349, 0.4), (330, 0.4), (294, 0.4),
        (262, 0.4), (262, 0.4), (294, 0.4), (330, 0.4),
        (294, 0.6), (262, 0.2), (262, 0.8),
    ],
    '哆来咪': [
        (262, 0.5), (294, 0.5), (330, 0.5), (262, 0.5),
        (330, 0.5), (262, 0.5), (330, 1.0),
        (294, 0.5), (349, 0.5), (392, 1.0),
        (392, 0.5), (349, 0.5), (294, 0.5), (262, 0.5),
        (392, 0.5), (262, 0.5), (392, 1.0),
    ],
}

# ==================== 全局状态 ====================
player_state = {
    'playing': False,
    'paused': False,
    'current_file': '',
    'volume': DEFAULT_VOLUME,
    'duration': 0,
    'position': 0,
    'buzzer_playing': False,
    'buzzer_song': '',
    'recording': False,
    'tts_speaking': False,
    'mode': 'idle',   # idle / playing / buzzer / recording / tts
}

play_log = deque(maxlen=30)
current_process = None
process_lock = threading.Lock()

# ==================== 目录初始化 ====================
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(RECORD_DIR, exist_ok=True)

# 创建示例音频文件列表（如果目录为空，提示用户上传）
def get_audio_files():
    files = []
    for f in sorted(os.listdir(AUDIO_DIR)):
        if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS:
            path = os.path.join(AUDIO_DIR, f)
            size = os.path.getsize(path)
            files.append({
                'name': f,
                'size': f'{size // 1024} KB',
                'path': path,
            })
    return files

def get_recordings():
    files = []
    for f in sorted(os.listdir(RECORD_DIR), reverse=True):
        if f.endswith('.wav'):
            path = os.path.join(RECORD_DIR, f)
            size = os.path.getsize(path)
            files.append({'name': f, 'size': f'{size // 1024} KB'})
    return files

# ==================== 音频播放控制 ====================
def stop_all():
    """停止所有音频活动"""
    global current_process
    with process_lock:
        if current_process and current_process.poll() is None:
            current_process.terminate()
            current_process = None
    player_state['playing'] = False
    player_state['paused'] = False
    player_state['buzzer_playing'] = False
    player_state['recording'] = False
    player_state['tts_speaking'] = False
    player_state['mode'] = 'idle'
    player_state['current_file'] = ''


def play_file(filename):
    """播放音频文件"""
    global current_process
    stop_all()
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        return False, '文件不存在'

    def _play():
        global current_process
        player_state['playing'] = True
        player_state['current_file'] = filename
        player_state['mode'] = 'playing'
        play_log.appendleft({'time': datetime.now().strftime('%H:%M:%S'), 'action': f'▶ 播放：{filename}'})

        ext = os.path.splitext(filename)[1].lower()
        vol = player_state['volume']

        try:
            if ext == '.mp3':
                cmd = ['mpg123', '-q', f'--scale={int(vol * 327)}', filepath]
            else:
                cmd = ['aplay', '-q', filepath]

            with process_lock:
                current_process = subprocess.Popen(cmd)
            current_process.wait()
        except FileNotFoundError:
            # 回退：使用 ffplay
            try:
                cmd = ['ffplay', '-nodisp', '-autoexit', '-volume', str(vol), filepath]
                with process_lock:
                    current_process = subprocess.Popen(cmd, stderr=subprocess.DEVNULL)
                current_process.wait()
            except Exception as e:
                print(f"播放失败: {e}")

        player_state['playing'] = False
        player_state['mode'] = 'idle'
        player_state['current_file'] = ''

    threading.Thread(target=_play, daemon=True).start()
    return True, f'开始播放：{filename}'


def set_volume(vol):
    """设置音量"""
    player_state['volume'] = max(0, min(100, int(vol)))
    # 使用 amixer 设置系统音量
    try:
        subprocess.run(['amixer', 'sset', 'Master', f'{player_state["volume"]}%'],
                       capture_output=True)
    except Exception:
        pass


def speak_tts(text, lang='zh'):
    """文字转语音"""
    stop_all()

    def _speak():
        global current_process
        player_state['tts_speaking'] = True
        player_state['mode'] = 'tts'
        play_log.appendleft({'time': datetime.now().strftime('%H:%M:%S'), 'action': f'🔊 TTS：{text[:20]}'})
        try:
            if lang == 'zh':
                cmd = ['espeak', '-v', 'zh', '-s', '150', text]
            else:
                cmd = ['espeak', '-v', 'en', '-s', '150', text]
            with process_lock:
                current_process = subprocess.Popen(cmd)
            current_process.wait()
        except Exception as e:
            print(f"TTS失败: {e}")
        player_state['tts_speaking'] = False
        player_state['mode'] = 'idle'

    threading.Thread(target=_speak, daemon=True).start()
    return True, f'正在朗读：{text[:20]}...'


def start_recording(duration=10):
    """开始录音"""
    stop_all()

    def _record():
        global current_process
        player_state['recording'] = True
        player_state['mode'] = 'recording'
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'rec_{ts}.wav'
        filepath = os.path.join(RECORD_DIR, filename)
        play_log.appendleft({'time': datetime.now().strftime('%H:%M:%S'), 'action': f'🎙 录音：{filename}'})
        try:
            cmd = ['arecord', '-d', str(duration), '-f', 'cd', '-t', 'wav', filepath]
            with process_lock:
                current_process = subprocess.Popen(cmd)
            current_process.wait()
        except Exception as e:
            print(f"录音失败: {e}")
        player_state['recording'] = False
        player_state['mode'] = 'idle'
        print(f"🎙 录音完成：{filename}")

    threading.Thread(target=_record, daemon=True).start()
    return True, f'开始录音，持续{duration}秒'


# ==================== 蜂鸣器控制 ====================
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    buzzer_pwm = GPIO.PWM(BUZZER_PIN, 440)
    BUZZER_AVAILABLE = True
except Exception:
    BUZZER_AVAILABLE = False

def play_buzzer_song(song_name):
    """蜂鸣器演奏歌曲"""
    if song_name not in SONGS:
        return False, '曲目不存在'
    stop_all()

    def _buzz():
        player_state['buzzer_playing'] = True
        player_state['buzzer_song'] = song_name
        player_state['mode'] = 'buzzer'
        play_log.appendleft({'time': datetime.now().strftime('%H:%M:%S'), 'action': f'🎵 蜂鸣器：{song_name}'})
        notes = SONGS[song_name]
        for freq, dur in notes:
            if not player_state['buzzer_playing']:
                break
            if BUZZER_AVAILABLE:
                buzzer_pwm.start(50)
                buzzer_pwm.ChangeFrequency(freq)
                time.sleep(dur * 0.9)
                buzzer_pwm.stop()
                time.sleep(dur * 0.1)
            else:
                # 模拟模式：打印音符
                note_names = {262:'C4',294:'D4',330:'E4',349:'F4',392:'G4',
                              440:'A4',466:'A#4',523:'C5',196:'G3'}
                print(f"♪ {note_names.get(freq, str(freq)+'Hz')} ({dur}s)")
                time.sleep(dur)
        player_state['buzzer_playing'] = False
        player_state['mode'] = 'idle'
        player_state['buzzer_song'] = ''

    threading.Thread(target=_buzz, daemon=True).start()
    return True, f'开始演奏：{song_name}'


# ==================== Flask Web服务器 ====================
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('audio_web_player.html',
                           songs=list(SONGS.keys()))

@app.route('/api/status')
def api_status():
    return jsonify({**player_state, 'audio_files': get_audio_files()})

@app.route('/api/play', methods=['POST'])
def api_play():
    data = request.get_json()
    ok, msg = play_file(data.get('filename', ''))
    return jsonify({'success': ok, 'message': msg})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    stop_all()
    play_log.appendleft({'time': datetime.now().strftime('%H:%M:%S'), 'action': '⏹ 停止'})
    return jsonify({'success': True, 'message': '已停止'})

@app.route('/api/volume', methods=['POST'])
def api_volume():
    data = request.get_json()
    set_volume(data.get('volume', 70))
    return jsonify({'success': True, 'volume': player_state['volume']})

@app.route('/api/tts', methods=['POST'])
def api_tts():
    data = request.get_json()
    text = data.get('text', '').strip()
    lang = data.get('lang', 'zh')
    if not text:
        return jsonify({'success': False, 'message': '请输入文字'})
    ok, msg = speak_tts(text, lang)
    return jsonify({'success': ok, 'message': msg})

@app.route('/api/buzzer', methods=['POST'])
def api_buzzer():
    data = request.get_json()
    ok, msg = play_buzzer_song(data.get('song', ''))
    return jsonify({'success': ok, 'message': msg})

@app.route('/api/record', methods=['POST'])
def api_record():
    data = request.get_json()
    duration = int(data.get('duration', 10))
    ok, msg = start_recording(duration)
    return jsonify({'success': ok, 'message': msg})

@app.route('/api/recordings')
def api_recordings():
    return jsonify(get_recordings())

@app.route('/api/play_recording', methods=['POST'])
def api_play_recording():
    data = request.get_json()
    filename = data.get('filename', '')
    filepath = os.path.join(RECORD_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': '文件不存在'})
    stop_all()
    def _play():
        player_state['playing'] = True
        player_state['current_file'] = filename
        player_state['mode'] = 'playing'
        try:
            subprocess.run(['aplay', '-q', filepath])
        except Exception:
            pass
        player_state['playing'] = False
        player_state['mode'] = 'idle'
    threading.Thread(target=_play, daemon=True).start()
    return jsonify({'success': True, 'message': f'播放录音：{filename}'})

@app.route('/api/log')
def api_log():
    return jsonify(list(play_log))

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '未选择文件'})
    f = request.files['file']
    if not f.filename:
        return jsonify({'success': False, 'message': '文件名为空'})
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in AUDIO_EXTENSIONS:
        return jsonify({'success': False, 'message': f'不支持的格式：{ext}'})
    save_path = os.path.join(AUDIO_DIR, f.filename)
    f.save(save_path)
    return jsonify({'success': True, 'message': f'上传成功：{f.filename}'})

@app.route('/api/delete', methods=['POST'])
def api_delete():
    data = request.get_json()
    filename = data.get('filename', '')
    filepath = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True, 'message': f'已删除：{filename}'})
    return jsonify({'success': False, 'message': '文件不存在'})

# ==================== 主程序 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("🎵 网页音频控制中心")
    print("=" * 50)
    print(f"音频目录: {os.path.abspath(AUDIO_DIR)}")
    print(f"录音目录: {os.path.abspath(RECORD_DIR)}")
    print(f"蜂鸣器: {'可用' if BUZZER_AVAILABLE else '模拟模式'}")
    print(f"曲库: {len(SONGS)} 首")
    print()

    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = '127.0.0.1'

    print(f"🌐 控制台地址：http://{ip}:5006")
    print("按 Ctrl+C 停止")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5006, debug=False, threaded=True)