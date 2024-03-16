package com.example.fluidgpt.widgets;

public class ActionArgumentItem {
    String name;
    String description;
    String value;

    public ActionArgumentItem(String name, String description) {
        this.name = name;
        this.description = description;
    }

    public String getName() {
        return this.name;
    }
    public String getDescription() {
        return this.description;
    }
    public void setValue(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }
}
