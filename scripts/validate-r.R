source('scripts/r-profile.R',encoding='UTF-8')
source('scripts/lab.R',encoding='UTF-8')
results <- lapply(c('iris','heart','khan'),fit_case_r)
for (i in seq_along(results)) {
  results[[i]]$score <- NULL; results[[i]]$truth <- NULL
  m <- results[[i]]$confusion
  results[[i]]$confusion <- lapply(seq_len(nrow(m)),function(j) as.numeric(m[j,]))
}
jsonlite::write_json(results,'reports/r-results.json',pretty=TRUE,auto_unbox=TRUE,digits=10)
renv::snapshot(lockfile='renv.lock',library=.libPaths(),type='all',prompt=FALSE)
cat('R experiments and lockfile recorded.\n')
