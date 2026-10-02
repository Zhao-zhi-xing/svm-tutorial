# 从项目根目录运行；安装到项目库，不修改全局库。
if (.Platform$OS.type=='windows') invisible(Sys.setlocale('LC_CTYPE','English_United States.utf8'))
dir.create('.R-library',showWarnings=FALSE)
.libPaths(c(normalizePath('.R-library'),.libPaths()))
install.packages(c('knitr','rmarkdown','reticulate','e1071','renv','jsonlite','ISLR2'),
  lib='.R-library',repos='https://cloud.r-project.org')
packages <- c('knitr','rmarkdown','reticulate','e1071','renv','jsonlite','ISLR2')
stopifnot(all(vapply(packages,requireNamespace,logical(1),quietly=TRUE)))
renv::snapshot(lockfile='renv.lock',library=.libPaths(),type='all',prompt=FALSE)
