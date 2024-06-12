package com.example.hardcode.response;

import android.util.Log;

import org.json.JSONException;
import org.json.JSONObject;

public class GPTMessage {
    private JSONObject action;
    private JSONObject args;

    public GPTMessage(String response_string) {
        try {
            Log.d("TAG", response_string);
            action = new JSONObject(response_string);
            args = (JSONObject) action.get("parameters");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getActionName() {
        try {
            return (String) action.get("name");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public JSONObject getArgs() {
        return args;
    }

}
