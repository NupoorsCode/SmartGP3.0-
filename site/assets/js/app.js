/* ============================================================================
   SmartGP — consultation, account and admin.

   These three areas stay a JavaScript app on purpose. They sit behind a login,
   hold personal health data, and are marked noindex — so there is nothing for a
   crawler to gain from them. Every page a search engine should see is static
   HTML built at deploy time instead.

   The catalogue and question set are fetched from /assets/js/data.json, which
   the build generates from the same content model as the public pages. Nothing
   here is a clinical decision: questions carry `flag` metadata that highlights
   an answer for a clinician. No rule anywhere approves or rejects a patient.
   (BR-04, FR-CON-11)
   ============================================================================ */
(function () {
  'use strict';

  var mountEl = document.getElementById('app');
  if (!mountEl) return;
  var MOUNT = mountEl.getAttribute('data-mount');

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  var money = function (n) { return '\u00a3' + Number(n).toFixed(2).replace(/\.00$/, ''); };
  var toast = function (m) { if (window.sgToast) window.sgToast(m); };

  var D = null;                                     // catalogue, once loaded
  var SEQ = 4200;
  var nextId = function (p) { return p + '-' + (++SEQ); };

  /* ------------------------------------------------------- in-memory store */
  var S = {
    user: null, role: 'Super Admin', journey: null, checkin: {},
    submissions: [], appointments: [], orders: [], sideEffects: [],
    patients: [
      { id: 'P-1041', name: 'Amara Okafor', email: 'a.okafor@example.co.uk', dob: '1988-03-12', postcode: 'M1 4BT', status: 'Booked', service: 'Mounjaro (tirzepatide)', flags: 1, submitted: '2 hours ago' },
      { id: 'P-1040', name: 'Tom Bradshaw', email: 't.bradshaw@example.co.uk', dob: '1975-11-02', postcode: 'BS3 2AA', status: 'Awaiting outcome', service: 'Wegovy (semaglutide injection)', flags: 0, submitted: 'Yesterday' },
      { id: 'P-1039', name: 'Priya Raman', email: 'p.raman@example.co.uk', dob: '1992-07-24', postcode: 'LS6 1AB', status: 'Approved', service: 'Mounjaro (tirzepatide)', flags: 0, submitted: '3 days ago' }
    ],
    enquiries: [
      { from: 'Helen Yates', subject: 'Delivery has not arrived', when: '18 minutes ago', status: 'New' },
      { from: 'Marcus Idowu', subject: 'Can I switch from Wegovy to Mounjaro?', when: '2 hours ago', status: 'New' }
    ],
    audit: []
  };

  function audit(action, entity, detail) {
    S.audit.unshift({
      at: new Date(),
      actor: S.user ? (S.user.firstName + ' ' + S.user.lastName + ' (patient)') : 'Anonymous visitor',
      action: action, entity: entity || '\u2014', detail: detail || ''
    });
  }

  /* ------------------------------------------------------------- helpers */
  function fmtDate(d, o) { return new Intl.DateTimeFormat('en-GB', o || { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }).format(d); }
  function fmtTime(d) { return new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Europe/London' }).format(d); }
  function ageFrom(dob) {
    if (!dob) return null;
    var b = new Date(dob); if (isNaN(b)) return null;
    var n = new Date(), a = n.getFullYear() - b.getFullYear(), m = n.getMonth() - b.getMonth();
    if (m < 0 || (m === 0 && n.getDate() < b.getDate())) a--;
    return a;
  }
  function bmiOf(cm, kg) {
    if (!cm || !kg) return null;
    var b = kg / Math.pow(cm / 100, 2);
    return isFinite(b) && b > 5 && b < 120 ? Math.round(b * 10) / 10 : null;
  }
  function svc(id) { for (var i = 0; i < D.services.length; i++) if (D.services[i].id === id) return D.services[i]; return null; }
  function qs(name) { return new URLSearchParams(location.search).get(name); }

  /* --------------------------------------------------------- form engine */
  function visible(f, v) {
    if (!f.showIf) return true;
    return v[f.showIf.k] === f.showIf.is;
  }
  function visibleFields(fs, v) { return fs.filter(function (f) { return visible(f, v); }); }
  function depKeys(fs) {
    var s = {}; fs.forEach(function (f) { if (f.showIf) s[f.showIf.k] = 1; }); return s;
  }

  var GP_PRACTICES = [
    { n: 'Rusholme Health Centre', t: '0161 000 0001', e: 'admin@rusholmehc.nhs.uk' },
    { n: 'Bridge Street Surgery', t: '0117 000 0002', e: 'reception@bridgestreet.nhs.uk' },
    { n: 'Headingley Medical Practice', t: '0113 000 0003', e: 'contact@headingleymp.nhs.uk' }
  ];

  function renderField(f, v) {
    var val = v[f.k], id = 'f_' + f.k, bad = v.__errors && v.__errors[f.k];
    var reqMark = f.required ? ' <span class="req" aria-hidden="true">*</span>' : '';
    var hint = f.hint ? '<p class="hint" id="' + id + '-hint">' + esc(f.hint) + '</p>' : '';
    var desc = f.hint ? ' aria-describedby="' + id + '-hint"' : '';
    var errH = bad ? '<p class="err" id="' + id + '-err">' + esc(bad) + '</p>' : '';
    var open = '<div class="field ' + (bad ? 'bad' : '') + '" data-field="' + f.k + '">';
    var close = errH + '</div>';
    var lab = '<label for="' + id + '">' + esc(f.label) + reqMark + '</label>';
    var groupLab = '<span class="field-label" id="' + id + '-lab">' + esc(f.label) + reqMark + '</span>';

    switch (f.type) {
      case 'radio':
        return open + '<fieldset><legend class="field-label" style="font-family:var(--f-body);font-size:.97rem;font-weight:600">' +
          esc(f.label) + reqMark + '</legend>' + hint +
          f.options.map(function (o) {
            return '<label class="opt ' + (val === o ? 'sel' : '') + '">' +
              '<input type="radio" name="' + f.k + '" data-k="' + f.k + '" value="' + esc(o) + '"' +
              (val === o ? ' checked' : '') + '><b>' + esc(o) + '</b></label>';
          }).join('') + '</fieldset>' + close;

      case 'checkboxes':
        var arr = Array.isArray(val) ? val : [];
        return open + '<fieldset><legend class="field-label" style="font-family:var(--f-body);font-size:.97rem;font-weight:600">' +
          esc(f.label) + reqMark + '</legend>' + hint +
          f.options.map(function (o) {
            return '<label class="opt ' + (arr.indexOf(o) > -1 ? 'sel' : '') + '">' +
              '<input type="checkbox" data-k="' + f.k + '" data-multi="1"' +
              (f.exclusive ? ' data-exclusive="' + esc(f.exclusive) + '"' : '') +
              ' value="' + esc(o) + '"' + (arr.indexOf(o) > -1 ? ' checked' : '') +
              '><b>' + esc(o) + '</b></label>';
          }).join('') + '</fieldset>' + close;

      case 'consent':
        return open + '<label class="opt ' + (val ? 'sel' : '') + '">' +
          '<input type="checkbox" data-k="' + f.k + '" data-bool="1"' + (val ? ' checked' : '') +
          '><b style="font-weight:500">' + esc(f.label) + reqMark + '</b></label>' + close;

      case 'textarea':
        return open + lab + hint + '<textarea id="' + id + '" data-k="' + f.k + '"' + desc +
          ' placeholder="' + esc(f.placeholder || '') + '">' + esc(val || '') + '</textarea>' + close;

      case 'select':
        return open + lab + hint + '<select id="' + id + '" data-k="' + f.k + '"' + desc + '>' +
          '<option value="">Please choose</option>' +
          f.options.map(function (o) { return '<option' + (val === o ? ' selected' : '') + '>' + esc(o) + '</option>'; }).join('') +
          '</select>' + close;

      case 'postcode':
        return open + lab + hint +
          '<div style="display:flex;gap:10px"><input id="' + id + '" type="text" data-k="' + f.k +
          '" value="' + esc(val || '') + '" placeholder="M1 4BT" autocomplete="postal-code" style="flex:1">' +
          '<button type="button" class="btn btn-quiet" data-act="postcode">Find address</button></div>' +
          '<p class="hint" style="margin-top:8px">UK postcodes only. Non-UK addresses cannot be accepted.</p>' + close;

      case 'gplookup':
        return open + lab + hint +
          '<div style="display:flex;gap:10px"><input id="' + id + '" type="text" data-k="' + f.k +
          '" value="' + esc(val || '') + '" placeholder="Practice name, postcode or town" style="flex:1">' +
          '<button type="button" class="btn btn-quiet" data-act="gplookup">Search</button></div>' +
          (v.__gpDetail ? '<p class="hint" style="margin-top:8px">' + esc(v.__gpDetail) + '</p>' : '') + close;

      case 'file':
        return open + groupLab + hint +
          '<div class="upload ' + (val ? 'has' : '') + '">' +
          (val
            ? '<span class="upload-thumb">' + esc(String(val).split('.').pop().toUpperCase()) + '</span>' +
              '<div style="flex:1"><b>' + esc(val) + '</b><p class="hint" style="margin:2px 0 0">Encrypted private storage. Deleted 30 days after verification.</p></div>' +
              '<button type="button" class="btn btn-ghost btn-sm" data-act="upload" data-k="' + f.k + '">Replace</button>'
            : '<p style="margin:0 0 12px" class="muted">JPG, PNG or PDF, up to 10&nbsp;MB. Make sure all four corners are visible.</p>' +
              '<button type="button" class="btn btn-quiet" data-act="upload" data-k="' + f.k + '">Choose file</button>') +
          '</div>' + close;

      case 'number':
        return open + lab + hint + '<input id="' + id + '" type="number" inputmode="decimal" data-k="' + f.k +
          '" value="' + esc(val || '') + '"' + desc + '>' + close;

      default:
        var t = f.type === 'date' ? 'date' : f.type === 'email' ? 'email' : f.type === 'tel' ? 'tel' : f.type === 'password' ? 'password' : 'text';
        return open + lab + hint + '<input id="' + id + '" type="' + t + '" data-k="' + f.k +
          '" value="' + esc(val || '') + '" placeholder="' + esc(f.placeholder || '') + '"' + desc + '>' + close;
    }
  }

  function renderFields(fs, v) {
    var vis = visibleFields(fs, v), out = '', buf = [];
    function flush() {
      if (!buf.length) return;
      out += buf.length > 1 ? '<div class="row2">' + buf.join('') + '</div>' : buf[0];
      buf = [];
    }
    vis.forEach(function (f) {
      if (f.half) { buf.push(renderField(f, v)); if (buf.length === 2) flush(); }
      else { flush(); out += renderField(f, v); }
    });
    flush();
    return out;
  }

  function validate(fs, v) {
    var errs = {};
    visibleFields(fs, v).forEach(function (f) {
      if (!f.required) return;
      var val = v[f.k];
      var empty = val === undefined || val === null || val === '' ||
        (Array.isArray(val) && !val.length) || (f.type === 'consent' && !val);
      if (empty) errs[f.k] = f.type === 'consent' ? 'You need to tick this to continue.' : 'This answer is needed before you can continue.';
      else if (f.type === 'email' && !/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(val)) errs[f.k] = 'Enter an email address in the format name@example.co.uk';
      else if (f.type === 'tel' && !/^0\d[\d\s]{8,12}$/.test(String(val))) errs[f.k] = 'Enter a UK mobile number, for example 07700 900000';
      else if (f.type === 'postcode' && !/^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$/i.test(String(val).trim())) errs[f.k] = 'Enter a full UK postcode, for example M1 4BT';
    });
    return errs;
  }

  function flagsFor(fs, v) {
    var out = [];
    visibleFields(fs, v).forEach(function (f) {
      if (!f.flag) return;
      var val = v[f.k], hit = false;
      if (f.flag.when) hit = f.flag.when.indexOf(val) > -1;
      if (f.flag.whenAnyExcept) hit = Array.isArray(val) && val.some(function (x) { return x !== f.flag.whenAnyExcept; });
      if (hit) out.push({ k: f.k, label: f.label, answer: Array.isArray(val) ? val.join(', ') : val, level: f.flag.level, note: f.flag.note });
    });
    return out;
  }

  function collect(root, v) {
    $$('[data-k]', root).forEach(function (el) {
      var k = el.getAttribute('data-k');
      if (el.type === 'radio') { if (el.checked) v[k] = el.value; }
      else if (el.dataset.multi) {
        var arr = Array.isArray(v[k]) ? v[k].slice() : [], i = arr.indexOf(el.value);
        if (el.checked && i === -1) arr.push(el.value);
        if (!el.checked && i > -1) arr.splice(i, 1);
        v[k] = arr;
      } else if (el.dataset.bool) v[k] = !!el.checked;
      else if (el.type !== 'checkbox') v[k] = el.value;
    });
    return v;
  }

  /* ------------------------------------------------------------- routing */
  var ROUTES = [];
  function route(p, fn) { ROUTES.push({ p: p, fn: fn }); }
  function go(h) { location.hash = h; }
  function path() { var h = location.hash.replace(/^#/, ''); return h && h !== '/' ? h : '/'; }

  function resolve(pt) {
    for (var i = 0; i < ROUTES.length; i++) {
      var r = ROUTES[i];
      if (r.p === pt) return { fn: r.fn, args: [] };
      if (r.p.indexOf(':') > -1) {
        var pp = r.p.split('/'), ap = pt.split('/');
        if (pp.length !== ap.length) continue;
        var args = [], ok = true;
        for (var j = 0; j < pp.length; j++) {
          if (pp[j][0] === ':') args.push(decodeURIComponent(ap[j]));
          else if (pp[j] !== ap[j]) { ok = false; break; }
        }
        if (ok) return { fn: r.fn, args: args };
      }
    }
    return null;
  }

  function render() {
    var m = resolve(path());
    mountEl.innerHTML = m ? m.fn.apply(null, m.args) : defaultRoute();
    if (m && m.fn.after) m.fn.after();
    var h1 = mountEl.querySelector('h1');
    if (h1) { document.title = h1.textContent.trim() + ' | SmartGP'; }
    window.scrollTo(0, 0);
  }

  function defaultRoute() {
    if (MOUNT === 'account') return pageDashboard();
    if (MOUNT === 'admin') return adminHome();
    return stepAge();
  }

  /* ============================== JOURNEY ============================== */
  var STAGES = [
    { id: 'age', label: 'Your age', route: '#/' },
    { id: 'status', label: 'Where you are now', route: '#/status' },
    { id: 'select', label: 'Choose a treatment', route: '#/select' },
    { id: 'info', label: 'About the treatment', route: '#/info', branch: true },
    { id: 'expect', label: 'What to expect', route: '#/expect' },
    { id: 'personal', label: 'About you', route: '#/personal' },
    { id: 'bmi', label: 'Height, weight and BMI', route: '#/bmi' },
    { id: 'identity', label: 'Consent and photo ID', route: '#/identity' },
    { id: 'safety', label: 'Safety questions', route: '#/safety', branch: true },
    { id: 'gp', label: 'Your GP', route: '#/gp' },
    { id: 'confirm', label: 'Confirm and agree', route: '#/confirm' },
    { id: 'account', label: 'Create your account', route: '#/account' },
    { id: 'booking', label: 'Book your appointment', route: '#/booking' }
  ];
  var FIELDS = [], DEPS = {};

  function J() {
    if (!S.journey) S.journey = { serviceId: qs('treatment') || null, answers: {}, furthest: 0 };
    return S.journey;
  }
  function jSvc() { return svc(J().serviceId); }

  function shell(stageId, inner) {
    var idx = 0;
    STAGES.forEach(function (s, i) { if (s.id === stageId) idx = i; });
    J().furthest = Math.max(J().furthest, idx);
    var pct = Math.round(((idx + 1) / STAGES.length) * 100);
    var items = STAGES.map(function (s, i) {
      var cls = (i < idx ? 'done ' : '') + (i === idx ? 'now ' : '') + (s.branch ? 'branch' : '');
      var txt = (i <= J().furthest && i !== idx)
        ? '<a href="' + s.route + '" style="color:inherit">' + esc(s.label) + '</a>'
        : esc(s.label);
      return '<li class="rail-item ' + cls + '"><span class="rail-dot" aria-hidden="true">' +
        (i < idx ? '\u2713' : i + 1) + '</span><span class="rail-txt">' + txt + '</span></li>';
    }).join('');

    return '<div class="wrap journey">' +
      '<aside class="rail"><h2>Your consultation</h2><ol class="rail-list">' + items + '</ol>' +
      '<p class="rail-foot">Answers are saved as you go. You can close this and pick it up again.<br><br>' +
      '<a href="/support/">Need help?</a></p>' +
      '<div class="rail-mobile"><div style="display:flex;justify-content:space-between;font-size:.82rem;color:var(--ink-3)">' +
      '<span>Step ' + (idx + 1) + ' of ' + STAGES.length + '</span><span>' + pct + '%</span></div>' +
      '<div class="bar"><i style="width:' + pct + '%"></i></div>' +
      '<p style="margin:8px 0 0;font-weight:600">' + esc(STAGES[idx].label) + '</p></div></aside>' +
      '<div class="step">' + inner + '</div></div>';
  }

  function errSummary(errs) {
    var keys = Object.keys(errs || {});
    if (!keys.length) return '';
    return '<div class="formerr" role="alert" tabindex="-1" id="errsum"><b>There ' +
      (keys.length === 1 ? 'is 1 answer' : 'are ' + keys.length + ' answers') +
      ' to check before you continue</b><ul>' +
      keys.map(function (k) { return '<li>' + esc(errs[k]) + '</li>'; }).join('') + '</ul></div>';
  }

  function nav(next, back, label) {
    return '<div class="step-nav">' +
      (back ? '<a class="btn btn-ghost" href="' + back + '">Back</a>' : '') +
      '<div class="spacer"></div><button class="btn btn-solid" data-act="next" data-next="' + next + '">' +
      esc(label || 'Continue') + '</button></div>';
  }

  function emergencyPanel() {
    var e2 = D.emergency;
    return '<div class="emergency"><h2>' + esc(e2.title) + '</h2>' +
      '<p style="font-weight:600;margin:8px 0 0">' + esc(e2.lead) + '</p>' +
      '<p class="small muted" style="margin:10px 0 0">This includes, but is not limited to:</p><ul>' +
      e2.items.map(function (i) { return '<li>' + esc(i) + '</li>'; }).join('') +
      '</ul><p class="nhs">' + esc(e2.nhs) + '</p></div>';
  }

  function stepAge() {
    var j = J(), a = j.answers;
    FIELDS = [{ k: 'dob', type: 'date', label: 'What is your date of birth?', required: true, hint: 'This must match the photo ID you upload later.' }];
    DEPS = {};
    return shell('age',
      (j.furthest > 0 ? '<div class="notice notice-ok"><b>You have a consultation in progress</b>' +
        'Pick up where you left off, or start again.<div class="btnrow" style="margin-top:10px">' +
        '<a class="btn btn-solid btn-sm" href="' + STAGES[j.furthest].route + '">Resume</a>' +
        '<button class="btn btn-ghost btn-sm" data-act="restart">Start again</button></div></div>' : '') +
      emergencyPanel() +
      '<h1>First, your age</h1>' +
      '<p class="step-why">This service is for adults aged 18 or over who live in the UK. ' +
      'We ask before anything else so that nobody fills in a long form only to find they ' +
      'cannot be seen here. There is no upper age limit \u2014 your clinician reviews your ' +
      'age alongside everything else on the call.</p>' +
      errSummary(a.__errors) +
      '<form data-stepform>' + renderFields(FIELDS, a) + '</form>' +
      (j.serviceId && jSvc() ? '<p class="small muted">Continuing with <b>' + esc(jSvc().name) +
        '</b>. You can change this at the next step.</p>' : '') +
      '<div class="step-nav"><div class="spacer"></div>' +
      '<button class="btn btn-solid" data-act="agecheck">Continue</button></div>');
  }

  function pageBlocked() {
    return '<div class="wrap" style="padding:60px 0;max-width:720px">' +
      '<p class="eyebrow">We cannot continue</p>' +
      '<h1>This service is for adults aged 18 and over</h1>' +
      '<p class="lead">We have not kept any of the answers you started. Nothing has been saved against your name.</p>' +
      '<div class="card" style="margin-top:26px"><h2 style="font-family:var(--f-body);font-size:1.05rem;font-weight:700">What to do instead</h2>' +
      '<ul style="padding-left:20px;color:var(--ink-2)">' +
      '<li>Speak to your GP practice \u2014 they can refer you to NHS weight management support designed for young people.</li>' +
      '<li>Visit the NHS website for advice on healthy weight for your age.</li>' +
      '<li>If you need to talk to someone, your school nurse or GP can help.</li></ul></div>' +
      '<div class="notice notice-stop" style="margin-top:24px"><b>If you need urgent help</b>' +
      'Call NHS 111. In an emergency, call 999 or go to A&amp;E.</div>' +
      '<div class="btnrow"><a class="btn btn-ghost" href="/">Back to the homepage</a>' +
      '<a class="btn btn-quiet" href="/learn/">Read our Learn articles</a></div></div>';
  }

  function stepStatus() {
    var a = J().answers;
    FIELDS = [{ k: 'status', type: 'radio', required: true,
      label: 'Where are you with weight loss treatment right now?',
      options: ['I am new to weight loss treatment', 'I have taken it before but stopped', 'I am taking a treatment now and want to continue'] }];
    DEPS = {};
    return shell('status', '<h1>Where you are now</h1>' +
      '<p class="step-why">Your answer decides which questions you are asked. Someone already on treatment gets a short check-in rather than the full form.</p>' +
      errSummary(a.__errors) + '<form data-stepform>' + renderFields(FIELDS, a) + '</form>' +
      nav('#/select', '#/'));
  }

  function stepSelect() {
    var j = J();
    return shell('select', '<h1>Choose a treatment</h1>' +
      '<p class="step-why">Choosing here does not mean you will be prescribed it. It decides which safety questions you are asked and what the clinician discusses with you.</p>' +
      D.services.filter(function (s) { return s.published; }).map(function (s) {
        var avail = s.strengths.some(function (x) { return x.available; });
        return '<label class="opt ' + (j.serviceId === s.id ? 'sel' : '') + '" style="align-items:flex-start">' +
          '<input type="radio" name="pick" data-pick="' + s.id + '"' + (j.serviceId === s.id ? ' checked' : '') +
          (avail ? '' : ' disabled') + '><span style="flex:1"><b>' + esc(s.name) +
          (avail ? '' : ' <span class="tag tag-off">Currently unavailable</span>') + '</b>' +
          '<span>' + esc(s.strapline) + ' \u00b7 from ' + money(s.priceFrom) + ', including the consultation</span></span></label>';
      }).join('') +
      '<p class="small muted">A treatment shown as unavailable cannot be selected until stock is flagged back in by the clinic.</p>' +
      nav('#/info', '#/status'));
  }

  function stepInfo() {
    var s = jSvc();
    if (!s) return stepSelect();
    function blk(t, arr) {
      return '<h2 style="font-size:1.1rem;font-family:var(--f-body);font-weight:700;margin-top:22px">' + esc(t) +
        '</h2><ul style="padding-left:20px;color:var(--ink-2);font-size:.95rem">' +
        arr.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>';
    }
    return shell('info', '<h1>' + esc(s.name) + '</h1>' +
      '<p class="step-why">Read this before you answer any questions. It is the same information the clinician will go through with you.</p>' +
      '<p>' + esc(s.blurb) + '</p>' +
      blk('Is it suitable for me?', s.info.suitable) + blk('How do I use it?', s.info.how) +
      blk('How does it work?', s.info.works) + blk('Other important information', s.info.other) +
      '<div class="notice notice-info" style="margin-top:24px"><b>The final decision is made jointly with a clinician</b>Nothing on this page means treatment will be prescribed for you.</div>' +
      '<div class="step-nav"><a class="btn btn-ghost" href="#/select">Choose a different treatment</a>' +
      '<div class="spacer"></div><a class="btn btn-solid" href="#/expect">I have read this</a></div>');
  }

  function stepExpect() {
    var s = jSvc();
    return shell('expect', '<h1>What we are about to ask, and why</h1>' +
      '<p class="step-why">About 8 minutes. You can stop at any point and come back \u2014 nothing is lost.</p>' +
      '<div class="list" style="margin-bottom:22px">' +
      [['Who you are and where you live', 'Name, date of birth, UK address and mobile number. We check your age against your ID.'],
       ['Your height and weight', 'We calculate your BMI for you. Have a recent weight to hand.'],
       ['Photo ID', 'A passport or UK driving licence. Have it ready to photograph or upload.'],
       ['Your GP practice', 'So the clinician can write to them, if you agree to that.'],
       ['A few safety questions about ' + (s ? s.name : 'the treatment'), 'Only the things that would stop treatment outright. Everything else is discussed live.']]
        .map(function (r) { return '<div class="li"><div class="li-main"><b>' + esc(r[0]) + '</b><span>' + esc(r[1]) + '</span></div></div>'; }).join('') +
      '</div><div class="notice notice-flag"><b>Honest answers matter more than \u201cright\u201d answers</b>' +
      'Nothing you say here refuses you treatment. Answers are read by a clinician, who will ask you about anything that stands out. Leaving something out is what makes prescribing unsafe.</div>' +
      '<div class="step-nav"><a class="btn btn-ghost" href="#/info">Back</a><div class="spacer"></div>' +
      '<a class="btn btn-solid" href="#/personal">Start the questions</a></div>');
  }

  function stepPersonal() {
    var a = J().answers;
    FIELDS = D.common.personal; DEPS = depKeys(FIELDS);
    return shell('personal', '<h1>About you</h1>' +
      '<p class="step-why">These are the common preliminary questions. They are identical for every service we offer, asked once and reused if you come back for something else.</p>' +
      errSummary(a.__errors) + '<form data-stepform>' + renderFields(FIELDS, a) + '</form>' +
      nav('#/bmi', '#/expect'));
  }

  function stepBMI() {
    var a = J().answers;
    FIELDS = []; DEPS = {};
    return shell('bmi', '<h1>Your height and weight</h1>' +
      '<p class="step-why">Your BMI is calculated as you type. Your clinician will confirm your weight on the video call, or from timestamped photographs if a call is not possible \u2014 an online figure alone is not enough to prescribe from.</p>' +
      '<form data-stepform id="bmiform">' +
      '<div class="field"><span class="field-label">Height <span class="req">*</span></span>' +
      '<div class="opt-inline" style="margin-bottom:10px">' +
      '<button type="button" class="btn btn-sm ' + (a.__hUnit !== 'ft' ? 'btn-solid' : 'btn-ghost') + '" data-unit="h" data-val="cm">Centimetres</button>' +
      '<button type="button" class="btn btn-sm ' + (a.__hUnit === 'ft' ? 'btn-solid' : 'btn-ghost') + '" data-unit="h" data-val="ft">Feet and inches</button></div>' +
      (a.__hUnit === 'ft'
        ? '<div class="row2"><label class="visually-hidden" for="hFt">Feet</label><input type="number" id="hFt" placeholder="Feet" value="' + esc(a.__hFt || '') + '">' +
          '<label class="visually-hidden" for="hIn">Inches</label><input type="number" id="hIn" placeholder="Inches" value="' + esc(a.__hIn || '') + '"></div>'
        : '<label class="visually-hidden" for="hCm">Height in centimetres</label><input type="number" id="hCm" placeholder="e.g. 172" value="' + esc(a.heightCm || '') + '">') +
      '</div>' +
      '<div class="field"><span class="field-label">Weight <span class="req">*</span></span>' +
      '<div class="opt-inline" style="margin-bottom:10px">' +
      '<button type="button" class="btn btn-sm ' + (a.__wUnit !== 'st' ? 'btn-solid' : 'btn-ghost') + '" data-unit="w" data-val="kg">Kilograms</button>' +
      '<button type="button" class="btn btn-sm ' + (a.__wUnit === 'st' ? 'btn-solid' : 'btn-ghost') + '" data-unit="w" data-val="st">Stones and pounds</button></div>' +
      (a.__wUnit === 'st'
        ? '<div class="row2"><label class="visually-hidden" for="wSt">Stones</label><input type="number" id="wSt" placeholder="Stones" value="' + esc(a.__wSt || '') + '">' +
          '<label class="visually-hidden" for="wLb">Pounds</label><input type="number" id="wLb" placeholder="Pounds" value="' + esc(a.__wLb || '') + '"></div>'
        : '<label class="visually-hidden" for="wKg">Weight in kilograms</label><input type="number" id="wKg" placeholder="e.g. 96" value="' + esc(a.weightKg || '') + '">') +
      '</div></form><div id="bmiOut" aria-live="polite"></div><div id="condWrap"></div>' +
      nav('#/identity', '#/personal'));
  }

  function bmiPaint() {
    var a = J().answers, b = bmiOf(a.heightCm, a.weightKg);
    var out = $('#bmiOut'), cond = $('#condWrap');
    if (!out) return;
    if (!b) {
      out.innerHTML = '<div class="bmi"><div class="bmi-num">\u2014<small>Your BMI</small></div>' +
        '<p class="bmi-txt">Enter your height and weight and we will work it out.</p></div>';
      cond.innerHTML = ''; return;
    }
    var band = 'below the range where medical weight management is usually considered';
    if (b >= 30) band = 'in the range where medical weight management is usually considered';
    else if (b >= 27) band = 'in the range where treatment may be considered if you also have a weight-related condition';
    out.innerHTML = '<div class="bmi"><div class="bmi-num">' + b + '<small>Your BMI</small></div>' +
      '<p class="bmi-txt">That is ' + esc(band) + '. Your clinician confirms this at the appointment \u2014 BMI is a starting point, not a decision.</p></div>';

    if (b >= 25 && b < 30) {
      var sel = Array.isArray(a.conditions) ? a.conditions : [];
      cond.innerHTML = '<div class="field" data-field="conditions"><fieldset>' +
        '<legend class="field-label" style="font-family:var(--f-body);font-size:.97rem;font-weight:600">Because your BMI is between 25 and 30, please tell us whether any of these apply <span class="req">*</span></legend>' +
        '<p class="hint">A weight-related condition changes what a clinician can consider.</p>' +
        D.common.conditions.map(function (c) {
          return '<label class="opt ' + (sel.indexOf(c) > -1 ? 'sel' : '') + '">' +
            '<input type="checkbox" data-k="conditions" data-multi="1" data-exclusive="None of these" value="' +
            esc(c) + '"' + (sel.indexOf(c) > -1 ? ' checked' : '') + '><b>' + esc(c) + '</b></label>';
        }).join('') + '</fieldset></div>';
    } else cond.innerHTML = '';
  }
  stepBMI.after = bmiPaint;

  function stepIdentity() {
    var a = J().answers;
    FIELDS = D.common.consent.concat([
      { k: 'idType', type: 'radio', label: 'Which document will you upload?', options: ['UK passport', 'UK driving licence'], required: true },
      { k: 'idFile', type: 'file', label: 'Upload your photo ID', required: true, hint: 'All four corners visible, no glare, and the photograph and dates readable.' },
      { k: 'verifyMethod', type: 'radio', required: true,
        label: 'How would you like your height and weight verified?',
        options: ['On the video call with my clinician (recommended)', 'By uploading timestamped photographs instead'],
        hint: 'One of these must happen before a first supply. It is a legal requirement for weight loss medicines, not a preference.' },
      { k: 'verifyFile', type: 'file', label: 'Upload your timestamped photographs',
        showIf: { k: 'verifyMethod', is: 'By uploading timestamped photographs instead' }, required: true,
        hint: 'A photograph of you on the scales with the reading visible, and one showing your height against a measure. Both must show today\u2019s date.' }
    ]);
    DEPS = depKeys(FIELDS);
    return shell('identity', '<h1>Consent and photo ID</h1>' +
      '<p class="step-why">Your document is held in encrypted storage that only clinical staff can open, and is deleted 30 days after your identity has been confirmed. It is never used for automated face matching.</p>' +
      errSummary(a.__errors) + '<form data-stepform>' + renderFields(FIELDS, a) + '</form>' +
      nav('#/safety', '#/bmi'));
  }

  function stepSafety() {
    var s = jSvc();
    if (!s) return stepSelect();
    var a = J().answers;
    FIELDS = s.module; DEPS = depKeys(FIELDS);
    return shell('safety', '<h1>Safety questions about ' + esc(s.name) + '</h1>' +
      '<p class="step-why">This is the part of the form that changes with the treatment you chose. We only ask the things that would stop treatment outright \u2014 everything else is discussed on the call, where a clinician can follow up on what you say.</p>' +
      errSummary(a.__errors) + '<form data-stepform>' + renderFields(FIELDS, a) + '</form>' +
      '<div class="notice notice-info"><b>Answering \u201cyes\u201d does not refuse you treatment</b>It marks that answer for the clinician so they see it first. No system here approves or rejects anyone.</div>' +
      nav('#/gp', '#/identity'));
  }

  function stepGP() {
    var a = J().answers;
    FIELDS = D.common.gp; DEPS = depKeys(FIELDS);
    return shell('gp', '<h1>Your GP practice</h1>' +
      '<p class="step-why">Telling your GP keeps your medical record complete and is safer if you are prescribed something else later. You can decline and still be seen.</p>' +
      errSummary(a.__errors) + '<form data-stepform>' + renderFields(FIELDS, a) + '</form>' +
      nav('#/confirm', '#/safety'));
  }

  function stepConfirm() {
    var a = J().answers, s = jSvc(), b = bmiOf(a.heightCm, a.weightKg);
    FIELDS = [
      { k: 'cHonest', type: 'consent', required: true, label: 'I have understood the questions and answered them truthfully and completely.' },
      { k: 'cForMe', type: 'consent', required: true, label: 'This treatment is for me alone. I will not share or resell it.' },
      { k: 'cLeaflet', type: 'consent', required: true, label: 'I will read the patient information leaflet supplied with any medicine.' }
    ];
    DEPS = {};
    function row(l, v, href) {
      return '<div class="ans"><dt>' + esc(l) + '</dt><dd>' + esc(v || '\u2014') +
        (href ? ' <a class="small" href="' + href + '" style="font-weight:500">Change</a>' : '') + '</dd></div>';
    }
    return shell('confirm', '<h1>Check your answers</h1>' +
      '<p class="step-why">One last look before this goes to a clinician. Change anything that is not right.</p>' +
      '<dl style="margin:0 0 26px">' +
      row('Name', [a.title, a.firstName, a.lastName].filter(Boolean).join(' '), '#/personal') +
      row('Date of birth', a.dob ? a.dob + ' (age ' + ageFrom(a.dob) + ')' : '', '#/') +
      row('Address', [a.address1, a.town, a.postcode].filter(Boolean).join(', '), '#/personal') +
      row('Treatment', s ? s.name : '', '#/select') +
      row('Height and weight', (a.heightCm && a.weightKg) ? a.heightCm + ' cm, ' + a.weightKg + ' kg \u2014 BMI ' + b : '', '#/bmi') +
      row('Photo ID', a.idFile ? a.idType + ' \u2014 ' + a.idFile : '', '#/identity') +
      row('Weight verification', a.verifyMethod, '#/identity') +
      row('GP notification', a.gpRegistered === 'Yes' ? (a.gpConsent || '') : 'Not registered with a UK GP', '#/gp') +
      '</dl>' + errSummary(a.__errors) +
      '<form data-stepform>' + renderFields(FIELDS, a) + '</form>' + nav('#/terms', '#/gp'));
  }

  function stepTerms() {
    var a = J().answers, s = jSvc();
    FIELDS = (s ? s.cautions : []).map(function (c, i) {
      return { k: 'caution' + i, type: 'consent', required: true, label: c };
    });
    DEPS = {};
    return shell('confirm', '<h1>Safety information for ' + esc(s ? s.name : 'your treatment') + '</h1>' +
      '<p class="step-why">Tick each one to show you have read it. These are the cautions the clinician is required to make sure you understand.</p>' +
      errSummary(a.__errors) + '<form data-stepform>' + renderFields(FIELDS, a) + '</form>' +
      '<div class="notice notice-info" style="margin-top:8px"><b>What you are consenting to</b>' +
      'You are consenting to being assessed and to us handling your health information. You are not consenting to a specific treatment \u2014 that conversation happens with the clinician after they have decided.</div>' +
      nav('#/account', '#/confirm'));
  }

  function stepAccount() {
    var a = J().answers;
    FIELDS = [
      { k: 'email', type: 'email', label: 'Email address', required: true, hint: 'We send a verification link here. You will need it to open your account.' },
      { k: 'pw', type: 'password', label: 'Create a password', required: true, half: true, hint: 'At least 10 characters.' },
      { k: 'pw2', type: 'password', label: 'Confirm your password', required: true, half: true },
      { k: 'deliverySame', type: 'radio', label: 'Is your delivery address the same as the address you gave us?', options: ['Yes, the same', 'No, use a different address'], required: true },
      { k: 'deliveryAddr', type: 'textarea', label: 'Delivery address', showIf: { k: 'deliverySame', is: 'No, use a different address' }, required: true },
      { k: 'prefs', type: 'checkboxes', label: 'How should we send service messages about your appointments?', options: ['Email', 'SMS'], required: true }
    ];
    DEPS = depKeys(FIELDS);
    return shell('account', '<h1>Create your account</h1>' +
      '<p class="step-why">Almost done. Your account is where you book, reschedule, follow your order and ask for a repeat supply.</p>' +
      errSummary(a.__errors) + '<form data-stepform>' + renderFields(FIELDS, a) + '</form>' +
      '<div class="notice notice-info"><b>Nothing to pay</b>Submitting this does not take payment and does not order any medicine. Payment only happens if a clinician approves treatment, and it is handled by SmartRx.</div>' +
      '<div class="step-nav"><a class="btn btn-ghost" href="#/terms">Back</a><div class="spacer"></div>' +
      '<button class="btn btn-solid" data-act="submitQ">Create account and submit</button></div>');
  }

  function buildSlots() {
    var p = D.booking, now = new Date();
    var first = new Date(now.getTime() + p.leadTimeHours * 3600e3), days = [];
    for (var d = 0; d < p.horizonDays && days.length < 5; d++) {
      var date = new Date(first.getFullYear(), first.getMonth(), first.getDate() + d);
      if (p.workingDays.indexOf(date.getDay()) === -1) continue;
      var iso = date.toISOString().slice(0, 10);
      if (p.closures.indexOf(iso) > -1) continue;
      var times = [], step = p.durationMins + p.bufferMins;
      for (var m = p.hours.from * 60; m + p.durationMins <= p.hours.to * 60; m += step) {
        var t = new Date(date); t.setHours(Math.floor(m / 60), m % 60, 0, 0);
        if (t < first) continue;
        var taken = S.appointments.some(function (ap) { return ap.when.getTime() === t.getTime(); });
        var seeded = ((d * 7 + m) % 11) < 4;
        times.push({ t: t, free: !taken && !seeded });
      }
      if (times.length) days.push({ date: date, times: times });
    }
    return days;
  }

  function stepBooking() {
    var days = buildSlots(), j = J(), s = jSvc();
    return shell('booking', emergencyPanel() +
      '<h1>Book your video appointment</h1>' +
      '<p class="step-why">All times are UK time. Nothing is taken from you now' +
      (s && s.kind === 'service' ? ', except the advice-only appointment fee, which is paid at the end of this step' : '') +
      '. You can move or cancel this from your account at any time, free of charge.</p>' +
      '<div class="pill-row"><span class="tag tag-teal">' + D.booking.durationMins + ' minutes</span>' +
      '<span class="tag tag-teal">Video call</span><span class="tag tag-teal">Any available clinician</span>' +
      '<span class="tag tag-teal">Earliest ' + D.booking.leadTimeHours + ' hours from now</span></div>' +
      '<div class="slots">' + days.map(function (d) {
        return '<div class="slotday"><div class="slotday-h"><b>' + fmtDate(d.date, { weekday: 'short' }) +
          '</b><span>' + fmtDate(d.date, { day: 'numeric', month: 'short' }) + '</span></div><div class="slotday-b">' +
          (d.times.filter(function (x) { return x.free; }).length === 0
            ? '<p class="slotday-none">No slots</p>'
            : d.times.map(function (x, i) {
                var hidden = i > 4 ? ' style="display:none"' : '';
                var cls = 'slot' + (i > 4 ? ' more' : '') + (j.slotIso === x.t.toISOString() ? ' sel' : '');
                return x.free
                  ? '<button class="' + cls + '" data-slot="' + x.t.toISOString() + '"' + hidden + '>' + fmtTime(x.t) + '</button>'
                  : '<button class="' + cls + '" disabled aria-label="' + fmtTime(x.t) + ' unavailable"' + hidden + '>' + fmtTime(x.t) + '</button>';
              }).join('')) + '</div></div>';
      }).join('') + '</div>' +
      '<div class="btnrow" style="margin-top:14px"><button class="btn btn-ghost btn-sm" data-act="moretimes">Show more times</button>' +
      '<span class="small muted">Slots you select are held for 10 minutes so nobody can take them from under you.</span></div>' +
      '<div id="slotpick" aria-live="polite"></div>' +
      '<div class="step-nav"><a class="btn btn-ghost" href="/account/">Book later from my account</a><div class="spacer"></div>' +
      '<button class="btn btn-solid" data-act="confirmSlot"' + (j.slotIso ? '' : ' aria-disabled="true"') + '>Confirm appointment</button></div>');
  }

  function stepDone() {
    var ap = S.appointments[0];
    return shell('booking',
      '<div class="notice notice-ok"><b>Your appointment is booked</b>Confirmation sent by email and SMS, with a calendar invitation attached.</div>' +
      '<h1>What happens next</h1>' +
      (ap ? '<div class="card" style="background:var(--mint-2);margin-bottom:24px"><p class="eyebrow" style="margin-bottom:6px">Your appointment</p>' +
        '<h2 style="margin-bottom:4px;font-size:1.3rem">' + fmtDate(ap.when, { weekday: 'long', day: 'numeric', month: 'long' }) + ' at ' + fmtTime(ap.when) + '</h2>' +
        '<p class="small muted" style="margin:0">' + esc(ap.service) + ' \u00b7 ' + D.booking.durationMins + '-minute video call \u00b7 UK time \u00b7 reference ' + esc(ap.id) + '</p></div>' : '') +
      '<div class="list" style="margin-bottom:24px">' +
      [['Before the call', 'Have your photo ID and a set of scales nearby. Find a private spot with a decent connection.'],
       ['During the call', 'The clinician checks your identity against the document you uploaded, confirms your weight, and asks about the answers you gave.'],
       ['After the call', 'You are told the outcome by email and SMS, usually within 24 working hours. If treatment is approved, SmartRx sends one payment link.']]
        .map(function (r) { return '<div class="li"><div class="li-main"><b>' + esc(r[0]) + '</b><span>' + esc(r[1]) + '</span></div></div>'; }).join('') +
      '</div><div class="notice notice-flag"><b>If something changes before your appointment</b>' +
      'If you become unwell, start a new medicine, or think you may be pregnant, tell us before the call. If you need urgent help, contact NHS 111. In an emergency, call 999.' +
      '<p class="small" style="margin:10px 0 0">Report any suspected side effect through the MHRA Yellow Card scheme.</p></div>' +
      '<div class="step-nav"><div class="spacer"></div><a class="btn btn-solid" href="/account/">Go to my account</a></div>');
  }

  /* ============================== ACCOUNT ============================== */
  function demoUser() {
    return { id: 'P-1041', firstName: 'Amara', lastName: 'Okafor', email: 'a.okafor@example.co.uk', mobile: '07700 900123', dob: '1988-03-12', postcode: 'M1 4BT', prefs: ['Email', 'SMS'], marketing: false };
  }
  function requireUser() {
    if (!S.user) { S.user = demoUser(); audit('Patient signed in', S.user.id, 'Prototype session'); }
    return S.user;
  }
  function dashShell(active, inner) {
    var items = [['#/', 'Overview'], ['#/appointments', 'Appointments'], ['#/repeat', 'Request a repeat'],
                 ['#/side-effects', 'Report a side effect'], ['#/profile', 'Profile and preferences']];
    return '<div class="appshell"><nav class="side" aria-label="Your account"><h2>My account</h2>' +
      items.map(function (i) { return '<a href="' + i[0] + '"' + (active === i[0] ? ' class="on" aria-current="page"' : '') + '>' + esc(i[1]) + '</a>'; }).join('') +
      '</nav><div class="panel">' + inner + '</div></div>';
  }

  function pageDashboard() {
    var u = requireUser();
    var upcoming = S.appointments.filter(function (a) { return a.status === 'Booked'; });
    var order = S.orders[0];
    return dashShell('#/', '<p class="eyebrow">Overview</p><h1 style="font-size:2rem">Hello, ' + esc(u.firstName) + '</h1>' +
      (upcoming.length ? upcoming.map(function (a) {
        return '<div class="card" style="background:var(--mint-2);margin-bottom:18px">' +
          '<div style="display:flex;gap:18px;flex-wrap:wrap;align-items:center"><div style="flex:1;min-width:240px">' +
          '<span class="tag tag-teal">Upcoming</span><h2 style="margin:10px 0 4px;font-size:1.3rem">' +
          fmtDate(a.when, { weekday: 'long', day: 'numeric', month: 'long' }) + ' at ' + fmtTime(a.when) + '</h2>' +
          '<p class="small muted" style="margin:0">' + esc(a.service) + ' \u00b7 video call \u00b7 reference ' + esc(a.id) + '</p></div>' +
          '<div class="btnrow"><button class="btn btn-ghost btn-sm" data-act="cancelap" data-id="' + a.id + '">Cancel</button></div></div>' +
          '<p class="small muted" style="margin:14px 0 0">Joining instructions were sent by email and SMS. No charge applies if you move or cancel this.</p></div>';
      }).join('')
        : '<div class="card" style="margin-bottom:18px"><h2 style="font-size:1.2rem">No appointment booked</h2>' +
          '<p>You have nothing in the diary. If you have already submitted a questionnaire you can book straight away.</p>' +
          '<a class="btn btn-solid btn-sm" href="/consultation/">Start a consultation</a></div>') +
      '<div class="grid g2" style="margin-top:8px"><div class="card"><h2 style="font-size:1.1rem;font-family:var(--f-body);font-weight:700">Your most recent order</h2>' +
      (order
        ? '<p style="margin:8px 0 4px"><b>' + esc(order.item) + '</b> \u00b7 ' + money(order.price) + '</p>' +
          '<p class="small muted" style="margin:0 0 12px">Order ' + esc(order.id) + '</p><div class="list">' +
          ['Payment received', 'Dispensed by SmartRx', 'Dispatched', 'Delivered'].map(function (st, i) {
            return '<div class="li" style="padding:11px 16px"><span class="tag ' + (i <= order.stage ? 'tag-ok' : 'tag-off') + '">' +
              (i <= order.stage ? '\u2713' : i + 1) + '</span><div class="li-main"><b>' + esc(st) + '</b></div></div>';
          }).join('') + '</div>'
        : '<p class="muted">Nothing yet. An order appears here after a clinician approves treatment and you have paid the link SmartRx sends you.</p>') +
      '</div><div class="card"><h2 style="font-size:1.1rem;font-family:var(--f-body);font-weight:700">Repeat supply</h2>' +
      '<p>Every repeat needs a clinical review \u2014 your current weight, how you are tolerating treatment, and anything that has changed. It is never automatic.</p>' +
      '<a class="btn btn-solid btn-sm" href="#/repeat">Request a repeat prescription</a></div></div>' +
      '<div class="notice notice-info" style="margin-top:30px"><b>What this dashboard deliberately does not show</b>' +
      'Prescriptions, invoices, your completed questionnaire and your uploaded ID are not displayed here. They are held in the clinical record. You have the right to request a copy at any time.</div>');
  }

  function pageAppointments() {
    requireUser();
    return dashShell('#/appointments', '<p class="eyebrow">Appointments</p><h1 style="font-size:2rem">Your appointments</h1>' +
      (S.appointments.length
        ? '<div class="list">' + S.appointments.map(function (a) {
            return '<div class="li"><div class="li-main"><b>' + fmtDate(a.when, { weekday: 'long', day: 'numeric', month: 'long' }) +
              ' at ' + fmtTime(a.when) + '</b><span>' + esc(a.service) + ' \u00b7 reference ' + esc(a.id) + '</span></div>' +
              '<span class="tag ' + (a.status === 'Booked' ? 'tag-teal' : 'tag-off') + '">' + esc(a.status) + '</span></div>';
          }).join('') + '</div>'
        : '<div class="list"><p class="empty">Nothing booked yet. <a href="/consultation/">Start a consultation</a>.</p></div>') +
      '<p class="small muted" style="margin-top:16px">All times are UK time and adjust automatically for British Summer Time.</p>');
  }

  function pageRepeat() {
    requireUser();
    var a = S.checkin;
    a.sexAtBirth = a.sexAtBirth || 'Female';
    FIELDS = D.checkin; DEPS = depKeys(FIELDS);
    return dashShell('#/repeat', '<p class="eyebrow">Repeat supply</p><h1 style="font-size:2rem">Your check-in</h1>' +
      '<p class="lead" style="font-size:1.05rem">Short, because we already know your history. Five questions, then a review appointment.</p>' +
      errSummary(a.__errors) +
      '<div class="card" style="max-width:680px"><form data-stepform>' + renderFields(FIELDS, a) + '</form>' +
      '<div class="step-nav" style="margin-top:20px"><div class="spacer"></div>' +
      '<button class="btn btn-solid" data-act="submitCheckin">Submit and book a review</button></div></div>' +
      '<div class="notice notice-info" style="margin-top:24px;max-width:680px"><b>Repeat supply is never automatic</b>' +
      'Nothing is dispensed on the strength of this form. A clinician reviews it and speaks to you before deciding whether to continue treatment and at what dose.</div>');
  }

  function pageSideEffects() {
    requireUser();
    return dashShell('#/side-effects', '<p class="eyebrow">Safety</p><h1 style="font-size:2rem">Report a side effect</h1>' +
      '<div class="notice notice-stop" style="max-width:680px"><b>If this is severe, do not use this form</b>' +
      'For a severe allergic reaction, severe abdominal pain, or any life-threatening symptom, call 999. For urgent advice, call NHS 111.</div>' +
      '<div class="card" style="max-width:680px"><div class="field"><label for="se_w">What happened? <span class="req">*</span></label>' +
      '<textarea id="se_w" placeholder="Describe the symptom, when it started and how long it lasted."></textarea></div>' +
      '<div class="field"><label for="se_s">How severe is it? <span class="req">*</span></label>' +
      '<select id="se_s"><option value="">Please choose</option><option>Mild \u2014 annoying but manageable</option>' +
      '<option>Moderate \u2014 affecting daily life</option><option>Severe \u2014 I am struggling</option></select></div>' +
      '<button class="btn btn-solid" data-act="sideeffect">Send to the clinic</button></div>' +
      (S.sideEffects.length ? '<h2 style="margin-top:34px;font-size:1.3rem">Reports you have sent</h2><div class="list" style="max-width:680px">' +
        S.sideEffects.map(function (r) {
          return '<div class="li"><div class="li-main"><b>' + esc(r.severity) + '</b><span>' + esc(r.what) + '</span></div>' +
            '<span class="tag tag-flag">Clinic alerted</span></div>';
        }).join('') + '</div>' : ''));
  }

  function pageProfile() {
    var u = requireUser();
    return dashShell('#/profile', '<p class="eyebrow">Your details</p><h1 style="font-size:2rem">Profile and preferences</h1>' +
      '<div class="grid g2" style="align-items:start"><div class="card">' +
      '<h2 style="font-size:1.1rem;font-family:var(--f-body);font-weight:700">Personal details</h2>' +
      '<div class="row2"><div class="field"><label for="pf_f">First name</label><input id="pf_f" value="' + esc(u.firstName) + '"></div>' +
      '<div class="field"><label for="pf_l">Last name</label><input id="pf_l" value="' + esc(u.lastName) + '"></div></div>' +
      '<div class="field"><label for="pf_d">Date of birth</label><input id="pf_d" value="' + esc(u.dob) + '" disabled>' +
      '<p class="hint">Locked once your identity has been verified. Contact us if this is wrong.</p></div>' +
      '<div class="field"><label for="pf_e">Email</label><input id="pf_e" type="email" value="' + esc(u.email) + '"></div>' +
      '<button class="btn btn-solid btn-sm" data-act="saveprofile">Save changes</button></div>' +
      '<div class="card"><h2 style="font-size:1.1rem;font-family:var(--f-body);font-weight:700">Your data</h2>' +
      '<p class="small">You can ask for a copy of everything we hold, or ask us to close your account. Clinical records we are required to keep are retained for the statutory period.</p>' +
      '<div class="btnrow"><button class="btn btn-ghost btn-sm" data-act="dsar">Request a copy of my data</button></div></div></div>');
  }

  /* =============================== ADMIN =============================== */
  var ADMIN_NAV = [['#/', 'Dashboard'], ['#/submissions', 'Questionnaires'], ['#/patients', 'Patients'],
                   ['#/appointments', 'Appointments'], ['#/products', 'Products and prices'], ['#/audit', 'Audit log']];

  function adminShell(active, inner) {
    return '<div class="appshell"><nav class="side" aria-label="Back office"><h2>Back office</h2>' +
      ADMIN_NAV.map(function (i) { return '<a href="' + i[0] + '"' + (active === i[0] ? ' class="on" aria-current="page"' : '') + '>' + esc(i[1]) + '</a>'; }).join('') +
      '</nav><div class="panel">' + inner + '</div></div>';
  }

  function adminHome() {
    var flagged = S.submissions.filter(function (s) { return s.flags.length; }).length;
    return adminShell('#/', '<h1 style="font-size:2rem">Today at a glance</h1>' +
      '<div class="stats"><div class="stat"><b>' + S.appointments.length + '</b><span>Appointments booked</span></div>' +
      '<div class="stat"><b>' + S.submissions.length + '</b><span>Questionnaires submitted</span></div>' +
      '<div class="stat"><b>' + flagged + '</b><span>Submissions with flagged answers</span></div>' +
      '<div class="stat"><b>' + S.enquiries.filter(function (e2) { return e2.status === 'New'; }).length + '</b><span>New enquiries</span></div></div>' +
      '<h2 style="font-size:1.4rem">Questionnaires waiting</h2>' +
      (S.submissions.length
        ? '<div class="list">' + S.submissions.map(function (s) {
            return '<div class="li"><div class="li-main"><b>' + esc(s.patient ? s.patient.firstName + ' ' + s.patient.lastName : 'Patient') +
              ' \u2014 ' + esc(s.service) + '</b><span>Submitted ' + fmtTime(s.at) + ' \u00b7 ' + esc(s.status) + '</span></div>' +
              (s.flags.length ? '<span class="tag tag-flag">' + s.flags.length + ' flagged</span>' : '<span class="tag tag-ok">No flags</span>') +
              '<a class="btn btn-ghost btn-sm" href="#/submission/' + s.id + '">Open</a></div>';
          }).join('') + '</div>'
        : '<div class="list"><p class="empty">Nothing submitted yet in this session. <a href="/consultation/">Run the patient journey</a> and it will appear here.</p></div>'));
  }

  function adminSubmissions() {
    return adminShell('#/submissions', '<h1 style="font-size:2rem">Questionnaire submissions</h1>' +
      '<p class="lead" style="font-size:1.02rem">SmartGP does not host a clinical review queue. Its job is to hand the clinician a complete, well-organised submission and to tell the patient the outcome afterwards.</p>' +
      (S.submissions.length
        ? '<div class="list" style="margin-top:20px">' + S.submissions.map(function (s) {
            return '<div class="li"><div class="li-main"><b>' + esc(s.id) + ' \u00b7 ' +
              esc(s.patient ? s.patient.firstName + ' ' + s.patient.lastName : 'Patient') + '</b>' +
              '<span>' + esc(s.service) + (s.bmi ? ' \u00b7 BMI ' + s.bmi : '') + '</span></div>' +
              (s.flags.length ? '<span class="tag tag-flag">' + s.flags.length + ' flagged</span>' : '<span class="tag tag-ok">No flags</span>') +
              '<a class="btn btn-solid btn-sm" href="#/submission/' + s.id + '">Open</a></div>';
          }).join('') + '</div>'
        : '<div class="list" style="margin-top:20px"><p class="empty">No submissions in this session yet.</p></div>'));
  }

  function adminSubmission(id) {
    var s = null;
    S.submissions.forEach(function (x) { if (x.id === id) s = x; });
    if (!s) return adminShell('#/submissions', '<div class="notice notice-stop">Submission not found in this session.</div>');
    var a = s.answers, flagKeys = s.flags.map(function (f) { return f.k; });
    var rows = visibleFields(s.fields, a).map(function (f) {
      var v = a[f.k];
      var shown = Array.isArray(v) ? v.join(', ') : (typeof v === 'boolean' ? (v ? 'Agreed' : 'Not agreed') : v);
      if (shown === undefined || shown === '' || shown === null) return '';
      return '<div class="ans ' + (flagKeys.indexOf(f.k) > -1 ? 'flagged' : '') + '"><dt>' + esc(f.label) + '</dt><dd>' + esc(shown) + '</dd></div>';
    }).join('');

    return adminShell('#/submissions',
      '<p class="crumb"><a href="#/submissions">Questionnaires</a> \u2192 ' + esc(s.id) + '</p>' +
      '<h1 style="font-size:2rem">' + esc(s.patient ? s.patient.firstName + ' ' + s.patient.lastName : 'Patient') + '</h1>' +
      '<p class="muted">' + esc(s.service) + ' \u00b7 submitted ' + fmtDate(s.at) + ' at ' + fmtTime(s.at) + '</p>' +
      (s.flags.length
        ? '<div class="notice notice-flag" style="margin-top:20px"><b>' + s.flags.length + ' answer' +
          (s.flags.length > 1 ? 's need' : ' needs') + ' your attention first</b><ul style="margin:8px 0 0;padding-left:18px">' +
          s.flags.map(function (f) {
            return '<li><b>' + esc(f.level === 'exclusion' ? 'Exclusion' : 'Caution') + ':</b> ' + esc(f.label) +
              ' \u2014 answered \u201c' + esc(f.answer) + '\u201d. ' + esc(f.note) + '</li>';
          }).join('') + '</ul><p class="small" style="margin:10px 0 0">Flagging is not a decision. The patient has not been refused and has not been told anything about this.</p></div>'
        : '<div class="notice notice-ok" style="margin-top:20px"><b>No exclusions or cautions flagged</b>Read the answers in full anyway \u2014 the online form is a starting point, not an assessment.</div>') +
      '<div class="stats" style="margin-top:22px"><div class="stat"><b>' + (s.bmi || '\u2014') + '</b><span>Calculated BMI</span></div>' +
      '<div class="stat"><b>' + (a.heightCm || '\u2014') + '</b><span>Height (cm)</span></div>' +
      '<div class="stat"><b>' + (a.weightKg || '\u2014') + '</b><span>Declared weight (kg)</span></div>' +
      '<div class="stat"><b>' + (ageFrom(a.dob) || '\u2014') + '</b><span>Age</span></div></div>' +
      '<h2 style="margin-top:34px;font-size:1.4rem">Weight verification</h2>' +
      '<div class="card"><p style="margin:0"><b>' + esc(s.verification || 'Not recorded') + '</b></p>' +
      '<p class="small muted" style="margin:8px 0 0">Height and weight must be independently verified before first supply. Confirm it on the call and record it in the clinical system \u2014 SmartGP captures the method, you confirm the fact.</p></div>' +
      '<h2 style="margin-top:34px;font-size:1.4rem">All answers</h2>' +
      '<div style="background:#fff;border:1px solid var(--line);border-radius:var(--r-m);padding:8px 20px">' +
      (rows || '<p class="empty">No answers recorded.</p>') + '</div>' +
      '<h2 style="margin-top:34px;font-size:1.4rem">Record the outcome</h2><div class="card">' +
      '<p>Enter the decision you have already made and recorded in the practice management system. SmartGP notifies the patient \u2014 it does not make, store or second-guess the decision.</p>' +
      '<div class="btnrow"><button class="btn btn-solid" data-outcome="approved" data-id="' + esc(s.id) + '">Treatment approved</button>' +
      '<button class="btn btn-ghost" data-outcome="more" data-id="' + esc(s.id) + '">More information needed</button>' +
      '<button class="btn btn-ghost" data-outcome="unsuitable" data-id="' + esc(s.id) + '">Not suitable</button></div>' +
      (s.outcome ? '<div class="notice ' + (s.outcome === 'approved' ? 'notice-ok' : 'notice-flag') + '" style="margin:18px 0 0">' +
        '<b>Outcome recorded: ' + esc(s.outcomeLabel) + '</b>' + esc(s.outcomeNote) + '</div>' : '') + '</div>');
  }

  function adminPatients() {
    return adminShell('#/patients', '<h1 style="font-size:2rem">Patients</h1>' +
      '<div class="tablewrap"><table><caption class="visually-hidden">Patients</caption><thead><tr>' +
      '<th scope="col">Reference</th><th scope="col">Name</th><th scope="col">Service</th>' +
      '<th scope="col">Status</th><th scope="col">Flags</th></tr></thead><tbody>' +
      S.patients.map(function (p) {
        return '<tr><td class="ref">' + esc(p.id) + '</td><td><b>' + esc(p.name) + '</b><br><span class="small muted">' + esc(p.email) + '</span></td>' +
          '<td>' + esc(p.service) + '</td><td><span class="tag ' + (p.status === 'Approved' ? 'tag-ok' : 'tag-teal') + '">' + esc(p.status) + '</span></td>' +
          '<td>' + (p.flags ? '<span class="tag tag-flag">' + p.flags + '</span>' : '\u2014') + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<p class="small muted" style="margin-top:14px">Clinical answers, identity documents and verification evidence are visible only to clinical roles.</p>');
  }

  function adminAppointments() {
    return adminShell('#/appointments', '<h1 style="font-size:2rem">Appointments</h1>' +
      (S.appointments.length
        ? '<div class="list">' + S.appointments.map(function (a) {
            return '<div class="li"><div class="li-main"><b>' + fmtDate(a.when, { weekday: 'long', day: 'numeric', month: 'long' }) +
              ' at ' + fmtTime(a.when) + '</b><span>' + esc(a.patient) + ' \u00b7 ' + esc(a.service) + ' \u00b7 ' + esc(a.clinician) + '</span></div>' +
              '<span class="tag ' + (a.status === 'Booked' ? 'tag-teal' : 'tag-off') + '">' + esc(a.status) + '</span></div>';
          }).join('') + '</div>'
        : '<div class="list"><p class="empty">Nothing in the diary in this session.</p></div>'));
  }

  function adminProducts() {
    return adminShell('#/products', '<h1 style="font-size:2rem">Products and prices</h1>' +
      '<p class="lead" style="font-size:1.02rem">Service, then strength, then price variant. These values come from the same catalogue the public pages are built from, so the two can never disagree.</p>' +
      D.services.map(function (s) {
        return '<div class="card" style="margin-bottom:18px"><h2 style="font-size:1.2rem">' + esc(s.name) + '</h2>' +
          '<div class="tablewrap" style="margin-top:14px"><table><caption class="visually-hidden">' + esc(s.name) + ' prices</caption>' +
          '<thead><tr><th scope="col">Strength or pack</th><th scope="col" class="num">Price</th><th scope="col">Available to patients</th></tr></thead><tbody>' +
          s.strengths.map(function (x) {
            return '<tr><th scope="row">' + esc(x.label) + '</th><td class="num">' + money(x.price) + '</td>' +
              '<td><span class="tag ' + (x.available ? 'tag-ok' : 'tag-off') + '">' + (x.available ? 'Available' : 'Hidden from patients') + '</span></td></tr>';
          }).join('') + '</tbody></table></div></div>';
      }).join('') +
      '<div class="notice notice-info"><b>No stock quantities</b>Availability is a manual flag per strength, not a stock count.</div>');
  }

  function adminAudit() {
    return adminShell('#/audit', '<h1 style="font-size:2rem">Audit log</h1>' +
      '<p class="lead" style="font-size:1.02rem">Everything done in this session, in the order it happened. Read-only, tamper-evident, exportable, and kept for at least six years.</p>' +
      (S.audit.length
        ? '<div class="tablewrap"><table><caption class="visually-hidden">Audit log</caption><thead><tr>' +
          '<th scope="col">Time</th><th scope="col">Actor</th><th scope="col">Action</th><th scope="col">Entity</th><th scope="col">Detail</th></tr></thead><tbody>' +
          S.audit.map(function (a) {
            return '<tr><td class="ref">' + fmtTime(a.at) + '</td><td class="small">' + esc(a.actor) + '</td>' +
              '<td><b>' + esc(a.action) + '</b></td><td class="ref">' + esc(a.entity) + '</td><td class="small">' + esc(a.detail) + '</td></tr>';
          }).join('') + '</tbody></table></div>'
        : '<div class="list"><p class="empty">Nothing logged yet.</p></div>'));
  }

  /* ============================= LISTENERS ============================= */
  function saveAndValidate() {
    var a = (MOUNT === 'account' && path() === '/repeat') ? S.checkin : J().answers;
    collect(mountEl, a);
    var errs = validate(FIELDS, a);
    a.__errors = Object.keys(errs).length ? errs : null;
    return !a.__errors;
  }

  document.addEventListener('change', function (ev) {
    if (!ev.target.closest('#app')) return;
    var a = (MOUNT === 'account' && path() === '/repeat') ? S.checkin : J().answers;

    if (ev.target.dataset.multi && ev.target.dataset.exclusive) {
      var grp = $$('[data-k="' + ev.target.dataset.k + '"]');
      if (ev.target.checked && ev.target.value === ev.target.dataset.exclusive) {
        grp.forEach(function (x) { if (x !== ev.target) x.checked = false; });
      } else if (ev.target.checked) {
        grp.forEach(function (x) { if (x.value === ev.target.dataset.exclusive) x.checked = false; });
      }
    }
    collect(mountEl, a);
    var k = ev.target.getAttribute('data-k');
    if (k && DEPS[k]) { render(); return; }
    $$('.opt', mountEl).forEach(function (o) {
      var i = o.querySelector('input'); if (i) o.classList.toggle('sel', i.checked);
    });
  });

  document.addEventListener('input', function (ev) {
    if (!ev.target.closest('#bmiform')) return;
    var a = J().answers;
    if (a.__hUnit === 'ft') {
      a.__hFt = $('#hFt').value; a.__hIn = $('#hIn').value;
      a.heightCm = a.__hFt ? Math.round((Number(a.__hFt) * 30.48 + Number(a.__hIn || 0) * 2.54) * 10) / 10 : '';
    } else if ($('#hCm')) a.heightCm = $('#hCm').value;
    if (a.__wUnit === 'st') {
      a.__wSt = $('#wSt').value; a.__wLb = $('#wLb').value;
      a.weightKg = a.__wSt ? Math.round((Number(a.__wSt) * 6.35029 + Number(a.__wLb || 0) * 0.453592) * 10) / 10 : '';
    } else if ($('#wKg')) a.weightKg = $('#wKg').value;
    bmiPaint();
  });

  document.addEventListener('click', function (ev) {
    if (!ev.target.closest('#app')) return;
    var a = J().answers, t;

    if (ev.target.closest('[data-act="restart"]')) { S.journey = null; audit('Questionnaire restarted', 'Journey', ''); render(); return; }

    t = ev.target.closest('[data-unit]');
    if (t) { if (t.dataset.unit === 'h') a.__hUnit = t.dataset.val; else a.__wUnit = t.dataset.val; render(); return; }

    t = ev.target.closest('[data-pick]');
    if (t) { J().serviceId = t.dataset.pick; $$('.opt', mountEl).forEach(function (o) { o.classList.toggle('sel', o.contains(t)); }); return; }

    if (ev.target.closest('[data-act="agecheck"]')) {
      if (!saveAndValidate()) { render(); return; }
      var age = ageFrom(a.dob);
      if (age === null) { a.__errors = { dob: 'Enter your date of birth as a real date.' }; render(); return; }
      audit('Age check completed', 'Journey', 'age ' + age);
      if (age < 18) { S.journey = null; go('#/blocked'); return; }
      go('#/status'); return;
    }

    t = ev.target.closest('[data-act="next"]');
    if (t) {
      if (!saveAndValidate()) { render(); var es = $('#errsum'); if (es) es.focus(); return; }
      if (path() === '/select' && !J().serviceId) { toast('Choose a treatment to continue.'); return; }
      go(t.dataset.next); return;
    }

    if (ev.target.closest('[data-act="postcode"]')) {
      collect(mountEl, a);
      if (!/^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$/i.test((a.postcode || '').trim())) { toast('Enter a full UK postcode first, for example M1 4BT'); return; }
      a.address1 = '14 Marchant House'; a.address2 = 'Wilbraham Road'; a.town = 'Manchester'; a.county = 'Greater Manchester';
      audit('Address looked up', (a.postcode || '').toUpperCase(), 'UK postcode lookup');
      toast('Address found and filled in.'); render(); return;
    }

    if (ev.target.closest('[data-act="gplookup"]')) {
      collect(mountEl, a);
      var p = GP_PRACTICES[0];
      a.gpPractice = p.n; a.__gpDetail = p.n + ' \u00b7 ' + p.t + ' \u00b7 ' + p.e;
      render(); toast('Practice selected.'); return;
    }

    t = ev.target.closest('[data-act="upload"]');
    if (t) {
      collect(mountEl, a);
      var k = t.dataset.k, inp = document.createElement('input');
      inp.type = 'file'; inp.accept = 'image/*,application/pdf';
      inp.onchange = function () {
        a[k] = (inp.files && inp.files[0]) ? inp.files[0].name : 'document.jpg';
        audit('Identity document uploaded', a[k], 'Encrypted private storage \u00b7 deletion scheduled +30 days');
        render(); toast('Uploaded. Only clinical staff can open this.');
      };
      inp.click(); return;
    }

    if (ev.target.closest('[data-act="submitQ"]')) {
      if (!saveAndValidate()) { render(); return; }
      if (a.pw && a.pw.length < 10) { a.__errors = { pw: 'Use at least 10 characters.' }; render(); return; }
      if (a.pw !== a.pw2) { a.__errors = { pw2: 'The two passwords do not match.' }; render(); return; }
      submitQuestionnaire(); return;
    }

    t = ev.target.closest('[data-slot]');
    if (t) {
      J().slotIso = t.dataset.slot;
      $$('.slot', mountEl).forEach(function (x) { x.classList.remove('sel'); });
      t.classList.add('sel');
      var d = new Date(J().slotIso);
      $('#slotpick').innerHTML = '<div class="notice notice-ok" style="margin-top:20px"><b>Held for 10 minutes</b>' +
        fmtDate(d, { weekday: 'long', day: 'numeric', month: 'long' }) + ' at ' + fmtTime(d) + ', UK time. Confirm below to book it.</div>';
      var cb = $('[data-act="confirmSlot"]'); if (cb) cb.removeAttribute('aria-disabled');
      return;
    }
    if (ev.target.closest('[data-act="moretimes"]')) {
      $$('.slot.more', mountEl).forEach(function (x) { x.style.display = ''; });
      ev.target.closest('button').remove(); return;
    }
    if (ev.target.closest('[data-act="confirmSlot"]')) {
      if (!J().slotIso) { toast('Choose a time first.'); return; }
      confirmBooking(); return;
    }

    /* account */
    t = ev.target.closest('[data-act="cancelap"]');
    if (t) {
      S.appointments.forEach(function (x) { if (x.id === t.dataset.id) x.status = 'Cancelled by patient'; });
      audit('Appointment cancelled', t.dataset.id, 'Cancelled by patient \u00b7 no charge applied');
      render(); toast('Appointment cancelled. Nothing was charged.'); return;
    }
    if (ev.target.closest('[data-act="submitCheckin"]')) {
      var c = S.checkin;
      collect(mountEl, c);
      var errs = validate(D.checkin, c);
      c.__errors = Object.keys(errs).length ? errs : null;
      if (c.__errors) { render(); return; }
      var fl = flagsFor(D.checkin, c);
      S.submissions.unshift({ id: nextId('Q'), patient: S.user, service: 'Repeat review',
        at: new Date(), bmi: null, answers: JSON.parse(JSON.stringify(c)), fields: D.checkin,
        flags: fl, status: 'Check-in submitted \u2014 awaiting review', verification: 'Review appointment' });
      audit('Repeat check-in submitted', 'Repeat', fl.length + ' answer(s) flagged for the clinician');
      toast('Check-in sent. Now book your review appointment.');
      location.href = '/consultation/#/booking'; return;
    }
    if (ev.target.closest('[data-act="sideeffect"]')) {
      var w = $('#se_w').value.trim(), sv = $('#se_s').value;
      if (!w || !sv) { toast('Describe what happened and how severe it is.'); return; }
      S.sideEffects.unshift({ what: w, severity: sv, at: new Date() });
      audit('Side effect reported', S.user.id, sv + ' \u2014 clinic alerted');
      render(); toast('Sent to the clinic. Please also report it to the MHRA Yellow Card scheme.'); return;
    }
    if (ev.target.closest('[data-act="saveprofile"]')) {
      S.user.firstName = $('#pf_f').value; S.user.lastName = $('#pf_l').value; S.user.email = $('#pf_e').value;
      audit('Patient profile updated', S.user.id, 'Self-service change from dashboard');
      render(); toast('Saved.'); return;
    }
    if (ev.target.closest('[data-act="dsar"]')) {
      audit('Data subject request raised', S.user.id, 'Copy of data requested');
      toast('Request logged. We will send a copy within one month.'); return;
    }

    /* admin */
    t = ev.target.closest('[data-outcome]');
    if (t) {
      var sub = null;
      S.submissions.forEach(function (x) { if (x.id === t.dataset.id) sub = x; });
      if (!sub) return;
      var kind = t.dataset.outcome;
      sub.outcome = kind;
      if (kind === 'approved') {
        sub.outcomeLabel = 'Treatment approved';
        sub.outcomeNote = 'Patient notified by email and SMS. SmartRx has been asked to send the payment link. No payment is taken by SmartGP.';
        var st = sub.serviceId && svc(sub.serviceId) ? svc(sub.serviceId).strengths.filter(function (x) { return x.available; })[0] : null;
        S.orders.unshift({ id: nextId('O'), item: sub.service + (st ? ' ' + st.label : ''), price: st ? st.price : 0, stage: 0 });
      } else if (kind === 'more') {
        sub.outcomeLabel = 'More information needed';
        sub.outcomeNote = 'Patient asked for the missing information and invited to rebook. Nothing has been refused.';
      } else {
        sub.outcomeLabel = 'Not suitable';
        sub.outcomeNote = 'Patient sent a supportive message with alternatives and signposting to their GP or NHS 111. No payment taken.';
      }
      audit('Consultation outcome recorded', sub.id, sub.outcomeLabel);
      render(); toast('Outcome recorded and the patient has been notified.'); return;
    }
  });

  function submitQuestionnaire() {
    var j = J(), a = j.answers, s = jSvc(), b = bmiOf(a.heightCm, a.weightKg);
    var allFields = D.common.personal.concat(D.common.gp, D.common.consent, s ? s.module : []);
    var flags = flagsFor(s ? s.module : [], a);

    S.user = { id: nextId('P'), firstName: a.firstName, lastName: a.lastName, email: a.email,
      mobile: a.mobile, dob: a.dob, postcode: a.postcode, prefs: a.prefs || ['Email'], marketing: !!a.cMarketing };

    var sub = { id: nextId('Q'), patient: S.user, service: s ? s.name : '\u2014', serviceId: j.serviceId,
      at: new Date(), bmi: b, answers: JSON.parse(JSON.stringify(a)), fields: allFields,
      flags: flags, status: 'Submitted \u2014 awaiting appointment', verification: a.verifyMethod, version: 'v1.0' };
    S.submissions.unshift(sub);
    S.patients.unshift({ id: S.user.id, name: a.firstName + ' ' + a.lastName, email: a.email,
      dob: a.dob, postcode: a.postcode, status: 'Questionnaire submitted', service: sub.service,
      flags: flags.length, submitted: 'Just now' });

    audit('Account created', S.user.id, a.firstName + ' ' + a.lastName + ' \u00b7 verification email sent');
    audit('Consent recorded', 'Consent register', 'Terms, privacy, clinical assessment');
    audit('Questionnaire submitted', sub.id, sub.service + ' \u00b7 BMI ' + b + ' \u00b7 ' + flags.length + ' answer(s) flagged');
    go('#/booking');
    toast('Submitted. Now choose an appointment time.');
  }

  function confirmBooking() {
    var j = J(), s = jSvc(), when = new Date(j.slotIso);
    S.appointments.unshift({ id: nextId('A'), when: when, service: s ? s.name : '\u2014',
      clinician: D.booking.clinicians[S.appointments.length % D.booking.clinicians.length],
      status: 'Booked', patient: S.user ? S.user.firstName + ' ' + S.user.lastName : 'Guest' });
    audit('Appointment booked', 'Booking', fmtDate(when) + ' ' + fmtTime(when));
    go('#/done');
  }

  /* ================================ BOOT ================================ */
  function boot() {
    if (MOUNT === 'journey') {
      route('/', stepAge); route('/blocked', pageBlocked); route('/status', stepStatus);
      route('/select', stepSelect); route('/info', stepInfo); route('/expect', stepExpect);
      route('/personal', stepPersonal); route('/bmi', stepBMI); route('/identity', stepIdentity);
      route('/safety', stepSafety); route('/gp', stepGP); route('/confirm', stepConfirm);
      route('/terms', stepTerms); route('/account', stepAccount); route('/booking', stepBooking);
      route('/done', stepDone);
    } else if (MOUNT === 'account') {
      route('/', pageDashboard); route('/appointments', pageAppointments);
      route('/repeat', pageRepeat); route('/side-effects', pageSideEffects); route('/profile', pageProfile);
    } else {
      route('/', adminHome); route('/submissions', adminSubmissions);
      route('/submission/:id', adminSubmission); route('/patients', adminPatients);
      route('/appointments', adminAppointments); route('/products', adminProducts);
      route('/audit', adminAudit);
    }
    window.addEventListener('hashchange', render);
    audit('Session started', 'SmartGP prototype', 'In-memory only \u2014 nothing is persisted');
    render();
  }

  fetch('/assets/js/data.json')
    .then(function (r) { return r.json(); })
    .then(function (d) { D = d; boot(); })
    .catch(function () {
      mountEl.innerHTML = '<div class="wrap" style="padding:60px 0">' +
        '<div class="notice notice-stop"><b>Could not load the catalogue</b>' +
        'This page needs to be served over HTTP rather than opened directly from disk. ' +
        'Run <code>python3 -m http.server</code> in the site folder and reload.</div>' +
        '<p><a class="btn btn-ghost" href="/">Back to the homepage</a></p></div>';
    });
})();
