# 支持向量机：从几何到现代学习

赵知行原SVM笔记的交互教程重构。Python为主、核心R对照，Plotly交互与教学控件。

在VS Code打开本目录，用「终端 → 运行任务」选择预览或构建；完整说明见[使用指南](使用VSCode制作与维护QuartoBook.md)。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 preview
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 render
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 validate
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 serve
```

本地阅读地址：http://localhost:4317。源码修改`.qmd`，产出`_book/`。

工具：Quarto1.9.38（英文路径）、R4.5.3、项目`.R-library`、Python3.12 `.venv`及requirements版本。迁移说明见[MIGRATION.md](MIGRATION.md)。

交付验收见[reports/QA.md](reports/QA.md)：6项数值测试、三个Python/R案例一致、11页构建及浏览器交互检查。图表资源本地交付；默认MathJax公式资源需要网络。
