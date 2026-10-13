/* OMERO · web del proyecto
 * Lee data/proyecto.json, rellena la plantilla de index.html y anima la página.
 * Para actualizar la web NO hace falta tocar este archivo: ver ACTUALIZAR.md.
 */
(function () {
  'use strict';

  var DATA_URL = 'data/proyecto.json';
  var OBLIGATORIAS = ['meta', 'proyecto', 'enlaces', 'estado', 'sprints', 'calendario'];
  var ESTADOS = { 'hecho': 'Hecho', 'en-curso': 'En curso', 'pendiente': 'Pendiente' };
  var ENLACES = { notion: 'Notion', githubProjects: 'GitHub Projects', repositorio: 'Repositorio', carpetaCompartida: 'Carpeta compartida' };
  var MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  var ANIM = document.documentElement.classList.contains('anim');

  /* ---------- utilidades ---------- */

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
  function esc(v) {
    return String(v == null ? '' : v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function get(obj, path) { return path.split('.').reduce(function (o, k) { return o == null ? undefined : o[k]; }, obj); }
  function isEmpty(v) {
    if (v == null || v === '') return true;
    if (Array.isArray(v)) return v.length === 0;
    if (typeof v === 'object') return Object.keys(v).length === 0;
    return false;
  }
  function html(el, markup) { if (el) el.innerHTML = markup; }
  function list(arr, fn) { return (arr || []).map(fn).join(''); }

  // Fechas "AAAA-MM-DD" como fecha local (sin desfase de zona horaria)
  function parseDate(s) { if (!s) return null; var p = String(s).split('-').map(Number); return new Date(p[0], p[1] - 1, p[2]); }
  function today() { var d = new Date(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  function daysBetween(a, b) { return Math.round((b - a) / 86400000); }
  function fmt(s, conAnio) {
    var d = parseDate(s);
    return d ? d.getDate() + ' ' + MESES[d.getMonth()] + (conAnio ? ' ' + d.getFullYear() : '') : '';
  }
  function slug(s) { return String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-'); }

  var ICON = {
    ext: '<svg class="ext" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17L17 7M9 7h8v8"/></svg>',
    check: '<svg class="ck" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.6 2.5L16 9.5"/></svg>',
    chevron: '<svg class="chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>',
    arrow: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
  };
  var VERB_ICONS = [
    '<path d="M4 18v-6M9 18V8M14 18v-4M19 18V5"/>',
    '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    '<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
    '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
    '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>'
  ];
  function icon(paths) { return '<span class="ibox"><svg viewBox="0 0 24 24" aria-hidden="true">' + paths + '</svg></span>'; }

  function fail(msg, detalle) {
    console.error('[OMERO] ' + msg, detalle || '');
    var box = $('#load-error');
    box.hidden = false;
    box.innerHTML = '<div class="wrap"><strong>No se ha podido cargar la web.</strong> ' + esc(msg) +
      (location.protocol === 'file:' ? ' <br>Has abierto el archivo directamente: arranca un servidor con <code>python3 -m http.server</code> en la carpeta de la web y entra en <code>http://localhost:8000</code>.' : '') +
      '</div>';
    document.documentElement.classList.add('is-ready', 'is-error');
  }

  /* ---------- botones de enlace (vacío = "Próximamente") ---------- */

  function linkButton(url, label, variant, size, extra) {
    var cls = 'btn btn--' + (variant || 'primary') + (size ? ' btn--' + size : '') + (extra ? ' ' + extra : '');
    if (!url) {
      return '<span class="' + cls + ' is-disabled" aria-disabled="true" title="' + esc(label) + ': próximamente">' +
        esc(label) + ' <small>Próximamente</small></span>';
    }
    return '<a class="' + cls + '" href="' + esc(url) + '" target="_blank" rel="noopener">' + esc(label) + ICON.ext +
      '<span class="sr-only"> (se abre en una pestaña nueva)</span></a>';
  }

  /* ---------- cálculos de sprint ---------- */

  function puntosTotales(s) {
    if (typeof s.puntosTotales === 'number') return s.puntosTotales;
    return (s.tareas || []).reduce(function (n, t) { return n + (Number(t.puntos) || 0); }, 0);
  }
  function puntosHechos(s) {
    if (typeof s.puntosHechos === 'number') return s.puntosHechos;
    return (s.tareas || []).reduce(function (n, t) { return n + (t.estado === 'hecho' ? (Number(t.puntos) || 0) : 0); }, 0);
  }
  // Anteriores al actual = hecho, actual = en curso, siguientes = pendiente. Un "hecho" explícito se respeta.
  function estadoSprint(s, actual) {
    if (s.estado === 'hecho' || s.numero < actual) return 'hecho';
    return s.numero === actual ? 'en-curso' : 'pendiente';
  }

  /* ---------- render ---------- */

  function renderBindings(d) {
    $$('[data-bind]').forEach(function (el) {
      var v = get(d, el.getAttribute('data-bind'));
      if (isEmpty(v)) { el.hidden = true; return; }
      el.textContent = v;
    });
  }

  function hideEmpty(d) {
    $$('[data-requires]').forEach(function (el) {
      if (isEmpty(get(d, el.getAttribute('data-requires')))) el.hidden = true;
    });
  }

  function renderLinks(d) {
    $$('[data-link]').forEach(function (el) {
      el.outerHTML = linkButton(d.enlaces[el.getAttribute('data-link')], el.getAttribute('data-label'),
        el.getAttribute('data-variant'), el.getAttribute('data-size'), el.getAttribute('data-class'));
    });
  }

  function renderNav() {
    var secs = $$('section[data-nav]').filter(function (s) { return !s.hidden; });
    var a = function (s) { return '<li><a href="#' + s.id + '">' + esc(s.getAttribute('data-nav')) + '</a></li>'; };
    html($('#nav-primary'), secs.filter(function (s) { return s.hasAttribute('data-primary'); }).map(a).join(''));
    html($('#nav-all'), secs.map(a).join(''));
    html($('#footer-nav'), secs.map(a).join(''));
  }

  function renderHero(d) {
    var actual = d.estado.sprintActual;
    var s = d.sprints.filter(function (x) { return x.numero === actual; })[0];
    var badge = $('#sprint-badge');
    if (s) {
      var st = estadoSprint(s, actual);
      badge.innerHTML = '<span class="sem" aria-hidden="true"><i></i><i></i><i></i></span>' +
        esc((d.estado.fase ? d.estado.fase + ' · ' : '') + 'Sprint ' + s.numero + ' · ' + ESTADOS[st]) +
        (d.estado.mensaje ? ' <span class="pill__sep" aria-hidden="true">—</span> ' + esc(d.estado.mensaje) : '');
    } else badge.hidden = true;

    var cap = d.proyecto.capturaHero;
    var frame = $('#hero-frame');
    if (cap && cap.src) { var img = $('#hero-shot'); img.src = cap.src; img.alt = cap.alt || ''; }
    else frame.hidden = true;
  }

  function renderMarquee(d) {
    // Solo las tecnologías de arquitectura.stack; se repiten para llenar la franja
    var base = [];
    ((d.arquitectura || {}).stack || []).forEach(function (s) { base = base.concat(s.items || []); });
    if (!base.length) { $('.marquee').hidden = true; return; }
    var items = [];
    while (items.length < 12) items = items.concat(base);
    var row = function (hidden) {
      return '<ul class="marquee__row"' + (hidden ? ' aria-hidden="true"' : '') + '>' +
        items.map(function (t, i) { return '<li' + (i >= base.length ? ' aria-hidden="true"' : '') + '><span class="marquee__dot" aria-hidden="true"></span>' + esc(t) + '</li>'; }).join('') + '</ul>';
    };
    html($('#marquee'), row(false) + row(true));
  }

  function renderProblema(d) {
    var stats = [
      [(d.roles || []).length, 'Roles de usuario'],
      [(d.zonas || []).length, 'Zonas de la maqueta'],
      [(d.componentes || []).length, 'Componentes'],
      [(d.sprints || []).length, 'Sprints en S1']
    ].filter(function (x) { return x[0] > 0; });
    var icons = [VERB_ICONS[1], '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
      '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
      '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'];
    html($('#stats'), list(stats, function (s, i) {
      return '<li class="stat">' + icon(icons[i]) + '<div><p class="stat__n" data-count="' + s[0] + '">' + s[0] + '</p><p class="stat__l">' + esc(s[1]) + '</p></div></li>';
    }));
    html($('#referencias'), list(d.proyecto.referencias, function (r) { return '<li>' + esc(r) + '</li>'; }));
  }

  function renderSistema(d) {
    html($('#capacidades'), list(d.capacidades, function (c, i) {
      return '<li class="card card--white feature">' + icon(VERB_ICONS[i % VERB_ICONS.length]) +
        '<h3>' + esc(c.verbo) + '</h3><p>' + esc(c.texto) + '</p></li>';
    }));
    html($('#flujo'), list(d.flujoAlerta, function (f, i, arr) {
      var sem = f.paso === 'Semáforo' ? '<span class="sem sem--on" aria-hidden="true"><i></i><i></i><i></i></span>' : '';
      return '<li class="flow__step"><span class="flow__n">0' + (i + 1) + '</span><strong>' + esc(f.paso) + '</strong>' + sem +
        '<span class="flow__d">' + esc(f.detalle) + '</span>' +
        (i < arr.length - 1 ? '<span class="flow__arrow" aria-hidden="true">' + ICON.arrow + '</span>' : '') + '</li>';
    }));
    html($('#funcionalidades'), list(d.funcionalidades, function (f) { return '<li>' + ICON.check + '<span>' + esc(f) + '</span></li>'; }));
  }

  /* Pestañas accesibles: role=tab, flechas izquierda/derecha */
  function makeTabs(tablist, panels, onChange) {
    var tabs = $$('[role="tab"]', tablist);
    function select(i, focus) {
      tabs.forEach(function (t, j) {
        var on = i === j;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        if (panels[j]) { panels[j].hidden = !on; if (on) { panels[j].classList.remove('swap'); void panels[j].offsetWidth; panels[j].classList.add('swap'); } }
      });
      if (focus) tabs[i].focus();
      if (onChange) onChange(i);
    }
    tablist.addEventListener('click', function (e) { var t = e.target.closest('[role="tab"]'); if (t) select(tabs.indexOf(t)); });
    tablist.addEventListener('keydown', function (e) {
      var i = tabs.indexOf(document.activeElement);
      if (i < 0) return;
      if (e.key === 'ArrowRight') { e.preventDefault(); select((i + 1) % tabs.length, true); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); select((i - 1 + tabs.length) % tabs.length, true); }
    });
    select(0);
  }

  function renderRoles(d) {
    var roles = d.roles || [];
    html($('#roles-tabs'), list(roles, function (r, i) {
      return '<button type="button" role="tab" class="tab" id="rol-tab-' + i + '" aria-controls="rol-panel-' + i + '">' + esc(r.nombre) + '</button>';
    }));
    html($('#roles-panels'), list(roles, function (r, i) {
      var m = r.mockup || {};
      return '<div class="split" role="tabpanel" id="rol-panel-' + i + '" aria-labelledby="rol-tab-' + i + '" tabindex="0">' +
        '<div class="split__text">' +
          '<h3 class="h3">' + esc(r.nombre) + '</h3>' +
          (r.detalle ? '<p class="split__kicker">' + esc(r.detalle) + '</p>' : '') +
          '<p class="split__p">' + esc(r.descripcion) + '</p>' +
          '<p class="label">Sensores</p>' +
          '<ul class="checklist checklist--1">' + list(r.sensores, function (s) { return '<li>' + ICON.check + '<span>' + esc(s) + '</span></li>'; }) + '</ul>' +
        '</div>' +
        (m.src ? '<div class="media"><div class="media__bg" aria-hidden="true"></div><img src="' + esc(m.src) + '" alt="' + esc(m.alt || r.nombre) + '" loading="lazy" decoding="async" width="2560" height="1600"></div>' : '') +
      '</div>';
    }));
    makeTabs($('#roles-tabs'), $$('#roles-panels [role="tabpanel"]'));
    var regla = $('#regla-negocio');
    if (d.reglaNegocio) regla.innerHTML = '<strong>Regla de negocio.</strong> ' + esc(d.reglaNegocio); else regla.hidden = true;
  }

  function renderZonas(d) {
    var zonas = d.zonas || [], comps = d.componentes || [];
    html($('#zonas-list'), list(zonas, function (z, i) {
      var n = comps.filter(function (c) { return (c.zonas || []).indexOf(z.id) !== -1; }).length;
      return '<li class="card card--white zone zone--' + i + '">' +
        '<div class="zone__top"><span class="pill pill--sm">Zona ' + (i + 1) + '</span><span class="sem sem--on" aria-hidden="true"><i></i><i></i><i></i></span></div>' +
        '<div class="zone__body"><p class="zone__n"><span data-count="' + n + '">' + n + '</span><small> componentes</small></p>' +
        '<h3>' + esc(z.nombre) + '</h3>' + (z.detalle ? '<p class="zone__detail">' + esc(z.detalle) + '</p>' : '') +
        '<p>' + esc(z.contenido) + '</p></div></li>';
    }));

    var filtros = [{ id: '*', nombre: 'Todas' }].concat(zonas);
    html($('#filtros'), list(filtros, function (f, i) {
      return '<button type="button" class="tab" data-zona="' + esc(f.id) + '" aria-pressed="' + (i === 0) + '">' + esc(f.nombre) + '</button>';
    }));
    function pintar(zona) {
      html($('#componentes'), comps.filter(function (c) { return zona === '*' || (c.zonas || []).indexOf(zona) !== -1; }).map(function (c, i) {
        return '<tr style="--d:' + (i * 40) + 'ms"><th scope="row">' + esc(c.nombre) + '</th>' +
          '<td data-label="Tipo"><span class="tag tag--' + slug(c.tipo) + '">' + esc(c.tipo) + '</span></td>' +
          '<td data-label="Zona">' + esc(c.zonaTexto) + '</td><td data-label="Uso">' + esc(c.uso) + '</td><td data-label="Alerta">' + esc(c.alerta) + '</td></tr>';
      }).join(''));
    }
    pintar('*');
    $('#filtros').addEventListener('click', function (e) {
      var b = e.target.closest('.tab');
      if (!b) return;
      $$('#filtros .tab').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
      pintar(b.getAttribute('data-zona'));
    });

    var nota = $('#nota-umbrales');
    if (d.notaUmbrales) nota.textContent = d.notaUmbrales; else nota.hidden = true;
    html($('#descartados'), list(d.componentesDescartados, function (c) {
      return '<li class="card card--white card--muted"><h3>' + esc(c.nombre) + '</h3><p>' + esc(c.motivo) + '</p></li>';
    }));
  }

  function highlightJSON(obj) {
    return esc(JSON.stringify(obj, null, 2)).replace(/(&quot;(?:[^&]|&(?!quot;))*?&quot;)(\s*:)?|\b(-?\d+(?:\.\d+)?)\b|\b(true|false|null)\b/g,
      function (m, str, colon, num, lit) {
        if (str) return '<span class="' + (colon ? 'j-key' : 'j-str') + '">' + str + '</span>' + (colon || '');
        if (num) return '<span class="j-num">' + num + '</span>';
        return '<span class="j-lit">' + lit + '</span>';
      });
  }

  function renderArquitectura(d) {
    var a = d.arquitectura || {};
    html($('#capas'), list(a.capas, function (c, i) {
      return '<li><span class="layers__n">0' + (i + 1) + '</span><strong>' + esc(c.nombre) + '</strong><span>' + esc(c.descripcion) + '</span></li>';
    }));
    html($('#modelo'), list(a.modelo, function (m) { return '<li><code>' + esc(m) + '</code></li>'; }));
    $('#carpetas').textContent = a.carpetas || '';
    html($('#ejemplo-lectura'), a.ejemploLectura ? highlightJSON(a.ejemploLectura) : '');
    html($('#stack'), list(a.stack, function (s) {
      return '<div class="card card--gray" data-reveal><p class="label">' + esc(s.fase) + '</p><ul class="chips chips--lg">' +
        list(s.items, function (i) { return '<li>' + esc(i) + '</li>'; }) + '</ul></div>';
    }));
  }

  function sprintCard(s, actual, featured) {
    var st = estadoSprint(s, actual);
    var tot = puntosTotales(s), done = puntosHechos(s);
    var pct = tot ? Math.round(done / tot * 100) : 0;
    var tareas = s.tareas || [];
    var tasksHTML = list(tareas, function (t) {
      return '<li class="task task--' + esc(t.estado) + '">' + ICON.check + '<span class="task__t"><span class="task__id">' + esc(t.id) + '</span> ' + esc(t.titulo) +
        '</span><span class="task__p">' + esc(t.puntos) + '</span><span class="sr-only">puntos, ' + esc(ESTADOS[t.estado] || t.estado) + '</span></li>';
    });
    return '<article class="sprint' + (featured ? ' sprint--featured' : '') + ' sprint--' + st + '" data-reveal' +
      (s.numero === actual ? ' aria-current="step"' : '') + '>' +
      (featured ? '<div class="sprint__bg" aria-hidden="true"></div>' : '') +
      '<div class="sprint__head"><p class="sprint__n">Sprint ' + esc(s.numero) + '</p>' +
        '<span class="status status--' + st + '">' + ESTADOS[st] + '</span>' +
        (s.provisional ? '<span class="status status--prov">Provisional</span>' : '') + '</div>' +
      '<h3 class="sprint__title">' + esc(s.entregable || s.nombre) + '</h3>' +
      '<p class="sprint__dates">' + fmt(s.fechaInicio) + ' – ' + fmt(s.fechaFin, true) + '</p>' +
      '<p class="sprint__pts"><span data-count="' + done + '">' + done + '</span><small> / ' + tot + ' pts</small></p>' +
      '<div class="bar" role="progressbar" aria-label="Progreso del sprint ' + esc(s.numero) + '" aria-valuemin="0" aria-valuemax="' + tot + '" aria-valuenow="' + done + '" style="--p:' + pct + '%"><span></span></div>' +
      '<p class="sprint__pct">' + pct + '% completado</p>' +
      (tareas.length ? (featured
        ? '<p class="label">Tareas · ' + tareas.length + '</p><ul class="tasks tasks--2">' + tasksHTML + '</ul>'
        : '<details class="sprint__more"><summary>Tareas · ' + tareas.length + ICON.chevron + '</summary><ul class="tasks">' + tasksHTML + '</ul></details>') : '') +
    '</article>';
  }

  function renderRoadmap(d) {
    var actual = d.estado.sprintActual;
    var cur = d.sprints.filter(function (s) { return s.numero === actual; })[0];
    var rest = d.sprints.filter(function (s) { return s !== cur; });
    html($('#sprints'), (cur ? sprintCard(cur, actual, true) : '') + '<div class="sprints__rest">' + list(rest, function (s) { return sprintCard(s, actual, false); }) + '</div>');

    var tot = d.sprints.reduce(function (n, s) { return n + puntosTotales(s); }, 0);
    var done = d.sprints.reduce(function (n, s) { return n + puntosHechos(s); }, 0);
    html($('#roadmap-aside'), '<strong>' + done + ' / ' + tot + ' puntos</strong> completados en ' + d.sprints.length + ' sprints.');

    html($('#fases-s2'), list(d.fasesS2, function (f, i) { return '<li class="phase"><span>' + (i + 1) + '</span><p>' + esc(f) + '</p></li>'; }));
    var c = $('#cierre-s2');
    if (d.cierreS2) c.innerHTML = '<strong>Cierre de S2.</strong> ' + esc(d.cierreS2); else c.hidden = true;
  }

  function renderCalendario(d) {
    var hoy = today();
    var eventos = d.calendario.slice().sort(function (a, b) { return parseDate(a.fecha) - parseDate(b.fecha); });
    var siguiente = eventos.filter(function (e) { return /entrega|defensa/i.test(e.tipo) && parseDate(e.fecha) >= hoy; })[0];

    var cd = $('#countdown');
    if (siguiente) {
      var dias = daysBetween(hoy, parseDate(siguiente.fecha));
      cd.innerHTML = '<div class="countdown__bg" aria-hidden="true"></div><p class="pill pill--glass">Siguiente entrega</p>' +
        '<p class="countdown__num">' + (dias === 0 ? '¡Hoy!' : '<span data-count="' + dias + '">' + dias + '</span><small>' + (dias === 1 ? ' día' : ' días') + '</small>') + '</p>' +
        '<p class="countdown__what">' + esc(siguiente.titulo) + '</p>' +
        '<p class="countdown__date"><time datetime="' + esc(siguiente.fecha) + '">' + fmt(siguiente.fecha, true) + '</time></p>';
    } else {
      cd.innerHTML = '<div class="countdown__bg" aria-hidden="true"></div><p class="pill pill--glass">Siguiente entrega</p><p class="countdown__what">No quedan entregas en el calendario.</p>';
    }

    html($('#cal-list'), eventos.map(function (e) {
      var f = parseDate(e.fecha);
      var cls = +f === +hoy ? 'is-today' : (f < hoy ? 'is-past' : (e === siguiente ? 'is-next' : ''));
      return '<li class="cal ' + cls + '"><time datetime="' + esc(e.fecha) + '"><b>' + f.getDate() + '</b> ' + MESES[f.getMonth()] + ' ' + String(f.getFullYear()).slice(2) + '</time>' +
        '<span class="cal__t">' + esc(e.titulo) + (cls === 'is-today' ? ' <span class="today">Hoy</span>' : '') + '</span>' +
        '<span class="tag tag--' + slug(e.tipo) + '">' + esc(e.tipo) + '</span>' +
        (e === siguiente ? '<span class="sr-only"> (siguiente entrega)</span>' : '') + '</li>';
    }).join(''));

    html($('#contenido-entrega'), list(d.contenidoEntregaSprint, function (c) { return '<li>' + ICON.check + '<span>' + esc(c) + '</span></li>'; }));
    html($('#festivos'), list(d.festivos, function (f) {
      return '<li>' + esc(!f.hasta || f.desde === f.hasta ? fmt(f.desde, true) : fmt(f.desde, true) + ' – ' + fmt(f.hasta, true)) + '</li>';
    }));
  }

  function renderEquipo(d) {
    var actual = d.estado.sprintActual;
    var e = d.empresa;
    var emp = $('#empresa');
    if (e) emp.innerHTML = '<strong>' + esc(e.nombre) + '</strong>' + (e.tipo ? ' · ' + esc(e.tipo) : '') + '. ' + esc(e.descripcion); else emp.hidden = true;

    html($('#equipo-list'), list(d.equipo, function (p) {
      var ini = p.nombre.split(/\s+/).map(function (w) { return w[0]; }).slice(0, 2).join('');
      return '<li class="member"><span class="member__av" aria-hidden="true">' + esc(ini) + '</span><div>' +
        '<p class="member__name">' + esc(p.nombre) + '</p>' +
        (p.github ? '<a class="member__gh" href="https://github.com/' + esc(p.github) + '" target="_blank" rel="noopener">@' + esc(p.github) + '<span class="sr-only"> en GitHub (pestaña nueva)</span></a>' : '') +
        '</div></li>';
    }));

    html($('#rotacion'), list(d.rotacionScrum, function (r) {
      var cur = r.sprint === actual;
      return '<tr' + (cur ? ' class="is-current" aria-current="true"' : '') + '><th scope="row">Sprint ' + esc(r.sprint) +
        (cur ? ' <span class="status status--en-curso">Actual</span>' : '') + '</th><td>' + esc(r.productOwner) + '</td><td>' + esc(r.scrumMaster) + '</td></tr>';
    }));
  }

  var galeria = [];
  function renderGaleria(d) {
    galeria = d.galeria || [];
    var tipos = [];
    galeria.forEach(function (g) { if (tipos.indexOf(g.tipo) === -1) tipos.push(g.tipo); });
    html($('#galeria-tabs'), list(tipos, function (t, i) {
      return '<button type="button" role="tab" class="tab" id="gal-tab-' + i + '" aria-controls="gal-panel-' + i + '">' + esc(t) + 's</button>';
    }));
    html($('#galeria'), list(tipos, function (t, i) {
      return '<ul class="gallery" role="tabpanel" id="gal-panel-' + i + '" aria-labelledby="gal-tab-' + i + '">' +
        galeria.map(function (g, gi) { return g.tipo !== t ? '' :
          '<li><button type="button" class="shot" data-i="' + gi + '" aria-label="Ampliar: ' + esc(g.titulo) + '">' +
          '<span class="shot__img"><img src="' + esc(g.thumb || g.src) + '" alt="' + esc(g.alt || g.titulo) + '" loading="lazy" decoding="async" width="720" height="450"></span>' +
          '<span class="shot__t">' + esc(g.titulo) + '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg></span></button></li>';
        }).join('') + '</ul>';
    }));
    if (tipos.length < 2) $('#galeria-tabs').hidden = true;
    makeTabs($('#galeria-tabs'), $$('#galeria [role="tabpanel"]'));
  }

  function renderODS(d) {
    html($('#ods-list'), list(d.ods, function (o) {
      return '<li class="card card--gray ods"><p class="ods__n"><small>ODS</small>' + esc(o.numero) + '</p><h3>' + esc(o.nombre) + '</h3><p>' + esc(o.texto) + '</p></li>';
    }));
  }

  function renderEnlaces(d) {
    var keys = Object.keys(ENLACES).filter(function (k) { return k !== 'carpetaCompartida' || d.enlaces[k]; });
    html($('#enlaces-list'), keys.map(function (k, i) {
      return linkButton(d.enlaces[k], ENLACES[k], i === 0 ? 'white' : 'glass');
    }).join(''));
    html($('#footer-links'), keys.map(function (k) {
      var u = d.enlaces[k];
      return '<li>' + (u ? '<a href="' + esc(u) + '" target="_blank" rel="noopener">' + esc(ENLACES[k]) + '<span class="sr-only"> (pestaña nueva)</span></a>'
        : '<span class="muted">' + esc(ENLACES[k]) + ' · próximamente</span>') + '</li>';
    }).join(''));
  }

  function renderFooter(d) {
    var a = d.asignatura || {};
    html($('#footer-asignatura'), [a.nombre, a.grado, a.universidad, a.curso ? 'Curso ' + a.curso : '', a.docente ? 'Docente: ' + a.docente : '']
      .filter(Boolean).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join(''));
    html($('#footer-update'), 'Última actualización: <time datetime="' + esc(d.meta.ultimaActualizacion) + '">' + fmt(d.meta.ultimaActualizacion, true) + '</time>' +
      (d.meta.version ? ' · v' + esc(d.meta.version) : ''));
  }

  /* ---------- animaciones ---------- */

  // Parte un texto en palabras para la aparición con desenfoque (el texto real sigue siendo legible por lectores de pantalla)
  function splitWords(el) {
    var text = el.textContent;
    if (!text.trim()) return;
    el.setAttribute('aria-label', text.trim());
    el.innerHTML = text.trim().split(/\s+/).map(function (w, i) {
      return '<span class="w" aria-hidden="true" style="--i:' + i + '">' + esc(w) + '</span>';
    }).join(' ');
  }

  // Texto destacado que se "enciende" palabra a palabra según el scroll
  function initStatement() {
    var el = $('#statement');
    if (!el || el.hidden) return;
    var text = el.textContent.trim();
    el.innerHTML = text.split(/\s+/).map(function (w) { return '<span class="sw">' + esc(w) + '</span>'; }).join(' ');
    var words = $$('.sw', el);
    if (!ANIM) { words.forEach(function (w) { w.classList.add('on'); }); return; }
    return function () {
      var r = el.getBoundingClientRect(), vh = innerHeight;
      var p = Math.min(1, Math.max(0, (vh * 0.85 - r.top) / (vh * 0.85 - vh * 0.3 + r.height * 0.6)));
      var n = Math.round(p * words.length);
      words.forEach(function (w, i) { w.classList.toggle('on', i < n); });
    };
  }

  function countUp(el) {
    var to = Number(el.getAttribute('data-count'));
    if (!ANIM || !to) return;
    var t0 = null, dur = 1100;
    function step(t) {
      if (!t0) t0 = t;
      var k = Math.min(1, (t - t0) / dur);
      el.textContent = Math.round(to * (1 - Math.pow(1 - k, 3)));
      if (k < 1) requestAnimationFrame(step);
    }
    el.textContent = '0';
    requestAnimationFrame(step);
  }

  function initAnimations() {
    // Retrasos escalonados para los hijos de [data-stagger]
    $$('[data-stagger]').forEach(function (p) {
      Array.prototype.forEach.call(p.children, function (c, i) {
        if (!c.hasAttribute('data-reveal')) c.setAttribute('data-reveal', '');
        if (!c.style.getPropertyValue('--d')) c.style.setProperty('--d', (i * 0.08) + 's');
      });
    });
    $$('[data-split]').forEach(splitWords);

    var targets = $$('[data-reveal], [data-split], .bar, [data-count]');
    function show(el) {
      el.classList.add('in');
      if (el.hasAttribute('data-count')) countUp(el);
      $$('[data-count]', el).forEach(function (c) { if (!c.closest('[data-reveal]:not(.in)')) countUp(c); });
    }
    if (!ANIM || !('IntersectionObserver' in window)) { targets.forEach(function (t) { t.classList.add('in'); }); }
    else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          en.target.classList.add('in');
          if (en.target.hasAttribute('data-count')) countUp(en.target);
          io.unobserve(en.target);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
      targets.forEach(function (t) { io.observe(t); });
    }

    // Scroll: barra superior, inclinación del mockup del hero y texto destacado
    var nav = $('.nav'), hero = $('#hero'), frame = $('#hero-frame');
    var statement = initStatement();
    var ticking = false;
    function onScroll() {
      ticking = false;
      var y = scrollY;
      nav.classList.toggle('is-scrolled', y > 8);
      nav.classList.toggle('on-hero', hero.getBoundingClientRect().bottom > 64 + (frame && !frame.hidden ? frame.offsetHeight * 0.55 : 0));
      if (ANIM && frame) frame.style.setProperty('--tilt', Math.max(0, 1 - y / 520).toFixed(3));
      if (statement) statement();
    }
    addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
    addEventListener('resize', onScroll);
    onScroll();
  }

  /* ---------- interacción ---------- */

  function initTheme() {
    var btn = $('#theme-toggle');
    var mq = matchMedia('(prefers-color-scheme: dark)');
    function isDark() { var t = document.documentElement.dataset.theme; return t ? t === 'dark' : mq.matches; }
    function sync() { btn.setAttribute('aria-label', isDark() ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'); }
    btn.addEventListener('click', function () {
      var next = isDark() ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem('omero-tema', next); } catch (e) {}
      sync();
    });
    if (mq.addEventListener) mq.addEventListener('change', sync);
    sync();
  }

  function initMenu() {
    var btn = $('#menu-toggle'), menu = $('#menu');
    function set(open) {
      menu.hidden = !open;
      btn.setAttribute('aria-expanded', String(open));
      btn.setAttribute('aria-label', open ? 'Cerrar índice de secciones' : 'Abrir índice de secciones');
      document.documentElement.classList.toggle('menu-open', open);
    }
    btn.addEventListener('click', function () { set(menu.hidden); });
    menu.addEventListener('click', function (e) { if (e.target.closest('a')) set(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !menu.hidden) { set(false); btn.focus(); } });

    // Resalta en la barra la sección visible
    if (!('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        $$('.nav a[aria-current], .menu a[aria-current]').forEach(function (a) { a.removeAttribute('aria-current'); });
        $$('a[href="#' + en.target.id + '"]', $('.nav')).forEach(function (a) { a.setAttribute('aria-current', 'true'); });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    $$('section[data-nav]').forEach(function (s) { io.observe(s); });
  }

  function initLightbox() {
    var dlg = $('#lightbox'), img = $('#lb-img'), title = $('#lb-title'), idx = 0;
    if (!dlg.showModal) return;
    function show(i) {
      idx = (i + galeria.length) % galeria.length;
      var g = galeria[idx];
      img.src = g.src; img.alt = g.alt || g.titulo;
      title.textContent = g.titulo + ' · ' + (idx + 1) + '/' + galeria.length;
    }
    $('#galeria').addEventListener('click', function (e) {
      var b = e.target.closest('.shot');
      if (!b) return;
      show(Number(b.getAttribute('data-i')));
      dlg.showModal();
    });
    $('#lb-prev').addEventListener('click', function () { show(idx - 1); });
    $('#lb-next').addEventListener('click', function () { show(idx + 1); });
    $('#lb-close').addEventListener('click', function () { dlg.close(); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') show(idx - 1);
      if (e.key === 'ArrowRight') show(idx + 1);
    });
  }

  /* ---------- arranque ---------- */

  function validar(d) {
    var faltan = OBLIGATORIAS.filter(function (k) { return d[k] == null; });
    if (faltan.length) return 'Faltan claves obligatorias en proyecto.json: ' + faltan.join(', ') + '.';
    if (typeof d.estado.sprintActual !== 'number') return 'estado.sprintActual debe ser un número (0, 1, 2…).';
    if (!Array.isArray(d.sprints)) return '"sprints" debe ser una lista.';
    if (!Array.isArray(d.calendario)) return '"calendario" debe ser una lista.';
    var malos = [];
    d.sprints.forEach(function (s) { (s.tareas || []).forEach(function (t) { if (!ESTADOS[t.estado]) malos.push(t.id + ' ("' + t.estado + '")'); }); });
    if (malos.length) console.warn('[OMERO] Estados de tarea no válidos (usa pendiente | en-curso | hecho): ' + malos.join(', '));
    return null;
  }

  function render(d) {
    if (d.proyecto.nombre) document.title = d.proyecto.nombre;
    renderBindings(d);
    hideEmpty(d);
    renderLinks(d);
    renderHero(d);
    renderMarquee(d);
    renderProblema(d);
    renderSistema(d);
    renderRoles(d);
    renderZonas(d);
    renderArquitectura(d);
    renderRoadmap(d);
    renderCalendario(d);
    renderEquipo(d);
    renderGaleria(d);
    renderODS(d);
    renderEnlaces(d);
    renderFooter(d);
    renderNav();
    initMenu();
    initLightbox();
    initAnimations();
    document.documentElement.classList.add('is-ready');
  }

  initTheme();

  fetch(DATA_URL, { cache: 'no-cache' })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status + ' al pedir ' + DATA_URL);
      return r.text();
    })
    .then(function (txt) {
      var d;
      try { d = JSON.parse(txt); } catch (e) { throw new Error('proyecto.json no es JSON válido: ' + e.message + '. Revisa comas y comillas.'); }
      var err = validar(d);
      if (err) { fail(err); return; }
      try { render(d); } catch (e) { fail('Error al pintar la página: ' + e.message, e); }
    })
    .catch(function (e) { fail(e.message, e); });
})();
