/** Native accounting model, legacy-compatible snapshots, and guarded station actions. */
import {DATA} from './content.js';

export const copy = value => structuredClone(value);
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const own = (object, key) => Object.hasOwn(object, key);
const valid = (value, choices, fallback) => typeof value === 'string' && choices.includes(value) ? value : fallback;
export const planKeys = ['funding','asset','operating','dividend'];
export const clean = text => String(text).replace(/\\\$/g, '$');
export const money = number => (number < 0 ? '−' : '') + '$' + Math.abs(number).toLocaleString('en-US', {maximumFractionDigits:0});
export function newState() {
  return {page:0,funding:'Balanced',asset:'Essential setup',operating:'Balanced growth',
    dividend:'Return some value to shareholders',organization_answer:null,organization_checked:false,
    launched:false,activity_selections:{},activity_answers:{},activity_checked:false,
    statement_selection:null,statement_answers:{},statement_results:{},decision_completed:false};
}
export function configFor(state) {
  return DATA.configs.find(config => config.choices.every((value,index) => value === state[planKeys[index]]));
}
export function buildScenario(choices) {
  const state=Array.isArray(choices)?Object.fromEntries(planKeys.map((key,index)=>[key,choices[index]])):choices;
  const config=configFor(state);
  if(!config)throw new Error('Unknown business plan');
  return copy(config.events);
}
export function calculateSummary(events) {
  const account=name=>events.reduce((sum,event)=>sum+(event.account_effects[name]??0),0);
  const cash=account('Cash'),equipment=account('Equipment'),notes_payable=account('Notes Payable');
  const common_stock=account('Common Stock'),revenue=account('Service Revenue');
  const wages_expense=account('Wages Expense'),other_expenses=account('Operating Expense'),dividends=account('Dividends');
  const total_expenses=wages_expense+other_expenses,net_income=revenue-total_expenses;
  const ending_retained_earnings=net_income-dividends;
  const flow=type=>events.filter(event=>event.activity_type===type).reduce((sum,event)=>sum+(event.account_effects.Cash??0),0);
  const operating_cash_flow=flow('Operating'),investing_cash_flow=flow('Investing'),financing_cash_flow=flow('Financing');
  return {cash,equipment,total_assets:cash+equipment,notes_payable,common_stock,revenue,wages_expense,
    other_expenses,total_expenses,net_income,dividends,ending_retained_earnings,
    total_liabilities_and_equity:notes_payable+common_stock+ending_retained_earnings,
    operating_cash_flow,investing_cash_flow,financing_cash_flow,
    net_change_in_cash:operating_cash_flow+investing_cash_flow+financing_cash_flow};
}
export function normalizeSaved(raw) {
  if(!object(raw))return null;
  const state=newState();
  planKeys.forEach((key,index)=>{state[key]=valid(raw[key],Object.keys(DATA.plans[index]),state[key]);});
  state.organization_answer=valid(raw.organization_answer,['Sole proprietorship','Partnership','Corporation'],null);
  state.organization_checked=Boolean(raw.organization_checked);
  state.launched=raw.launched===true;
  if(state.launched) {
    const config=configFor(state),events=config.events,allowed=['Not sure yet',...DATA.activities];
    for(const event of events) {
      const answer=object(raw.activity_answers)?raw.activity_answers[event.event_id]:null;
      if(allowed.includes(answer))state.activity_answers[event.event_id]=answer;
      const draft=object(raw.activity_selections)?raw.activity_selections[event.event_id]:null;
      const restored=draft??answer;
      if(allowed.includes(restored))state.activity_selections[event.event_id]=restored;
    }
    state.activity_checked=raw.activity_checked===true&&Object.keys(state.activity_answers).length===events.length;
    for(const name of DATA.statements) {
      const result=object(raw.statement_results)?raw.statement_results[name]:null;
      if(typeof result==='boolean')state.statement_results[name]=result;
      const answer=object(raw.statement_answers)?raw.statement_answers[name]:null;
      if(config.questions[name].options.includes(answer))state.statement_answers[name]=answer;
    }
    state.statement_selection=valid(raw.statement_selection,DATA.statements,null);
    state.decision_completed=raw.decision_completed===true&&state.activity_checked&&Object.keys(state.statement_results).length===4;
  }
  const requested=Number.isInteger(raw.page)&&raw.page>=0&&raw.page<4?raw.page:0;
  let minimum=0,maximum=0;
  if(state.launched) {
    minimum=maximum=1;
    if(state.activity_checked) {
      maximum=2;
      if(Object.keys(state.statement_results).length)minimum=2;
      if(Object.keys(state.statement_results).length===4) {
        maximum=3;
        if(state.decision_completed)minimum=3;
      }
    }
  }
  state.page=Math.max(minimum,Math.min(requested,maximum));
  return state;
}
export function canonicalJSON(value) {
  if(Array.isArray(value))return '['+value.map(canonicalJSON).join(',')+']';
  if(object(value))return '{'+Object.keys(value).sort().map(key=>JSON.stringify(key)+':'+canonicalJSON(value[key])).join(',')+'}';
  return JSON.stringify(value).replace(/[\u007f-\uffff]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'));
}
function to64(bytes) {
  let text='';for(const byte of bytes)text+=String.fromCharCode(byte);
  return btoa(text).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/g,'');
}
export function encodeState(state) {
  const normalized=normalizeSaved(state);
  if(!normalized)throw new Error('Invalid activity state');
  const bytes=new TextEncoder().encode(canonicalJSON({version:1,state:normalized}));
  if(bytes.length>9000)throw new Error('Saved state too large');
  return to64(bytes);
}
export function decodeState(token) {
  try {
    if(typeof token!=='string'||!token.length||token.length>12000||!/^[A-Za-z0-9_-]+$/.test(token))return null;
    const text=atob(token.replace(/-/g,'+').replace(/_/g,'/')+'='.repeat((4-token.length%4)%4));
    const bytes=Uint8Array.from(text,c=>c.charCodeAt(0));
    if(bytes.length>9000)return null;
    const raw=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
    return raw.version===1?normalizeSaved(raw.state):null;
  } catch{return null;}
}
export function shuffled(options) {
  const result=[...options];
  const below=max=>{
    const limit=Math.floor(4294967296/max)*max;
    let value;do{value=crypto.getRandomValues(new Uint32Array(1))[0];}while(value>=limit);
    return value%max;
  };
  for(let i=result.length-1;i>0;i--){const j=below(i+1);[result[i],result[j]]=[result[j],result[i]];}
  return result;
}
export class Lesson {
  constructor(state=newState(),view) {
    this.state=normalizeSaved(state);
    const number=typeof view==='string'&&/^-?\d+$/.test(view)?Number(view):view;
    this.view=Number.isInteger(number)&&number>=0&&number<=this.state.page?number:this.state.page;
  }
  get reviewing(){return this.view<this.state.page;}
  get config(){return configFor(this.state);}
  move(direction) {
    if(![-1,1].includes(direction))return false;
    const target=this.view+direction;
    if(target<0||target>this.state.page)return false;
    this.view=target;return true;
  }
  draft(key,value) {
    if(this.reviewing)return false;
    const state=this.state;
    const plan={funding_choice:0,asset_choice:1,operating_choice:2,dividend_choice:3}[key];
    if(state.page===0&&plan!==undefined&&Object.keys(DATA.plans[plan]).includes(value)) {
      state[planKeys[plan]]=value;return true;
    }
    if(state.page===0&&key==='organization_answer'&&['Sole proprietorship','Partnership','Corporation'].includes(value)) {
      state.organization_answer=value;return true;
    }
    if(state.page===1&&key.startsWith('activity_')) {
      const id=key.slice(9);
      if(this.config.events.some(event=>event.event_id===id)&&['Not sure yet',...DATA.activities].includes(value)) {
        state.activity_selections[id]=value;return true;
      }
    }
    if(state.page===2&&key==='statement_selection'&&DATA.statements.includes(value)) {
      state.statement_selection=value;return true;
    }
    if(state.page===2&&key.startsWith('statement_answer_')) {
      const name=DATA.statements.find(name=>'statement_answer_'+name.toLowerCase().replaceAll(' ','_')===key);
      if(name===state.statement_selection&&this.config.questions[name].options.includes(value)) {
        state.statement_answers[name]=value;return true;
      }
    }
    return false;
  }
  checkOrganization() {
    if(this.reviewing||this.state.page!==0||!this.state.organization_answer)return false;
    this.state.organization_checked=true;return true;
  }
  launch() {
    if(this.reviewing||this.state.page!==0)return false;
    Object.assign(this.state,{launched:true,page:1,activity_selections:{},activity_answers:{},
      activity_checked:false,statement_selection:null,statement_answers:{},statement_results:{},decision_completed:false});
    this.view=1;return true;
  }
  checkActivity() {
    if(this.reviewing||this.state.page!==1)return false;
    this.state.activity_answers=Object.fromEntries(this.config.events.map(event=>
      [event.event_id,this.state.activity_selections[event.event_id]??'Not sure yet']));
    this.state.activity_checked=true;return true;
  }
  checkStatement() {
    if(this.reviewing||this.state.page!==2)return false;
    const name=this.state.statement_selection,answer=this.state.statement_answers[name];
    if(!name||!this.config.questions[name].options.includes(answer))return false;
    this.state.statement_results[name]=answer===this.config.questions[name].correct;return true;
  }
  advance() {
    if(this.reviewing)return false;
    if(this.state.page===1&&this.state.activity_checked||
       this.state.page===2&&Object.keys(this.state.statement_results).length===4) {
      this.state.page++;this.view=this.state.page;return true;
    }
    return false;
  }
  complete() {
    if(this.reviewing||this.state.page!==3||!this.state.activity_checked||Object.keys(this.state.statement_results).length!==4)return false;
    this.state.decision_completed=true;return true;
  }
  reset() {
    if(this.reviewing)return false;
    this.state=newState();this.view=0;return true;
  }
}
