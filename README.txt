GATEBALL LOVERS - WEB UPDATE

Replace the existing files in D:\Gateball Lovers\web with the files from this package.

Main changes:
1. Dashboard Gateball News shows one latest headline + VIEW MORE NEWS.
2. /news shows all loaded Gateball headlines from worldwide search + WGU + JGU.
3. Tournament tabs change active color: selected tab = saffron; other tabs = grey.
4. Add Tournament country uses a searchable country list (type to search).
5. Upcoming: Admin/Organizer who manages the tournament gets EDIT + DELETE.
6. Ongoing: no tournament EDIT button; Admin/Organizer gets Live Social Media Link add/update.
7. Finished: no tournament EDIT button; Admin/Organizer gets ADD RESULT or EDIT RESULT.
8. Player can join Upcoming tournaments only.
9. Existing Supabase tournament tables are reused. No new tables are required.
10. Result save replaces the tournament's existing result rows so it works with the current
    unique constraint on (tournament_id, position).

Run:
cd /d "D:\Gateball Lovers\web"
python app.py

Open:
http://127.0.0.1:5000

After replacing files, press Ctrl+F5 in the browser.


MESSAGE BOARD UPDATE
---------------------
The dashboard now connects the Message Board to public.community_messages.
Admin and Organizer users can add messages. Admin can edit/delete any message.
Organizer can edit/delete their own messages. Players can only read active messages.

IMPORTANT: Run message_board_update_policy.sql once in the Supabase SQL Editor before testing Edit.
The SQL does not create a new table; it updates policies for the existing community_messages table.


CHAT PAGE UPDATE
================
The Chat page now uses the existing Supabase tables:
- public.direct_messages
- public.community_group_messages

Features:
- Individual/private chat
- Global community group chat
- Supabase Realtime incoming messages
- Mobile-friendly chat bubbles
- Member search
- Unread badges on the Chat member list (stored locally in the browser)
- Enter sends a message; Shift+Enter makes a new line

Before testing Chat, run chat_permissions_realtime.sql once in Supabase SQL Editor.
This SQL does not create new chat tables.
