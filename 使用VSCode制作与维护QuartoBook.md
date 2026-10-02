# 使用 VS Code 制作与维护 Quarto Book

这份指南教你维护当前 SVM 教程，并把它改成自己的下一本教程。正文源文件是 `.qmd`；`_book/` 是生成的 HTML。日常修改源文件，再重新构建，不直接修改 `_book/` 中的页面。

## 1. 先认识这条出版路线

Quarto Book 是 Quarto 的书籍项目类型。传统 bookdown 是 R Markdown 上的 R 包；二者都能组织章节、编号和引用，但配置与语法不完全一样。

传统 bookdown 通常使用 `.Rmd`、`_bookdown.yml`、`_output.yml`；本项目使用 `.qmd` 与统一的 `_quarto.yml`。旧的 `\@ref(fig:xxx)` 应改为 Quarto 的 `@fig-xxx`，而不是直接复制旧模板。Quarto Book 对 Python/Jupyter 与 R/knitr 都有支持，所以适合新建双语言教程。

Posit 的官方 FAQ 表示继续维护 R Markdown；bookdown.org 托管服务结束不等于 bookdown 包停止工作。已经稳定的 bookdown 项目不必只为了换工具而重写。本项目是一次内容与程序共同升级，因此直接使用 Quarto，ElegantBookdown 只作为外观参考。

参考：[Quarto FAQ](https://quarto.org/docs/faq/rmarkdown.html)、[bookdown.org 公告](https://posit.co/blog/bookdown-org-sunset)、[创建 Quarto Book](https://quarto.org/docs/books/)。

## 2. 在你的电脑上打开本教程

在 VS Code 选择「文件 → 打开文件夹」，打开 `SVM/quarto-book` 本身。这样 `.vscode/tasks.json` 中的项目任务才会直接出现。也可以在终端运行：

```powershell
code .
```

当前交付保留项目内 Quarto 1.9.38；因为 Windows 上该版本的 Lua 模块加载无法正确处理中文安装路径，实际验证使用英文路径 `C:/Users/HP/.cache/svm-quarto-1.9.38/bin/quarto.cmd`。`.tools/runtime-path.txt` 记录实际位置，项目脚本优先读取它。官方 VS Code 扩展 ID 为 `quarto.quarto`。CLI 负责构建，扩展提供编辑和预览入口，两者不是同一个程序。

查看工具：

```powershell
& 'C:/Users/HP/.cache/svm-quarto-1.9.38/bin/quarto.cmd' --version
code --install-extension quarto.quarto
```

迁移到另一台电脑时，工具和语言库目录不会随源码版本控制。推荐从 [Quarto 官网](https://quarto.org/docs/download/) 安装 CLI 到英文路径；也可以把同版本 Windows ZIP 解压到英文工具目录。将 VS Code 的 `quarto.path` 改为实际 CLI 路径；项目脚本可使用 PATH 上的 Quarto。若保留项目内 `.tools`，需更新 `runtime-path.txt`，避免再次从中文工具路径启动。

`.vscode/settings.json` 使用已验证的英文缓存工具路径。换电脑后，在 VS Code 工作区设置中将 **Quarto: Path** 指向本机英文安装目录中的 CLI，并同步更新 `.tools/runtime-path.txt`；或者使用系统 PATH 上的 Quarto。项目终端任务通过脚本找路径，不依赖扩展的路径展开。

## 3. Python 和 R 环境

本教程固定 Python 包版本在 `requirements.txt`。推荐另建项目虚拟环境：

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

VS Code 的「Python: Select Interpreter」选择 `.venv/Scripts/python.exe`。但编辑器的解释器选择**不自动控制 reticulate**；构建脚本会将该解释器同时写入当前进程的 `RETICULATE_PYTHON` 与 `QUARTO_PYTHON`。

交付使用 Python 3.12 项目 `.venv`，构建脚本优先使用它；建议复现时采用相同版本。`requirements.txt` 固定核心依赖，`requirements.lock.txt` 记录本次验证的完整 Python 包版本。排查中的退出崩溃最终定位到 R 的 `cli` 包读取了精简工具环境中缺失的 `PROCESSOR_ARCHITECTURE`，并非 Python 版本问题。项目 R profile 在该变量缺失时补全它；正常 VS Code 环境已有的值保持不变。

R 需要 `knitr/rmarkdown/reticulate/e1071/jsonlite/renv/ISLR2`。项目 R 包放在 `.R-library/`，不同于系统 R 库：

```powershell
# 换成你电脑上的 Rscript 路径
& 'C:/Program Files/R/R-4.5.3/bin/Rscript.exe' scripts/install-r.R
```

已有 `renv.lock` 时，按锁文件恢复到项目库：

```powershell
& 'C:/Program Files/R/R-4.5.3/bin/Rscript.exe' -e ".libPaths(c('.R-library',.libPaths())); renv::restore(lockfile='renv.lock',library='.R-library',prompt=FALSE)"
```

新机器第一次仍需先安装 `renv`。`install-r.R` 可完成首次初始化，再恢复锁文件。项目 `.Rprofile` 和 `scripts/r-profile.R` 设置项目库，并处理 Windows 中文路径的 UTF-8 会话。

双语言章节采用 **knitr + reticulate**：R 负责代码执行引擎，Python 通过 reticulate 在同一个章节中运行。不要同时把章节设为 `jupyter: python3`；那是另一条执行路径。独立纯 Python 项目可以使用 Jupyter，本教程的最小模板示例会介绍它。

## 4. 预览、构建与阅读

推荐从项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 preview
```

浏览器打开 `http://localhost:4317`。保存 `.qmd` 后，Quarto 会重新渲染相关内容。终端 `Ctrl+C` 停止预览。这里 `Bypass` 仅应用于这次 PowerShell 进程，不修改系统执行策略。

完整构建：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 render
```

构建完成后 `_book/index.html` 是首页。为使搜索和资源加载最可靠，使用静态服务阅读：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 serve
```

VS Code 菜单「终端 → 运行任务」有预览、完整构建、验证实验、重新生成交互数据四个任务；`Ctrl+Shift+B` 运行完整构建。编辑器右上角 Quarto 预览入口可用于单章，整本教程的环境配置以项目任务为准。

如自动检测不到语言路径，可明确指定：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 render -PythonPath 'C:/path/to/python.exe' -RPath 'C:/path/to/Rscript.exe'
```

浏览器阅读已托管的 HTML 不需要 Python 或 R。这里的本地静态服务命令只需要 Python，不需要 R/Quarto；重跑代码和更新结果才需要完整构建环境。

## 5. 理解项目目录

- `_quarto.yml`：教程标题、作者、目录、输出、全局执行选项。
- `index.qmd` 与 `chapters/`：正文；`references.bib`：引用。
- `scripts/`：数据、训练、R/Python 辅助函数与构建脚本。
- `assets/`：样式、本地 Plotly、浏览器交互代码、预计算模型。
- `data/`：共享实验数据和固定划分。
- `tests/` 与 `reports/`：数值检查、验证记录。
- `MIGRATION.md` 与 `docs/`：迁移说明、旧附件和源文件清单。
- `_book/`：可分享的结果，构建会覆盖它。

不要把 `.tools/`、`.R-library/`、`.venv/` 上传为网站资源。

## 6. 添加一个章节

复制一个现有 `.qmd`，例如新建 `chapters/10-my-experiment.qmd`。文件开头：

```yaml
---
title: "我的实验"
---
```

然后在 `_quarto.yml` 的 `book.chapters` 列表中加入文件。目录顺序来自列表，而不是文件名前缀。一个一级标题为教程中的章节名称，正文一般从二级标题开始。

想从零建一个纯 Python 小书，可使用最小结构：

```yaml
project:
  type: book
book:
  title: "我的第一本教程"
  chapters:
    - index.qmd
    - experiment.qmd
format:
  html:
    toc: true
    code-copy: true
```

在 `experiment.qmd` 中设置 `jupyter: python3` 并编写 `{python}` 代码块。这个单语言示例无需 R；当前双语言书则维持 `engine: knitr`。

## 7. 可执行代码与双语言标签页

代码围栏里的 `{python}` 表示渲染时执行；只有 `python`、没有大括号时，只显示代码。常见单元选项：`echo` 控制显示源码，`include` 控制整个单元是否进入输出，`results: asis` 让字符串作为 HTML/Markdown 内容进入文档。

本教程每个计算章节先执行隐藏的 R 设置单元，载入自己的依赖；不要依赖上一章的变量。双语言部分可以这样写：

````markdown
```{r}
#| include: false
source('scripts/setup-chapter.R', encoding='UTF-8')
```

::: {.panel-tabset group="language"}
### Python

```{python}
print(1 + 1)
```

### R

```{r}
print(1 + 1)
```
:::
````

相同 `group="language"` 的标签页会联动。标签切换只是选择已经构建的内容，不会现场运行代码。完整双语言教程需要构建时运行两套代码，即使默认只显示 Python。

## 8. 插图、公式与引用

静态插图语法：

```markdown
![图的说明](assets/my-figure.svg){#fig-example}

参见 @fig-example。
```

公式使用 `$...$` 和 `$$...$$`，需要跨引用时命名：

```markdown
$$f(x)=w^Tx+b.$$ {#eq-score}

参见 @eq-score。
```

编号由 Quarto 管理，不要从旧 notebook 复制手写的 `\tag{9.1}`。标签完整教程唯一，图用 `fig-`、公式用 `eq-`，方便识别。

在 `references.bib` 添加 BibTeX 条目，正文写 `[@islp]` 或 `@islp`。参考文献页面使用 `#refs` 容器。本教程研究文献同时标明年份、出处和预印本身份。

自定义 HTML 交互图可放入带图标签和标题的 fenced div：

````markdown
::: {#fig-interactive}
```{=html}
<section class="lab" data-svm-lab="rbf">
<div class="lab-controls"></div>
<div class="lab-plot"></div>
<div class="lab-stats"></div>
</section>
```
交互式 RBF 参数探索。
:::
````

## 9. 使用 Plotly

Python 示例的图可以这样加入本教程：

````markdown
```{python}
#| results: asis
import plotly.graph_objects as go
fig = go.Figure(go.Scatter(x=[1,2,3], y=[1,4,9], mode='lines+markers'))
fig.update_layout(xaxis_title='x', yaxis_title='x²')
print(lab.figure_html(fig, 'my-unique-plot'))
```
````

`figure_html()` 将数据写成页面内的 JSON，由 `assets/tutorial.js` 读取，使用共用的本地 `plotly.min.js` 绘制。每个图 ID 必须唯一，否则会读取错误的 JSON。

R 实验也可生成 Plotly.js 可识别的数据结构；`figure_html_r()` 示例将 R 计算的混淆矩阵编码成 JSON。这里不用完整 R plotly 包，但读者看到的同样是 Plotly 交互图。如果想用 R plotly 语法扩展其他图，可以另安装 `plotly` 后研究 htmlwidgets 与 Quarto 的嵌入方法。

常用交互包括悬停、矩形缩放、平移、图例隐藏、双击复位及三维旋转。`config` 默认不启用滚轮缩放，减少读正文时误触；可在 `tutorial.js` 中修改。三维图依赖浏览器 WebGL。

标签页隐藏时，图可能以零宽度初始化；本教程监听 `shown.bs.tab` 并调用 `Plotly.Plots.resize`。添加新图时沿用 `.plotly-output` 或 `.lab-plot`，不要写死桌面宽度。

## 10. 维护参数滑块与模型网格

这里有两类交互：超平面和预测分数是浏览器即时计算；C/γ 是切换预计算模型。界面必须告诉读者属于哪类。

修改训练网格的位置为 `scripts/prepare.py`：线性 `costs` 与 RBF `costs/gammas`。每个模型状态保存参数、决策网格、支持向量、训练错误、交叉验证分数和测试指标。

更新时运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 prepare
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 render
```

`prepare` 同时更新 CSV、模型数据、Khan 导出与验证记录。Heart 原始输入已随源码保存在 `sources/Heart.csv`，因此可单独复制教程目录重新生成。原 notebook 的附件已归档，普通重新生成不需要原 notebook；如果要重新提取，执行 `python scripts/prepare.py --extract-notebook '../支持向量机.ipynb'`。也可用 `--heart-source` 指定别的原始 Heart 文件；脚本先检查输入再写产物。

不要只手工改 `models.js` 中的一个指标，那会使图和模型失配。

添加交互模块：先在 `tutorial.js` 增加一个初始化函数，再在 `init()` 中按 `data-svm-lab` 名称分派，最后在 `.qmd` 添加对应容器。控件必须有标签、合理初始值、重置和文字解释。新增实时训练属于另一种架构，不能只给预计算下拉框改名为“训练”。

JSON 用于检查，`models.js` 用于站点加载；使用脚本输出减少浏览器读取本地文件时的限制。Plotly 库在生成脚本中从安装版本导出并本地保存。

## 11. 验证与缓存

```powershell
powershell -ExecutionPolicy Bypass -File scripts/book.ps1 validate
```

数值测试检查教学 SMO、共享划分与模型网格；`validate.py` 运行两套核心实验，写 `reports/validation.json` 并检查一致性。HTML 检查另用浏览器验证控件和链接。本次检查记录在 `reports/QA.md`。

可选自动浏览器验收需要 Playwright（本次版本1.60.0），与正文构建依赖分开。`scripts/browser_check.py` 使用本机 Chrome；路径不同需修改其中的 `executable_path`。在安装了 Playwright 的解释器中运行 `python scripts/browser_check.py`，会临时启动本地服务、检查11页及交互控件，并保存 `reports/browser-validation.json` 和截图。正文和构建本身不需要该包。

本教程默认 `cache: false`，每次完整构建重新计算，适合学习与避免旧结果混入。若以后启用缓存，数据/辅助脚本变化后必须强制重算，并检查缓存失效规则。大型论文实验宜单独运行并保存可追溯结果，不让每次写正文都下载权重或训练大型模型。

发布前至少执行：重新生成所改实验 → 数值验证 → 完整教程构建 → 浏览器检查。生成成功不等于所有统计结论都正确。

## 12. 常见问题

**扩展找不到 Quarto**：确认 CLI 的实际路径；修改工作区 `quarto.path`，重载 VS Code。先用项目任务验证，分清扩展问题和 CLI 问题。

**找不到 Python 包**：编辑器解释器与 reticulate 可能不同。查看 `RETICULATE_PYTHON`，用 `book.ps1 -PythonPath` 指定，并在对应解释器安装 requirements。

**找不到 R 包**：确认 `.R-library` 已恢复，Rscript 版本相符；从项目根运行，而不是某个章节目录。

**中文路径报错**：Windows R 会话使用 UTF-8；`.Rprofile` 和构建脚本已经配置。如果 Pandoc 报 `modules/astshortcode` 找不到且路径乱码，使用英文路径安装的 Quarto CLI，并更新工具指向；项目源码可继续保留在中文路径。

**图不出现**：检查浏览器控制台、`plotly.min.js` 和 `models.js` 是否加载、ID 是否重复，以及是否使用 `results: asis`。只复制一个 HTML、漏掉 assets，是常见原因。

**语言切换后图很窄**：确认 Bootstrap 标签切换事件触发重算尺寸，不在 CSS 中固定宽度。

**公式有原始文本**：确认 MathJax 成功加载、LaTeX 括号匹配及引用标签有效。默认数学资源可能需要网络；完全离线阅读需另外本地化 MathJax。

**编辑生成 HTML 后被覆盖**：修改 `.qmd`、CSS 或脚本，然后重新构建。

## 13. 分享与 GitHub Pages

本地分享时发送整个 `_book/`，接收者用静态服务打开它，而不是只发送首页。首次阅读不需要安装 R/Python。

发布 GitHub Pages 的简单路线是发布已经构建的静态目录：先在本机验证并生成 `_book/`；将其内容放到仓库的 `docs/`；确保有 `.nojekyll`；在仓库 Pages 设置中选择对应分支的 `/docs`。源代码和生成站点可以放在同一个仓库，但目录要区分。

另外也可以使用 `quarto publish gh-pages` 或 GitHub Actions 自动构建。自动构建需要安装相同 Quarto、Python/R 依赖并恢复项目库；不能仅安装 Quarto 扩展。本次交付提供步骤，不直接连接或上传你的 GitHub。

公开站点前检查：相对资源路径、参考书版权、外部数据许可、不要上传个人环境和缓存。Quarto 会改写本站链接；自定义脚本路径也需要测试仓库子路径部署。

官方步骤：[GitHub Pages](https://quarto.org/docs/publishing/github-pages.html)。

## 14. 一次完整的维护练习

新建一章“线性 SVM 与逻辑回归”，加入目录；沿用固定的 Iris 划分；在训练集内分别选参；生成两种语言的混淆矩阵；加一段结果解释和一个练习。运行验证和完整构建，最后在浏览器切换语言、操作图，并检查引用。

完成后，你掌握的不只是套用模板，而是从源码、计算、交互到发布的完整教程制作流程。


## 15. 本次视觉与推导调整的维护入口

本教程以桌面阅读为主。`_quarto.yml` 的 `grid.body-width` 为 1040px，图形在 `assets/tutorial.js` 中统一设置二维几何图高度 860px、三维图高度 800px、其他实验图高度 560px；等比例坐标需要足够高度，单纯拉宽容器不会让正方形绘图区同步变宽。

指标卡片由 `renderStats(el, entries, note)` 生成。每项写成 `[标签, 数值]`；加第三项 `true` 可横跨三列，例如范数或最终分类结果。补充说明单独放在 `note`，配色、字号和边框统一在 `assets/book.css` 的 `.stat-card` 中维护。

二分类图统一使用深蓝粗实线表示 $f=0$、绿色虚线表示 $f=+1$、橙色虚线表示 $f=-1$；距离垂线用红色，支持向量用空心圆。Python/JavaScript 先将相邻网格中的等值线线段连接起来，再绘制虚线，避免线型在每个小格中重新开始。R 使用 `contourLines()` 得到完整路径。背景只显示颜色，不再绘制额外等值线。

0–1 损失在零点发生跳跃，阶跃线的垂直连接仅用于示意不连续，并不代表中间值。填充/空心端点区分零点处的取值。绘图回归测试位于 `tests/test_plot_semantics.py`。

新增数学推导集中在第1至6章，KKT完整推导在 `chapters/03-duality-smo.qmd`。修改公式后既要重新构建，也要检查浏览器中的 MathJax 错误；SMO章节同时计算原始目标、对偶目标和间隙，将推导与运行结果对应起来。


## 16. 独立Notebook与新增对照实验

`notebooks/python-svm-start.ipynb` 不依赖R或项目辅助模块。安装 `requirements-notebook.txt` 后，在VS Code选择Python内核并全部运行。维护时使用nbformat读写Notebook，运行 `scripts/execute-notebook.py` 在独立内核从头验证。Notebook运行依赖与双语言HTML构建依赖分开记录；`requirements-notebook.lock.txt`保存含可选Notebook工具的完整环境版本。

新增对照实验和重复评估的训练代码在 `scripts/experiments.py`，交互在 `assets/experiments-ui.js`。运行 `python scripts/experiments.py` 更新CSV、划分记录与 `assets/experiments.json/js`；常规 `prepare` 也会调用它。然后重新构建HTML。页面容器使用 `data-experiment="scaling|imbalance|calibration|repeated|smo"`，切换对照不会触发实时训练。

教学SMO的 `record_history=True` 保存每次成功更新后的系数、法向量、截距、目标与残差。浏览器重放真实记录，初始状态的w=0不画边界。新增测试检查每步约束与对偶单调性；浏览器验收覆盖每个步骤和样本选择。重复评估CSV包含参数、CV分数、外层分数及划分哈希，JSON保存外层和内层验证ID。


## 17. 居中正文与双侧目录

布局参考 [simple-ml-code 的章节页面](https://acgpp.github.io/simple-ml-code/chapters/chapter6.html)：左侧是教程章节列表，右侧是当前章节的二级标题，正文位于中间。保留 Quarto Book 的搜索、编号、交叉引用和语言标签页。

- `_quarto.yml`：`book.chapters` 使用平铺章节；`book.sidebar` 设置左侧标题；`book.navbar` 设置首页、教程和 GitHub 链接；`toc-title` 与 `toc-depth` 设置右侧目录。
- `assets/book.css`：`--tutorial-body-width` 是正文最大宽度（1040px），`--tutorial-nav-width` 是两侧导航的等宽区域（270px），`--tutorial-gutter` 是正文与目录之间的留白（32px）。同步修改 YAML 的 grid 参数与这些变量。
- 桌面窗口宽度达到 1200px 时，两侧导航占用等宽区域，使正文中心与窗口中心重合；大窗口增加外围留白，正文不会无限拉长。中等窗口收起右侧目录，为正文保留空间。
- 图表使用 `width:100%` 和 `min-width:0`，不再用固定最小宽度撑开正文。Plotly 的窗口变化事件会更新图表宽度，语言标签页切换仍会触发尺寸更新。

构建后可运行 `python scripts/layout_check.py` 检查 1280、1440、1920、2560px 窗口下的正文居中、目录位置、页面溢出、目录锚点和图表缩放。此命令需要可选的 Playwright 开发依赖与本机 Chrome，结果保存至 `reports/layout-validation.json`。

已发布站点：[SVM 教程](https://zhao-zhi-xing.github.io/svm-tutorial/)。源码提交并推送后，在教程根目录执行 `powershell -ExecutionPolicy Bypass -File scripts/book.ps1 render`，再执行 `quarto publish gh-pages --no-render` 更新网站；Quarto 未加入 PATH 时可使用 `.tools/runtime-path.txt` 中记录的完整路径。


## 18. 紧凑热图与模型比较图

C–γ 热图在 `assets/tutorial.js` 的 `tuning()` 中设置 420px 高度，CSS 将它的最大宽度限制为 660px 并居中；格内显示三位小数，悬停保留四位小数与参数值。

Python 混淆矩阵由 `scripts/svm_lab.py` 的 `confusion_plot()` 绘制，R 版本在 `scripts/lab.R` 的 `figure_html_r()`。两者都使用 490px 高度、600px 最大宽度、正方形格子和从上到下的真实类别顺序。颜色编码原始样本数，格内和悬停补充按真实类别归一化的比例；这不会改变模型结果或训练协议。

`compare_models()` 使用水平分组柱形图：浅色为选参时的五折验证分数，深色为独立测试分数。保留固定模型顺序、从零开始的坐标和原始选参记录；末端直接显示三位小数。柱图为 410px 高、最大宽度 880px。

`layout.meta.tutorial_kind` 标记 `confusion` 或 `comparison`；浏览器初始化时据此添加 CSS 类。初始化器必须保留各图明确设置的 `height`、`margin` 和 `font`，否则统一的几何图样式会把统计图再次撑大。

样式借鉴：[Plotly 带标注热图](https://plotly.com/python/annotated-heatmap/)、[Plotly 水平柱形图](https://plotly.com/python/horizontal-bar-charts/)。


## 现代技术文档样式的维护（2026-10-03）

整站样式集中在 `assets/book.css`。顶部变量定义正文最大宽度 1040px、普通阅读宽度 800px、两侧导航宽度 270px，以及字体、蓝色强调、浅灰背景与分隔线。正文采用系统中文无衬线字体，字号 17px、行高 1.85；不需要外部字体服务。

普通段落、标题和列表自动居中；代码、长公式、Python/R 标签页和实验可使用完整正文宽度。不要直接缩窄 `main`，否则几何画布也会变窄。小型图的尺寸单独维护：参数热图 420px 高、混淆矩阵 490px 高、模型比较 410px 高。

`_quarto.yml` 的 `book.chapters` 使用 `href` 指定章节、`text` 指定左侧简短名称；章节 YAML 的 `title` 保留正文完整标题。首页使用 Markdown 一级标题 `# 支持向量机教程 {.unnumbered}`（不要放在 YAML 的 `title` 字符串中），并设置 `number-sections: false`，作为不编号导读；正文各章仍自动编号。新增章节时复制 `.chapter-intro` 区块，写明学习目标和前置知识，不加入未经验证的学习时长。

核心代码默认展开，`code-overflow: scroll` 保留缩进。需要折叠冗长参数和日志时，将对应代码块放在原生 `<details class="result-details">` 中，用 `<summary>查看完整实验记录（参数与指标）</summary>` 命名；HTML 标签与 Markdown 代码块之间留空行。重要推导不折叠，练习解答继续使用 Quarto 的 `callout-tip collapse="true"`。

`assets/footer.html` 为代码增加语言标识，并在 Python/R 标签切换与结果折叠展开后调用 Plotly resize。复制按钮由 Quarto 提供，不要删除其 HTML 标记。

完整构建后运行 `scripts/layout_check.py`、`scripts/chart_check.py` 和 `scripts/browser_check.py` 检查居中、目录、交互与图表；`scripts/reading_check.py` 专门检查普通阅读宽度、首页编号和折叠结果。浏览器检查使用安装了 Playwright 的 Python 与本机 Chrome，不属于读者运行教程的依赖。发布后若仍看到旧样式，可用 Ctrl+F5 刷新。
