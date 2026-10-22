const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {test} = require('node:test');
const repo = path.resolve(__dirname, '..');
const source = name => fs.readFileSync(path.join(repo, 'extension', name), 'utf8');

function setup() {
  const events = [];
  const chrome = {
    runtime: {onInstalled:{addListener(){}}, onMessage:{addListener(){}}, getURL: x=>x,
      getContexts: async()=>[{}], sendMessage: async()=>({success:true,text:'OCR text',confidence:95})},
    contextMenus: {onClicked:{addListener(){}}},
    tabs: {query:async()=>[{id:11,windowId:1}], sendMessage:async(id,message)=>events.push({id,...message}),
      captureVisibleTab:async()=>{events.push({action:'captured'});return 'data:image/png;base64,AA==';}},
    scripting:{insertCSS:async()=>{},executeScript:async()=>{}},
  };
  const context = vm.createContext({chrome, crypto, performance, AbortSignal, console:{log(){},warn(){},error(){}},
    fetch:async()=>({ok:true,json:async()=>({status:'completed',verdict:'insufficient_evidence'})})});
  context.importScripts = (...names) => names.forEach(name => vm.runInContext(source(path.posix.normalize('background/'+name)), context));
  vm.runInContext(source('background/service-worker.js'), context);
  return {context, chrome, events, run: code=>vm.runInContext(code,context)};
}

test('browser and backend share expected normalization and triage cases', () => {
  const {context} = setup();
  const cases = JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/claims.json')));
  for (const item of cases) {
    const normalized = context.UnFakeClaims.normalize(item.input);
    assert.equal(normalized,item.normalized);
    assert.equal(context.UnFakeClaims.triage(normalized).category,item.category,item.input);
  }
});

test('client triage rejects opinions without any backend request', async()=>{
  const {context,run} = setup();
  context.fetch = async()=>{throw new Error('Unexpected request');};
  const result = await run('callVerifyAPI("In my opinion, adobo is the best dish.","text")');
  assert.equal(result.status,'triage_rejected');
  assert.equal(result.evaluation_method,'client_triage');
});

test('popup request retains initiating tab across backend delay', async()=>{
  const {context,chrome,events,run} = setup();
  let resolve;
  context.fetch = ()=>new Promise(r=>resolve=r);
  let tab = 11;
  chrome.tabs.query = async()=>[{id:tab,windowId:1}];
  const resultPromise = run('handleVerifyClaim({claim:"Marcos signed the law in 2023."}, {})');
  while (!resolve) await new Promise(r=>setImmediate(r));
  tab = 22;
  resolve({ok:true,json:async()=>({status:'completed'})});
  await resultPromise;
  assert.ok(events.every(e=>e.id===11));
});

test('failed page delivery returns an error instead of success', async()=>{
  const {chrome,run} = setup();
  chrome.tabs.sendMessage=async()=>{throw new Error('No access');};
  chrome.scripting.insertCSS=async()=>{throw new Error('Restricted');};
  await assert.rejects(run('handleVerifyClaim({claim:"Marcos signed the law in 2023."},{tab:{id:11}})'), /cannot display/);
});

test('capture waits for overlay removal and precedes loading UI',async()=>{
  const {events,run}=setup();
  await run('handleCropCompleted({x:1,y:1,width:100,height:100},{id:11,windowId:1})');
  assert.deepEqual(events.slice(0,3).map(e=>e.action),['prepare_capture','captured','show_ocr_loading']);
});

test('capture rejects a changed active tab',async()=>{
  const {chrome,events,run}=setup();
  chrome.tabs.query=async()=>[{id:22}];
  const result=await run('handleCropCompleted({},{id:11,windowId:1})');
  assert.equal(result.success,false);
  assert.ok(!events.some(e=>e.action==='captured'));
});

test('content helpers can be injected twice',()=>{
  const context=vm.createContext({});
  context.window=context;
  for(const file of ['content/text-selection.js','content/image-crop.js']){
    vm.runInContext(source(file),context);
    vm.runInContext(source(file),context);
  }
});

test('newer request suppresses stale result in the same tab',async()=>{
  const {context,events,run}=setup();
  const resolvers=[];
  context.fetch=()=>new Promise(r=>resolvers.push(r));
  const first=run('handleVerifyClaim({claim:"Marcos signed the law in 2023."},{tab:{id:11}})');
  while(resolvers.length<1)await new Promise(r=>setImmediate(r));
  const second=run('handleVerifyClaim({claim:"DepEd announced classes in 2024."},{tab:{id:11}})');
  while(resolvers.length<2)await new Promise(r=>setImmediate(r));
  resolvers[1]({ok:true,json:async()=>({status:'completed',original_claim:'newer'})});
  assert.equal((await second).success,true);
  resolvers[0]({ok:true,json:async()=>({status:'completed',original_claim:'older'})});
  assert.equal((await first).success,false);
  assert.equal(events.filter(e=>e.action==='show_result').length,1);
});
