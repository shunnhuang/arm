import serial
import time
 
class ServoController:
 
    def __init__(self, port="COM3", baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # 等待 Arduino 重启
 
    # =====================================
    # 发送单个舵机角度
    # channel: 0=水平, 1=垂直, 2=备用
    # angle: 0~180
    # =====================================
 
    def send_angle(self, channel, angle):
        angle = max(0, min(180, int(angle)))
        cmd = f"{channel}:{angle}\n"
        self.ser.write(cmd.encode())
 
    # =====================================
    # 同时发送水平+垂直
    # =====================================
 
    def send_pan_tilt(self, pan, tilt):
        self.send_angle(0, pan)
        self.send_angle(1, tilt)
 
    def close(self):
        self.ser.close()