import socket
import threading
import tkinter as tk
from tkinter import ttk

def send_msg():
    server_ip = ip_var.get()
    server_port = int(port_var.get())
    message = msg_entry.get()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.connect((server_ip, server_port))
        server_socket.sendall(message.encode('utf-8'))

def main():
    global ip_entry, port_entry, msg_entry, response_label, ip_var, port_var

    window = tk.Tk()
    window.title("TCP 发送信息")

    ip_label = ttk.Label(window, text="IP 地址：")
    ip_label.grid(column=0, row=0, sticky=tk.W)

    ip_var = tk.StringVar(value="127.0.0.1")  # 设置默认IP地址
    ip_entry = ttk.Entry(window, textvariable=ip_var)
    ip_entry.grid(column=1, row=0)

    port_label = ttk.Label(window, text="端口号：")
    port_label.grid(column=0, row=1, sticky=tk.W)

    port_var = tk.StringVar(value="8889")  # 设置默认端口号
    port_entry = ttk.Entry(window, textvariable=port_var)
    port_entry.grid(column=1, row=1)

    msg_label = ttk.Label(window, text="发送信息：")
    msg_label.grid(column=0, row=2, sticky=tk.W)
    msg_entry = ttk.Entry(window)
    msg_entry.grid(column=1, row=2)

    send_button = ttk.Button(window, text="发送", command=send_msg)
    send_button.grid(column=1, row=3)

    response_label = ttk.Label(window, text="")
    response_label.grid(column=0, row=4, columnspan=2)

    window.mainloop()

if __name__ == "__main__":
    main()
