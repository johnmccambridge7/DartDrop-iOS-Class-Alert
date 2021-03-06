package dartmouthTimetableScannerServer;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import java.io.FileWriter;
import java.io.IOException;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

/**
 * Extracts course information from HTML and saves to file as JSON, only crawls when HTML is 
 * updated (a change is detected).
 * 
 * @author Jai Smith
 */
public class Scanner extends Thread {
    private String html;
    private Boolean update;
    private Map<String, Map<String, String>> courses;
    private App caller;
    private String threadName;

    public Scanner(App caller, String threadName) {
        this.caller = caller;
        this.threadName = threadName;
    }

    public void run() {
        // System.out.printf("[%s] run() called\n", threadName);

        if(update) {
            scanCourses();
            update = false;

            caller.reportChange();
        }
    }

    public void passHTML(String html) {
        if(this.html == null || !this.html.equals(html)) {
            System.out.printf("[%s] New data received\n", threadName);
            this.html = html;
            update = true;
        } else {
            System.out.printf("[%s] Nothing new to process\n", threadName);
            update = false;
        }
    }

    private synchronized void scanCourses() {
        Document page = Jsoup.parse(html);

        Elements courseAttributeElements = page.getElementsByAttributeValue("scope", "col");
        List<String> courseProperties = courseAttributeElements.eachText();
        System.out.printf("[%s] %s\n", threadName, courseProperties);

        courses = new HashMap<String, Map<String, String>>();

        int i = 0;
        Map<String, String> current = new LinkedHashMap<String, String>();
        for(Element element : page.getElementsByIndexGreaterThan(courseAttributeElements.last().siblingIndex()).select("td")) {
            if(!(i < courseProperties.size())) {
                courses.put(current.get("CRN"), current);
                current = new LinkedHashMap<String, String>();
                i = 0;
            }

            current.put(courseProperties.get(i), element.text());
            i++;
        }

        System.out.printf("[%s] %d courses processed\n", threadName, courses.size());
    }

    public synchronized void writeOutput() throws IOException {
        FileWriter writer = new FileWriter("output.json");
        Gson gson = new GsonBuilder().setPrettyPrinting().create();

        System.out.printf("[%s] Writing data to JSON\n", threadName);

        gson.toJson(courses, writer);
        writer.close();

        System.out.printf("[%s] Data written to 'output.json'\n", threadName);
    }

    public Map<String, Map<String, String>> getCourses() {
        return courses;
    }
}
