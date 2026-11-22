"""Build the submission report from audited seasonal statistics and source tables."""
import csv,json
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from discussion_content import SECTIONS,POLICY

ROOT=Path(__file__).resolve().parents[1]
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    facts=json.loads((ROOT/'07_核查记录/report_facts.json').read_text(encoding='utf-8'))
    periods=('2020-08','2021-03');names={'2020-08':'夏季','2021-03':'冬季'}
    ss=facts['scenarios'];ix=facts['interactions'];seasons=facts['seasons']
    case=lambda p,t=0,d=1,q=1:next(r for r in ss if r['period']==p and int(r['T_plus_C'])==t and int(r['DIP_factor'])==d and float(r['Q_factor'])==q)
    C=lambda p,t=0,d=1,q=1:float(case(p,t,d,q)['mean23_Chla_ug_L'])
    doc=Document();sec=doc.sections[0]
    sec.page_width=Inches(8.5);sec.page_height=Inches(11)
    sec.left_margin=sec.right_margin=Inches(.75);sec.top_margin=Inches(.65);sec.bottom_margin=Inches(.65)
    for name in ('Normal','Title','Heading 1','Heading 2','Caption'):
        st=doc.styles[name];st.font.name='Microsoft YaHei';st.font.color.rgb=RGBColor(0,0,0)
        st._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
    for st in doc.styles:
        for x in list(st._element.iter(qn('w:pBdr'))):x.getparent().remove(x)
    doc.styles['Normal'].font.size=Pt(10.5);doc.styles['Normal'].paragraph_format.line_spacing=1.15
    doc.styles['Normal'].paragraph_format.space_after=Pt(6)
    doc.styles['Title'].font.size=Pt(18);doc.styles['Title'].font.bold=True
    for name,size in [('Heading 1',14),('Heading 2',11.5)]:
        st=doc.styles[name];st.font.size=Pt(size);st.font.bold=True
        st.paragraph_format.space_before=Pt(10);st.paragraph_format.space_after=Pt(5)
        st.paragraph_format.keep_with_next=True
    doc.styles['Caption'].font.size=Pt(9);doc.styles['Caption'].font.italic=False
    footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run('南水北调中线 WASP8 季节模拟课程作业  |  ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    for r in footer.runs:r.font.size=Pt(8)
    p=lambda s:doc.add_paragraph(s)
    h=lambda s,l=2:doc.add_heading(s,l)
    def table(title,headers,rows):
        cap=doc.add_paragraph(title,style='Caption');cap.paragraph_format.keep_with_next=True
        t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid'
        for c,v in zip(t.rows[0].cells,headers):c.text=str(v)
        for vals in rows:
            for c,v in zip(t.add_row().cells,vals):c.text=str(v)
        repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
        for i,row in enumerate(t.rows):
            no_split=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no_split)
            for cell in row.cells:
                cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                pr=cell._tc.get_or_add_tcPr();borders=OxmlElement('w:tcBorders')
                for side in ('top','bottom','left','right'):
                    b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
                pr.append(borders)
                if i==0:
                    shd=OxmlElement('w:shd');shd.set(qn('w:fill'),'EEEEEE');pr.append(shd)
                for q in cell.paragraphs:
                    q.paragraph_format.space_before=Pt(2);q.paragraph_format.space_after=Pt(2)
                    for r in q.runs:r.font.size=Pt(9);r.bold=(i==0)
        doc.add_paragraph().paragraph_format.space_after=Pt(1)
    def figure(name,caption,width=6.8):
        q=doc.add_paragraph();q.paragraph_format.keep_with_next=True
        q.add_run().add_picture(str(ROOT/'04_figures'/name),width=Inches(width))
        doc.add_paragraph(caption,style='Caption')
    def equation(text):
        q=doc.add_paragraph();q.paragraph_format.space_after=Pt(4)
        if text.startswith(('Iₜₚ','Iₜq')):q.paragraph_format.keep_with_next=True
        math=OxmlElement('m:oMath');run=OxmlElement('m:r');t=OxmlElement('m:t');t.text=text;run.append(t);math.append(run);q._p.append(math)

    doc.add_paragraph('南水北调中线 WASP8 季节藻类模拟及多因素交互响应',style='Title')
    p('课程作业  ·  夏季与冬季独立率定  ·  升温、增磷与流量变化')
    h('摘要',1)
    p('以南水北调中线两期水环境资料和文献 Chl-a 图像估读为基础，构建 29 段一维等效渠网，分别率定夏季与冬季模型，并采用季节内空间四折检验。每季设置 27 个温度、可利用磷和流量组合，比较干渠藻量响应与非加法交互。夏季、冬季四折 RMSE 分别为 1.903 和 2.452 µg/L，模型能表达平均水平及有限沿程趋势，但局部站点起伏仍未充分重现。单独升温 4°C 时，两季体积加权 Chl-a 分别变化 −5.3% 和 +44.3%；单独 DIP×4 时分别增加 51.1% 和 2.4%。升温 4°C、DIP×4、流量降低 30% 的组合分别使其增加 66.6% 和 174.7%。冬季以温度×磷交互为主，夏季以磷×低流量交互为主，提示低磷背景下仍需关注复合扰动。结果属于固定工况的条件性压力测试，可用于提出监测重点，不能直接解释为藻华发生概率。')
    p('关键词：南水北调中线；WASP8；季节率定；叶绿素 a；全因子情景；交互作用')
    h('1 Introduction',1)
    p('南水北调中线长距离输水系统具有低磷背景，相关研究报告长期磷约束及小基因组蓝藻在低磷条件下的生态优势［2,3］。这并不意味着渠道已普遍发生富营养化，而是提出了一个管理问题：当水温、可利用磷和输水流量共同改变时，藻类增长的响应是否随季节而不同，联合效应能否超过各单因素效应之和？')
    p('本作业将研究分为数据与假设整理、分季节率定及空间检验、三因素情景与管理解释三个部分。采用统一断面和单一综合浮游植物状态量，以有限资料建立可运行、可核查的课程模型。研究重点是两套季节工况的响应规律和交互分解，不涉及特定蓝藻种属或毒性预测。')
    h('2 Methods',1)
    h('2.1 数据来源与季节定义')
    p('站点、水温、流量和营养盐来自随附 env.xlsx 整理资料，文献背景和采样资料参照 Chen 等［3］及 Wang 等［2］。按本作业命名约定，2020-08 为夏季，2021-03 为冬季；月份保留原始记录。两期不是连续时间序列，分别作为恒定外部强迫下的 90 d 工况。未获得逐站 Chl-a 原值时，由 Science Bulletin 补充图 Fig. S2 高清散点图估读，并以横坐标和沿程距离匹配候选站号。')
    p('入口设于站 03；站 04—26 为 23 个共同干渠目标站，分别对应 S01—S23。夏季、冬季可用 Chl-a 为 20、22 个点，重叠点、相邻站歧义和缺失标记保留。站 27 为分流节点候选，不纳入评分。图像估读值不是实验原始测量，其不确定性未被当作重复测量误差。公开的多年 TP 数据可用于背景对照，但未被拼接为本模型的连续入口边界。')
    table('表 1 主要输入及替代假设',['输入','采用方式','主要局限'],[
        ['断面与水工结构','29 段统一矩形断面，宽 54 m、深 6.95 m；复杂结构等效简化','非逐段测量几何，不能重现局部水工扰动'],
        ['流量与取水','两期空间快照按水量守恒重整；保留分流与概念取水','缺少连续调度、流速与旅行时间约束'],
        ['水温与光照','全渠代表水温；日均辐射 150 W/m²，日照比例 0.5','固定强迫，不代表逐时气象及沿程光场'],
        ['磷与有机氮','基准 DIP=TP 的 10%；剩余组分按质量平衡拆分','缺少同期 SRP 与颗粒／溶解形态'],
        ['Chl-a 与入口藻体','沿程图像估读；夏季入口 5、冬季 7 µg/L','入口为假设，冬季方案属于事后探索'],
        ['DO','年均文献代理值，细节见输入表','非同期观测，本作业不报告 DO 率定性能']])
    h('2.2 渠网输运与藻类过程')
    p('采用 WASP8 的水柱渠段和预设流路，将沿程距离换算为段长，以 Vᵢ=段长×54×6.95 计算体积。每段满足入流、出流与取水的水量平衡；分流口按给定比例连接支路。全部 29 段参加求解，汇报重点限于分叉前 S01—S23。流速与停留时间分别由代表流量／断面面积和体积／代表流量推算；不求解完整明渠动量方程，也不宣称已完成独立水动力率定。纵向弥散基准设为 0，体积固定。')
    equation('Vᵢ dCᵢ/dt = Σ Qⱼᵢ Cⱼ − Σ Qᵢₖ Cᵢ + Vᵢ Rᵢ')
    p('式中 Cᵢ 为状态量浓度，Q 为包括取水在内的流路流量，Rᵢ 表示反应源汇项。模型采用氨氮、NOx-N、溶解有机氮、碎屑氮、DIP、溶解有机磷、碎屑磷、DO、CBODU、POC 及一个综合浮游植物 Chl-a 状态量。NOx-N 由 NO₃-N 与 NO₂-N 合并代理；TN、TP 用于总量约束和守恒检查，本研究未对营养盐过程另行拟合和独立验证。')
    p('藻类增长受温度、光照和营养条件调节，损失过程单独计算［1］。本工程固定呼吸系数为 0.02 d⁻¹、温度系数为 1.07；非捕食死亡与浮游动物摄食显式设为 0，未设底泥释放或藻类群落替代。自遮光开关关闭，水下光衰减作为统一参数率定。生长温度系数为 1、最适温度两侧形状参数均为 0.05。完整显式参数、初始化占位值与来源命令见参数附录和总表；WIF 保存全部内部设置。')
    temp=[float(case(v)['temperature_C']) for v in periods]
    p(f'实际温度函数为 29 段代表水温的算术平均，夏季 {temp[0]:.3f}°C、冬季 {temp[1]:.3f}°C，全部渠段采用同一温度。流量、入口营养盐、入口藻体及辐射在每次 90 d 试算中保持恒定。初值采用入口浓度均匀赋值，因此沿程观测不用于设置下游初值。')
    h('2.3 参数率定与空间区间检验')
    p('每季独立执行 18 个参数组合：20°C 最大生长率 G20 为 0.5、2、4 d⁻¹，最适温度 Topt 为 20、30、35°C，光衰减 Kd 为 0.3、0.7 m⁻¹。第一轮入口与初始 Chl-a 固定为 5 µg/L，C:Chl-a=25、N:C=0.15、P:C=0.012，磷半饱和常数为 0.001 mg P/L。每组均实际生成 WIF 并调用 WASP8 求解。')
    p('按站号预先固定 04—09、10—15、16—21、22—26 四个连续空间区间。每折用另外三个区间的 Chl-a 训练 RMSE 选择参数，再在留出区间评分；各可用点仅作为测试点一次。计算过程中仍模拟所有渠段，但留出观测不参加该折选参。以训练站点观测均值预测留出站点作为比较基线。最终展示参数由全体可用点选择，其拟合误差与交叉检验误差分开报告。')
    p('第一轮冬季偏低后，补充入口敏感性试算：固定 G20=4 d⁻¹、Topt=20°C、Kd=0.3 m⁻¹，将 N:C 设为 0.10，再比较 Chl-a=5、6、7 µg/L。按藻体 N=Chl-a×0.001×25×N:C、藻体 P=Chl-a×0.001×25×0.012，分别从溶解有机池和碎屑池各扣除一半，以维持入口 TN、TP。入口 7 µg/L 占冬季 TN−NOx 余额约 92.1%，因此该方案强烈依赖未测入口与化学计量假设。每折仅在上述三个入口候选间再次选择，不能将此第二轮改进视为完全独立外部验证。')
    p('RMSE 为残差平方均值的平方根，MAE 为绝对残差均值，偏差为预测减观测的均值。NSE=1−Σ(预测−观测)²／Σ(观测−均值)²。逐折 NSE 使用该测试折观测均值，合并 NSE 使用该季所有留出观测的均值；合并指标从全部留出预测重算，不平均各折 NSE。参数范围参考总体观测和试算表现，四折结果仅衡量给定方案下的条件性空间稳健性。')
    h('2.4 三因素情景与响应指标')
    p('以各季最终工程为基准，温度增量设为 0、2、4°C，DIP 倍数为 1、2、4，流量倍数为 0.7、1.0、1.3；每季 27 个组合，共 54 个。升温施加于统一温度函数；DIP 同时增加入口和各段初值，其他磷池不变；流量统一缩放入口、分流与取水，体积固定，入口浓度不变。因而流量降低 30% 时停留时间约变为 1.43 倍，增流 30% 时约为 0.77 倍，营养盐输入负荷亦随 Q 改变。该设计是固定入口浓度的输运与反应综合试验。')
    p('所有情景使用第 90 d 末值。以 S01—S23 固定体积权重计算 Chl-a 均值，并保存逐段和最大值；变化率为 100×(情景均值−该季基准均值)／该季基准均值。图 1 及空间拟合统计仅使用有观测的 20／22 个站点，采用站点算术统计；情景分析包含 23 段并采用体积权重，两类均值不可混用。情景水平为课程压力测试，未与排放路径、未来年份或藻华判别阈值绑定。')
    h('2.5 交互分解与数值核查')
    p('记 C(t,p,q) 为同一渠段或同一固定权重下的 Chl-a，基准为 (0,1,1)。温度×磷项在基准流量下定义，温度×流量项在基准磷下定义，磷×流量项在基准温度下定义。')
    equation('Iₜₚ = C(t,p,1) − C(t,1,1) − C(0,p,1) + C(0,1,1)')
    equation('Iₜq = C(t,1,q) − C(t,1,1) − C(0,1,q) + C(0,1,1)')
    equation('Iₚq = C(0,p,q) − C(0,p,1) − C(0,1,q) + C(0,1,1)')
    p('三阶项为 C(t,p,q) 减去 C(t,p,1)、C(t,1,q)、C(0,p,q)，再加上 C(t,1,1)、C(0,p,1)、C(0,1,q)，最后减去 C(0,1,1)。总非加法效应 Net=Iₜₚ+Iₜq+Iₚq+Iₜₚq，等于联合增量超过三个单因素增量之和的部分。所有交互单位均为 µg/L；正值指超过加法预期，不表示统计显著或真实事件概率。')
    p('从原始 OUT/BMD2 文件独立重算候选评分、留出选参、情景加权均值及交互，核对 WIF 哈希、求解闭合日志和氮磷总量误差。比较第 89 与 90 d 的 Chl-a，保留未充分收敛信息。相同结果表同时驱动图表和报告，避免不同文件间的人工转录。')

    h('3 Results',1)
    h('3.1 季节率定与空间检验')
    table('表 2 第一轮 18 组参数网格的最优拟合与留出检验',['季节','G20 / Topt / Kd','拟合 RMSE','四折 RMSE','四折 NSE','基线 RMSE'],[
        [names[pp],f"{float(seasons[pp]['first_grid']['final_growth_d-1']):g} / {float(seasons[pp]['first_grid']['final_Topt_C']):g} / {float(seasons[pp]['first_grid']['final_Kd_m-1']):g}",
         f"{float(seasons[pp]['first_grid']['final_fit_RMSE_ug_L']):.3f}",f"{seasons[pp]['first_grid_cv']['RMSE_ug_L']:.3f}",f"{seasons[pp]['first_grid_cv']['NSE']:.3f}",f"{seasons[pp]['baseline']['RMSE_ug_L']:.3f}"] for pp in periods])
    p('表 2 中生长率、最适温度、光衰减单位依次为 d⁻¹、°C、m⁻¹，RMSE 为 µg/L。夏季留出误差仅比均值基线低约 0.013 µg/L；冬季第一轮误差大于基线，说明参数网格未能解决系统性低估。')
    wc=read(ROOT/'03_最终结果/01_率定与检验/冬季入口组成探索_候选方案.csv')
    table('表 3 冬季入口敏感性方案',['入口 Chl-a（µg/L）','N:C','藻体 N 占 TN−NOx','全点 RMSE','全点 NSE'],[
        [f"{float(r['inlet_Chla_ug_L']):g}",'0.10',f"{float(r['inlet_Chla_ug_L'])*.001*25*.1/.019*100:.1f}%",f"{float(r['RMSE_ug_L']):.3f}",f"{float(r['NSE']):.3f}"] for r in wc])
    w=seasons['2021-03'];a=seasons['2020-08']
    improvement=(1-w['final_cv']['RMSE_ug_L']/w['baseline']['RMSE_ug_L'])*100
    p(f"冬季四折均选取入口 7 µg/L，合并 RMSE={w['final_cv']['RMSE_ug_L']:.3f} µg/L、NSE={w['final_cv']['NSE']:.3f}，较均值基线误差降低 {improvement:.1f}%。各测试折 NSE 仍为负；合并 NSE 略为正来自不同分母和站点间均值差异，两者并不矛盾。两季最终工程参数分别为夏季 G20=0.5、Topt=30、Kd=0.7、入口 5；冬季 G20=4、Topt=20、Kd=0.3、入口 7（单位同表 2、3）。")
    p(f"夏季观测均值与样本标准差为 {a['spatial']['observed_mean']:.2f}±{a['spatial']['observed_sd']:.2f} µg/L，拟合为 {a['spatial']['fitted_mean']:.2f}±{a['spatial']['fitted_sd']:.2f}；冬季分别为 {w['spatial']['observed_mean']:.2f}±{w['spatial']['observed_sd']:.2f} 和 {w['spatial']['fitted_mean']:.2f}±{w['spatial']['fitted_sd']:.2f} µg/L。模拟剖面比观测平滑，主要再现平均水平和缓慢沿程变化，局部高低值尚未重现（图 1）。")
    figure('Fig01_seasonal_spatial_calibration.png','图 1 季节内空间率定。灰点为图像估读，橙叉为留出预测，蓝线为全点最终拟合。夏季 n=20，冬季 n=22。冬季采用事后入口敏感性方案；蓝线仅连接同一工程输出。')
    h('3.2 单因素及联合情景响应')
    cases=[('基准',0,1,1),('升温 2°C',2,1,1),('升温 4°C',4,1,1),('DIP×4',0,4,1),('Q×0.7',0,1,.7),('Q×1.3',0,1,1.3),('+4°C，DIP×4，Q×0.7',4,4,.7),('+4°C，DIP×4，Q×1.3',4,4,1.3)]
    table('表 4 代表情景下 S01—S23 体积加权 Chl-a 及变化率',['情景','夏季 µg/L','夏季变化','冬季 µg/L','冬季变化'],[
        [label]+sum(([f"{C(pp,t,d,q):.2f}",f"{float(case(pp,t,d,q)['percent_mean23']):+.1f}%"] for pp in periods),[]) for label,t,d,q in cases])
    p(f"夏季单独增磷的响应较强：DIP×4 使均值由 {C('2020-08'):.2f} 增至 {C('2020-08',0,4):.2f} µg/L。冬季同一操作仅由 {C('2021-03'):.2f} 增至 {C('2021-03',0,4):.2f} µg/L，但单独升温 4°C 后达到 {C('2021-03',4):.2f} µg/L。夏季升温响应非单调，+2°C 时为 {C('2020-08',2):.2f}，+4°C 时为 {C('2020-08',4):.2f} µg/L。")
    p(f"+4°C、DIP×4、Q×0.7 组合下，两季均值分别为 {C('2020-08',4,4,.7):.2f} 和 {C('2021-03',4,4,.7):.2f} µg/L。图 2 显示联合响应依赖季节与流量：在原温原磷条件下冬季降流使 Chl-a 略降，而在升温增磷条件下，降流转为促进浓度积累。这里比较的是条件性藻量响应，而非超标概率。")
    figure('Fig02_seasonal_factorial.png','图 2 全部 54 个情景相对各季基准的 Chl-a 增量。单位 µg/L；六个面板采用共同色阶。每格为 S01—S23 体积加权均值之差，单因素与联合组合均来自实际求解。')
    h('3.3 二阶与三阶交互')
    keys=('I_TP_ug_L','I_TQ_ug_L','I_PQ_ug_L','I_TPQ_ug_L','net_nonadditivity_ug_L')
    table('表 5 升温 4°C 与 DIP×4 时的交互分解（µg/L）',['季节与流量','T×P','T×Q','P×Q','T×P×Q','Net'],[
        [names[r['period']]+f" Q×{r['Q_factor']}"]+[f"{r[k]:+.3f}" for k in keys] for r in ix])
    p('冬季温度×磷交互为 +7.60 µg/L，是强扰动组合的主要非加法贡献；低流量和高流量下 Net 分别为 +8.59 与 +6.63 µg/L。夏季低流量组合的 Net 为 +1.09 µg/L，主要来自磷×流量项 +1.48 µg/L，而温度×磷为负；高流量时 Net 转为 −0.94 µg/L。')
    p('低流量下冬季三阶项为 +0.714 µg/L，夏季为 −0.117 µg/L；高流量下分别为 −0.746 与 +0.092 µg/L。三阶项随工况变号，不能将某一组合的正值概括为普遍协同。完整交互分解见图 3，正负均指相对加法预期的偏离。')
    figure('Fig03_seasonal_interactions.png','图 3 两季在升温 4°C、DIP×4 下的交互分解。左为 Q×0.7，右为 Q×1.3；各柱为体积加权交互项。Net 是四项之和，不是 Chl-a 总增量。')
    h('3.4 数值完整性与诊断结果')
    qa=read(ROOT/'03_最终结果/04_季节情景与交互/季节三因素_数值核验.csv')
    maximum=max(float(r['max_last_day_Chla_change_ug_L']) for r in qa);notsteady=sum(float(r['max_last_day_Chla_change_ug_L'])>=.01 for r in qa)
    p(f'54 个情景均有正常求解闭合记录，1566 条逐段结果及 464 条交互分解与原始输出相符，TN、TP 与设定总量的最大差均小于 2×10⁻⁶ mg/L。最大末日 Chl-a 变化为 {maximum:.4f} µg/L，其中 {notsteady} 个情景超过 0.01 µg/L；因此统一报告 90 d 末值，不将全部结果视为严格稳态。两季基准情景与最终率定工程一致。')
    p('在 Q=1、DIP=1 下，冬季升温 4°C 使残余 DIP 加权均值从约 0.00114 降至 0.00023 mg P/L；同温度下 DIP×4 时为约 0.00102 mg P/L。温度曲线诊断显示，冬季 +4°C 的生长温度项约为基准的 25.25 倍，呼吸温度项约为 1.31 倍。上述为末值和参数函数诊断，不是净摄磷通量或过程贡献率。')
    heading=h('4 Discussion',1);heading.paragraph_format.page_break_before=True
    for i,(title,paras) in enumerate(SECTIONS):
        if i==0:
            for text in paras:p(text)
        elif title.startswith('政策建议') or title.startswith('适用范围'):continue
        else:
            h('4.'+str(i)+' '+title)
            for text in paras:p(text)
    h('4.4 管理建议与适用范围')
    for title,paras in SECTIONS:
        if title.startswith('政策建议'):
            for text in paras:p(text.replace('下表','表 6'))
    table('表 6 基于季节响应的监测与管理建议',['关注工况','建议行动','实施前验证'],POLICY)
    for title,paras in SECTIONS:
        if title.startswith('适用范围'):
            for text in paras:p(text)
    h('5 Conclusions',1)
    p('本研究完成了两期输入规范化、29 段 WASP8 渠网、两套季节率定工程和 54 个全因子情景。空间检验显示，模型能够表达季节平均水平和有限沿程趋势，但尚不足以准确恢复局地藻量。基于当前参数与入口设定，夏季对增磷更敏感，冬季在升温后出现更强的增磷响应；冬季以温度×磷交互为主，夏季低流量组合以磷×流量交互为主。')
    p('课程作业的主要探索是将分季节机理模型与可精确分解的因子情景结合，明确区分单因素效应、二阶交互和三阶交互。管理上宜关注冬季升温与磷输入并发，以及夏季低流量与磷输入并发；具体调度阈值应在补充同期 Chl-a、可利用磷和水动力观测后确定。')
    h('参考文献与数据说明',1)
    for text in [
        '［1］Wool TA, Ambrose RB Jr, Martin JL. WASP8 Multiple Algae—Model Theory and User’s Guide. US EPA. https://www.epa.gov/sites/default/files/2018-05/documents/mpm-user-guide.pdf',
        '［2］Wang J, Chen Y, Chen T, et al. Genomic blueprint enables early intervention in cyanobacterial risk management. Science Bulletin, 2025, 70:4263–4275. https://doi.org/10.1016/j.scib.2025.11.005',
        '［3］Chen T, Liu T, Wu Z, et al. Virus–pathogen interactions improve water quality along the Middle Route of the South-to-North Water Diversion Canal. The ISME Journal, 2023, 17:1719–1732. https://doi.org/10.1038/s41396-023-01481-2',
        '环境输入为课程提供的 env.xlsx 整理资料；Chl-a 为［2］补充图估读，不作为原作者逐站实验原值发布。参数假设及局限见参数附录，完整输入、脚本、工程、图表源数据及一致性核查表随项目保存。图表未使用随机重复或统计置信区间。']:
        p(text)
    out=ROOT/'05_report/南水北调中线WASP8_季节率定与情景汇报.docx';doc.save(out);print(out)
if __name__=='__main__':main()
