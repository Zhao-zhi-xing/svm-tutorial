/* 浏览器只计算几何和预测分数；训练由 Python/R 在构建时完成。 */
(() => {
  'use strict';
  const palette=['#245e91','#d17b26','#137d80'];
  const config={responsive:true,displaylogo:false,scrollZoom:false,toImageButtonOptions:{format:'png',scale:2}};
  const base={font:{family:'Segoe UI, Microsoft YaHei, sans-serif',size:13,color:'#17324d'},
    margin:{l:65,r:35,t:60,b:115},paper_bgcolor:'#fff',plot_bgcolor:'#fafcfe',
    xaxis:{title:'x₁',range:[-3,3],constrain:'domain',zeroline:false},yaxis:{title:'x₂',range:[-3,3],scaleanchor:'x',constrain:'domain',zeroline:false},
    legend:{orientation:'h',y:-.12,font:{size:14}},height:860};
  const layout=extra=>({...base,...extra});
  const round=(x,n=3)=>Number(x).toFixed(n);
  const controls=el=>el.querySelector('.lab-controls');
  const plot=el=>el.querySelector('.lab-plot');
  const stats=el=>el.querySelector('.lab-stats');
  const dot=(w,x)=>w[0]*x[0]+w[1]*x[1];
  const argmax=a=>a.indexOf(Math.max(...a));
  function renderStats(el,entries,note) {
    const panel=stats(el);panel.replaceChildren();
    entries.forEach(([label,value,wide])=>{
      const card=document.createElement('div');card.className='stat-card'+(wide?' stat-wide':'');
      const title=document.createElement('span');title.className='stat-label';title.textContent=label;
      const number=document.createElement('strong');number.className='stat-value';number.textContent=value;
      card.append(title,number);panel.append(card);
    });
    const explanation=document.createElement('p');explanation.className='stat-note';explanation.textContent=note;panel.append(explanation);
  }
  // 从已训练模型的决策网格插值等值线，分开画边界与两侧间隔线。
  // 相邻网格线段连接为完整路径，避免每个单元重新开始虚线节奏。
  function levelTrace(axis,z,level,name,color,dash='solid',width=2) {
    const xs=[],ys=[],segments=[];
    for(let j=0;j<axis.length-1;j++)for(let i=0;i<axis.length-1;i++){
      const p=[[axis[i],axis[j]],[axis[i+1],axis[j]],[axis[i+1],axis[j+1]],[axis[i],axis[j+1]]];
      const v=[z[j][i],z[j][i+1],z[j+1][i+1],z[j+1][i]],cross=[];
      for(let e=0;e<4;e++){
        const k=(e+1)%4;
        if((v[e]>level)===(v[k]>level))continue;
        const t=(level-v[e])/(v[k]-v[e]);cross.push([p[e][0]+t*(p[k][0]-p[e][0]),p[e][1]+t*(p[k][1]-p[e][1])]);
      }
      const pairs=cross.length===4?((v.reduce((a,b)=>a+b,0)/4>level)===(v[0]>level)?[[0,1],[2,3]]:[[0,3],[1,2]]):cross.length===2?[[0,1]]:[];
      pairs.forEach(([a,b])=>segments.push([cross[a],cross[b]]));
    }
    const key=p=>p.map(v=>v.toFixed(9)).join(',');
    const adjacency=new Map(),unused=new Set(segments.map((_,i)=>i));
    segments.forEach((segment,i)=>segment.forEach(p=>{const k=key(p);if(!adjacency.has(k))adjacency.set(k,[]);adjacency.get(k).push(i);}));
    while(unused.size){
      const index=unused.values().next().value;unused.delete(index);const path=[...segments[index]];
      for(const front of [false,true])while(true){
        const endpoint=front?path[0]:path[path.length-1];
        const next=adjacency.get(key(endpoint)).find(i=>unused.has(i));if(next===undefined)break;
        unused.delete(next);const [a,b]=segments[next],other=key(a)===key(endpoint)?b:a;
        if(front)path.unshift(other);else path.push(other);
      }
      path.forEach(p=>{xs.push(p[0]);ys.push(p[1]);});xs.push(null);ys.push(null);
    }
    return {type:'scatter',mode:'lines',x:xs,y:ys,name,line:{color,dash,width},hovertemplate:name+'<extra></extra>'};
  }

  function selector(el,name,label,values,initial) {
    const wrapper=document.createElement('label'); wrapper.textContent=label+' ';
    const select=document.createElement('select'); select.name=name; select.setAttribute('aria-label',label);
    values.forEach(v=>{const o=document.createElement('option'); o.value=v; o.textContent=v; select.append(o);});
    select.value=initial; wrapper.append(select); controls(el).append(wrapper); return select;
  }
  function slider(el,name,label,min,max,step,value) {
    const wrapper=document.createElement('label'); wrapper.textContent=label+' ';
    const input=document.createElement('input'); Object.assign(input,{type:'range',name,min,max,step,value}); input.setAttribute('aria-label',label);
    const output=document.createElement('output'); output.textContent=value;
    input.addEventListener('input',()=>output.textContent=input.value);
    wrapper.append(input,output); controls(el).append(wrapper); return input;
  }
  function reset(el,fn) {
    const button=document.createElement('button'); button.type='button';button.textContent='重置';button.addEventListener('click',fn); controls(el).append(button);
  }
  function samples(points,labels,split) {
    const traces=[];
    [...new Set(labels)].sort().forEach((k,i)=>{
      const ids=labels.map((y,j)=>y===k?j:-1).filter(j=>j>=0);
      traces.push({type:'scatter',mode:'markers',name:'类别 '+k,x:ids.map(j=>points[j][0]),y:ids.map(j=>points[j][1]),
        customdata:ids.map(j=>[j,split?split[j]:'教学样本']),marker:{size:8,color:palette[i],symbol:ids.map(j=>split&&split[j]==='test'?'diamond-open':'circle')},
        hovertemplate:'样本 %{customdata[0]}<br>x₁=%{x:.2f}, x₂=%{y:.2f}<br>%{customdata[1]}<extra>%{fullData.name}</extra>'});
    });return traces;
  }
  function line(w,b,level,name,color='#17324d',dash='solid') {
    // 与显示矩形的四条边相交，避免竖直超平面时除零。
    const intersections=[];
    if(Math.abs(w[1])>1e-10) for(const x of [-3,3]) {const y=(level-b-w[0]*x)/w[1];if(Math.abs(y)<=3.001)intersections.push([x,y]);}
    if(Math.abs(w[0])>1e-10) for(const y of [-3,3]) {const x=(level-b-w[1]*y)/w[0];if(Math.abs(x)<=3.001)intersections.push([x,y]);}
    return {type:'scatter',mode:'lines',name,x:intersections.slice(0,2).map(p=>p[0]),y:intersections.slice(0,2).map(p=>p[1]),line:{color,width:2,dash},hoverinfo:'name'};
  }
  function geometry(el) {
    const payload=window.SVM_MODELS.linear;
    const angle=slider(el,'angle','法向量角度 θ',0,180,1,45);
    const bias=slider(el,'bias','截距 b',-2,2,.05,0);
    const point=selector(el,'point','观察样本',payload.points.map((_,i)=>i),0);
    const update=()=>{
      const rad=Number(angle.value)*Math.PI/180,w=[Math.cos(rad),Math.sin(rad)],b=Number(bias.value);
      const p=payload.points[Number(point.value)]; const score=dot(w,p)+b;
      const foot=[p[0]-score*w[0],p[1]-score*w[1]];
      const axis=Array.from({length:31},(_,i)=>-3+i*.2);
      const z=axis.map(y=>axis.map(x=>dot(w,[x,y])+b));
      const background={type:'contour',x:axis,y:axis,z,contours:{coloring:'heatmap',showlines:false},line:{width:0},colorscale:[[0,'#e9f1fa'],[1,'#fff2e3']],opacity:.55,showscale:false,hoverinfo:'skip',showlegend:false};
      const traces=[background,...samples(payload.points,payload.labels),{...line(w,b,0,'决策边界 f(x)=0','#17324d'),line:{color:'#17324d',width:3.5}},line(w,b,1,'正侧间隔线 f(x)=+1','#137d80','dash'),line(w,b,-1,'负侧间隔线 f(x)=−1','#b96a15','dash'),
       {type:'scatter',mode:'lines+markers',name:'所选样本的垂线',x:[p[0],foot[0]],y:[p[1],foot[1]],line:{color:'#ae3953',width:3},marker:{size:10},hoverinfo:'skip'}];
      Plotly.react(plot(el),traces,layout({title:'改变法向量，观察带符号距离'}),config);
      const y=payload.labels[Number(point.value)]===1?1:-1;
      const mistakes=payload.labels.reduce((n,label,i)=>n+((dot(w,payload.points[i])+b>=0?1:0)!==label),0);
      const inside=payload.labels.reduce((n,label,i)=>n+(((label===1?1:-1)*(dot(w,payload.points[i])+b))<1),0);
      renderStats(el,[['正确分类',`${payload.points.length-mistakes} / ${payload.points.length}`],['间隔内样本（yf < 1）',inside],['参考间隔宽度 2/‖w‖','2.00'],['‖w‖','1.00',true],['所选样本分数 f(x)',round(score)],['带符号几何间隔 yf/‖w‖',round(y*score)],['样本到边界的距离',round(Math.abs(score))]],'手动几何演示，未训练模型。深蓝实线是决策边界，绿/橙虚线是 f=+1 / −1，红色垂线表示距离。‖w‖固定为1；这里的参考间隔宽度不是训练得到的最大间隔。');
    };
    [angle,bias,point].forEach(c=>c.addEventListener('input',update));
    reset(el,()=>{angle.value=45;bias.value=0;point.value=0;angle.dispatchEvent(new Event('input'));bias.dispatchEvent(new Event('input'));}); update();
  }
  function grid(el,kind) {
    const data=window.SVM_MODELS[kind],best=data.models[data.best_index];
    const Cs=[...new Set(data.models.map(m=>m.C))],Gs=[...new Set(data.models.map(m=>m.gamma))];
    const C=selector(el,'C','C',Cs,best.C);
    const gamma=kind==='rbf'?selector(el,'gamma','γ',Gs,best.gamma):null;
    const update=()=>{
      const m=data.models.find(m=>m.C===Number(C.value)&&(!gamma||m.gamma===Number(gamma.value)));
      const contours={type:'contour',x:data.axis,y:data.axis,z:m.decision,colorscale:[[0,'#dceaf8'],[.5,'#ffffff'],[1,'#f9e8d4']],zmin:-3,zmax:3,opacity:.7,contours:{coloring:'heatmap',showlines:false},line:{width:0},showscale:false,hovertemplate:'x₁=%{x:.2f}<br>x₂=%{y:.2f}<br>f(x)=%{z:.3f}<extra></extra>'};
      const boundary=levelTrace(data.axis,m.decision,0,'决策边界 f(x)=0','#17324d','solid',3.5);
      const upper=levelTrace(data.axis,m.decision,1,'正侧间隔线 f(x)=+1','#137d80','dash',2);
      const lower=levelTrace(data.axis,m.decision,-1,'负侧间隔线 f(x)=−1','#b96a15','dash',2);
      const sv={type:'scatter',mode:'markers',name:'支持向量（训练集）',x:m.sv.map(p=>p[0]),y:m.sv.map(p=>p[1]),marker:{size:13,symbol:'circle-open',color:'#17324d',line:{width:2}},hoverinfo:'name'};
      Plotly.react(plot(el),[contours,boundary,upper,lower,...samples(data.points,data.labels,data.split),sv],layout({title:kind==='linear'?'软间隔线性 SVM':'RBF SVM：局部相似度与边界'}),config);
      const cards=[['C',m.C],...(gamma?[['γ',m.gamma]]:[['原始坐标间隔宽度',round(m.input_margin_width,2)]]),['支持向量',m.sv.length],['训练误分类',m.train_errors],['五折验证 macro-F1',round(m.cv_macro_f1)],['测试 accuracy',round(m.test_accuracy)]];
      renderStats(el,cards,'预计算模型，切换参数不会实时训练。深蓝实线 f=0；绿/橙虚线 f=+1 / −1。圆点为训练样本，空心菱形为测试样本。默认参数仅按训练集CV选择。'+(gamma?'核图中的间隔线不是输入空间的等距离线。':'显示宽度按原始坐标中的法向量计算；标准化空间的范数不同。'));
      el.dataset.currentC=m.C;el.dataset.currentGamma=m.gamma;el.dataset.currentSv=m.sv.length;
    };
    C.addEventListener('change',update);if(gamma)gamma.addEventListener('change',update);
    reset(el,()=>{C.value=best.C;if(gamma)gamma.value=best.gamma;update();});update();
  }
  function mapping(el) {
    const d=window.SVM_MODELS.mapping;
    const traces=[];
    for(const k of [0,1]){
      const ids=d.labels.map((v,i)=>v===k?i:-1).filter(i=>i>=0);
      traces.push({type:'scatter3d',mode:'markers',name:'类别 '+k,x:ids.map(i=>d.points[i][0]),y:ids.map(i=>d.points[i][1]),z:ids.map(i=>d.z[i]),marker:{size:5,color:palette[k]},hovertemplate:'x₁=%{x:.2f}<br>x₂=%{y:.2f}<br>x₁²+x₂²=%{z:.2f}<extra></extra>'});
    }
    traces.push({type:'surface',x:[-1.2,1.2],y:[-1.2,1.2],z:[[.55,.55],[.55,.55]],opacity:.35,showscale:false,colorscale:[[0,'#137d80'],[1,'#137d80']],name:'教学分隔平面',hoverinfo:'skip'});
    const L=layout({title:'φ(x)=(x₁,x₂,x₁²+x₂²)',scene:{xaxis:{title:'x₁'},yaxis:{title:'x₂'},zaxis:{title:'x₁²+x₂²'},camera:{eye:{x:1.5,y:1.5,z:1}}},height:800});
    // Plotly 会在拖动时修改 layout.camera，重置应使用独立的初始值。
    Plotly.newPlot(plot(el),traces,L,config);reset(el,()=>Plotly.relayout(plot(el),{'scene.camera':{eye:{x:1.5,y:1.5,z:1},up:{x:0,y:0,z:1},center:{x:0,y:0,z:0}}}));
    renderStats(el,[['特征维数','3'],['教学分隔平面','z = 0.55'],['原空间边界','x₁² + x₂² = 0.55']],'拖动旋转，工具栏缩放。绿色平面为手动设置的教学平面；这个有限维映射不是 RBF 的完整特征空间。');
  }
  function multiclass(el) {
    const d=window.SVM_MODELS.multiclass;
    const strategy=selector(el,'strategy','规则',['OvR 符号判定','OvR argmax','OvO 投票'],'OvR 符号判定');
    const step=selector(el,'step','显示分类器',['全部',0,1,2],'全部');
    const px=slider(el,'x1','样本 x₁',-2.8,2.8,.1,0),py=slider(el,'x2','样本 x₂',-2.8,2.8,.1,0);
    function predict(x,mode){
      const scores=d.ovr.map(m=>dot(m.w,x)+m.b);
      const pairs=d.pairs.map(m=>dot(m.w,x)+m.b);const votes=[0,0,0];pairs.forEach((s,i)=>votes[s>=0?d.pairs[i].j:d.pairs[i].i]++);
      const positive=scores.map((s,i)=>s>0?i:-1).filter(i=>i>=0);
      let winner;
      if(mode==='OvR 符号判定')winner=positive.length===1?positive[0]:3;
      else if(mode==='OvR argmax')winner=argmax(scores);
      else winner=votes.filter(v=>v===Math.max(...votes)).length===1?argmax(votes):3;
      return {winner,scores,pairs,votes,positive};
    }
    const update=()=>{
      const mode=strategy.value,x=[Number(px.value),Number(py.value)],r=predict(x,mode);
      const axis=Array.from({length:61},(_,i)=>-3+i*.1);
      const z=axis.map(y=>axis.map(x=>predict([x,y],mode).winner));
      const traces=[{type:'heatmap',x:axis,y:axis,z,zmin:0,zmax:3,colorscale:[[0,'#e1ecf7'],[.166,'#e1ecf7'],[.167,'#fbebd6'],[.5,'#fbebd6'],[.501,'#daf0eb'],[.833,'#daf0eb'],[.834,'#e4e4e7'],[1,'#e4e4e7']],showscale:false,hovertemplate:'x₁=%{x:.1f}, x₂=%{y:.1f}<br>区域编码 %{z}（3=模糊/平票）<extra></extra>'},...samples(d.points,d.labels)];
      const models=mode==='OvO 投票'?d.pairs:d.ovr;
      if(mode==='OvR argmax') {
        [[0,1],[0,2],[1,2]].forEach(([i,j],index)=>{if(step.value==='全部'||Number(step.value)===index)traces.push(line([d.ovr[i].w[0]-d.ovr[j].w[0],d.ovr[i].w[1]-d.ovr[j].w[1]],d.ovr[i].b-d.ovr[j].b,0,`f${i}=f${j}`,palette[index],'dash'));});
      }else models.forEach((m,i)=>{if(step.value==='全部'||Number(step.value)===i)traces.push(line(m.w,m.b,0,mode==='OvO 投票'?`${m.i} vs ${m.j}`:`f${i}=0`,palette[i],'dash'));});
      traces.push({type:'scatter',mode:'markers',name:'观察样本',x:[x[0]],y:[x[1]],marker:{symbol:'star',size:18,color:'#ae3953'},hoverinfo:'name'});
      Plotly.react(plot(el),traces,layout({title:mode+'：比较分类规则'}),config);
      const verdict=r.winner===3?'模糊区域 / 平票':`类别 ${r.winner}`;
      renderStats(el,[['当前结果',verdict,true],...r.scores.map((s,k)=>[`OvR：类别 ${k} 分数`,round(s)]),...r.votes.map((v,k)=>[`OvO：类别 ${k} 票数`,v]),...r.pairs.map((s,k)=>[`类别对 ${d.pairs[k].i} vs ${d.pairs[k].j} 分数`,round(s)]),['观察样本',`(${round(x[0],1)}, ${round(x[1],1)})`],['OvR 正分数类别',r.positive.length?r.positive.join(', '):'无'],['预测规则',mode]],'OvO正分数投给类别对中较大的编号；灰色表示符号判定或原始投票的歧义。argmax使用同一组OvR分数，不能理解为概率比较。');
      el.dataset.currentStrategy=mode;el.dataset.currentWinner=r.winner;
    };
    [strategy,step].forEach(c=>c.addEventListener('change',update));[px,py].forEach(c=>c.addEventListener('input',update));
    reset(el,()=>{strategy.value='OvR 符号判定';step.value='全部';px.value=0;py.value=0;px.dispatchEvent(new Event('input'));py.dispatchEvent(new Event('input'));});update();
    plot(el).on('plotly_click',ev=>{const p=ev.points[0];if(Number.isFinite(p.x)&&Number.isFinite(p.y)){px.value=p.x;py.value=p.y;px.dispatchEvent(new Event('input'));py.dispatchEvent(new Event('input'));}});
  }
  function tuning(el) {
    const d=window.SVM_MODELS.rbf,Cs=[...new Set(d.models.map(m=>m.C))],Gs=[...new Set(d.models.map(m=>m.gamma))];
    const z=Cs.map(C=>Gs.map(g=>d.models.find(m=>m.C===C&&m.gamma===g).cv_macro_f1));
    Plotly.newPlot(plot(el),[{type:'heatmap',z,x:Gs.map(String),y:Cs.map(String),colorscale:'Viridis',hovertemplate:'C=%{y}, γ=%{x}<br>CV macro-F1=%{z:.4f}<extra></extra>'}],layout({title:'训练集五折验证网格',xaxis:{title:'γ（离散值）',type:'category'},yaxis:{title:'C（离散值）',type:'category',scaleanchor:undefined}}),config);
    const best=d.models[d.best_index];renderStats(el,[['最佳 C',best.C],['最佳 γ',best.gamma],['最佳 CV macro-F1',round(best.cv_macro_f1)]],'颜色来自训练集五折验证，测试集没有参与选参。');
  }
  function initializeFigures(){
    document.querySelectorAll('[data-plotly-source]').forEach(el=>{
      if(el.dataset.initialized)return;
      const source=document.getElementById(el.dataset.plotlySource);if(!source)return;
      const f=JSON.parse(source.textContent);el.dataset.initialized='true';
      f.layout={...f.layout,font:base.font,margin:{l:70,r:40,t:75,b:115},height:f.layout.yaxis?.scaleanchor?860:560,autosize:true};
      Plotly.newPlot(el,f.data,f.layout,config);
    });
  }
  function init(){
    if(!window.Plotly||!window.SVM_MODELS)return;
    document.querySelectorAll('[data-svm-lab]').forEach(el=>{
      if(el.dataset.initialized)return;el.dataset.initialized='true';
      const type=el.dataset.svmLab;
      if(type==='geometry')geometry(el);else if(type==='linear'||type==='rbf')grid(el,type);
      else if(type==='mapping')mapping(el);else if(type==='multiclass')multiclass(el);else if(type==='tuning')tuning(el);
    });initializeFigures();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
  window.addEventListener('resize',()=>document.querySelectorAll('.js-plotly-plot').forEach(el=>{if(el.offsetWidth)Plotly.Plots.resize(el);}));
})();
