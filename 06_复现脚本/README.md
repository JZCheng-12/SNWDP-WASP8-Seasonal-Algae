# 脚本入口

以仓库根目录运行 `python 06_复现脚本/reproduce.py check`，即可核查保存的模型结果，无需安装 WASP8 或第三方 Python 库。核查从 OUT/BMD2 重算拟合指标、留出选参、情景统计和交互分解。

`python 06_复现脚本/reproduce.py report` 重建图表和 Word，需 `pip install -r requirements.txt` 及 R（仅使用 base R）。缺少 R 时可加 `--skip-plots`，复用已提供图件。环境变量 `RSCRIPT` 可指定 Rscript 路径。

`python 06_复现脚本/reproduce.py full` 从随附基础 WIF 重跑参数候选、入口探索与情景，再生成报告。需要 Windows 上的 WASP8，环境变量 `WASP_BIN` 指向含 `wasptool.exe` 与 `waspccli.exe` 的目录。首次参数网格和入口试算每次重跑；情景只在基础 WIF、命令文本、输出及成功日志全部匹配时复用缓存，设 `WASP_FORCE=1` 强制重算情景。

| 脚本 | 工作 |
|---|---|
| plan_seasonal_spatial_cv.py | 根据站号生成固定空间四折表 |
| fit_seasons_spatial_cv.py | 两季各 18 组参数网格与四折评分 |
| run_winter_inlet_candidates.py / score_winter_inlet_exploration.py | 冬季 3 组入口试算及评分 |
| package_seasonal_models.py | 汇集两季最终 WIF、日志与参数索引 |
| run_seasonal_scenarios.py | 54 个三因素情景及 464 条交互分解 |
| audit_project.py / verify_seasonal_scenarios.py | 原始输出、表格、哈希和末日变化核查 |
| build_parameter_appendix.py / diagnose_seasonal_mechanisms.py | 完整参数附录及温度／残余磷诊断 |
| sync_chart_data.py / plot_seasonal_*.R | 同步实际数据并绘图 |
| build_submission_report.py | 从核查统计与结果表生成提交报告 |
| render_word.ps1 | 使用 Windows Word 导出 PDF 至临时核查目录 |
| refresh_manifest.py | 生成文件 SHA-256 清单 |

`运行依赖` 包含求解辅助程序、必要输入副本及基础 WIF；`参数溯源命令` 用于核对参数写入来源，不是从空白渠网生成模型的完整脚本。主报告由单一脚本生成；不应手工修改报告数值而不更新其数据源。

## 课程汇报演示文稿

`05_report/南水北调中线WASP8_课程汇报.pptx` 为 18 页演示文稿，采用用户提供的 `PPT_模板.pptx` 设计。内容分为「1 背景与目标、2 数据与建模方法、3 结果与机制解释、4 政策建议」，有目录、逐页讲解备注及两页附录。9 个科学数据图面板全部由 R 重画；文字与 6 张表格可编辑。PDF 是同版逐页渲染的预览文件，编辑时以 PPTX 为准。

按以下顺序在项目根目录复现：

1. 运行 `Rscript 06_复现脚本/plot_course_presentation.R`。仅依赖 base R 与 grDevices；Windows 需 Microsoft YaHei 字体。输出在 `04_figures/course_presentation_R`，包含 PNG、PDF、SVG、绘图数据摘录和 R 会话信息。PNG 为 330 dpi；PDF 保留矢量图形和文本，base R SVG 的文字可能以轮廓保存。
2. 运行 `python 06_复现脚本/prepare_presentation_template.py TEMPLATE_PPTX _qa_render/course_ppt/template-expanded.pptx 18`，将 `TEMPLATE_PPTX` 替换为用户提供的单页模板路径。依赖 python-pptx，仅做模板结构复制。该外部模板不随代码重新分发。
3. 运行 `node 06_复现脚本/build_course_presentation.mjs`。依赖 Node.js 和 `@oai/artifact-tool`；可用 `ARTIFACT_TOOL_MODULE` 指定其 `artifact_tool.mjs`。`PPT_BUILD_DIR` 指定临时输出目录，默认 `_qa_render/course_ppt`；`PPT_TEMPLATE` 可指定第二步生成的文件。输出 `candidate.pptx`、18 张逐页 PNG 和讲解备注 JSON。数据读取自 `report_facts.json` 与 `chart_data`，图面板读取自 R 输出；不运行或改变 WASP 模型。
4. 检查草稿字体、模板标识、页面溢出和数值后，再替换交付文件。交付 PPTX 已通过字体、包结构、模板覆盖和版面几何验证，并重新导入渲染核查。

这些图以高清图片嵌入 PPT，修改图中数据应修改数据源并重新运行 R 脚本；不能通过 PowerPoint 的「编辑图表数据」修改。模板校徽、标题装饰及可编辑表格不属于科学数据图。

`build_presentation_preview.py RENDER_DIRECTORY OUTPUT_PDF` 使用 reportlab 将已渲染的连续编号 PNG 合并为 PDF 预览。渲染和 PDF 依赖不影响原有 `reproduce.py check/report/full`。

### 可复制的重建命令

以下命令在项目根目录执行；Python 可选依赖与原有模型核查依赖分开安装。`TEMPLATE_PPTX` 是外部单页模板的路径。`@oai/artifact-tool` 需在执行环境中可导入；使用 Codex 捆绑运行时时，将 `ARTIFACT_TOOL_MODULE` 设置为该环境实际的 `artifact_tool.mjs` 路径，不要照搬另一台电脑的路径。本仓库不提供该运行时，也不假定它能通过公开 npm 安装。

```powershell
python -m pip install -r 06_复现脚本/requirements-presentation.txt
Rscript 06_复现脚本/plot_course_presentation.R
python 06_复现脚本/prepare_presentation_template.py "TEMPLATE_PPTX" _qa_render/course_ppt/template-expanded.pptx 18
node 06_复现脚本/build_course_presentation.mjs
node 06_复现脚本/render_course_presentation.mjs _qa_render/course_ppt/candidate.pptx _qa_render/course_ppt/final_render
python 06_复现脚本/build_presentation_preview.py _qa_render/course_ppt/final_render _qa_render/course_ppt/preview.pdf
```

最后两步重新读取保存的 PPTX 再渲染，便于核查实际文件中图片是否完整。若只希望为已交付 PPT 重新生成预览，可直接将渲染命令的输入替换为 `05_report/南水北调中线WASP8_课程汇报.pptx`。没有上述组装运行时的用户仍可独立运行 R 绘图，或使用 PowerPoint 编辑已交付文件并导出 PDF。

交付清单：18 页 PPT、18 页 PDF 预览、18 份演讲者备注、9 张 R 数据图（每张 PNG/PDF/SVG）、R 会话信息和绘图数据摘录。检查新生成文件后再替换 `05_report` 中的交付件，并运行 `python 06_复现脚本/refresh_manifest.py` 更新校验清单。R 绘图、模板组装、PDF 预览是单独流程，`reproduce.py report` 不会自动重建课程 PPT。
