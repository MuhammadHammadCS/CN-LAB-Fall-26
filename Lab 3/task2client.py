import socket

HOST = "127.0.0.2"
PORT = 3000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        client_socket.connect((HOST, PORT))
        print("\nConnected to server")
        grade = input("Enter your grade points: ")
        client_socket.send(grade.encode())
        response = client_socket.recv(1024).decode()
        print("Result from server: ", response)
        break
    except Exception as e:
        print("Error: ", e)
        break


        
        