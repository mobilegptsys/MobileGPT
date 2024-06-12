package com.example.hardcode;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.graphics.Bitmap;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Display;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import android.view.accessibility.AccessibilityWindowInfo;

import androidx.annotation.NonNull;

import com.example.hardcode.widgets.FloatingButtonManager;

public class MobileGPTAccessibilityService extends AccessibilityService{
    private static final String TAG = "MobileGPT_Service";
    private MobileGPTClient mClient;
    public FloatingButtonManager mFloatingButtonManager;
    private HashMap<Integer, AccessibilityNodeInfo> nodeMap;
    private String targetPackageName; // variables for current state.
    private ExecutorService mExecutorService;
    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());
    private String currentScreenXML = "";
    private Bitmap currentScreenShot = null;
    private File fileDirectory;

    // 이벤트가 발생할때마다 실행되는 부분
    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event.getEventType() == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
            CharSequence packageName = event.getPackageName();
            if (!packageName.equals("com.example.hardcode")) {
                targetPackageName = packageName.toString();
            }

        }
    }


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

        mExecutorService = Executors.newSingleThreadExecutor();

        mFloatingButtonManager = new FloatingButtonManager(this, mClient);
        mFloatingButtonManager.show();
    }

    private AccessibilityNodeInfo getRootForActiveApp(){
        List<AccessibilityWindowInfo> windows = getWindows();

        for (AccessibilityWindowInfo window : windows) {
            AccessibilityNodeInfo root = window.getRoot();
            if (root != null) {
                if (root.getPackageName().equals(targetPackageName)) {
                    return root;
                }
            }
        }
        Log.d(TAG, "No Appropriate Root found in this screen.");
        return null;
    }

    public void start() {
        reset();
        mExecutorService.execute(this::initNetworkConnection);
        mExecutorService.execute(()-> mClient.sendPackageName(targetPackageName));
    }

    public void finish(){
        mExecutorService.execute(()-> mClient.sendFinish());
    }

    public void captureScreen() {
        mFloatingButtonManager.dismiss();
        saveCurrScreenXML();
        saveCurrentScreenShot();

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
                mFloatingButtonManager.show();
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

    @Override
    public void onInterrupt() {
        // TODO Auto-generated method stub
        Log.e("TEST", "OnInterrupt");
    }

    @Override
    public void onDestroy() {
        mClient.disconnect();
        mClient = null;
        super.onDestroy();
    }

    private void reset() {
        if (mClient != null) {
            mClient.disconnect();
            mClient = null;
        }
    }

    private void initNetworkConnection() {
        mClient = new MobileGPTClient(MobileGPTGlobal.HOST_IP, MobileGPTGlobal.HOST_PORT);
        try {
            mClient.connect();

        } catch (IOException e) {
            Log.e(TAG, "server offline");
        }
    }
}

