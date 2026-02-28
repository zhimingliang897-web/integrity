# 📘 AI6126 Advanced Computer Vision — 考前冲刺精要

*Based on 7 Lectures | Multi-stage Balanced Generation*

---

## 第一部分：全课程考点深度分析

### 1. 跨章节高频考点（列表形式）

| 高频考点 | 出现章节 | 核心内涵 | 考试关联性 |
|----------|-----------|-----------|-------------|
| **卷积操作的数学定义与计算** | Lecture 2, 3 | 离散卷积公式 $u(i,j) = \sum_{l=-a}^{a}\sum_{m=-b}^{b} x(i+l,j+m)w(l,m) + b$；空间尺寸计算 $H_2 = \frac{H_1 - F + 2P}{S} + 1$；FLOPs 计算公式 $(2 \times D_1 \times F^2) \times D_2 \times H_2 \times W_2$ | ⭐⭐⭐（必考计算题） |
| **过拟合/欠拟合与正则化策略** | Lecture 1, 3 | 偏差-方差权衡、早停法、Dropout（训练时随机置零，测试时缩放）、L2正则化、数据增强（Mixup/Cutmix/Mosaic） | ⭐⭐⭐（概念辨析+方案选择） |
| **损失函数与优化器原理** | Lecture 2, 3 | Softmax + Cross-Entropy Loss ($L(\hat{y}, y) = -\sum_i y_i \log \hat{y}_i$)；SGD with Momentum ($v_t = \gamma v_{t-1} + \eta \nabla_\theta L$)；Adam（融合动量与自适应学习率） | ⭐⭐⭐（公式推导+超参影响分析） |
| **Transformer核心机制** | Lecture 4 | Scaled Dot-Product Attention ($\text{Attention}(Q,K,V) = \text{Softmax}(\frac{QK^T}{\sqrt{d_k}})V$)；位置编码（正弦/余弦嵌入）；LayerNorm vs BatchNorm | ⭐⭐⭐（机制理解+公式默写） |
| **目标检测评估指标** | Lecture 6 | IoU（交并比）、NMS（非极大值抑制）、mAP（平均精度均值，含COCO标准 mAP@0.5:0.95） | ⭐⭐⭐（计算题+流程排序） |
| **生成模型范式对比** | Lecture 5 | Autoencoder（确定性重构）、VAE（概率建模+重参数化技巧）、VQ-VAE（离散隐变量）；KL散度在ELBO中的作用 | ⭐⭐⭐（推导填空+优劣比较） |
| **分割任务架构演进** | Lecture 7 | FCN（全卷积网络）、U-Net（跳跃连接）、SETR（ViT适配分割）、Mask R-CNN（RoIAlign + mask分支） | ⭐⭐⭐（结构图识别+模块功能匹配） |

---

### 2. 核心算法深度解析

| 算法 | 优点 | 缺点 | 适用场景 | 关键公式 | 考试关注度 |
|------|------|------|-----------|-----------|-------------|
| **CNN** | 局部连接+权值共享 → 参数高效, 平移不变性（池化层）, 特征层次化提取（浅层边缘→深层语义） | 感受野受限（需堆叠多层）, 难以建模长程依赖, 对输入尺度/旋转敏感 | 图像分类、检测、分割等通用视觉任务 | 卷积输出尺寸： $H_2 = \frac{H_1 - F + 2P}{S} + 1$, FLOPs： $(2 \times D_1 \times F^2) \times D_2 \times H_2 \times W_2$ | ⭐⭐⭐ |
| **Transformers** | 全局感受野（Self-Attention）, 并行计算能力强, 天然支持多模态（文本+图像） | 计算复杂度高（$O(N^2)$）, 小数据集上易过拟合（缺乏归纳偏置）, 需大量预训练数据 | 大规模图像识别（ViT）、端到端检测（DETR）、生成任务（Diffusion） | Self-Attention： $\text{Attention}(Q,K,V) = \text{Softmax}(\frac{QK^T}{\sqrt{d_k}})V$, 位置编码： $PE_{(pos,2i)} = \sin(pos/10000^{2i/d_{\text{model}}})$ | ⭐⭐⭐ |
| **Autoencoder (AE)** | 无监督特征学习, 结构简单，训练稳定, 可用于降维/去噪（DAE） | 无法采样生成新数据（非概率模型）, 隐空间无结构（不可控编辑）, 重建质量一般（L2 loss导致模糊） | 特征提取、异常检测、图像压缩 | 重构损失： $\mathcal{L}_{\text{rec}} = \|x - \hat{x}\|_2^2$ | ⭐⭐ |
| **VAE** | 概率生成模型（可采样）, 隐空间连续平滑（支持插值/编辑）, KL项强制隐变量接近先验（解耦性） | 重建图像模糊（后验坍缩）, ELBO是下界（非精确似然）, 重参数化引入方差 | 图像生成、可控编辑（表情/姿态）、半监督学习 | ELBO（证据下界）： $\mathcal{L}_{\text{ELBO}} = \mathbb{E}_{q_\phi(z|x)}[\log p_\theta(x|z)] - D_{\text{KL}}(q_\phi(z|x)\|p(z))$, KL闭式解（对角高斯）： $D_{\text{KL}} = \frac{1}{2}\sum_j(1 + \log\sigma_j^2 - \mu_j^2 - \sigma_j^2)$ | ⭐⭐⭐ |
| **YOLO** | 单阶段端到端（极快，45 FPS）, 全局推理（避免局部误检）, 网络轻量，适合部署 | 小目标检测性能弱（网格限制）, 定位精度低于两阶段方法, 对重叠目标（IoU高）敏感 | 实时检测（自动驾驶、视频监控）、移动端应用 | 输出张量维度（Pascal VOC）： $7 \times 7 \times (2 \times 5 + 20) = 1470$, 置信度： $P(\text{class}) = P(\text{class}|\text{Object}) \times P(\text{Object})$ | ⭐⭐⭐ |
| **Faster R-CNN** | 两阶段精度最优（COCO mAP最高）, RPN实现区域提议可学习, RoIAlign解决像素错位问题 | 推理速度慢（7 FPS）, 结构复杂（RPN+RCNN双头）, 需NMS后处理 | 高精度需求场景（医疗影像、卫星图像） | RPN损失： $\mathcal{L}_{\text{RPN}} = \lambda_{\text{cls}}\mathcal{L}_{\text{cls}} + \lambda_{\text{reg}}\mathcal{L}_{\text{reg}}$, 边界框回归目标： $t_x = \frac{g_x - p_x}{p_w},\ t_w = \log\frac{g_w}{p_w}$ | ⭐⭐⭐ |
| **Swin Transformer** | 窗口注意力 → 线性复杂度, 移位窗口 → 跨窗连接, 层次化结构 → 多尺度特征 | 实现复杂（移位操作）, 预训练成本仍高, 小模型优势不明显 | 高分辨率图像分割、医学图像分析 | 窗口注意力复杂度： $\Omega_{\text{W-MSA}} = 4hwC^2 + 2M^2 hwC$ ($M$: 窗口大小, $hw$: 总 patch 数) | ⭐⭐⭐ |

> **注**：所有公式均源自课件原文（如Lecture 2第13页卷积公式、Lecture 4第20页Attention、Lecture 5第94页ELBO、Lecture 6第39页bbox回归等），考试要求精准复现。

---

### 3. 知识点考试关注度评级说明

- **⭐⭐⭐（极高关注）**：  
  必考内容，涵盖**计算题（FLOPs/IoU/mAP）、公式默写（Attention/ELBO/Conv尺寸）、机制对比（CNN vs ViT、AE vs VAE）、流程排序（NMS步骤、DETR匈牙利匹配）**。占Quiz和Project评分权重70%以上。

- **⭐⭐（中等关注）**：  
  概念理解题，如**归纳偏置（Inductive Bias）含义、BatchNorm训练/测试差异、Dropout与Ensemble关系、VQ-VAE字典学习原理**。常以选择题或简答题出现。

- **⭐（基础关注）**：  
  背景知识，如**计算机视觉发展史（Hubel & Wiesel, LeNet）、神经缩放定律（Neural Scaling Law）、DETR的Set Prediction思想**。仅作常识性考查。

---
**总结**：本课程以**“模型机理-计算实现-评估验证”三位一体**为脉络，所有高频考点均指向对**数学本质**（公式推导）、**工程权衡**（速度/精度/内存）、**任务范式**（分类/检测/分割/生成）的深度理解。备考需紧扣课件公式与图示，杜绝死记硬背。

---
## 第二部分：模拟备考练习题（含详尽题解）

### MCQ 1-20
以下是严格依据您提供的 **7份课程讲义（lecture_1_intro 至 lecture_7_segmentation）** 设计的 **20道高质量单项选择题（MCQ 1–20）**。题目覆盖课程前5周核心内容（Intro, CNN I/II, Transformers, Autoencoders, Detection），聚焦基础概念、关键计算与原理辨析，所有术语（如ReLU, IoU, FLOPs, ViT, VAE, NMS等）均保留英文，中文仅用于题干、选项与解析说明。

每题均含三要素：  
✅ **【正确答案】**（明确标注）  
✅ **【详细知识点分析】**（紧扣讲义原文页码与逻辑，指出定义、动机、数学本质）  
✅ **【解题思路/题解】**（分步推演、排除干扰项、强调易错点）

---

### **MCQ 1**  
A deep convolutional network learns hierarchical features: shallow layers detect edges and simple shapes, while deeper layers recognize parts and attributes. This hierarchical processing principle was first formally established by which neuroscientist?  
A) Hubel & Wiesel  
B) David Marr  
C) Kunihiko Fukushima  
D) Yann LeCun  

**【正确答案】** B  
**【详细知识点分析】**  
讲义 `lecture_1_intro.pdf` 第38页明确指出：“In 1982, neuroscientist David Marr established that vision works hierarchically and introduced algorithms for machines to detect edges, corners, curves and similar basic shapes.” Hubel & Wiesel (p.31–33) discovered *neural response* to edges in cats; Fukushima (p.39) proposed Neocognitron with convolution; LeCun (p.40) applied CNNs to digit recognition.但“hierarchical processing”这一**理论框架的正式建立者是Marr**。  
**【解题思路/题解】**  
题干关键词是“formally established that vision works hierarchically”。Hubel & Wiesel 的贡献是实验发现（p.31–33），Fukushima 和 LeCun 是工程实现者（p.39–40），而 Marr（p.38）是首位将该机制上升为**计算理论**的科学家。故选 B。

---

### **MCQ 2**  
In supervised learning, we assume training data \((\mathbf{x}_i, y_i)\) are i.i.d. samples from an unknown joint distribution \(P(X,Y)\). What does “i.i.d.” stand for, and why is this assumption critical?  
A) Independent and identical — ensures all samples come from the same generative process and have no memory of past samples  
B) Identical and independent — guarantees zero correlation between any two samples  
C) Independent and identically distributed — implies equal probability for each sample and mutual independence  
D) Identical and identically distributed — a redundancy meaning all samples are copies of one another  

**【正确答案】** C  
**【详细知识点分析】**  
讲义 `lecture_1_intro.pdf` 第104页脚注明确定义：“i.i.d. (independent and identically distributed) — each random variable has the same probability distribution as the others and all are mutually independent”. 同页正文强调：“This assumption is often made for training datasets to imply that all samples stem from the same generative process and that the generative process is assumed to have no memory of past generated samples.” 这是经验风险最小化（ERM）成立的前提（p.108–112）。  
**【解题思路/题解】**  
A 项“identical”用词错误（应为“identically distributed”）；B 项“zero correlation”是 i.i.d. 的推论但非定义；D 项“copies”完全曲解。C 项完整、准确复述讲义定义，且“same probability distribution + mutual independence”是标准统计学表述。

---

### **MCQ 3**  
Consider polynomial regression where the true data-generating function \(g(x)\) is an unknown cubic polynomial, and we use a hypothesis space \(\mathcal{F}\) of polynomials of degree 3. As the number of training samples \(N \to \infty\), what does the empirical risk minimizer \(\hat{\mathbf{w}}_{\mathbf{d}}\) converge to?  
A) The zero vector  
B) The coefficients of \(g(x)\) itself  
C) A vector with minimum L2 norm among all interpolating solutions  
D) The solution of ordinary least squares on a single sample  

**【正确答案】** B  
**【详细知识点分析】**  
讲义 `lecture_1_intro.pdf` 第117页明确结论：“The expected risk minimizer \(\mathbf{w}^*\) within our hypothesis space is \(g\) itself. Therefore, on this toy problem, we can verify that \(\hat{f}(x;\mathbf{w}_{\mathbf{d}}) \to f(x;\mathbf{w}^*) = g(x)\) as \(N \to \infty\).” 这正是**一致收敛性**（consistency）的体现：当模型容量匹配真实函数复杂度时，ERM 收敛到真函数。  
**【解题思路/题解】**  
A、C 是过参数化（\(p \gg n\)）下的现象（p.152–153）；D 显然错误。题干中“hypothesis space of degree 3”与“true \(g(x)\) is cubic”完全匹配，故最优解即真函数系数，选 B。

---

### **MCQ 4**  
A neural network exhibits high bias and low variance. Which of the following is the most direct consequence?  
A) It performs well on training data but poorly on test data  
B) It performs poorly on both training and test data  
C) Its predictions are highly sensitive to small changes in training data  
D) It fails to capture the underlying pattern due to insufficient model complexity  

**【正确答案】** B & D（单选题，选最直接者 → **D**）  
**【详细知识点分析】**  
讲义 `lecture_1_intro.pdf` 第141页定义：“Bias is the difference between the average prediction... and the correct value... Model with high bias pays very little attention to the training data and oversimplifies the model. It always leads to high error on training and test data.” 第146页进一步解释：“This happens when we have insufficient amount of data... or when we try to use an overly simple model.” 高偏差的本质是**欠拟合（underfitting）**，源于模型能力不足（p.123–134）。  
**【解题思路/题解】**  
A 描述的是高方差（过拟合）；C 是高方差的特征；B 是结果，但 D 指出了根本原因（“fails to capture... due to insufficient complexity”），更契合题干“most direct consequence”。讲义 p.146 明确将“insufficient amount of data”和“overly simple model”并列为高偏差成因，故 D 最精准。

---

### **MCQ 5**  
In modern over-parameterized regimes (e.g., ViT-22B), the double descent phenomenon occurs. At the interpolation threshold where \(p = n\) (parameters = samples), what is the primary reason for poor generalization?  
A) The model has insufficient capacity to fit the training set  
B) The L2 norm of parameters is minimized by SGD, acting as implicit regularization  
C) The model exhibits high variance due to fitting noise in the training set  
D) The optimization landscape contains many saddle points that trap SGD  

**【正确答案】** C  
**【详细知识点分析】**  
讲义 `lecture_1_intro.pdf` 第153页：“When \(p = n\), the model possesses just enough parameters to over-fit all the training data. However, it also exhibits a significant variance, making it unable to generalize.” 这正是 double descent 曲线在 \(p=n\) 处出现**泛化误差尖峰**的原因——模型恰好插值所有训练点，对噪声极度敏感（high variance）。B 项描述的是 \(p \gg n\) 时的正则化效应（p.153）；D 项是 SGD 的通用性质（p.154），非 \(p=n\) 特有。  
**【解题思路/题解】**  
A 错误（此时已能完美拟合）；B 是 \(p \gg n\) 的优势；D 是背景知识，非主因。C 直接对应讲义原文“significant variance, making it unable to generalize”，故为答案。

---

### **MCQ 6**  
Given an input volume of size \(3 \times 32 \times 32\) and a convolutional layer with ten \(3 \times 5 \times 5\) filters, stride 1, and zero padding of 2, what is the total number of trainable parameters in this layer?  
A) 380  
B) 760  
C) 1,520  
D) 3,040  

**【正确答案】** B  
**【详细知识点分析】**  
讲义 `lecture_2_cnn.pdf` 第49页例题：“Each filter has \(5 \times 5 \times 3 + 1 = 76\) params (+1 for bias) ⇒ \(76 \times 10 = 760\).” 计算逻辑：每个 filter 的权重数 = spatial_size × input_channels = \(5 \times 5 \times 3 = 75\)，加 1 个 bias，共 76；10 个 filters 共 \(76 \times 10 = 760\)。padding 和 stride 不影响参数量（只影响输出尺寸）。  
**【解题思路/题解】**  
A=76（单 filter）；C=1520（误×2）；D=3040（误×4）。严格按讲义 p.49 计算，得 B。

---

### **MCQ 7**  
A convolutional layer uses a \(1 \times 1\) filter on an input volume of size \(64 \times 56 \times 56\). What is the primary purpose of such a “pointwise convolution”?  
A) To reduce spatial resolution via subsampling  
B) To increase the number of channels while preserving spatial dimensions  
C) To perform depthwise separation for computational efficiency  
D) To blend information across channels via linear combination  

**【正确答案】** D  
**【详细知识点分析】**  
讲义 `lecture_3_cnn.pdf` 第43页：“Why having filter of spatial size \(1 \times 1\)? • Change the size of channels • ‘Blend’ information among channels by linear combination.” 第44页补充：“1×1 convolutions are used for compute reductions before expensive 3×3 and 5×5 convolutions.” 其本质是跨通道的线性变换（linear combination），而非单纯增减通道数（B 项片面）或深度分离（C 是 depthwise conv）。  
**【解题思路/题解】**  
A 是 pooling 或 stride>1 conv 的功能；B 是效果之一，但“primary purpose”是讲义强调的“blend information”（p.43）；C 是 depthwise conv 的定义（p.47）；D 准确概括了其数学本质（线性组合），故为最佳答案。

---

### **MCQ 8**  
Batch Normalization (BN) computes per-channel statistics (mean \(\mu_j\), variance \(\sigma_j^2\)) over a mini-batch during training. Why are these statistics *not* computed over the entire dataset or a single sample?  
A) Computing over the full dataset is computationally infeasible; over a single sample yields undefined variance  
B) BN requires stochasticity for regularization; full-dataset stats would eliminate gradient noise  
C) Mini-batch statistics provide unbiased estimates of population statistics and enable efficient gradient flow  
D) BN’s effectiveness relies on the *inter-sample variation* within a batch to normalize activations  

**【正确答案】** D  
**【详细知识点分析】**  
讲义 `lecture_3_cnn.pdf` 第66–67页图示及公式：BN 对 mini-batch 中同一 channel 的所有样本（如 \(N \times D\) 矩阵的第 j 列）计算 \(\mu_j, \sigma_j^2\)，即利用 batch 内 variation 进行归一化。第72页指出测试时需用 moving average（因无 batch）。p.81 提到 BN 平滑优化景观，但核心设计动机是利用 batch variation（p.66–67）。  
**【解题思路/题解】**  
A 中“undefined variance”不成立（单样本方差可定义为0）；B 将 BN 误作 dropout；C 中“unbiased estimates”非主要目的（BN 本质是 heuristic）；D 直接对应讲义图示（p.66）和“normalize the values across samples, the same row/the same channel”（p.66），故为答案。

---

### **MCQ 9**  
In the scaled dot-product attention mechanism, the query-key dot product is divided by \(\sqrt{D_k}\) (where \(D_k\) is key dimension). What is the primary reason for this scaling?  
A) To ensure numerical stability during floating-point computation  
B) To prevent softmax saturation and maintain gradient magnitude  
C) To make the attention weights sum to 1 across all tokens  
D) To align the output variance with the input variance  

**【正确答案】** B  
**【详细知识点分析】**  
讲义 `lecture_4_transformers.pdf` 第23页：“Why dividing by \(\sqrt{D_k}\)? This leads to having more stable gradients (large similarities will cause softmax to saturate and give vanishing gradients).” 若不缩放，大维度下点积方差增大，softmax 输入过大，导致输出趋近 one-hot，梯度消失（vanishing gradients）。  
**【解题思路/题解】**  
A 是数值计算常识，非此设计主因；C 是 softmax 自然属性，无需缩放保证；D 是间接效果，非设计目标。B 直接引用讲义原文，是唯一正确动机。

---

### **MCQ 10**  
A Vision Transformer (ViT) processes an image by splitting it into non-overlapping patches, linearly embedding each patch, adding positional encoding, and feeding the sequence to a Transformer encoder. Compared to CNNs, ViT has significantly less *inductive bias*. Which of the following is NOT an inductive bias inherent to CNNs but absent in standard ViT?  
A) Translation equivariance  
B) Locality (local connectivity)  
C) Two-dimensional neighborhood structure  
D) Global self-attention over all tokens  

**【正确答案】** D  
**【详细知识点分析】**  
讲义 `lecture_4_transformers.pdf` 第70页：“Inductive bias in CNN • Locality • Two-dimensional neighborhood structure • Translation equivariance... ViT • Only MLP layers are local and translationally equivariant. Self-attention layer is global.” 可见 A/B/C 均是 CNN 的 inductive bias，而 D（global self-attention）是 ViT 的**特性**，非 CNN 的 bias，更非“absent in ViT”。题干问“NOT an inductive bias inherent to CNNs but absent in ViT”，D 完全不符合逻辑（它是 ViT 的 feature）。  
**【解题思路/题解】**  
A/B/C 均在讲义 p.70 明确列为 CNN bias；D 是 ViT 的核心机制（p.71），故为“NOT an inductive bias of CNN”，且它在 ViT 中存在，因此是唯一符合题干双重否定的选项。

---

### **MCQ 11**  
An autoencoder is trained to reconstruct its input \(x\) from a latent code \(z\). If the encoder and decoder are both linear functions and the loss is mean squared error (MSE), the learned representation is mathematically equivalent to which classical method under certain normalization?  
A) Principal Component Analysis (PCA)  
B) Linear Discriminant Analysis (LDA)  
C) Independent Component Analysis (ICA)  
D) t-Distributed Stochastic Neighbor Embedding (t-SNE)  

**【正确答案】** A  
**【详细知识点分析】**  
讲义 `lecture_5_autoencoder.pdf` 第49页：“Linear-linear encoder-decoder with Euclidian loss is actually equivalent to PCA (under certain data normalization).” 这是经典结论：线性 AE 的 bottleneck 层基向量即数据协方差矩阵的 top-k 特征向量，与 PCA 完全一致。  
**【解题思路/题解】**  
B/LDA 用于监督降维；C/ICA 寻找统计独立分量；D/t-SNE 是非线性可视化方法。仅 A 在讲义中被明确等价，故选 A。

---

### **MCQ 12**  
In Variational Autoencoders (VAEs), the encoder outputs parameters \((\mu_{z|x}, \Sigma_{z|x})\) of a Gaussian distribution \(q_\phi(z|x)\), and the reparameterization trick is used: \(z = \mu_{z|x} + \Sigma_{z|x}^{1/2} \cdot \epsilon\), where \(\epsilon \sim \mathcal{N}(0,I)\). Why is this trick essential?  
A) It allows backpropagation through the stochastic sampling step  
B) It ensures the latent space is perfectly disentangled  
C) It guarantees the KL divergence term is zero  
D) It makes the decoder output deterministic  

**【正确答案】** A  
**【详细知识点分析】**  
讲义 `lecture_5_autoencoder.pdf` 第122页图示标题：“Backprop?” 并配文：“Does not depend on parameters” — 指出若直接采样 \(z \sim q_\phi(z|x)\)，反向传播无法通过随机节点。reparameterization 将随机性从参数中解耦，使 \(z\) 成为 \(\phi\) 的确定性函数，从而支持梯度下降（p.99–108）。  
**【解题思路/题解】**  
B 是 VAE 的期望效果，非 re

---
### MCQ 21-40 + 填空题
以下为严格依据您提供的全部课程资料（lecture_1_intro.pdf 至 lecture_7_segmentation.pdf）设计的 **20 道单项选择题（MCQ 21–40）** 与 **6 道填空题**。所有题目均聚焦于 **目标检测（Object Detection）、图像分割（Segmentation）及高级模型（ViT, DETR, Mask R-CNN, VAE, Swin, Autoencoder）**，完全覆盖课程中讲授的核心技术、公式、架构与评估指标。

每道题均包含三要素：  
✅ **【正确答案】**（明确标注）  
✅ **【详细知识点分析】**（紧扣课件原文，标注页码与关键句）  
✅ **【解题思路/题解】**（逻辑推导、排除法或数值验证）

---

### ✅ 一、20 道单项选择题（MCQ 21–40）

---

**MCQ 21.**  
在 Faster R-CNN 中，Region Proposal Network (RPN) 在每个特征图位置使用 K 个 anchor boxes 的主要目的是：  
A. 减少 RoI Align 的计算量  
B. 解决 anchor box 尺寸/长宽比不匹配真实物体的问题  
C. 替代 Non-Max Suppression (NMS) 步骤  
D. 加速 CNN backbone 的前向传播  

**【正确答案】** B  
**【详细知识点分析】**  
课件 `lecture_6_detection.pdf` 第110页明确指出：“Problem: Anchor box may have the wrong size / shape. Solution: Use K different anchor boxes at each point!”（问题：anchor box 可能尺寸/形状错误；解决方案：在每个点使用 K 个不同 anchor）。该设计是 RPN 能够适应多尺度、多长宽比物体的关键机制（第105–110页）。  
**【解题思路/题解】**  
选项 A 错误：RoI Align 是 Fast R-CNN 后续步骤，与 anchor 数量无关；选项 C 错误：NMS 仍用于后处理 RPN 输出（第52页）；选项 D 错误：增加 anchor 数会略微增加计算，而非加速。唯一符合课件原意的是 B。

---

**MCQ 22.**  
DETR 模型采用 Hungarian matching 进行训练时，其匹配成本（matching cost）不包括以下哪一项？  
A. 分类损失（Classification cost）  
B. L1 距离损失（L1 distance between predicted and GT box coordinates）  
C. GIoU 损失（GIoU loss）  
D. KL 散度损失（KL divergence between predicted and GT distributions）  

**【正确答案】** D  
**【详细知识点分析】**  
课件 `lecture_6_detection.pdf` 第145页清晰列出匹配成本组成：“Minimize matching cost consisting of: • Classification cost • L1 distance between boxes • IoU between boxes”。第146页进一步说明损失函数包含“Classification loss”、“Box regression loss : L1 loss”和“GIoU loss”。全篇未提及 KL 散度用于 DETR 匹配（KL 散度仅出现在 VAE 讲义 `lecture_5_autoencoder.pdf` 中）。  
**【解题思路/题解】**  
A、B、C 均被课件直接引用；D 是 VAE 的核心概念（`lecture_5_autoencoder.pdf` 第94–98页），与 DETR 无关，故为正确排除项。

---

**MCQ 23.**  
在 U-Net 架构中，skip connection 的核心作用是：  
A. 实现残差学习以缓解梯度消失  
B. 将低层高分辨率特征与高层语义特征融合，恢复空间细节  
C. 替代 batch normalization 层以减少参数  
D. 引入随机 dropout 以增强泛化能力  

**【正确答案】** B  
**【详细知识点分析】**  
课件 `lecture_7_segmentation.pdf` 第42–44页图示并文字说明：“While the output is HxW, just upsampling often produces results without details/not aligned with the image.”（仅上采样导致细节丢失）→ “How do you send details forward in the network? You copy the activations forward.”（通过复制激活值前传细节）。第45页指出 U-Net “Extremely popular architecture, was originally used for biomedical image segmentation”，其 skip connection 正为此目的设计。  
**【解题思路/题解】**  
A 是 ResNet 的设计动机（`lecture_3_cnn.pdf` 第19–20页），非 U-Net；C、D 在课件中未关联 skip connection（BN 见 `lecture_3_cnn.pdf` 第61–80页；Dropout 见第82–115页）。

---

**MCQ 24.**  
Swin Transformer 通过以下哪种机制实现线性计算复杂度（Ω ∝ ℎ𝑤），区别于 ViT 的二次复杂度（Ω ∝ (ℎ𝑤)²）？  
A. 使用 1×1 卷积替代 self-attention  
B. 限制 self-attention 在非重叠局部窗口内计算（Window-based MSA）  
C. 移除 positional encoding 以降低维度  
D. 采用 depthwise separable convolution 作为 backbone  

**【正确答案】** B  
**【详细知识点分析】**  
课件 `lecture_4_transformers.pdf` 第79页公式对比：ViT 的 Ω_MSA = 4ℎ𝑤𝐶² + 2(ℎ𝑤)²𝐶（二次），而 Swin 的 Ω_W−MSA = 4ℎ𝑤𝐶² + 2𝑀²ℎ𝑤𝐶（线性）。第80–81页解释：“In W-MSA, there are ℎ/𝑀 × 𝑤/𝑀 windows. In each window, the complexity ... is (𝑀²)²𝐶 ... total complexity is 𝑀²ℎ𝑤𝐶”。第73页标题即点明：“Perform local self-attention thus having linear computational complexity”。  
**【解题思路/题解】**  
A、C、D 均未在 Swin 讲义中出现；B 是课件唯一强调的线性化机制，且与公式推导完全一致。

---

**MCQ 25.**  
在 Variational Autoencoder (VAE) 中，reparameterization trick 的核心数学表达是：  
A. \( z = \mu_{z|x} + \epsilon \cdot \sigma_{z|x},\ \epsilon \sim \mathcal{N}(0,I) \)  
B. \( z = \mu_{z|x} + \sigma_{z|x} \cdot \epsilon,\ \epsilon \sim \mathcal{U}(0,1) \)  
C. \( z = \text{tanh}(\mu_{z|x}) + \epsilon \cdot \sigma_{z|x},\ \epsilon \sim \mathcal{N}(0,I) \)  
D. \( z = \mu_{z|x} \cdot \epsilon + \sigma_{z|x},\ \epsilon \sim \mathcal{N}(0,I) \)  

**【正确答案】** A  
**【详细知识点分析】**  
课件 `lecture_5_autoencoder.pdf` 第122页图示明确显示：“Sample z from encoder output”路径中，\( z = \mu + \epsilon \cdot \sigma \)，且旁注“e ~ N(0,I)”。第104页公式亦给出闭式解推导基础：“Assume q is diagonal Gaussian and p is unit Gaussian”，其 reparameterization 正是标准形式。  
**【解题思路/题解】**  
B 错误：ε 必须服从标准正态分布（非均匀分布）；C 错误：tanh 非 VAE 标准操作（课件中 tanh 仅作 activation 对比，见 `lecture_2_cnn.pdf` 第68页）；D 错误：乘法顺序颠倒，破坏可微性。

---

**MCQ 26.**  
Mask R-CNN 相较于 Faster R-CNN 的关键改进在于：  
A. 用 transformer 替换 RPN  
B. 在 RoI Align 后增加一个 mask head，输出 C×28×28 的 per-class mask  
C. 移除 bounding box regression 分支  
D. 采用 multi-head attention 替代 RoI Pooling  

**【正确答案】** B  
**【详细知识点分析】**  
课件 `lecture_7_segmentation.pdf` 第76页架构图清晰展示：Mask R-CNN 在 Faster R-CNN 的 RoI Align 输出（256×28×28）后，接一个“Predict a mask for each of C classes: C x 28 x 28”的分支。第74–75页标题即为“Instance Segmentation: Mask R-CNN”，并强调其“Perform object detection, then predict a segmentation mask for each object!”（第72页）。  
**【解题思路/题解】**  
A、D 未在课件中提及（transformer 用于 DETR）；C 错误：Mask R-CNN 完全保留 Faster R-CNN 的分类与回归分支（第76页图示含“Classification Scores”和“Box coordinates”）。

---

**MCQ 27.**  
在语义分割任务中，FCN（Fully Convolutional Network）使用 per-pixel cross-entropy loss 的输入维度是：  
A. \( C \times H \times W \)（C 类别数，H/W 图像高宽）  
B. \( 1 \times H \times W \)（单通道预测图）  
C. \( 3 \times H \times W \)（RGB 输入维度）  
D. \( 2 \times H \times W \)（二分类输出）  

**【正确答案】** A  
**【详细知识点分析】**  
课件 `lecture_7_segmentation.pdf` 第12页架构图标注：“Scores: C x H x W”，并注明“Loss function: Per-Pixel cross-entropy”。第51页公式 \( -\log \frac{\exp(Wx_i)}{\sum_k \exp(Wx_k)} \) 明确要求输入为 C 维 logits（即 C×H×W）。课件从未将 loss 输入设为单通道（B）或 RGB（C）。  
**【解题思路/题解】**  
cross-entropy loss 必须作用于类别概率分布（需 C 维 logits），故 A 正确；B 是 argmax 后的整型标签图，非 loss 输入。

---

**MCQ 28.**  
YOLOv1 的输出张量维度为 \( 7 \times 7 \times (2 \times 5 + 20) = 7 \times 7 \times 30 \)。其中 “2×5” 的 “5” 代表每个 bounding box 预测的 5 个值，它们是：  
A. \( (x, y, w, h, \text{confidence}) \)  
B. \( (x, y, w, h, \text{class\_prob}) \)  
C. \( (x, y, w, h, \text{IoU}) \)  
D. \( (x, y, w, h, \text{objectness}) \)  

**【正确答案】** A  
**【详细知识点分析】**  
课件 `lecture_6_detection.pdf` 第123–124页图示：“Each cell predicts B boxes(x,y,w,h) and confidences of each box: P(Object)”。第131页公式：“P(class|Object) * P(Object) = P(class)”，其中 P(Object) 即 confidence score。第133页总结：“For each bounding box: 4 coordinates (x, y, w, h), 1 confidence value”。  
**【解题思路/题解】**  
“confidence” 在 YOLO 中定义为 \( \text{P(Object)} \times \text{IoU}_{\text{pred,truth}} \)（课件虽未写全，但第131页“Box confidence score”即此含义），是标准术语；B 的 class_prob 是条件概率，非 confidence；C、D 非课件术语。

---

**MCQ 29.**  
在计算卷积层 FLOPs 时，若输入为 \( D_1 \times H_1 \times W_1 \)，滤波器为 \( D_1 \times F \times F \)，输出为 \( D_2 \times H_2 \times W_2 \)，则总 FLOPs 公式为：  
A. \( (2 \times D_1 \times F^2) \times D_2 \times H_2 \times W_2 \)  
B. \( (D_1 \times F^2 + D_1 \times (F^2 - 1) + 1) \times D_2 \times H_2 \times W_2 \)  
C. \( D_1 \times F^2 \times D_2 \times H_2 \times W_2 \)  
D. \( (2 \times D_1 \times F^2) \times H_2 \times W_2 \)  

**【正确答案】** A  
**【详细知识点分析】**  
课件 `lecture_3_cnn.pdf` 第39页明确给出：“FLOPs = (2 × D₁ × F²) × D₂ × H₂ × W₂”。第37页解释：“𝐷₁ × 𝐹² + 𝐷₁ × 𝐹² − 1 + 1 = (2 × 𝐷₁ × 𝐹²)”，即每个空间位置需 \( 2D_1F^2 \) 次浮点运算（\( D_1F^2 \) 次乘 + \( D_1F^2-1 \) 次加 + 1 次加 bias），再乘以 \( D_2H_2W_2 \) 个输出元素。  
**【解题思路/题解】**  
B 是未简化形式（第39页公式左侧），但课件最终采用 A 的简洁形式；C 缺少加法项；D 缺少 \( D_2 \) 维度。

---

**MCQ 30.**  
DETR 的 object queries 是：  
A. 从训练数据中采样的真实 bounding boxes  
B. 由 CNN backbone 提取的图像 patch embeddings  
C. 一组可学习的、固定数量的嵌入向量（通常 100 个），初始化为零  
D. ViT 中的 [class] token 复制而来  

**【正确答案】** C  
**【详细知识点分析】**  
课件 `lecture_6_detection.pdf` 第143页图示：“N , typically 100, initialized with zeros”，并文字说明：“Query embeddings distinguish output positions (object slots)”。第138页描述：“A transformer decoder then takes as input a small fixed number of learned positional embeddings (object queries)”。  
**【解题思路/题解】**  
A、B 是 encoder 输入；D 错误：ViT 的 [class] token 用于分类（`lecture_4_transformers.pdf` 第66–67页），DETR 的 queries 是 decoder 独立参数。

---

**MCQ 31.**  
Panoptic Segmentation 的核心定义是：  
A. 仅对“things”类别进行实例级分割  
B. 对所有像素分配类别标签，并对“things”类别额外区分实例 ID  
C. 结合 semantic 和 instance segmentation 的 ensemble 方法  
D. 使用 GAN 生成全景分割掩码  

**【正确答案】** B  
**【详细知识点分析】**  
课件 `lecture_7_segmentation.pdf` 第84页定义：“Label all pixels in the image (both things and stuff) ... For ‘thing’ categories also separate into instances”。第82页对比：“Instance Segmentation: Separate object instances, but only things! Semantic Segmentation: Identify both things and stuff, but doesn’t separate instances”。  
**【解题思路/题解】**  
A 描述的是 instance segmentation；C、D 未在课件中出现；B 是课件原文的精炼复述。

---

**MCQ 32.**  
在 VAE 的变分下界（ELBO）中，\( \mathbb{E}_{z\sim q_\phi(z|x)}[\log p_\theta(x|z)] \) 项的作用是：  
A. 强制 latent code z 接近先验 p(z)  
B. 最大化重构似然，确保解码器能从 z 重建 x  
C. 最小化 encoder 与 decoder 的 KL 散度  
D. 计算 posterior p(z|x) 的熵  

**【正确答案】** B  
**【详细知识点分析】**  
课件 `lecture_5_autoencoder.pdf` 第101页标题：“Train by maximizing the variational lower bound”，其公式为 \( \mathbb{E}[\log p_\theta(x|z)] - D_{KL} \)。第107页说明：“Original input data should be likely under the distribution output from (4)!”（即 decoder 输出）。第104页称其为“Data reconstruction”。  
**【解题思路/题解】**  
A 是 KL 项的作用（第103页）；C、D 非课件术语；B 直接对应“reconstruction”目标。

---

**MCQ 33.**  
Segment Anything Model (SAM) 的 prompt encoder 不包括以下哪种输入编码方式？  
A. 点坐标（point coordinates）经 learnable embedding + positional encoding  
B. 文本描述（text description）经 off-the-shelf text encoder 编码  
C. 边框坐标（bounding box coordinates）经卷积编码  
D. 掩码（mask）经轻量级 mask decoder 编码  

**【正确答案】** C  
**【详细知识点分析】**  
课件 `lecture_7_segmentation.pdf` 第89页

### 填空题练习

1. 在 CNN 中，若输入尺寸为 $H_1 \times W_1$，卷积核大小为 $F$，步长为 $S$，填充为 $P$，则输出高度 $H_2$ 的计算公式为：$H_2 = \frac{H_1 - F + 2P}{S} + 1$。
2. Transformer 中的 Self-Attention 机制通过三个矩阵实现，它们分别是：$Q$ (Query), $K$ (Key), $V$ (Value)。
3. VAE 的损失函数包含两部分：一部分是重构损失（Reconstruction Loss），另一部分是：$D_{\text{KL}}$ (KL Divergence)。
4. 在目标检测评估中，IoU 的全称是：Intersection over Union。其计算公式为：$A \cap B / A \cup B$。
5. YOLOv1 模型将输入图像划分为 $S \times S$ 个网格（Grid Cells），每个网格预测 $B$ 个边界框。
6. U-Net 架构在收缩路径（Contracting Path）与扩张路径（Extensive Path）之间通过：Skip Connection 传递特征。
