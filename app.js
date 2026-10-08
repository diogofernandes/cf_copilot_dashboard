
'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = value => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(value);
let data, selected=null, loaded=false;
function status(text){$('status').textContent=text;}
function showTab(name){
 ['demo','about'].forEach(id=>{const active=id===name;$(id).hidden=!active;$(id+'-tab').setAttribute('aria-selected',active);$(id+'-tab').tabIndex=active?0:-1;});
}
['demo','about'].forEach(name=>{
 $(name+'-tab').onclick=()=>showTab(name);
 $(name+'-tab').onkeydown=e=>{if(['ArrowRight','ArrowLeft','Home','End'].includes(e.key)){e.preventDefault();const next=e.key==='Home'?'demo':e.key==='End'?'about':name==='demo'?'about':'demo';showTab(next);$(next+'-tab').focus();}};
});
function progress(step){document.querySelectorAll('.progress span').forEach((el,i)=>el.classList.toggle('active',i<step));}
function table(headers,rows){return '<div class="table-wrap"><table><thead><tr>'+headers.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table></div>';}
function metric(label,value){return '<div class="metric"><span>'+esc(label)+'</span><strong>'+esc(value)+'</strong></div>';}
function reset(){
 loaded=false;selected=null;
 ['invoices','forecast-result','ranking-result','draft-result'].forEach(id=>{$(id).hidden=true;$(id).innerHTML='';});
 ['forecast','rank','draft'].forEach(id=>$(id).disabled=true);progress(0);status('Demo reset. Load the sample to begin.');
}
function load(){
 reset();loaded=true;$('forecast').disabled=false;
 const total=data.invoices.reduce((sum,row)=>sum+Number(row.total_open_amount),0);
 $('invoices').innerHTML='<div class="metrics">'+metric('Loaded invoices',data.invoices.length)+metric('Outstanding sample value',money(total))+metric('Reference date',data.reference_date)+'</div>'+
 table(['Invoice','Customer','Amount (USD)','Due date'],data.invoices.map(r=>'<tr><td>'+esc(r.doc_id)+'</td><td>'+esc(r.name_customer)+'</td><td>'+money(r.total_open_amount)+'</td><td>'+esc(r.due_in_date)+'</td></tr>'));
 $('invoices').hidden=false;progress(1);status('Loaded 24 sample invoices. Generate the forecast to continue.');
}
function forecast(){
 if(!loaded)return;
 selected=null;$('ranking-result').hidden=true;$('ranking-result').innerHTML='';$('draft-result').hidden=true;$('draft-result').innerHTML='';$('draft').disabled=true;
 const weeks=data.forecast.filter(r=>r.week_bucket<=6), tail=data.forecast.find(r=>r.week_bucket===7);
 const sum=weeks.reduce((v,r)=>v+r.forecast_cash,0), max=Math.max(...weeks.map(r=>r.forecast_cash),1);
 let cumulative=0;const points=[];
 const bars=weeks.map((r,i)=>{const h=r.forecast_cash/max*190; cumulative+=r.forecast_cash;points.push((90+i*112)+','+(250-cumulative/Math.max(sum,1)*210));return '<rect x="'+(60+i*112)+'" y="'+(250-h)+'" width="60" height="'+h+'" fill="#00d4aa" rx="4"/><text x="'+(90+i*112)+'" y="278" text-anchor="middle">Week '+r.week_bucket+'</text>';}).join('');
 const svg='<div class="chart"><h3>Weekly expected cash & cumulative receipts</h3><svg viewBox="0 0 760 300" role="img" aria-label="Six-week cash-flow forecast with cumulative receipt line"><line x1="40" y1="250" x2="730" y2="250" stroke="#35506b"/>'+bars+'<polyline points="'+points.join(' ')+'" fill="none" stroke="#65a9ff" stroke-width="3"/><text x="40" y="20">Bars: weekly cash · Blue line: cumulative (separate scale)</text></svg></div>';
 $('forecast-result').innerHTML='<div class="metrics">'+metric('Expected within 42 days',money(sum))+metric('Average weekly inflow',money(sum/6))+metric('Expected after 42 days',money(tail.forecast_cash))+'</div>'+svg+
 table(['Payment interval','Expected cash (USD)'],data.forecast.map(r=>'<tr><td>'+esc(r.week_bucket===7?'43+ days':'Week '+r.week_bucket)+'</td><td>'+money(r.forecast_cash)+'</td></tr>'))+
 '<p class="note">The 43+ day tail is open ended. These are expected receipts, not guaranteed payments.</p><button class="secondary" id="export-forecast">Download forecast CSV</button>';
 $('forecast-result').hidden=false;$('rank').disabled=false;progress(2);status('Forecast ready. Run risk predictions to explore collections priorities.');
 $('export-forecast').onclick=()=>download('cashflow-forecast.csv','payment_interval,expected_cash_usd\n'+data.forecast.map(r=>(r.week_bucket===7?'43+ days':'Week '+r.week_bucket)+','+r.forecast_cash).join('\n'));
}
function download(name,text){const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function rank(){
 if(!loaded)return;
 const rows=data.rankings.map(r=>'<tr data-invoice="'+esc(r.doc_id)+'"><td>'+r.collections_rank+'</td><td>'+esc(r.doc_id)+'</td><td>'+esc(r.name_customer)+'</td><td>'+money(r.total_open_amount)+'</td><td><span class="pill '+esc(r.risk_category.toLowerCase())+'">'+esc(r.risk_category)+'</span></td><td>'+(r.risk_score*100).toFixed(1)+'%</td></tr>');
 $('ranking-result').innerHTML=table(['Priority','Invoice','Customer','Amount (USD)','Timing risk','P(after 28 days)'],rows)+'<label for="invoice-select">Select an invoice</label><select id="invoice-select"><option value="">Choose a customer invoice…</option>'+data.rankings.map(r=>'<option value="'+esc(r.doc_id)+'">'+esc(r.name_customer)+' · '+esc(r.doc_id)+' · '+money(r.total_open_amount)+'</option>').join('')+'</select><div id="detail"></div>';
 $('ranking-result').hidden=false;selected=null;$('draft').disabled=true;$('draft-result').hidden=true;
 $('invoice-select').onchange=e=>selectInvoice(e.target.value);
 document.querySelectorAll('[data-invoice]').forEach(row=>row.onclick=()=>{$('invoice-select').value=row.dataset.invoice;selectInvoice(row.dataset.invoice);});
 progress(3);status('Ten collection priorities ready. Select an invoice using the table or dropdown.');
}
function selectInvoice(id){
 selected=data.rankings.find(row=>row.doc_id===id)||null;
 $('draft-result').hidden=true;$('draft-result').innerHTML='';$('draft').disabled=!selected;
 document.querySelectorAll('[data-invoice]').forEach(row=>row.classList.toggle('selected',row.dataset.invoice===id));
 if(!selected){$('detail').innerHTML='';return;}
 const r=selected,p=data.predictions.find(row=>row.doc_id===id);
 $('detail').innerHTML='<div class="invoice-panel"><h3>'+esc(r.name_customer)+' · '+esc(id)+'</h3><div class="metrics">'+metric('Open amount',money(r.total_open_amount))+metric('Days past due',r.days_past_due)+metric('Payment after 28 days',(r.risk_score*100).toFixed(1)+'%')+'</div><p>Due date: '+esc(r.due_in_date.slice(0,10))+' · Collection priority score: '+Number(r.priority_score).toFixed(0)+'</p>'+
 table(['Payment interval','Model probability'],Object.entries(p.bucket_probabilities).map(([key,value],i)=>'<tr><td>'+esc(i===6?'43+ days':(i*7+1)+'–'+((i+1)*7)+' days')+'</td><td>'+(value*100).toFixed(1)+'%</td></tr>'))+
 '<p class="note">Timing risk is P(payment after 28 days), not default risk. Ranking combines amount, timing risk and an overdue multiplier.</p></div>';
 status('Selected '+id+'. Generate its collection draft.');
}
function draft(){
 if(!selected)return;
 const result=data.drafts[selected.doc_id];
 $('draft-result').innerHTML='<h3>Draft for '+esc(selected.doc_id)+'</h3><p class="note">Provider: local_rules · Recorded sample draft · Review before use · No email is sent</p><div class="email-box"><strong>Subject: '+esc(result.subject)+'</strong>\n\n'+esc(result.email_body)+'</div><p>'+esc(result.reasoning)+'</p><button class="secondary" id="copy-draft">Copy draft</button>';
 $('draft-result').hidden=false;progress(4);status('Draft ready for '+selected.doc_id+'. Select another invoice to explore its draft.');
 $('copy-draft').onclick=async()=>{try{await navigator.clipboard.writeText('Subject: '+result.subject+'\n\n'+result.email_body);status('Draft copied.');}catch{status('Select the draft text to copy it manually.');}};
}
async function init(){
 try{
 const responses=await Promise.all(['demo-data.json','landing.html','about.html'].map(path=>fetch(path)));
 if(responses.some(r=>!r.ok))throw Error('Unable to load showcase assets.');
 data=await responses[0].json();const landing=await responses[1].text();$('about').innerHTML=await responses[2].text();
 const parsed=document.createElement('div');parsed.innerHTML=landing;const nav=parsed.querySelector('.nav');$('nav').append(nav);parsed.querySelectorAll('style').forEach(e=>e.remove());$('landing').innerHTML=parsed.innerHTML;
 $('nav').querySelectorAll('a').forEach(link=>link.onclick=()=>showTab('demo'));
 $('load').onclick=load;$('reset').onclick=reset;$('forecast').onclick=forecast;$('rank').onclick=rank;$('draft').onclick=draft;progress(0);status('Ready. Load sample invoices to begin.');
 }catch(error){$('status').classList.add('error');status('The demo could not load. Please refresh the page.');console.error(error);}
}
init();
