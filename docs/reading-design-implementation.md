# 教程整站阅读样式实施记录

2026-10-03，依据用户确认的现代技术文档方案完成。

## 已确定的约束

- 白色正文、浅灰导航、深灰文字、蓝色强调；系统字体，无外部字体服务。
- 正文画布上限 1040px，普通阅读上限 800px；两侧目录对称，页面中心与窗口中心一致。
- 保留 Python/R 与全部 Plotly 交互、分类配色、算法、数据和研究结论。
- 热图 420px、混淆矩阵 490px、模型比较 410px；几何实验保留宽画布。
- 核心代码和推导展开，冗长实验记录使用原生 details；每章提供学习目标与前置知识。

## 实现与配置判断

样式统一在 assets/book.css 的变量和组件规则中；不引入前端框架。导航简称使用 book.chapters 中的 href/text，完整标题保留在章节源码。当前 Quarto 1.9.38 不使用 sidebar-title 作为 Book 自动导航名称。

首页使用带 .unnumbered 的 Markdown 一级标题与 number-sections: false。当前 Quarto 的 Book 编号解析器不把普通 YAML title 字符串末尾的属性识别为不编号标记。首页原生 title block 提供视觉标题，结构性一级标题及其目录父项由首页样式隐藏，避免重复标题；小节链接仍保留。

footer.html 添加代码语言标签；复制按钮保留原生 Quarto 行为。语言切换与 details 展开通过 requestAnimationFrame 调用 Plotly resize。

## 验收记录

完整执行 12 个 Quarto 页面成功。两轮集中截图后，只做行为与尺寸回归，不继续截图打磨。

- reading_check.py：导读/KKT/案例在 1280、1440、1920、2560px 下正文居中、阅读宽度正确，无整页溢出；代码复制、原生折叠、键盘焦点和公式错误检查通过。
- layout_check.py：目录独立、定位及活动状态、窗口变化后图表 resize、重置通过。
- chart_check.py：紧凑热图，Python/R 混淆矩阵尺寸、计数和行占比，CV/测试对照柱图通过。
- browser_check.py：12 页本地资源与内部链接、搜索、语言标签切换、全部预计算状态与控件、3D、SMO 回放和 MathJax 渲染通过；没有浏览器脚本错误。

详细尺寸和交互结果见 reports/reading-validation.json、layout-validation.json、chart-validation.json、browser-validation.json。制作指南已同步更新维护规则。
