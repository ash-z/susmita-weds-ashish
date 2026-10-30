# Turning on RSVPs (about 5 minutes)

1. Create a new Google Sheet, e.g. **Wedding RSVPs**. Leave it empty.
2. In the sheet: **Extensions → Apps Script**. Delete whatever is in the editor, paste all of `Code.gs`, and click **Save**.
3. Click **Deploy → New deployment**. Click the gear next to "Select type" and choose **Web app**.
   - Execute as: **Me**
   - Who has access: **Anyone**
4. Click **Deploy**, then **Authorize access** and allow it. (Google warns that the app isn't verified — it's your own script; choose *Advanced → Go to … (unsafe)*.)
5. Copy the **Web app URL** (it ends in `/exec`) and set it as `CONFIG.rsvp.endpoint` in `invite-src/app.js`, then rebuild — or just send the URL to Claude.

Responses appear in a tab called **RSVPs**: updated time, full name, coming yes/no, which events, party size.
Guests who answer again from the same phone update their own row instead of adding a new one.

If you ever edit the script, use **Deploy → Manage deployments → Edit → Version: New version** so the URL stays the same.
