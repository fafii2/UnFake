/** Real Chromium MV3 smoke test. No keys or external services required. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');

const repo = path.resolve(__dirname, '..');
const artifacts = path.resolve(process.env.UNFAKE_TEST_OUTPUT || path.join(repo, 'test-results'));
fs.mkdirSync(artifacts, {recursive:true});
const claim = 'The BSP stores 400,000 tons of Tallano gold owned by Ferdinand Marcos Sr.';

(async()=>{
  const profile = fs.mkdtempSync(path.join(process.env.TEMP || os.tmpdir(), 'unfake-browser-'));
  const context = await chromium.launchPersistentContext(profile, {
    channel:'chromium', headless:true, viewport:{width:1280,height:1000},
    ignoreDefaultArgs:['--disable-extensions'],
    ...(process.env.UNFAKE_CHROMIUM ? {executablePath:process.env.UNFAKE_CHROMIUM} : {}),
    args:['--enable-unsafe-extension-debugging',`--disable-extensions-except=${path.join(repo,'extension')}`,`--load-extension=${path.join(repo,'extension')}`],
  });
  try {
    const worker = context.serviceWorkers()[0] || await context.waitForEvent('serviceworker',{timeout:20000});
    const extensionId = new URL(worker.url()).hostname;
    const errors=[];
    worker.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
    const page = await context.newPage();
    const demoOrigin = 'http://localhost:8000';
    await page.goto(demoOrigin + '/demo');
    const tabId = await worker.evaluate(async origin => {
      const tabs=await chrome.tabs.query({});
      return tabs.find(tab=>tab.url?.startsWith(origin)).id;
    },demoOrigin);
    await page.bringToFront();
    // Exercise production scripts on the allowed local demo origin. On unrelated
    // sites, activeTab access is granted by an actual toolbar/context-menu gesture.
    await worker.evaluate(async ({id})=>{
      await chrome.scripting.insertCSS({target:{tabId:id},files:['content/content.css']});
      await chrome.scripting.executeScript({target:{tabId:id},files:['content/text-selection.js','content/image-crop.js','content/content.js']});
    },{id:tabId});
    const result = await worker.evaluate(async ({id,claim}) => handleVerifyClaim({claim,inputType:'text',tabId:id},{}), {id:tabId,claim});
    assert.equal(result.success,true);
    assert.equal(result.result.verdict,'contradicted');
    await page.locator('.unfake-verdict-badge').filter({hasText:'Contradicted'}).waitFor();
    assert.ok((await page.locator('.unfake-evidence-link').first().getAttribute('href')).startsWith('https://verafiles.org/'));
    await page.screenshot({path:path.join(artifacts,'verification-result.png')});
    console.log('PASS: real extension -> local FastAPI -> SQLite archive -> sourced verdict modal');
    await page.locator('#unfake-close').click();

    const rejected = await worker.evaluate(async id => handleVerifyClaim({claim:'In my opinion, adobo is the best dish.',tabId:id},{}), tabId);
    assert.equal(rejected.result.evaluation_method,'client_triage');
    await page.locator('.unfake-verdict-badge').filter({hasText:'Not a Factual Claim'}).waitFor();
    console.log('PASS: client-side opinion triage rendered in actual page');
    await page.locator('#unfake-close').click();

    // Exercise untrusted provider strings in the actual renderer.
    await worker.evaluate(async id => chrome.tabs.sendMessage(id,{action:'show_result',result:{status:'completed',verdict:'insufficient_evidence',explanation:'<img src=x onerror=alert(1)>',evidence:[{id:'test',title:'Untrusted title',source_url:'javascript:alert(1)',publisher:'Test',snippet:'<script>window.injected=true</script>',relevance:'contextual'}]}}),tabId);
    assert.equal(await page.locator('.unfake-evidence-link').getAttribute('href'),'#');
    assert.equal(await page.locator('#unfake-modal script').count(),0);
    console.log('PASS: unsafe citation scheme and provider HTML remain inert');
    await page.locator('#unfake-close').click();

    // Real crop overlay coordinates, offscreen page, local WASM worker, and OCR review.
    const browserSession = await context.browser().newBrowserCDPSession();
    const {targetInfos} = await browserSession.send('Target.getTargets',{filter:[{type:'tab',exclude:false},{exclude:true}]});
    const tabTarget = targetInfos.find(target=>target.url===page.url());
    if(!tabTarget) throw new Error('No browser tab target found: '+JSON.stringify(targetInfos));
    await browserSession.send('Extensions.triggerAction',{id:extensionId,targetId:tabTarget.targetId});
    for(const candidate of context.pages()) {
      if(candidate.url().includes('/popup/popup.html')) await candidate.close();
    }
    await page.bringToFront();
    await worker.evaluate(async id=>chrome.tabs.sendMessage(id,{action:'start_crop'}),tabId);
    await page.locator('#unfake-crop-canvas').waitFor();
    const box=await page.locator('#ocr').boundingBox();
    await page.mouse.move(box.x+3,box.y+3);
    await page.mouse.down();
    await page.mouse.move(box.x+box.width-3,box.y+box.height-3,{steps:10});
    await page.mouse.up();
    const ocrOutcome = await Promise.race([
      page.locator('#unfake-ocr-input').waitFor({timeout:45000}).then(()=> 'review'),
      page.locator('.unfake-verdict-error').waitFor({timeout:45000}).then(async()=> 'error: ' + await page.locator('.unfake-explanation').innerText()),
    ]);
    if(ocrOutcome !== 'review') throw new Error(ocrOutcome);
    const extracted = await page.locator('#unfake-ocr-input').inputValue();
    assert.match(extracted,/BSP/i);
    assert.match(extracted,/Tallano/i);
    await page.screenshot({path:path.join(artifacts,'ocr-review.png')});
    console.log('PASS: viewport crop -> local Tesseract WASM -> editable OCR review:',extracted.replace(/\s+/g,' '));
    // User correction is intentionally part of the supported workflow.
    await page.locator('#unfake-ocr-input').fill(claim);
    await page.locator('#unfake-verify-ocr-btn').click();
    await page.locator('.unfake-verdict-badge').filter({hasText:'Contradicted'}).waitFor();
    console.log('PASS: reviewed OCR text -> verification result');

    const popup=await context.newPage();
    await popup.goto(`chrome-extension://${extensionId}/popup/popup.html`);
    await popup.locator('#statusText').filter({hasText:'Backend online'}).waitFor();
    await popup.locator('#exampleBtn').click();
    assert.equal(await popup.locator('#manualClaim').inputValue(),claim);
    await popup.screenshot({path:path.join(artifacts,'extension-popup.png')});
    console.log('PASS: actual extension popup health check and archived example');
    if(errors.length) console.log('Worker errors:',JSON.stringify(errors));
    console.log('BROWSER CHECKS PASSED');
  } finally {
    await context.close();
    // Keep the isolated profile as a debugging intermediate; never touch user profiles.
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
