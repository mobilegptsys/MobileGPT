import json
import os
import socket
import threading

from utils.utils import log
from screenParser.Encoder import xmlEncoder
from mobilegpt import MobileGPT
from agents.app_agent import AppAgent
from agents.task_agent import TaskAgent
from datetime import datetime


class Server:
    def __init__(self, host='000.000.000.000', port=12345, buffer_size=4096):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.memory_directory = './memory'

        # Create the directory for saving received files if it doesn't exist
        if not os.path.exists(self.memory_directory):
            os.makedirs(self.memory_directory)

    def open(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Connecting to an external IP address (Google DNS in this example)
            s.connect(("8.8.8.8", 80))
            real_ip = s.getsockname()[0]
        finally:
            s.close()
    
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()

        log("--------------------------------------------------------")
        log(f"Server is listening on {real_ip}:{self.port}\nInput this IP address into the app. : [{real_ip}]", "red")

        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(
                client_socket, client_address))
            client_thread.start()

    def handle_client(self, client_socket, client_address):
        print(f"Connected to client: {client_address}")

        mobileGPT = MobileGPT(client_socket)
        app_agent = AppAgent()
        task_agent = TaskAgent()
        screen_parser = xmlEncoder()
        screen_count = 0
        log_directory = self.memory_directory

        while True:
            raw_message_type = client_socket.recv(1)

            if not raw_message_type:
                log(f"Connection closed by {client_address}", 'red')
                client_socket.close()
                return

            message_type = raw_message_type.decode()

            if message_type == 'L':
                log("App list is received", "blue")

                # Receive the string
                package_lists = b''
                while not package_lists.endswith(b'\n'):
                    package_lists += client_socket.recv(1)
                package_lists = package_lists.decode().strip()
                package_lists = package_lists.split("##")

                app_agent.update_app_list(package_lists)

            elif message_type == 'I':  # Instruction
                log("Instruction is received", "blue")
                # Receive the string
                instruction = b''
                while not instruction.endswith(b'\n'):
                    instruction += client_socket.recv(1)
                instruction = instruction.decode().strip()

                task, is_new_task = task_agent.get_task(instruction)
                target_app = task['app']
                if target_app == 'unknown' or target_app == "":
                    target_app = app_agent.predict_app(instruction)
                    task['app'] = target_app

                target_package = app_agent.get_package_name(target_app)

                now = datetime.now()
                # dd/mm/YY H:M:S
                dt_string = now.strftime("%Y_%m_%d %H:%M:%S")
                log_directory += f'/log/{target_app}/{task["name"]}/{dt_string}/'
                screen_parser.init(log_directory)

                response = "##$$##" + target_package
                client_socket.send(response.encode())
                client_socket.send("\r\n".encode())

                mobileGPT.init(instruction, task, is_new_task)

            elif message_type == 'S':
                file_info = b''
                while not file_info.endswith(b'\n'):
                    file_info += client_socket.recv(1)
                file_size_str = file_info.decode().strip()
                file_size = int(file_size_str)

                # save screenshot image
                scr_shot_path = os.path.join(log_directory, "screenshots", f"{screen_count}.jpg")
                with open(scr_shot_path, 'wb') as f:
                    bytes_remaining = file_size
                    image_data = b""
                    while bytes_remaining > 0:
                        data = client_socket.recv(min(bytes_remaining, self.buffer_size))
                        image_data += data
                        bytes_remaining -= len(data)
                    f.write(image_data)

            elif message_type == 'X':
                raw_xml = self.__recv_xml(client_socket, screen_count, log_directory)

                parsed_xml, hierarchy_xml, encoded_xml = screen_parser.encode(raw_xml, screen_count)
                screen_count += 1

                action = mobileGPT.get_next_action(parsed_xml, hierarchy_xml, encoded_xml)

                if action is not None:
                    message = json.dumps(action)
                    client_socket.send(message.encode())
                    client_socket.send("\r\n".encode())


            elif message_type == 'A':
                qa_string = b''
                while not qa_string.endswith(b'\n'):
                    qa_string += client_socket.recv(1)
                qa_string = qa_string.decode().strip()
                info_name, question, answer = qa_string.split("\\", 2)
                log(f"QA is received ({question}: {answer})", "blue")
                action = mobileGPT.set_qa_answer(info_name, question, answer)

                if action is not None:
                    message = json.dumps(action)
                    client_socket.send(message.encode())
                    client_socket.send("\r\n".encode())

    def __recv_xml(self, client_socket, screen_count, log_directory):
        # Receive the file name and size
        file_info = b''
        while not file_info.endswith(b'\n'):
            file_info += client_socket.recv(1)
        file_size_str = file_info.decode().strip()
        file_size = int(file_size_str)

        raw_xml_path = os.path.join(log_directory, "xmls", f"{screen_count}.xml")

        with open(raw_xml_path, 'w', encoding='utf-8') as f:
            bytes_remaining = file_size
            string_data = b''
            while bytes_remaining > 0:
                data = client_socket.recv(min(bytes_remaining, self.buffer_size))
                string_data += data
                bytes_remaining -= len(data)
            raw_xml = string_data.decode().strip().replace("class=\"\"", "class=\"unknown\"")
            f.write(raw_xml)
        return raw_xml
