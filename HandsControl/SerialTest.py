import serial

# 创建一个串口对象
ser = serial.Serial('COM3', 9600)  # 将'COM4'替换为你的Arduino连接的串口号

# 写入数据
ser.write(b'1')

# 关闭串口
ser.close()
