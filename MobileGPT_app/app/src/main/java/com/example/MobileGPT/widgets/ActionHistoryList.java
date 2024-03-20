package com.example.MobileGPT.widgets;

import android.annotation.SuppressLint;
import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;

import com.example.MobileGPT.R;

import java.util.ArrayList;
import java.util.HashMap;

public class ActionHistoryList extends BaseAdapter {
    Context mContext;
    LayoutInflater mLayoutInflater;
    ArrayList<ActionHistoryItem> items;

    public ActionHistoryList(Context context, ArrayList<ActionHistoryItem> items) {
        mContext = context;
        this.items = items;
        mLayoutInflater = LayoutInflater.from(mContext);
    }

    @Override
    public int getCount() {
        return items.size();
    }

    @Override
    public long getItemId(int position) {
        return position;
    }

    @Override
    public ActionHistoryItem getItem(int position) {
        return items.get(position);
    }

    @Override
    public View getView(int position, View converView, ViewGroup parent) {
        @SuppressLint("ViewHolder")
        View view = mLayoutInflater.inflate(R.layout.action_history_item, null);

        TextView actionName = (TextView)view.findViewById(R.id.action_name);
        String text = (position+1)+". "+items.get(position).getDescription();
        HashMap<String, String> arguments = items.get(position).getArguments();
        for (String argName : arguments.keySet()) {
            String argText = argName+": "+arguments.get(argName);
            text = text + "\n"+argText;
        }

        actionName.setText(text);

        return view;
    }

}
