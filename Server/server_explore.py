import os
import socket
import threading
from datetime import datetime

from agents.app_agent import AppAgent
from agents.explore_agent import ExploreAgent
from memory.memory_manager import Memory
from screenParser.Encoder import xmlEncoder
from utils.utils import log


class Explorer:
    def __init__(self, host='000.000.000.000', port=0, buffer_size=4096):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.log_directory = './memory'

        # Create the directory for saving received files if it doesn't exist
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

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

        log(f"Server is listening on {real_ip}:{self.port}", "red")

        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(
                client_socket, client_address))
            client_thread.start()

    def handle_client(self, client_socket, client_address):
        print(f"Connected to client: {client_address}")
        self.log_directory = './memory'
        memory = None
        explore_agent = None

        app_agent = AppAgent()
        screen_parser = xmlEncoder()
        screens = []

        screen_count = 0
        while True:
            raw_message_type = client_socket.recv(1)
            if not raw_message_type:
                log(f"Connection closed by {client_address}", 'red')
                client_socket.close()
                return

            message_type = raw_message_type.decode()

            if message_type == 'A':
                package_name = b''
                while not package_name.endswith(b'\n'):
                    package_name += client_socket.recv(1)
                package_name = package_name.decode().strip()
                log(f"package name: {package_name}", "blue" )
                app_name = app_agent.get_app_name(package_name)
                log(f"App name: {app_name}", "blue")
                if (package_name == ""):
                    log("Package name is empty", "red")
                    return

                now = datetime.now()
                # dd/mm/YY H:M:S
                dt_string = now.strftime("%Y_%m_%d %H:%M:%S")
                self.log_directory += f'/log/{app_name}/hardcode/{dt_string}/'
                screen_parser.init(self.log_directory)

                memory = Memory(app_name, "hardcode", "hardcode")
                explore_agent = ExploreAgent(memory)


            elif message_type == 'X':
                raw_xml = self.__recv_xml(client_socket, screen_count)

                parsed_xml, hierarchy_xml, encoded_xml = screen_parser.encode(raw_xml, screen_count)
                screen_count += 1
                screens.append({"parsed": parsed_xml, "hierarchy": hierarchy_xml, "encoded": encoded_xml})
                log(f"captured new screen: #{screen_count}", "green")

            elif message_type == 'S':
                file_info = b''
                while not file_info.endswith(b'\n'):
                    file_info += client_socket.recv(1)
                file_size_str = file_info.decode().strip()
                file_size = int(file_size_str)

                scr_shot_path = os.path.join(self.log_directory, "screenshots", f"{screen_count}.jpg")
                with open(scr_shot_path, 'wb') as f:
                    bytes_remaining = file_size
                    image_data = b""
                    while bytes_remaining > 0:
                        data = client_socket.recv(min(bytes_remaining, self.buffer_size))
                        image_data += data
                        bytes_remaining -= len(data)
                    f.write(image_data)

            elif message_type == 'F':
                for screen_num, screen in enumerate(screens):
                    page_index, _ = memory.search_node(screen['parsed'], screen['hierarchy'], screen['encoded'])
                    print(page_index)
                    if page_index == -1:
                        page_index, _ = explore_agent.explore(screen['parsed'], screen['hierarchy'], screen['encoded'], screen_num)
            else:
                log("unknown message type: " + message_type, "red")

    def __recv_xml(self, client_socket, screen_count):
        # Receive the file name and size
        file_info = b''
        while not file_info.endswith(b'\n'):
            file_info += client_socket.recv(1)
        file_size_str = file_info.decode().strip()
        file_size = int(file_size_str)

        raw_xml_path = os.path.join(self.log_directory, "xmls", f"{screen_count}.xml")

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
