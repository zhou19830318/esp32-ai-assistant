import asyncio
import websockets
import pyaudio
 
# WebSocket 服务器的 URL
WS_URL = "ws://192.168.127.22:8765/"  # 服务器的实际 IP 地址或域名
 
# 配置音频播放参数
CHUNK = 1024  # 每个数据块的大小
FORMAT = pyaudio.paInt16  # 音频格式
CHANNELS = 2  # 音频通道数量（立体声）
RATE = 44100  # 采样率（每秒样本数）
 
# 初始化 PyAudio
audio = pyaudio.PyAudio()
 
# 创建流对象用于音频播放
stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    frames_per_buffer=CHUNK)
 
 
async def play_audio_from_websocket():
    async with websockets.connect(WS_URL) as websocket:
        print("已连接到 WebSocket 服务器...")
        try:
            while True:
                # 接收音频数据
                audio_data = await websocket.recv()
 
                # 将接收到的数据写入到音频流中播放
                stream.write(audio_data)
 
        except websockets.ConnectionClosed as e:
            print(f"WebSocket 连接关闭: {e}")
        except Exception as e:
            print(f"发生错误: {e}")
 
 
# 运行异步任务
asyncio.run(play_audio_from_websocket())
 
# 关闭流和 PyAudio
stream.stop_stream()
stream.close()
audio.terminate()
