package com.example.fluidgpt.response;

import android.util.Log;

import org.json.JSONException;
import org.json.JSONObject;

public class AutoGPT {
    private JSONObject response;
    private JSONObject thoughts;
    private JSONObject command;
    private JSONObject args;

    public AutoGPT(String response_string) {
        try {
//            String response_substring = response_string.substring(response_string.indexOf('\"')+1, response_string.lastIndexOf('\"'));
//            response_substring = response_substring.replace("\\\"", "\"");
            Log.d("TAG", response_string);
            response = new JSONObject(response_string);
            thoughts = (JSONObject) response.get("thoughts");
            command = (JSONObject) thoughts.get("command");
            args = (JSONObject) command.get("args");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getThoughtText() {
        try {
            return (String) thoughts.get("text");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getThoughtReasoning() {
        try {
            return (String) thoughts.get("reasoning");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getThoughtPlan() {
        try {
            return (String) thoughts.get("plan");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getThoughtCriticism() {
        try {
            return (String) thoughts.get("criticism");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getSpeak() {
        try {
            return (String) thoughts.get("speak");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public String getCommandName() {
        try {
            return (String) command.get("name");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public JSONObject getArgs() {
        return args;
    }

    public String getCompletion() {
        try {
            return (String) thoughts.get("completion");
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }
}
