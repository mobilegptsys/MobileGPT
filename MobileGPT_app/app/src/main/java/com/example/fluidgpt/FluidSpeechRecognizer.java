package com.example.fluidgpt;

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

import com.example.fluidgpt.FluidGlobal.step;

public class FluidSpeechRecognizer implements TextToSpeech.OnInitListener {
    private static final String TAG = "FLUID_SPEECH";
    private Context mContext;
    private FluidGlobal mFluidGlobal;
    private TextToSpeech mTts;
    private SpeechRecognizer speechRecognizer;
    private UtteranceProgressListener ttsListener;
    private RecognitionListener recognitionListener;
    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());
    private Runnable sttRunnable;
    private Intent sttIntent;
    public boolean sttOn = false;
    public FluidSpeechRecognizer(Context context) {
        mContext = context;
        sttOn = false;
        mTts = new TextToSpeech(mContext, this);
        mFluidGlobal = FluidGlobal.getInstance();
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
                    if (mFluidGlobal.curStep != step.WAIT && mFluidGlobal.curStep != step.LEARNING) {
                        listen();
                    }
                    message = "말하지 않음";
                }
                Log.e(TAG, "에러가 발생하였습니다. : " + message);
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
        if (mFluidGlobal.curStep == step.QACONFIRM) {
            if (result.contains("yes")) {
                mFluidGlobal.curStep = step.WAIT;
                ((FluidAccessibilityService) mContext).mAskPopUp.sendAnswer();
            } else {
                mFluidGlobal.curStep = step.QA;
                //speechRecognizer.stopListening();
                speak("please repeat your answer", true);
            }
        } else if (mFluidGlobal.curStep == step.QA) {
            ((FluidAccessibilityService) mContext).mAskPopUp.setAnswer(result);
            //speechRecognizer.stopListening();
            mFluidGlobal.curStep = step.QACONFIRM;
            speak("Did you say " + result + "?", true);
        }
//        else if (mFluidGlobal.curStep == step.CMDCONFIRM) {
//            if (result.contains("yes")) {
//                mFluidGlobal.curStep = step.WAIT;
//                Log.d(TAG, "Command is correct");

//                learnedCommand = "CORRECT";
//                mainThreadHandler.post(learningDoneRunnable);
//                screenShot(FluidGlobal.STATE_AUTO);
//            }
//            else {
//                moveBack();
//                mainThreadHandler.postDelayed(new Runnable() {
//                    @Override
//                    public void run() {
//                        startLearning();
//                    }
//                }, 3000);
//            }
//        }
    }
}


