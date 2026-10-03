/* 教学几何直接计算；软间隔模型全部来自真实离散预计算。 */
(()=>{
'use strict';
const D=window.SVM_TEACHING,colors=['#245e91','#d17b26'];
const cfg={responsive:true,displaylogo:false,toImageButtonOptions:{scale:2}};
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),fmt=x=>Number(x).toFixed(3);
function cards(el,items,note){const root=el.querySelector('.lab-stats');root.replaceChildren();for(const [title,value] of items){const c=document.createElement('div');c.className='stat-card';const l=document.createElement('span');l.className='stat-label';l.textContent=title;const v=document.createElement('strong');v.className='stat-value';v.textContent=value;c.append(l,v);root.append(c);}const p=document.createElement('p');p.className='stat-note';p.textContent=note;root.append(p);}
function choice(el,name,title,values,initial=0){const l=document.createElement('label');l.textContent=title+' ';const s=document.createElement('select');s.name=name;s.setAttribute('aria-label',title);values.forEach((v,i)=>{const o=document.createElement('option');o.value=i;o.textContent=v;s.append(o);});s.value=initial;l.append(s);el.querySelector('.lab-controls').append(l);return s;}
function range(el,name,title,min,max,step,value){const l=document.createElement('label');l.textContent=title+' ';const s=document.createElement('input');Object.assign(s,{type:'range',name,min,max,step,value});s.setAttribute('aria-label',title);const o=document.createElement('output');o.textContent=value;s.addEventListener('input',()=>o.textContent=s.value);l.append(s,o);el.querySelector('.lab-controls').append(l);return s;}
function reset(el,inputs,values,fn){const b=document.createElement('button');b.type='button';b.textContent='重置';b.addEventListener('click',()=>{inputs.forEach((s,i)=>{s.value=values[i];s.dispatchEvent(new Event(s.type==='range'?'input':'change'));});fn();});el.querySelector('.lab-controls').append(b);}
function points(X,y){return [-1,1].map((k,index)=>{const ids=y.map((v,i)=>v===k?i:-1).filter(i=>i>=0);return {type:'scatter',mode:'markers+text',name:k===1?'正类 +1':'负类 −1',x:ids.map(i=>X[i][0]),y:ids.map(i=>X[i][1]),text:ids.map(i=>'样本'+i),textposition:'top center',customdata:ids,marker:{size:13,color:colors[index]},hovertemplate:'样本 %{customdata}<br>(%{x:.2f}, %{y:.2f})<extra>%{fullData.name}</extra>'};});}
function line(w,b,level,name,color,dash='solid'){const P=[];if(Math.abs(w[1])>1e-10)for(const x of [-3,3]){const y=(level-b-w[0]*x)/w[1];if(Math.abs(y)<=3.00001)P.push([x,y]);}if(Math.abs(w[0])>1e-10)for(const y of [-3,3]){const x=(level-b-w[1]*y)/w[0];if(Math.abs(x)<=3.00001)P.push([x,y]);}return{type:'scatter',mode:'lines',x:P.slice(0,2).map(p=>p[0]),y:P.slice(0,2).map(p=>p[1]),name,line:{color,width:level===0?3.5:2,dash},hoverinfo:'name'};}
function boundary(w,b,band=true){return [line(w,b,0,'决策边界 f=0','#17324d'),...(band?[line(w,b,1,'正侧参考线 f=+1','#137d80','dash'),line(w,b,-1,'负侧参考线 f=−1','#b96a15','dash')]:[])];}
function draw(el,traces,title,extra={}){return Plotly.react(el.querySelector('.lab-plot'),traces,{title:{text:title,font:{size:18}},height:860,font:{family:'Segoe UI,Microsoft YaHei,sans-serif',size:14,color:'#30323b'},paper_bgcolor:'#fffdf9',plot_bgcolor:'#faf7f1',xaxis:{title:'x₁',range:[-3,3],zeroline:false,constrain:'domain'},yaxis:{title:'x₂',range:[-3,3],zeroline:false,scaleanchor:'x',constrain:'domain'},legend:{orientation:'h',y:-.13},margin:{l:65,r:35,t:60,b:110},...extra},cfg);}
function geometry(el){const angle=range(el,'angle','法向量角度',-80,80,1,0),bias=range(el,'bias','基准截距 b₀',-2,2,.05,0),scale=choice(el,'scale','参数整体缩放',[.5,1,2,5],1),p=choice(el,'point','观察样本',D.points.map((_,i)=>i),3),band=choice(el,'band','显示',['仅决策边界','增加参考间隔线'],0);
 const update=()=>{const s=[.5,1,2,5][scale.value],a=+angle.value*Math.PI/180,w=[s*Math.cos(a),s*Math.sin(a)],b=s*Number(bias.value),x=D.points[p.value],score=dot(w,x)+b,n=Math.hypot(...w),foot=x.map((v,i)=>v-score*w[i]/n**2),margin=D.labels[p.value]*score,correct=D.points.filter((v,i)=>(dot(w,v)+b>=0?1:-1)===D.labels[i]).length;
 draw(el,[...points(D.points,D.labels),...boundary(w,b,band.value==='1'),{type:'scatter',mode:'lines+markers',name:'所选样本到垂足',x:[x[0],foot[0]],y:[x[1],foot[1]],line:{color:'#ae3953',width:3},marker:{size:8}}],'分类分数与同一条边界');
 cards(el,[['正确分类',correct+' / 6'],['分数 f(x)',fmt(score)],['函数间隔 yf',fmt(margin)],['‖w‖',fmt(n)],['几何间隔 yf/‖w‖',fmt(margin/n)],['无符号距离',fmt(Math.abs(score)/n)]],'手动几何，未求最优模型。实际参数为 s·(w₀,b₀)，整体缩放不改变边界与垂足；参考 f=±1 线会随尺度变化。');el.dataset.scale=s;
 };[angle,bias,p,scale,band].forEach(v=>v.addEventListener(v.type==='range'?'input':'change',update));reset(el,[angle,bias,scale,p,band],[0,0,1,3,0],update);update();}
function projection(el){
 const scale=choice(el,'scale','参数整体缩放',[.5,1,2,5],1);
 const update=()=>{
  const s=[.5,1,2,5][scale.value],w=[3*s,4*s],b=-5*s,foot=[.76,.68],unit=[.6,.8],tangent=[-.8,.6];
  const q=foot.map((v,i)=>v+.12*unit[i]),r=q.map((v,i)=>v+.12*tangent[i]),u=foot.map((v,i)=>v+.12*tangent[i]);
  const label=(x,y,text,ax,ay)=>({x,y,text,ax,ay,xref:'x',yref:'y',showarrow:true,arrowhead:0,arrowwidth:1,arrowcolor:'#8a7d70',bgcolor:'rgba(255,253,249,.96)',borderpad:5,font:{size:14,color:'#352f2a'}});
  draw(el,[line(w,b,0,'超平面 3x₁+4x₂−5=0','#17324d'),
   {type:'scatter',mode:'lines+markers',x:[1,.76],y:[1,.68],name:'垂直距离 d=0.4',line:{color:'#ae3953',width:3},marker:{size:9,color:'#ae3953'},hovertemplate:'(%{x:.2f}, %{y:.2f})<extra>样本与垂足</extra>'},
   {type:'scatter',mode:'lines',x:[q[0],r[0],u[0]],y:[q[1],r[1],u[1]],name:'直角标记',line:{color:'#70675e'},hoverinfo:'skip'}],
   '从样本沿法向量投影到超平面',{
    xaxis:{title:'x₁',range:[-1,2],constrain:'domain'},yaxis:{title:'x₂',range:[-1,2],scaleanchor:'x',constrain:'domain'},
    annotations:[
     {x:1.16,y:1.63,ax:.56,ay:.83,axref:'x',ayref:'y',xref:'x',yref:'y',text:'',showarrow:true,arrowhead:3,arrowwidth:3,arrowcolor:'#137d80'},
     label(1,1,'样本 x=(1,1)',100,-12),
     label(.76,.68,'垂足 x⊥=(0.76,0.68)',-120,52),
     label(.88,.84,'几何距离 d=0.4',92,72),
     {x:1.12,y:1.82,xref:'x',yref:'y',text:'单位法向量 n=w/‖w‖=(0.6,0.8)',showarrow:false,bgcolor:'rgba(255,253,249,.96)',borderpad:5,font:{size:14,color:'#137d80'}}
    ]});
  cards(el,[['f(x)',fmt(2*s)],['‖w‖',fmt(5*s)],['距离 |f|/‖w‖','0.400'],['垂足','(0.76, 0.68)']],
   '红线段连接样本与垂足，长度为0.4；绿色箭头平移到垂线左侧单独绘出，方向为单位法向量，长度为1；平移不改变向量的方向和长度。整体缩放不改变这两段几何关系。');
 };
 scale.addEventListener('change',update);reset(el,[scale],[1],update);update();
}
function modelTable(el,X,y,m){
 let table=el.querySelector('.lab-table');if(!table){table=document.createElement('table');table.className='lab-table';el.append(table);}
 table.replaceChildren();const head=document.createElement('thead'),header=document.createElement('tr');
 for(const v of ['样本','y','α','yf','ξ']){const t=document.createElement('th');t.scope='col';t.textContent=v;header.append(t);}head.append(header);table.append(head);
 const body=document.createElement('tbody');y.forEach((v,i)=>{const tr=document.createElement('tr');for(const value of [i,v,fmt(m.alpha[i]),fmt(m.margins[i]),fmt(m.slack[i])]){const td=document.createElement('td');td.textContent=value;tr.append(td);}body.append(tr);});table.append(body);
}
function cEffect(el){
 const d=D.c_effect,C=choice(el,'C','违例惩罚 C',d.models.map(m=>m.C),0);
 const update=()=>{
  const m=d.models[C.value],norm=Math.hypot(...m.w),hinge=m.slack.reduce((a,b)=>a+b,0);
  const traces=[...points(d.points,d.labels),...boundary(m.w,m.b),
   {type:'scatter',mode:'markers',x:m.sv.map(i=>d.points[i][0]),y:m.sv.map(i=>d.points[i][1]),name:'支持向量',marker:{symbol:'circle-open',size:24,color:'#17324d'}},
   {type:'scatter',mode:'markers',x:[-1.5],y:[1.5],name:'偏离主群的正类：样本6',marker:{symbol:'diamond-open',size:28,color:'#ae3953',line:{width:2}}}];
  draw(el,traces,'固定七个样本，仅改变 C');
  cards(el,[['C',m.C],['训练误分类数',m.errors+' / 7'],['总 hinge 损失 Σξ',fmt(hinge)],['范数项 ½‖w‖²',fmt(.5*norm**2)],['违例代价 CΣξ',fmt(m.C*hinge)],['参考带宽 2/‖w‖',fmt(2/norm)]],
   `真实离散预计算，无标准化。样本6的 yf=${fmt(m.margins[6])}，ξ=${fmt(m.slack[6])}；当前边界为 ${fmt(m.w[0])}x₁ + ${fmt(m.w[1])}x₂ + ${fmt(m.b)} = 0。C增加后模型降低总违例，但对应目标的数值不可跨C直接排名。`);
  modelTable(el,d.points,d.labels,m);el.dataset.currentC=m.C;
 };
 C.addEventListener('change',update);reset(el,[C],[0],update);update();
}
function scenario(el,soft){const stage=choice(el,'scenario','样本状态',D.scenarios.map(s=>s.label),soft?2:0),C=soft?choice(el,'C','C',[.1,1,10,100],1):null;
 const update=()=>{const d=D.scenarios[stage.value],m=soft?d.soft[C.value]:null,w=m?m.w:d.w||[1,0],b=m?m.b:d.b||0,traces=[...points(d.points,D.labels)];if(!d.feasible&&!soft)traces.unshift({type:'scatter',mode:'lines',x:[-2,-2,-1,-2],y:[-1,1,0,-1],fill:'toself',fillcolor:'rgba(36,94,145,.09)',name:'负类凸包',line:{color:'#245e91',dash:'dot'}});
 traces.push(...boundary(w,b,soft||d.feasible));if(m){const ids=m.sv;traces.push({type:'scatter',mode:'markers',x:ids.map(i=>d.points[i][0]),y:ids.map(i=>d.points[i][1]),name:'支持向量',marker:{symbol:'circle-open',size:23,color:'#17324d'}});}
 draw(el,traces,soft?'同一六点数据上的软间隔':d.feasible?'硬间隔最优解':'硬间隔不可行：x₁=0仅作参考');
 const norm=Math.hypot(...w);cards(el,soft?[['C',m.C],['误分类数',m.errors],['总松弛 Σξ',fmt(m.slack.reduce((a,b)=>a+b,0))],['参考带宽 2/‖w‖',norm>1e-10?fmt(2/norm):'无定义'],['原始目标 P',fmt(m.primal)],['对偶目标 D',fmt(m.dual)]]:[['硬间隔可行',d.feasible?'是':'否'],['最优 ‖w‖',d.feasible?fmt(norm):'不存在'],['最小几何间隔',d.feasible?fmt(1/norm):'无硬间隔解'],['最优参数',d.feasible?`w=(${w.join(', ')}), b=${b}`:'参考线不代表最优解']],soft?'真实预计算线性C-SVM，无标准化；各点的α、yf与ξ可在下表核对。参考带宽不等于软间隔数据的最小几何间隔两倍。':d.feasible?'解析最优解已由最近样本的约束给出下界并验证。':'正类样本3位于负类凸包，仿射函数不能同时正确分开它们。');
 if(m)modelTable(el,d.points,D.labels,m);
 el.dataset.currentScenario=stage.value;if(m)el.dataset.currentC=m.C;
 };stage.addEventListener('change',update);if(C)C.addEventListener('change',update);reset(el,C?[stage,C]:[stage],C?[2,1]:[0],update);update();}
function mapping(el){const view=choice(el,'view','坐标视图',['输入空间二维','特征空间三维'],0);const X=[],y=[];for(const [r,label] of [[1,-1],[2,1]])for(let i=0;i<16;i++){const a=i*Math.PI/8;X.push([r*Math.cos(a),r*Math.sin(a)]);y.push(label);}const update=()=>{if(view.value==='0'){const a=Array.from({length:101},(_,i)=>i*Math.PI/50),r=Math.sqrt(2.5);draw(el,[...points(X,y).map(t=>({...t,mode:'markers'})),{type:'scatter',mode:'lines',x:a.map(t=>r*Math.cos(t)),y:a.map(t=>r*Math.sin(t)),name:'映回输入空间的圆',line:{color:'#137d80',width:3}}],'输入空间：圆环需要弯曲边界');}else{const tr=[-1,1].map((k,index)=>{const ids=y.map((v,i)=>v===k?i:-1).filter(i=>i>=0);return{type:'scatter3d',mode:'markers',x:ids.map(i=>X[i][0]),y:ids.map(i=>X[i][1]),z:ids.map(i=>dot(X[i],X[i])),name:k===1?'正类 +1':'负类 −1',marker:{size:6,color:colors[index]}};});tr.push({type:'surface',x:[-2.2,2.2],y:[-2.2,2.2],z:[[2.5,2.5],[2.5,2.5]],colorscale:[[0,'#137d80'],[1,'#137d80']],opacity:.35,showscale:false});draw(el,tr,'φ(x)=(x₁,x₂,x₁²+x₂²)',{scene:{xaxis:{title:'x₁'},yaxis:{title:'x₂'},zaxis:{title:'r²'},camera:{eye:{x:1.5,y:1.5,z:1}}}});}cards(el,[['内圈新坐标 r²','1'],['外圈新坐标 r²','4'],['教学平面','z=2.5']],'同一批理想圆环点；平面是手动构造，不代表已训练最优解。有限三维映射不等于RBF的无限维空间。');el.dataset.view=view.value;};view.addEventListener('change',update);reset(el,[view],[0],update);update();}
function loss(el){const m=range(el,'margin','函数间隔 m',-3,4,.05,.5);const X=Array.from({length:141},(_,i)=>-3+i*.05);const update=()=>{const v=+m.value;draw(el,[{type:'scatter',mode:'lines',x:[-3,0],y:[1,1],name:'0–1 (m≤0)',line:{color:'#60636e',width:2}},{type:'scatter',mode:'lines',x:[0,4],y:[0,0],name:'0–1 (m>0)',line:{color:'#60636e',width:2},showlegend:false},{type:'scatter',mode:'markers',x:[0,0],y:[1,0],marker:{size:10,color:'#60636e',symbol:['circle','circle-open']},showlegend:false,hoverinfo:'skip'},{type:'scatter',mode:'lines',x:X,y:X.map(x=>Math.max(0,1-x)),name:'hinge',line:{color:'#245e91',width:3}},{type:'scatter',mode:'lines',x:X,y:X.map(x=>Math.log1p(Math.exp(-x))),name:'logistic',line:{color:'#d17b26',width:3}}],'分段、折角与光滑损失',{height:480,xaxis:{title:'函数间隔 m=yf(x)',range:[-3,4]},yaxis:{title:'损失',range:[-.2,4.3]},shapes:[{type:'line',x0:v,x1:v,y0:0,y1:4,xref:'x',yref:'y',line:{color:'#ae3953',dash:'dot'}}]});cards(el,[['0–1',v<=0?1:0],['hinge',fmt(Math.max(0,1-v))],['logistic',fmt(Math.log1p(Math.exp(-v)))]],'0–1在0处不连续，端点用实心和空心表示。');};
 // Keep explanation in the metric panel.
 const wrapped=()=>{update();const n=el.querySelector('.stat-note');n.textContent='0–1在0处不连续：实心包含，空心不包含；hinge在1处连续但不可微。';};m.addEventListener('input',wrapped);reset(el,[m],[.5],wrapped);wrapped();}
function init(){if(!D||!window.Plotly)return;document.querySelectorAll('[data-teaching]').forEach(el=>{if(el.dataset.initialized)return;el.dataset.initialized='true';const type=el.dataset.teaching;if(type==='geometry')geometry(el);else if(type==='projection')projection(el);else if(type==='c-effect')cEffect(el);else if(type==='hard'||type==='soft')scenario(el,type==='soft');else if(type==='mapping')mapping(el);else if(type==='loss')loss(el);});}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
