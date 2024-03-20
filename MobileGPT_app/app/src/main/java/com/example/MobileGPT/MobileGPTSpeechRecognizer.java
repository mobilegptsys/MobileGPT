package com.example.MobileGPT;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.util.Log;

import java.util.ArrayList;
import java.util.Locale;

import com.example.MobileGPT.MobileGPTGlobal.step;

public class MobileGPTSpeechRecognizer implements TextToSpeech.OnInitListener {
    private static final String TAG = "MobileGPT_SPEECH";
    private Context mContext;
    private MobileGPTGlobal mMobileGPTGlobal;
    private TextToSpeech mTts;
    private SpeechRecognizer speechRecognizer;
    private UtteranceProgressListener ttsListener;
    private RecognitionListener recognitionListener;
    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());
    private Runnable sttRunnable;
    private Intent sttIntent;
    public boolean sttOn = false;
    public MobileGPTSpeechRecognizer(Context context) {
        mContext = context;
        sttOn = false;
        mTts = new TextToSpeech(mContext, this);
        mMobileGPTGlobal = MobileGPTGlobal.getInstance();
        ttsListener = new UtteranceProgressListener() {
            @Override
            public void onStart(String s) {
            }
            @Override
            public void onDone(String s) {
                if (sttOn) {
                    listen();
                }
                sttOn = false;
            }

            @Override
            public void onError(String s) {
            }
        };

        recognitionListener = new RecognitionListener() {
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    handleSttResult(matches.get(0));
                }
            }

            @Override
            public void onError(int error) {
                String message = String.valueOf(error);

                if (error == SpeechRecognizer.ERROR_NO_MATCH){
                    if (mMobileGPTGlobal.curStep != step.WAIT && mMobileGPTGlobal.curStep != step.LEARNING) {
                        listen();
                    }
                    message = "Don't Speak";
                }
                Log.e(TAG, "Error is occurred : " + message);
            }
            @Override
            public void onReadyForSpeech(Bundle bundle) {
            }
            @Override
            public void onBeginningOfSpeech() {
            }
            @Override
            public void onRmsChanged(float v) {
            }
            @Override
            public void onBufferReceived(byte[] bytes) {
            }
            @Override
            public void onEndOfSpeech() {
            }
            @Override
            public void onPartialResults(Bundle partialResults) {
            }
            @Override
            public void onEvent(int eventType, Bundle params) {
            }
        };

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(mContext);
        speechRecognizer.setRecognitionListener(recognitionListener);

        sttIntent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        sttIntent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        sttIntent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-US");

        // for STT
        mTts.setOnUtteranceProgressListener(ttsListener);
        sttRunnable = new Runnable() {
            @Override
            public void run() {
                speechRecognizer.startListening(sttIntent);
                Log.d(TAG, "START LISTENING");
            }
        };

    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            // Set your preferred language and other TTS settings here
            mTts.setLanguage(Locale.getDefault());
        } else {
            // Handle TTS initialization failure
        }
    }

    public void speak(String text, boolean needResponse) {
        mTts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
        if (needResponse)
            sttOn = true;
    }

    public void listen() {
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                speechRecognizer.startListening(sttIntent);
            }
        });
    }

    public void stopListening() {
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                speechRecognizer.stopListening();
            }
        });

    }

    private void handleSttResult(String result) {
        Log.d(TAG, result);
        if (mMobileGPTGlobal.curStep == step.QACONFIRM) {
            if (result.contains("yes")) {
                mMobileGPTGlobal.curStep = step.WAIT;
                ((MobileGPTAccessibilityService) mContext).mAskPopUp.sendAnswer();
            } else {
                mMobileGPTGlobal.curStep = step.QA;
                //speechRecognizer.stopListening();
                speak("please repeat your answer", true);
            }
        } else if (mMobileGPTGlobal.curStep == step.QA) {
            ((MobileGPTAccessibilityService) mContext).mAskPopUp.setAnswer(result);
            //speechRecognizer.stopListening();
            mMobileGPTGlobal.curStep = step.QACONFIRM;
            speak("Did you say " + result + "?", true);
        }
    }
}


