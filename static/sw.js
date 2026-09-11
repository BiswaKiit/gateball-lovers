const CACHE='gateball-lovers-v4';
self.addEventListener('install',event=>event.waitUntil(self.skipWaiting()));
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  const url=new URL(event.request.url);
  if(url.origin!==self.location.origin) return;
  event.respondWith(fetch(event.request).catch(()=>caches.match(event.request)));
});
self.addEventListener('push',event=>{
  let data={};try{data=event.data?event.data.json():{}}catch(e){data={body:event.data?event.data.text():''}}
  const title=data.title||'Gateball Lovers';
  const options={body:data.body||'💬 New chat message',icon:'/static/images/icon-192.png',badge:'/static/images/icon-192.png',tag:data.tag||'gateball-chat',renotify:true,data:{url:data.url||'/chat'}};
  event.waitUntil(self.registration.showNotification(title,options));
});
self.addEventListener('notificationclick',event=>{
  event.notification.close();
  const target=(event.notification.data&&event.notification.data.url)||'/chat';
  event.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(list=>{
    for(const client of list){
      if('focus' in client){client.navigate(target);return client.focus();}
    }
    if(clients.openWindow) return clients.openWindow(target);
  }));
});
