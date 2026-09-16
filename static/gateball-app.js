(function(){
  // Gateball Lovers PWA helpers: service worker, reliable Web Push registration,
  // authenticated chat realtime alerts, and app-style Android back handling.
  var pushState = {registered:false, lastError:''};

  function setPushText(message){
    var el=document.getElementById('notificationPromptText');
    if(el) el.textContent=message;
  }

  async function ensureServiceWorker(){
    if(!('serviceWorker' in navigator)) throw new Error('This browser does not support service workers.');
    var reg=await navigator.serviceWorker.ready;
    if(!reg) throw new Error('Service worker is not ready yet.');
    return reg;
  }

  try{
    if('serviceWorker' in navigator){
      window.addEventListener('load',function(){
        navigator.serviceWorker.register('/sw.js?v=20260913-pushfix2',{scope:'/'}).then(function(reg){
          try{ reg.update(); }catch(e){}
        }).catch(function(e){console.warn('PWA service worker:',e);});
      });
    }
  }catch(e){console.warn(e)}

  function showDashboardNotificationPrompt(){
    if(location.pathname !== '/settings') return;
    var box=document.getElementById('notificationPrompt');
    var btn=document.getElementById('dashboardNotifyBtn');
    var text=document.getElementById('notificationPromptText');
    if(!box||!btn) return;

    box.style.display='block';

    if(!('Notification' in window)){
      btn.style.display='none';
      text.textContent='⚠️ This browser does not expose the Notification API. Open Gateball Lovers in Chrome and check Android site notification permissions.';
      return;
    }

    if(Notification.permission === 'granted'){
      btn.style.display='block';
      btn.disabled=false;
      btn.textContent='🔔 ENABLE / TEST CHAT NOTIFICATIONS';
      text.textContent='Notifications are allowed. Registering this phone for background chat notifications...';
      btn.onclick=function(){ subscribeForPushIfConfigured(true); };
      subscribeForPushIfConfigured(false);
      return;
    }
    if(Notification.permission === 'denied') {
      btn.style.display='none';
      text.textContent='Notifications are blocked for this browser. Enable Gateball Lovers notifications in Android/Chrome site settings, then return here.';
      return;
    }

    btn.style.display='block';
    btn.disabled=false;
    btn.textContent='🔔 ALLOW CHAT NOTIFICATIONS';
    text.textContent='Enable notifications to receive new chat alerts even when Gateball Lovers is closed.';
    btn.onclick=function(){
      btn.disabled=true; btn.textContent='Requesting permission...';
      Notification.requestPermission().then(function(result){
        if(result==='granted'){
          subscribeForPushIfConfigured(true);
        }else if(result==='denied'){
          btn.style.display='none';
          text.textContent='Notifications are blocked. Enable them in Android/Chrome site settings and return here.';
        }else{
          btn.disabled=false; btn.textContent='🔔 ALLOW CHAT NOTIFICATIONS';
        }
      }).catch(function(err){
        console.error('Notification permission error:',err);
        btn.disabled=false; btn.textContent='🔔 ALLOW CHAT NOTIFICATIONS';
        text.textContent='Could not request notification permission: '+(err.message||err);
      });
    };
  }

  async function subscribeForPushIfConfigured(showTest){
    var btn=document.getElementById('dashboardNotifyBtn');
    try{
      if(!('serviceWorker' in navigator)) throw new Error('Service Worker is not supported by this browser.');
      if(!('PushManager' in window)) throw new Error('Web Push is not supported by this browser.');
      if(!('Notification' in window) || Notification.permission!=='granted') throw new Error('Notification permission is not granted.');
      if(btn){btn.disabled=true;btn.textContent='Registering this phone...';}
      setPushText('Connecting to the Gateball Lovers push service...');

      var r=await fetch('/api/push/public-key',{credentials:'same-origin',cache:'no-store'});
      if(!r.ok) throw new Error('Push public-key request failed ('+r.status+').');
      var info=await r.json();
      if(!info.public_key) throw new Error('Server VAPID public key is missing.');

      var reg=await ensureServiceWorker();
      var sub=await reg.pushManager.getSubscription();
      if(!sub){
        sub=await reg.pushManager.subscribe({
          userVisibleOnly:true,
          applicationServerKey:base64UrlToUint8Array(info.public_key)
        });
      }
      if(!sub || !sub.endpoint) throw new Error('Browser did not return a valid push subscription.');

      var save=await fetch('/api/push/subscribe',{
        method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},
        body:JSON.stringify(sub.toJSON ? sub.toJSON() : sub)
      });
      var saveText=await save.text();
      var saveInfo={}; try{saveInfo=JSON.parse(saveText)}catch(e){}
      if(!save.ok || !saveInfo.ok){
        var detail=saveInfo.error||('HTTP '+save.status);
        throw new Error('Server could not save this phone subscription: '+detail);
      }

      pushState.registered=true; pushState.lastError='';
      setPushText('✅ This phone is registered for background chat notifications. Keep notifications allowed in Android/Chrome.');
      if(btn){btn.disabled=false;btn.textContent='🔔 SEND TEST NOTIFICATION';btn.onclick=function(){sendPushTest();};}
      if(showTest) await sendPushTest();
      return true;
    }catch(e){
      pushState.lastError=String(e&&e.message||e);
      console.error('Push subscription:',e);
      setPushText('❌ Push setup failed: '+pushState.lastError);
      if(btn){btn.disabled=false;btn.textContent='🔁 RETRY CHAT NOTIFICATIONS';btn.onclick=function(){subscribeForPushIfConfigured(false);};}
      return false;
    }
  }

  async function sendPushTest(){
    var btn=document.getElementById('dashboardNotifyBtn');
    try{
      if(btn){btn.disabled=true;btn.textContent='Sending test...';}
      var r=await fetch('/api/push/test',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'});
      var txt=await r.text(), data={}; try{data=JSON.parse(txt)}catch(e){}
      if(!r.ok || !data.ok) throw new Error(data.error||('Push test failed ('+r.status+'). Sent: '+(data.sent||0)));
      setPushText('✅ Test push sent. If this phone is closed/backgrounded, the notification should appear in the Android notification bar.');
      try{localStorage.setItem('gl_push_tested','1');}catch(e){}
      var firstNotice=document.getElementById('notificationPromptDashboard');
      if(firstNotice) firstNotice.style.display='none';
      if(btn){btn.disabled=false;btn.textContent='🔔 SEND TEST AGAIN';btn.onclick=function(){sendPushTest();};}
    }catch(e){
      console.error('Push test:',e);
      setPushText('❌ Test push failed: '+(e.message||e));
      if(btn){btn.disabled=false;btn.textContent='🔁 RETRY PUSH TEST';btn.onclick=function(){sendPushTest();};}
    }
  }

  function base64UrlToUint8Array(base64String){
    var padding='='.repeat((4-base64String.length%4)%4),base64=(base64String+padding).replace(/-/g,'+').replace(/_/g,'/');
    var raw=atob(base64);var out=new Uint8Array(raw.length);for(var i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);return out;
  }

  function browserNotify(title, body, url){
    if(!('Notification' in window) || Notification.permission !== 'granted') return;
    try{
      if(navigator.serviceWorker){
        navigator.serviceWorker.ready.then(function(reg){
          reg.showNotification(title,{body:body,icon:'/static/images/icon-192.png',badge:'/static/images/icon-192.png',tag:'gateball-chat',data:{url:url||'/chat'},renotify:true});
        }).catch(function(e){console.warn('Notification:',e)});
      }
    }catch(e){console.warn('Notification:',e)}
  }

  function showFirstTimeDashboardNotice(){
    if(location.pathname !== '/dashboard') return;
    var box=document.getElementById('notificationPrompt');
    if(!box) return;
    var tested=false;
    try{tested=localStorage.getItem('gl_push_tested')==='1';}catch(e){}
    box.style.display=tested?'none':'block';
  }

  async function initGlobalChatNotifications(){
    if(location.pathname === '/login' || location.pathname === '/signup') return;
    try{
      var r=await fetch('/api/session-info',{credentials:'same-origin',cache:'no-store'});
      if(!r.ok) return;
      var info=await r.json();
      if(!info.logged_in || !info.access_token || !info.user_id || !info.supabase_url || !info.supabase_key) return;

      showDashboardNotificationPrompt();
      showFirstTimeDashboardNotice();
      if(Notification.permission==='granted') subscribeForPushIfConfigured(false);

      if(!window.supabase){
        await new Promise(function(resolve,reject){var s=document.createElement('script');s.src='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';s.onload=resolve;s.onerror=reject;document.head.appendChild(s);});
      }
      var sb=window.supabase.createClient(info.supabase_url,info.supabase_key,{global:{headers:{Authorization:'Bearer '+info.access_token}}});
      try{sb.realtime.setAuth(info.access_token)}catch(e){}
      var channel=sb.channel('global-chat-notifications-'+info.user_id)
        .on('postgres_changes',{event:'INSERT',schema:'public',table:'direct_messages'},function(payload){
          var m=payload.new||{};
          if(String(m.receiver_id||'')!==String(info.user_id)||String(m.sender_id||'')===String(info.user_id))return;
          var when=new Date(m.created_at||Date.now()).getTime(),last=Number(localStorage.getItem('gl_last_chat_notice')||0);
          if(when<=last)return;localStorage.setItem('gl_last_chat_notice',String(when));
          if(document.visibilityState!=='visible'||!location.pathname.startsWith('/chat/direct/')) browserNotify('Gateball Lovers','💬 New private chat message','/chat');
        }).subscribe();
      window.__glGlobalChatChannel=channel;
    }catch(e){console.warn('Global chat notifications:',e)}
  }

  function init(){
    showDashboardNotificationPrompt();
    showFirstTimeDashboardNotice();
    initGlobalChatNotifications();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
