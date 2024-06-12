package com.example.MobileGPT;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.annotation.SuppressLint;
import android.content.BroadcastReceiver;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.Rect;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Display;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import android.view.accessibility.AccessibilityWindowInfo;

import androidx.annotation.NonNull;

import com.example.MobileGPT.widgets.AskPopUp;
import com.example.MobileGPT.response.GPTMessage;

public class MobileGPTAccessibilityService extends AccessibilityService{
    private static final String TAG = "MobileGPT_Service";
    private WindowManager wm;
    private MobileGPTClient mClient;
    private MobileGPTSpeechRecognizer mSpeech;
    public AskPopUp mAskPopUp;
    private MobileGPTGlobal mMobileGPTGlobal;
    private HashMap<Integer, AccessibilityNodeInfo> nodeMap;
    private String instruction, targetPackageName; // variables for current state.
    public boolean xmlPending, screenNeedUpdate, firstScreen = false;
    private Runnable screenUpdateWaitRunnable, screenUpdateTimeoutRunnable;     // Runnables for sending screen XML.
    private Runnable clickRetryRunnable, actionFailedRunnable;     // Runnables for failure handling.
    private ExecutorService mExecutorService;
    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());
    private String currentScreenXML = "";
    private Bitmap currentScreenShot = null;
    private File fileDirectory;

    private BroadcastReceiver stringReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (intent.getAction().equals(MobileGPTGlobal.STRING_ACTION)) {
                reset();
                instruction = intent.getStringExtra(MobileGPTGlobal.INSTRUCTION_EXTRA);
                Log.d(TAG, "receive broadcast");
                mExecutorService.execute(()->initNetworkConnection());

                mExecutorService.execute(()->mClient.sendInstruction(instruction));
            }
        }
    };

    // 이벤트가 발생할때마다 실행되는 부분
    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if ((event.getEventType() == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED ||
                event.getEventType() == AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED) &&
                event.getSource() != null) {
            if (event.getPackageName().equals("com.example.MobileGPT")) {
                return;
            }
//            Log.e(TAG, "Catch Event type: " + AccessibilityEvent.eventTypeToString(event.getEventType()));
//            Log.e(TAG, "Catch Event Package Name : " + event.getPackageName());
//            Log.e(TAG, "Catch Event TEXT : " + event.getText());
//            Log.e(TAG, "Catch Event ContentDescription  : " + event.getContentDescription());
//            Log.e(TAG, "Catch Event getSource : " + event.getSource());
//            Log.e(TAG, "Catch Event Type : " + event.getContentChangeTypes());
//                Log.e(TAG, "=========================================================================");
            if (xmlPending) {
                if (firstScreen && screenNeedUpdate){
                    // for First screen, we wait 5 s for loading app
                    Log.d(TAG, "first screen");
                    mainThreadHandler.postDelayed(screenUpdateTimeoutRunnable, 5000);
                    screenNeedUpdate = false;

                } else if (!firstScreen) {
                    if (screenNeedUpdate) {
                        mainThreadHandler.removeCallbacks(clickRetryRunnable);
                        mainThreadHandler.removeCallbacks(actionFailedRunnable);
                        mainThreadHandler.postDelayed(screenUpdateTimeoutRunnable, 10000);
                        screenNeedUpdate = false;
                    }
                    mainThreadHandler.removeCallbacks(screenUpdateWaitRunnable);
                    mainThreadHandler.postDelayed(screenUpdateWaitRunnable, 5000);
                }
            }
        }
    }


    // 접근성 권한을 가지고, 연결이 되면 호출되는 함수
    public void onServiceConnected() {
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();

        info.eventTypes = AccessibilityEvent.TYPES_ALL_MASK; // 전체 이벤트 가져오기
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
                | AccessibilityServiceInfo.FEEDBACK_HAPTIC;
        info.notificationTimeout = 100; // millisecond
        info.flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
                | AccessibilityServiceInfo.CAPABILITY_CAN_PERFORM_GESTURES
                | AccessibilityServiceInfo.CAPABILITY_CAN_TAKE_SCREENSHOT
                | AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
                | AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;

        // monitor every launchable package
        info.packageNames = getAppList();
        setServiceInfo(info);

        mExecutorService = Executors.newSingleThreadExecutor();
        mExecutorService.execute(this::initNetworkConnection);
        mExecutorService.execute(()->mClient.sendAppList(info.packageNames));
        mExecutorService.execute(()->mClient.disconnect());

        /* Register the BroadcastReceiver */
        IntentFilter intentFilter = new IntentFilter(MobileGPTGlobal.STRING_ACTION);
        registerReceiver(stringReceiver, intentFilter);

        wm = (WindowManager) getSystemService(WINDOW_SERVICE);

        mSpeech = new MobileGPTSpeechRecognizer(this);
        mAskPopUp = new AskPopUp(this, mClient, mSpeech);
        mMobileGPTGlobal = MobileGPTGlobal.getInstance();

        screenUpdateWaitRunnable = new Runnable() {
            @Override
            public void run() {
                Log.d(TAG, "screen update waited");
                mainThreadHandler.removeCallbacks(screenUpdateTimeoutRunnable);
                saveCurrScreen();
            }
        };

        screenUpdateTimeoutRunnable = new Runnable() {
            @Override
            public void run() {
                Log.d(TAG, "screen update timeout");
                mainThreadHandler.removeCallbacks(screenUpdateWaitRunnable);
                saveCurrScreen();
            }
        };
    }

    public void sendAnswer(String infoName, String question, String answer) {
        String QAString = infoName + "\\" + question + "\\" + answer;
        mClient.sendQA(QAString);
    }

    @SuppressLint("DefaultLocale")
    private void handleResponse(String message) {
        boolean action_success = true;

        Log.d(TAG, "Received message: " + message);

        // If app selection
        if (message.startsWith("##$$##")) {
            String selectedApp = message.substring((6));
            targetPackageName = selectedApp;
            fileDirectory = new File(getExternalFilesDir(null), targetPackageName);
            if (!fileDirectory.exists()) {
                fileDirectory.mkdirs();
            }
            mExecutorService.execute(()->launchAppAndInit(selectedApp));
            return;

        } else if (message.startsWith("$$##$$")) {
            String subtask = message.substring(6);

            return;

        } else if (message.startsWith("$$$$$")){
            // disconnect from the server
            Log.d(TAG, "-----------Task finished--------");
            mSpeech.speak("작업이 완료 되었습니다.", false);
            mClient.disconnect();
            reset();
            return;
        }

        try {
            GPTMessage gptMessage = new GPTMessage(message);
            String action = gptMessage.getActionName();
            JSONObject args = gptMessage.getArgs();

            if (action.equals("speak")) {
                String content = (String) args.get("message");
                mSpeech.speak(content, false);
                return;
            }
            else if (action.equals("ask")) {
                String question = (String)args.get("question");
                String info_name = (String)args.get("info_name");
                handleAsk(info_name, question);

            /* handle input */
            } else if (MobileGPTGlobal.AVAILABLE_ACTIONS.contains(action)){
                int index = -1;
                try {
                    index = Integer.parseInt((String) (args.get("index")));     //인덱스 기져옴

                } catch (ClassCastException e) {
                    index = (Integer)args.get("index");
                }

                AccessibilityNodeInfo targetNode = nodeMap.get(index);      //지금 화면에서의 xml을 노드 + index를 매칭 시킴 ( 있나 없나를 확인)          여기가 에러 문제 생김
                Log.d(TAG, "nodeMap contents:");
                for (Map.Entry<Integer, AccessibilityNodeInfo> entry : nodeMap.entrySet()) {
                    Integer key = entry.getKey();
                    AccessibilityNodeInfo node = entry.getValue();
//                        String valueDescription = value.toString(); // 또는 원하는 대로 AccessibilityNodeInfo를 설명하는 다른 메서드 사용
                    Rect nodeBound = new Rect();
                    node.getBoundsInScreen(nodeBound);
                    Log.d(TAG, "Index: " + key + " - Bound: ["+nodeBound.left+","+nodeBound.top+","+nodeBound.right+","+nodeBound.bottom+"]");
                }

                if (targetNode == null) {
                    Log.d(TAG, "nodeMap contents:");
                    for (Map.Entry<Integer, AccessibilityNodeInfo> entry : nodeMap.entrySet()) {
                        Integer key = entry.getKey();
                        AccessibilityNodeInfo node = entry.getValue();
//                        String valueDescription = value.toString(); // 또는 원하는 대로 AccessibilityNodeInfo를 설명하는 다른 메서드 사용
                        Rect nodeBound = new Rect();
                        node.getBoundsInScreen(nodeBound);
                        Log.d(TAG, "Index: " + key + " - Bound: ["+nodeBound.left+","+nodeBound.top+","+nodeBound.right+","+nodeBound.bottom+"]");
                    }

                    setActionFailedRunnable(String.format("There is no UI with index:%d in the screen. Double check the UI index.", index), 0);
                    return;
                }
//                targetNode.refresh();

                if (args.has("id") && !((String) args.get("id")).isEmpty()){
                    String real_id = targetNode.getViewIdResourceName();
                    if (real_id!=null) {
                        int i = real_id.lastIndexOf("/") + 1;
                        String short_id = real_id.substring(i);
                        if (!args.get("id").equals(short_id)){
                            setActionFailedRunnable(String.format("There is no UI with id:\"%s\" in the screen. Double check the UI id.",
                                    args.get("id")), 0);
                            return;
                        }
                    } else {
                        setActionFailedRunnable(String.format("There is no UI with id:\"%s\" in the screen. Double check the UI id.",
                                args.get("id")), 0);
                        return;
                    }

                }

                switch (action) {
                    case "click":
                        action_success = InputDispatcher.performClick(this, targetNode, false);
                        Log.d(TAG, "click success=" + action_success);

                        clickRetryRunnable = new Runnable() {
                            @Override
                            public void run() {
                                InputDispatcher.performClick(MobileGPTAccessibilityService.this, targetNode, true);
                            }
                        };
                        mainThreadHandler.postDelayed(clickRetryRunnable, 3000);

                        break;
                    case "long-click":
                        action_success = InputDispatcher.performLongClick(MobileGPTAccessibilityService.this, targetNode);
                        Log.d(TAG, "long-click success=" + action_success);

                        break;
                    case "input":
                        String text = (String) (args.get("input_text"));

                        ClipboardManager clipboard = (ClipboardManager) this.getSystemService(Context.CLIPBOARD_SERVICE);
                        action_success = InputDispatcher.performTextInput(this, clipboard, targetNode, text);
                        Log.d(TAG, "input success=" + action_success);

                        break;
                    case "scroll":
                        String direction = (String) (args.get("direction"));
                        action_success = InputDispatcher.performScroll(targetNode, direction);
                        Log.d(TAG, "scroll success=" + action_success);
                        break;
                    case "back":
                        performGlobalAction(GLOBAL_ACTION_BACK);
                        break;
                }

                screenNeedUpdate = true;
                xmlPending = true;
                setActionFailedRunnable("There is no change in the screen. Try other approach.", 10000);
            }
        } catch (JSONException e) {
            String error = "The action has wrong parameters. Make sure you have put all parameters correctly.";
            e.printStackTrace();
            mExecutorService.execute(()->mClient.sendError(error));
            Log.e(TAG, "wrong json format");
        }
    }
    private void handleAsk(String info, String question) {
        mAskPopUp.setQuestion(info, question);
        mSpeech.speak(question, true);
        mAskPopUp.showPopUp();
    }

    private AccessibilityNodeInfo getRootForActiveApp(){
        List<AccessibilityWindowInfo> windows = getWindows();

        for (AccessibilityWindowInfo window : windows) {
            AccessibilityNodeInfo root = window.getRoot();
            if (root.getPackageName().equals(targetPackageName)) {
                return root;
            }
        }
        Log.d(TAG, "No Appropriate Root found in this screen.");
        return null;
    }

    private void saveCurrScreen() {
        screenNeedUpdate = false;
        xmlPending = false;
        firstScreen = false;
        saveCurrScreenXML();
        saveCurrentScreenShot();
//        mainThreadHandler.postDelayed(() -> {
//            saveCurrScreenXML();
//            saveCurrentScreenShot();
//        }, 400);
    }

    private void saveCurrScreenXML() {
        nodeMap = new HashMap<>();
        Log.d(TAG, "Node Renewed!!!!!!!");
        AccessibilityNodeInfo rootNode = getRootForActiveApp();
        if (rootNode != null) {
            currentScreenXML = AccessibilityNodeInfoDumper.dumpWindow(rootNode, nodeMap, fileDirectory);
        }
    }

    private void saveCurrentScreenShot() {
        takeScreenshot(Display.DEFAULT_DISPLAY, getMainExecutor(), new TakeScreenshotCallback() {
            @Override
            public void onSuccess(@NonNull ScreenshotResult screenshotResult) {
                Log.d(TAG, "Screen shot Success!");
                currentScreenShot = Bitmap.wrapHardwareBuffer(screenshotResult.getHardwareBuffer(),screenshotResult.getColorSpace());
                sendScreen();
            }
            @Override
            public void onFailure(int i) {
                Log.i(TAG,"ScreenShot onFailure code is "+ i);
            }
        });
    }

    private void sendScreen(){
        mExecutorService.execute(()->mClient.sendScreenshot(currentScreenShot));
        mExecutorService.execute(()-> mClient.sendXML(currentScreenXML));
    }

    public void showActions() {
        // prevent sending screen due to action popup.
        xmlPending = false;
        mExecutorService.execute(()->mClient.getActions());
    }

    private void setActionFailedRunnable(String reason, int delay) {
        mainThreadHandler.removeCallbacks(actionFailedRunnable);
        actionFailedRunnable = new Runnable() {
            @Override
            public void run() {
                Log.e(TAG, reason);
                mExecutorService.execute(()->mClient.sendError(reason));
            }
        };
        mainThreadHandler.postDelayed(actionFailedRunnable, delay);
    }

    private String[] getAppList(){
        ArrayList<String> wholeAppss = new ArrayList<String>();
        final PackageManager pm = getApplicationContext().getPackageManager();
        List<ApplicationInfo> packages = pm.getInstalledApplications(PackageManager.GET_META_DATA);
        for (ApplicationInfo packageInfo : packages) {
            if (packageInfo.packageName.equals("com.example.MobileGPT")) {
                continue;
            }
            Intent launchIntent = pm.getLaunchIntentForPackage(packageInfo.packageName);
            if (launchIntent != null) {
                wholeAppss.add(packageInfo.packageName);
            }
        }

        Log.e(TAG, "# of Apps : " + wholeAppss.size());
        return wholeAppss.toArray(new String[0]);
    }

    public void launchAppAndInit(String packageName) {
        Log.d(TAG, "package name: "+packageName);
        Intent launchIntent = getPackageManager().getLaunchIntentForPackage(packageName);
        if (launchIntent != null) {
            startActivity(launchIntent);//null pointer check in case package name was not found
        } else {
            Log.d(TAG, "intent null");
        }
        xmlPending = true;
        screenNeedUpdate = true;
        firstScreen = true;
    }

    private void reset() {
        if (mClient != null) {
            mClient.disconnect();
        }
        mClient = null;
        xmlPending = screenNeedUpdate = firstScreen = false;
        mMobileGPTGlobal = MobileGPTGlobal.reset();
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                mSpeech = new MobileGPTSpeechRecognizer(MobileGPTAccessibilityService.this);
            }
        });

        if (mAskPopUp != null)
            mAskPopUp.reset();
    }

    @Override
    public void onInterrupt() {
        // TODO Auto-generated method stub
        Log.e("TEST", "OnInterrupt");
    }

    @Override
    public void onDestroy() {
        // Unregister the BroadcastReceiver
        unregisterReceiver(stringReceiver);
        mClient.disconnect();
        super.onDestroy();
    }

    private void initNetworkConnection() {
        mClient = new MobileGPTClient(MobileGPTGlobal.HOST_IP, MobileGPTGlobal.HOST_PORT);
        try {
            mClient.connect();
            mClient.receiveMessages(message -> {
                new Thread(() -> {
                    if (message!=null)
                        handleResponse(message);
                }).start();

            });

        } catch (IOException e) {
            Log.e(TAG, "server offline");
        }
    }
}

