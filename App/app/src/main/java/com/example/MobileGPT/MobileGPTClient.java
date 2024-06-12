package com.example.MobileGPT;

import android.graphics.Bitmap;
import android.util.Log;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

public class MobileGPTClient {
    private static final String TAG = "MobileGPT_CLIENT";
    private String serverAddress;
    private int serverPort;
    private Socket socket;
    private DataOutputStream dos;

    public MobileGPTClient(String serverAddress, int serverPort) {
        this.serverAddress = serverAddress;
        this.serverPort = serverPort;
    }

    public void connect() throws IOException{
        socket = new Socket(serverAddress, serverPort);
        dos = new DataOutputStream(socket.getOutputStream());
    }

    public void disconnect() {
        try {
            if (socket != null) {
                dos.close();
                socket.close();
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    public void sendAppList(String[] packages) {
        try {
            if (socket!= null) {
                dos.writeByte('L');
                dos.write((String.join("##", packages) + "\n").getBytes("UTF-8"));
                dos.flush();
            } else {
                Log.d(TAG, "socket not connected yet");
            }
        } catch (IOException e) {
            Log.e(TAG, "server offline");
        }
    }

    public void sendInstruction(String instruction) {
        try {
            if (socket!= null) {
                dos.writeByte('I');
                dos.write((instruction+"\n").getBytes("UTF-8"));
                dos.flush();
            } else {
                Log.d(TAG, "socket not connected yet");
            }
        } catch (IOException e) {
            Log.e(TAG, "server offline");
        }
    }

    public void sendScreenshot(Bitmap bitmap) {
        try {
            if (socket!=null) {
                dos.writeByte('S');

                ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
                bitmap.compress(Bitmap.CompressFormat.JPEG, 100, byteArrayOutputStream);
                byte[] byteArray = byteArrayOutputStream.toByteArray();

                int size = byteArray.length;
                String file_size = size+"\n";
                dos.write(file_size.getBytes());

                // send image
                dos.write(byteArray);
                dos.flush();

                Log.v(TAG, "screenshot sent successfully");
            }
        } catch (IOException e) {
            Log.e(TAG, "server offline");
        }
    }

    public void sendXML(String xml) {
        try {
            if (socket!= null) {
                dos.writeByte('X');
                int size = xml.getBytes("UTF-8").length;
                String file_size = size+"\n";
                dos.write(file_size.getBytes());

                // send xml
                dos.write(xml.getBytes(StandardCharsets.UTF_8));
                dos.flush();

                Log.v(TAG, "xml sent successfully");
            }
        } catch (IOException e) {
            Log.e(TAG, "server offline");
        }
    }

    public void sendQA(String QAString) {
        try {
            if (socket != null) {
                dos.writeByte('A');
                dos.write((QAString+"\n").getBytes("UTF-8"));
                dos.flush();
                Log.d(TAG, "socket not connected yet");
            } else {
                Log.d(TAG, "socket not connected yet");
            }
        } catch (IOException e) {
            Log.d(TAG, "server offline");
            Log.e(TAG, "IOException: " + e.getMessage());
        }
    }

    public void sendError(String msg) {
        try {
            if (socket != null) {
                dos.writeByte('E');
                dos.write((msg+"\n").getBytes("UTF-8"));
                dos.flush();
            } else {
                Log.d(TAG, "socket not connected yet");
            }
        } catch (IOException e) {
            Log.d(TAG, "server offline");
        }
    }

    public void getActions() {
        try {
            if (socket!=null) {
                dos.writeByte('G');
                dos.flush();
            }
        } catch (IOException e) {
            Log.e(TAG, "server offline");
        }
    }

    public void receiveMessages(OnMessageReceived onMessageReceived) {
        new Thread(() -> {
            try {
                BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                String message;
                while ((message = reader.readLine()) != null) {
                    onMessageReceived.onReceived(message);
                }
            } catch (IOException e) {

                e.printStackTrace();
            }
        }).start();
    }

    public interface OnMessageReceived {
        void onReceived(String message);
    }
}

