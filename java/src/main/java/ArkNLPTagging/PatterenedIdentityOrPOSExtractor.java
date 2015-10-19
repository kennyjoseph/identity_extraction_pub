package ArkNLPTagging;

import java.io.*;
import java.util.List;
import java.util.regex.Pattern;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

import cmu.arktweetnlp.Tagger;

import com.google.common.base.Joiner;
import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.ListMultimap;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

public class PatterenedIdentityOrPOSExtractor implements Runnable {

    public static final String FILE_ENCODING = "UTF-8";
    //private static final LangIdV3 mLangid = new LangIdV3();

    public static final String MODEL_LOCATION = "/model.ritter_ptb_alldata_fixed.20130723";

    String IAMA_REGEX_STRING = "(^|\\W|\\p{Punct})(i am|i'm|i was|[s]?he's|[s]?he is|[s]?he was|you're|you are|u r|you r)";
    Pattern I_AM_A_LOOSE_REGEX = Pattern.compile(IAMA_REGEX_STRING,Pattern.CASE_INSENSITIVE);
    Pattern I_AM_A_REGEX = Pattern.compile(IAMA_REGEX_STRING + "( [A-Za-z0-9]*)? (a[n]?|my) ",Pattern.CASE_INSENSITIVE);

    Pattern WE_ARE_REGEX = Pattern.compile("(^|\\W|\\p{Punct})(they[']?re|they are|they were|we're|we are|we r|they r) ",
                                            Pattern.CASE_INSENSITIVE);

    Pattern PERSON_REGEX = Pattern.compile("(person|ppl|people|peeps)",Pattern.CASE_INSENSITIVE);
    Pattern QUANTIFIER_REGEX = Pattern.compile("(all|any|both|each|enough|every|few|no|many|most|some|much|only|more|"
                    +"first|second|third|fourth|fifth|sixth|seventh|eigth|ninth|tenth|other"+
                    "hundred|thousand|million|billion|same|different|same|different|better|worse)",Pattern.CASE_INSENSITIVE);

    private Tagger mPosTagger;
    private String mFileName;
    private String mOutputFileName;

    private boolean mRunPOSTagger;
    private boolean mRunIdentityExtractor;

    Joiner tabJoiner = Joiner.on("\t").skipNulls();
    Joiner barJoiner = Joiner.on("|").skipNulls();

	public PatterenedIdentityOrPOSExtractor(String fileName, Tagger posTagger,
                                            String outputFileName,
                                            boolean runPOSTagger,
                                            boolean runIdentityExtractor){
        mPosTagger = posTagger;
        mFileName =fileName;
        mOutputFileName = outputFileName;
        mRunIdentityExtractor = runIdentityExtractor;
        mRunPOSTagger = runPOSTagger;

	}

    @Override
    public void run() {
        //System.out.println("RUNNING!!!! : "  + mFileName);
        try {

            InputStream in = new FileInputStream(mFileName);
            OutputStream out = new FileOutputStream(mOutputFileName);
            if(mFileName.endsWith(".gz")) {
                in = new GZIPInputStream(in);
            }
            if(mOutputFileName.endsWith(".gz")){
                out = new GZIPOutputStream(out);
            }
            BufferedReader reader = new BufferedReader(new InputStreamReader(in, FILE_ENCODING));
            BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(out, FILE_ENCODING));

            String line = "";
            while ((line = reader.readLine()) != null) {
                //ln(lineCount);
                JsonObject root = new JsonParser().parse(line).getAsJsonObject();
                JsonElement textElt = root.get("text");
                String text = null;
                if (textElt != null) {
                    text = textElt.getAsString();
                }


                String userId = root.get("user").getAsJsonObject().get("id_str").getAsString();
                String tweetId = root.get("id").getAsString();

                String retweeted = root.has("retweeted_status") ? "rt" : "no_rt";
                //System.out.println(tweetId + "    "+ text);
                if (text != null) {
                    ListMultimap<Integer, String> tokenIdToRuleMap = ArrayListMultimap.create();
                    List<Tagger.TaggedToken> tokens = null;

                    if (mRunIdentityExtractor && I_AM_A_REGEX.matcher(text).find()) {
                        tokens = mPosTagger.tokenizeAndTag(text);
                        runIAmARules(tokens, userId, tweetId, retweeted, mRunPOSTagger ? null : writer, tokenIdToRuleMap);

                    }
                    if (mRunIdentityExtractor && I_AM_A_REGEX.matcher(text).find()) {
                        tokens = mPosTagger.tokenizeAndTag(text);
                        runIAmARules(tokens, userId, tweetId, retweeted, mRunPOSTagger ? null : writer, tokenIdToRuleMap);

                    }

                    if (mRunIdentityExtractor && PERSON_REGEX.matcher(text).find()) {
                        if(tokens == null){
                            tokens = mPosTagger.tokenizeAndTag(text);
                        }
                        runPersonRules(tokens, userId, tweetId,retweeted, mRunPOSTagger ? null : writer, tokenIdToRuleMap);
                    }
                    if(mRunPOSTagger) {
                        if (tokens == null) {
                            tokens = mPosTagger.tokenizeAndTag(text);
                        }
                        //System.out.println(text);
                        writer.write(tweetId + "\n");
                        for (int i = 0; i < tokens.size(); i++) {
                            Tagger.TaggedToken t = tokens.get(i);
                            writer.write(tabJoiner.join(i, t.tag, t.token, barJoiner.join(tokenIdToRuleMap.get(i))) + "\n");
                        }
                        writer.write("\n");
                    }


                }

            }
            reader.close();
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
        } catch(Exception e){
            e.printStackTrace();
        }
    }



    public void runIAmARules(List<Tagger.TaggedToken> tokens,
                             String userId, String tweetId, String retweeted,
                             BufferedWriter writer,
                             ListMultimap<Integer, String> tokenIdToRuleMap) throws IOException{
        int tokenSize = tokens.size();
        for (int i = 1; i < tokenSize - 1; ) {
            if (!tokens.get(i).token.toLowerCase().equals("a") &&
                    !tokens.get(i).token.toLowerCase().equals("an")) {
                i++;
                continue;
            }



            String toPrint = "";
            String middleString = "";
            if (I_AM_A_LOOSE_REGEX.matcher(tokens.get(i - 1).token).matches()) {
                //e.g. I'm a ...
                toPrint = tokens.get(i - 1).token;
            } else if (i >= 2 &&
                    I_AM_A_LOOSE_REGEX.matcher(tokens.get(i - 2).token + " " + tokens.get(i - 1).token).matches()) {
                //e.g. I am a
                toPrint = tokens.get(i - 2).token + " " + tokens.get(i - 1).token;
            } else if (i >= 2 &&
                    I_AM_A_LOOSE_REGEX.matcher(tokens.get(i - 2).token).matches() &&
                    (tokens.get(i-1).tag.equals("RB") || tokens.get(i-1).token.equals("being"))) {
                //e.g. I'm still a
                toPrint = tokens.get(i - 2).token;
                middleString = tokens.get(i-1).token+"/"+tokens.get(i-1).tag;
            } else if (i >= 3 &&
                    I_AM_A_LOOSE_REGEX.matcher(tokens.get(i - 3).token + " " + tokens.get(i - 2).token).matches() &&
                    (tokens.get(i-1).tag.equals("RB") || tokens.get(i-1).token.equals("being"))) {
                //e.g. I am still a
                toPrint = tokens.get(i - 3).token + " " + tokens.get(i - 2).token;
                middleString = tokens.get(i-1).token+"/"+tokens.get(i-1).tag;
            } else {
                i++;
                continue;
            }

            i++;
            String outputString = "";

            int startingI = i;
            // ignore a lot, a little, a few
            if(tokens.get(i).token.equals("lot") ||
                    tokens.get(i).token.equals("little") ||
                    tokens.get(i).token.equals("few") ||
                    tokens.get(i).token.equals("bit") ||
                    tokens.get(i).token.equals("whole") ||
                    tokens.get(i).token.equals("lil") ||
                    tokens.get(i).token.length() > 10){
                continue;
            }

            int nTokens = 0;
            while(i < tokenSize &&
                    (tokens.get(i).tag.startsWith("N") ||
                            tokens.get(i).tag.startsWith("JJ") ||
                            (i == startingI && tokens.get(i).tag.equals("RB")) ||
                            tokens.get(i).tag.equals("''") ||
                            tokens.get(i).tag.equals("CD") ||
                            (i == startingI && tokens.get(i).tag.equals("VBN")) ||
                            (i == startingI && tokens.get(i).tag.equals("VBG")) ||
                            (i == startingI && tokens.get(i).tag.equals("DT")))){
                outputString += tokens.get(i).token + "/"+ tokens.get(i).tag + " ";
                tokenIdToRuleMap.put(i, middleString + " " + toPrint );
                tokenIdToRuleMap.put(i, "i_am_rule" );
                i++;
                nTokens++;
            }

            while((tokens.get(i-1).tag.startsWith("V") || tokens.get(i-1).tag.equals("DT")) && nTokens > 1){
                tokenIdToRuleMap.removeAll(i);
                outputString = outputString.replace(tokens.get(i - 1).token + "/" + tokens.get(i - 1).tag + " ", "");
                i--;
                nTokens--;
                if(i == 0){
                    break;
                }
            }

            if(nTokens == 1 && i > 0 && tokens.get(i-1).tag.equals("RB")){
                tokenIdToRuleMap.removeAll(i-1);
                continue;
            }

            String lastFollowing = "<END>";
            if(i != tokenSize){
                lastFollowing = tokens.get(i).token + "/"+ tokens.get(i).tag;
            }

            if(outputString.replace(" ","") != "" && writer != null) {
                writer.write(userId + "\t" + tweetId + "\t" + retweeted+"\t" + toPrint
                        + "\t" + middleString + "\t" + outputString + "\t" + lastFollowing+ "\n");
            }
            //if(outputString.equals("")){
            //    System.out.println("WTF  ::: " + text);
            //    for(Tagger.TaggedToken t : tokens){
            //        System.out.println(t.token + " " + t.tag + " " + t.tag.startsWith("N"));
            //    }
            //    System.out.println("\n\n\n");
            // }

        }
    }

    public void runPersonRules(List<Tagger.TaggedToken> tokens,
                               String userId, String tweetId, String retweeted,
                               BufferedWriter writer,
                               ListMultimap<Integer, String> tokenIdToRuleMap) throws IOException{
        int tokenSize = tokens.size();
        for (int i = 1; i < tokenSize;i++) {
            if (!PERSON_REGEX.matcher(tokens.get(i).token).matches() ||
                    QUANTIFIER_REGEX.matcher(tokens.get(i-1).token).matches()){
                continue;
            }
            if (tokens.get(i - 1).tag.startsWith("JJ")) {
                tokenIdToRuleMap.put(i-1, tokens.get(i).token+" "+tokens.get(i).tag);
                tokenIdToRuleMap.put(i-1, "people_rule");
                tokenIdToRuleMap.put(i, "people_rule");

                String prev = "<START>";
                if(i-2 > 0 ){
                    prev = tokens.get(i-2).token + "/"+ tokens.get(i-2).tag;
                }
                String lastFollowing = "<END>";
                if(i+1 != tokenSize){
                    lastFollowing = tokens.get(i+1).token + "/"+ tokens.get(i+1).tag;
                }

                if(writer != null) {
                    writer.write(userId + "\t" + tweetId + "\t" + retweeted + "\t" + tokens.get(i).token + "\t" + prev + "\t"
                            + tokens.get(i - 1).token + "/" + tokens.get(i - 1).tag + "\t" + lastFollowing + "\n");
                }
            }
        }
    }

    public static Tagger initTagger(){
        Tagger posTagger = new Tagger();
        boolean initialized = false;
        try {
            posTagger.loadModel(MODEL_LOCATION);
            initialized = true;
        } catch (IOException e1) {
            e1.printStackTrace();
        }
        if(!initialized){
            try {
                posTagger.loadModel("/Users/kennyjoseph/git/thesis/java_utils_thesis/ark_nlp_tagger/src/main/resources/model.ritter_ptb_alldata_fixed.20130723");
            } catch (IOException e1) {
                e1.printStackTrace();
            }
        }
        return posTagger;
    }

    public static void main(String[] args){
//        System.out.println("Args given: ");
//        for(String arg : args){
//           System.out.println("\t" + arg);
//        }
//		if(args.length != 4){
//            throw new RuntimeException("\nUsage: [fileToParse] [outputFileName]");
//		}
//		String file = args[0];
//		String outputFileName =  args[1];

        String file = "/Users/kennyjoseph/git/thesis/thesis_work/identity_extraction/python/all_tweets.json";
        String outputFileName = "/Users/kennyjoseph/git/thesis/thesis_work/identity_extraction/python/processed_data/java_out.txt";

        new PatterenedIdentityOrPOSExtractor(file, initTagger(),outputFileName, true, true).run();

    }

}

