package com.example.fluidgpt;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import android.app.AlertDialog;
import android.app.UiAutomation;
import android.content.ComponentName;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.provider.Settings;
import android.util.Log;
import android.view.View;

import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;

import android.Manifest;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "FLUID(MainActivity)";
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 접근성 권한이 없으면 접근성 권한 설정하는 다이얼로그 띄워주는 부분
        if(!checkAccessibilityPermissions()) {
            Log.d(TAG, "accessibiltiy denied");
            setAccessibilityPermissions();
        }

        requestAudioPermission();

        Button instruction_button = (Button) findViewById(R.id.setinstruction_button);
        instruction_button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                setInstruction(((EditText)findViewById(R.id.instruction)).getText().toString());
            }
        });
    }

    // audio 권한
    public void requestAudioPermission() {
        if (Build.VERSION.SDK_INT >= 23) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.INTERNET, Manifest.permission.RECORD_AUDIO}, 1);
        }
    }

    // 접근성 권한이 있는지 없는지 확인하는 부분
    // 있으면 true, 없으면 false
    public boolean checkAccessibilityPermissions() {
        int accessibilityEnabled = 0;
        final String service = getPackageName() + "/" + "com.example.fluidgpt.FluidAccessibilityService";

        try {
            accessibilityEnabled = Settings.Secure.getInt(
                    getApplicationContext().getContentResolver(),
                    android.provider.Settings.Secure.ACCESSIBILITY_ENABLED);
        } catch (Settings.SettingNotFoundException e) {
            // Accessibility is not enabled
        }

        if (accessibilityEnabled == 1) {
            String settingValue = Settings.Secure.getString(
                    getApplicationContext().getContentResolver(),
                    Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
            if (settingValue != null) {
                String[] services = settingValue.split(":");
                for (String enabledService : services) {
                    if (enabledService.equalsIgnoreCase(service)) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    // 접근성 설정화면으로 넘겨주는 부분
    public void setAccessibilityPermissions() {
        AlertDialog.Builder gsDialog = new AlertDialog.Builder(this);
        gsDialog.setTitle("접근성 권한 설정");
        gsDialog.setMessage("접근성 권한을 필요로 합니다");
        gsDialog.setPositiveButton("확인", new DialogInterface.OnClickListener() {
            public void onClick(DialogInterface dialog, int which) {
                // 설정화면으로 보내는 부분
                Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
                intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(intent);
                return;
            }
        }).create().show();
    }

    public void setInstruction(String instruction) {
        Intent intent = new Intent(FluidGlobal.STRING_ACTION);
        intent.putExtra(FluidGlobal.INSTRUCTION_EXTRA, instruction);
        sendBroadcast(intent);
    }

    public void setInstruction1(View view) {
        Intent intent = new Intent(FluidGlobal.STRING_ACTION);
        intent.putExtra(FluidGlobal.INSTRUCTION_EXTRA, ((Button)view).getText().toString());
//        intent.putExtra(FluidGlobal.APP_NAME_EXTRA, "com.google.android.apps.messaging");
//        intent.putExtra(FluidGlobal.APP_NAME_EXTRA, "com.android.messaging");
        intent.putExtra(FluidGlobal.APP_NAME_EXTRA, "org.telegram.messenger");
        sendBroadcast(intent);
    }
    public void setInstruction2(View view) {
        Intent intent = new Intent(FluidGlobal.STRING_ACTION);
        intent.putExtra(FluidGlobal.INSTRUCTION_EXTRA, ((Button)view).getText().toString());
//        intent.putExtra(FluidGlobal.APP_NAME_EXTRA, "com.google.android.dialer");
        intent.putExtra(FluidGlobal.APP_NAME_EXTRA, "com.android.dialer");
        sendBroadcast(intent);
    }
    public void setInstruction3(View view) {
        Intent intent = new Intent(FluidGlobal.STRING_ACTION);
        intent.putExtra(FluidGlobal.INSTRUCTION_EXTRA, ((Button)view).getText().toString());

        intent.putExtra(FluidGlobal.APP_NAME_EXTRA, "com.coffeebeanventures.easyvoicerecorder");
//        intent.putExtra(FluidGlobal.APP_NAME_EXTRA, "com.google.android.apps.recorder");
        sendBroadcast(intent);
    }
    public void setInstruction4(View view) {
        Intent intent = new Intent(FluidGlobal.STRING_ACTION);
        intent.putExtra(FluidGlobal.INSTRUCTION_EXTRA, ((Button)view).getText().toString());
        intent.putExtra(FluidGlobal.APP_NAME_EXTRA, "com.coffeebeanventures.easyvoicerecorder");
        sendBroadcast(intent);
    }

    public void setInstruction5(View view) {
        Intent intent = new Intent(FluidGlobal.STRING_ACTION);
        intent.putExtra(FluidGlobal.INSTRUCTION_EXTRA, ((Button)view).getText().toString());
        intent.putExtra(FluidGlobal.APP_NAME_EXTRA, "com.microsoft.todos");
        sendBroadcast(intent);
    }

    public void setInstruction6(View view) {
        Intent intent = new Intent(FluidGlobal.STRING_ACTION);
        intent.putExtra(FluidGlobal.INSTRUCTION_EXTRA, ((Button)view).getText().toString());
        intent.putExtra(FluidGlobal.APP_NAME_EXTRA, "com.grabtaxi.passenger");
        sendBroadcast(intent);
    }
}