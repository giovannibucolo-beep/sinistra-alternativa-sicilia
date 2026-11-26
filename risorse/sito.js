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
