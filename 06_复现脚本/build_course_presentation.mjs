/** Course deck. Requires @oai/artifact-tool, or ARTIFACT_TOOL_MODULE pointing to its .mjs. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const {Presentation,PresentationFile,FileBlob}=await import(process.env.ARTIFACT_TOOL_MODULE ? pathToFileURL(process.env.ARTIFACT_TOOL_MODULE).href : '@oai/artifact-tool');
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const BUILD=process.env.PPT_BUILD_DIR || path.join(ROOT,'_qa_render','course_ppt');
await fs.mkdir(BUILD,{recursive:true});
const facts=JSON.parse(await fs.readFile(path.join(ROOT,'07_核查记录/report_facts.json'),'utf8'));
const csv=async name=>(await fs.readFile(path.join(ROOT,'chart_data',name),'utf8')).replace(/^\uFEFF/,'').trim().split(/\r?\n/).map(x=>x.split(',')).reduce((o,r,i,a)=>i?[...o,Object.fromEntries(r.map((v,j)=>[a[0][j],v]))]:o,[]);
const fitS=(await csv('seasonal_final_fit.csv')).filter(x=>x.period==='2020-08');
const fitW=await csv('winter_inlet_final_fit.csv');
const periods=['2020-08','2021-03'];
const cases=facts.scenarios;
const C=(p,t=0,d=1,q=1)=>Number(cases.find(x=>x.period===p && +x.T_plus_C===t && +x.DIP_factor===d && +x.Q_factor===q).mean23_Chla_ug_L);
const pct=(p,t,d,q)=>100*(C(p,t,d,q)/C(p)-1);
const round=(n,d=2)=>+n.toFixed(d);
const P=await PresentationFile.importPptx(await FileBlob.load(process.env.PPT_TEMPLATE || path.join(BUILD,'template-expanded.pptx')));
let slideIndex=0, figureIndex=0;
const ink='#293C47',gray='#5B6A72',summer='#B45339',winter='#247B8D',light='#E9EEF0',white='#FFFFFF';
const font='Microsoft YaHei';

const allNotes=[];
function text(s,txt,x,y,w,h,size=24,color=ink,bold=false){
 const z=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 z.text=txt;z.text.style={typeface:font,fontSize:size,color,bold}; return z;
}
const titles={
 '南水北调中线 WASP8':'课程汇报',
 '低磷背景下，复合扰动是否会放大藻类增长？':'1.1 背景简介与研究问题',
 '建模路线与输入输出':'1.2 研究目标与技术路线',
 '资料不足通过显式假设补齐':'2.1 数据收集与替代假设',
 '模型将沿程输运与藻类生长、损失同时计算':'2.2 模型构建与过程设置',
 '两季分别率定，季节内用空间区间留出检验':'2.3 分季节率定与空间检验',
 '模型接近平均水平，但局部起伏仍明显不足':'2.4 率定效果与适用范围',
 '三因素全因子情景：每季 27 组，共 54 组':'2.5 情景设计与交互分析',
 '夏季对增磷更敏感，冬季对升温更敏感':'3.1 结果一：两季单因素响应',
 '冬季升温后，增磷效应由弱转强':'3.2 结果二：升温与增磷联合响应',
 '冬季以温度×磷交互为主，夏季以磷×低流量为主':'3.3 结果三：因素交互作用分解',
 '温度响应曲线提供解释，也放大参数依赖':'3.4 机制解释：温度与损失平衡',
 '流量效应取决于净增长条件，低流量可放大联合响应':'3.5 机制解释：流量与停留时间',
 '政策建议聚焦季节性复合风险与同步监测':'4.1 政策建议与实施条件',
 '结论与课程作业的主要贡献':'4.2 研究总结与改进方向',
 '附录：关键参数与交互定义':'附录 A 关键参数与交互定义',
 '附录：资料来源与复现入口':'附录 B 资料来源与复现入口'
};
function slide(title,note,source='本项目提交稿及对应 WASP8 输出'){
 const s=P.slides.items[slideIndex++];
 if(!s)throw new Error('Insufficient duplicated template slides');
 const header=s.shapes.items.find(z=>String(z.text)==='2.1 标题');
 if(!header)throw new Error('Template heading was not preserved');
 header.text=titles[title]||title;
 header.position={left:133.33,top:18.17,width:865,height:54.93};
 header.text.style={typeface:'Arial',fontSize:'28pt',bold:true,color:'#8B0012'};
 text(s,source,60,675,1100,26,14.6667,gray);
 text(s,String(slideIndex).padStart(2,'0'),1175,675,50,26,14.6667,gray);
 s.speakerNotes.text=note+'\n\n资料来源：'+source;
 allNotes.push({slide:slideIndex,title:titles[title]||title,note,source});return s;
}

function table(s,values,y=160,widths=[350,380,430],height=360,size=25){
 const tb=s.tables.add({rows:values.length,columns:values[0].length,left:60,top:y,width:1160,height,columnWidths:widths,values});
 tb.borders.assign({fill:white,width:3,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=tb.getCell(r,c);cell.fill=r===0?'#8B0012':(r%2?'#F6F2F3':white);
  cell.text.style={typeface:font,fontSize:size,bold:r===0,color:r===0?white:ink};
 }
 return tb;
}
const axisStyle={typeface:font,fontSize:21,fill:gray};
const figureNames=['fit_summer','fit_winter','single_factor','tp_summer','tp_winter','interactions','temperature_summer','temperature_winter','flow_response'];
const figureBytes=Object.fromEntries(await Promise.all(figureNames.map(async name=>[name,new Uint8Array(await fs.readFile(path.join(ROOT,'04_figures/course_presentation_R',name+'.png')))])));
function chart(s,type,cats,series,box,opt={}){
 const name=figureNames[figureIndex++];
 if(!name)throw new Error('Unexpected scientific chart');
 return s.images.add({blob:figureBytes[name],contentType:'image/png',alt:'R 绘制：'+name,fit:'contain',position:{left:box[0],top:box[1],width:box[2],height:box[3]}});
}

const series=(name,values,color,markers=false)=>({name,values,fill:color,line:{fill:color,width:3},marker:{symbol:markers?'circle':'none',...(markers?{size:7,fill:color}:{})}});
const sourceScenario='数据：季节三因素_情景汇总.csv；第 90 天、23 个干渠段体积加权 Chl-a';
const sourceInteraction='数据：季节三因素_交互分解.csv；交互项单位为 µg/L';

// 01. Typographic cover.
{
 const s=slide('南水北调中线 WASP8',
 '本课程作业从现有数据出发，建立可运行的简化输水渠模型，分别率定夏季和冬季工况，再比较升温、可利用磷和流量变化。汇报重点是两季响应为何不同，以及因素联合变化是否产生非加法效应。全部结果是固定工况下的条件性压力测试，不是未来某年的气候预测。建议正文用时约15分钟，最后两页备查。','课程汇报 · 基于提交稿与参数补充材料');
 text(s,'南水北调中线 WASP8\n季节藻类模拟与交互响应',90,194,1130,178,54,'#8B0012',true);
 text(s,'分季节建模  /  全因子情景  /  管理启示',60,428,1110,50,30,gray);
 text(s,'夏季  2020-08',60,548,470,50,30,summer,true);
 text(s,'冬季  2021-03',650,548,470,50,30,winter,true);
}
// Chapter map.
{
 const s=slide('汇报提纲','汇报分为四章。第一章说明低磷背景下的研究问题与目标。第二章解释数据、假设、模型构建、分季节率定与情景设计。第三章依次展示单因素、联合响应和交互分解，再解释温度与流量机制。第四章提出对应管理建议，说明实施条件和下一步改进。');
 const parts=[['1','背景与目标','低磷背景、研究问题与技术路线'],['2','数据与建模方法','数据收集、模型构建、率定与情景设计'],['3','结果与机制解释','两季响应差异、因素交互及过程解释'],['4','政策建议与总结','季节性监测重点、调度评估与改进方向']];
 parts.forEach((v,i)=>{const y=155+i*112;text(s,v[0],90,y,75,60,42,'#8B0012',true);text(s,v[1],192,y,1000,49,32,ink,true);text(s,v[2],192,y+52,1000,45,25,gray);});
}
// 02. Research question.
{
 const s=slide('低磷背景下，复合扰动是否会放大藻类增长？',
 '文献描述南水北调中线长期低磷环境，并讨论小基因组蓝藻在低磷条件下的优势。本作业不预设渠道已发生普遍富营养化，而是研究外源磷增加、升温和调度流量共同改变时的潜在增殖响应。Chl-a表示综合浮游植物藻量，不能区分蓝藻主导、种属或产毒性。公开多年TP数据仅作背景对照，没有拼接成同期连续入口边界。',
 '背景：Wang 等，Science Bulletin，2025；Chen 等，The ISME Journal，2023');
 text(s,'研究对象：长距离输水渠道中的综合浮游植物',60,142,1160,50,30,ink,true);
 text(s,'01',60,246,80,60,38,summer,true);text(s,'相同扰动下，夏季和冬季的藻量响应是否一致？',156,246,1050,66,30);
 text(s,'02',60,358,80,60,38,winter,true);text(s,'升温、增磷与流量变化能否产生超过简单相加的效应？',156,358,1050,82,30);
 text(s,'03',60,480,80,60,38,ink,true);text(s,'哪些结果可以转化为监测重点与调度评估依据？',156,480,1050,70,30);
 text(s,'输出指标：叶绿素 a（Chl-a，µg/L），用于比较条件性增殖响应。',60,602,1160,40,23,gray);
}
// 03. Workflow as editable table.
{
 const s=slide('建模路线与输入输出',
 '首先统一站点、单位和两期环境资料，记录所有替代假设。然后构建29段一维等效渠网，预设流量及分流取水关系，以水量守恒完成输运配置。再分别率定夏季和冬季的藻类参数，利用季节内空间分块留出检验。最后每季运行27个组合，用统一指标进行交互分解。这里的水动力基础是给定流量的输运配置，不是完整动量方程水动力求解。营养盐用于输入分配和守恒核验，未单独开展营养盐过程率定。');
 table(s,[['环节','主要输入','形成的结果'],['数据准备','env.xlsx、文献与图像估读','站点表、边界与假设清单'],['渠网与输运','段长、断面、流量与分流','29 段体积与守恒流路'],['分季节率定','温度、光照、N/P 组分、Chl-a','两套参数与空间留出误差'],['情景与交互','升温 × DIP × 流量','54 组情景、效应分解与建议']],155,[285,455,420],380,25);
 text(s,'全部 29 段参与求解；比较指标聚焦分叉前 23 个干渠段。',60,579,1160,52,28,ink,true);
}
// 04. Data assumptions.
{
 const s=slide('资料不足通过显式假设补齐',
 '几何采用宽54m、深6.95m的统一矩形断面，复杂水工结构等效简化，保留分流和取水。两期只有空间快照，不作真实逐日预报。Chl-a从Science Bulletin补充图Fig.S2高清散点估读，匹配候选站点后夏季20点、冬季22点。图像点有重叠和相邻站歧义，不能作为实验原值。基准溶解无机磷DIP为TP的10%，其余磷形态按质量平衡拆分。光照使用固定代理值。入口Chl-a及冬季N:C的探索会影响季节比较，因此结果需结合假设解释。DO为代理输入，未报告同期DO率定。');
 table(s,[['必要输入','本作业采用方式','影响解释的局限'],['几何与流量','统一断面 + 两期守恒流量','未约束局部水工及真实旅行时间'],['Chl-a 观测','夏季 20 点 / 冬季 22 点估读','重叠点与站点匹配存在误差'],['溶解无机磷','DIP = TP 的 10%','缺少同期磷形态实测'],['光照与温度','固定光照 + 全渠代表水温','未描述逐时及沿程变化']],150,[260,430,470],390,24);
 text(s,'假设、参数、边界及运行工程均保留，便于复现与替换。',60,581,1160,55,28,ink,true);
}
// Governing processes. Added to make the modeling logic explicit.
{
 const s=slide('模型将沿程输运与藻类生长、损失同时计算',
 '每段质量变化等于所有入流携带的物质，减所有出流及取水携带的物质，再加局地反应。给定流量、段长与统一断面后，体积和停留时间确定。反应项按WASP8多藻类框架计算，生长受温度、光照和营养条件调节，呼吸等损失单独计算。这里的图示文字是过程概括，不能代替WASP内部完整反应方程。工程采用一个综合Chl-a状态变量，不分具体藻种。入口浓度均匀初始化全部渠段，不把下游观测直接填入初值。两季各自保持外部强迫90天，取末日结果。营养盐进行形态拆分与守恒检查，未完成独立营养盐过程率定。纵向弥散基准0，非捕食死亡与摄食显式0，底泥释放和自遮光未启用。',
 '依据：EPA WASP8 模型指南；本项目最终 WIF 与提交稿 Methods');
 text(s,'每段物质量变化 = 入流携带 − 出流携带 + 局地反应',60,155,1160,65,34,ink,true);
 text(s,'输运部分',60,280,470,50,31,summer,true);
 text(s,'段长 × 统一断面确定体积\n给定流量与取水满足水量守恒\n体积与流量共同决定停留时间',60,350,535,162,28);
 text(s,'藻类反应部分',665,280,555,50,31,winter,true);
 text(s,'温度、光照和营养条件调节生长\n呼吸等损失与生长共同决定净变化\n以一个综合 Chl-a 状态量表示藻量',665,350,555,162,28);
 text(s,'入口浓度均匀初始化全渠；每季在固定外部强迫下计算 90 天。',60,584,1160,63,27,gray);
}
// 05. Calibration design.
{
 const s=slide('两季分别率定，季节内用空间区间留出检验',
 '2020-08称夏季，2021-03称冬季，为本课程命名约定，月份不变。站03为入口，站04至26共23个共同目标站。固定四折分别为04—09、10—15、16—21、22—26，每次用其他区间的Chl-a评分选择参数，再评价留出区间，模型仍模拟全部29段。每季候选为G20三水平、Topt三水平和Kd两水平，共18组。冬季第一轮表现较差，后续入口Chl-a用5、6、7µg/L探索并将N:C由0.15设为0.10，最终用7。因探索由首轮结果触发，冬季最终分数属于条件性空间检验，非独立外部验证。');
 text(s,'独立参数化',60,146,1100,48,30,ink,true);
 table(s,[['最终设置','夏季','冬季'],['生长率 G20 / 最适温度','0.5 d⁻¹ / 30°C','4.0 d⁻¹ / 20°C'],['光衰减 Kd / 入口 Chl-a','0.7 m⁻¹ / 5 µg/L','0.3 m⁻¹ / 7 µg/L']],210,[360,400,400],218,26);
 text(s,'固定四折：04–09    10–15    16–21    22–26',60,473,1160,50,30);
 text(s,'留出的是 Chl-a 评分数据，求解渠网始终完整。',60,541,1160,45,27,gray);
 text(s,'冬季入口组成为事后探索，最终检验结果具有条件性。',60,603,1160,40,23,gray);
}
// 06. Fit vs observations with native scatter charts.
{
 const s=slide('模型接近平均水平，但局部起伏仍明显不足',
 '图中橙色或青色实线为全样本最终拟合，灰点为图像估读观测，不应将这条拟合线称为留出预测线。下方指标来自对应的空间四折留出预测。夏季模型RMSE1.903，对照训练集均值1.916，改善很小；冬季最终条件性RMSE2.452，对照2.589，改善约5.3%。夏季NSE为−0.061，冬季合并NSE为0.039，不能据此宣称已精确重现沿程分布。冬季逐折NSE均负，合并略正来自分母不同。观测均值夏季5.849、冬季6.457，拟合均值5.814、6.578，但拟合标准差仅0.402和0.243，体现平滑性。',
 '数据：季节独立率定与冬季入口组成探索的最终拟合、空间四折留出结果');
 for(const [i,dat,col,season] of [[0,fitS,summer,'夏季'],[1,fitW,winter,'冬季']]){
  text(s,season,70+i*595,139,530,42,29,col,true);
  const ser=[{name:'图像估读',xValues:dat.map(x=>+x.distance_km),values:dat.map(x=>+x.observed_ug_L_approx),line:{fill:'none',width:0},marker:{symbol:'circle',size:7,fill:'#929C9F'}},
   {name:'最终拟合',xValues:dat.map(x=>+x.distance_km),values:dat.map(x=>+x.final_fitted_ug_L),line:{fill:col,width:3},marker:{symbol:'none'}}];
  chart(s,'scatter',[],ser,[60+i*595,184,565,345],{scatterOptions:{style:'lineWithMarkers'},xAxis:{min:0,max:1200,majorUnit:400,textStyle:axisStyle,title:'沿程距离 / km'},yAxis:{min:0,max:14,majorUnit:4,textStyle:axisStyle,majorGridlines:{fill:light,width:1},title:'Chl-a / µg/L'}});
 }
 text(s,'留出 RMSE   1.903 µg/L\n均值基线      1.916 µg/L',83,552,530,77,26,summer,true);
 text(s,'条件性留出 RMSE   2.452 µg/L\n均值基线                  2.589 µg/L',676,552,540,77,26,winter,true);
}
// 07. Factorial design.
{
 const s=slide('三因素全因子情景：每季 27 组，共 54 组',
 '每季均使用最终模型运行3×3×3个情景。温度在全渠代表水温上加0、2、4°C。DIP在入口和所有初始浓度上乘1、2、4，其他磷组分不变，因此DIP四倍不等于TP四倍。流量同步缩放入口、各流路与取水，体积固定、入口浓度固定，因此质量负荷也随Q改变。这不是固定负荷下的纯水动力实验。运行90天，取第90天而非宣称严格稳态。主要指标为23干渠段体积加权Chl-a，与校准20/22观测点的算术统计口径不同。所有情景是压力测试，没有对应未来年份或RCP路径。');
 table(s,[['因素','水平','边界含义'],['升温 ΔT','0 / +2 / +4°C','全渠水温同步增加'],['DIP 倍率','1 / 2 / 4','入口与初值改变，其他 P 固定'],['流量 Q 倍率','0.7 / 1.0 / 1.3','流路与取水同步缩放']],171,[260,390,510],310,27);
 text(s,'第 90 天的 23 段体积加权 Chl-a 用于统一比较',60,512,1160,42,27,ink,true);
 text(s,'净非加法效应 = 联合增量 − 三个单因素增量之和',60,562,1160,40,25,ink);
 text(s,'DIP ×4 不等于 TP ×4；固定入口浓度时，流量改变也会改变输入负荷。',60,615,1160,42,22,gray);
}
// 08. Single factor response.
{
 const s=slide('夏季对增磷更敏感，冬季对升温更敏感',
 '各单因素情景只改变一个因素，其余保持基准。夏季单独+4°C使均值从5.814降至5.505，变化−5.3%；DIP四倍升至8.784，+51.1%。冬季单独+4°C从6.588升至9.508，+44.3%；DIP四倍仅升至6.748，+2.4%。这表示在两套最终参数化的基准工况下，边际响应不同，不是实测验证的普适季节规律。低流量单独作用较弱，不能据此判断其在联合胁迫下也不重要。',sourceScenario);
 text(s,'夏季对增磷更敏感，冬季对升温更敏感',60,132,1160,42,28,ink,true);
 const levels=[[4,1,1],[0,4,1],[0,1,.7],[0,1,1.3]];
 chart(s,'bar',['升温 +4°C','DIP ×4','流量 −30%','流量 +30%'],periods.map((p,i)=>series(i?'冬季':'夏季',levels.map(v=>round(pct(p,...v),1)),i?winter:summer)),[60,187,1160,402],{
  yAxis:{min:-20,max:60,majorUnit:20,textStyle:axisStyle,majorGridlines:{fill:light,width:1},numberFormatCode:'0'},
  dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:24,bold:true}}});
 text(s,'两季差异同时受温度、率定参数和入口组成影响。',60,613,1160,42,25,gray);
}
// 09. T-P response.
{
 const s=slide('冬季升温后，增磷效应由弱转强',
 '这里固定Q为1，横轴为DIP倍率，分别比较原温和+4°C。夏季DIP由1升到4时，原温增加2.970µg/L，+4°C时增加2.777，温度×磷交互约−0.193。冬季相应增量从0.160升到7.759，差为+7.599，是强正交互。冬季23段残余DIP均值从基准0.001141mgP/L降到升温但未增磷的0.000228，再在升温且DIP四倍时回到0.001024。它与升温后磷需求增强相一致，但残余浓度不是净吸收通量，不能据此排除其他限制过程。',sourceScenario);
 for(const [i,p,col,name]of [[0,periods[0],summer,'夏季'],[1,periods[1],winter,'冬季']]){
  text(s,name,68+i*595,140,545,42,29,col,true);
  chart(s,'line',['1','2','4'],[series('原温',[1,2,4].map(d=>C(p,0,d,1)),col,true),series('+4°C',[1,2,4].map(d=>C(p,4,d,1)),ink,true)],[60+i*595,188,565,355],{
   yAxis:{min:0,max:20,majorUnit:5,textStyle:axisStyle,title:'Chl-a / µg/L',majorGridlines:{fill:light,width:1}},xAxis:{textStyle:axisStyle,title:'DIP 倍率'}});
 }
 text(s,'增磷增量：2.97 → 2.78 µg/L',76,570,550,45,27,summer,true);
 text(s,'增磷增量：0.16 → 7.76 µg/L',671,570,550,45,27,winter,true);
 text(s,'流量保持基准；“增磷增量”指 DIP 从 1 倍升至 4 倍的 Chl-a 差值。',60,625,1160,35,21,gray);
}
// 10. Exact interaction decomposition.
{
 const s=slide('冬季以温度×磷交互为主，夏季以磷×低流量为主',
 '交互按全因子差分定义。温度×磷在Q基准下等于联合响应减两个单因子响应再加基准；温度×流量及磷×流量同理。三因素项用八角点包含排除式。净非加法效应等于联合增量减三个单因子增量，也等于三个二阶项加一个三阶项。图示+4°C、DIP×4、Q0.7。夏季交互项依次−0.193、−0.078、+1.481、−0.117，总和+1.093；冬季+7.599、+0.215、+0.059、+0.714，总和+8.587。夏季三阶项为负，不能称两季三阶均放大。正值表示超过简单相加，不代表统计显著性，未做重复试验或置信区间。',sourceInteraction);
 text(s,'组合：+4°C、DIP ×4、流量 −30%',60,135,1160,43,27,gray);
 const vals=periods.map(p=>facts.interactions.find(x=>x.period===p && +x.Q_factor===.7));
 chart(s,'bar',['温度 × 磷','温度 × 流量','磷 × 流量','三因素'],vals.map((v,i)=>series(i?'冬季':'夏季',['I_TP_ug_L','I_TQ_ug_L','I_PQ_ug_L','I_TPQ_ug_L'].map(k=>round(+v[k],2)),i?winter:summer)),[60,187,1160,365],{
  yAxis:{min:-2,max:10,majorUnit:2,textStyle:axisStyle,majorGridlines:{fill:light,width:1}},
  dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:22,bold:true}}});
 text(s,'夏季以磷×低流量为主，冬季以温度×磷为主',60,575,1160,43,28,ink,true);
 text(s,'净非加法效应：夏季 +1.09 µg/L，冬季 +8.59 µg/L',60,626,1160,38,25,gray);
}
// 11. Temperature mechanism.
{
 const s=slide('温度响应曲线提供解释，也放大参数依赖',
 '曲线使用工程实际温度函数：温度因子相对值exp{-0.05[(T0+ΔT−Topt)²−(T0−Topt)²]}，生长温度系数为1。呼吸相对值为1.07^ΔT。夏季T0=27.883，Topt30，+2°C时温度因子1.250，+4°C时1.048，呼吸则分别1.145、1.311。虽然+4°C超过最适温度，但生长温度因子仍略高于原工况，不能只凭超过最适温度就解释净藻量下降，需要看生长与损失及营养条件的共同平衡。冬季T0=9.928，Topt20，+4°C时温度因子比值25.25，但最终藻量只增44.3%，不能混淆。两图纵轴尺度不同，单位都是相对倍数。本页是既定函数诊断，不是完整过程通量归因。',
 '来源：季节机制诊断_温度曲线与残余磷.csv；最终 WIF 温度与呼吸参数');
 for(const [i,t0,opt,col,name,max,step]of [[0,27.882758620689657,30,summer,'夏季：接近最适温度',1.5,.5],[1,9.927586206896551,20,winter,'冬季：低于最适温度',30,10]]){
  const dt=[0,1,2,3,4];
  text(s,name,65+i*595,140,560,44,29,col,true);
  chart(s,'line',dt.map(String),[series('生长温度因子',dt.map(d=>Math.exp(-.05*((t0+d-opt)**2-(t0-opt)**2))),col,true),series('呼吸温度因子',dt.map(d=>1.07**d),'#78848B',true)],[60+i*595,192,565,355],{
   yAxis:{min:0,max,majorUnit:step,textStyle:axisStyle,title:'相对基准 / 倍',majorGridlines:{fill:light,width:1}},xAxis:{textStyle:axisStyle,title:'升温 / °C'}});
 }
 text(s,'+4°C：生长 1.05 倍，呼吸 1.31 倍',65,570,560,60,26,summer,true);
 text(s,'+4°C：生长温度项 25.25 倍',660,570,560,60,26,winter,true);
 text(s,'注意两图纵轴不同；温度因子倍数不等于 Chl-a 倍数。',60,626,1160,38,22,gray);
}
// 12. Flow in combined disturbance.
{
 const s=slide('流量效应取决于净增长条件，低流量可放大联合响应',
 '固定体积下Q0.7使停留时间约变为1.43倍，Q1.3变为0.77倍。单独低流量时夏季约+2.0%、冬季−2.4%，但升温与增磷同时发生时，两季联合藻量都在低流量下更高。+4°C且DIP四倍，夏季Q0.7、1、1.3的均值分别9.69、8.28、7.41，冬季18.09、17.27、16.38。相对于各自原始基准，低流量组合增长66.6%和174.7%。机制上延长停留时间可放大净积累，也可放大净损失。基准夏季沿程均值5.81高于入口5，冬季6.59低于入口7，与两季单独低流量方向相符。由于Q与入口质量负荷同时变化，这些结果无法直接给出真实增流调度的效果，应补固定磷负荷对照。',sourceScenario);
 text(s,'固定 +4°C 与 DIP ×4，比较流量变化',60,135,1160,43,27,gray);
 chart(s,'line',['0.7','1.0','1.3'],periods.map((p,i)=>series(i?'冬季':'夏季',[.7,1,1.3].map(q=>round(C(p,4,4,q))),i?winter:summer,true)),[60,190,810,398],{
  yAxis:{min:0,max:22,majorUnit:5,textStyle:axisStyle,title:'Chl-a / µg/L',majorGridlines:{fill:light,width:1}},xAxis:{textStyle:axisStyle,title:'流量倍率'},
  dataLabels:{showValue:true,position:'top',textStyle:{typeface:font,fontSize:23}}});
 text(s,'流量 −30% 时',925,236,290,45,28,ink,true);
 text(s,'夏季 +66.6%',925,308,290,48,31,summer,true);
 text(s,'冬季 +174.7%',925,377,290,48,31,winter,true);
 text(s,'相对各季原始基准',925,450,290,48,23,gray);
 text(s,'调度评估需同时核算停留时间、入口浓度与磷质量负荷。',60,618,1160,44,26,gray);
}
// 13. Policy matrix.
{
 const s=slide('政策建议聚焦季节性复合风险与同步监测',
 '建议按风险组合而非只看单项浓度组织监测。冬季关注异常升温与可利用磷同步升高，增加入口及沿程水温、SRP/PO4-P、TP、Chl-a同步观测，并核查可控磷来源。夏季低流量期出现磷异常时，优先削减可避免外源输入，结合真实调度、分流和旅行时间核算停留时间。调度层面比较方案时同时看浓度与质量通量，在供水约束下补固定磷负荷对照。Chl-a只能表示藻量，涉及毒性或饮水安全判断时需增加群落、产毒种或毒素监测。本模型的+4°C、DIP四倍和Q0.7是试验水平，不能当成运行报警阈值，也不支持给出最优流量。');
 table(s,[['重点场景','可执行建议','实施前需核实'],['冬季异常升温 + 磷增加','同步监测水温、SRP/TP 与 Chl-a\n核查可控磷来源','连续观测及藻类组成'],['夏季低流量 + 磷异常','减少可避免的外源磷输入\n核算停留时间与磷负荷','真实分流、取水和旅行时间'],['供水调度方案比较','同时评价浓度与质量通量\n设置固定磷负荷对照','供水约束与独立模型检验']],164,[330,490,340],370,25);
 text(s,'试验情景可帮助确定监测重点，尚不足以设定调度或藻华报警阈值。',60,582,1160,65,27,ink,true);
}
// 14. Closing.
{
 const s=slide('结论与课程作业的主要贡献',
 '本作业的工作量体现在可追溯数据包、显式假设、29段实际WASP工程、分季节率定和留出检验，以及54组实际模型运行与交互分解。核心结论是夏季基准下更敏感于磷，冬季升温使磷的边际效应增强，低流量可在联合扰动下进一步提高藻量。创新点是将分季节参数化与全因子精确差分结合，直接展示非加法效应，不需要额外用SHAP重复解释同一小型全因子设计。本研究的可用范围是条件性机制探索与监测优先级，不是发生概率或精确空间预报。未来优先取得同期Chl-a、SRP和真实旅行时间，用其替换最敏感假设，并加入参数不确定性和固定负荷对照。');
 text(s,'可复现的课程模型',60,157,1130,52,34,ink,true);
 text(s,'数据与假设清单、两套季节工程、54 组运行及交互分解。',60,225,1130,62,28,gray);
 text(s,'两季风险组合不同',60,323,1130,52,34,ink,true);
 text(s,'夏季关注磷与低流量；冬季关注升温与磷同步增加。',60,391,1130,62,28,gray);
 text(s,'下一步优先补足关键约束',60,488,1130,52,34,ink,true);
 text(s,'同期 Chl-a、磷形态与旅行时间，并检验参数不确定性。',60,556,1130,62,28,gray);
}
// 15. Backup parameters.
{
 const s=slide('附录：关键参数与交互定义',
 '本页用于答辩备查，完整1185行显式参数见参数总表，工程WIF保存内部配置。两季C:Chl-a25、P:C0.012，N:C夏季0.15、冬季0.10。冬季入口7µg/L的藻氮占可分配氮余额92.1%，其组成假设尤其重要。生长温度曲线两侧形状参数0.05，呼吸系数0.02d−1、温度系数1.07。非捕食死亡和浮游动物摄食显式为0。下方以温度磷交互为例，C00为基准温度基准磷，CT0仅升温，C0P仅增磷，CTP联合；流量固定基准。三阶交互按八角点包含排除计算。',
 '来源：参数补充材料、完整参数总表及最终 WIF');
 table(s,[['参数','夏季','冬季'],['代表水温 / 最适温度','27.883 / 30°C','9.928 / 20°C'],['入口 Chl-a / N:C','5 µg/L / 0.15','7 µg/L / 0.10'],['磷半饱和常数','0.001 mg P/L','0.001 mg P/L'],['氮半饱和常数','0.020 mg N/L','0.020 mg N/L'],['呼吸系数 / 温度系数','0.02 d⁻¹ / 1.07','0.02 d⁻¹ / 1.07']],151,[420,370,370],368,24);
 text(s,'I温度×磷 = C温度+磷 − C仅温度 − C仅磷 + C基准',60,565,1160,54,29,ink,true);
}
// 16. References and reproducibility.
{
 const s=slide('附录：资料来源与复现入口',
 '参考资料为EPA WASP8多藻类用户指南、2025 Science Bulletin文章及2023 ISME Journal文章。Chl-a估读来自2025文章补充图S2，未在本PPT重印原图。现有提交稿、参数补充、输入、脚本、工程和结果均在02_version2中。公开项目提供可追踪的源码和输入输出。复现数值检查命令为python 06_复现脚本/reproduce.py check；完整模型运行需要本机WASP8和相关可执行程序。当前PPT中所有结果图由R根据已核查数据重绘，保留绘图脚本、高清PNG和矢量PDF/SVG，没有增加新模型结果。',
 '本地：02_version2；公开仓库：JZCheng-12/SNWDP-WASP8-Seasonal-Algae');
 text(s,'WASP8 模型理论与指南',60,151,1150,42,29,ink,true);
 text(s,'Wool、Ambrose 与 Martin，US EPA\nhttps://www.epa.gov/sites/default/files/2018-05/documents/mpm-user-guide.pdf',60,207,1150,68,22,gray);
 text(s,'Wang 等，Science Bulletin 70 (2025) 4263–4275\nGenomic blueprint enables early intervention in cyanobacterial risk management\nDOI: 10.1016/j.scib.2025.11.005',60,310,1150,100,23);
 text(s,'Chen 等，The ISME Journal 17 (2023) 1719–1732\nVirus–pathogen interactions improve water quality along the Middle Route\nof the South-to-North Water Diversion Canal · DOI: 10.1038/s41396-023-01481-2',60,438,1150,106,23);
 text(s,'https://github.com/JZCheng-12/SNWDP-WASP8-Seasonal-Algae',60,592,1160,48,23,winter,true);
}

// R renders all scientific figures. This exporter only assembles the supplied template and slide text.
if(slideIndex!==18 || figureIndex!==9)throw new Error('Slide or R-figure inventory mismatch');
await fs.writeFile(path.join(BUILD,'speaker_notes.json'),JSON.stringify(allNotes,null,2),'utf8');
await (await PresentationFile.exportPptx(P)).save(path.join(BUILD,'candidate.pptx'));
for(let i=0;i<P.slides.items.length;i++){
 const png=await P.export({slide:P.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(BUILD,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
console.log(JSON.stringify({slides:P.slides.items.length,build:BUILD}));
