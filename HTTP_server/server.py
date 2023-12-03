#Imports
import socket
import json
import random
import datetime
import hashlib
import sys

#Function to handle a POST request for user login
def handle_post(username, password, accounts_file, all_sessions, http_version):
    sessionID = random.getrandbits(64)

    if username == "" or password == "":
        print(f"SERVER LOG: {datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} LOGIN FAILED")
        return f"{http_version} 501 Not Implemented\r\n".encode('utf-8')
    if username in accounts_file:
        password_hash = hashlib.sha256((password.encode('utf-8') + accounts_file[username][1].encode('utf-8'))).hexdigest()
        if password_hash == accounts_file[username][0]: #Username and Password are valid
            session = [username, datetime.datetime.now()]
            all_sessions[sessionID] = session
            print(f"SERVER LOG: {datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} LOGIN SUCCESSFUL: {username} : {password}")
            return f"{http_version} 200 OK\r\nSet-Cookie: sessionID=0x{sessionID}\r\n\r\nLogged in!".encode('utf-8')
        else:
            print(f"SERVER LOG: {datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} LOGIN FAILED: {username} : {password}")
            return f"{http_version} 200 OK\r\nSet-Cookie: sessionID=0x{sessionID}\r\n\r\nLogin failed!".encode('utf-8')
    else:
        print(f"SERVER LOG: {datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} LOGIN FAILED: {username} : {password}")
        return f"{http_version} 200 OK\r\nSet-Cookie: sessionID=0x{sessionID}\r\n\r\nLogin failed!".encode('utf-8')
        
def file_exist(file):
    try:
        file_reader = open(file, 'r')
        file_reader.close()
        return True
    except FileNotFoundError:
        return False

#Function to handle a GET request for file downloads
def handle_get(cookie, target, session_timeout, all_sessions, root_directory, http_version):
    if cookie == "":
        print(f"SERVER LOG: {datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} COOKIE INVALID: {target}")
        return f"{http_version} 401 Unauthorized\r\n".encode('utf-8')
    
    if cookie in all_sessions:
        username = all_sessions[cookie][0]
        timestamp = all_sessions[cookie][1]
    else:
        print(f"SERVER LOG: {datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} COOKIE INVALID: {target}")
        return f"{http_version} 401 Unauthorized\r\n".encode('utf-8')

    new_timestamp = datetime.datetime.now()
    time_difference = new_timestamp - timestamp

    if time_difference.total_seconds() < int(session_timeout):
        all_sessions[cookie][1] = datetime.datetime.now()
        file = f"{root_directory}/{username}{target}"
        if file_exist(file):
            file_reader = open(file, 'r')
            print(f"SERVER LOG: {datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} GET SUCCEEDED: {username} : {target}")
            return_statement = f"{http_version} 200 OK\r\n\r\n{file_reader.read()}".encode('utf-8')
            file_reader.close()
            return return_statement
        else:
            print(f"SERVER LOG: {datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} GET FAILED: {username} : {target}")
            return f"{http_version} 404 NOT FOUND\r\n".encode('utf-8')
    else:
        print(f"SERVER LOG: {datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} SESSION EXPIRED: {username} : {target}")
        return f"{http_version} 401 Unauthorized\r\n".encode('utf-8')

def toInt(string):
    try:
        int(string)
        return True
    except ValueError:
        return False
    
#Function to start the server
def start_server(ip, port, accounts_file, session_timeout, root_directory, all_sessions):
    
    #Create and bind a TCP socket. Start listening for incoming connections.
    address = (ip, port)
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(address)
    tcp_socket.listen(1)

    while True:
        connection, _ = tcp_socket.accept()
        http_request = connection.recv(1024).decode('utf-8')

        #HERE: Extract the HTTP method, request target, and HTTP version
        lines = http_request.split('\n')
        first_line = lines[0].split(' ')
        http_method = first_line[0]
        request_target = first_line[1]
        http_version = first_line[2].strip()

        if http_method == "POST" and request_target == "/":
            #Handle POST request and send response
            username = ""
            password = ""
            for line in lines:
                if line.startswith('username'):
                    split_line = line.split(': ')
                    if len(split_line) >= 2:
                        username = (username + split_line[1]).strip()
                    else:
                        username = ""
                elif line.startswith('password'):
                    split_line = line.split(': ')
                    if len(split_line) >= 2:
                        password = (password + split_line[1]).strip()
                    else:
                        password = ""
            connection.send(handle_post(username, password, accounts_file, all_sessions, http_version))
        elif http_method == "GET":
            #Handle GET request and send response
            cookie = ""
            for line in lines:
                if line.startswith('Cookie'):
                    split_line = line.split(': sessionID=0x')
                    if len(split_line) >= 2:
                        cookie = (cookie + split_line[1]).strip()
                    else:
                        cookie = ""
            if toInt(cookie):
                connection.send(handle_get(int(cookie), request_target, session_timeout, all_sessions, root_directory, http_version))
            else:
                print(f"SERVER LOG: {datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')} COOKIE INVALID: {request_target}")
                connection.send(f"{http_version} 401 Unauthorized\r\n".encode('utf-8'))
        else:
            #Send HTTP status "501 Not Implemented"
            connection.send(f"{http_version} 501 Not Implemented\r\n".encode('utf-8'))
        connection.close()

#Function Main
def main():

    #Arguments
    ip = sys.argv[1]
    port = int(sys.argv[2])
    with open(sys.argv[3]) as json_file:
        accounts_file = json.load(json_file)
    session_timeout = sys.argv[4]
    root_directory = sys.argv[5]

    #Dictionaries
    all_sessions = {}

    start_server(ip, port, accounts_file, session_timeout, root_directory, all_sessions)

if __name__ == "__main__":
    main()
