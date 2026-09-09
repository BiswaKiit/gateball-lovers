(function(){
  // Gateball Lovers PWA + session-safe chat notifications.
  try{
    if('serviceWorker' in navigator){
      window.addEventListener('load',function(){
        navigator.serviceWorker.register('/sw.js').catch(function(e){console.warn('PWA service worker:',e);});
      });
    }
  }catch(e){console.warn(e)}

  function addNotificationButton(){
    if(!('Notification' in window) || Notification.permission === 'granted' || Notification.permission === 'denied') return;
    if(document.getElementById('glNotifyBtn')) return;
    var btn=document.createElement('button');
    btn.id='glNotifyBtn';
    btn.type='button';
    btn.textContent='🔔 Enable chat notifications';
    btn.style.cssText='position:fixed;right:12px;bottom:84px;z-index:90;border:0;border-radius:22px;padding:10px 14px;background:#075b35;color:#fff;font-weight:700;box-shadow:0 5px 18px rgba(0,0,0,.22);font-size:12px;cursor:pointer';
    btn.onclick=function(){
      Notification.requestPermission().then(function(){btn.remove();}).catch(function(){});
    };
    document.body.appendChild(btn);
  }

  function browserNotify(title, body, url){
    if(!('Notification' in window) || Notification.permission !== 'granted') return;
    try{
      if(navigator.serviceWorker && navigator.serviceWorker.ready){
        navigator.serviceWorker.ready.then(function(reg){
          reg.showNotification(title,{body:body,icon:'/static/images/icon-192.png',badge:'/static/images/icon-192.png',tag:'gateball-chat',data:{url:url||'/chat'},renotify:true});
        }).catch(function(){new Notification(title,{body:body,icon:'/static/images/icon-192.png'});});
      }else{
        new Notification(title,{body:body,icon:'/static/images/icon-192.png'});
      }
    }catch(e){console.warn('Notification:',e)}
  }

  async function initGlobalChatNotifications(){
    // The login/signup pages have no authenticated session and need no chat listener.
    if(location.pathname === '/login' || location.pathname === '/signup') return;
    try{
      var r=await fetch('/api/session-info',{credentials:'same-origin',cache:'no-store'});
      if(!r.ok) return;
      var info=await r.json();
      if(!info.logged_in || !info.access_token || !info.user_id || !info.supabase_url || !info.supabase_key) return;

      addNotificationButton();
      if(!window.supabase){
        await new Promise(function(resolve,reject){
          var s=document.createElement('script');
          s.src='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
          s.onload=resolve;s.onerror=reject;document.head.appendChild(s);
        });
      }
      var sb=window.supabase.createClient(info.supabase_url,info.supabase_key,{global:{headers:{Authorization:'Bearer '+info.access_token}}});
      try{sb.realtime.setAuth(info.access_token)}catch(e){}

      var channel=sb.channel('global-chat-notifications-'+info.user_id)
        .on('postgres_changes',{event:'INSERT',schema:'public',table:'direct_messages'},function(payload){
          var m=payload.new||{};
          if(String(m.receiver_id||'')!==String(info.user_id) || String(m.sender_id||'')===String(info.user_id)) return;
          var when=new Date(m.created_at||Date.now()).getTime();
          var last=Number(localStorage.getItem('gl_last_chat_notice')||0);
          if(when<=last) return;
          localStorage.setItem('gl_last_chat_notice',String(when));
          // The direct-chat page already renders the incoming message. The global listener
          // adds the OS/browser notification when the member is elsewhere in the app.
          if(document.visibilityState !== 'visible' || !location.pathname.startsWith('/chat/direct/')){
            browserNotify('Gateball Lovers', '💬 New private chat message', '/chat');
          }
        })
        .subscribe();
      window.__glGlobalChatChannel=channel;
    }catch(e){console.warn('Global chat notifications:',e)}
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',initGlobalChatNotifications);
  else initGlobalChatNotifications();
})();
