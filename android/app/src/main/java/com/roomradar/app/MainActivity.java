package com.roomradar.app;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.BridgeWebViewClient;
import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Catch ANY failed page load, anywhere in the app, not just at startup
        this.bridge.getWebView().setWebViewClient(new BridgeWebViewClient(this.bridge) {
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    view.loadUrl("file:///android_asset/public/offline.html");
                } else {
                    super.onReceivedError(view, request, error);
                }
            }
        });

        // Existing startup check
        new Thread(() -> {
            boolean online = checkRealInternet();
            new Handler(Looper.getMainLooper()).post(() -> {
                if (!online && this.bridge != null && this.bridge.getWebView() != null) {
                    this.bridge.getWebView().loadUrl("file:///android_asset/public/offline.html");
                }
            });
        }).start();
    }

    private boolean checkRealInternet() {
        try {
            HttpURLConnection connection = (HttpURLConnection)
                    new URL("https://chartertechnologies.pythonanywhere.com").openConnection();
            connection.setConnectTimeout(3000);
            connection.setReadTimeout(3000);
            connection.setRequestMethod("HEAD");
            connection.connect();
            int code = connection.getResponseCode();
            return code == 200 || code == 302;
        } catch (Exception e) {
            return false;
        }
    }
}