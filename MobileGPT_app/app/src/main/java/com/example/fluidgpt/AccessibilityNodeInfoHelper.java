package com.example.fluidgpt;

import android.graphics.Point;
import android.graphics.Rect;
import android.view.Display;
import android.view.accessibility.AccessibilityNodeInfo;

public class AccessibilityNodeInfoHelper {
    /**
     * Returns the node's bounds clipped to the size of the display
     *
     * @param node
     * @return null if node is null, else a Rect containing visible bounds
     */
    static Rect getVisibleBoundsInScreen(AccessibilityNodeInfo node) {
        if (node == null) {
            return null;
        }
        // targeted node's bounds
        Rect nodeRect = new Rect();
        node.getBoundsInScreen(nodeRect);

//        Rect displayRect = new Rect();
//        Point outSize = new Point();
//        display.getSize(outSize);
//        displayRect.top = 0;
//        displayRect.left = 0;
//        displayRect.right = outSize.x;
//        displayRect.bottom = outSize.y;
//
//        nodeRect.intersect(displayRect);
        return nodeRect;
    }
}
