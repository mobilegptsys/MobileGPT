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

public class MobileGPTSpeechRecognizer implements TextToSpeech.OnInitListener {
    private static final String TAG = "MobileGPT_SPEECH";
    private Context mContext;
    private TextToSpeech mTts;
    private UtteranceProgressListener ttsListener;
    public boolean sttOn = false;
    public MobileGPTSpeechRecognizer(Context context) {
        mContext = context;
        sttOn = false;
        mTts = new TextToSpeech(mContext, this);
        ttsListener = new UtteranceProgressListener() {
            @Override
            public void onStart(String s) {
            }
            @Override
            public void onDone(String s) {
            }

            @Override
            public void onError(String s) {
            }
        };
        mTts.setOnUtteranceProgressListener(ttsListener);
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            // Set your preferred language and other TTS settings here
            // Set language to English (US)
            mTts.setLanguage(Locale.US);
//            mTts.setLanguage(Locale.getDefault());
        } else {
            // Handle TTS initialization failure
        }
    }

    public void speak(String text, boolean needResponse) {
        mTts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
        if (needResponse)
            sttOn = true;
    }
}


