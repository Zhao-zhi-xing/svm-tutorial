# 支持向量机自学教程

从分类问题、间隔与软间隔，到对偶/KKT、核与RKHS、SMO、多分类及评估；理论之后提供完整Python/R实践、真实数据案例与研究导读。共13个学习章节，加不编号导读和参考文献。交互图使用本地Plotly和离散预计算模型，无模型服务器。

在线阅读：[SVM教程](https://zhao-zhi-xing.github.io/svm-tutorial/)。

在VS Code打开本目录，使用终端运行项目任务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 preview
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 render
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 validate
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 serve
```

预览/本地阅读地址：`http://localhost:4317`。完整操作见[制作与维护指南](使用VSCode制作与维护QuartoBook.md)，内容审查见[作者记录](docs/内容审查与改写说明.md)。这些作者Markdown保留于源码，不随Pages发布。

数值测试：`python -m pytest tests -q`。教学图更新：`python scripts/teaching.py`。网页可见代码独立执行：`python scripts/check_visible_code.py`。站点验收：`python scripts/content_check.py`，紧凑图验收：`python scripts/chart_check.py`。浏览器检查需要可选Playwright与本机Chrome。

独立Notebook位于 `notebooks/python-svm-start.ipynb`，内嵌同一份Iris数据与固定划分。站点产物位于 `_book/`，由Quarto生成，不手工修改。公式继续使用Quarto的MathJax网络资源。

通过验收后，先提交并推送源码，运行 `python scripts/publish_site.py` 预览差异，`python scripts/publish_site.py --publish` 更新现有gh-pages。部署不会强制覆盖分支，会清理明确退役的作者资源。
