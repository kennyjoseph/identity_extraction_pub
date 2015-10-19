package ArkNLPTagging;

/**
 * Created by kjoseph on 10/1/14.
 */

import cmu.arktweetnlp.Tagger;

import java.io.File;
import java.io.IOException;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Demonstrates how to first use the tagger, then use the
 * ShiftReduceParser.  Note that ShiftReduceParser will not work
 * on untagged text.
 *
 * @author John Bauer
 */
public class RunIdentityExtractOrPOSTagger {


    public static void runIdentityExtractionAndOrPOSTagging(String inputDirectory,
                                                          final String outputDirectory,
                                                          int numThreads,
                                                          boolean runPOSTagger, boolean runIdentityExtractor){
        final ExecutorService executor = Executors.newFixedThreadPool(numThreads);
        final Tagger tagger = PatterenedIdentityOrPOSExtractor.initTagger();

        try {
            Files.walkFileTree(Paths.get(inputDirectory), new SimpleFileVisitor<Path>() {
                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                    //System.out.println(file );
                    if(file.toString().contains(".DS_Store")){
                        return FileVisitResult.CONTINUE;
                    }

                    executor.execute(new PatterenedIdentityOrPOSExtractor(file.toString(),
                            tagger,
                            outputDirectory + file.getFileName().toString().replace(".json.gz",".txt.gz"),
                            runPOSTagger,
                            runIdentityExtractor));
                    return FileVisitResult.CONTINUE;
                }
            });
        } catch (IOException e) {
            e.printStackTrace();
        }
        executor.shutdown();
    }

    public static void main(String[] args) {
        if(args.length != 4){
            System.out.println("Usage: [input_directory] [output_directory] [n_threads] "
                            + " [run_identity_extractor (1 does identity extraction, 2 outputs POS labels, 3 does both) ]");
            System.exit(-1);
        }
        String inputDirectory = args[0];
        if(!inputDirectory.endsWith("/")){
            inputDirectory+="/";
        }
        String outputDirectory = args[1];
        if(!outputDirectory.endsWith("/")){
            outputDirectory+="/";
        }
        File outputDirFile = new File(outputDirectory);
        if (!outputDirFile.exists()) {
            boolean madeDir = outputDirFile.mkdirs();
            if (madeDir) {
                System.out.println("Output Directory successfully created");
            }
            else {
                System.out.println("Failed to create output directory: " + outputDirectory + ", exiting");
                System.exit(-1);
            }
        } else {
            System.out.println("NOT OVERWRITING OUTPUT, EXITING");
            //System.exit(-1);
        }

        int numThreads = Integer.parseInt(args[2]);

        boolean runPOSTagger = false;
        boolean runIdentityExtractor = false;
        int runValueFromUser = Integer.valueOf(args[3]);
        switch(runValueFromUser){
            case 1: runIdentityExtractor = true; break;
            case 2: runPOSTagger = true; break;
            case 3: runPOSTagger = runIdentityExtractor = true;
        }

        runIdentityExtractionAndOrPOSTagging(inputDirectory, outputDirectory, numThreads, runPOSTagger, runIdentityExtractor);

    }
}