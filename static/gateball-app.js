(function(){
  try{
    if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('/static/sw.js').catch(function(e){console.warn('PWA service worker:',e);});});}
  }catch(e){console.warn(e)}
})();
