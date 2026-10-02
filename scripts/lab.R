# 项目根目录下 source('scripts/lab.R')；每个实验重新读取自己的数据。
macro_f1 <- function(truth, pred, labels) {
  mean(vapply(labels, function(k) {
    tp <- sum(truth == k & pred == k)
    denominator <- sum(truth == k) + sum(pred == k)
    if (denominator == 0) 0 else 2 * tp / denominator
  }, numeric(1)))
}

fit_preprocessor <- function(data) {
  numeric <- names(data)[vapply(data, is.numeric, logical(1))]
  categorical <- setdiff(names(data), numeric)
  medians <- vapply(data[numeric], median, numeric(1), na.rm=TRUE)
  modes <- lapply(data[categorical], function(x) names(sort(table(x), decreasing=TRUE))[1])
  levels <- lapply(data[categorical], function(x) sort(unique(x[!is.na(x)])))
  state <- list(numeric=numeric, categorical=categorical, medians=medians, modes=modes, levels=levels)
  raw <- transform_features(data, state, scale=FALSE)
  state$mean <- colMeans(raw)
  state$sd <- apply(raw, 2, sd) * sqrt((nrow(raw)-1)/nrow(raw)) # 对齐 StandardScaler ddof=0
  state$sd[state$sd == 0] <- 1
  # 只标准化数值列；one-hot 的 0/1 与 Python 保持一致。
  state$mean[!colnames(raw) %in% numeric] <- 0
  state$sd[!colnames(raw) %in% numeric] <- 1
  state
}

transform_features <- function(data, state, scale=TRUE) {
  output <- list()
  for (name in state$numeric) {
    x <- data[[name]]; x[is.na(x)] <- state$medians[[name]]; output[[name]] <- x
  }
  for (name in state$categorical) {
    x <- as.character(data[[name]]); x[is.na(x)] <- state$modes[[name]]
    for (level in state$levels[[name]]) output[[paste(name,level,sep='_')]] <- as.numeric(x==level)
  }
  result <- do.call(cbind, output)
  if (scale) result <- sweep(sweep(result,2,state$mean,'-'),2,state$sd,'/')
  result
}

fit_case_r <- function(name='iris') {
  data <- read.csv(file.path('data', paste0(name,'.csv')), check.names=FALSE, stringsAsFactors=FALSE, na.strings=c('NA',''))
  train <- data[data$split=='train', ]; test <- data[data$split=='test', ]
  features <- setdiff(names(data),c('id','split','target','fold'))
  labels <- sort(unique(data$target))
  candidates <- if (name=='khan') expand.grid(C=c(.1,1,10),gamma=.1) else expand.grid(C=c(.1,1,10),gamma=c(.01,.1,1))
  # Python ParameterGrid 按 C 然后 gamma 排序，使平分时的规则一致。
  candidates <- candidates[order(candidates$C,candidates$gamma), ]
  scores <- numeric(nrow(candidates))
  kernel <- if (name=='khan') 'linear' else 'radial'
  for (i in seq_len(nrow(candidates))) {
    fold_scores <- numeric(5)
    for (f in 0:4) {
      a <- train[train$fold!=f, ]; b <- train[train$fold==f, ]
      state <- fit_preprocessor(a[features])
      model <- e1071::svm(x=transform_features(a[features],state),y=factor(a$target,levels=labels),kernel=kernel,cost=candidates$C[i],gamma=candidates$gamma[i],scale=FALSE)
      pred <- as.numeric(as.character(predict(model,transform_features(b[features],state))))
      fold_scores[f+1] <- macro_f1(b$target,pred,labels)
    }
    scores[i] <- mean(fold_scores)
  }
  best <- which.max(scores)
  state <- fit_preprocessor(train[features])
  model <- e1071::svm(x=transform_features(train[features],state),y=factor(train$target,levels=labels),kernel=kernel,cost=candidates$C[best],gamma=candidates$gamma[best],scale=FALSE)
  prediction <- predict(model,transform_features(test[features],state),decision.values=TRUE)
  pred <- as.numeric(as.character(prediction))
  score <- NULL
  if (length(labels)==2) {
    values <- attr(prediction,'decision.values')
    positive <- strsplit(colnames(values)[1], '/',fixed=TRUE)[[1]][1]
    score <- as.numeric(values[,1]) * if (positive==as.character(labels[2])) 1 else -1
  }
  confusion <- unclass(table(factor(test$target,levels=labels),factor(pred,levels=labels)))
  list(case=name, language='R', train_n=nrow(train),test_n=nrow(test), parameters=as.list(candidates[best,]),cv_macro_f1=scores[best],accuracy=mean(pred==test$target),macro_f1=macro_f1(test$target,pred,labels),labels=labels,confusion=confusion,support_vectors=nrow(model$SV),score=score,truth=test$target)
}

evaluation_html_r <- function(id='heart-roc-r') {
  r <- fit_case_r('heart')
  thresholds <- c(Inf,sort(unique(r$score),decreasing=TRUE))
  positive <- r$truth==1
  counts <- vapply(thresholds,function(t) c(tp=sum(r$score>=t & positive),fp=sum(r$score>=t & !positive)),numeric(2))
  recall <- counts[1,]/sum(positive); fpr <- counts[2,]/sum(!positive)
  precision <- ifelse(colSums(counts)==0,1,counts[1,]/colSums(counts))
  auc <- sum(diff(fpr)*(head(recall,-1)+tail(recall,-1))/2)
  ap <- sum(diff(recall)*tail(precision,-1))
  fig <- list(data=list(
    list(type='scatter',mode='lines',x=fpr,y=recall,name=sprintf('ROC · AUC=%.3f',auc)),
    list(type='scatter',mode='lines',x=recall,y=precision,name=sprintf('PR · AP=%.3f',ap),visible='legendonly')),
    layout=list(title='Heart · R：点击图例切换 ROC/PR',height=560,xaxis=list(title='FPR（ROC）/ Recall（PR）',range=c(0,1)),yaxis=list(title='TPR（ROC）/ Precision（PR）',range=c(0,1.02))))
  encoded <- jsonlite::toJSON(fig,auto_unbox=TRUE,digits=8)
  paste0('<div class="plotly-output" id="',id,'" data-plotly-source="',id,'-json"></div><script type="application/json" id="',id,'-json">',encoded,'</script>')
}

binary_html_r <- function(name='linear',kernel='linear',C=1,gamma=1,id='binary-r') {
  d <- read.csv(paste0('data/',name,'.csv'))
  tr <- d[d$split=='train', ]; features <- c('x1','x2')
  state <- fit_preprocessor(tr[features])
  model <- e1071::svm(x=transform_features(tr[features],state),y=factor(tr$target),kernel=kernel,cost=C,gamma=gamma,scale=FALSE)
  axis <- seq(-3,3,length.out=61)
  q <- expand.grid(x1=axis,x2=axis)
  pred <- predict(model,transform_features(q,state),decision.values=TRUE)
  values <- attr(pred,'decision.values')
  sign <- if (strsplit(colnames(values)[1], '/',fixed=TRUE)[[1]][1]=='1') 1 else -1
  z <- matrix(as.numeric(values)*sign,nrow=61,byrow=TRUE)
  rows <- lapply(seq_len(nrow(z)),function(i) as.numeric(z[i,]))
  traces <- list(list(type='contour',x=axis,y=axis,z=rows,colorscale=list(list(0,'#dceaf8'),list(.5,'#ffffff'),list(1,'#f9e8d4')),showscale=FALSE,opacity=.55,contours=list(coloring='heatmap',showlines=FALSE),line=list(width=0)))
  for (level in c(0,1,-1)) {
    paths <- contourLines(x=axis,y=axis,z=t(z),levels=level)
    label <- if (level==0) '决策边界 f(x)=0' else if (level==1) '正侧间隔线 f(x)=+1' else '负侧间隔线 f(x)=−1'
    color <- if (level==0) '#17324d' else if (level==1) '#137d80' else '#b96a15'
    for (j in seq_along(paths)) traces[[length(traces)+1]] <- list(type='scatter',mode='lines',x=paths[[j]]$x,y=paths[[j]]$y,name=label,legendgroup=label,showlegend=j==1,line=list(color=color,width=if (level==0) 3.5 else 2,dash=if (level==0) 'solid' else 'dash'),hovertemplate=paste0(label,'<extra></extra>'))
  }
  for (k in 0:1) {
    p <- d[d$target==k, ]
    traces[[length(traces)+1]] <- list(type='scatter',mode='markers',name=paste('类别',k),x=p$x1,y=p$x2,marker=list(color=c('#245e91','#d17b26')[k+1],symbol=ifelse(p$split=='train','circle','diamond-open')))
  }
  p <- tr[model$index, ]
  traces[[length(traces)+1]] <- list(type='scatter',mode='markers',name='支持向量',x=p$x1,y=p$x2,marker=list(symbol='circle-open',size=13,color='#17324d'))
  fig <- list(data=traces,layout=list(title=sprintf('R · %s, C=%g, γ=%g',kernel,C,gamma),height=860,xaxis=list(title='x₁'),yaxis=list(title='x₂',scaleanchor='x')))
  encoded <- jsonlite::toJSON(fig,auto_unbox=TRUE,digits=8)
  paste0('<div class="plotly-output" id="',id,'" data-plotly-source="',id,'-json"></div><script type="application/json" id="',id,'-json">',encoded,'</script>')
}

figure_html_r <- function(result, id) {
  z <- lapply(seq_len(nrow(result$confusion)),function(i) as.numeric(result$confusion[i,]))
  figure <- list(data=list(list(type='heatmap',z=z,x=as.character(result$labels),y=as.character(result$labels),colorscale='Blues',text=z,texttemplate='%{text}',hovertemplate='真实=%{y}<br>预测=%{x}<br>数量=%{z}<extra></extra>')),
    layout=list(title=sprintf('%s · R 测试集：accuracy=%.3f, macro-F1=%.3f',result$case,result$accuracy,result$macro_f1),height=560,xaxis=list(title='预测类别'),yaxis=list(title='真实类别')))
  encoded <- jsonlite::toJSON(figure,auto_unbox=TRUE, digits=8, force=TRUE)
  paste0('<div class="plotly-output" id="',id,'" data-plotly-source="',id,'-json"></div><script type="application/json" id="',id,'-json">',encoded,'</script>')
}
