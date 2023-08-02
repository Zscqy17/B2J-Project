import threading

# 定义一个线程要执行的任务
def print_numbers():
    for i in range(10):
        print(f"数字线程: {i}")

def print_letters():
    for letter in 'abcdefghij':
        print(f"字母线程: {letter}")

# 创建线程实例
thread1 = threading.Thread(target=print_numbers)
thread2 = threading.Thread(target=print_letters)

# 启动线程
thread1.start()
thread2.start()

# 等待线程完成
thread1.join()
thread2.join()

print("所有线程已完成.")
