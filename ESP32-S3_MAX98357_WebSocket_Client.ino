#include "Arduino.h"
#include "WiFi.h"
#include <WebSocketsClient.h>
#include <driver/i2s.h> // 使用ESP32 I2S库
 
// WiFi 信息
const char* ssid = "your wifi"; // 替换为WiFi名称
const char* password = "12345678"; // 替换为WiFi密码
 
// WebSocket 服务器信息
const char* websocket_server = "172.19.1.170"; // 替换为WebSocket服务器IP地址
const uint16_t websocket_port = 8765; // WebSocket服务器端口
const char* websocket_path = "/"; // WebSocket路径
WebSocketsClient webSocket; // 创建 WebSocket 客户端对象
 
void onWebSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
 
    switch (type) {
        case WStype_CONNECTED:
            Serial.println("Connected to WebSocket server");
            break;
        case WStype_DISCONNECTED:
            Serial.println("Disconnected from WebSocket server");
            break;
        case WStype_BIN:
            // 将接收到的二进制音频数据写入 I2S
            size_t bytes_written;
            i2s_write(I2S_NUM_0, payload, length, &bytes_written, portMAX_DELAY);
            break;
        case WStype_ERROR:
            Serial.println("WebSocket Error");
            break;
        default:
            break;
    }
}
 
void setup() {
 
    Serial.begin(115200);
    // 连接到 WiFi
    WiFi.disconnect();
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    // 等待连接到 WiFi
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
 
    Serial.println("Connected to WiFi");
    // 初始化 I2S
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = 44100,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = I2S_COMM_FORMAT_I2S_MSB,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 1024,
        .use_apll = false,
        .tx_desc_auto_clear = true,
        .fixed_mclk = 0
    };
 
    i2s_pin_config_t pin_config = {
        .bck_io_num = 3,    // BCLK 引脚
        .ws_io_num = 4,     // LRC 引脚
        .data_out_num = 5,  // DATA 输出引脚
        .data_in_num = I2S_PIN_NO_CHANGE
    };
 
    // 配置 I2S 接口
    i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config);
    i2s_zero_dma_buffer(I2S_NUM_0);
    // 初始化 WebSocket 客户端
    webSocket.begin(websocket_server, websocket_port, websocket_path);
    webSocket.onEvent(onWebSocketEvent); // 设置 WebSocket 事件处理函数
    // 开始 WebSocket 连接
    webSocket.setReconnectInterval(5000); // 自动重连间隔
}
 
void loop() {
    webSocket.loop(); // 处理 WebSocket 客户端事件
}
