import {test} from 'node:test';import assert from 'node:assert/strict';import {spawnSync} from 'node:child_process';
test('all 18 controllers run against an API double and exercise distinct behaviors',()=>{
 for(const profile of ['full','stable20']){
 const result=spawnSync(process.execPath,['--no-warnings','--experimental-loader','./tests/minecraft-loader.mjs','./tests/runtime-smoke.mjs'],{encoding:'utf8',env:{...process.env,MOBPORTS_API_20_ONLY:profile==='stable20'?'1':'0'}});
 assert.equal(result.status,0,result.stdout+'\n'+result.stderr);
 }
});
