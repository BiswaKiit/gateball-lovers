GATEBALL LOVERS - MOBILE PUSH REPLACEMENT FILES

Replace these four files in the existing web project:

1. gateball_web.py
2. templates/dashboard.html
3. static/gateball-app.js
4. static/sw.js

The dashboard notification panel is forced visible so mobile/desktop browser
capability problems can be diagnosed instead of hiding the panel.

The Dashboard JS and service worker use a cache-busting version so an older
browser cache is less likely to serve the previous notification code.

Do not delete other Gateball Lovers files.
