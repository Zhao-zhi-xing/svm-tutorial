if (.Platform$OS.type=='windows') invisible(Sys.setlocale('LC_CTYPE','English_United States.utf8'))
project_lib <- Sys.getenv('SVM_R_LIBRARY',unset=file.path(getwd(),'.R-library'))
if (dir.exists(project_lib)) .libPaths(c(project_lib,.libPaths()))
Sys.setenv(RETICULATE_USE_MANAGED_VENV='no',PYTHONIOENCODING='utf-8')
# cli 3.6.6 calls strcmp(getenv("PROCESSOR_ARCHITECTURE"), "ARM64") on exit.
# Some stripped tool environments omit this Windows variable. This project
# uses the verified Intel x64 host; normal VS Code processes keep their value.
if (.Platform$OS.type=='windows' && !nzchar(Sys.getenv('PROCESSOR_ARCHITECTURE')))
  Sys.setenv(PROCESSOR_ARCHITECTURE=if (grepl('aarch64|arm64',R.version$arch)) 'ARM64' else 'AMD64')
Sys.setenv(RENV_PATHS_ROOT=file.path(getwd(),'.renv-cache'),RENV_CONFIG_AUTOLOADER_ENABLED='FALSE',RENV_CONFIG_CONSENT='TRUE')
