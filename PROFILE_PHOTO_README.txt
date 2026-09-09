PROFILE PHOTO UPDATE

1. Replace your web project files with this package.
2. In Supabase SQL Editor, run profile_photo_storage.sql once.
3. Restart Flask.
4. Open Profile > Edit Profile.
5. On a mobile phone, TAKE PHOTO opens the camera; CHOOSE PHOTO opens gallery/file picker.
6. Photo uploads to the existing Supabase project and its public URL is saved in profiles.photo_url when SAVE CHANGES is pressed.

No new database table is created. The only new Supabase resource is the Storage bucket profile-photos.
