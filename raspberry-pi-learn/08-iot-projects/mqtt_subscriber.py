#!/usr/bin/env python3
"""
MQTT 消息订阅者
订阅 MQTT 主题并处理接收到的消息

安装依赖:
  pip3 install paho-mqtt

学习要点:
  - MQTT 订阅模式
  - 消息回调处理
  - 主题通配符
"""

import time
import json
import sys

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("安装: pip3 install paho-mqtt")

BROKER_HOST = "localhost"
BROKER_PORT = 1883
CLIENT_ID = "rpi_subscriber"
BASE_TOPIC = "raspberry_pi"

received_messages = []

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"已连接到 Broker，订阅主题...")
        # 订阅主题
        client.subscribe(f"{BASE_TOPIC}/#", qos=1)
        print(f"已订阅: {BASE_TOPIC}/#")
    else:
        print(f"连接失败，错误码: {rc}")

def on_message(client, userdata, msg):
    timestamp = time.strftime("%H:%M:%S")
    topic = msg.topic
    payload = msg.payload.decode('utf-8', errors='replace')

    received_messages.append({
        'time': timestamp,
        'topic': topic,
        'payload': payload
    })

    # 尝试解析 JSON
    try:
        data = json.loads(payload)
        if 'temperature' in data:
            print(f"  [{timestamp}] {topic}")
            print(f"    温度: {data.get('temperature')}°C  湿度: {data.get('humidity')}%")
        else:
            print(f"  [{timestamp}] {topic}: {payload[:80]}")
    except json.JSONDecodeError:
        print(f"  [{timestamp}] {topic}: {payload[:80]}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"意外断开连接，错误码: {rc}")

def subscribe(broker=BROKER_HOST, topics=None):
    """启动订阅"""
    if not MQTT_AVAILABLE:
        print("paho-mqtt 未安装")
        return

    client = mqtt.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect(broker, BROKER_PORT, keepalive=60)
        print(f"订阅模式启动 (Ctrl+C 退出)")
        client.loop_forever()
    except KeyboardInterrupt:
        print(f"\n已停止，共收到 {len(received_messages)} 条消息")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        client.disconnect()

def main():
    print("=" * 40)
    print("📥 MQTT 消息订阅者")
    print("=" * 40)

    broker = input(f"Broker 地址 (默认 {BROKER_HOST}): ").strip() or BROKER_HOST
    subscribe(broker)

if __name__ == "__main__":
    main()