library(data.table)
library(dplyr)
library(Hmisc)
library(ggplot2)
b <- fread("../python/results/param_tuning_results.tsv")
setnames(b, c("fold","cutoff","use_filtered","dataset","param","v","tp","fn","fp","tn","prec","recall","f1","auc"))
b <- b[cutoff == .0001]

b_av <- b[,list(f1=mean(f1),sd_f1=sd(f1)), by=c("use_filtered","dataset","param","v")]

b_av <- arrange(b_av, by=-f1)
#not interesting, just without head features. Doesn't really change much but performs slightly worse
# in absolute terms
b_av <- b_av[dataset != "x_wv_ls"]
plot_dat_for_cross_val <- b_av[,list(v=.SD$v[which.max(f1)],
                                     param=.SD$param[which.max(f1)],
                                     f1=max(f1),
                                     sd_f1=.SD$sd_f1[which.max(f1)]),
                               by=c("dataset","use_filtered")]


plot_dat_for_cross_val$dataset <- factor(plot_dat_for_cross_val$dataset,
                                         levels=c("full","x_wv","x","all_wv","wv"),
                                         labels=c("All Features",
                                                  "Lexical+Dictionary+Word Vectors",
                                                  "Lexical+Dictionary",
                                                  "All Word Vectors",
                                                  "Word Vector for W Only"))

dictionary_res <- fread("../python/results/baselines_on_ferg_data.tsv",header=F,sep = "\t")
setnames(dictionary_res, c("dict","tp","fn","fp","tn","prec","recall","f1","auc"))

theme_set(theme_bw(20))
p <- ggplot(plot_dat_for_cross_val,
           aes(dataset,f1,ymin=f1-sd_f1,ymax=f1+sd_f1,color=use_filtered)) 
p <- p + geom_pointrange(position=position_dodge(width=.5), size=1.5) + ylab("F1") + xlab("Feature Set")
p <- p + theme(axis.text.x =element_text(angle=45,hjust=1), legend.title=element_blank(),legend.position=c(.8,.9))
p <- p + scale_color_discrete(labels=c("Non-filtered model","Filtered Model")) 
p <- p + geom_hline(y=max(dictionary_res$f1),size=1.2,color='blue') + annotate("text",x=1.6,y=.54,
                                                    label="Best Dictionary-only\nCombination",
                                                    size=6,color='blue')
p <- p + coord_flip()
ggsave("~/Dropbox/Kenny/papers/current/defense/study_1/figs/f1.png",p, dpi=400,w=10,h=7)


final_res <- fread("../python/results/final_model_pub_res.tsv")
final_res_dict  <- fread("../python/results/baselines_on_public_data.tsv")

library(scales)
theme_set(theme_bw(12))
d <- fread("../python/results/top_ten.txt")
d[d$V1 == 'nigga']$V1 <- '$$$ga'
d$V1 <- factor(d$V1, levels=arrange(d,V2)$V1)
p1 <- ggplot(d, aes(V1,V2)) + geom_bar(stat='identity') + coord_flip() 
p1 <- p1 + xlab("Top Ten Identities") + ylab("% of All Identity Labels")
p1 <- p1 + scale_y_continuous(labels=percent)
ggsave("~/Dropbox/Kenny/papers/current/defense/study_1/figs/f2.png",p1, dpi=400,w=4,h=2)

theme_set(theme_bw(15))
d <- fread("../python/results/pdf_identities.csv")
d <- d[V2 > 0]
pX <- ggplot(d, aes(V2,V3)) + geom_point() + scale_x_log10() + scale_y_log10() 

theme_set(theme_bw(12))
d <- fread("../python/results/per_user_identity_counts.csv")
p2 <- ggplot(d, aes(uniq)) + geom_histogram()
p2 <- p2 + ylab("Number of Users") + xlab("Number of Unique Identities Used")
p2 <- p2 + geom_vline(x=68,color='red',size=1.2)
ggsave("~/Dropbox/Kenny/papers/current/defense/study_1/figs/f3.png",p2, dpi=400,w=4,h=2)

library(stringr)
d <- fread("../python/results/lda_results_tagged.csv",header=T)
d$n <- rep(1:20,30)
d$V1 <- NULL
setnames(d, c("topic","prob","word","topic_name","ranking"))
d <- d[ranking <= 10]
d <- d[topic_name != "" & topic_name != "British One" & topic_name != "Politics British"]
d$topic_name <- str_replace_all(d$topic_name,"One","1")
d$topic_name <- str_replace_all(d$topic_name,"Two","2")
d$topic_name <- str_replace_all(d$topic_name,"Three","3")
d$word <- sub("nig","$$$",d$word)
d$word_topic <- with(d, paste(word,topic))
p4 <- ggplot(d, aes(reorder(word_topic,-prob),prob)) + geom_bar(stat='identity') 
p4 <- p4 + facet_wrap(~topic_name,scales="free_x",nrow=3)
p4 <- p4 + theme(axis.text.x=element_text(angle=45,hjust=1),panel.margin = unit(1.1, "lines"))
p4 <- p4 + scale_x_discrete("Word",breaks=d$word_topic,labels=d$word)
p4 <- p4 + ylab("Probabilistic Association With Topic")
theme_set(theme_bw(12))
ggsave("~/Dropbox/Kenny/papers/current/defense/study_1/figs/f4.png",p4,dpi=400,w=14,h=6)


write.table(d[,c("word","topic","prob"),with=F],file="../python/results/word2topic.tsv",row.names=F,col.names=F,quote=F)

d2 <- fread("../python/results/spatial_lda_results.csv",header=T)
d2 <- d2[,24:ncol(d2),with=F]
d3 <- melt(d2, id.vars="b_percent")
#topic distributions are bimodal
#ggplot(d3, aes(value,color=variable)) + geom_density() + scale_x_log10() + geom_vline(x=.005,size=1.5)
d3$split <- d3$value > .01
d3$topic <- rep(0:29,each=72991)
d3 <- merge(d3,unique(d[,c("topic","topic_name"),with=F]), by="topic")
dat <- d3[,as.list(smean.cl.boot(.SD$b_percent,conf.int = .99)),by=c("topic_name","split")]

library(scales)
p5 <- ggplot(dat[topic_name %in% c("Race","Sports","Politics"),], 
             aes(split,Mean,ymin=Lower,ymax=Upper, group=topic_name))
p5 <- p5 + geom_pointrange()  + geom_line() + facet_wrap(~topic_name)
p5 <- p5 + ylab("Mean County-level\nPercentage African American") + scale_y_continuous(labels=percent)
p5 <- p5 + scale_x_discrete("Users Associated With Topic",labels=c("No","Yes"))
theme_set(theme_bw(12))
ggsave("~/Dropbox/Kenny/papers/current/defense/study_1/figs/f5.png",p5,dpi=400,w=5,h=2.5)







b <- fread("../python/results/affect_scores.csv")
setnames(b,"term","word")
d_w_sent <- merge(d,b,by="word")

q <- d_w_sent[,list(  tot_v=sum(sent_per_doc*prob),
                      tot=sum(sent_per_doc),
                      abs_v=sum(abs(sent_per_doc*prob)),
                      dist=sum(dist(sent_per_doc))/45,
                      dist_v=sum(dist(sent_per_doc*prob))/45),by="topic_name"]

ggplot(q, aes(reorder(topic_name,tot),tot)) + geom_bar(stat='identity') + coord_flip()
ggplot(q, aes(reorder(topic_name,dist),dist)) + geom_bar(stat='identity') + coord_flip()












#q <- q[!grepl("^u",topic_name),]
tc <- fread("../python/results/top_coherence.txt")
setnames(tc, c("top_coh","word"))
q2 <- merge(tc,d[ranking==1],by="word" )
q2 <- q2[-8,]
q2 <- merge(q,q2, by="topic_name")

ggplot(q2, aes(-dist,top_coh,label=topic_name)) + geom_text() + xlab("Affective Coherence") + ylab("Semantic Coherence")



t <- fread("../python/results/time_df.csv",header=T)
t$V1 <- NULL
setnames(t, c("word","date","count"))
t$date <- paste0("01-",t$date)
library(lubridate)
t$dt <- dmy(t$date)
w_date <- merge(d,t,by="word",allow.cartesian = T)
w_date_sum <- w_date[,sum(count),by=c("topic_name","dt")]
w_date$date_int <- as.integer(factor(as.character(w_date$dt), levels=as.character(sort(unique(w_date$dt)))))

blah <- function(d){
return(summary(lm(count~lag(count),arrange(d,dt)))$adj.r.squared)
}

q4 <-w_date[dt > ymd("2013-01-01") & dt < ymd("2015-01-01"),blah(.SD),by=c("word","topic_name")]
q4 <- q4[,mean(V1),by="topic_name"]
q4 <- merge(q4,q2,by="topic_name")

ggplot(q4, aes(-dist, tot, label=topic_name)) + geom_text()
ggplot(q4, aes(-dist, top_coh, label=topic_name)) + geom_text()

cor(q4$V1,-q4$coh)
cor(q4$V1,q4$dist_v)

wn_sims <- fread("../python/wn_top_sims.txt")

q5 <- merge(q4,wn_sims,by="topic")
ggplot(q5, aes(wn_sim, dist,label=topic_name)) + geom_text()

ggplot(dat[topic_name %in% c("Brown/Garner","Brown/Garner 1")], aes(split,Mean,ymin=Lower,ymax=Upper, color=topic_name,group=topic_name)) + geom_pointrange() + geom_line()
ggplot(dat[topic_name %in% c("College","Race Two")], aes(split,Mean,ymin=Lower,ymax=Upper, color=topic_name,group=topic_name)) + geom_pointrange() + geom_line()


z <- fread("../python/results/fil_count.txt")
sum(z)



a <- fread("../python/results/affect_clustering.csv")
setnames(a, "term","word")
all_affect_info <- merge(a,b,by="word")



tdf <- fread("../python/results/time_sent_df.csv",header=T)
tdf$V1 <- NULL
setnames(tdf,c("term","date","sent","count"))
tdf$av <- tdf$sent/tdf$count
tdf$d <- mdy(tdf$date)

ggplot(tdf[d > ymd("2014-01-01") & term %in% c("officer","police_officer")], aes(d,av,color=term)) + geom_point()  + geom_line() + geom_vline(x=as.integer(ymd("2014-08-09")),color='red') + geom_vline(x=as.integer(ymd("2014-11-24")),color='red') + geom_smooth()

tdf <- fread("../python/results/time_sent_user_df.csv",header=T)
tdf$V1 <- NULL
setnames(tdf,c("uid","term","date","sent","count"))
tdf$av <- tdf$sent/tdf$count
tdf$d <- mdy(tdf$date)

z <- fread("../python/results/full_loc_dat.csv")

val <- tdf[,sum(av),by=c("uid","term")]
val <- spread(val, term, V1)
val <- merge(val,z,by="uid")
