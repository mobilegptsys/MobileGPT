package com.example.MobileGPT;

public class MobileGPTGlobal {
    public static final String HOST_IP = "";
    public static final int HOST_PORT = ;
    public static final String STRING_ACTION = "com.example.MobileGPT.STRING_ACTION";
    public static final String INSTRUCTION_EXTRA = "com.example.MobileGPT.INSTRUCTION_EXTRA";
    public static final String APP_NAME_EXTRA = "com.example.MobileGPT.APP_NAME_EXTRA";

    public enum step {WAIT, FINISH, QA, QACONFIRM, LEARNING, CONTINUE}
    public static final int STATE_AUTO = 0;
    public static final int STATE_CONTINUE = 1;
    public static final int STATE_FINISH = 2;
    public static final int STATE_LEARN = 3;

    private static MobileGPTGlobal sInstance = null;
    public step curStep = step.WAIT;
    public String curAction = null;


    protected MobileGPTGlobal() {
        curStep = step.WAIT;
        curAction = null;
    }

    public static synchronized MobileGPTGlobal getInstance() {
        if (sInstance == null) {
            sInstance = new MobileGPTGlobal();
        }
        return sInstance;
    }

    public static synchronized MobileGPTGlobal reset() {
        sInstance = new MobileGPTGlobal();
        return sInstance;
    }
}
