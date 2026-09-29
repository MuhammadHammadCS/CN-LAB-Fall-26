import socket
import json
HOST = "127.0.0.1"
PORT = 5000
while True:
    try:    
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        print("\nConnected to server")
        num1 = float(input("Enter first number: "))
        num2 = float(input("Enter second number: "))
        operation = input("Enter operation (+, -, *, /): ")
        data = {
            "num1": num1,
            "operation": operation,
            "num2": num2
        }
        message = json.dumps(data)
        client_socket.send(message.encode())
        response = client_socket.recv(1024).decode()
        print("Result from server: ", response)
        client_socket.close()
        choice = input("\nDo another calculation(y/n): ")
        if choice.lower() != "y":
            print("Client closed.")
            break
    except Exception as e:
        print("Error: ", e)
        break