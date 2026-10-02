Sys.setlocale('LC_CTYPE','English_United States.utf8')
.libPaths(c('.R-library',.libPaths()))
data('Khan',package='ISLR2')
train <- data.frame(id=seq_len(nrow(Khan$xtrain)),Khan$xtrain,target=Khan$ytrain,split='train',check.names=FALSE)
test <- data.frame(id=nrow(train)+seq_len(nrow(Khan$xtest)),Khan$xtest,target=Khan$ytest,split='test',check.names=FALSE)
names(train)[2:(ncol(train)-2)] <- names(test)[2:(ncol(test)-2)] <- paste0('gene_',seq_len(ncol(Khan$xtrain)))
# 原书规定的训练/测试集保留；按类别确定性地轮流分入五个训练折。
train$fold <- -1L
for (k in sort(unique(train$target))) {
  rows <- which(train$target==k); train$fold[rows] <- rep(0:4,length.out=length(rows))
}
test$fold <- -1L
write.csv(rbind(train,test),'data/khan.csv',row.names=FALSE)
cat('Exported Khan official split:',nrow(train),nrow(test),ncol(Khan$xtrain),'features\n')
