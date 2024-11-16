import asyncio
import websockets
import wave
 
# 服务器地址和端口
HOST = '172.19.1.180'  # 可以替换为服务器的实际 IP 地址或域名(本电脑的IP地址)
PORT = 8765            # WebSocket 服务器端口
 
# 音频文件路径
AUDIO_FILE_PATH = 'D:\\daoxiang.wav'  # 音频文件路径
 
async def send_audio(websocket, path):
    print(f"客户端已连接: {websocket.remote_address}")
 
    # 打开音频文件
    try:
        with wave.open(AUDIO_FILE_PATH, 'rb') as wf:
            print(f"音频文件 {AUDIO_FILE_PATH} 已打开.")
 
            # 获取音频文件参数
            chunk_size = 1024  # 每次发送的数据块大小
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
 
            print(f"音频参数: {n_channels} 通道, {sampwidth} 字节样本宽度, {framerate} 采样率.")
 
            # 逐块读取音频数据并发送给客户端
            while True:
                audio_data = wf.readframes(chunk_size)
                if not audio_data:  # 如果读取完所有数据，退出循环
                    break
 
                # 发送音频数据给客户端
                await websocket.send(audio_data)
                await asyncio.sleep(0.01)  # 确保非阻塞发送，控制发送速度
 
    except websockets.ConnectionClosed as e:
        print(f"客户端断开连接: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
 
async def start_server():
    # 创建 WebSocket 服务器
    async with websockets.serve(send_audio, HOST, PORT):
        print(f"WebSocket 服务器已启动: ws://{HOST}:{PORT}/")
        await asyncio.Future()  # 运行服务器，直到手动停止
 
# 运行服务器
asyncio.run(start_server())
