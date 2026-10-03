# 实验数据

- `linear.csv`：80 个重叠高斯簇样本；生成器 sklearn make_blobs，random_state=19。
- `moons.csv`：180 个双月牙样本；make_moons，noise=0.22，random_state=42。
- `multiclass.csv`：90 个三类高斯簇样本；make_blobs，random_state=12。
- `iris.csv`：scikit-learn 内置 Iris（原始 Fisher/Anderson 数据），150 个样本、四个特征；对应 scikit-learn 数据说明。
- `heart.csv`：旧笔记 `SVM/Heart.csv` 的衍生文件；303 行；删除行号，将 AHD=Yes 编码为 1。这个文件与 ISL Heart 教学数据结构一致，保留原文件的来源限制，公开分享前应核对原数据授权。
- `khan.csv`：从 ISLR2 1.3-2 包的 Khan 导出，63 个训练、20 个测试、2308 个特征；标签 1–4。保留该数据的预定义划分。ISLR2 包许可证 GPL-2，数据原文为 Khan et al. (2001), Classification and diagnostic prediction of cancers using gene expression profiling and artificial neural networks, Nature Medicine 7:673–679。

元数据列 `id/split/fold/target` 不进入特征。除 Khan 外，30% 分层测试集由种子42生成；五折编号保存为0–4。Khan 每类训练样本按原始行序轮流分折。

源码与教学文字许可不替代外部数据许可。参考数据说明：[ISLR2 CRAN](https://cran.r-project.org/package=ISLR2)、[Iris](https://scikit-learn.org/1.6/datasets/toy_dataset.html#iris-dataset)。

`manifest.json` 由生成/验证脚本更新，记录所有CSV的SHA-256，便于确认是否使用同一版本。

`teaching-six-points.json` 是六点连续教学例：三个可行性状态、12个未标准化线性C-SVM模型。不用于泛化指标，与既有训练/测试数据分开。

七点C对照扩展保存在同一教学JSON的 `c_effect` 字段中：保留原六点，再添加正类(-1.5,1.5)，使用C=0.1、0.3、1、3、10、100。它只解释惩罚与范数取舍；不是训练/测试数据，也不改变案例协议。
