// RSVP backend for the Sai Susmita & Ashish invitation. Setup: invite-src/rsvp/SETUP.md.
// Each guest answers the wedding and the reception separately, with a party size for each. Everything stays in
// the sheet: the invitation is only told that a reply was saved (and the shared akshintalu count), never any
// names or numbers of guests, so opening this script's link shows nothing about who is coming.
// (Line comments only: pasted on a phone, the editor mangles block comments.)

var SHEET = 'RSVPs';
// The couple's spreadsheet. A script made from the sheet (Extensions -> Apps Script) uses that sheet; a script made
// on its own at script.google.com (e.g. from a phone) has no sheet of its own, so it opens this one by its id.
var SPREADSHEET_ID = '1hA_KvHGzC9amlnnR008L8vf2evqOwqZF6R03BTCU0m4';
var HEADERS = ['Updated', 'Token', 'Full name', 'Wedding', 'Wedding guests', 'Reception', 'Reception guests', 'Invite'];

var TOTALS = 'Totals';

function book_() {
  return SpreadsheetApp.getActiveSpreadsheet() || SpreadsheetApp.openById(SPREADSHEET_ID);
}

function sheet_() {
  var ss = book_();
  // times in the Updated column show in India time (a new sheet can default to US Pacific)
  if (ss.getSpreadsheetTimeZone() !== 'Asia/Kolkata') ss.setSpreadsheetTimeZone('Asia/Kolkata');
  var sh = ss.getSheetByName(SHEET);
  if (!sh) {
    sh = ss.insertSheet(SHEET);
    sh.appendRow(HEADERS);
    sh.setFrozenRows(1);
  }
  totals_(ss);
  return sh;
}

function rows_(sh) {
  var n = sh.getLastRow() - 1;
  return n > 0 ? sh.getRange(2, 1, n, HEADERS.length).getValues() : [];
}

// A Totals tab the couple can glance at. Its formulas keep counting on their own as replies arrive; the
// akshintalu count (row 11) is written by the script. Delete the tab to have it rebuilt.
function totals_(ss) {
  var t = ss.getSheetByName(TOTALS);
  if (t) return t;
  t = ss.insertSheet(TOTALS);
  var r = "'" + SHEET + "'!";
  t.getRange(1, 1, 11, 2).setValues([
    ['', 'Count'],
    ['Replies', '=COUNTA(' + r + 'B2:B)'],
    ['Wedding: replies attending', '=COUNTIF(' + r + 'D2:D,"Yes")'],
    ['Wedding: people coming', '=SUMIF(' + r + 'D2:D,"Yes",' + r + 'E2:E)'],
    ['Wedding: can\'t make it', '=COUNTIF(' + r + 'D2:D,"No")'],
    ['Reception: replies attending', '=COUNTIF(' + r + 'F2:F,"Yes")'],
    ['Reception: people coming', '=SUMIF(' + r + 'F2:F,"Yes",' + r + 'G2:G)'],
    ['Reception: can\'t make it', '=COUNTIF(' + r + 'F2:F,"No")'],
    ['Replies from the Relatives link', '=COUNTIF(' + r + 'H2:H,"Relatives")'],
    ['Replies from the Friends link', '=COUNTIF(' + r + 'H2:H,"Friends")'],
    ['Akshintalu showered (all guests)', akshi_()]
  ]);
  t.getRange(1, 1, 1, 2).setFontWeight('bold');
  t.setColumnWidth(1, 260);
  return t;
}

// Akshintalu: one shared count of every handful showered, by every guest
function akshi_() {
  return Number(PropertiesService.getScriptProperties().getProperty('akshi')) || 0;
}

// What anyone may see: that it worked, and the shared akshintalu count
function summary_() {
  return { ok: true, akshi: akshi_() };
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function doGet() {
  sheet_();
  return json_(summary_());
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var d = {};
    try { d = JSON.parse((e && e.postData && e.postData.contents) || '{}'); } catch (err) {}
    if (d.website) { sheet_(); return json_(summary_()); }                            // bots fill the hidden field; store nothing

    if (d.type === 'akshi') {                                                   // a guest showered akshintalu
      var add = Math.min(50, Math.max(1, parseInt(d.n, 10) || 1));
      var total = akshi_() + add;
      PropertiesService.getScriptProperties().setProperty('akshi', String(total));
      sheet_();
      book_().getSheetByName(TOTALS).getRange(11, 2).setValue(total);
      return json_({ ok: true, akshi: total });
    }

    var token = String(d.token || '');
    var name = String(d.name || '').replace(/\s+/g, ' ').trim().slice(0, 80);
    if (!/^[A-Za-z0-9-]{8,48}$/.test(token) || name.length < 2) return json_({ ok: false, error: 'invalid' });
    if (/^[=+\-@]/.test(name)) name = "'" + name;                                // never let a name become a formula

    var w = d.wedding || {}, r = d.reception || {};
    if (typeof w.coming !== 'boolean' || typeof r.coming !== 'boolean') return json_({ ok: false, error: 'answer both' });
    var party = function (x) { return x.coming ? Math.min(10, Math.max(1, parseInt(x.party, 10) || 1)) : 0; };

    var sh = sheet_();
    var row = [new Date(), token, name, w.coming ? 'Yes' : 'No', party(w), r.coming ? 'Yes' : 'No', party(r),
               d.invite === 'friends' ? 'Friends' : d.invite === 'groom' ? 'Groom side' : 'Relatives'];   // which link they answered from
    var tokens = rows_(sh).map(function (existing) { return existing[1]; });
    var i = tokens.indexOf(token);
    if (i >= 0) sh.getRange(i + 2, 1, 1, row.length).setValues([row]);         // same phone answering again
    else sh.appendRow(row);

    return json_(summary_());
  } finally {
    lock.releaseLock();
  }
}
