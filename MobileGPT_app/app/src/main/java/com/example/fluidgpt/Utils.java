package com.example.fluidgpt;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Utils {
    public static int[] getBoundsInt(String stringBounds) {
        int[] bounds = new int[4];
        // Define the regular expression pattern to find integer values inside brackets
        Pattern pattern = Pattern.compile("\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]");
        Matcher matcher = pattern.matcher(stringBounds);

        if (matcher.matches()) {
            // Extract integer values from the matched groups
            bounds[0] = Integer.parseInt(matcher.group(1));
            bounds[1] = Integer.parseInt(matcher.group(2));
            bounds[2] = Integer.parseInt(matcher.group(3));
            bounds[3] = Integer.parseInt(matcher.group(4));

        } else {
            System.out.println("Invalid input format.");
        }
        return bounds;
    }
}
