# 课程汇报 R 图件

由 `06_复现脚本/plot_course_presentation.R` 从项目已核查的数据表重画。以项目根目录为工作目录运行该脚本即可复现，无需重新运行 WASP8。

| 图件 | 对应 PPT | 含义 |
|---|---|---|
| fit_summer / fit_winter | 2.4 | 两季最终模型与数字化观测的沿程比较 |
| single_factor | 3.1 | 三个因素单独变化的相对响应 |
| tp_summer / tp_winter | 3.2 | 基准流量下升温与 DIP 增加的联合响应 |
| interactions | 3.3 | +4°C、DIP×4、Q×0.7 的非加法效应分解 |
| temperature_summer / temperature_winter | 3.4 | 相对各季基准的生长、呼吸温度因子 |
| flow_response | 3.5 | +4°C、DIP×4 条件下的流量响应 |

夏季使用赭红色，冬季使用青蓝色。每个面板提供 330 dpi PNG、矢量 PDF 和 SVG；PDF 含文本，base R SVG 文本可能转换为轮廓。PPT 嵌入 PNG。图表没有独立重复，未绘制置信区间；观测值为图片数字化值，模型线为最终拟合，不代表独立检验。情景指标是第 90 天 23 个干渠段体积加权 Chl-a；温度因子倍率不等于 Chl-a 倍率。

`single_factor_source.csv` 和 `interaction_source.csv` 为相应图的数据摘录，其他面板从 `chart_data` 读取。完整参数、空间检验和模型局限见报告及补充材料。`R_sessionInfo.txt` 记录实际绘图环境。
