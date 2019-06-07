package dartmouthTimetableScannerServer;

/**
 * Main process, manages PageLoader and Scanner threads
 *
 *
 *
 * @author Jai Smith
 */
public class App {
    private PageLoader pageLoader;
    private Scanner scanner;
    private String threadName = "Main";

    public App() {
        pageLoader = new PageLoader(this, "PageLoader");
        scanner = new Scanner(this, "Scanner");

        pageLoader.setDaemon(true);
        scanner.setDaemon(true);

        pageLoader.start();

        while(true) {
            try {
                Thread.sleep(30000);
            } catch(Exception e) {
                System.out.printf("[%s] Error pausing thread: %s\n", threadName, e);
            };

            pageLoader.run();
        }
    }

    public void reportUpdate() {
        System.out.printf("[%s] Course data updated\n", threadName);

        scanner.passHTML(pageLoader.getPage());
        scanner.run();
    }

    public void reportChange() {
        System.out.printf("[%s] Course data changed\n", threadName);

        try {
            scanner.writeOutput();
        } catch(Exception e) {
            System.out.printf("[%s] Error writing output: %s\n", threadName, e);
        }
    }

    public static void main(String[] args) {
        new App();
    }
}
