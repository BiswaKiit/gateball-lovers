(function(){
  // Gateball Lovers PWA helpers: service worker, dashboard notification opt-in,
  // authenticated chat realtime alerts, and app-style Android back handling.
  try{
    if('serviceWorker' in navigator){
      window.addEventListener('load',function(){
        navigator.serviceWorker.register('/sw.js').catch(function(e){console.warn('PWA service worker:',e);});
      });
    }
  }catch(e){console.warn(e)}

  function showDashboardNotificationPrompt(){
    if(location.pathname !== '/dashboard') return;
    var box=document.getElementById('notificationPrompt');
    var btn=document.getElementById('dashboardNotifyBtn');
    var text=document.getElementById('notificationPromptText');
    if(!box||!btn||!('Notification' in window)) return;

    if(Notification.permission === 'granted') { box.style.display='none'; return; }
    if(Notification.permission === 'denied') {
      box.style.display='block';
      btn.style.display='none';
      text.textContent='Notifications are blocked for this browser. Please enable Gateball Lovers notifications in your browser/site settings.';
      return;
    }

    // permission === default: show to every member who has not chosen yet,
    // including both new and existing members.
    box.style.display='block';
    btn.style.display='block';
    btn.onclick=function(){
      btn.disabled=true;
      btn.textContent='Requesting permission...';
      Notification.requestPermission().then(function(result){
        if(result==='granted'){
          box.style.display='none';
          subscribeForPushIfConfigured();
        }else if(result==='denied'){
          btn.style.display='none';
          text.textContent='Notifications are blocked for this browser. You can enable them later in site/browser settings.';
        }else{
          btn.disabled=false;btn.textContent='🔔 ALLOW CHAT NOTIFICATIONS';
        }
      }).catch(function(){btn.disabled=false;btn.textContent='🔔 ALLOW CHAT NOTIFICATIONS';});
    };
  }

  async function subscribeForPushIfConfigured(){
    // The current build registers the service worker and permission. Full
    // closed-app Web Push delivery also needs a VAPID public key/server sender.
    // Keep this hook ready without breaking normal chat/realtime operation.
    try{
      if(!('PushManager' in window)||!('serviceWorker' in navigator)) return;
      var r=await fetch('/api/push/public-key',{credentials:'same-origin',cache:'no-store'});
      if(!r.ok)return;
      var info=await r.json();
      if(!info.public_key)return;
      var reg=await navigator.serviceWorker.ready;
      var sub=await reg.pushManager.getSubscription();
      if(!sub) sub=await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:base64UrlToUint8Array(info.public_key)});
      await fetch('/api/push/subscribe',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(sub)});
    }catch(e){console.warn('Push subscription:',e)}
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
        }).catch(function(){});
      }
    }catch(e){console.warn('Notification:',e)}
  }

  async function initGlobalChatNotifications(){
    if(location.pathname === '/login' || location.pathname === '/signup') return;
    try{
      var r=await fetch('/api/session-info',{credentials:'same-origin',cache:'no-store'});
      if(!r.ok) return;
      var info=await r.json();
      if(!info.logged_in || !info.access_token || !info.user_id || !info.supabase_url || !info.supabase_key) return;

      showDashboardNotificationPrompt();
      if(Notification.permission==='granted') subscribeForPushIfConfigured();

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

  // Keep the PWA feeling like a single app instead of a stack of web pages.
  // Internal links use location.replace(), so normal navigation does not add
  // another Back entry. A single guarded history entry then handles Android
  // / browser Back with our Exit dialog.
  catch(e){}
      setTimeout(function(){try{location.replace('/');}catch(e){}},120);
    };
  }

  function init(){
    showDashboardNotificationPrompt();
    initGlobalChatNotifications();
    initAppBack();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
