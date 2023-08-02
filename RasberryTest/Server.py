import socket
import re
from enum import Enum


class Movements(Enum):
    RHYTHM_L=1
    CLAPHAND_M=2
    RHYTHM_R=3
    HANDUP_L=4
    FEVERMAX_M=5
    HANDUP_R=6
    POINTFINGER_L=7
    FLASHLIGHT_M=8
    POINTFINGER_R=9

def excute_movement(command):
    print(command)
    pass


def process_command(r_value, c_value):
    command = 3 * ( int(r_value) - 1) + int(c_value)
    if command in (e.value for e in Movements):
        excute_movement(command)
    else:
        print("wrong!")

def main():
    # 创建套接字
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('localhost', 12345))

    # 监听端口
    s.listen(5)

    print('服务器已启动，正在监听端口...')

    while True:
        c, addr = s.accept()
        print('已连接：', addr)

        r_received = False
        c_received = False
        r_value = None
        c_value = None
        while True:
            data = c.recv(1024).decode('utf-8')
            if not data:
                break
            # 使用正则表达式解析数据
            match = re.match('(\d+)([rc])', data)
            if match:
                value, type = match.groups()
                if type == 'r':
                    r_received = True
                    r_value = value
                elif type == 'c':
                    c_received = True
                    c_value = value
            else:
                print('接收到无效的数据：', data)

            # 只有当 'r' 和 'c' 都已收到后才处理命令
            if r_received and c_received:
                process_command(r_value, c_value)
                # 重置标志以便于处理下一个命令
                r_received = False
                c_received = False
                r_value = None
                c_value = None

        c.close()

if __name__ == "__main__":
    main()
