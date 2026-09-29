import socket
import json
from datetime import datetime
HOST = "127.0.0.1"
PORT = 5000
s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_socket.bind((HOST, PORT))
s_socket.listen(5)
print("Server is running...")
print(f"Listening on {HOST}:{PORT}")
while True:
    
    c_socket, c_addr = s_socket.accept()
    print(f"\nClient connected: {c_addr}")
    try:
        data = c_socket.recv(1024).decode()
        if not data: 
            c_socket.close()
            continue
        request = json.loads(data)
        num1 = request["num1"]
        num2 = request["num2"]
        operation = request["operation"]
        if operation == "+":
            answer = num1 + num2
        elif operation == "-":
            answer = num1 - num2
        elif operation == "*":
            answer = num1 * num2
        elif operation == "/":
            if num2 == 0:
                answer = "Cannot divide by zero"
            else:
                answer = num1 / num2
        else:
            answer = "Invalid operation"
        record = {
            "num1": num1,
            "operation": operation,
            "num2": num2,
            "answer": answer,
            "client_ip": c_addr[0],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            with open("records.json", "r") as file:
                calculations = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            calculations = []
        calculations.append(record)
        with open("records.json", "w") as file:
            json.dump(calculations, file, indent=4)
        response = str(answer)
        c_socket.send(response.encode())
        print(f"Received: {num1} {operation} {num2}")
        print(f"Answer sent: {answer}")
        print("Details saved to records.json")
    except Exception as e:
        c_socket.send(f"Error: {e}".encode())
    c_socket.close()
