package com.example.fluidgpt.widgets;

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

import com.example.fluidgpt.FluidAccessibilityService;
import com.example.fluidgpt.FluidClient;
import com.example.fluidgpt.R;
import com.google.android.material.floatingactionbutton.ExtendedFloatingActionButton;
import com.google.android.material.floatingactionbutton.FloatingActionButton;

import java.util.ArrayList;

public class FloatingButtonManager implements View.OnClickListener{
    public static String FLUID_TAG = "FLUID(FloatingButton)";
    private final static float CLICK_DRAG_TOLERANCE = 10; // Often, there will be a slight, unintentional, drag when the user taps the FAB, so we need to account for this.
    int initialX;
    int initialY;
    float initialTouchX;
    float initialTouchY;
    FrameLayout layout;
    private Context mContext;
    private WindowManager windowManager;
    private FluidClient mClient;
    private ExtendedFloatingActionButton mFLoatingButton;
    public ArrayList<FloatingActionButton> subFabs;
    public ArrayList<TextView> subFabsText;
    public FloatingActionButton mFinishButton, mMyselfButton, mContinueButton, mActionButton;
    private TextView mFinishText, mMyselfText, mContinueText, mActionText;
    boolean mIsAllFabsVisible = false;

    private mode curMode;
    private enum mode {AUTO, DEMO}

    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());

    @SuppressLint("ClickableViewAccessibility")
    public FloatingButtonManager(Context context, FluidClient client){
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

        mMyselfButton = (FloatingActionButton) layout.findViewById(R.id.myself_fab);
        subFabs.add(mMyselfButton);
        mMyselfText = (TextView) layout.findViewById(R.id.myself_text);
        subFabsText.add(mMyselfText);

        mActionButton = (FloatingActionButton) layout.findViewById(R.id.action_fab);
        subFabs.add(mActionButton);
        mActionText = (TextView) layout.findViewById(R.id.action_text);
        subFabsText.add(mActionText);

        mContinueButton = (FloatingActionButton) layout.findViewById(R.id.continue_fab);
        subFabs.add(mContinueButton);
        mContinueText = (TextView) layout.findViewById(R.id.continue_text);
        subFabsText.add(mContinueText);

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
                mClient.sendQuit();
                shrink();
            }
        });

        mContinueButton.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View view) {
                curMode = mode.AUTO;
                ((FluidAccessibilityService)mContext).continue_GPT();
                shrink();

            }
        });

        mMyselfButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                curMode = mode.DEMO;
                ((FluidAccessibilityService)mContext).pause();
                shrink();
            }
        });

        mActionButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                ((FluidAccessibilityService)mContext).showActions();
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

    public void setMode(int mode) {
        if (mode == 0) {
            curMode = FloatingButtonManager.mode.AUTO;
        } else {
            curMode = FloatingButtonManager.mode.DEMO;
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
            if (curMode == mode.AUTO && (fab.equals(mContinueButton) || fab.equals(mActionButton))) {
                    continue;
            }
            if (curMode == mode.DEMO && (fab.equals(mMyselfButton))) {
                continue;
            }
            fab.show();
        }
        for (TextView text : subFabsText) {
            if (curMode == mode.AUTO && (text.equals(mContinueText)|| text.equals(mActionText))) {
                continue;
            }
            if (curMode == mode.DEMO && (text.equals(mMyselfText))) {
                continue;
            }
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

    public void reset() {
        curMode = mode.AUTO;
        shrink();
    }
}
