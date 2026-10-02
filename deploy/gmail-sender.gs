/**
 * PoliglotAi: sends the site's emails (registration codes, password resets) from your own Gmail.
 *
 * Setup (5 minutes, see README "Почта через Gmail без SMTP"):
 * 1. script.google.com → New project → replace everything with this file.
 * 2. Put your own long random secret below (the same value goes to GMAIL_SCRIPT_SECRET on the server).
 * 3. Deploy → New deployment → type "Web app" → Execute as: Me → Who has access: Anyone → Deploy,
 *    allow access to Gmail when Google asks.
 * 4. Copy the Web app URL (…/exec) to GMAIL_SCRIPT_URL on the server.
 */
const SECRET = 'PUT-YOUR-SECRET-HERE';

function doPost(e) {
  let data;
  try {
    data = JSON.parse(e.postData.contents);
  } catch (err) {
    return reply({ ok: false, error: 'bad request' });
  }
  if (SECRET === 'PUT-YOUR-SECRET-HERE' || data.secret !== SECRET) {
    return reply({ ok: false, error: 'wrong secret' });
  }
  MailApp.sendEmail({
    to: data.to,
    subject: data.subject,
    body: data.body,
    name: data.name || 'PoliglotAi',
  });
  return reply({ ok: true, left_today: MailApp.getRemainingDailyQuota() });
}

function reply(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
