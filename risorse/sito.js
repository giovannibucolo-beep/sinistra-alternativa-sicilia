/* Sinistra per l'Alternativa — comportamento comune a tutte le pagine. Nessuna libreria esterna. */
(function () {
  var doc = document, fermo = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Menu su telefono
  var b = doc.querySelector('.menu-b'), m = doc.getElementById('menu');
  if (b && m) {
    var chiudi = function () { m.classList.remove('aperto'); b.setAttribute('aria-expanded', 'false'); doc.body.style.overflow = ''; };
    b.addEventListener('click', function () {
      var ap = m.classList.toggle('aperto'); b.setAttribute('aria-expanded', ap ? 'true' : 'false'); doc.body.style.overflow = ap ? 'hidden' : '';
    });
    m.addEventListener('click', function (e) { if (e.target.closest('a')) chiudi(); });
    addEventListener('keydown', function (e) { if (e.key === 'Escape') chiudi(); });
    matchMedia('(min-width: 1000px)').addEventListener('change', chiudi);
  }

  // Verbi che si accendono a turno in apertura
  var vv = doc.querySelectorAll('.verbi li');
  if (vv.length) {
    var i = 0; vv[0].classList.add('on');
    if (fermo) vv.forEach(function (v) { v.classList.add('on'); });
    else setInterval(function () { vv[i].classList.remove('on'); i = (i + 1) % vv.length; vv[i].classList.add('on'); }, 1900);
  }

  // Comparsa morbida allo scorrimento
  var rr = doc.querySelectorAll('.riv');
  if ('IntersectionObserver' in window && !fermo) {
    var o = new IntersectionObserver(function (es) { es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add('vis'); o.unobserve(x.target); } }); }, { threshold: 0.05 });
    rr.forEach(function (e) { o.observe(e); });
  } else rr.forEach(function (e) { e.classList.add('vis'); });

  // Fotografie: se il file indicato esiste lo mostra, altrimenti resta il segnaposto
  doc.querySelectorAll('.foto[data-file]').forEach(function (f) {
    var im = new Image(); im.onload = function () { f.style.backgroundImage = 'url("' + im.src + '")'; f.classList.remove('vuota'); }; im.src = f.dataset.file;
  });

  // Misure delle visite. Senza cookie: partono subito. Con cookie: solo dopo il sì, categoria per categoria; rifiuto e × valgono uguale.
  var M = window.SA_MISURE;
  if (M) {
    var metti = function (src, attr) { var s = doc.createElement('script'); s.async = true; s.src = src; for (var k in (attr || {})) s.setAttribute(k, attr[k]); doc.head.appendChild(s); };
    if (M.gc) metti('https://gc.zgo.at/count.js', { 'data-goatcounter': 'https://' + M.gc + '.goatcounter.com/count' });
    if (M.ga || M.fb) {
      var CH = 'sa-consenso', SEI_MESI = 180 * 864e5, scelta = null, partiti = {};
      try { var o = JSON.parse(localStorage.getItem(CH)); if (o && o.v && Date.now() - o.t < SEI_MESI) scelta = o.v; } catch (e) {}
      var carica = function (v) {
        if (M.ga && v.ga && !partiti.ga) { partiti.ga = 1; window.dataLayer = window.dataLayer || []; window.gtag = function () { dataLayer.push(arguments); }; gtag('js', new Date()); gtag('config', M.ga, { anonymize_ip: true }); metti('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(M.ga)); }
        if (M.fb && v.fb && !partiti.fb) { partiti.fb = 1; var f = window.fbq = function () { f.callMethod ? f.callMethod.apply(f, arguments) : f.queue.push(arguments); }; f.push = f; f.loaded = true; f.version = '2.0'; f.queue = []; metti('https://connect.facebook.net/it_IT/fbevents.js'); fbq('init', M.fb); fbq('track', 'PageView'); }
      };
      var decidi = function (v) {
        var tolto = (partiti.ga && !v.ga) || (partiti.fb && !v.fb); scelta = v;
        try { localStorage.setItem(CH, JSON.stringify({ v: v, t: Date.now() })); } catch (e) {}
        var a = doc.getElementById('avviso-cookie'); if (a) a.remove();
        if (tolto) { doc.cookie.split(';').forEach(function (c) { var n = c.split('=')[0].trim(); if (/^(_ga|_gid|_gat|_fb)/.test(n)) { doc.cookie = n + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/'; doc.cookie = n + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=.' + location.hostname; } }); location.reload(); }
        else carica(v);
      };
      var mostra = function () {
        if (doc.getElementById('avviso-cookie')) return;
        var s = scelta || {}, a = doc.createElement('div'); a.id = 'avviso-cookie'; a.setAttribute('role', 'dialog'); a.setAttribute('aria-label', 'Scelta sui cookie');
        a.innerHTML = '<button type="button" class="x" data-v="no" aria-label="Chiudi senza accettare">×</button><p><strong>Cookie.</strong> Il sito funziona senza. Con il tuo consenso usiamo cookie di terze parti per le statistiche e per misurare le campagne sui social. Se rifiuti o chiudi, non cambia nulla. <a href="' + (M.r || '') + 'cookie.html">Dettagli</a></p>'
          + '<div class="pers" hidden>' + (M.ga ? '<label><input type="checkbox" name="ga"' + (s.ga ? ' checked' : '') + '> Statistiche di visita (Google Analytics)</label>' : '') + (M.fb ? '<label><input type="checkbox" name="fb"' + (s.fb ? ' checked' : '') + '> Campagne sui social (pixel di Meta)</label>' : '') + '<button type="button" data-v="salva">Salva la scelta</button></div>'
          + '<div class="scelte"><button type="button" data-v="no">Rifiuta</button><button type="button" data-v="si">Accetta tutto</button><button type="button" class="sec" data-v="pers">Personalizza</button></div>';
        a.addEventListener('click', function (e) {
          var b2 = e.target.closest('[data-v]'); if (!b2) return; var v = b2.dataset.v;
          if (v === 'pers') { a.querySelector('.pers').hidden = false; b2.hidden = true; return; }
          if (v === 'salva') return decidi({ ga: !!(a.querySelector('[name=ga]') || {}).checked, fb: !!(a.querySelector('[name=fb]') || {}).checked });
          decidi({ ga: v === 'si', fb: v === 'si' });
        });
        doc.body.appendChild(a);
      };
      if (scelta) carica(scelta); else mostra();
      doc.querySelectorAll('[data-cookie-scelta]').forEach(function (b3) { b3.addEventListener('click', function (e) { e.preventDefault(); mostra(); }); });
    }
  }

  // Ricerca nel sito: scarica l'indice una volta e filtra mentre si scrive
  var q = doc.getElementById('q'), esiti = doc.getElementById('esiti');
  if (q && esiti) {
    var pulisci = function (s) { return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); };
    fetch('risorse/indice.json').then(function (r) { return r.json(); }).then(function (indice) {
      indice.forEach(function (v) { v.z = pulisci(v.t + ' ' + v.d + ' ' + v.x); v.zt = pulisci(v.t); });
      var cerca = function () {
        var parole = pulisci(q.value).split(/\s+/).filter(function (w) { return w.length > 1; }), conta = doc.getElementById('conta');
        esiti.innerHTML = '';
        if (!parole.length) { conta.textContent = ''; return; }
        var trovati = indice.filter(function (v) { return parole.every(function (w) { return v.z.indexOf(w) > -1; }); })
          .sort(function (a, b) { return (parole.some(function (w) { return b.zt.indexOf(w) > -1; }) ? 1 : 0) - (parole.some(function (w) { return a.zt.indexOf(w) > -1; }) ? 1 : 0); });
        conta.textContent = trovati.length ? trovati.length + (trovati.length === 1 ? ' risultato' : ' risultati') : 'Nessun risultato. Prova con una parola sola.';
        trovati.slice(0, 30).forEach(function (v) {
          var li = doc.createElement('li'), a = doc.createElement('a'), s = doc.createElement('span'), et = doc.createElement('span'), t = doc.createElement('strong'), d = doc.createElement('span');
          a.className = 'evento'; a.href = v.u; et.className = 'et'; et.textContent = v.k; t.textContent = v.t; d.textContent = v.d;
          s.appendChild(et); s.appendChild(t); s.appendChild(d); a.appendChild(s); li.appendChild(a); esiti.appendChild(li);
        });
      };
      q.addEventListener('input', cerca);
      var iniziale = new URLSearchParams(location.search).get('q'); if (iniziale) { q.value = iniziale; cerca(); }
    });
  }

  // Modulo di adesione
  var f = doc.getElementById('adesione');
  if (f) {
    var p = new URLSearchParams(location.search).get('provincia'), sel = f.querySelector('[name=provincia]');
    if (p && sel) Array.prototype.forEach.call(sel.options, function (op) { if (op.value.toLowerCase() === p.toLowerCase()) sel.value = op.value; });
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var g = function (k) { return f.querySelector('[name=' + k + ']'); }, out = f.querySelector('.esito');
      var nome = g('nome').value.trim(), email = g('email').value.trim();
      var errore = function (t, campo) { out.textContent = t; campo.focus(); };
      if (!nome) return errore('Scrivi nome e cognome.', g('nome'));
      if (!/^[^@ ]+@[^@ ]+[.][^@ ]+$/.test(email)) return errore('Controlla l’indirizzo email.', g('email'));
      if (!g('provincia').value) return errore('Scegli la provincia.', g('provincia'));
      if (!g('consenso').checked) return errore('Serve il consenso per essere ricontattati.', g('consenso'));
      var dati = { nome: nome, email: email, comune: g('comune').value.trim(), provincia: g('provincia').value, quando: new Date().toISOString() };
      var grazie = function (nota) {
        var d = doc.createElement('div'); d.className = 'fatto'; d.setAttribute('role', 'status');
        var t = doc.createElement('b'); t.textContent = 'Grazie, ' + nome.split(' ')[0] + '.';
        var r = doc.createElement('p'); r.textContent = 'Adesione registrata per la provincia di ' + dati.provincia + '. Ti scriveremo per il prossimo incontro nel tuo territorio.';
        var n = doc.createElement('p'); n.style.fontSize = '14px'; n.textContent = nota;
        d.appendChild(t); d.appendChild(r); if (nota) d.appendChild(n); f.innerHTML = ''; f.appendChild(d);
      };
      var dove = f.dataset.inviaA;
      if (!dove) return grazie('Dimostrazione: il modulo non è ancora collegato, nessun dato è stato inviato o conservato.');
      out.textContent = 'Invio in corso…';
      fetch(dove, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(dati) })
        .then(function (r) { if (!r.ok) throw new Error(r.status); grazie(''); })
        .catch(function () { out.textContent = 'Invio non riuscito. Riprova fra poco, oppure scrivici dai contatti.'; });
    });
  }
})();
