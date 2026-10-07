# Wedding invitation — handoff

Live (GitHub Pages, branch **`golden`**, folder `/docs`), two versions of one invitation:
- **Relatives:** https://ash-z.github.io/susmita-weds-ashish/ (`docs/index.html`)
- **Friends:** https://ash-z.github.io/susmita-weds-ashish/friends/ (`docs/friends/index.html`): the same, plus the day-before page

Both pages are **generated**: edit the files here, then rebuild:

```sh
cd invite-src && npm install && python3 build.py          # -> ../docs/{,friends/}index.html, build/artifact{,-dev}{,-friends}.html
node og.mjs "$PWD/../docs/index.html" /tmp/og.png         # link-preview image; convert to ../docs/og.jpg
```

| File | What it holds |
|---|---|
| `style.html` | `<title>`, font link, all CSS. Palettes are tokens: ivory = light, jewel = dark |
| `body.html` | all markup: opening screen, the screens, tab bar; `<!--friends-->` blocks are friends-only |
| `app.js` | `CONFIG` at the top (photos, share URL), then palette, particles, tilt, opening, tabs, photo deck, countdowns, blessings, the three.js sea |
| `three-entry.js` | the three.js symbols esbuild keeps; add to it if `app.js` needs more |

## Golden and dev
- The GitHub repository was renamed `myapp` -> `susmita-weds-ashish` (Sept 2026) for a nicer link; the built-in
  address (share button, link preview) lives in `build.py` (`url`) and `app.js` (`CONFIG.shareUrl`).
- **`golden`** is what guests see. GitHub Pages serves it; nothing is committed to it directly.
  `golden-v1` (commit `4bcc0d7`) is the version first shared with guests.
- **`claude/add-threejs-library-ogt1s7`** is where work happens. Its previews are the dev artifacts
  (`build/artifact-dev.html`, `build/artifact-dev-friends.html` and `build/artifact-dev-groom.html` (https://claude.ai/artifact/3h5V4rixSjAEg7Jpar1VW3), marked DEV); the golden preview artifact is `build/artifact.html`.
- **Promote** only when the couple says so, after checking the dev preview on a phone:
  ```sh
  git checkout golden && git merge --ff-only claude/add-threejs-library-ogt1s7 && git push origin golden
  git checkout claude/add-threejs-library-ogt1s7
  ```
  Pages redeploys in about a minute. To roll back, reset `golden` to the previous good commit and push.

## Locked decisions
- Names: **Sai Susmita** in formal places (opening screen, hero, families, closing, title, previews); **Susmita** in casual ones (photo deck). The woman is always named first.
- Two events for everyone: **sumuhurtam** Thu 29 Oct 2026 **7:31 PM**, **Hotel Ambica Sea Green** (ticket heading) with **'Marina' Banquet Hall** as the subheading (`.t-hall`, gold), Beach Road, Visakhapatnam;
  reception Sun 1 Nov 2026 **12:00 PM onwards** (moved from 11 AM on 29 Sep), Hotel Tulip Grand, **'Vedha'** (the hall, added 5 Oct) **· 5th floor**, Annojiguda, Hyderabad
  (hall name not known yet; add it next to the floor when the couple sends it). Directions: the couple's pin
  https://maps.app.goo.gl/9DuCbhDxaaxrSeXr5. Wedding Directions: the couple's pin for Marina Banquet Hall,
  https://maps.app.goo.gl/AhTU2qBLJbRZLm4s6.
- English invitation wording (the couple chose it, 29 Sep): cover shows "Wedding Invitation" under శుభలేఖ; the first
  page reads "Together with our families, we invite you to celebrate the wedding of" above the names.
- **Friends only**, Wed 28 Oct 2026: Haldi & Pellikuturu 9 AM onwards · Mehendi 5 PM onwards (changed 28 Sep from
  Haldi 9:30 · Pellikuturu 11:30 · Mehendi & Sangeet 5:30 onwards; the couple's update named only Mehendi for the evening).
  All at Home, 9-6-93/3, Sivajipalem, Opp. Sivaji Park, Visakhapatnam. These must never appear in the relatives' version. It is the only difference between the two.
- Type: **Alex Brush** (the couple's names only) / **Tiro Telugu** (headings, ticket dates, the closing line; its Latin is
  drawn to sit with Telugu script) / Marcellus (times, venues) / Karla (body, labels) / Noto Sans Telugu (Telugu labels).
  The couple chose this pairing from six traditional options; generic serifs (Cormorant, Playfair, Cinzel, Lora…) were rejected
  as not matching the page. Palettes ivory + jewel, toggle top-right. Always opens in Ivory (the page is marked `data-theme="light"` from the
  start, so dark-mode phones do not flash Jewel); Jewel only when the guest taps it, remembered per phone.
- **Readability comes first** (the couple asked for it): no text below 12px (tab labels excepted, 9.5–12px by width),
  small capitals tracked no wider than .12em, body text regular weight, and light-theme gold/grey text at ≥4.5:1
  (`--gold:#8A6420`, `--muted:#6B5B47`). Italiana, the first display face, was too thin to read and was dropped; Cormorant Garamond after it didn't suit.
  Short screens (≤740px tall) get a compact layout (less spacing, smaller ornaments) so the text doesn't shrink.
- three.js is **inlined**, never loaded from a CDN (a CDN load silently failed before).
- No copy the couple did not supply. Keep it plain; no invented backstory.
- **Telugu: natural words only**, one small label per page, never a word-for-word gloss that no Telugu card would use.
  The couple rejected made-up labels (మీ రాక, పెద్దలు, వధూవరులు, వివాహం as a ticket tag, the "&" signature). In use now:
  ॥ శ్రీ గణేశాయ నమః ॥ and శుభలేఖ (opening screen, Invite) · సుస్మిత / ఆశిష్ (photo captions) · వివాహ ముహూర్తం (Wedding) ·
  రిసెప్షన్ (Reception; the couple chose it over the brief's ఆశీర్వచనం) · మీరు వస్తున్నారా? (RSVP) · ఆశీస్సులతో (Blessings) · అక్షింతలు (the note under Shower akshintalu).
  The Us page has no Telugu label.
- No framed oval portraits side by side — in India that reads as a memorial photo. Photos live in the swipeable deck.
- No algorithmic line-art or posterised portraits (tried twice, rejected).

## 3D (branch `claude/invite-3d`)
Live (promoted to dev and golden on 7 Oct, at the couple's request): the envelope as page one, the letter that
becomes the cover (page two), and the shadows on every page, all below. Further 3D work continues on the branch.
Plan after researching 3D sites (7 Oct), in order: A light that moves with the phone; B photos with real depth
(depth maps); C a real 3D envelope and petals in WebGL; D one continuous 3D world; E a scanned real place.
- **A, the light (7 Oct, on the branch):** LIGHT in app.js replaces the old TILT. One light glides toward its target
  (10% a frame) and writes --fx/--fy (-1..1), --rx/--ry (lean in degrees) and --tilt (the lean as a rotate value) on
  the lit things that are showing: the envelope, the cover's photograph, the photo deck, the tickets. They lean with
  it. It follows the phone's tilt only where that needs no permission (Android); **the invitation never asks for a
  permission** (the couple's rule, 7 Oct), so on iPhones, where tilt needs DeviceOrientationEvent.requestPermission,
  it follows the finger while it touches the screen and settles back when it lifts; the mouse on a computer. The
  tickets now really lean: their old tilt transform was always overridden by the drift-in on arrival (.reveal.in),
  so they use `rotate`, in their wrap's perspective. Gold numbers and the cover's names stand proud (a light edge, a
  soft shadow). Tried and taken out the same day: sliding sheens/glints across the cards and photos (the old faint
  ticket foil too): "the glint in the middle looks very fake". Reduce motion: no tilt.

## Three invitations
- **Relatives** `/`, **Friends** `/friends/` (adds the 28 Oct page), and **Groom's side** `/bhimanpalliwar/` (added 2 Oct
  for the groom's family): the relatives' invitation with Ashish named first everywhere: cover and first-page names,
  page title and link preview, share text and link, his photo before hers, captions, calendar titles, the groom's
  parents before the bride's on Blessings, and the closing names. build.py makes it from the relatives' page with
  `groom_first()` (each swap asserts it found its text, so a wording change there fails the build loudly instead of
  leaving a half-swapped page). It plays the relatives' song. `/Bhimanpalliwar/` (capital B) forwards to it.
  Its RSVPs send `invite: "groom"`; the script writes "Groom side" in the Invite column (Code.gs from 2 Oct; an older
  deployed script writes "Relatives"). The Totals tab's per-link rows count only Relatives and Friends.

## Posters
Each invitation also has a poster: https://susmitawedsashish.in/poster/, /friends/poster/ and /bhimanpalliwar/poster/
(added 5 Oct). Each folder holds `poster.svg` (self-contained: art, photo and font subsets embedded), `poster.png`
(1620px wide, for WhatsApp and printing; phones don't preview SVG) and `index.html` (the poster with Save / Share /
Open invitation). The poster: toranam with Ganesha, ॥ శ్రీ గణేశాయ నమః ॥, the cover photo in an arch, శుభలేఖ /
Wedding Invitation, "Together with our families…", the names (groom first on his side's), the friends' 28 Oct block,
wedding and reception side by side, both sets of parents, and a QR code to that invitation (checked to scan, also at
a third of the size). Made by `invite-src/poster/poster.py` (not by build.py): run it with a Python that has `segno`
when any detail changes; its wording and details are a copy of body.html's, so change both. It caches Google
Fonts subsets in `poster/fonts/` (fetches new ones only when the text changes) and renders the PNGs with
`poster/render.mjs` (node + Playwright's Chromium).

## Screens
Invite (the sea) · Us (photo deck) · Wedding · Reception · RSVP · Blessings — six tabs, each its own full screen. Both tickets carry the same days/hours/mins/secs countdown.
The friends' version adds a seventh, **Haldi** ("The day before"), between Us and Wedding: one ticket with the day's
events at **Home, 9-6-93/3, Sivajipalem, Opp. Sivaji Park, Visakhapatnam**, a countdown to the haldi, Directions (the couple's pin for
the house, https://maps.app.goo.gl/4jKmVR2unpEwwRWNA) and an all-day "Save date". A toranam hangs
along the ticket's top edge with Ganesha in its gap.

**Two versions:** anything between `<!--friends-->` and `<!--/friends-->` lines in `body.html` is only in the friends'
version (`build.py` drops it for the relatives'), and the friends' page sets `window.INVITE = "friends"`, which `app.js`
reads for its share link and the RSVP. The tab bar sizes itself to however many tabs there are.
The invitation is a **pager**: pages are stacked full-screen layers and only the active one shows (`.js` styles; without JS it degrades to one scrolling document).
- Scroll, swipe or arrow keys / Page Up/Down / Space at a page's edge turn the page. The next page rises under a row of temple arches with a gold line riding the edge (line and mask are driven from the same thread so they never drift); going back runs downward.
- **Pages never scroll.** Every page fits one screen: layouts are compact, and the FIT module in app.js scales a page's
  content as a whole (like a slide) when a small phone can't fit it — measured: no scaling on 390×844, 412×915, 430×932;
  79–87% on 375×667 and 360×640. Below 62% (a phone held sideways) the page scrolls rather than shrinking further.
- A link to `#rsvp` (or any page id) while the invitation is open turns to that page.
- The opening screen shows on every visit. Only a link that arrives with `#page` skips it (a deliberate deep link);
  the pager does not write the page into the address, so reloading always returns to the cover.
- One trackpad flick turns at most one page: input during a turn, and until it has been quiet for 250ms after it, is swallowed.
- Tab taps bloom the page open from the tab; tapping the current tab scrolls that page to its top.
- **No Next button and no "swipe up" text:** the couple had both removed; the side rail is the page-turn control.
- **Side rail** (`#rail`), fixed on the right edge: ▲ / a dot per page (current one gold) / ▼, 20px wide so it sits in
  the 28px page margin beside tickets and cards, never over them, and anchored low (just above the tab bar) so it
  sits beside the cards' plain lower half, not the ticket's tear line and notches (≥5px clear at 360–412px). The section blinks gently: ▲ and ▼ fade and nudge in turn, and a soft gold glow breathes around
  it (off under reduced motion). ▲ on the first page and ▼ on the last page go to the cover.
- **Back to the cover:** ▲ or a swipe down (or wheel/arrow up) on the first page; ▼ or a swipe up on the last page. The cover slides back down over the invitation (which resets to its first page) and
  opens again as usual (`cover.close()` in the opening module).
- **Cues:** on the cover, the arrow in "Open invitation" nudges and blinks and a gold ring pulses from the button
  (tapping the photo opens it too). The rail blinks gently. **Welcome shimmer:** when the invitation opens (or a shared
  #page link lands), a soft gold light sweeps across the tab bar three times and then it rests; the couple chose this
  over a tab bar that flashes all the time (too busy, pulls the eye off the details). All of it stops under reduced motion.
- Modules listen for `pagechange` / `pagesettle` events instead of IntersectionObserver (stacked pages all intersect the viewport). The sea renders only while its page shows.
- Tapping the sea floats a lamp only on a real tap; a swipe turns the page instead.

## Polish from the design/QA review (Sept 2026)
- Pages stay **vertically centred**. Top-aligning them (so headings sat at one height) left the Wedding and Reception
  cards at different heights with uneven space below; the couple saw it as misaligned, so it was reverted. The small
  label above each heading still takes one fixed 25px line. The photo deck grows with tall screens (up to 400px).
- The ticket's foil sheen is a plain overlay: with `mix-blend-mode:soft-light` inside the tilting card, Android Chrome
  drew it in hard-edged bright tiles (seen across the Save date button in the Jewel theme).
- Every content page (Us, Wedding, Reception, RSVP, Blessings: class `garland` on the section) hangs the same toranam
  along its top, Ganesha in its gap, 460px wide on wide screens. The friends' day-before page is the exception: it
  already hangs one across its ticket. Corner florals (`.t-flora`, the corner art): all four corners of the reception
  ticket; only the bottom two on the wedding ticket and the RSVP card, whose tops carry the gopuram and the diya
  (four corners there looked crowded).
- From 700px wide, every top toranam (opening screen, first page, Blessings) is 460px and the same art repeats outward to both edges as a `.crown::before` background (`--toranam-img`, set in app.js), masked off behind the centre one so its sway never doubles. (It was one 900px garland on the first two, which looked stretched on laptops.) `--crown` sets that width: 100vw on phones, 460px from 700px. Phones are unchanged.
- Photo deck: swipe left = next photo, swipe right = back (the previous one slides in from the left); tap = next.
- Telugu labels 15.5px (were 13.5px) and marked `lang="te"`. Light gold `#826019` (≥4.6:1 on every page background);
  Jewel accent `#D0707A` (5.6:1).
- Short screens: cover corner florals 74px so they clear "Open invitation"; the 28 Oct ticket shows "Wednesday" at
  full size beside the date when the time line is hidden. The compact layout also serves wide-but-short screens
  (laptops ≤900px tall), so Blessings no longer shrinks to ~10px text there.
- Known and accepted: while no song is in `docs/music/`, each load makes three 404 requests (song.mp3/.m4a/.wav) —
  the price of "drop a file in, no rebuild".

## Blessings: the two families
The bride's and groom's parents sit in two mirrored columns with a gold rule between. Their three lines share rows
across the columns (CSS subgrid), both sides break at the same places ("Parents of / the bride", "Chandrika & /
Srinivasulu Gorantla"), the children's names sit on their own line, and the parents' names scale with the screen so
"Suresh Bhimanpalliwar" (the longest line) always fits. Checked identical line-for-line from 360px to desktop.

## Address: susmitawedsashish.in
The invitations live at **https://susmitawedsashish.in/** (relatives) and **https://susmitawedsashish.in/friends/**.
The domain was bought at Hostinger and points at GitHub Pages with Hostinger DNS records: four A records for `@`
(185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153) and a CNAME `www` -> `ash-z.github.io`.
`docs/CNAME` (one line: the domain) tells Pages to serve it there, and the old github.io address redirects to it.
Keep that file on golden; without it, Pages drops the domain. Live since 28 Sep 2026: DNS check passed and
Enforce HTTPS is on (the first hour showed a certificate warning until GitHub issued it). The share button (`CONFIG.shareUrl` in app.js) and
the link preview (`url` in build.py: og:url, og:image) use this address.

## Cloudflare (backup address)
The same site is also served by Cloudflare Workers from `golden`: `wrangler.jsonc` at the repo root tells
`npx wrangler deploy` to publish `docs/` as static assets. In the Cloudflare project (name `susmita-weds-ashish`):
production branch `golden`, build command none, deploy command `npx wrangler deploy`, root `/`. Every promote to
golden redeploys it. Keep it: it is the backup for guests whose office filter blocks the new domain (corporate
filters block newly registered domains for about 30 days). Confirmed working 28 Sep 2026:
https://susmita-weds-ashish.ashishbhimanpalliwar.workers.dev/ and .../friends/.

## Music
Each invitation has **its own song** in **`docs/music/`**: `relatives.mp3` and `friends.mp3` (or `.m4a` / `.wav`); see the
README there. **Both invitations now play the same song** (two identical files; git stores it once): an audio clip
the couple sent on 29 Sep (an Instagram export, 0:54), whole, as is: loudnorm -14 LUFS, 1.5 s fade-in, 3 s fade-out so
the loop flows, 128 kbps mp3 (0.9 MB). Command: `ffmpeg -i <upload>.mp3 -af
"loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=1.5,afade=t=out:st=51.5:d=3" -ar 44100 -b:a 128k friends.mp3`.
Before it: the flute version of "Moh Moh Ke Dhaage" (Dum Laga Ke Haisha), 0:56 to 1:43, same treatment.
Earlier friends' songs, all in git history: "Ramasamyku thottam undu" (a76ad54), then "Pehli Nazar Mein" in a
slow-lounge treatment, with the vocals turned down, then with the singing replaced by synthesised violins
(scripts in `invite-src/music-tools/`).
The pages point at that folder, so a file uploaded there plays without a rebuild; the artifact previews embed it
(rebuild after adding one). It starts when a guest taps "Open invitation" (phones need a tap before sound), loops,
pauses when the page is hidden, and the speaker button next to Ivory/Jewel pauses/resumes it (remembered per phone).
With no file the button stays hidden and the page is silent. Copyrighted film songs on a public page can draw a
takedown; that's the couple's call.

## RSVP
`rsvp/Code.gs` is a Google Apps Script web app over the couple's Google Sheet. Setup steps: `rsvp/SETUP.md`.
Put the deployed `/exec` URL in `CONFIG.rsvp.endpoint` (app.js) and rebuild; until then the form says RSVPs open soon.
- Guests give a full name (first + last required), then answer the wedding and the reception separately: Attending / Can't make it, with a separate party size (1–10) for each. Both must be answered.
- Sheet columns: Updated, Token, Full name, Wedding, Wedding guests, Reception, Reception guests, Invite (Friends or Relatives: which link they answered from). Both versions share one sheet and one guest list.
- **No guest list on the page** (the couple's call): after sending, a guest sees only "Thank you, <first name> /
  Your details are saved." with Change my RSVP / RSVP for someone else. Names and counts live only in the sheet.
- Each phone keeps a token in localStorage; answering again updates the same sheet row.
- The script answers only `{ok:true, akshi:N}`: no names or head counts ever leave the sheet, even via its /exec link.
- Guards: honeypot field, token and length validation, names can't become sheet formulas, LockService around writes.
- Tested by running Code.gs in Node with stand-ins for the Google services (upsert, validation, formula guard, honeypot) and a full browser flow against it. Not yet tested against a real Apps Script deployment.
- The claude.ai artifact preview blocks outside requests, so RSVP only works on GitHub Pages.
- The sheet also has a **Totals** tab (built by the script): replies, per event replies attending / people coming /
  can't make it, replies per link, and the shared akshintalu count. Formulas count on their own; delete the tab to
  rebuild it. Don't rename the RSVPs tab (the script would start a new one).
- **Akshintalu is one shared count** for all guests: taps are sent in batches (≤50 per request) to the script, which keeps
  the total in Script Properties and in Totals!B11; the page shows "Blessings from everyone so far · N" (this phone's own count, "Your blessings · n", when the script can't be reached). With an old
  script or offline it falls back to this phone's own count.
  A batch is never re-sent (fixed 29 Sep): before, a batch whose reply the phone couldn't read (the guest switched
  apps, or the connection dropped) was sent again although the script had already counted it, so the total ran ahead
  of the real taps (a test: 12 taps counted as 17). Now a truly lost batch is simply not counted. Every tap still
  counts, with no per-phone limit (the couple's choice).
- While typing a name (phone keyboard up) the page keeps full size and scrolls, the tab bar and rail step aside,
  and pages don't turn (`html.typing`). The guest-list sheet keeps keyboard focus inside while open.
- While `CONFIG.rsvp.endpoint` is null the card says "RSVPs open very soon — please check back." up front and the form
  is dimmed and inert (guests used to fill it in and only then learn nothing was saved).

## Photographs
The couple's photos are in `photos/` (phone screenshots, ~1200px wide). `photos_process.py` crops each to a 4:5 card
(crops chosen by eye to frame faces and drop relatives at the edges) and writes `photos/out/*.webp` at 800×1000.
Deck order: laughing together (lead, captioned) · Susmita · Ashish · seated portrait · the ring. (The standing-with-garlands photo was removed at the couple's request; its source screenshot is still in `photos/`.)
On GitHub Pages the photos are separate files in `docs/photos/` (the page stays ~1.1MB); the artifact embeds them.
To add or reorder: add the file to `photos/`, add a line to `DECK` in `photos_process.py`, add a `<figure>` and a dot in
`body.html`, then run `photos_process.py` and `build.py`. The deck shows three cards in its stack at a time.

## Illustrations (from the couple's Canva)
All art lives in `art/` (WebP for the build, PNG lossless masters) and is embedded once in the page as `window.ART`;
every `<img data-art="name">` shares it. Ganesha is a CSS mask (`--ganesha-img`) so it takes the theme colour.

| Art | Used on |
|---|---|
| `toranam` (mango leaves, marigold, jasmine, brass bells) | top of the opening screen, the sea, and Blessings; Ganesha hangs in its centre gap |
| `ganesha` (line art; Canva stock element "lord ganesha", from the engagement invitation) | centre of the toranam on the opening screen and the sea |
| `couple` (bride and groom holding hands) | **retired** — its garland on the bride was drawn wrong (strands hanging like a stole). The opening screen now shows the couple's seated portrait (`photos/out/cover.webp`) in a temple-arch window before the kolam |
| `gopuram` | rising from the wedding ticket |
| `toranam` + `ganesha` (again) | hung along the top of the friends' day-before ticket |
| `corner-left`, `corner-right` | opening screen bottom corners; reception ticket top corners (flipped) |
| `diya` (with sprig) | RSVP card corner |
| `peacock` | Blessings, a facing pair |

**How they were extracted** (this environment blocks Canva's download host, `export-download.canva.com`):
each illustration was placed alone on a solid magenta page in a workbench copy (`DAHV9YJ2Iq0`) of the art sheets, each
page copied out as its own one-page design (Canva only stores previews for page 1), and the stored preview's S3 copy
downloaded. `art_process.py urls.json` keys out the magenta (unmixing it from soft edges), stitches tiles (the couple
is 2 tiles, the toranam 3) and trims. The source images are small (the peacock is 277×540), so the previews lose nothing.
The toranam's big centre flower lived in its sheet's background image, so the garland has a gap — that is where Ganesha sits.

Licensing: the Ganesha is Canva stock content, used inside this design. Don't offer any piece as a standalone download.
Canva designs created along the way (safe to delete once happy): the workbench `DAHV9YJ2Iq0` and its 11 one-page copies;
also junk from generation: `DAHV9DpqFrs`, `DAHV9AoBxNs`, `DAHV9IZyYZ4`.

## Open items
- The "forgot him for a couple of days" joke — never confirmed as family-safe; not on the page.
- RSVP — **connected**: the couple deployed `rsvp/Code.gs` from a phone as a standalone script (script.google.com; it
  opens their sheet by id) — `CONFIG.rsvp.endpoint` is its /exec URL. If they redeploy, use Manage deployments → Edit →
  New version so the URL stays the same. The current script (Code.gs with the India-time line, on golden) is deployed:
  the /exec GET returns only {"ok":true,"akshi":N}, the Totals tab exists, and RSVPs from the live domain land in the
  sheet (checked 28 Sep 2026).
