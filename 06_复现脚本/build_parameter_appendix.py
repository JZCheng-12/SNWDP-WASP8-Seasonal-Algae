"""Build the seasonal parameter registry from packaged inputs and command records."""
import csv, hashlib, json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'01_模型输入/共用参数参考'
REGISTRY = DEST/'补充材料_WASP8季节模型完整参数总表.csv'
REPORT = ROOT/'05_report/补充材料_WASP8季节模型参数与复现说明.docx'

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def commands(p):
    return [line.split() for line in p.read_text(encoding='ascii').splitlines() if line.strip()]

def rel(p): return p.relative_to(ROOT).as_posix()

def main():
    rows=[]
    def add(cat,model,period,seg,code,name,value,unit,status,source,note=''):
        rows.append(dict(category=cat,model=model,period=period,segment_id=seg,
                         parameter_code=code,parameter_name=name,value=str(value),unit=unit,
                         evidence_status=status,source_file=source,note=note))
    meta=json.loads((ROOT/'06_复现脚本/WASP8_5_参数元数据快照.json').read_text(encoding='utf-8'))
    geometry=ROOT/'01_模型输入/01_segments_uniform_geometry.csv'
    for g in read(geometry):
        for k,name,u in [('length_m','渠段长度','m'),('rectangular_width_m','统一矩形渠宽','m'),
                         ('rectangular_depth_m','统一水深','m'),('cross_section_m2','矩形面积','m²'),('volume_m3','渠段体积','m³')]:
            add('渠道几何','两季共用','两期',g['segment_id'],k,name,g[k],u,'距离推算或统一断面假设',rel(geometry))
    flow=ROOT/'01_模型输入/02_flow_mass_balanced_two_cases.csv'
    for f in read(flow):
        for k,name,u in [('Q_in_m3_s','入流','m³/s'),('Q_out_m3_s','出流','m³/s'),('withdrawal_m3_s','概念取水','m³/s'),
                         ('representative_Q_m3_s','代表流量','m³/s'),('velocity_m_s','断面流速','m/s'),
                         ('residence_days','渠段停留时间','d'),('temperature_C','站点配对水温','°C')]:
            add('水动力与水温',f['period'],f['period'],f['segment_id'],k,name,f[k],u,'输入重整或推算',rel(flow),
                '配对水温用于构造代表工况；实际模型采用29段算术均温时间函数')
    models=read(ROOT/'05_report/补充材料_季节独立率定参数与工程索引.csv')
    state_names={1:'NH₄-N',2:'NOx-N',3:'溶解有机氮',4:'碎屑氮',5:'DIP',6:'溶解有机磷',7:'碎屑磷',8:'DO',9:'CBODU',10:'POC',11:'Chl-a'}
    for model in models:
        period=model['period']; label='夏季' if period=='2020-08' else '冬季'
        folder=ROOT/'06_复现脚本/参数溯源命令'/period
        wif=ROOT/model['WIF_relative_path']
        files=[folder/'eutro_finalize.txt',folder/'PHYTO_daily_combined_finalize.txt',wif.with_name(wif.stem+'_build.txt')]
        const={}; tf={}; param={}; initial={}; boundary={}
        for p in files:
            for c in commands(p):
                source=rel(p)
                if c[0]=='PCONSTVALUEBYISC': const[int(c[1])]=(c[3],source)
                elif c[0]=='PBRKTF' and c[3]=='1': tf[int(c[1])]=(c[5],source)
                elif c[0]=='PCONSTPARAM': param[int(c[1]),int(c[2])]=(c[4],source)
                elif c[0]=='PINITC': initial[int(c[1]),int(c[2])]=(c[3],source)
                elif c[0]=='PBOUNDFUNC' and c[3]=='1': boundary[int(c[1])]=(c[5],source)
        assert len(const)>=38 and set(tf)==set(range(1,71))
        for isc,key in [(65,'N_to_C'),(66,'P_to_C'),(68,'C_to_Chla'),(69,'growth_20C_d-1'),
                        (71,'optimal_temperature_C'),(74,'respiration_d-1'),(82,'P_half_saturation_mgP_L')]:
            assert float(const[isc][0])==float(model[key]), (period,key)
        assert all(float(param[seg,17][0])==float(model['light_attenuation_m-1']) for seg in range(1,30))
        assert hashlib.sha256(wif.read_bytes()).hexdigest()==model['WIF_SHA256']
        for isc,(v,source) in sorted(const.items()):
            add('WASP动力学常数',label,period,'全模型',f'CONST_ISC_{isc}',meta['constants'].get(str(isc),'WASP常数'),
                v,'参见WASP原生参数名','基础设置与季节覆盖命令合并',source)
        for isc,(v,source) in sorted(tf.items()):
            add('时间函数',label,period,'全模型',f'TF_ISC_{isc}',meta['funcs'].get(str(isc),'初始化函数'),v,
                {1:'°C',3:'比例',4:'W/m²',8:'m⁻¹'}.get(isc,'原生值'),'0—90 d常值',source,
                '包括初始化占位函数；条目存在不等于相关过程已启用')
        for (seg,isc),(v,source) in sorted(param.items()):
            add('WASP分段参数',label,period,f'S{seg:02d}',f'PARAM_ISC_{isc}',meta['params'].get(str(isc),'分段参数'),v,
                'm⁻¹' if isc==17 else '原生值','显式设定',source)
        for sys in range(1,12):
            v,source=initial[sys,1]
            assert all(float(initial[sys,seg][0])==float(v) for seg in range(1,30))
            if sys in boundary:
                assert float(boundary[sys][0])==float(v)
            else:
                basefile=ROOT/'01_模型输入/11_EUTRO_state_boundary_and_initial_ASSUMED.csv'
                names={1:'Ammonia Nitrogen',2:'Nitrate Nitrogen',5:'Inorganic Phosphate',8:'Dissolved Oxygen'}
                if sys in names:
                    b=next(r for r in read(basefile) if r['period']==period and r['case']=='DIP_10pct' and r['WASP_state_variable']==names[sys])
                    assert float(v)==float(b['value_mg_L'])
                    source=rel(basefile)
                else:
                    assert sys in (9,10) and float(v)==0
            add('边界与初值',label,period,'S01—S29',f'SYS{sys}',state_names[sys],v,'µg/L' if sys==11 else 'mg/L',
                '入口代理或假设拆分；有机氮磷已扣除藻体份额',source,'恒定入口和29段统一初值')
        add('工程文件',label,period,'全模型','WIF_SHA256','最终工程哈希',hashlib.sha256(wif.read_bytes()).hexdigest(),
            'hex','实际工程',rel(wif))
    scenarios=ROOT/'03_最终结果/04_季节情景与交互/季节三因素_情景汇总.csv'
    for s in read(scenarios):
        key=f"T{s['T_plus_C']}_P{s['DIP_factor']}_Q{s['Q_factor']}"
        for code,u in [('T_plus_C','°C'),('DIP_factor','倍数'),('Q_factor','倍数')]:
            add('情景输入',s['period'],s['period'],key,code,code,s[code],u,'全因子压力测试',rel(scenarios))
    DEST.mkdir(parents=True,exist_ok=True)
    with REGISTRY.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

    doc=Document();sec=doc.sections[0]
    sec.page_width=Inches(8.5);sec.page_height=Inches(11)
    sec.left_margin=sec.right_margin=Inches(.75)
    sec.top_margin=sec.bottom_margin=Inches(.7)
    for name in ('Normal','Title','Heading 1','Heading 2'):
        style=doc.styles[name];style.font.name='Microsoft YaHei'
        style._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
        style.font.color.rgb=RGBColor(0,0,0)
    doc.styles['Normal'].font.size=Pt(10)
    doc.styles['Normal'].paragraph_format.space_after=Pt(4)
    doc.styles['Normal'].paragraph_format.line_spacing=1.1
    doc.styles['Title'].font.size=Pt(17)
    doc.styles['Heading 1'].font.size=Pt(13)
    doc.styles['Heading 1'].paragraph_format.space_before=Pt(10)
    doc.styles['Heading 1'].paragraph_format.space_after=Pt(5)
    for style in doc.styles:
        for border in list(style._element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    def p(s):doc.add_paragraph(s)
    def table(headers,values):
        t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.alignment=WD_TABLE_ALIGNMENT.CENTER
        for c,s in zip(t.rows[0].cells,headers):c.text=s
        for vals in values:
            for c,s in zip(t.add_row().cells,vals):c.text=str(s)
        for i,row in enumerate(t.rows):
            for cell in row.cells:
                cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                pr=cell._tc.get_or_add_tcPr(); borders=OxmlElement('w:tcBorders')
                for side in ('top','left','bottom','right'):
                    b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
                pr.append(borders)
                if i==0:
                    fill=OxmlElement('w:shd');fill.set(qn('w:fill'),'EEEEEE');pr.append(fill)
                for q in cell.paragraphs:
                    q.paragraph_format.space_after=Pt(3);q.paragraph_format.space_before=Pt(3)
                    for r in q.runs:r.font.size=Pt(9);r.bold=(i==0)
    doc.add_paragraph('南水北调中线 WASP8 季节模型参数与复现说明',style='Title')
    p('本附录配套夏季与冬季独立率定及三因素情景研究，列明模型设定、参数来源和复现顺序。逐段、逐季的完整显式参数保存在配套 CSV 中；最终 WIF 保存求解器全部设置。')
    doc.add_heading('研究设计与数据边界',1)
    p('夏季对应 2020-08，冬季对应 2021-03。两季分别率定，不把一个季节用作另一个季节的检验集。模拟包含 29 个等效渠段；站 04—26 为 23 个共同干渠目标站，图像估读可用点分别为 20 和 22 个。四个连续站段按空间区间轮流留出。')
    p('Chl-a 为文献图像估读，站点匹配和重叠圆点存在误差。参数网格参考总体数据，冬季入口方案在第一轮试算后确定，空间检验因此属于条件性检验，不能视作完全独立的外部验证。')
    table(['设定','夏季','冬季'],[
        ['入口及初始 Chl-a（µg/L）','5','7'],['20°C 生长率（d⁻¹）','0.5','4'],
        ['最适温度（°C）','30','20'],['水下光衰减（m⁻¹）','0.7','0.3'],['N:C','0.15','0.10'],
        ['C:Chl-a / P:C','25 / 0.012','25 / 0.012'],['呼吸速率（d⁻¹）','0.02','0.02'],
        ['磷吸收半饱和常数（mg P/L）','0.001','0.001'],['实际统一水温（°C，约）','27.883','9.928'],
        ['生长温度系数 / 曲线形状系数','1 / 0.05','1 / 0.05'],['呼吸温度系数','1.07','1.07'],
        ['日均辐射（W/m²）/ 日照比例','150 / 0.5','150 / 0.5'],['渠宽 / 水深（m）','54 / 6.95','54 / 6.95'],
        ['模拟时长（d）','90','90']])
    doc.add_page_break()
    doc.add_heading('参数总表与工程对应关系',1)
    p(f'补充材料_WASP8季节模型完整参数总表.csv 共 {len(rows)} 条记录。每条均包含类别、季节、渠段、参数代码、原生名称、值、单位、证据状态及本项目内来源路径。动力学常数、时间函数和分段参数按基础命令与季节覆盖命令合并，以最终覆盖值为准。')
    p('总表包含显式设置及初始化占位值，不表示每个过程都参与本研究计算。未显式覆盖的内部默认值由随附基础与最终 WIF 保留。原生参数名来自随附 WASP8 参数数据库快照；完整函数值、逐段流量和几何量以 CSV 全精度值为准。')
    p('参数溯源命令用于核对设置来源，并非从空白渠网开始构建的完整脚本。复现计算从项目内保存的基础 WIF 开始；无需另取其他项目的工程文件。最终工程及其 SHA-256 见补充材料_季节独立率定参数与工程索引.csv。')
    doc.add_heading('缺失数据的替代及局限',1)
    p('渠道采用统一矩形断面，复杂水工结构等效简化；停留时间由流量和体积推算，未通过独立旅行时间验证。流量为按水量守恒整理的工况，不能代表完整调度过程。实测站点水温用于构造季节代表温度，实际 WIF 对全渠采用统一温度函数。')
    p('未获得同期入口 SRP/PO₄-P 时，基准 DIP 取 TP 的 10%；其他磷池按假设拆分。藻体氮磷从有机池扣除，维持入口总氮、总磷平衡。冬季入口 Chl-a 7 µg/L 和 N:C 0.10 为试算假设，非直接观测；DO 为代理输入，固定辐射和光衰减亦未通过现场光学数据验证。')
    p('每季运行温度增量 0、2、4°C，DIP 倍数 1、2、4，流量倍数 0.7、1、1.3，共 27 个组合。全体流路与取水同步缩放，体积和入口浓度固定，因此输入负荷随流量变化。DIP×4 不等同于 TP×4；90 日末值不一概视为严格稳态。')
    doc.add_heading('复现顺序',1)
    p('以项目根目录为工作目录，使用 Python、R 和本机 WASP8。求解脚本中的 WASP8 安装目录需与运行电脑一致。计算与绘图不依赖网络数据。')
    for s in [
        '1. fit_seasons_spatial_cv.py：两季分别执行参数网格与空间四折评分；run_winter_inlet_candidates.py 和 score_winter_inlet_exploration.py：冬季入口敏感性试算与评分。',
        '2. package_seasonal_models.py：汇集两套最终工程和参数索引；run_seasonal_scenarios.py 与 verify_seasonal_scenarios.py：运行并核验 54 个情景。',
        '3. build_parameter_appendix.py：重建本附录及完整参数总表；diagnose_seasonal_mechanisms.py：计算温度项和残余磷诊断。',
        '4. sync_chart_data.py 同步绘图数据，执行两份 plot_seasonal_*.R；build_submission_report.py 生成主报告。可统一执行 reproduce.py check 核查存档，或 reproduce.py report 重建图表和文档。render_word.ps1 导出 PDF。']:
        p(s)
    doc.save(REPORT)
    print('registry rows',len(rows));print(REPORT)

if __name__=='__main__': main()
