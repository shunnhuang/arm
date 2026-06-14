#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// =====================================
// PWM 范围 (根据你的舵机校准)
// 通常: 150=0°, 600=180°
// =====================================
#define SERVO_MIN 150
#define SERVO_MAX 600

// =====================================
// CH3 底盘电机 PWM 范围
// 中点 375 = 停止，低于中点 = 逆时针，高于中点 = 顺时针
// =====================================
#define MOTOR_STOP 375
#define MOTOR_MIN  150
#define MOTOR_MAX  600

// =====================================
// 初始值
// =====================================
int angle0 = 90;  // CH0 水平
int angle1 = 90;  // CH1 垂直
int angle2 = 90;  // CH2 备用
int speed3 = 0;   // CH3 底盘电机 (-100~100)

// =====================================
// 角度 → PWM 映射
// =====================================
int angleToPulse(int angle) {
  angle = constrain(angle, 0, 180);
  return map(angle, 0, 180, SERVO_MIN, SERVO_MAX);
}

void setServo(int channel, int angle) {
  pwm.setPWM(channel, 0, angleToPulse(angle));
}

// speed: -100~100，0=停止，正=顺时针，负=逆时针
void setMotor(int speed) {
  speed = constrain(speed, -100, 100);
  int pulse;
  if (speed == 0) {
    pulse = MOTOR_STOP;
  } else if (speed > 0) {
    pulse = map(speed, 0, 100, MOTOR_STOP, MOTOR_MAX);
  } else {
    pulse = map(speed, -100, 0, MOTOR_MIN, MOTOR_STOP);
  }
  pwm.setPWM(3, 0, pulse);
}

void setup() {
  Serial.begin(115200);

  pwm.begin();
  pwm.setPWMFreq(50);
  delay(500);

  // 三个舵机归中，底盘停止
  setServo(0, angle0);
  setServo(1, angle1);
  setServo(2, angle2);
  setMotor(speed3);

  Serial.println("READY");
}

void loop() {

  // =====================================
  // 读取串口指令
  // 格式: "0:90\n"   →  CH0 转到 90°
  //       "1:45\n"   →  CH1 转到 45°
  //       "2:120\n"  →  CH2 转到 120°
  //       "3:80\n"   →  底盘顺时针 80%
  //       "3:-50\n"  →  底盘逆时针 50%
  //       "3:0\n"    →  底盘停止
  // =====================================

  if (Serial.available()) {

    String line = Serial.readStringUntil('\n');
    line.trim();

    int colonIdx = line.indexOf(':');

    if (colonIdx > 0) {
      int ch  = line.substring(0, colonIdx).toInt();
      int val = line.substring(colonIdx + 1).toInt();

      if (ch >= 0 && ch <= 2) {
        setServo(ch, val);
        Serial.print("CH");
        Serial.print(ch);
        Serial.print("=");
        Serial.println(val);

      } else if (ch == 3) {
        speed3 = val;
        setMotor(speed3);
        Serial.print("CH3=");
        Serial.println(speed3);

      } else {
        Serial.println("ERR:invalid_channel");
      }
    }
  }
}