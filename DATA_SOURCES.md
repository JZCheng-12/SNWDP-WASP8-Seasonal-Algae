# 数据来源与使用边界

本项目为课程作业。公开内容包括处理后的模型输入、图像估读数据、模型设置与计算输出。不得将估读值或假设输入引用为原作者的逐站原始测量。

| 数据 | 来源与用途 | 局限 |
|---|---|---|
| 站点、流量、水温、氮磷 | 课程提供的 env.xlsx，经站点匹配、单位整理和水量守恒处理 | 两期空间快照，不是连续调度序列；流量换算和分流有假设 |
| Chl-a | Wang et al. (2025) 补充图 Fig. S2 的高清图像估读 | 图形估读、重叠圆点与站点匹配存在误差；原图不随公开仓库分发 |
| 渠道几何 | 统一宽 54 m、深 6.95 m 的课程等效设定；段长由沿程距离推算 | 非逐段实测；水工结构简化 |
| 营养盐形态、入口藻体、辐射 | 参数附录列出的质量平衡及固定强迫假设 | 需要同期 SRP、Chl-a、光场等补充观测 |
| 模型参数名与理论 | EPA WASP8 手册与本机参数元数据快照 | 显式参数总表不代表所有过程均已启用；完整工程以 WIF 为准 |

课程命名为 2020-08 夏季、2021-03 冬季，月份保留原记录；`model_season` 表示本项目标签。分析采用站 04—26，站 01=QS、02=DKKX。站号候选匹配及质量标记见估读 CSV。01_模型输入 中的磷形态表含备选分配比例，本模型仅采用 `DIP_10pct`；营养盐观测表用于背景和边界约束，未完成独立营养盐过程率定。

文献全文和出版社图像不包含在本公开项目中。下列来源保留其作者及出版方的权利。程序代码可运行和查看；本项目不为第三方数据或文献素材另行授予许可证。

- Wool TA, Ambrose RB Jr, Martin JL. [WASP8 Multiple Algae—Model Theory and User’s Guide](https://www.epa.gov/sites/default/files/2018-05/documents/mpm-user-guide.pdf).
- Wang J, Chen Y, Chen T, et al. [Genomic blueprint enables early intervention in cyanobacterial risk management](https://doi.org/10.1016/j.scib.2025.11.005). Science Bulletin 70 (2025), 4263–4275.
- Chen T, Liu T, Wu Z, et al. [Virus–pathogen interactions improve water quality along the Middle Route of the South-to-North Water Diversion Canal](https://doi.org/10.1038/s41396-023-01481-2). The ISME Journal 17 (2023), 1719–1732.
- Chen et al. 提供的 [Source Data.xlsx 所在仓库](https://github.com/ChenTianYi99/MR-SNWDC_virus) 可用于多年 TP 背景核查；本项目未将其作为连续边界强迫。

