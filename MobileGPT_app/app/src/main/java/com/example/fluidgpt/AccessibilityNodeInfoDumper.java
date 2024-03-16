package com.example.fluidgpt;

import android.graphics.Bitmap;
import android.os.Build;
import android.os.Environment;
import android.os.SystemClock;
import android.util.Log;
import android.util.Xml;
import android.view.Display;
import android.view.accessibility.AccessibilityNodeInfo;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.StringWriter;
import java.util.HashMap;

import org.xmlpull.v1.XmlSerializer;

public class AccessibilityNodeInfoDumper {
    private static int screen_num = 0;
    private static final String TAG = "FLUID_XMLDumper";
    private static final String[] NAF_EXCLUDED_CLASSES = new String[] {
            android.widget.GridView.class.getName(), android.widget.GridLayout.class.getName(),
            android.widget.ListView.class.getName(), android.widget.TableLayout.class.getName()
    };
    /**
     * Using {@link AccessibilityNodeInfo} this method will walk the layout hierarchy
     * and generates an xml dump to the location specified by <code>dumpFile</code>
     * @param root
     */
    public static String dumpWindow(AccessibilityNodeInfo root, HashMap<Integer, AccessibilityNodeInfo> nodeMap, File baseDir) {
        if (root == null) {
            Log.d(TAG, "root is null!!!");
            return null;
        }
        final long startTime = SystemClock.uptimeMillis();
        try {
            XmlSerializer serializer = Xml.newSerializer();
            StringWriter stringWriter = new StringWriter();
            serializer.setOutput(stringWriter);
            serializer.startDocument("UTF-8", true);
            serializer.startTag("", "hierarchy");
            dumpNodeRec(root, serializer, nodeMap, nodeMap.size());
            serializer.endTag("", "hierarchy");
            serializer.endDocument();
            final long endTime = SystemClock.uptimeMillis();
            Log.w(TAG, "Fetch time: " + (endTime - startTime) + "ms");
            String xml = stringWriter.toString();
//            dumpWindowToFile(xml, baseDir);
            return xml;
        } catch (IOException e) {
            Log.e(TAG, "failed to dump window to string", e);
            return null;
        }
    }

    private static void dumpWindowToFile(String xml, File baseDir) {
        File dumpFile = new File(baseDir, screen_num+".txt");
        try {
            FileWriter writer = new FileWriter(dumpFile);
            writer.write(xml);
            writer.close();


            screen_num ++;
        } catch (IOException e) {
            Log.e(TAG, "failed to dump window to file", e);
        }
    }

    public static void saveImage(Bitmap bitmap, File baseDir) {
        File file = new File( baseDir, screen_num+".jpg");
        FileOutputStream out = null;
        try {
            out = new FileOutputStream(file);
            bitmap.compress(Bitmap.CompressFormat.JPEG, 100, out);
            out.flush();
            out.close();
        } catch (Exception e) {
            Log.e(TAG, "failed to save screenshot");
        }
    }



    private static void dumpNodeRec(AccessibilityNodeInfo node, XmlSerializer serializer,
                                    HashMap<Integer, AccessibilityNodeInfo> nodeMap, int index) throws IOException {
        nodeMap.put(index, node);
        serializer.startTag("", "node");
        if (!nafExcludedClass(node) && !nafCheck(node))
            serializer.attribute("", "NAF", Boolean.toString(true));
        serializer.attribute("", "resource-id",safeCharSeqToString(node.getViewIdResourceName()));
        serializer.attribute("", "important", Boolean.toString(node.isImportantForAccessibility()));
        serializer.attribute("", "index",Integer.toString(index));
        serializer.attribute("", "text", safeCharSeqToString(node.getText()));
        serializer.attribute("", "class", safeCharSeqToString(node.getClassName()));
        serializer.attribute("", "content-desc", safeCharSeqToString(node.getContentDescription()));
        serializer.attribute("", "checkable", Boolean.toString(node.isCheckable()));
        serializer.attribute("", "checked", Boolean.toString(node.isChecked()));
        serializer.attribute("", "clickable", Boolean.toString(node.isClickable()));
        serializer.attribute("", "enabled", Boolean.toString(node.isEnabled()));
        serializer.attribute("", "scrollable", Boolean.toString(node.isScrollable()));
        serializer.attribute("", "long-clickable", Boolean.toString(node.isLongClickable()));
        serializer.attribute("", "selected", Boolean.toString(node.isSelected()));
        serializer.attribute("", "password", Boolean.toString(node.isPassword()));
        serializer.attribute("", "bounds",
                AccessibilityNodeInfoHelper.getVisibleBoundsInScreen(node).toShortString());
        int count = node.getChildCount();
        for (int i = 0; i < count; i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                if (child.isVisibleToUser()) {
                    dumpNodeRec(child, serializer, nodeMap, nodeMap.size());
                    child.recycle();
                } else {
//                    Log.d(TAG, String.format("Skipping invisible child: %s", child.toString()));
                }
            } else {
                Log.d(TAG, String.format("Null child %d/%d, parent: %s",
                        i, count, node.toString()));
            }
        }
        serializer.endTag("", "node");
    }

    /**
     * The list of classes to exclude my not be complete. We're attempting to
     * only reduce noise from standard layout classes that may be falsely
     * configured to accept clicks and are also enabled.
     *
     * @param n
     * @return
     */
    private static boolean nafExcludedClass(AccessibilityNodeInfo n) {
        String className = safeCharSeqToString(n.getClassName());
        for(String excludedClassName : NAF_EXCLUDED_CLASSES) {
            if(className.endsWith(excludedClassName))
                return true;
        }
        return false;
    }

    /**
     * We're looking for UI controls that are enabled, clickable but have no
     * text nor content-description. Such controls configuration indicate an
     * interactive control is present in the UI and is most likely not
     * accessibility friendly. We refer to such controls here as NAF controls
     * (Not Accessibility Friendly)
     *
     * @param node
     * @return false if a node fails the check, true if all is OK
     */
    private static boolean nafCheck(AccessibilityNodeInfo node) {
        boolean isNaf = node.isClickable() && node.isEnabled()
                && safeCharSeqToString(node.getContentDescription()).isEmpty()
                && safeCharSeqToString(node.getText()).isEmpty();

        if (!isNaf)
            return true;

        // check children since sometimes the containing element is clickable
        // and NAF but a child's text or description is available. Will assume
        // such layout as fine.
        return childNafCheck(node);
    }

    /**
     * This should be used when it's already determined that the node is NAF and
     * a further check of its children is in order. A node maybe a container
     * such as LinerLayout and may be set to be clickable but have no text or
     * content description but it is counting on one of its children to fulfill
     * the requirement for being accessibility friendly by having one or more of
     * its children fill the text or content-description. Such a combination is
     * considered by this dumper as acceptable for accessibility.
     *
     * @param node
     * @return
     */
    private static boolean childNafCheck(AccessibilityNodeInfo node) {
        int childCount = node.getChildCount();
        for (int x = 0; x < childCount; x++) {
            AccessibilityNodeInfo childNode = node.getChild(x);

            if (!safeCharSeqToString(childNode.getContentDescription()).isEmpty()
                    || !safeCharSeqToString(childNode.getText()).isEmpty())
                return true;

            if (childNafCheck(childNode))
                return true;
        }
        return false;
    }

    private static String safeCharSeqToString(CharSequence cs) {
        if (cs == null)
            return "";
        else {
            return stripInvalidXMLChars(cs);
        }
    }

    private static String stripInvalidXMLChars(CharSequence cs) {
        StringBuffer ret = new StringBuffer();
        char ch;
        /* http://www.w3.org/TR/xml11/#charsets
        [#x1-#x8], [#xB-#xC], [#xE-#x1F], [#x7F-#x84], [#x86-#x9F], [#xFDD0-#xFDDF],
        [#x1FFFE-#x1FFFF], [#x2FFFE-#x2FFFF], [#x3FFFE-#x3FFFF],
        [#x4FFFE-#x4FFFF], [#x5FFFE-#x5FFFF], [#x6FFFE-#x6FFFF],
        [#x7FFFE-#x7FFFF], [#x8FFFE-#x8FFFF], [#x9FFFE-#x9FFFF],
        [#xAFFFE-#xAFFFF], [#xBFFFE-#xBFFFF], [#xCFFFE-#xCFFFF],
        [#xDFFFE-#xDFFFF], [#xEFFFE-#xEFFFF], [#xFFFFE-#xFFFFF],
        [#x10FFFE-#x10FFFF].
         */
        for (int i = 0; i < cs.length(); i++) {
            ch = cs.charAt(i);

            if((ch >= 0x1 && ch <= 0x8) || (ch >= 0xB && ch <= 0xC) || (ch >= 0xE && ch <= 0x1F) ||
                    (ch >= 0x7F && ch <= 0x84) || (ch >= 0x86 && ch <= 0x9f) ||
                    (ch >= 0xFDD0 && ch <= 0xFDDF) || (ch >= 0x1FFFE && ch <= 0x1FFFF) ||
                    (ch >= 0x2FFFE && ch <= 0x2FFFF) || (ch >= 0x3FFFE && ch <= 0x3FFFF) ||
                    (ch >= 0x4FFFE && ch <= 0x4FFFF) || (ch >= 0x5FFFE && ch <= 0x5FFFF) ||
                    (ch >= 0x6FFFE && ch <= 0x6FFFF) || (ch >= 0x7FFFE && ch <= 0x7FFFF) ||
                    (ch >= 0x8FFFE && ch <= 0x8FFFF) || (ch >= 0x9FFFE && ch <= 0x9FFFF) ||
                    (ch >= 0xAFFFE && ch <= 0xAFFFF) || (ch >= 0xBFFFE && ch <= 0xBFFFF) ||
                    (ch >= 0xCFFFE && ch <= 0xCFFFF) || (ch >= 0xDFFFE && ch <= 0xDFFFF) ||
                    (ch >= 0xEFFFE && ch <= 0xEFFFF) || (ch >= 0xFFFFE && ch <= 0xFFFFF) ||
                    (ch >= 0x10FFFE && ch <= 0x10FFFF))
                ret.append(".");
            else
                ret.append(ch);
        }
        return ret.toString();
    }


}
