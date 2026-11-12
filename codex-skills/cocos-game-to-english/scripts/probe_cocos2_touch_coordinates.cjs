'use strict';
// Executes the package's actual legacy Cocos converter, not a reimplementation.
const vm=require('vm'),fs=require('fs');
function probe(files){
 const engine=files['cocos/cocos2d-js-min.js']||'';
 const start=engine.indexOf('getTouchesByEvent:function(');
 const end=engine.indexOf(',registerSystemEvent:function',start);
 if(start<0||end<0)throw Error('unsupported Cocos touch converter; do not mark input verified');
 const fn=engine.slice(start+'getTouchesByEvent:'.length,end);
 class Touch{constructor(x,y,id){this.x=x;this.y=y;this.id=id;}getLocation(){return{x:this.x,y:this.y};}_setPrevPoint(){}}
 const manager={_glView:{convertToLocationInView(x,y){return{x:x*1,y:y*1};}},_preTouchPoint:{x:0,y:0},getPreTouch(){return{getLocation(){return{x:0,y:0};}};},setPreTouch(){}};
 manager.getTouchesByEvent=vm.runInNewContext('('+fn+')',{n:{BROWSER_TYPE_FIREFOX:'firefox',browserType:'native'},s:{},o:{},cc:{Touch}});
 const entry=files['game.js']||'';
 if(entry.includes("require('./touch-coordinates').install(cc)")){
  const context={module:{exports:{}},Number,Object,Array,Error};vm.runInNewContext(files['touch-coordinates.js']||'',context,{timeout:1000});
  context.module.exports.install({internal:{inputManager:manager}});
 }
 const cases=[['sdk_screen_coordinates',{identifier:0,screenX:195,screenY:392},195,392],['client_coordinates',{identifier:0,clientX:20,clientY:30},20,30],['preserve_client_coordinates',{identifier:0,clientX:11,clientY:12,screenX:99,screenY:98},11,12],['zero_coordinates',{identifier:0,screenX:0,screenY:0},0,0]];
 const rows=cases.map(([id,t,x,y])=>{const a=manager.getTouchesByEvent({changedTouches:[t],touches:[t]},{});return{id,passed:a.length===1&&a[0].x===x&&a[0].y===y&&a[0].id===0,observed:a.map(t=>({x:t.x,y:t.y,id:t.id}))};});
 return{schema:'cocos2_touch_coordinates.v1',passed:rows.every(r=>r.passed),rows,boundary:'actual converter with controlled SDK payloads; not renderer/device acceptance'};
}
if(require.main===module){try{const payload=JSON.parse(fs.readFileSync(0,'utf8'));const r=probe(payload.files);console.log(JSON.stringify(r));process.exitCode=r.passed?0:1;}catch(e){console.log(JSON.stringify({passed:false,error:e.message}));process.exitCode=1;}}
module.exports={probe};
