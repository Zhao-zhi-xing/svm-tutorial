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

train_case_r <- function(name='iris') {
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

