import os, sys

os.chdir('./MobileGPT_server')
sys.path.append('.')

from MobileGPT_Server import MobileGPT_Server

os.environ["OPENAI_API_KEY"] = ""
os.environ["GOOGLESEARCH_KEY"] = ""
os.environ["PINECONE_KEY"] = ""
os.environ["PINECONE_ENVIRONMENT"] = "asia-northeast1-gcp"

os.environ["PARAMETER_FILLER_AGENT_GPT_VERSION"] = "gpt-4"
os.environ["APP_SELECT_AGENT_GPT_VERSION"] = "gpt-4"
os.environ["SELECT_AGENT_HISTORY_GPT_VERSION"] = "gpt-4"
os.environ["EXPLORE_AGENT_GPT_VERSION"] = "gpt-4"
os.environ["INFER_AGENT_GPT_VERSION"] = "gpt-4"
os.environ["SELECT_AGENT_GPT_VERSION"] = "gpt-4"
os.environ["INSTRUCTION_TRANSLATOR_AGENT_GPT_VERSION"] = "gpt-4"
os.environ["OVERLAPPING_AGENT_GPT_VERSION"] = "gpt-4"

os.environ["gpt_4"] = "gpt-4"
os.environ["gpt_4_turbo"] = "gpt-4-0125-preview"
os.environ["gpt_3_5_turbo"] = "gpt-3.5-turbo-0125"

os.environ["vision_model"] = "gpt-4-vision-preview"
os.environ["MOBILEGPT_USER_NAME"] = "Default_user"

def main():
    server_ip = sys.argv[1]
    server_port = sys.argv[2]

    server_vision = False
    if len(sys.argv) >= 4:
        server_vision = sys.argv[3]

        if server_vision == "True":
            server_vision = True

        elif server_vision == "False":
            server_vision = False

    if len(sys.argv) >= 5:
        user_name = sys.argv[4]
        os.environ["MOBILEGPT_USER_NAME"] = user_name

    mobilGPT_server = MobileGPT_Server(host=server_ip, port=int(server_port), buffer_size=4096, server_vision=server_vision)
    mobilGPT_server.server_open()

if __name__ == '__main__':
    main()
