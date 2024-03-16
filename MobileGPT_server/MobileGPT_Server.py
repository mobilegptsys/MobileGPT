import json
import os, socket, threading

from utils.Utils import log
from MobileGPT_Operator import MobileGPT_Operator
from xmlEncoder.Encoder import xmlEncoder


class MobileGPT_Server:
    # host and port initialize
    def __init__(self, host='000.000.000.000', port=0, buffer_size=4096, server_vision=False):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.file_base_directory = './server_memory'

        self.is_vision = server_vision

        # Create the directory for saving received files if it doesn't exist
        if not os.path.exists(self.file_base_directory):
            os.makedirs(self.file_base_directory)

    # open the server using socket
    def server_open(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()

        print(f"Server is listening on {self.host}:{self.port}")

        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(
            client_socket, client_address))  # new user is connected -> handle client
            client_thread.start()

    # handle connected user(client)
    def handle_client(self, client_socket, client_address):
        print(f"Connected to client: {client_address}")

        mobileGPT_operator = MobileGPT_Operator(client_socket)  # main system -> MobileGPT
        xml_encoder = xmlEncoder()  # xml_encoder to transfrom HTML representation
        xml_count = 0  # check report of processing history
        file_save_directory = self.file_base_directory  # this client's base directory
        paused = False
        package_lists = None


        def operate(parsed_xml, hierarchy_xml, encoded_xml, xml_count, sub_task_finish):
            if self.is_vision:
                scr_shot_path = os.path.join(file_save_directory, "screenshots", f"{xml_count-1}.jpg")
            else:
                scr_shot_path = None

            response = mobileGPT_operator.operate(parsed_xml, hierarchy_xml, encoded_xml, scr_shot_path, sub_task_finish, self.is_vision)

            if response is not None:
                message = json.dumps(response)
                log(f"send response:{message}")
                if not paused:
                    # Send the response.
                    client_socket.send(message.encode())
                    client_socket.send("\r\n".encode())
                else:
                    log("Paused!!, not sending", "red")

        def listen_for_message():
            nonlocal mobileGPT_operator  # share client's info
            nonlocal xml_encoder
            nonlocal xml_count
            nonlocal file_save_directory
            nonlocal paused
            nonlocal package_lists

            while True:
                # Receive the message type (1 byte): 'X' for XML, 'I' for Instruction
                raw_message_type = client_socket.recv(1)

                if not raw_message_type:
                    log(f"Connection closed by {client_address}", 'red')
                    client_socket.close()
                    break

                message_type = raw_message_type.decode()

                if message_type == 'L':  # App lists
                    log("App list is recieved", "blue")
                    # Receive the string
                    package_lists = b''
                    while not package_lists.endswith(b'\n'):
                        package_lists += client_socket.recv(1)
                    package_lists = package_lists.decode().strip()
                    package_lists = package_lists.split("##")

                    mobileGPT_operator.app_select_agent.store_applist(package_lists)  # store given user's (client) applist(downloaded apps)

                elif message_type == 'I':  # Instruction
                    log("Instruction is recieved", "blue")
                    # Receive the string
                    instruction = b''
                    while not instruction.endswith(b'\n'):
                        instruction += client_socket.recv(1)
                    instruction = instruction.decode().strip()

                    known_api_list = mobileGPT_operator.api_book.api_book_data
                    generated_api = mobileGPT_operator.instruction_translator.translate(instruction, known_api_list, mobileGPT_operator.app_select_agent.applist)  # 여기서 처리

                    app = generated_api["app"]

                    if generated_api['found_match']:            #api description update
                        mobileGPT_operator.api_book.update_api_description(generated_api)
                    else:
                        app = mobileGPT_operator.app_select_agent.predict_app(instruction)

                    response = "##$$##" + app
                    client_socket.send(response.encode())
                    client_socket.send("\r\n".encode())

                    file_save_directory += f'/database/{app}/{generated_api["name"]}'

                    xml_encoder.init(file_save_directory)
                    if not os.path.exists(file_save_directory):
                        os.makedirs(file_save_directory)

                    mobileGPT_operator.init(instruction, generated_api, app)

                elif message_type == 'S':  # ScreenShot
                    log("Screenshot is recieved", "blue")
                    # Receive the file name and size
                    file_info = b''
                    while not file_info.endswith(b'\n'):
                        file_info += client_socket.recv(1)
                    file_size_str = file_info.decode().strip()
                    file_size = int(file_size_str)

                    # save screenshot image
                    scr_shot_path = os.path.join(file_save_directory, "screenshots", f"{xml_count}.jpg")
                    with open(scr_shot_path, 'wb') as f:
                        bytes_remaining = file_size
                        image_data = b""
                        while bytes_remaining > 0:
                            data = client_socket.recv(min(bytes_remaining, self.buffer_size))
                            image_data += data
                            bytes_remaining -= len(data)
                        f.write(image_data)

                elif message_type == 'X':  # XML
                    log("XML is recieved", "blue")
                    # Receive xml
                    raw_xml = self.__recv_xml(client_socket, xml_count, file_save_directory)

                    # Encode the xml.
                    parsed_xml, hierarchy_xml, encoded_xml = xml_encoder.encode(raw_xml, xml_count)
                    xml_count += 1

                    # tell MobileGPT that new screen is available
                    sub_task_finish = False
                    threading.Thread(target=operate, args=(parsed_xml, hierarchy_xml, encoded_xml, xml_count, sub_task_finish)).start()

                elif message_type == 'F':  # action finished
                    log("Sub Task Finish is recieved", "blue")
                    # Receive xml
                    raw_xml = self.__recv_xml(client_socket, xml_count, file_save_directory)

                    # Encode the xml.
                    parsed_xml, hierarchy_xml, encoded_xml = xml_encoder.encode(raw_xml, xml_count)
                    xml_count += 1

                    # tell MobileGPT that new screen is available
                    sub_task_finish = True
                    threading.Thread(target=operate, args=(parsed_xml, hierarchy_xml, encoded_xml, xml_count, sub_task_finish)).start()

                elif message_type == 'A':  # Answer to the question
                    log("Answer is recieved", "blue")
                    # Receive the string
                    answer = b''
                    while not answer.endswith(b'\n'):
                        answer += client_socket.recv(1)
                    answer = answer.decode().strip()

                    # tell GPT that new information is available
                    response = mobileGPT_operator.Answer(answer)
                    message = json.dumps(response)

                    # Send the response.
                    client_socket.send(message.encode())
                    client_socket.send("\r\n".encode())

                elif message_type == 'E':  # error message
                    log("Error is recieved", "blue")
                    # Receive the string
                    err_msg = b''
                    while not err_msg.endswith(b'\n'):
                        err_msg += client_socket.recv(1)
                    err_msg = err_msg.decode().strip()

                    # tell GPT that new information is available
                    response = mobileGPT_operator.Error(err_msg)
                    message = json.dumps(response)

                    # Send the response.
                    client_socket.send(message.encode())
                    client_socket.send("\r\n".encode())

                elif message_type == 'Q':  # force quit instruction.
                    log("Quit is recieved", "blue")
                    mobileGPT_operator.Quit()

                else:
                    print(f"Invalid message type received from {client_address}")

        threading.Thread(target=listen_for_message, args=()).start()  # handle the sended user's smartphone app's message

    def __recv_xml(self, client_socket, xml_count, file_save_directory):
        # Receive the file name and size
        file_info = b''
        while not file_info.endswith(b'\n'):
            file_info += client_socket.recv(1)
        file_size_str = file_info.decode().strip()
        file_size = int(file_size_str)

        # Save the received raw_xml file
        raw_xml_path = os.path.join(file_save_directory, "xmls", f"{xml_count}.xml")

        with open(raw_xml_path, 'w', encoding='utf-8') as f:
            bytes_remaining = file_size
            string_data = b''
            while bytes_remaining > 0:
                data = client_socket.recv(min(bytes_remaining, self.buffer_size))
                string_data += data
                bytes_remaining -= len(data)
            raw_xml = string_data.decode().strip().replace("class=\"\"","class=\"unknown\"")
            f.write(raw_xml)
        return raw_xml