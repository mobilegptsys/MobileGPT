package com.example.fluidgpt;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.graphics.Path;
import android.graphics.Rect;
import android.os.Bundle;
import android.util.Log;
import android.view.accessibility.AccessibilityNodeInfo;

public class InputDispatcher {
    private static final String TAG = "FLUID_InputDispatcher";

    // callback invoked either when the gesture has been completed or cancelled
    private static AccessibilityService.GestureResultCallback callback = new AccessibilityService.GestureResultCallback() {
        @Override
        public void onCompleted(GestureDescription gestureDescription) {
            super.onCompleted(gestureDescription);
            Log.d(TAG, "gesture completed");
        }

        @Override
        public void onCancelled(GestureDescription gestureDescription) {
            super.onCancelled(gestureDescription);
            Log.d(TAG, "gesture cancelled");
        }
    };

    public static boolean performClick(AccessibilityService service, AccessibilityNodeInfo node, boolean retry) {
        // find nearest clickable ancestor.
        AccessibilityNodeInfo targetNode = nearestClickableNode(node);
        if (targetNode != null) {
            targetNode.refresh();
            Rect nodeBound = new Rect();
            targetNode.getBoundsInScreen(nodeBound);
            if (!retry)
                return targetNode.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            else
                return InputDispatcher.dispatchClick(service, (int)((nodeBound.left+nodeBound.right)/2), (int)((nodeBound.top+nodeBound.bottom)/2));
        }
        else {
            // if we can't fine any clickable button,
            Log.e(TAG, "No matching UI to click.");     //기서 문제 발생
            Rect nodeBound = new Rect();
            node.getBoundsInScreen(nodeBound);
            return InputDispatcher.dispatchClick(service, (int)((nodeBound.left+nodeBound.right)/2), (int)((nodeBound.top+nodeBound.bottom)/2));
        }
    }

    public static boolean performLongcilick(AccessibilityNodeInfo node){
        AccessibilityNodeInfo targetNode = nearestScrollalbeNode(node);
        if (targetNode!=null) {
                return targetNode.performAction(AccessibilityNodeInfo.ACTION_LONG_CLICK);
        } else {
            Log.e(TAG, "No matching UI to long-click.");
            return false;
        }
    }

    public static boolean performScroll(AccessibilityNodeInfo node, String direction) {
        AccessibilityNodeInfo targetNode = nearestScrollalbeNode(node);
        if (targetNode!=null) {
            if (direction.equals("down"))
                return targetNode.performAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD);
            else
                return targetNode.performAction(AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD);
        } else {
            Log.e(TAG, "No matching UI to scroll.");
            return false;
        }
    }
    /*
    public static boolean performScroll(AccessibilityNodeInfo node, String direction) {         // 여기 상하 좌우 추가
        AccessibilityNodeInfo targetNode = nearestScrollalbeNode(node);
        if (targetNode!=null) {
            if (direction.equals("up"))
                return targetNode.performAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_UP.getId());
            else if (direction.equals("down"))
                return targetNode.performAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_DOWN.getId());
            else if (direction.equals("left"))
                return targetNode.performAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_LEFT.getId());
            else
                return targetNode.performAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_RIGHT.getId());
        } else {
            Log.e(TAG, "No matching UI to scroll.");
            return false;
        }
    }*/

    public static boolean performTextInput(AccessibilityService service, ClipboardManager clipboard , AccessibilityNodeInfo node, String text) {
        if (node.isEditable()) {
            node.refresh();

            // clip-paste method.
//            ClipData clip = ClipData.newPlainText("label", text);
//            clipboard.setPrimaryClip(clip);
//            node.performAction(AccessibilityNodeInfo.ACTION_PASTE);

            // direct text injection method.
            Bundle arguments = new Bundle();
            arguments.putCharSequence(AccessibilityNodeInfo
                    .ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text);
            Boolean textset = node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments);

            try {
                // Add a short delay here
                Thread.sleep(100); // 100 milliseconds delay
            } catch (InterruptedException e) {
                // Handle the interruption
                Thread.currentThread().interrupt(); // Restore interrupted status
            }

            InputDispatcher.dispatchClick(service, (int)(950), (int)(2130));
            return textset;
        } else {
            return performClick(service, node, false);
        }
    }

    public static boolean dispatchClick(AccessibilityService service, float x , float y) {
        int id = service.getResources().getIdentifier("status_bar_height", "dimen", "android");
        int statusbar_height = service.getResources().getDimensionPixelSize(id);   // statisBar의 높이

        // accessibilityService: contains a reference to an accessibility service
        // callback: can be null if you don't care about gesture termination
        Log.d(TAG, String.format("Click Gesture for x=%f y=%f",x,y));
        boolean result = service.dispatchGesture(createClick(x, y), callback, null);
        Log.d(TAG, "Gesture dispatched? " + result);
        return result;

    }

    private static AccessibilityNodeInfo nearestClickableNode(AccessibilityNodeInfo node) {
        if (node == null)
            return null;

        if (node.isClickable()) {
            return node;
        } else {
            return null;
//            return nearestClickableNode(node.getParent());
        }
    }

    private static AccessibilityNodeInfo nearestScrollalbeNode(AccessibilityNodeInfo node) {
        if (node == null)
            return null;

        if (node.isScrollable()) {
            return node;
        } else {
            return nearestScrollalbeNode(node.getParent());
        }
    }

    private static GestureDescription createClick(float x, float y) {
        // for a single tap a duration of 1 ms is enough
        final int DURATION = 10;

        Path clickPath = new Path();
        clickPath.moveTo(x, y);
        GestureDescription.StrokeDescription clickStroke =
                new GestureDescription.StrokeDescription(clickPath, 0, DURATION);
        GestureDescription.Builder clickBuilder = new GestureDescription.Builder();
        clickBuilder.addStroke(clickStroke);
        return clickBuilder.build();
    }
}
