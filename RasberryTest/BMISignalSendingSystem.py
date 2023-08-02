import socket
import threading
import tkinter as tk
from tkinter import ttk
import queue
import tkinter.messagebox


class SokectServerThread(threading.Thread):
    def __init__(self, name, ip, port, queue, wrong_queue):
        super().__init__(daemon=True)
        self.name = name
        self.ip = ip
        self.port = port
        self.queue = queue
        self.wrong_queue = wrong_queue

        try:
            self.socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.ip, self.port))
            self.socket.listen(1)
        except Exception as e:
            self.wrong_queue.put(str(name)+str(e))

    def run(self):
        client_socket, addr = self.socket.accept()
        while True:
            print(f"Accepted connection from {addr[0]}:{addr[1]}")
            msg = client_socket.recv(1024)
            if not msg:
                break
            data = msg.decode('utf-8')
            self.queue.put(data)
        self.socket.close()



class SocketThread(threading.Thread):
    def __init__(self, name, ip, port, queue, wrong_queue):
        super().__init__(daemon=True)
        self.name = name
        self.ip = ip
        self.port = port
        self.queue = queue
        self.wrong_queue = wrong_queue
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1.0)
        try:
            self.socket.connect((self.ip, self.port))
            self.socket.settimeout(None)
        except Exception as e:
            self.wrong_queue.put(str(name)+str(e))

    def run(self):
        while True:
            data = self.socket.recv(1024)
            if not data:
                break
            self.queue.put(data)
            print(data)
        self.socket.close()


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid()
        self.create_widgets()
        self.arm_queue = queue.Queue()
        self.bmi_queue = queue.Queue()
        self.arm_wrong_queue = queue.Queue()
        self.bmi_wrong_queue = queue.Queue()
        self.bmi_callback_queue = queue.Queue()
        self.bmi_callback_wrong_queue = queue.Queue()
        self.bmi_callback_server_queue = queue.Queue()
        self.bmi_callback_server_wrong_queue = queue.Queue()

        self.bmi_callback_server = None
        self.bmi_callback_socket_thread = None
        self.arm_socket_thread = None
        self.bmi_socket_thread = None
        self.bmi_callback_server_thread = None

    def destroy(self):
        if self.arm_socket_thread is not None:
            self.arm_socket_thread.socket.close()
        if self.bmi_socket_thread is not None:
            self.bmi_socket_thread.socket.close()
        if self.bmi_callback_server_thread is not None:
            self.bmi_callback_server_thread.socket.close()
        if self.bmi_callback_socket_thread is not None:
            self.bmi_callback_socket_thread.socket.close()
        super().destroy()

    def create_widgets(self):
        self.ip_label = tk.Label(self, text="Arm IP: ")
        self.ip_label.grid(row=0, column=0, sticky='w')

        self.ip_entry = tk.Entry(self)
        self.ip_entry.insert(0, "192.168.2.106")
        self.ip_entry.grid(row=0, column=1, sticky='w')

        self.port_label = tk.Label(self, text="Arm Port: ")

        self.port_label.grid(row=1, column=0, sticky='w')

        self.port_entry = tk.Entry(self)
        self.port_entry.insert(0, "12345")
        self.port_entry.grid(row=1, column=1, sticky='w')

        self.confirm_button = tk.Button(
            self, text="Arm Confirm", command=self.confirm, width=20)
        self.confirm_button.grid(row=1, column=2)

        self.signal_label = tk.Label(self, text="Signal: ")
        self.signal_label.grid(row=2, column=0, sticky='w')

        self.signal_entry = tk.Entry(self)
        self.signal_entry.grid(row=2, column=1, sticky='w')

        self.send_button = tk.Button(
            self, text="Send", command=self.send_data, width=20)
        self.send_button['state'] = tk.DISABLED
        self.send_button.grid(row=2, column=2)

        self.state_label = tk.Label(self, text="Change Mode: ")
        self.state_label.grid(row=3, column=0, sticky='w')

        self.state_var = tk.StringVar(self)
        self.state_var.set("Auto")

        self.state_option = ttk.Combobox(
            self, textvariable=self.state_var, state="readonly")
        self.state_option['values'] = ('Auto', 'Manual')
        self.state_option.grid(row=3, column=1, sticky='w')
        self.state_option.bind('<<ComboboxSelected>>', self.on_state_change)

    def start_arm_client_socket(self):
        self.arm_ip = self.ip_entry.get()
        self.arm_port = int(self.port_entry.get())
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.connect((self.arm_ip, self.arm_port))  # 在这里建立连接

    def confirm(self):
        if self.arm_socket_thread is not None:
            self.arm_socket_thread.socket.close()
        if self.bmi_socket_thread is not None:
            self.bmi_socket_thread.socket.close()
        if self.bmi_callback_server_thread is not None:
            self.bmi_callback_server_thread.socket.close() 
        if self.bmi_callback_socket_thread is not None:
            self.bmi_callback_socket_thread.socket.close()

        self.bmi_callback_server_thread = SokectServerThread(
            "bmi_callback_socket_thread", "0.0.0.0", 9001, self.bmi_callback_server_queue, self.bmi_callback_server_wrong_queue)
        self.bmi_callback_server_thread.start()

        arm_ip = self.ip_entry.get()
        arm_port = int(self.port_entry.get())
        self.arm_socket_thread = SocketThread(
            "arm_socket_thread", arm_ip, arm_port, self.arm_queue, self.arm_wrong_queue)
        self.arm_socket_thread.start()

        self.bmi_socket_thread = SocketThread(
            "bmi_socket_thread", '127.0.0.1', 8889, self.bmi_queue, self.bmi_wrong_queue)
        self.bmi_socket_thread.start()

        self.bmi_callback_socket_thread = SocketThread(
            "bmi_callback_socket_thread", '127.0.0.1', 9000, self.bmi_callback_queue, self.bmi_callback_wrong_queue)
        self.bmi_callback_socket_thread.start()

        self.check_new_message()
        

        # 检查队列中是否有错误消息
        if not self.arm_wrong_queue.empty():
            error_message = self.arm_wrong_queue.get()
            tkinter.messagebox.showerror(
                'Error', f'Arm connection error: {error_message}')

        if not self.bmi_wrong_queue.empty():
            error_message = self.bmi_wrong_queue.get()
            tkinter.messagebox.showerror(
                'Error', f'BMI connection error: {error_message}')
        if not self.bmi_callback_wrong_queue.empty():
            error_message = self.bmi_callback_wrong_queue.get()
            tkinter.messagebox.showerror(
                'Error', f'BMI callback connection error: {error_message}')
        if not self.bmi_callback_server_wrong_queue.empty():
            error_message = self.bmi_callback_server_wrong_queue.get()
            tkinter.messagebox.showerror(
                'Error', f'BMI callback server error: {error_message}')

    def check_new_message(self):
        if not self.bmi_queue.empty():
            if self.state_var.get() == 'Manual':
                self.bmi_socket_thread.queue.get()
            else:
                message = self.bmi_socket_thread.queue.get()
                self.process_data(message)
        
        if not self.bmi_callback_server_queue.empty():
            signal = self.bmi_callback_server_queue.get()
            self.bmi_callback_socket_thread.socket.sendall(signal.encode('utf-8'))
            print("we got signal from robot"+signal)
        self.after(100, self.check_new_message)  # 每100ms检查一次新消息

    def process_data(self, data):
        self.signal_entry.delete(0, tk.END)
        self.signal_entry.insert(0, data)
        if self.state_var.get() == 'Auto':
            self.send_data()

    def send_data(self):
        self.data = self.signal_entry.get()
        self.arm_socket_thread.socket.send(self.data.encode())

    def on_state_change(self, event):
        if self.state_var.get() == "Auto":
            self.send_button['state'] = tk.DISABLED
        else:
            self.send_button['state'] = tk.NORMAL


root = tk.Tk()
root.title("BMI Signal Sending System")
app = Application(master=root)
app.mainloop()
