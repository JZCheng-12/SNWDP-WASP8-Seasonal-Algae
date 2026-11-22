# Figure contract: reproduce the audited course-model evidence, using only R.
# Nine evidence panels: two seasonal fits, single-factor response, two T-P
# response panels, exact interactions, two temperature diagnostics, flow response.
# All 20 summer and 22 winter Chl-a estimates are retained. Scenario curves are
# deterministic results, without sampling error bars or significance claims.
# Run from the project root: Rscript 06_复现脚本/plot_course_presentation.R
# Only base R / grDevices are required. No Python graphics are used.
options(encoding = "UTF-8")
out <- file.path("04_figures", "course_presentation_R")
dir.create(out, recursive = TRUE, showWarnings = FALSE)
read_data <- function(f) read.csv(file.path("chart_data", f), fileEncoding="UTF-8-BOM", check.names=FALSE)
sc <- read_data("seasonal_scenarios.csv")
fit_s <- subset(read_data("seasonal_final_fit.csv"), period=="2020-08")
fit_w <- read_data("winter_inlet_final_fit.csv")
stopifnot(nrow(sc)==54, nrow(fit_s)==20, nrow(fit_w)==22)
periods <- c("2020-08", "2021-03")
C <- function(p,t=0,d=1,q=1) {
 z <- sc$mean23_Chla_ug_L[sc$period==p & sc$T_plus_C==t & sc$DIP_factor==d & sc$Q_factor==q]
 stopifnot(length(z)==1, is.finite(z)); z
}
summer <- "#B45339"; winter <- "#247B8D"; ink <- "#293C47"; muted <- "#78858C"
cols <- c(summer,winter); FONT <- "Microsoft YaHei"
season_names <- c("\u590f\u5b63", "\u51ac\u5b63")
chla_label <- "Chl-a (\u00b5g/L)"
draw_axes <- function(xlab,ylab,ylim,xlim) {
 plot(NA,xlim=xlim,ylim=ylim,xlab=xlab,ylab=ylab,bty="l",yaxs="i",xaxs="r")
 abline(h=axTicks(2),col="#E5E9EC",lwd=.7)
}
export <- function(stem,draw,width,height) {
 for(fmt in c("png","pdf","svg")) {
  f <- file.path(out,paste0(stem,".",fmt))
  if(fmt=="png") png(f,width=width,height=height,units="in",res=330,type="cairo",pointsize=15,bg="white")
  if(fmt=="pdf") cairo_pdf(f,width=width,height=height,family=FONT,pointsize=15,bg="white")
  if(fmt=="svg") svg(f,width=width,height=height,family=FONT,pointsize=15,bg="white")
  par(family=FONT,mar=c(4,4.2,1.1,.7),mgp=c(2.55,.7,0),tcl=-.22,
      col=ink,col.axis=ink,col.lab=ink,fg=ink,las=1,cex.axis=.9,cex.lab=.95)
  draw(); dev.off()
 }
}
for(i in 1:2) local({
 j <- i; d <- list(fit_s,fit_w)[[j]]; d <- d[order(d$distance_km),]
 export(paste0("fit_",c("summer","winter")[j]),function(){
  draw_axes("\u6cbf\u7a0b\u8ddd\u79bb (km)",chla_label,c(0,14),c(0,1250))
  points(d$distance_km,d$observed_ug_L_approx,pch=21,bg="#9BA5A9",col="white",cex=1.05)
  lines(d$distance_km,d$final_fitted_ug_L,col=cols[j],lwd=2.5)
  legend("topright",c("\u56fe\u50cf\u4f30\u8bfb","\u6700\u7ec8\u62df\u5408"),
    pch=c(16,NA),lty=c(NA,1),col=c("#9BA5A9",cols[j]),lwd=c(NA,2.5),bty="n",cex=.85)
 },5.8,3.55)
})
levels <- rbind(c(4,1,1),c(0,4,1),c(0,1,.7),c(0,1,1.3))
single <- t(sapply(periods,function(p) apply(levels,1,function(v)100*(C(p,v[1],v[2],v[3])/C(p)-1))))
rownames(single)<-season_names
export("single_factor",function(){
 par(mar=c(3.6,4,1,.7))
 bx<-barplot(single,beside=TRUE,col=cols,border=NA,ylim=c(-20,68),axes=FALSE,
  names.arg=c("\u5347\u6e29 +4\u00b0C","DIP \u00d74","\u6d41\u91cf \u221230%","\u6d41\u91cf +30%"),cex.names=.95)
 abline(h=seq(-20,60,20),col="#E5E9EC",lwd=.7)
 barplot(single,beside=TRUE,col=cols,border=NA,add=TRUE,axes=FALSE,axisnames=FALSE)
 axis(2,at=seq(-20,60,20));abline(h=0,col="#88959B")
 mtext("Chl-a \u76f8\u5bf9\u53d8\u5316 (%)",side=2,line=2.5,las=0)
 text(bx,single+ifelse(single>=0,3,-4),sprintf("%.1f",single),cex=.98,font=2)
 legend("topright",legend=season_names,fill=cols,border=NA,horiz=TRUE,bty="n",cex=.95)
},11.7,4.05)
for(i in 1:2) local({
 j<-i;p<-periods[j]; x<-c(1,2,4)
 export(paste0("tp_",c("summer","winter")[j]),function(){
  draw_axes("DIP \u500d\u7387",chla_label,c(0,20),c(.85,4.15))
  for(t in c(0,4))lines(x,sapply(x,function(d)C(p,t,d,1)),type="b",pch=16,lwd=2.5,col=if(t==0)cols[j] else ink)
  legend("topleft",c("\u539f\u6e29","+4\u00b0C"),col=c(cols[j],ink),pch=16,lty=1,lwd=2.5,bty="n",cex=.9)
 },5.8,3.65)
})
interaction <- function(p,q=.7) {
 b<-C(p);t<-4;d<-4
 tp<-C(p,t,d,1)-C(p,t,1,1)-C(p,0,d,1)+b
 tq<-C(p,t,1,q)-C(p,t,1,1)-C(p,0,1,q)+b
 pq<-C(p,0,d,q)-C(p,0,d,1)-C(p,0,1,q)+b
 net<-C(p,t,d,q)-C(p,t,1,1)-C(p,0,d,1)-C(p,0,1,q)+2*b
 c(tp,tq,pq,net-tp-tq-pq)
}
ints<-t(sapply(periods,interaction));stopifnot(abs(sum(ints[2,])-8.58740089015044)<1e-8)
export("interactions",function(){
 par(mar=c(3.6,4,1,.7))
 bx<-barplot(ints,beside=TRUE,col=cols,border=NA,ylim=c(-1.2,9.4),axes=FALSE,
  names.arg=c("\u6e29\u5ea6 \u00d7 \u78f7","\u6e29\u5ea6 \u00d7 \u6d41\u91cf","\u78f7 \u00d7 \u6d41\u91cf","\u4e09\u56e0\u7d20"),cex.names=.95)
 abline(h=seq(0,8,2),col="#E5E9EC",lwd=.7)
 barplot(ints,beside=TRUE,col=cols,border=NA,add=TRUE,axes=FALSE,axisnames=FALSE)
 axis(2,at=seq(0,8,2)); abline(h=0,col="#88959B")
 mtext("\u4ea4\u4e92\u6548\u5e94 (\u00b5g/L)",side=2,line=2.5,las=0)
 text(bx,ints+ifelse(ints>=0,.35,-.38),sprintf("%.2f",ints),cex=.95,font=2)
 legend("topright",legend=season_names,fill=cols,border=NA,horiz=TRUE,bty="n",cex=.95)
},11.7,3.7)
for(i in 1:2) local({
 j<-i;p<-periods[j];t0<-unique(sc$temperature_C[sc$period==p & sc$T_plus_C==0]);opt<-c(30,20)[j]
 dt<-seq(0,4,.1);growth<-exp(-.05*((t0+dt-opt)^2-(t0-opt)^2));resp<-1.07^dt
 export(paste0("temperature_",c("summer","winter")[j]),function(){
  draw_axes("\u5347\u6e29 (\u00b0C)","\u76f8\u5bf9\u57fa\u51c6 (\u500d)",c(0,c(1.55,31)[j]),c(0,4))
  lines(dt,growth,col=cols[j],lwd=2.5);lines(dt,resp,col=muted,lwd=2.2,lty=2)
  legend(if(j==1)"bottomleft" else "topleft",c("\u751f\u957f\u6e29\u5ea6\u56e0\u5b50","\u547c\u5438\u6e29\u5ea6\u56e0\u5b50"),
    col=c(cols[j],muted),lty=c(1,2),lwd=c(2.5,2.2),bty="n",cex=.85)
 },5.8,3.65)
})
export("flow_response",function(){
 x<-c(.7,1,1.3);draw_axes("\u6d41\u91cf\u500d\u7387",chla_label,c(0,22),c(.67,1.33))
 for(j in 1:2){
  y<-sapply(x,function(q)C(periods[j],4,4,q));lines(x,y,type="b",pch=16,col=cols[j],lwd=2.5)
  text(x,y+1.1,sprintf("%.2f",y),col=cols[j],font=2,cex=.95)
 }
 legend("bottomleft",legend=season_names,col=cols,lwd=2.5,pch=16,horiz=TRUE,bty="n",cex=.9)
},8.2,4.05)
write.csv(data.frame(season=rep(periods,each=4),factor=rep(c("T+4","DIPx4","Q0.7","Q1.3"),2),percent=as.vector(t(single))),file.path(out,"single_factor_source.csv"),row.names=FALSE)
write.csv(data.frame(season=rep(periods,each=4),term=rep(c("TP","TQ","PQ","TPQ"),2),effect=as.vector(t(ints))),file.path(out,"interaction_source.csv"),row.names=FALSE)
writeLines(capture.output(sessionInfo()),file.path(out,"R_sessionInfo.txt"))
cat("Exported 9 panels in PNG, PDF and SVG\n")
