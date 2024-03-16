package com.example.fluidgpt;

public class FluidGlobal {
    public static final String HOST_IP = "";
    public static final int HOST_PORT = ;
    public static final String STRING_ACTION = "com.example.fluidgpt.STRING_ACTION";
    public static final String INSTRUCTION_EXTRA = "com.example.fluidgpt.INSTRUCTION_EXTRA";
    public static final String APP_NAME_EXTRA = "com.example.fluidgpt.APP_NAME_EXTRA";

    public enum step {WAIT, FINISH, QA, QACONFIRM, LEARNING, CONTINUE}
    public static final int STATE_AUTO = 0;
    public static final int STATE_CONTINUE = 1;
    public static final int STATE_FINISH = 2;
    public static final int STATE_LEARN = 3;

    private static FluidGlobal sInstance = null;
    public step curStep = step.WAIT;
    public String curAction = null;


    protected FluidGlobal() {
        curStep = step.WAIT;
        curAction = null;
    }

    public static synchronized FluidGlobal getInstance() {
        if (sInstance == null) {
            sInstance = new FluidGlobal();
        }
        return sInstance;
    }

    public static synchronized FluidGlobal reset() {
        sInstance = new FluidGlobal();
        return sInstance;
    }
}
