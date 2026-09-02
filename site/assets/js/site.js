/* SmartGP — public site behaviour.
   Everything here is progressive enhancement. With JavaScript disabled the
   navigation still works, every FAQ answer is readable, and no content is
   hidden — which is also what makes the pages fully crawlable. */
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------------------------------------------------------- mobile nav */
  var burger = $('#burger'), mnav = $('#mobilenav');
  if (burger && mnav) {
    mnav.hidden = true;                       // hidden only once JS is running
    burger.addEventListener('click', function () {
      var open = burger.getAttribute('aria-expanded') === 'true';
      burger.setAttribute('aria-expanded', String(!open));
      burger.setAttribute('aria-label', open ? 'Open menu' : 'Close menu');
      mnav.hidden = open;
    });
    mnav.addEventListener('click', function (ev) {
      if (ev.target.closest('a')) { mnav.hidden = true; burger.setAttribute('aria-expanded', 'false'); }
    });
  }

  /* -------------------------------------------------------------- toast */
  var toastEl = $('#toast'), toastT;
  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg; toastEl.hidden = false;
    clearTimeout(toastT);
    toastT = setTimeout(function () { toastEl.hidden = true; }, 3400);
  }
  window.sgToast = toast;

  /* ----------------------------------------------------- cookie consent
     No non-essential cookie is set before an explicit choice. The choice is
     kept in memory for this prototype; production stores a consent record. */
  var consent = { set: false, analytics: false };
  var cookieEl = $('#cookie');

  function paintCookie() {
    if (!cookieEl) return;
    if (consent.set) { cookieEl.hidden = true; paintCookieState(); return; }
    cookieEl.hidden = false;
    cookieEl.innerHTML =
      '<div class="wrap cookie-in">' +
      '<p><b>We use essential cookies to run this site.</b> We would also like to set ' +
      'analytics cookies to understand where people get stuck. No health information ' +
      'is ever sent to analytics. <a href="/legal/cookies/">Read the cookie policy</a>.</p>' +
      '<div class="btnrow">' +
      '<button class="btn btn-ghost btn-sm" style="color:#fff;border-color:#3A5A52" data-cookie="reject">Reject analytics</button>' +
      '<button class="btn btn-solid btn-sm" data-cookie="accept">Accept analytics</button>' +
      '</div></div>';
  }

  function paintCookieState() {
    var el = $('#cookiestate');
    if (!el) return;
    el.innerHTML = consent.set
      ? (consent.analytics ? 'Analytics cookies are <b>on</b>.' : 'Analytics cookies are <b>off</b>.')
      : 'You have not chosen yet. No analytics cookies have been set.';
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-cookie]');
    if (!b) return;
    consent = { set: true, analytics: b.getAttribute('data-cookie') === 'accept' };
    paintCookie();
    toast(consent.analytics ? 'Analytics cookies accepted.' : 'Analytics cookies rejected.');
  });

  paintCookie();
  paintCookieState();

  /* --------------------------------------------------------- FAQ search
     Answers ship expanded in the HTML. This only filters them. */
  var faqq = $('[data-faqsearch]');
  if (faqq) {
    faqq.addEventListener('input', function () {
      var q = faqq.value.toLowerCase().trim();
      $$('#faqlist .faq').forEach(function (d) {
        d.style.display = (!q || d.getAttribute('data-q').indexOf(q) > -1) ? '' : 'none';
      });
      $$('#faqlist h2').forEach(function (h) {
        var n = h.nextElementSibling, any = false;
        while (n && n.tagName === 'DETAILS') {
          if (n.style.display !== 'none') any = true;
          n = n.nextElementSibling;
        }
        h.style.display = any ? '' : 'none';
      });
    });
  }

  /* ------------------------------------------------------------- forms */
  document.addEventListener('submit', function (ev) {
    var f = ev.target;
    if (f.matches('[data-newsletter]')) {
      ev.preventDefault();
      var i = f.querySelector('input[type=email]');
      if (!i.checkValidity()) { i.reportValidity(); return; }
      i.value = '';
      toast('Subscribed. Marketing consent is recorded separately from service messages.');
      return;
    }
    if (f.matches('[data-contact]')) {
      ev.preventDefault();
      if (!f.checkValidity()) { f.reportValidity(); return; }
      f.reset();
      toast('Enquiry sent. We reply within one working day.');
    }
  });
})();
