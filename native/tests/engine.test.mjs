import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {DATA} from '../content.js';
import {Lesson,buildScenario,calculateSummary,configFor,newState,normalizeSaved,
  encodeState,decodeState,canonicalJSON,shuffled} from '../engine.js';

const oracle=JSON.parse(readFileSync(new URL('./python-oracles.json',import.meta.url)));
const legacy=JSON.parse(readFileSync(new URL('./legacy-links.json',import.meta.url)));
function completed() {
  const lesson=new Lesson();lesson.draft('organization_answer','Corporation');lesson.checkOrganization();lesson.launch();
  for(const event of lesson.config.events)lesson.draft('activity_'+event.event_id,event.activity_type);
  lesson.checkActivity();assert.equal(lesson.advance(),true);
  for(const name of DATA.statements) {
    lesson.draft('statement_selection',name);
    lesson.draft('statement_answer_'+name.toLowerCase().replaceAll(' ','_'),lesson.config.questions[name].correct);
    lesson.checkStatement();
  }
  assert.equal(lesson.advance(),true);assert.equal(lesson.complete(),true);return lesson;
}
test('all 36 financial plans match independent Python event and summary outcomes',()=>{
  assert.equal(oracle.length,36);
  for(const expected of oracle) {
    const events=buildScenario(expected.choices);
    assert.deepEqual(events,expected.events);
    assert.deepEqual(calculateSummary(events),expected.summary);
    assert.equal(calculateSummary(events).cash,calculateSummary(events).net_change_in_cash);
    assert.equal(calculateSummary(events).total_assets,calculateSummary(events).total_liabilities_and_equity);
  }
});
test('legacy version-1 bookmarks retain earned stations and submitted work',()=>{
  for(const fixture of legacy) {
    const state=decodeState(fixture.token);assert.ok(state);
    assert.equal(state.page,fixture.state.page);assert.equal(state.launched,fixture.state.launched);
    assert.deepEqual(state.activity_answers,fixture.state.activity_answers);
    assert.deepEqual(state.statement_results,fixture.state.statement_results);
    assert.deepEqual(decodeState(encodeState(state)),state);
  }
});
test('native snapshots are decoded without loss by the unchanged Python codec',()=>{
  const state=completed().state,token=encodeState(state);
  const result=spawnSync(process.env.PYTHON??'python3',['-c',
    'import json,sys;from resume_state import decode_resume_state;print(json.dumps(decode_resume_state(sys.argv[1]),sort_keys=True))',token],
    {cwd:new URL('../../',import.meta.url),encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);assert.deepEqual(JSON.parse(result.stdout),state);
});
test('incorrect activity and statement answers retain the original explored-only gates',()=>{
  const lesson=new Lesson();
  assert.equal(lesson.advance(),false);assert.equal(lesson.launch(),true);
  assert.equal(lesson.advance(),false);
  lesson.checkActivity();assert.equal(lesson.advance(),true);
  for(const name of DATA.statements) {
    lesson.draft('statement_selection',name);
    const wrong=lesson.config.questions[name].options.find(value=>value!==lesson.config.questions[name].correct);
    assert.equal(lesson.draft('statement_answer_'+name.toLowerCase().replaceAll(' ','_'),wrong),true);
    lesson.checkStatement();assert.equal(lesson.state.statement_results[name],false);
  }
  assert.equal(lesson.advance(),true);assert.equal(lesson.complete(),true);
});
test('repeated checks replace only the original results; drafts remain distinct from submitted answers',()=>{
  const lesson=new Lesson();lesson.launch();lesson.draft('activity_issue_stock','Investing');lesson.checkActivity();
  const answer=lesson.state.activity_answers.issue_stock;
  lesson.draft('activity_issue_stock','Financing');
  assert.equal(lesson.state.activity_answers.issue_stock,answer);
  const restored=decodeState(encodeState(lesson.state));
  assert.equal(restored.activity_selections.issue_stock,'Financing');
  assert.equal(restored.activity_answers.issue_stock,'Investing');
  lesson.checkActivity();lesson.checkActivity();assert.equal(lesson.state.activity_answers.issue_stock,'Financing');
  assert.equal(Object.hasOwn(lesson.state,'attempts'),false);
});
test('every review station rejects every progress mutation independently of its controls',()=>{
  const lesson=completed(),before=canonicalJSON(lesson.state);
  for(let view=2;view>=0;view--) {
    assert.equal(lesson.move(-1),true);assert.equal(lesson.view,view);
    for(const method of ['checkOrganization','launch','checkActivity','checkStatement','advance','complete','reset'])
      assert.equal(lesson[method](),false,method);
    assert.equal(lesson.draft('funding_choice','Credit-forward'),false);
    assert.equal(lesson.draft('activity_issue_stock','Investing'),false);
    assert.equal(lesson.draft('statement_selection','Balance Sheet'),false);
    assert.equal(canonicalJSON(lesson.state),before);
  }
  for(let view=1;view<=3;view++){assert.equal(lesson.move(1),true);assert.equal(lesson.view,view);}
  assert.equal(lesson.move(1),false);assert.equal(canonicalJSON(lesson.state),before);
});
test('future views and legacy unearned station requests are clamped; malformed links reset safely',()=>{
  const lesson=completed();
  for(const view of ['99','-1','NaN','3.5',{},null])assert.equal(new Lesson(lesson.state,view).view,3);
  const raw={...newState(),launched:true,page:3};assert.equal(normalizeSaved(raw).page,1);
  for(const token of [null,'','invalid!','a'.repeat(12001),Buffer.from('{"version":2,"state":{}}').toString('base64url')])
    assert.equal(decodeState(token),null);
  const unknown={...raw,funding:'unknown',statement_answers:{'Balance Sheet':'not an option'}};
  assert.equal(normalizeSaved(unknown).funding,'Balanced');
  assert.deepEqual(normalizeSaved(unknown).statement_answers,{});
});
test('reset and independent instances preserve old copied bookmarks',()=>{
  const first=completed(),token=encodeState(first.state),second=new Lesson();
  assert.equal(second.state.launched,false);first.reset();assert.deepEqual(first.state,newState());
  assert.equal(decodeState(token).decision_completed,true);assert.equal(second.state.page,0);
});
test('shuffle retains every original option and the original per-instance permutation semantics',()=>{
  const values=['Financing','Investing','Operating'];
  for(let n=0;n<40;n++)assert.deepEqual(shuffled(values).sort(),[...values].sort());
  assert.deepEqual(values,['Financing','Investing','Operating']);
});
test('every captured lesson variant contains no provisional student-facing branding',()=>{
  const titles=DATA.configs.flatMap(config=>[
    ...Object.values(config.launch),...Object.values(config.activity),
    ...Object.values(config.statements).flatMap(Object.values),...Object.values(config.decision)]);
  const audit=node=>{
    if(Array.isArray(node)){node.forEach(audit);return;}
    if(node&&typeof node==='object'){
      for(const key of ['text','label','value'])if(typeof node[key]==='string')
        assert.doesNotMatch(node[key],/\b(?:pilot|preview|test(?:ing)?\s+(?:app|version|site))\b/i);
      if(node.children)audit(node.children);
    }
  };
  titles.forEach(audit);assert.equal(DATA.title,'Anatomy of a Business');
  assert.equal(configFor(newState()).choices[0],'Balanced');
});
