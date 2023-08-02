import socket
import threading

clients_lock = threading.Lock()
clients = set()

def broadcast(client_socket, msg):
    with clients_lock:
        for client in clients:
            if client is not client_socket:
                client.send(msg)

def handle_client(client_socket):
    with clients_lock:
        clients.add(client_socket)

    while True:
        msg = client_socket.recv(1024)
        if not msg:
            break
        num = msg.decode('utf-8')
        print(f"Received from client and incremented: {num}")
        broadcast(client_socket, num.encode('utf-8'))

    with clients_lock:
        clients.remove(client_socket)
    client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 9000))
    server.listen(50)

    print("Server is listening on 127.0.0.1:9000")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()