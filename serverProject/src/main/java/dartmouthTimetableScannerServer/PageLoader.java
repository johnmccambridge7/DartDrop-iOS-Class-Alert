package dartmouthTimetableScannerServer;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.FileReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Map;
import java.lang.reflect.Type;
import java.lang.ClassLoader;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import org.apache.commons.io.IOUtils;

/**
 * Fetches page with full course listing from Dartmouth Timetable site
 * (https://oracle-www.dartmouth.edu/dart/groucho/timetable.main)
 * 
 * @author Jai Smith
 */
public class PageLoader extends Thread {
    private String page;
    private App caller;
    private String threadName;

    public PageLoader(App caller, String threadName) {
        this.caller = caller;
        this.threadName = threadName;
    }

    public void run() {
        // System.out.printf("[%s] run() called\n", threadName);

        try {
            requestPage();
        } catch(Exception e) {
            System.out.printf("[%s] Error loading page: %s\n", threadName, e);
        }

        caller.reportUpdate();
    }

    private void requestPage() throws Exception {
        // System.out.printf("[%s] Loading parameters...\n", threadName);

        ClassLoader classLoader = this.getClass().getClassLoader();
        BufferedReader parametersFile = new BufferedReader(new InputStreamReader(
            classLoader.getResourceAsStream("post_parameters.json")));
        Type type = new TypeToken<Map<String, Map<String, String>>>(){}.getType();
        Map<String, Map<String, String>> parameters =  new Gson().fromJson(parametersFile, type);

        // System.out.printf("[%s] Parameters loaded\n", threadName);

        URL url = null;
        HttpURLConnection connection = null;
        String response = null;

        try {
            System.out.printf("[%s] Opening connection...\n", threadName);
            url = new URL("https://oracle-www.dartmouth.edu/dart/groucho/timetable.display_courses");
            connection = (HttpURLConnection) url.openConnection();
            
            System.out.printf("[%s] Setting parameters...\n", threadName);

            for(String header : parameters.get("headers").keySet()) {
                connection.setRequestProperty(header, parameters.get("headers").get(header));
            }
            System.out.printf("[%s] Headers set successfully\n", threadName);

            connection.setRequestMethod("GET");
            connection.setDoOutput(true);

            DataOutputStream out = new DataOutputStream(connection.getOutputStream());
            out.writeBytes(parameterBuilder(parameters.get("data")));
            out.flush();
            out.close();
            System.out.printf("[%s] Data set successfully\n", threadName);

            System.out.printf("[%s] Sending request...\n", threadName);
            System.out.printf("[%s] Response received: %s\n", threadName, connection.getResponseCode());

            response = IOUtils.toString(connection.getInputStream(), "UTF-8");
        } catch(Exception e) {
            throw e;
        }

        synchronized(this) {
            page = response;
        }
    }

    private String parameterBuilder(Map<String, String> parameters) {
        String output = new String();

        for(String parameter : parameters.keySet()) {
            output += String.format("&%s=%s", parameter, parameters.get(parameter));
        }

        return output.substring(1);
    }

    public synchronized String getPage() {
        return page;
    }
}