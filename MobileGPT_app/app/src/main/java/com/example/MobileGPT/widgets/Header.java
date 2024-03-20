package com.example.MobileGPT.widgets;

import android.content.Context;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;

import com.example.MobileGPT.MobileGPTClient;
import com.example.MobileGPT.R;

public class Header {
    Context mContext;
    MobileGPTClient mClient;
    private View mHeaderOverlay;
    private TextView mHeaderField;
    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());
    private WindowManager wm;
    public Header(Context context, MobileGPTClient client){
        mContext = context;
        mClient = client;
        mHeaderOverlay = LayoutInflater.from(mContext).inflate(R.layout.header_overlay, null, false);
        mHeaderField = mHeaderOverlay.findViewById(R.id.header_title);
        wm = (WindowManager) mContext.getSystemService(Context.WINDOW_SERVICE);
    }

    public void addOverlay(String instruction) {
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                WindowManager.LayoutParams overlayLayoutParams = new WindowManager.LayoutParams(
                        WindowManager.LayoutParams.WRAP_CONTENT,
                        WindowManager.LayoutParams.WRAP_CONTENT,
                        WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                                | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE | WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                        PixelFormat.TRANSLUCENT);
                overlayLayoutParams.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
                wm.addView(mHeaderOverlay, overlayLayoutParams);
                mHeaderField.setText("GPT Running..."+instruction);
            }
        });
    }

    public void setText(String s) {
        mHeaderField.setText(s);
    }

    public void reset() {
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                try {
                    wm.removeView(mHeaderOverlay);
                } catch (IllegalArgumentException e) {

                }
            }
        });
    }
}
