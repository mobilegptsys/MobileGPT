package com.example.MobileGPT.widgets;

import android.content.Context;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.WindowManager;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.ListView;

import com.example.MobileGPT.MobileGPTAccessibilityService;
import com.example.MobileGPT.MobileGPTClient;
import com.example.MobileGPT.R;

import java.util.ArrayList;
import java.util.HashMap;

import com.google.gson.Gson;

public class ActionPopUp {
    private static final String TAG = "MobileGPT_ACTION_POPUP";
    Context mContext;
    MobileGPTClient mClient;

    ArrayList<HashMap<String, String>> mActionHistory;
    ArrayList<HashMap<String, String>> mActionList;
    ArrayList<ActionListItem> mActionListItems = new ArrayList<>();
    ArrayList<ActionHistoryItem> mActionHistoryItems = new ArrayList<>();
    View mActionPopUp;
    ActionFillPopUp mActionFillPopUp;
    Button mDoneButton;
    ListView mActionHistoryView;
    ListView mActionListView;
    private WindowManager wm;
    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());
    final ActionHistoryList mHistoryAdapter;
    final ActionListList mListAdapter;

    public ActionPopUp(Context context, MobileGPTClient client) {
        mContext = context;
        mClient = client;
        wm = (WindowManager) mContext.getSystemService(Context.WINDOW_SERVICE);

        mActionPopUp = LayoutInflater.from(mContext).inflate(R.layout.action_overlay, null, false);

        mActionHistoryView = (ListView) mActionPopUp.findViewById(R.id.action_history);
        mActionListView = (ListView) mActionPopUp.findViewById(R.id.action_list);

        mHistoryAdapter = new ActionHistoryList(mContext, mActionHistoryItems);
        mActionHistoryView.setAdapter(mHistoryAdapter);

        mListAdapter = new ActionListList(mContext, mActionListItems);
        mActionListView.setAdapter(mListAdapter);


        mActionHistoryView.setOnItemClickListener(new AdapterView.OnItemClickListener(){

            @Override
            public void onItemClick(AdapterView<?> adapterView, View view, int position, long l) {
                Log.d(TAG, "item clicked! position: "+position);
                mActionHistory.remove(position);
                mActionHistoryItems.remove(position);

                mHistoryAdapter.notifyDataSetChanged();
            }
        });

        mActionListView.setOnItemClickListener(new AdapterView.OnItemClickListener(){

            @Override
            public void onItemClick(AdapterView<?> adapterView, View view, int position, long l) {
                Log.d(TAG, "item clicked! position: "+position);
                ActionListItem action = mActionListItems.get(position);
                String name = action.getName();
                String description = action.getDescription();
                HashMap<String, String> arguments = action.getArguments();
                if (!arguments.isEmpty()) {
                    for (String argName : arguments.keySet()) {
                        mActionFillPopUp = new ActionFillPopUp(mContext, mActionHistory, mActionHistoryItems, mHistoryAdapter);
                        mActionFillPopUp.addArgument(argName, arguments.get(argName));
                    }
                    mActionFillPopUp.showPopUp(name, description);
                } else {
                    HashMap<String, String> newHistory = new HashMap<>();
                    newHistory.put("name", name);
                    newHistory.put("arguments","{}");
                    mActionHistory.add(newHistory);
                    mActionHistoryItems.add(new ActionHistoryItem(name, description, "{}"));
                    mHistoryAdapter.notifyDataSetChanged();
                }
            }
        });

        mDoneButton = (Button) mActionPopUp.findViewById(R.id.done);
        mDoneButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // Remove the overlay view
                sendModifiedAction();
            }
        });

    }

    public void showPopUp(){
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                WindowManager.LayoutParams overlayLayoutParams = new WindowManager.LayoutParams(
                        WindowManager.LayoutParams.WRAP_CONTENT,
                        WindowManager.LayoutParams.WRAP_CONTENT,
                        WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS ,
                        PixelFormat.TRANSLUCENT);
                wm.addView(mActionPopUp,overlayLayoutParams);

            }
        });
    }

    public void setActions(ArrayList<String> actionHistory, ArrayList<String>  actionList) {
        mActionHistory = new ArrayList<>();
        mActionList = new ArrayList<>();
        mActionListItems.clear();
        mActionHistoryItems.clear();

        HashMap<String, String> actionToDescription = new HashMap<>();

        Gson gson = new Gson();
        for (String action_str : actionList) {
            HashMap<String, String> action = gson.fromJson(action_str, HashMap.class);
            String name = action.get("name");
            String description = action.get("description");
            String arguments = action.get("parameters");

            actionToDescription.put(name, description);

            mActionList.add(action);
            mActionListItems.add(new ActionListItem(name, description, arguments));
        }

        for (String action_str : actionHistory) {
            HashMap<String, String> action = gson.fromJson(action_str, HashMap.class);
            String name = action.get("name");
            String description = actionToDescription.get(name);
            String arguments = action.get("arguments");

            mActionHistory.add(action);
            mActionHistoryItems.add(new ActionHistoryItem(name, description, arguments));
        }

        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                mHistoryAdapter.notifyDataSetChanged();
                mListAdapter.notifyDataSetChanged();
            }
        });
    }

    public void sendModifiedAction() {
        Gson gson = new Gson();
        String actionHistory = gson.toJson(mActionHistory);
        Log.d(TAG, actionHistory);
        ((MobileGPTAccessibilityService)mContext).sendModifiedActions(actionHistory);
        new Thread(new Runnable() {
            @Override
            public void run() {
                mClient.sendModifiedActions(actionHistory);
            }
        }).start();

        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                wm.removeView(mActionPopUp);
                Log.d(TAG, "remove action popup");
            }
        });
    }
}
