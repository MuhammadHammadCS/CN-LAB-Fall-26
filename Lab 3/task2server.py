import socket

HOST = "127.0.0.2"
PORT = 3000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))

server_socket.listen(5)
print("Server is running...")

while True:
    client_socket, client_address = server_socket.accept()
    print(f"\nClient connected: {client_address}")

    try:
        data = client_socket.recv(1024).decode()
        if not data:
            client_socket.close()
            continue

        grade_points = float(data)
        if grade_points >= 4.33:
            letter_grade = "A+"
            Qualitative_feedback = "Excellent"
        elif grade_points >= 4.0:   
            letter_grade = "A"
            Qualitative_feedback = "Excellent"
        elif grade_points >= 3.66:
            letter_grade = "A-"
            Qualitative_feedback = "Very Good"
        elif grade_points >= 3.33:
            letter_grade = "B+"
            Qualitative_feedback = "Very Good"
        elif grade_points >= 3.0:
            letter_grade = "B"
            Qualitative_feedback = "Very Good"
        elif grade_points >= 2.66:
            letter_grade = "B-"
            Qualitative_feedback = "Good"
        elif grade_points >= 2.33:
            letter_grade = "C+"
            Qualitative_feedback = "Good"
        elif grade_points >= 2.0:
            letter_grade = "C"
            Qualitative_feedback = "Good"
        elif grade_points >= 1.66:
            letter_grade = "C-"
            Qualitative_feedback = "Passable"
        elif grade_points >= 1.33:
            letter_grade = "D+"
            Qualitative_feedback = "Passable"
        elif grade_points >= 1.0:
            letter_grade = "D"
            Qualitative_feedback = "Passable"
        else:
            letter_grade = "E"
            Qualitative_feedback = "Failure"

        response = f"Your letter grade is: {letter_grade}\nQualitative feedback: {Qualitative_feedback}"
        client_socket.send(response.encode())
        print(f"Received grade points: {grade_points}")
        print(f"Letter grade sent: {letter_grade}")
        print(f"Qualitative feedback sent: {Qualitative_feedback}")

    except Exception as e:
        client_socket.send(f"Error: {e}".encode())

    client_socket.close()