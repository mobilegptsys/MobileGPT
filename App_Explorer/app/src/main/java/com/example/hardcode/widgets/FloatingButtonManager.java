package com.example.hardcode.widgets;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.TextView;

import com.example.hardcode.MobileGPTAccessibilityService;
import com.example.hardcode.MobileGPTClient;
import com.example.hardcode.R;
import com.google.android.material.floatingactionbutton.ExtendedFloatingActionButton;
import com.google.android.material.floatingactionbutton.FloatingActionButton;

import java.util.ArrayList;

public class FloatingButtonManager implements View.OnClickListener{
    public static String MobileGPT_TAG = "MobileGPT(FloatingButton)";
    private final static float CLICK_DRAG_TOLERANCE = 10; // Often, there will be a slight, unintentional, drag when the user taps the FAB, so we need to account for this.
    FrameLayout layout;
    private Context mContext;
    private WindowManager windowManager;
    private MobileGPTClient mClient;
    private ExtendedFloatingActionButton mFLoatingButton;
    public ArrayList<FloatingActionButton> subFabs;
    public ArrayList<TextView> subFabsText;
    public FloatingActionButton mFinishButton, mCaptureButton, mStartButton;
    private TextView mFinishText, mCaptureText, mStartText;
    boolean mIsAllFabsVisible = false;

    private mode curMode;
    private enum mode {AUTO, DEMO}

    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());

    @SuppressLint("ClickableViewAccessibility")
    public FloatingButtonManager(Context context, MobileGPTClient client){
        curMode = mode.AUTO;
        mContext = context;
        mClient = client;
        windowManager = (WindowManager) mContext.getSystemService(Context.WINDOW_SERVICE);
        layout = new FrameLayout(context);
        final WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT);
        params.gravity = Gravity.END | Gravity.CENTER_VERTICAL;

        LayoutInflater inflater = LayoutInflater.from(context);
        inflater.inflate(R.layout.floating_button, layout);
        windowManager.addView(layout, params);

        mFLoatingButton = layout.findViewById(R.id.fab);

        subFabs = new ArrayList<>();
        subFabsText = new ArrayList<>();

        mFinishButton = (FloatingActionButton) layout.findViewById(R.id.finish_fab);
        subFabs.add(mFinishButton);
        mFinishText = (TextView) layout.findViewById(R.id.finish_text);
        subFabsText.add(mFinishText);

        mCaptureButton = (FloatingActionButton) layout.findViewById(R.id.capture_fab);
        subFabs.add(mCaptureButton);
        mCaptureText = (TextView) layout.findViewById(R.id.capture_text);
        subFabsText.add(mCaptureText);

        mStartButton = (FloatingActionButton) layout.findViewById(R.id.start_fab);
        subFabs.add(mStartButton);
        mStartText = (TextView) layout.findViewById(R.id.start_text);
        subFabsText.add(mStartText);

        shrink();
        mFLoatingButton.setOnClickListener(this);
        mFLoatingButton.setOnTouchListener(new View.OnTouchListener(){
            private int initialX;
            private int initialY;
            private float initialTouchX;
            private float initialTouchY;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        initialX = params.x;
                        initialY = params.y;
                        initialTouchX = event.getRawX();
                        initialTouchY = event.getRawY();
                        return true;
                    case MotionEvent.ACTION_UP:
                        float upRawX = event.getRawX();
                        float upRawY = event.getRawY();

                        float upDX = upRawX - initialTouchX;
                        float upDY = upRawY - initialTouchY;

                        if (Math.abs(upDX) < CLICK_DRAG_TOLERANCE && Math.abs(upDY) < CLICK_DRAG_TOLERANCE) { // A click
                            return v.performClick();
                        }
                    case MotionEvent.ACTION_MOVE:
                        params.x = initialX - (int) (event.getRawX() - initialTouchX);
                        params.y = initialY + (int) (event.getRawY() - initialTouchY);
                        windowManager.updateViewLayout(layout, params);
                        return true;
                }
                return false;
            }
        });
        layout.setVisibility(View.GONE);

        mFinishButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                ((MobileGPTAccessibilityService)mContext).finish();
            }
        });

        mCaptureButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                ((MobileGPTAccessibilityService)mContext).captureScreen();

            }
        });

        mStartButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                ((MobileGPTAccessibilityService)mContext).start();
            }
        });

    }

    @Override
    public void onClick(View view) {
        if(!mIsAllFabsVisible) {
            extend();
        } else {
            shrink();
        }
    }

    public void dismiss(){
        layout.setVisibility(View.GONE);
    }

    public void show() {
        layout.setVisibility(View.VISIBLE);
    }

    private void extend() {
        for (FloatingActionButton fab : subFabs) {
            fab.show();
        }
        for (TextView text : subFabsText) {
            text.setVisibility(View.VISIBLE);
        }
        mFLoatingButton.extend();
        mIsAllFabsVisible = true;
    }
    private void shrink() {
        for (FloatingActionButton fab : subFabs) {
            fab.hide();
        }
        for (TextView text : subFabsText) {
            text.setVisibility(View.GONE);
        }
        mFLoatingButton.shrink();
        mIsAllFabsVisible = false;
    }
}
