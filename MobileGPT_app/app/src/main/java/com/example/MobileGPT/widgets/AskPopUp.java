package com.example.MobileGPT.widgets;

import android.content.Context;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import com.example.MobileGPT.MobileGPTAccessibilityService;
import com.example.MobileGPT.MobileGPTClient;
import com.example.MobileGPT.MobileGPTGlobal;
import com.example.MobileGPT.MobileGPTSpeechRecognizer;
import com.example.MobileGPT.R;

public class AskPopUp {
    private static final String TAG = "MobileGPT_ASK_POPUP";
    Context mContext;
    MobileGPTClient mClient;
    private MobileGPTSpeechRecognizer mSpeech;
    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());
    private View mAskOverlay;     // Overlay views
    private EditText mAnswerField;
    private Button mSendButton;
    private Button mMySelfButton;
    private WindowManager wm;

    private String mQuestion, mInfo;
    public AskPopUp(Context context, MobileGPTClient client, MobileGPTSpeechRecognizer speech){
        mContext = context;
        mClient = client;
        mSpeech = speech;
        wm = (WindowManager) mContext.getSystemService(Context.WINDOW_SERVICE);
        mAskOverlay = LayoutInflater.from(mContext).inflate(R.layout.ask_overlay, null, false);
        mAnswerField = mAskOverlay.findViewById(R.id.overlay_edit);
        mSendButton = mAskOverlay.findViewById(R.id.sendButton);
        mMySelfButton = mAskOverlay.findViewById(R.id.my_self);

        mSendButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // Remove the overlay view
                MobileGPTGlobal.getInstance().curStep = MobileGPTGlobal.step.WAIT;
                sendAnswer();
            }
        });
//
        mMySelfButton.setOnClickListener(new View.OnClickListener(){
            @Override
            public void onClick(View v) {
                if (mAskOverlay != null) {
                    wm.removeView(mAskOverlay);
                    // stop voice recognition
                    if (mSpeech != null) {
                        mSpeech.stopListening();
                    }
                }
                ((MobileGPTAccessibilityService)mContext).pause();
                ((MobileGPTAccessibilityService)mContext).mFloatingButtonManager.setMode(1);
                ((MobileGPTAccessibilityService)mContext).mFloatingButtonManager.show();

            }
        });
    }

    public void showPopUp() {
        // add overlay view to question user.
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                WindowManager.LayoutParams overlayLayoutParams = new WindowManager.LayoutParams(
                        WindowManager.LayoutParams.WRAP_CONTENT,
                        WindowManager.LayoutParams.WRAP_CONTENT,
                        WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                        PixelFormat.TRANSLUCENT);
                wm.addView(mAskOverlay,overlayLayoutParams);

                mAnswerField.setText("");

            }
        });
    }

    public void setQuestion(String info, String question) {
        mQuestion = question;
        mInfo = info;
        TextView text = (TextView) mAskOverlay.findViewById(R.id.overlay_text);
        text.setText(question);
    }

    public void setAnswer(String answer) {
        mAnswerField.setText(answer);
    }

    public void sendAnswer() {
        if (mAskOverlay != null) {
            String extra_info = mQuestion + "\\" + mInfo + "\\" + mAnswerField.getText().toString();
            Log.d(TAG, "send answer to gpt");
            new Thread(new Runnable() {
                @Override
                public void run() {
                    ((MobileGPTAccessibilityService) mContext).sendAnswer(extra_info);
                }
            }).start();

            wm.removeView(mAskOverlay);
            // stop voice recognition
            if (mSpeech != null) {
                mSpeech.stopListening();
            }
        }
    }

    public void reset() {
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                try {
                    wm.removeView(mAnswerField);
                } catch (IllegalArgumentException e) {

                }
            }
        });
    }
}
