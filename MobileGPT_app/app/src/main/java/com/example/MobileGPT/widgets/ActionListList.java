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

public class ActionListList extends BaseAdapter {
    Context mContext;
    LayoutInflater mLayoutInflater;
    ArrayList<ActionListItem> items;

    public ActionListList(Context context, ArrayList<ActionListItem> items) {
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
    public ActionListItem getItem(int position) {
        return items.get(position);
    }

    @Override
    public View getView(int position, View converView, ViewGroup parent) {
        @SuppressLint("ViewHolder")
        View view = mLayoutInflater.inflate(R.layout.action_list_item, null);

        TextView actionName = (TextView)view.findViewById(R.id.action_name);
        String text = items.get(position).getDescription();
        actionName.setText(text);

        return view;
    }

}
