# Full 54-case deterministic factorial; no uncertainty intervals from replicates.
# Panels compare within-season changes, then exact additive contrasts.
s <- read.csv('chart_data/seasonal_scenarios.csv',fileEncoding='UTF-8-BOM')
i <- read.csv('chart_data/seasonal_interactions.csv',fileEncoding='UTF-8-BOM')
g <- read.csv('chart_data/segments.csv',fileEncoding='UTF-8-BOM')
stopifnot(nrow(s)==54,nrow(i)==464)
savefig <- function(name,draw,w=9.1,h=6.6){
 png(paste0('04_figures/',name,'.png'),width=w,height=h,units='in',res=330,type='cairo');draw();dev.off()
 cairo_pdf(paste0('04_figures/',name,'.pdf'),width=w,height=h,family='Arial');draw();dev.off()
 svg(paste0('04_figures/',name,'.svg'),width=w,height=h,family='Arial');draw();dev.off()
}
savefig('Fig02_seasonal_factorial',function(){
 par(mfrow=c(2,3),mar=c(3.5,3.6,2.6,.7),oma=c(1.8,0,1.8,0),family='Arial',cex=.9,mgp=c(1.8,.6,0),cex.lab=.85)
 lim<-max(abs(s$delta_mean23_ug_L)); cols<-colorRampPalette(c('#387CA2','#FFFFFF','#C66338'))(101)
 for(period in c('2020-08','2021-03')) for(q in c(.7,1,1.3)){
  a<-s[s$period==period & s$Q_factor==q,]
  plot.new();plot.window(xlim=c(.5,3.5),ylim=c(.5,3.5),xaxs='i',yaxs='i')
  for(k in seq_len(nrow(a))){x<-match(a$T_plus_C[k],c(0,2,4));y<-match(a$DIP_factor[k],c(1,2,4));v<-a$delta_mean23_ug_L[k]
   rect(x-.5,y-.5,x+.5,y+.5,col=cols[1+round((v+lim)/(2*lim)*100)],border='white')
   text(x,y,sprintf('%+.2f',v),cex=.95,col=if(abs(v)>.65*lim)'white' else '#25343E')
  }
  axis(1,1:3,c('0','+2','+4'));axis(2,1:3,c('1','2','4'),las=1)
  title(main=paste(if(period=='2020-08')'Summer' else 'Winter','| Q x',q),xlab='Warming (C)',ylab='DIP multiplier')
 }
 mtext('Change in volume-weighted Chl-a over S01-S23 (ug/L)',outer=TRUE,side=3,line=.4,cex=1)
 mtext(sprintf('Common colour scale: blue %.2f | white 0 | orange +%.2f; cells show exact changes.',-lim,lim),outer=TRUE,side=1,line=.3,cex=.8)
})
weighted<-function(a,col){j<-match(a$segment_id,g$segment_id);use<-j<=23;weighted.mean(a[[col]][use],g$volume_m3[j[use]])}
effects<-c('I_TP_ug_L','I_TQ_ug_L','I_PQ_ug_L','I_TPQ_ug_L','net_nonadditivity_ug_L')
mats<-lapply(c(.7,1.3),function(q){do.call(rbind,lapply(c('2020-08','2021-03'),function(p){a<-i[i$period==p&i$T_plus_C==4&i$DIP_factor==4&i$Q_factor==q,];sapply(effects,function(e)weighted(a,e))}))})
savefig('Fig03_seasonal_interactions',function(){
 par(mfrow=c(1,2),mar=c(4,4.4,3,1),oma=c(2.4,0,0,0),family='Arial')
 yl<-range(c(0,unlist(mats)));yl<-c(yl[1]-.15*diff(yl),yl[2]+.3*diff(yl))
 for(k in 1:2){barplot(mats[[k]],beside=TRUE,col=c('#C56C30','#1D8C88'),border=NA,
   names.arg=c('T x P','T x Q','P x Q','T x P x Q','Net'),ylim=yl,ylab='Additive interaction (ug/L)',
   main=paste('+4 C, DIP x4, Q x',c(.7,1.3)[k]),cex.names=.85);abline(h=0,col='#65747E');
   legend('topright',c('Summer','Winter'),fill=c('#C56C30','#1D8C88'),bty='n',cex=.85)}
 mtext('Volume-weighted contrasts over S01-S23; Net = sum of the three pairwise terms and the three-way term.',outer=TRUE,side=1,line=.5,cex=.74)
},h=4.8)
