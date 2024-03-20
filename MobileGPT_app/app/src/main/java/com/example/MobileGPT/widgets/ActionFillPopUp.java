package com.example.MobileGPT.widgets;

import android.content.Context;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.Looper;
import android.view.LayoutInflater;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.ListView;
import android.widget.TextView;

import com.example.MobileGPT.R;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.ArrayList;
import java.util.HashMap;

public class ActionFillPopUp {
    private static final String TAG = "MobileGPT_ACTION_FILL_POPUP";

    Context mContext;
    View mActionFillPopUp;
    TextView mActionDescription;
    String mActionName;
    String mActionDesc;
    ArrayList<ActionArgumentItem> mActionArgumentItems = new ArrayList<>();
    ArrayList<HashMap<String, String>> sActionHistory;
    ArrayList<ActionHistoryItem> sActionHistoryItems;
    ActionHistoryList sActionHistoryAdapter;
    private WindowManager wm;
    ListView mArgumentsListView;
    Button mCancelButton;
    Button mAddButton;
    final ActionArgumentsList mArgumentsAdapter;
    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());

    public ActionFillPopUp(Context context, ArrayList<HashMap<String, String>> actionHistory,
                           ArrayList<ActionHistoryItem> actionHistoryItems, ActionHistoryList historyAdapter) {
        mContext = context;
        sActionHistory = actionHistory;
        sActionHistoryItems = actionHistoryItems;
        sActionHistoryAdapter = historyAdapter;

        wm = (WindowManager) mContext.getSystemService(Context.WINDOW_SERVICE);
        mActionFillPopUp = LayoutInflater.from(mContext).inflate(R.layout.action_fill_overlay, null, false);
        mActionDescription = (TextView) mActionFillPopUp.findViewById(R.id.action_description);
        mCancelButton = (Button) mActionFillPopUp.findViewById(R.id.cancel);
        mAddButton = (Button) mActionFillPopUp.findViewById(R.id.add);

        mArgumentsListView = (ListView) mActionFillPopUp.findViewById(R.id.arguments_list);
        mArgumentsAdapter = new ActionArgumentsList(mContext, mActionArgumentItems);
        mArgumentsListView.setAdapter(mArgumentsAdapter);

        mCancelButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // Remove the overlay view
                dismiss();
            }
        });

        mAddButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                try {
                    HashMap<String, String> newHistory = new HashMap<>();
                    HashMap<String, String> arguments = new HashMap<>();

                    for (ActionArgumentItem arg : mActionArgumentItems) {
                        if (arg.getValue() != null) {
                            arguments.put(arg.getName(), arg.getValue());
                        }
                    }
                    newHistory.put("name", mActionName);

                    ObjectMapper objectMapper = new ObjectMapper();
                    String arg_str = objectMapper.writeValueAsString(arguments);
                    newHistory.put("arguments", arg_str);

                    sActionHistory.add(newHistory);
                    sActionHistoryItems.add(new ActionHistoryItem(mActionName, mActionDesc, arg_str));
                } catch (JsonProcessingException e) {
                    throw new RuntimeException(e);
                }
                sActionHistoryAdapter.notifyDataSetChanged();
                dismiss();
            }
        });
    }

    public void showPopUp(String actionName, String action_description){
        mActionName = actionName;
        mActionDesc = action_description;
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                mActionDescription.setText(action_description);
                WindowManager.LayoutParams overlayLayoutParams = new WindowManager.LayoutParams(
                        WindowManager.LayoutParams.WRAP_CONTENT,
                        WindowManager.LayoutParams.WRAP_CONTENT,
                        WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS ,
                        PixelFormat.TRANSLUCENT);
                wm.addView(mActionFillPopUp,overlayLayoutParams);

            }
        });
    }

    private void dismiss() {
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                wm.removeView(mActionFillPopUp);
            }
        });
    }

    public void addArgument(String argName, String argQuestion) {
        mActionArgumentItems.add(new ActionArgumentItem(argName, argQuestion));
        mainThreadHandler.post(new Runnable() {
            @Override
            public void run() {
                mArgumentsAdapter.notifyDataSetChanged();
            }
        });
    }
}
