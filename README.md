# MobileGPT
This repository is an implementation of the code for :

[MobileGPT: Augmenting LLM with Human-like App Memory for Mobile Task Automation]

For accessing the our Benchmark Dataset, you can download it from [Google Cloud](https://drive.google.com/file/d/1dmc9iHFRSD-rEiknV3R_tcihGXMsm/view?usp=sharing), 
you can check related information [About Dataset](#About-Dataset). 


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

[//]: # (If successfully installed, you should be able to execute `droidbot -h`.)

# How to use
Our MobileGPT system consists of a Python Server and an Android Client app. You need to run both the server and the client at the same time to see how it works.

Prepare IP address and appropriate port to communicate with the server in advance. The `IP`, `PORT` must be set to the same for server and client.

## MobileGPT App
+ Replace the ./MobileGPT_app/app/src/main/java/com/example/fluidgpt/FluidGlobal.java file's IP and Port. And The version of our MobileGPT's SDK must be at least 33.

```java
public static final String HOST_IP = "000.000.000.000";
public static final int HOST_PORT = 12345;

//Replace these IP and Port!
```

+ Then build the app and install it on your smartphone. After installation, run the server

## MobileGPT Server
First, You need some keys to operate the MobileGPT Server 

1. `OPENAI_API_KEY` /  [OPENAI_API](https://platform.openai.com/)
2. `GOOGLESEARCH_KEY` / [serpapi key](https://serpapi.com/integrations/python#how-to-set-serp-api-key)
3. `PINECONE_KEY` / [PINECONE](https://www.pinecone.io/)

* pinecone setting [METRIC: cosine, DIMENSIONS: 1024, POD TYPE: starter]

Input the ./MobileGPT_Main.py file's keys.

```python
os.environ["OPENAI_API_KEY"] = ""
os.environ["GOOGLESEARCH_KEY"] = ""
os.environ["PINECONE_KEY"] = ""

#Input your key!
```
After Default Setting,  you can operate the MobileGPT Server

```shell
python ./MobileGPT_Main.py <server_ip> <server_port> <using vision True or False> <Client_name>

#For example 
#python ./MobileGPT_Main.py 000.000.000.000 12345 False Default_user
```
## Run
Now you're all set. Let's run it

![Explain](https://github.com/mobile-gpt/MobileGPT/assets/152391659/1f9dd04e-da1a-40d2-80fc-b15785377d58)

1. after the server is up and running. Force stop and restart the client app.
2. Allow the Accessibility Service.
    + The first time you run the app to register a user, it will take quite a while to clean up the current app's available apps. Verify that registration is complete via a terminal on the server and move on. You may get a crash error.
   
4. Return to the app again and input the desired user Instruction in the red box.
5. then click the Blue box [Set New Instruction] button to execute it.

+ This app is a prototype for experimentation and interacting with other buttons is not recommended.
+ Unless a pop-up window pops up and asks the user for something, interacting with the screen during execution is not recommended, as it can cause errors.

# About Dataset

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

# Note

- Since MobileGPT is a research software, it may produce unexpected behavior or results (automatic payments, unsubscribing the account), so it is recommended to check its behavior carefully.
