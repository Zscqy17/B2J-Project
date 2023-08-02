import socket
import time

def main():
    # 创建套接字
    s = socket.socket()
    # 连接到服务器
    s.connect(('192.168.80.129', 12345))

    messages = ['2r', '1c', '1r', '2c','3r', '2c', '5r', '1c']
    for msg in messages:
        s.send(msg.encode('utf-8'))
        time.sleep(1)
    
    s.close()

if __name__ == "__main__":
    main()
