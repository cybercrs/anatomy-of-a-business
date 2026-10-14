/** Original teaching screens rendered with native HTML controls. */
import {DATA} from './content.js';
import {Lesson,clean,decodeState,encodeState,shuffled} from './engine.js';

const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node;};
let lesson,orders=new Map(),reviewStatement='Income Statement';
function order(key,options) {
  const existing=orders.get(key);
  if(!existing||existing.length!==options.length||existing.some(value=>!options.includes(value)))orders.set(key,shuffled(options));
  return orders.get(key);
}
function save() {
  document.documentElement.dataset.saving='true';
  try {
    const url=new URL(location.href);url.searchParams.set('progress',encodeState(lesson.state));
    url.searchParams.set('view',String(lesson.view));history.replaceState(null,'',url);$('save-error').hidden=true;
  } catch {
    $('save-error').textContent='Your address could not be updated. Keep this tab open; refreshing may not preserve the latest input.';
    $('save-error').hidden=false;
  } finally {document.documentElement.dataset.saving='false';}
}
function defaults() {
  if(lesson.reviewing)return;
  const state=lesson.state;
  if(state.page===0&&state.organization_answer===null)state.organization_answer=order('organization',['Sole proprietorship','Partnership','Corporation'])[0];
  if(state.page===1)for(const event of lesson.config.events)state.activity_selections[event.event_id]??='Not sure yet';
  if(state.page===2) {
    state.statement_selection??='Income Statement';
    const name=state.statement_selection;
    state.statement_answers[name]??=order('statement:'+name,lesson.config.questions[name].options)[0];
  }
}
function scrollTop() {window.scrollTo({top:0,left:0,behavior:'instant'});$('lesson').focus({preventScroll:true});}
function update(scroll=false,focus) {render();save();if(scroll)scrollTop();else if(focus)document.getElementById(focus)?.focus({preventScroll:true});}
function valueFor(key) {
  const state=lesson.state,plans={funding_choice:'funding',asset_choice:'asset',operating_choice:'operating',dividend_choice:'dividend'};
  if(plans[key])return state[plans[key]];
  if(key==='organization_answer')return state.organization_answer;
  if(key==='statement_selection')return lesson.reviewing?reviewStatement:state.statement_selection;
  if(key.startsWith('activity_'))return state.activity_selections[key.slice(9)]??'Not sure yet';
  if(key.startsWith('statement_answer_'))return state.statement_answers[statementName()]??null;
  return null;
}
function statementName() {return lesson.reviewing?reviewStatement:lesson.state.statement_selection??'Income Statement';}
function choose(key,value,id) {if(lesson.draft(key,value))update(false,id);}
function inputNode(node) {
  if(node.key==='statement_selection') {
    const list=el('div',undefined,'tab-list');list.setAttribute('role','tablist');list.setAttribute('aria-label',node.label);
    DATA.statements.forEach((name,index)=>{
      const button=el('button',name);button.type='button';button.id='statement-tab-'+index;
      button.setAttribute('role','tab');button.setAttribute('aria-selected',String(valueFor(node.key)===name));
      button.tabIndex=valueFor(node.key)===name?0:-1;
      const select=()=>{if(lesson.reviewing){reviewStatement=name;render();document.getElementById(button.id).focus({preventScroll:true});}
        else choose(node.key,name,button.id);};
      button.addEventListener('click',select);
      button.addEventListener('keydown',event=>{
        const delta=event.key==='ArrowRight'?1:event.key==='ArrowLeft'?-1:0;
        if(delta){event.preventDefault();const next=(index+delta+DATA.statements.length)%DATA.statements.length;document.getElementById('statement-tab-'+next).click();}
        if(event.key==='Home'||event.key==='End'){event.preventDefault();document.getElementById('statement-tab-'+(event.key==='Home'?0:3)).click();}
      });
      list.append(button);
    });
    return list;
  }
  if(lesson.reviewing) {
    const box=el('p',undefined,'readonly-answer');
    box.append(el('strong',node.label),document.createTextNode(clean(valueFor(node.key)??'No response saved.')));return box;
  }
  let options=node.options;
  if(node.key==='organization_answer')options=order('organization',options);
  if(node.key.startsWith('activity_'))options=['Not sure yet',...order(node.key,DATA.activities)];
  if(node.key.startsWith('statement_answer_'))options=order('statement:'+statementName(),lesson.config.questions[statementName()].options);
  if(node.kind==='select') {
    const wrapper=el('div'),label=el('label',node.label,'select-label'),select=el('select');
    label.htmlFor=node.key;select.id=node.key;
    options.forEach(value=>{const option=el('option',clean(value));option.value=value;option.selected=value===valueFor(node.key);select.append(option);});
    select.addEventListener('change',()=>choose(node.key,select.value,node.key));
    wrapper.append(label,select);return wrapper;
  }
  const fieldset=el('fieldset');fieldset.append(el('legend',node.label));
  options.forEach((value,index)=>{
    const label=el('label',undefined,'choice'),input=el('input');input.type='radio';input.name=node.key;
    input.id=node.key+'_'+index;input.value=value;input.checked=value===valueFor(node.key);
    input.addEventListener('change',()=>choose(node.key,value,input.id));
    label.append(input,el('span',clean(value)));fieldset.append(label);
  });
  return fieldset;
}
function escapeHTML(value) {return String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');}
function inline(value) {return escapeHTML(clean(value)).replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');}
function markdown(text) {
  const box=el('div');let list=null;
  for(const line of clean(text).split('\n').map(line=>line.trim()).filter(Boolean)) {
    const heading=/^(#{1,6})\s+(.+)/.exec(line),bullet=/^[-*]\s+(.+)/.exec(line);
    if(bullet){if(!list){list=el('ul');box.append(list);}const item=el('li');item.innerHTML=inline(bullet[1]);list.append(item);}
    else {list=null;const item=el(heading?'h'+heading[1].length:'p');item.innerHTML=inline(heading?heading[2]:line);box.append(item);}
  }
  return box;
}
function action(node) {
  if(lesson.reviewing)return document.createDocumentFragment();
  const button=el('button',node.label,node.label==='Check the organization'?'':'primary');button.type='button';
  if(node.label==='See the financial statements →')button.disabled=!lesson.state.activity_checked;
  if(node.label==='Enter the Decision Desk →')button.disabled=Object.keys(lesson.state.statement_results).length!==4;
  if(node.label==='Complete the activity')button.disabled=!lesson.state.activity_checked||Object.keys(lesson.state.statement_results).length!==4;
  button.addEventListener('click',()=>{
    let changed=false,scroll=false;
    if(node.label==='Check the organization')changed=lesson.checkOrganization();
    else if(node.label==='Launch the business →'){changed=lesson.launch();scroll=true;}
    else if(node.label==='Check the activity map')changed=lesson.checkActivity();
    else if(node.label==='Check this statement')changed=lesson.checkStatement();
    else if(node.label==='Complete the activity')changed=lesson.complete();
    else if(['See the financial statements →','Enter the Decision Desk →'].includes(node.label)){changed=lesson.advance();scroll=true;}
    if(changed)update(scroll);
  });return button;
}
function renderNode(original) {
  let node=original;
  if(lesson.view===1&&node.kind==='details') {
    const event=lesson.config.events.find(event=>node.label.includes(event.title));
    if(event) {
      const answer=lesson.state.activity_answers[event.event_id]??'Not sure yet',correct=answer===event.activity_type;
      node={...node,label:(correct?'✓':'↺')+' '+event.title+' — '+event.activity_type,expanded:!correct,
        children:[...(!correct?[{kind:'write',text:'Your answer: **'+answer+'**'}]:[]),...node.children.filter(child=>!child.text?.startsWith('Your answer:'))]};
    }
  }
  if(node.kind==='radio'||node.kind==='select')return inputNode(node);
  if(node.kind==='button')return action(node);
  if(node.kind==='html') {const template=document.createElement('template');template.innerHTML=node.text;return template.content;}
  if(node.kind==='markdown'||node.kind==='write')return markdown(node.text);
  if(['columns','column','form'].includes(node.kind)) {
    const wrapper=el('div',undefined,node.kind==='columns'?'columns':null);
    if(node.kind==='columns')wrapper.style.setProperty('--columns',node.children.length);
    node.children.forEach(child=>wrapper.append(renderNode(child)));return wrapper;
  }
  if(node.kind==='tabs') {
    const wrapper=el('div'),list=el('div',undefined,'tab-list');list.setAttribute('role','tablist');list.setAttribute('aria-label','User perspective');
    const panels=node.children.map((tab,index)=>{
      const panel=el('section');panel.id='perspective-panel-'+index;panel.setAttribute('role','tabpanel');
      panel.setAttribute('aria-labelledby','perspective-tab-'+index);panel.hidden=index!==0;
      tab.children.forEach(child=>panel.append(renderNode(child)));return panel;
    });
    node.children.forEach((tab,index)=>{
      const button=el('button',tab.label);button.type='button';button.id='perspective-tab-'+index;button.setAttribute('role','tab');
      button.setAttribute('aria-controls',panels[index].id);button.setAttribute('aria-selected',String(index===0));button.tabIndex=index===0?0:-1;
      button.addEventListener('click',()=>{[...list.children].forEach((item,i)=>{item.setAttribute('aria-selected',String(i===index));item.tabIndex=i===index?0:-1;panels[i].hidden=i!==index;});});
      button.addEventListener('keydown',event=>{if(['ArrowRight','ArrowLeft','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?2:(index+(event.key==='ArrowRight'?1:2))%3;list.children[next].click();list.children[next].focus();}});
      list.append(button);
    });
    wrapper.append(list,...panels);return wrapper;
  }
  if(node.kind==='details') {
    const details=el('details');details.open=Boolean(node.expanded);details.append(el('summary',node.label));
    node.children.forEach(child=>details.append(renderNode(child)));return details;
  }
  if(node.kind==='progress') {
    const progress=el('progress');progress.max=4;progress.value=Object.keys(lesson.state.statement_results).length;
    progress.setAttribute('aria-label','Statement questions explored');return progress;
  }
  if(node.kind==='metric') {const box=el('div',undefined,'metric');box.append(el('span',node.label),el('strong',node.value));return box;}
  let text=node.text,kind=node.kind;
  if(lesson.view===1&&kind==='warning'&&text.startsWith('You mapped')) {
    const events=lesson.config.events,score=events.filter(event=>lesson.state.activity_answers[event.event_id]===event.activity_type).length;
    if(score===events.length){kind='success';text='Complete map: '+score+' of '+events.length+' activities are correct.';}
    else text='You mapped '+score+' of '+events.length+' correctly. Review the purpose of each event below—the financial statements are still available for exploration.';
  }
  if(lesson.view===2&&kind==='caption'&&text.startsWith('Statements explored:'))text='Statements explored: '+Object.keys(lesson.state.statement_results).length+' of 4';
  const item=el(kind==='header'?'h2':kind==='subheader'?'h3':'p',text,['success','warning','info'].includes(kind)?'notice '+kind:kind==='caption'?'caption':null);
  if(['success','warning','info'].includes(kind))item.setAttribute('role','status');return item;
}
function render() {
  defaults();
  const state=lesson.state,config=lesson.config;
  $('hero').replaceChildren(...DATA.hero.map(renderNode));
  $('page-counter').textContent='Station '+(lesson.view+1)+' of 4';
  $('back').disabled=lesson.view===0;$('forward').disabled=lesson.view>=state.page;$('reset').disabled=lesson.reviewing;
  $('stations').replaceChildren(...DATA.pages.slice(0,state.page+1).map((page,index)=>{const item=el('li',page.split(' · ')[1]);if(index===lesson.view)item.setAttribute('aria-current','step');return item;}));
  const percent=state.decision_completed?100:Object.keys(state.statement_results).length===4?75:state.activity_checked?50:state.launched?25:0;
  $('journey').textContent='Learning journey · '+percent+'%';$('journey-progress').value=percent;
  $('review-message').replaceChildren(...(lesson.reviewing?[el('p','Review only. Return to your current station to continue the activity.','notice info')]:[]));
  let nodes;
  if(lesson.view===0)nodes=config.launch[state.organization_checked?(state.organization_answer==='Corporation'?'correct':'wrong'):'unchecked'];
  if(lesson.view===1)nodes=config.activity[state.activity_checked?'checked':'unchecked'];
  if(lesson.view===2) {
    const name=statementName(),result=state.statement_results[name];
    nodes=config.statements[name][result===undefined?'unchecked':result?'correct':'wrong'];
    nodes=nodes.filter(node=>!(node.kind==='success'&&node.text==='All four statement questions have been explored.'));
    if(Object.keys(state.statement_results).length===4)nodes=nodes.flatMap(node=>node.kind==='caption'&&node.text.startsWith('Statements explored:')
      ?[node,{kind:'success',text:'All four statement questions have been explored.'}]:[node]);
  }
  if(lesson.view===3)nodes=config.decision[state.decision_completed?'complete':'open'];
  $('lesson').replaceChildren(...nodes.map(renderNode));$('lesson').setAttribute('aria-busy','false');
  document.documentElement.dataset.view=String(lesson.view);document.documentElement.dataset.reached=String(state.page);
}
function initialize() {
  const query=new URL(location.href).searchParams,token=query.get('progress'),state=token?decodeState(token):null;
  lesson=new Lesson(state??undefined,query.get('view')??undefined);orders=new Map();reviewStatement='Income Statement';
  render();if(token&&!state)$('lesson').prepend(el('p','This saved link could not be restored. A new business activity has been opened.','notice warning'));
  save();document.documentElement.dataset.ready='true';performance.mark('anatomy-ready');
}
$('back').addEventListener('click',()=>{if(lesson.move(-1)){update(true);}});
$('forward').addEventListener('click',()=>{if(lesson.move(1)){update(true);}});
$('reset').addEventListener('click',()=>{if(lesson.reset()){orders=new Map();reviewStatement='Income Statement';update(true);}});
window.addEventListener('popstate',initialize);
try {initialize();} catch(error) {
  $('lesson').replaceChildren(el('p','This browser could not open the activity. Use a current browser with JavaScript enabled.','notice warning'));
  $('lesson').setAttribute('aria-busy','false');console.error(error);
}
