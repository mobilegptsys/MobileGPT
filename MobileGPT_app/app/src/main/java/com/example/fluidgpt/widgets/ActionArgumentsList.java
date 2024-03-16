package com.example.fluidgpt.widgets;

import android.annotation.SuppressLint;
import android.content.Context;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.EditText;
import android.widget.TextView;

import com.example.fluidgpt.R;

import java.util.ArrayList;

public class ActionArgumentsList extends BaseAdapter {
    Context mContext;
    LayoutInflater mLayoutInflater;
    ArrayList<ActionArgumentItem> items;

    public ActionArgumentsList(Context context, ArrayList<ActionArgumentItem> items) {
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
    public ActionArgumentItem getItem(int position) {
        return items.get(position);
    }

    @Override
    public View getView(int position, View converView, ViewGroup parent) {
        @SuppressLint("ViewHolder")
        View view = mLayoutInflater.inflate(R.layout.action_arguments_item, null);

        TextView argNameView = (TextView)view.findViewById(R.id.arguments_name);
        String name = items.get(position).getName() + ": ";
        argNameView.setText(name);

        EditText argDescView = (EditText) view.findViewById(R.id.arguments_value);
        String question = items.get(position).getDescription();
        argDescView.setHint(question);

        argDescView.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void afterTextChanged(Editable s) {
                items.get(position).setValue(s.toString());
            }
        });

        return view;
    }
}
