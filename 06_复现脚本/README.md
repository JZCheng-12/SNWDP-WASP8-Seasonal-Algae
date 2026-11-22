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
