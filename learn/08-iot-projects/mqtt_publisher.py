#!/usr/bin/env python3
"""
MQTT 消息发布者
将传感器数据发布到 MQTT Broker

安装依赖:
  pip3 install paho-mqtt

安装本地 Broker:
  sudo apt install mosquitto mosquitto-clients
  sudo systemctl start mosquitto

学习要点:
  - MQTT 协议基础
  - 发布/订阅模式
  - QoS 级别
"""

import time
import json
import random
import sys

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("⚠️  未找到 paho-mqtt")
    print("   安装: pip3 install paho-mqtt")

BROKER_HOST = "localhost"
BROKER_PORT = 1883
CLIENT_ID = "rpi_publisher"
BASE_TOPIC = "raspberry_pi"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ 已连接到 MQTT Broker ({BROKER_HOST}:{BROKER_PORT})")
    else:
        print(f"❌ 连接失败，错误码: {rc}")

def on_publish(client, userdata, mid):
    pass  # 发布成功回调

def create_client(broker=BROKER_HOST, port=BROKER_PORT):
    """创建 MQTT 客户端"""
    if not MQTT_AVAILABLE:
        return None

    client = mqtt.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.on_publish = on_publish

    try:
        client.connect(broker, port, keepalive=60)
        client.loop_start()
        time.sleep(1)
        return client
    except Exception as e:
        print(f"连接失败: {e}")
        return None

def publish_sensor_data(client, interval=5):
    """持续发布传感器数据"""
    print(f"\n发布传感器数据 (间隔: {interval}秒, Ctrl+C 停止)")
    count = 0

    try:
        while True:
            count += 1
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # 模拟传感器数据
            data = {
                "timestamp": timestamp,
                "count": count,
                "temperature": round(25 + random.uniform(-3, 3), 2),
                "humidity": round(60 + random.uniform(-10, 10), 2),
                "pressure": round(1013 + random.uniform(-5, 5), 2),
                "light": random.randint(200, 1000),
                "motion": random.choice([True, False]),
            }

            # 发布到不同主题
            topics = {
                f"{BASE_TOPIC}/sensors/all": json.dumps(data),
                f"{BASE_TOPIC}/sensors/temperature": str(data['temperature']),
                f"{BASE_TOPIC}/sensors/humidity": str(data['humidity']),
                f"{BASE_TOPIC}/status": "online",
            }

            if client:
                for topic, payload in topics.items():
                    result = client.publish(topic, payload, qos=1)
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        pass
                    else:
                        print(f"  发布失败: {topic}")

            print(f"  [{count}] {timestamp} 温度:{data['temperature']}°C 湿度:{data['humidity']}%")

            if not client:
                print(f"  [模拟] 发布到 {BASE_TOPIC}/sensors/all")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n已停止，共发布 {count} 条消息")

def publish_single(client, topic, message):
    """发布单条消息"""
    if client:
        result = client.publish(topic, message, qos=1)
        result.wait_for_publish()
        print(f"  已发布: {topic} = {message}")
    else:
        print(f"  [模拟] 发布: {topic} = {message}")

def main():
    print("=" * 40)
    print("📤 MQTT 消息发布者")
    print("=" * 40)

    broker = input(f"Broker 地址 (默认 {BROKER_HOST}): ").strip() or BROKER_HOST
    client = create_client(broker)

    print("\n选择模式:")
    print("1. 持续发布传感器数据")
    print("2. 发布单条消息")

    choice = input("\n请选择 (1-2): ").strip()

    try:
        if choice == '1':
            interval = input("发布间隔秒数 (默认5): ").strip()
            interval = int(interval) if interval.isdigit() else 5
            publish_sensor_data(client, interval)
        elif choice == '2':
            topic = input(f"主题 (默认 {BASE_TOPIC}/test): ").strip() or f"{BASE_TOPIC}/test"
            message = input("消息内容: ").strip()
            publish_single(client, topic, message)
        else:
            publish_sensor_data(client)
    finally:
        if client:
            client.loop_stop()
            client.disconnect()
            print("MQTT 连接已断开")

if __name__ == "__main__":
    main()
