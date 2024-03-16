package com.example.fluidgpt;

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

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Array;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import com.google.gson.Gson;

import android.view.accessibility.AccessibilityWindowInfo;

import androidx.annotation.NonNull;

import com.example.fluidgpt.widgets.ActionPopUp;
import com.example.fluidgpt.widgets.AskPopUp;
import com.example.fluidgpt.widgets.FloatingButtonManager;
import com.example.fluidgpt.widgets.Header;
import com.example.fluidgpt.response.AutoGPT;
import com.example.fluidgpt.FluidGlobal.step;
import com.google.gson.reflect.TypeToken;

public class FluidAccessibilityService extends AccessibilityService{
    private static final String TAG = "FLUID_Service";
    private WindowManager wm;
    private FluidClient mClient;

    private FluidSpeechRecognizer mSpeech;
    public FloatingButtonManager mFloatingButtonManager;
    public AskPopUp mAskPopUp;
    private Header mHeader;
    public ActionPopUp mActionPopUp;
    private FluidGlobal mFluidGlobal;
    private HashMap<Integer, AccessibilityNodeInfo> nodeMap;
    private String instruction, targetPackageName; // variables for current state.
    public boolean xmlPending, screenNeedUpdate = false;
    private Runnable screenUpdateWaitRunnable, screenUpdateTimeoutRunnable;     // Runnables for sending screen XML.
    private Runnable clickRetryRunnable, actionFailedRunnable;     // Runnables for failure handling.
    private ExecutorService mExecutorService;
    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());
    private String currentScreenXML = "";
    private Bitmap currentScreenShot = null;
    private String mLearnedCommand = "";
    private Runnable textChangeRunnable;
    private JSONObject recentCommand = new JSONObject();
    private File fileDirectory;

    private BroadcastReceiver stringReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (intent.getAction().equals(FluidGlobal.STRING_ACTION)) {
                reset();
                instruction = intent.getStringExtra(FluidGlobal.INSTRUCTION_EXTRA);
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
            if (event.getPackageName().equals("com.example.fluidgpt")) {
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
                if (screenNeedUpdate) { // if this is the first screen update since the action.
                    mainThreadHandler.removeCallbacks(clickRetryRunnable);
                    mainThreadHandler.removeCallbacks(actionFailedRunnable);
                    // no matter what, after 5s from the first screen update, we send screen XML.
                    mainThreadHandler.postDelayed(screenUpdateTimeoutRunnable, 7500);
                    screenNeedUpdate = false;

                }
                // if there is a screen update, we wait another 1 s to see if screen continues to change.
                // But we wait maximum of total 5 s (Because of screenUpdateTimeoutRunnable)
                mainThreadHandler.removeCallbacks(screenUpdateWaitRunnable);
                mainThreadHandler.postDelayed(screenUpdateWaitRunnable, 2000);

            }
        }

        if (mFluidGlobal.curStep == step.LEARNING) {
            Log.e(TAG, "Catch Event type: " + AccessibilityEvent.eventTypeToString(event.getEventType()));
            Log.e(TAG, "Catch Event Package Name : " + event.getPackageName());
            Log.e(TAG, "=========================================================================");
            if (event.getSource() != null) {

                // Log.d(TAG, "Size: " + nodeMap.size());
                if (event.getEventType() == AccessibilityEvent.TYPE_VIEW_CLICKED) {
                    // 몇몇 back button도 scroll로 인식함
                    int ti = getTargetNodeIndex(event.getSource());
                    if (ti > -1) {
                        mLearnedCommand = "click#$#" + ti;
                        Log.d(TAG, "touch 인식:" + mLearnedCommand);
                        sendDemonstration(mLearnedCommand);
                    }
                    xmlPending = true;
                }else if (event.getEventType() == AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED) {
                    mainThreadHandler.removeCallbacks(textChangeRunnable);
                    mainThreadHandler.removeCallbacks(screenUpdateWaitRunnable);
                    mainThreadHandler.removeCallbacks(screenUpdateTimeoutRunnable);

                    int ti = getTargetNodeIndex(event.getSource());

                    if (ti > -1) {
                        String text = "";
                        if (event.getText().size() > 0) {
                            text = event.getText().get(0).toString();
                        }
                        Log.d(TAG, "text 인식:"+text+" , "+ti);
                        mLearnedCommand = "input#$#" + ti + "#$#" + text;
                        mainThreadHandler.postDelayed(textChangeRunnable, 2000);
                    }
                    xmlPending = true;
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
        IntentFilter intentFilter = new IntentFilter(FluidGlobal.STRING_ACTION);
        registerReceiver(stringReceiver, intentFilter);

        wm = (WindowManager) getSystemService(WINDOW_SERVICE);

        mSpeech = new FluidSpeechRecognizer(this);
        mFloatingButtonManager = new FloatingButtonManager(this, mClient);
        mFloatingButtonManager.show();
        mAskPopUp = new AskPopUp(this, mClient, mSpeech);
        mHeader = new Header(this, mClient);
        mActionPopUp = new ActionPopUp(this, mClient);
        mFluidGlobal = FluidGlobal.getInstance();

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

        textChangeRunnable = () -> sendDemonstration(mLearnedCommand);
    }

    public void sendAnswer(String answer) {
        mClient.sendInfo(answer);
    }

    @SuppressLint("DefaultLocale")
    private void handleResponse(String message) {
        boolean action_success = true;

        Log.d(TAG, "Received message: " + message);
        try {

            // If app selection
            if (message.startsWith("##$$##")) {
                String selectedApp = message.substring((6));
                targetPackageName = selectedApp;
                fileDirectory = new File(getExternalFilesDir(null), targetPackageName);
                if (!fileDirectory.exists()) {
                    fileDirectory.mkdirs();
                }
                mExecutorService.execute(()->launchAppAndInit(selectedApp));
                mHeader.addOverlay(instruction);
                return;

            // got new action to be performed
            } else if (message.startsWith("$$##$$")) {
                String action = message.substring(6);
                mFluidGlobal.curAction = action;
                // display current action at the top of the screen.
                mainThreadHandler.post(new Runnable() {
                    @SuppressLint("SetTextI18n")
                    @Override
                    public void run() {
                        mHeader.setText(action);
                        mFloatingButtonManager.show();
                    }
                });
                return;

            // get list of actions and action history for this screen.
            } else if (message.startsWith("$####$")) {
                String msg = message.substring(6);

                String[] list = msg.split("\\$", 2);

                // use Gson to convert the json string into a list
                Gson gson = new Gson();
                ArrayList<String> action_history = new ArrayList<>();
                ArrayList<String> action_list = new ArrayList<>();

                try {
                    JSONArray jsonHistory = new JSONArray(list[0]);
                    for (int i = 0; i < jsonHistory.length(); i++) {
                        action_history.add(jsonHistory.getString(i));
                    }

                    JSONArray jsonList = new JSONArray(list[1]);
                    for (int i = 0; i < jsonList.length(); i++) {
                        action_list.add(jsonList.getString(i));
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                }

//                ArrayList<String> action_history = gson.fromJson(list[0], ArrayList.class);
//                ArrayList<String> action_list = gson.fromJson(list[1], ArrayList.class);
                mActionPopUp.setActions(action_history, action_list);
                mActionPopUp.showPopUp();
                return;

            // handle instruction finish.
            } else if (message.startsWith("$$$$$")){
                // disconnect from the server
                mClient.disconnect();
                reset();
                return;
            }else{
                // hide floating button before performing command.
                mainThreadHandler.post(new Runnable() {
                    @Override
                    public void run() {
                        mFloatingButtonManager.dismiss();
                    }
                });
            }

            // From here, Command message
            AutoGPT gpt = new AutoGPT(message);
//            GPT4 gpt = new GPT4(message);
            String thought = gpt.getThoughtReasoning();
            String command = gpt.getCommandName();
            JSONObject args = gpt.getArgs();
            int taskCompletionRate = 0;
            try {
                taskCompletionRate = Integer.parseInt(gpt.getCompletion().replace("%", ""));
            } catch (NumberFormatException e) {
                taskCompletionRate = -1;
            }


            if (command.equals("finish")) {
                finish();
                return;
            }
            if (command.equals("share")) {
                handleRead((String) args.get("information"));
                return;
            }
            mSpeech.speak(thought, false);
            if (command.equals("ask")) {

                String question = (String)args.get("question");
                String info_name = (String)args.get("needed_info_name");

                handleAsk(info_name, question);

            /* handle input */
            } else if (command.equals("click")||command.equals("input")||command.equals("scroll")||command.equals("long-click")) {
                int index = -1;
                try {
                    index = Integer.parseInt((String) (args.get("index")));     //인덱스 기져옴

                } catch (ClassCastException e) {
                    index = (Integer)args.get("index");
                }
                Log.d(TAG, "index="+index);
                AccessibilityNodeInfo targetNode = nodeMap.get(index);      //지금 화면에서의 xml을 노드 + index를 매칭 시킴 ( 있나 없나를 확인)          여기가 에러 문제 생김
                if (targetNode == null) {
                    Log.d(TAG, "nodeMap contents:");
                    for (Map.Entry<Integer, AccessibilityNodeInfo> entry : nodeMap.entrySet()) {
                        Integer key = entry.getKey();
                        AccessibilityNodeInfo value = entry.getValue();
                        String valueDescription = value.toString(); // 또는 원하는 대로 AccessibilityNodeInfo를 설명하는 다른 메서드 사용
                        Log.d(TAG, "Index: " + key + " - NodeInfo: " + valueDescription);
                    }
                    setActionFailedRunnable(String.format("There is no UI with index:%d in the screen. Double check the UI index.", index), 0);
                    return;
                }
                targetNode.refresh();

                // if targetNode's id and GPT's detection of view id mismatch, return no such UI error.   -->?
                if (args.has("id") && ((String)args.get("id")).length()>0){
                    String real_id = targetNode.getViewIdResourceName();
                    if (real_id!=null) {
                        int i = real_id.lastIndexOf("/") + 1;
                        real_id = real_id.substring(i);
                        if (!args.get("id").equals(real_id)){
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

                if (command.equals("click")) {
                    action_success = InputDispatcher.performClick(this, targetNode, false);
                    Log.d(TAG, "click success="+action_success);

                    // wait 200ms to see if click actually happened.
                    // in case click event doesn't work on target UI, explicitly make touch event on the screen.
//                    clickRetryRunnable = new Runnable() {
//                        @Override
//                        public void run() {
//                            InputDispatcher.performClick(FluidAccessibilityService.this, targetNode, true);
//                        }
//                    };
//                    mainThreadHandler.postDelayed(clickRetryRunnable, 500);
                    if (action_success) {
                        recentCommand.put("command", "click");
                    }
                } else if (command.equals("long-click")){
                    action_success = InputDispatcher.performLongcilick(targetNode);
                    Log.d(TAG, "long-click success="+action_success);

                    if (action_success) {
                        recentCommand.put("command", "long-click");
                    }
                } else if (command.equals("input")) {
                    String text = (String)(args.get("input_text"));

                    if (text.equals("ask")) { // For some reason, gpt put "ask" in the text argument...
                        handleAsk(thought, thought);
                        return;
                    }
                    ClipboardManager clipboard = (ClipboardManager) this.getSystemService(Context.CLIPBOARD_SERVICE);
                    action_success = InputDispatcher.performTextInput(this, clipboard, targetNode, text);
                    Log.d(TAG, "command success="+action_success);
                    if (!action_success) {
                        setActionFailedRunnable("Try other command.", 0);
                        return;
                    } else {
                        recentCommand.put("command", "input");
                        recentCommand.put("id", index);
                    }
                } else if (command.equals("scroll")) {
                    String direction = (String)(args.get("direction"));
                    action_success = InputDispatcher.performScroll(targetNode, direction);
                    Log.d(TAG, "command success="+action_success);
                    if (!action_success) {
                        setActionFailedRunnable("Try other command.", 0);
                        return;
                    } else {
                        recentCommand.put("command", "scroll");
                        recentCommand.put("id", index);
                        recentCommand.put("direction", direction);
                    }
                } else {
                    performGlobalAction(GLOBAL_ACTION_BACK);
                }


                if (taskCompletionRate == 100) {
                    finish();
                } else {
                    screenNeedUpdate = true;
                    xmlPending = true;
                    mFluidGlobal.curStep = step.WAIT;
                    // Set failure handler that waits 10s to see if event triggered screen change.
                    setActionFailedRunnable("There is no change in the screen. Try other approach.", 10000);
                }

//              ToDo: else if ... other input handlings.

            }
        } catch (JSONException e) {
            String error = "The command has wrong arguments. Make sure you put all arguments for the command correctly.";
            e.printStackTrace();
            mExecutorService.execute(()->mClient.sendError(error));
            Log.e(TAG, "wrong json format");
        }
    }
    private void handleAsk(String info, String question) {
        mAskPopUp.setQuestion(info, question);
        mFluidGlobal.curStep = step.QA;
        mSpeech.speak(question, true);
        mAskPopUp.showPopUp();
    }

    private void handleRead(String content) {
        mSpeech.speak(content, false);
        finish();
    }


    public int getTargetNodeIndex(AccessibilityNodeInfo src) {
        for (int i = 0; i < nodeMap.size(); i++) {
            if (src.equals(nodeMap.get(i))) {
                return i;
            }
        }

        Rect target_bounds_original = AccessibilityNodeInfoHelper.getVisibleBoundsInScreen(src);
        // UIs can get shifted up because of soft keyboard
        Rect target_bounds_shiftUp = new Rect(target_bounds_original);
        target_bounds_shiftUp.top -= 840; // Keyboard height hard-coded
        target_bounds_shiftUp.bottom -= 840; // keyboard height hard-coded
        for (int i = 0; i < nodeMap.size(); i++) {
            Rect temp_bounds = AccessibilityNodeInfoHelper.getVisibleBoundsInScreen(nodeMap.get(i));
            if (temp_bounds.toShortString().equals(target_bounds_original.toShortString())
                    || temp_bounds.toShortString().equals(target_bounds_shiftUp.toShortString())) {
                return i;
            }
        }

        return -1;
    }

    public void sendModifiedActions(String actionHistory) {
        mExecutorService.execute(()->mClient.sendModifiedActions(actionHistory));
    }

    public void pause() {
        mExecutorService.execute(()->mClient.sendPause());
        mFluidGlobal.curStep = step.LEARNING;
        screenNeedUpdate = true;
        xmlPending = true;
//        AccessibilityServiceInfo info = getServiceInfo();
//        info.eventTypes = AccessibilityEvent.TYPE_VIEW_CLICKED
//                | AccessibilityEvent.TYPE_VIEW_SELECTED
//                | AccessibilityEvent.TYPE_VIEW_SCROLLED
//                | AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED; // 특정 이벤트만 가져오기
    }

    public void continue_GPT() {
        mFluidGlobal.curStep = step.CONTINUE;
        saveCurrScreen();
        xmlPending = false;
    }

    private void finish(){
        Runnable finishRunnable = new Runnable() {
            @Override
            public void run() {
                mFluidGlobal.curStep = step.FINISH;
                saveCurrScreen();
                Log.d(TAG, "TASK IS DONE!!!");
            }
        };
        mainThreadHandler.postDelayed(finishRunnable, 1000);
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
        if (mFluidGlobal.curStep == step.WAIT) {
            screenNeedUpdate = false;
            xmlPending = false;
        }
        mainThreadHandler.postDelayed(() -> {
            saveCurrScreenXML();
            saveCurrentScreenShot();
        }, 400);
    }

    private void saveCurrentScreenShot() {
        takeScreenshot(Display.DEFAULT_DISPLAY, getMainExecutor(), new TakeScreenshotCallback() {
            @Override
            public void onSuccess(@NonNull ScreenshotResult screenshotResult) {
                Log.d(TAG, "Screen shot Success!");
                currentScreenShot = Bitmap.wrapHardwareBuffer(screenshotResult.getHardwareBuffer(),screenshotResult.getColorSpace());
                if (mFluidGlobal.curStep == step.WAIT) {
                    sendScreen(FluidGlobal.STATE_AUTO);
                } else if (mFluidGlobal.curStep == step.FINISH) {
                    sendScreen(FluidGlobal.STATE_FINISH);
                } else if (mFluidGlobal.curStep == step.LEARNING) {
                    sendScreen(FluidGlobal.STATE_LEARN);
                } else if (mFluidGlobal.curStep == step.CONTINUE) {
                    sendScreen(FluidGlobal.STATE_CONTINUE);
                }
            }

            @Override
            public void onFailure(int i) {
                Log.i(TAG,"ScreenShot onFailure code is "+ i);
            }
        });
    }

    private void saveCurrScreenXML() {
        nodeMap = new HashMap<>();
        AccessibilityNodeInfo rootNode = getRootForActiveApp();
        if (rootNode != null) {
            currentScreenXML = AccessibilityNodeInfoDumper.dumpWindow(rootNode, nodeMap, fileDirectory);
        }
    }

    private void sendDemonstration(String command) {
        mExecutorService.execute(()->mClient.sendDemonstration(command));
    }

    private void sendScreen(int state){
        mExecutorService.execute(()->mClient.sendScreenshot(currentScreenShot));
        mExecutorService.execute(()->sendXML(currentScreenXML, state));
    }

    private void sendXML(String xml, int state) {
        switch(state) {
            case FluidGlobal.STATE_AUTO:
                mClient.sendXML(xml);
                break;
            case FluidGlobal.STATE_CONTINUE:
                mClient.sendContinue(xml);
                break;
            case FluidGlobal.STATE_LEARN:
                mClient.sendPbdScreen(xml);
                break;
            case FluidGlobal.STATE_FINISH:
                mClient.sendFinish(xml);
                break;
        }
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
            if (packageInfo.packageName.equals("com.example.fluidgpt")) {
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
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                mFloatingButtonManager.dismiss();
            }
        });
        xmlPending = true;
        screenNeedUpdate = true;
        mFluidGlobal.curStep = step.WAIT;
    }

    private void reset() {
        mClient = null;
        xmlPending = screenNeedUpdate = false;
        mFluidGlobal = FluidGlobal.reset();
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                mSpeech = new FluidSpeechRecognizer(FluidAccessibilityService.this);
            }
        });

        recentCommand = new JSONObject();
        mFloatingButtonManager.reset();
        mAskPopUp.reset();
        mHeader.reset();
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
        mClient = new FluidClient(FluidGlobal.HOST_IP, FluidGlobal.HOST_PORT);
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
    public void moveBack() {
        try {
            if (recentCommand.has("command")) {
                String recentcmd = (String) recentCommand.get("command");
                Log.d(TAG, "Recent command : " + recentcmd);
                if (recentcmd.equals("click")) {
                    List<AccessibilityWindowInfo> windowInfoList = getWindows();
                    for (int k = 0; k < windowInfoList.size(); k++) {
                        if (windowInfoList.get(k).getType() == AccessibilityWindowInfo.TYPE_INPUT_METHOD) {
                            performGlobalAction(GLOBAL_ACTION_BACK);
                            break;
                        }
                    }
                    performGlobalAction(GLOBAL_ACTION_BACK);
                } else if (recentcmd.equals("scroll")) {
                    AccessibilityNodeInfo targetNode = nodeMap.get((int) recentCommand.get("id"));
                    if (targetNode == null) {
                        return;
                    }
                    String newdirection;
                    String prevdirection = (String) recentCommand.get("direction");
                    if (prevdirection.equals("up")) {
                        newdirection = "down";
                    } else if (prevdirection.equals("down")) {
                        newdirection = "up";
                    } else if (prevdirection.equals("left")) {
                        newdirection = "right";
                    } else {
                        newdirection = "left";
                    }
                    Boolean action_success = InputDispatcher.performScroll(targetNode, newdirection);
                    Log.d(TAG, "command success="+action_success);
                } else if (recentcmd.equals("input")) {
                    AccessibilityNodeInfo targetNode = nodeMap.get((int) recentCommand.get("id"));
                    if (targetNode == null) {
                        return;
                    }
                    ClipboardManager clipboard = (ClipboardManager) this.getSystemService(Context.CLIPBOARD_SERVICE);
                    Boolean action_success = InputDispatcher.performTextInput(this, clipboard, targetNode, "");
                    Log.d(TAG, "command success="+action_success);
                }
            }
        } catch (JSONException e) {
            Log.e(TAG, "Recent command error: " + e.getMessage());
        }

    }
}

