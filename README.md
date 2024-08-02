# MobileGPT
This repository is an implementation of the code for :

[MobileGPT: Augmenting LLM with Human-like App Memory for Mobile Task Automation]

For accessing our Benchmark Dataset, you can download it from [Google Cloud](https://drive.google.com/file/d/18Te3l0VtoxsZtEQYPTUylivVSqa-WBdG/view?usp=sharing), 
you can check related information [About Dataset](#About-Dataset). 

## Abstract

> The advent of large language models (LLMs) has opened up new opportunities in the field of mobile task automation. Their superior language understanding and reasoning capabilities allow users to automate complex and repetitive tasks. However, due to the inherent unreliability and high operational cost of LLMs, their practical applicability is quite limited. To address these issues, this paper introduces MobileGPT, an innovative LLM-based mobile task automator equipped with a human-like app memory. MobileGPT emulates the cognitive process of humans interacting with a mobile app—explore, select, derive, and recall. This approach allows for a more precise and efficient learning of a task’s procedure by breaking it down into smaller, modular sub-tasks that can be re-used, re-arranged, and adapted for various objectives. We implement MobileGPT using online LLMs services (GPT-3.5 and GPT-4) and evaluate its performance on a dataset of 160 user instructions across 8 widely used mobile apps. The results indicate that MobileGPT can automate and learn new tasks with 82.5% accuracy, and is able to adapt them to different contexts with near perfect (98.75%) accuracy while reducing both latency and cost by 62.5% and 68.8%, respectively, compared to the GPT-4 powered baseline.

# Installation
Make sure you have:

1. `Python 3.12` 
2. `Android SDK >= 33`

Then clone this repo and install with `pip` about requirements.txt:

```shell
git clone https://github.com/mobile-gpt/MobileGPT.git
cd ./MobileGPT
pip install --upgrade pip
pip install -r ./requirements.txt
```

# How to use
Our MobileGPT system consists of a Python Server and an Android Client app. You need to run both the server and the client at the same time to see how it works.

Prepare IP address and appropriate port to communicate with the server in advance. The `IP`, `PORT` must be set to the same for server and client.

## MobileGPT Server (./Server/)
First, You need some keys to operate the MobileGPT Server 

1. `OPENAI_API_KEY` /  [OPENAI_API](https://platform.openai.com/)
2. `GOOGLESEARCH_KEY` / [serpapi key](https://serpapi.com/integrations/python#how-to-set-serp-api-key)


Create a .env file in the root directory and set the keys as follows:

```
OPENAI_API_KEY = "<Your Key goes here>"
GOOGLESEARCH_KEY = "<Your Key goes here>"
```

In Server/main.py file, you can modify which GPT model to use for each agent. By default all agents use gpt-4o.
```
os.environ["TASK_AGENT_GPT_VERSION"] = "gpt-4o"
os.environ["APP_AGENT_GPT_VERSION"] = "gpt-4o"
os.environ["SELECT_AGENT_HISTORY_GPT_VERSION"] = "gpt-4o"
os.environ["EXPLORE_AGENT_GPT_VERSION"] = "gpt-4o"
os.environ["SELECT_AGENT_GPT_VERSION"] = "gpt-4o"
os.environ["DERIVE_AGENT_GPT_VERSION"] = "gpt-4o"
os.environ["PARAMETER_FILLER_AGENT_GPT_VERSION"] = "gpt-4o"
os.environ["ACTION_SUMMARIZE_AGENT_GPT_VERSION"] = "gpt-4o"
os.environ["SUBTASK_MERGE_AGENT_GPT_VERSION"] = "gpt-4o"
```

Now, you can run the server by executing the following command:

```shell
cd Server
python ./main.py <server_ip> <server_port>

#For example 
#python ./main.py 000.000.000.000 12345
```

## MobileGPT Mobile App (./App/)
+ The version of our MobileGPT's SDK must be at least 33.
+ Replace the ./App/app/src/main/java/com/example/MobileGPT/MobileGPTGlobal.java file's HOST_IP address and HOST_PORT with the ip address and port of the server.


```java
// Replace with the ip address and port of the server
public static final String HOST_IP = "000.000.000.000";
public static final int HOST_PORT = 12345;
```

+ Make sure that your server is correctly running. 
+ Build the app and install it on your smartphone.


## Run
Now you're all set. Let's run it

![alt text](https://github.com/mobilegptsys/MobileGPT/blob/main/explain.png?raw=true)

0. Make sure that your server is correctly running when you first run the MobileGPT app.
1. When you first run the MobileGPT app, it will ask you to allow the Accessibility Service. 
    + Go to the settings and allow the Accessibility Service for the MobileGPT app.
    + If you don't allow the Accessibility Service, the app will not work properly.
2. If it is the first time you run the app, it will take quite a while to analyze apps installed on your device.
   + After the analysis is done, you will see the list of apps that MobileGPT can interact with.
   + For efficiency, MobileGPT fetches app information only when the Accessibility Service gets enabled.
   + If this procedure is not done properly, MobileGPT can't find any apps to interact with. If so, diable the accessibility service and re-enable it while the server is running.
   + When you install new apps, do this procedure again to reinitialize app list.

3. Return to the MobileGPT app  and input the desired user Instruction in the red box.
4. then click the Green box [Set New Instruction] button to execute it.
5. MobileGPT will automatically launch appropriate app and interact with it to complete the given instruction.

# Offline Explorer
Our open-source version of MobileGPT does not include Random Explorer. Instead, we provide an offline explorer that lets you explore app pages manually. 
+ Note that offline exploration is not mandatory. MobileGPT can explore pages on demand.
+ But offline explorer can make task execution faster.
## Server
To run offline explorer, inside Server/main.py file,
modify
``` python
mobilGPT_server = Server(host=server_ip, port=int(server_port), buffer_size=4096)
mobilGPT_server.open()
```
to
``` python
mobilGPT_explorer = Explorer(host=server_ip, port=int(server_port), buffer_size=4096)
mobilGPT_explorer.open()
```
Now, you can run the server by executing the following command:

```shell
cd Server
python ./main.py <server_ip> <server_port>

#For example 
#python ./main.py 000.000.000.000 12345
```

## App_Explorer (./App_Explorer/)
+ Replace the ./App_Explorer/app/src/main/java/com/example/hardcode/MobileGPTGlobal.java file's HOST_IP address and HOST_PORT with the ip address and port of the server.
```java
// Replace with the ip address and port of the server
public static final String HOST_IP = "000.000.000.000";
public static final int HOST_PORT = 12345;
```
+ Build and install the app on your device.

## Run
1. When you run the MobileGPT-Explorer app, you will see a green floating button on the right side of the screen. 
2. Launch the app you want to explore and press start button. 
3. Navigate the app to the page you want to explore and press the capture button. 
4. Continue navigate & capture until you are done. 
5. When you are done, press the Finish button. 
6. MobileGPT Server will analyze all captured pages and generate a memory for the app.

# Note
+ MobileGPT is a research software. It may produce unexpected behavior or results (automatic payments, unsubscribing the account), so it is recommended to check its behavior carefully.
+ The open-source version of MobileGPT does not include Human-in-the-Loop memory repair. But you can modify the memory manually in ./Server/memory/ folder.
# About Dataset
## Dataset Structure
```
Benchmark Dataset
│
<app1>
│  ├── <task1>
│  │       |── <user_instruction1.json>
│  │       |── <user_instruction2.json>
│  └── <task2>
│  │       |── <user_instruction1.json>
│  │       |── <user_instruction2.json>
│  └── ...
│  └── <task10>
│  │       |── <user_instruction1.json>
│  │       └── <user_instruction2.json>
│  │
│  └── Screenshots
│  │       |── <index.png>
│  │       └── ...
│  └── Xmls
│  │       |── <index.xml>
│  │       └── ...
│  │
<app2>
...
```
+ **BenchMark Dataset**: The top level of the dataset, containing folders for each eight application
+ 
  [YT Music, Uber Eats, Twitter, TripAdvisor, Telegram, Microsoft To-Do, Google Dialer, Gmail]

+ **App Folders**: Records of  all the screenshots and xmls parsed by MobileGPT:

    + **Task Folder**: This folder contains json for two similar instructions with two possible parameter changes. Each json stores the index of the current Step, Screenshot, and xml. It also contains a record of the action in the final infer step.

     + **Screenshot Folder**: Images captured from running the application's interface about the instruction, named sequentially indexing (e.g., `1.png`, `2.png`, etc.).

     + **Xmls Folder**: xml files detailing the structure of the application's UI for each step (e.g., `1.xml`, `2.xml`, etc.).

## JSON Structure

Each JSON file within the dataset follows the structure outlined below:

```json
{
    "instruction": "<instruction>",
    "steps": [
        {
            "step": "<step count>",
            "HTML representation": "<text representation of the screen parsed in HTML format>",
            "action": {
                "name": "<name of the action to take>",
                "args": {
                    "index": "<index of the UI on which the action needs to be performed>"
                }
            },
            "screenshot": "<screenshot file_name>",
            "xml": "<raw_xml file_name>"
        }
    ]
}
```
+ **JSON Structure Explanation**: 
    + **instruction**: Provides a natural language user instruction for the given task.
    + **steps**: Contains an array of steps to complete the instruction.
        + **step**: Indicates the step count/order.
        + **HTML representation**: Contains an array of steps to complete the instruction.
        + **action**: Contains an array of steps to complete the instruction.
            + **name**: Contains an array of steps to complete the instruction.
            + **args**: Arguments specifying additional details for the action.
        + **screenshot**: File name of the associated screenshot.
        + **xml**: File name of the associated raw XML file.
