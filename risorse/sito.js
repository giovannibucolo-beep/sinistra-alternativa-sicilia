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
  var _m = doc.getElementById('sa-misure');
  var M = null;
  try { M = _m ? JSON.parse(_m.textContent) : null; } catch (e) { M = null; }
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

  // Fotografia che non c'è ancora: al suo posto il segnaposto, senza lasciare un riquadro vuoto
  doc.querySelectorAll('img[data-se-manca]').forEach(function (im) {
    var manca = function () { var f = im.parentNode; if (!f) return; f.classList.add('vuota'); f.dataset.et = im.dataset.seManca; im.remove(); };
    im.addEventListener('error', manca);
    if (im.complete && im.naturalWidth === 0) manca();
  });

  // Copia il link della pagina (accanto ai pulsanti di condivisione)
  doc.querySelectorAll('[data-copia]').forEach(function (b2) {
    b2.addEventListener('click', function () {
      var fatto = function () { var o = b2.textContent; b2.textContent = 'Link copiato'; setTimeout(function () { b2.textContent = o; }, 2500); };
      if (navigator.clipboard) navigator.clipboard.writeText(b2.dataset.copia).then(fatto, function () { prompt('Copia il link:', b2.dataset.copia); });
      else prompt('Copia il link:', b2.dataset.copia);
    });
  });

  // Modulo di adesione: due passi, persona oppure organizzazione
  var f = doc.getElementById('adesione');
  if (f) {
    var g = function (k) { return f.querySelector('[name=' + k + ']'); }, out = f.querySelector('.esito'), org = f.querySelector('.solo-org'), etn = f.querySelector('.et-nome'), num = f.querySelector('.passo-n b');
    var qs = new URLSearchParams(location.search), pv = qs.get('provincia'), tv = qs.get('tavolo');
    if (pv) Array.prototype.forEach.call(g('provincia').options, function (op) { if (op.value.toLowerCase() === pv.toLowerCase()) g('provincia').value = op.value; });
    if (tv) g('tavolo').value = tv;
    var eOrg = function () { return f.querySelector('[name=chi]:checked').value === 'organizzazione'; };
    var chi = function () { org.hidden = !eOrg(); etn.textContent = eOrg() ? 'Chi fa da riferimento' : 'Nome e cognome'; };
    Array.prototype.forEach.call(f.querySelectorAll('[name=chi]'), function (r) { r.addEventListener('change', chi); }); chi();
    var errore = function (t2, campo) { out.textContent = t2; campo.focus(); return false; };
    var passo = function (n) { f.classList.toggle('p2', n === 2); num.textContent = n; out.textContent = ''; var primo = f.querySelector('[data-passo="' + n + '"] input, [data-passo="' + n + '"] select'); if (primo) primo.focus(); };
    var primoPasso = function () {
      if (eOrg() && !g('organizzazione').value.trim()) return errore('Scrivi il nome dell’organizzazione.', g('organizzazione'));
      if (!g('nome').value.trim()) return errore('Scrivi nome e cognome.', g('nome'));
      if (!/^[^@ ]+@[^@ ]+[.][^@ ]+$/.test(g('email').value.trim())) return errore('Controlla l’indirizzo email.', g('email'));
      if (!g('provincia').value) return errore('Scegli la provincia.', g('provincia'));
      return true;
    };
    f.querySelector('[data-avanti]').addEventListener('click', function () { if (primoPasso()) passo(2); });
    f.querySelector('[data-indietro]').addEventListener('click', function () { passo(1); });
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!primoPasso()) return passo(1), primoPasso();
      if (!f.classList.contains('p2')) return passo(2);
      if (!g('consenso').checked) return errore('Serve il consenso per essere ricontattati.', g('consenso'));
      var nome = g('nome').value.trim(), o = eOrg();
      var dati = { chi: o ? 'organizzazione' : 'persona', organizzazione: o ? g('organizzazione').value.trim() : '', tipo_organizzazione: o ? g('tipo_organizzazione').value : '', nome: nome, email: g('email').value.trim(), telefono: g('telefono').value.trim(), comune: g('comune').value.trim(), provincia: g('provincia').value, tavolo: g('tavolo').value, mano: Array.prototype.map.call(f.querySelectorAll('[name=mano]:checked'), function (c) { return c.value; }), consenso: true, quando: new Date().toISOString() };
      var grazie = function (nota) {
        var d = doc.createElement('div'); d.className = 'fatto'; d.setAttribute('role', 'status');
        var t3 = doc.createElement('b'); t3.textContent = 'Grazie, ' + (o ? dati.organizzazione : nome.split(' ')[0]) + '.';
        var r = doc.createElement('p'); r.textContent = 'Adesione registrata per la provincia di ' + dati.provincia + '. Ti scriveremo per il prossimo incontro nel tuo territorio.';
        d.appendChild(t3); d.appendChild(r);
        if (dati.mano.indexOf('Contributo in denaro') > -1) { var c2 = doc.createElement('p'); c2.textContent = 'Per il contributo in denaro ti ricontatteremo noi: dal sito non si raccolgono pagamenti.'; d.appendChild(c2); }
        if (nota) { var n = doc.createElement('p'); n.style.fontSize = '14px'; n.textContent = nota; d.appendChild(n); }
        f.innerHTML = ''; f.appendChild(d);
      };
      if (g('sito_web').value) return grazie('');
      var dove = f.dataset.inviaA;
      if (!dove) return grazie('Dimostrazione: il modulo non è ancora collegato, nessun dato è stato inviato o conservato.');
      out.textContent = 'Invio in corso…';
      fetch(dove, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(dati) })
        .then(function (r) { if (!r.ok) throw new Error(r.status); grazie(''); })
        .catch(function () { out.textContent = 'Invio non riuscito. Riprova fra poco, oppure scrivici dai contatti.'; });
    });
  }
})();
