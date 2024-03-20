package com.example.MobileGPT.response;

import android.accessibilityservice.AccessibilityService;

import org.json.JSONException;
import org.json.JSONObject;


public class GPT4 {
    private static final String TAG = "MobileGPT(GPT4)";
    private JSONObject response;
    private JSONObject prediction;
    private JSONObject args;

    private AccessibilityService service;

    public GPT4(String response_string) {
        this.service = service;
        try {
            response = new JSONObject(response_string);
            prediction = (JSONObject) response.get("Prediction");
            args = (JSONObject) prediction.get("args");

        } catch (JSONException e) {
            throw new RuntimeException(e);
        }

    }

    public String getPredictionAction() {
        try {
            return (String) prediction.get("action");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getCommandName() {
        try {
            return (String) prediction.get("command");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public JSONObject getArgs() {
        return args;
    }

    public String getDescription() {
        try {
            return (String) response.get("Description");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getCompletion() {
        try {
            return (String) response.get("Completion");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getReasoning() {
        try {
            return (String) response.get("Reasoning");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getSpeak() {
        try {
            return (String) response.get("Speak");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }
}
