package com.example.MobileGPT.widgets;

import com.google.gson.Gson;

import java.util.HashMap;

public class ActionHistoryItem {
    private String name;
    private String description;

    private HashMap<String, String> arguments;

    public ActionHistoryItem(String name, String description, String arguments) {
        this.name = name;
        this.description = description;

        Gson gson = new Gson();
        this.arguments = gson.fromJson(arguments, HashMap.class);
    }


    public String getName() {
        return this.name;
    }
    public String getDescription() {
        return this.description;
    }

    public HashMap<String, String> getArguments() {
        return this.arguments;
    }
}
