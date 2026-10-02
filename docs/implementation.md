# SVM Quarto Book 实施与验证记录

依据：用户已批准的「在 VS Code 中制作带 Plotly 交互图的 SVM Quarto Book」。

## 实施任务

- [x] 1. 构建环境与书籍骨架：本地 Quarto、项目 R 库、VS Code tasks、依赖清单。
- [x] 2. 可复现数据与计算：共享 CSV 划分、Python/R 实验、SMO、实验核对。
- [x] 3. 交互视图：几何、软间隔、核参数、核映射、多分类、评估。
- [x] 4. 中文正文：迁移、纠错、进阶导读、练习、引用和使用指南。
- [x] 5. 完整构建、数值测试、浏览器验收、最终审查。

## 接口与约定

`scripts/prepare.py` 从原始数据生成共享数据和模型网格。
`scripts/svm_lab.py` 提供独立 Python 实验与教学 SMO。
`scripts/lab.R` 提供独立 R 实验，返回 Plotly 图的数据 JSON。
`assets/tutorial.js` 消费 `assets/models.json` 及内嵌 Plotly 数据，渲染交互控件。
所有 CSV 的 `split` 标记由 Python 分层生成并保存，R 读取同一份划分。
所有图使用站点本地 Plotly，HTML 阅读不需要运行语言内核。

## 验证重点

SMO 的盒约束、等式约束、KKT、与 LIBSVM 的预测一致性；预处理无测试集泄漏；
核网格每个参数组合的模型/指标/支持向量对应；OvO 平票与 OvR 分数定义；
标签页隐藏后重显示的图尺寸；无外部 CDN 的图表运行；完整书籍引用和本地链接。

## 决策记录

- 目录未初始化 Git，因此在用户指定的新目录中实施，不创建仓库或提交。
- 使用本地 Quarto 1.9.38 固定版本（2026-05-25 已发布），依赖与工具目录忽略，不进入发布资源。
- R 图以 jsonlite + Plotly.js 生成，避免完整 R plotly 的额外依赖；Python 使用 plotly。两者都是对应语言计算所得结果。
- R 心脏病案例使用显式的训练折预处理函数；Python 使用 Pipeline/ColumnTransformer。

## 实施证据

2026-10-02：Python 3.12.14 下 6 项 pytest 通过；Python/R 的 Iris、Heart、Khan 选参、CV macro-F1 和测试混淆矩阵一致。完整执行并构建 11 个书籍页面；实际启动 Quarto preview。浏览器在仓库子路径下验收所有参数状态、语言切换、3D 旋转和重置、搜索与390px布局，无页面脚本错误或本站请求错误。详见 `reports/QA.md` 与 JSON 验收结果。

独立审查发现的三个 P2 问题均修复：静态阅读依赖过多、工具路径文档不一致、生成器依赖外部输入且检查过晚。浏览器进一步发现3D重置引用了可变相机配置，已修复并复验。原 notebook SHA-256 与迁移清单相同，原文件未改动。
