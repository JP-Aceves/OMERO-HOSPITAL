/* OMERO · web del proyecto
 * Lee data/proyecto.json y rellena la plantilla de index.html.
 * Para actualizar la web NO hace falta tocar este archivo: ver web/ACTUALIZAR.md.
 */
(function () {
  'use strict';

  var DATA_URL = 'data/proyecto.json';
  var OBLIGATORIAS = ['meta', 'proyecto', 'enlaces', 'estado', 'sprints', 'calendario'];
  var ESTADOS = { 'hecho': 'Hecho', 'en-curso': 'En curso', 'pendiente': 'Pendiente' };
  var ENLACES = { notion: 'Notion', githubProjects: 'GitHub Projects', repositorio: 'Repositorio', carpetaCompartida: 'Carpeta compartida' };
  var MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

  /* ---------- utilidades ---------- */

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

  function esc(v) {
    return String(v == null ? '' : v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function get(obj, path) {
    return path.split('.').reduce(function (o, k) { return o == null ? undefined : o[k]; }, obj);
  }

  function isEmpty(v) {
    if (v == null || v === '') return true;
    if (Array.isArray(v)) return v.length === 0;
    if (typeof v === 'object') return Object.keys(v).length === 0;
    return false;
  }

  // Fechas "YYYY-MM-DD" como fecha local (sin desfase de zona horaria)
  function parseDate(s) {
    if (!s) return null;
    var p = String(s).split('-').map(Number);
    return new Date(p[0], p[1] - 1, p[2]);
  }
  function today() { var d = new Date(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  function daysBetween(a, b) { return Math.round((b - a) / 86400000); }
  function fmt(s, conAnio) {
    var d = parseDate(s);
    if (!d) return '';
    return d.getDate() + ' ' + MESES[d.getMonth()] + (conAnio ? ' ' + d.getFullYear() : '');
  }

  function html(el, markup) { if (el) el.innerHTML = markup; }

  function fail(msg, detalle) {
    console.error('[OMERO] ' + msg, detalle || '');
    var box = $('#load-error');
    box.hidden = false;
    box.innerHTML = '<div class="wrap"><strong>No se ha podido cargar la web.</strong> ' + esc(msg) +
      (location.protocol === 'file:' ? ' <br>Parece que has abierto el archivo directamente: arranca un servidor con <code>python3 -m http.server</code> dentro de <code>web/</code> y entra en <code>http://localhost:8000</code>.' : '') +
      '</div>';
  }

  /* ---------- botones de enlace (vacío = "Próximamente") ---------- */

  function linkButton(url, label, variant, size) {
    var cls = 'btn btn--' + (variant || 'primary') + (size ? ' btn--' + size : '');
    if (!url) {
      return '<span class="' + cls + ' is-disabled" aria-disabled="true" title="' + esc(label) + ': próximamente">' +
        esc(label) + ' <small>Próximamente</small></span>';
    }
    return '<a class="' + cls + '" href="' + esc(url) + '" target="_blank" rel="noopener">' + esc(label) +
      '<svg class="ext" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17L17 7M9 7h8v8"/></svg>' +
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
  // Estado efectivo: los anteriores al sprint actual están hechos, el actual en curso, los siguientes pendientes.
  // Si en el JSON un sprint está marcado "hecho" explícitamente, se respeta.
  function estadoSprint(s, actual) {
    if (s.estado === 'hecho') return 'hecho';
    if (s.numero < actual) return 'hecho';
    if (s.numero === actual) return 'en-curso';
    return 'pendiente';
  }

  /* ---------- render ---------- */

  function renderBindings(d) {
    $$('[data-bind]').forEach(function (el) {
      var v = get(d, el.getAttribute('data-bind'));
      if (isEmpty(v)) { el.hidden = true; return; }
      el.textContent = v;
    });
  }

  function renderLinks(d) {
    $$('[data-link]').forEach(function (el) {
      var key = el.getAttribute('data-link');
      el.outerHTML = linkButton(d.enlaces[key], el.getAttribute('data-label'), el.getAttribute('data-variant'), el.getAttribute('data-size'));
    });
  }

  function hideEmptySections(d) {
    $$('[data-requires]').forEach(function (el) {
      if (isEmpty(get(d, el.getAttribute('data-requires')))) el.hidden = true;
    });
  }

  function renderNav() {
    var items = $$('section[data-nav]').filter(function (s) { return !s.hidden; });
    html($('#nav-list'), items.map(function (s) {
      return '<li><a href="#' + s.id + '">' + esc(s.getAttribute('data-nav')) + '</a></li>';
    }).join(''));
  }

  function renderHero(d) {
    var actual = d.estado.sprintActual;
    var s = d.sprints.filter(function (x) { return x.numero === actual; })[0];
    var badge = $('#sprint-badge');
    if (!s) { badge.hidden = true; return; }
    var st = estadoSprint(s, actual);
    badge.innerHTML = '<span class="badge__dot badge__dot--' + st + '" aria-hidden="true"></span>' +
      esc((d.estado.fase ? d.estado.fase + ' · ' : '') + 'Sprint ' + s.numero) +
      ' <span class="badge__sep" aria-hidden="true">·</span> ' + esc(ESTADOS[st]);
    var tot = puntosTotales(s), done = puntosHechos(s);
    var msg = d.estado.mensaje ? esc(d.estado.mensaje) :
      'Sprint ' + esc(s.numero) + ': ' + esc(s.entregable) + ' · ' + fmt(s.fechaInicio) + ' – ' + fmt(s.fechaFin) +
      ' · ' + done + '/' + tot + ' pts';
    html($('#hero-status'), msg);
  }

  function renderProblema(d) {
    html($('#referencias'), (d.proyecto.referencias || []).map(function (r) { return '<li>' + esc(r) + '</li>'; }).join(''));
  }

  function renderSistema(d) {
    var icons = [
      '<path d="M4 18v-6M9 18V8M14 18v-4M19 18V5"/>',
      '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
      '<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
      '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
      '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>'
    ];
    html($('#capacidades'), (d.capacidades || []).map(function (c, i) {
      return '<li class="verb"><span class="verb__icon"><svg viewBox="0 0 24 24" aria-hidden="true">' + (icons[i % icons.length]) +
        '</svg></span><h3>' + esc(c.verbo) + '</h3><p>' + esc(c.texto) + '</p></li>';
    }).join(''));

    html($('#flujo'), (d.flujoAlerta || []).map(function (f, i, arr) {
      var extra = f.paso === 'Semáforo' ? '<span class="semaforo semaforo--sm" aria-hidden="true"><i></i><i></i><i></i></span>' : '';
      return '<li class="flow__step"><span class="flow__n">' + (i + 1) + '</span><strong>' + esc(f.paso) + '</strong>' +
        extra + '<span>' + esc(f.detalle) + '</span></li>' +
        (i < arr.length - 1 ? '<li class="flow__arrow" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></li>' : '');
    }).join(''));

    html($('#funcionalidades'), (d.funcionalidades || []).map(function (f) { return '<li>' + esc(f) + '</li>'; }).join(''));
  }

  function renderRoles(d) {
    html($('#roles-list'), (d.roles || []).map(function (r, i) {
      return '<article class="card role"><span class="role__n">0' + (i + 1) + '</span><h3>' + esc(r.nombre) + '</h3>' +
        (r.detalle ? '<p class="role__detail">' + esc(r.detalle) + '</p>' : '') +
        '<p>' + esc(r.descripcion) + '</p>' +
        '<ul class="chips chips--sm" aria-label="Sensores">' + (r.sensores || []).map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') + '</ul></article>';
    }).join(''));
    var regla = $('#regla-negocio');
    if (d.reglaNegocio) regla.innerHTML = '<strong>Regla de negocio:</strong> ' + esc(d.reglaNegocio); else regla.hidden = true;
  }

  function renderZonas(d) {
    var zonas = d.zonas || [];
    html($('#zonas-list'), zonas.map(function (z, i) {
      return '<li class="card zone"><span class="zone__n">Zona ' + (i + 1) + '</span><h3>' + esc(z.nombre) + '</h3>' +
        (z.detalle ? '<p class="zone__detail">' + esc(z.detalle) + '</p>' : '') + '<p>' + esc(z.contenido) + '</p></li>';
    }).join(''));

    var comps = d.componentes || [];
    var filtros = [{ id: '*', nombre: 'Todas' }].concat(zonas.map(function (z) { return { id: z.id, nombre: z.nombre }; }));
    html($('#filtros'), filtros.map(function (f, i) {
      return '<button type="button" class="filter" data-zona="' + esc(f.id) + '" aria-pressed="' + (i === 0) + '">' + esc(f.nombre) + '</button>';
    }).join(''));

    function pintar(zona) {
      html($('#componentes'), comps.filter(function (c) {
        return zona === '*' || (c.zonas || []).indexOf(zona) !== -1;
      }).map(function (c) {
        var tipo = String(c.tipo || '').toLowerCase();
        return '<tr><th scope="row">' + esc(c.nombre) + '</th><td data-label="Tipo"><span class="tag tag--' + esc(tipo) + '">' + esc(c.tipo) + '</span></td><td data-label="Zona">' +
          esc(c.zonaTexto) + '</td><td data-label="Uso">' + esc(c.uso) + '</td><td data-label="Alerta">' + esc(c.alerta) + '</td></tr>';
      }).join(''));
    }
    pintar('*');
    $('#filtros').addEventListener('click', function (e) {
      var b = e.target.closest('.filter');
      if (!b) return;
      $$('.filter').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
      pintar(b.getAttribute('data-zona'));
    });

    var nota = $('#nota-umbrales');
    if (d.notaUmbrales) nota.textContent = d.notaUmbrales; else nota.hidden = true;

    html($('#descartados'), (d.componentesDescartados || []).map(function (c) {
      return '<li class="card card--muted"><h4>' + esc(c.nombre) + '</h4><p>' + esc(c.motivo) + '</p></li>';
    }).join(''));
  }

  function highlightJSON(obj) {
    var json = esc(JSON.stringify(obj, null, 2));
    return json.replace(/(&quot;(?:[^&]|&(?!quot;))*?&quot;)(\s*:)?|\b(-?\d+(?:\.\d+)?)\b|\b(true|false|null)\b/g,
      function (m, str, colon, num, lit) {
        if (str) return '<span class="' + (colon ? 'j-key' : 'j-str') + '">' + str + '</span>' + (colon || '');
        if (num) return '<span class="j-num">' + num + '</span>';
        return '<span class="j-lit">' + lit + '</span>';
      });
  }

  function renderArquitectura(d) {
    var a = d.arquitectura || {};
    html($('#capas'), (a.capas || []).map(function (c) {
      return '<li><strong>' + esc(c.nombre) + '</strong><span>' + esc(c.descripcion) + '</span></li>';
    }).join(''));
    html($('#modelo'), (a.modelo || []).map(function (m) { return '<li><code>' + esc(m) + '</code></li>'; }).join(''));
    $('#carpetas').textContent = a.carpetas || '';
    html($('#ejemplo-lectura'), a.ejemploLectura ? highlightJSON(a.ejemploLectura) : '');
    html($('#stack'), (a.stack || []).map(function (s) {
      return '<div class="card"><h4>Stack ' + esc(s.fase) + '</h4><ul class="chips">' +
        (s.items || []).map(function (i) { return '<li>' + esc(i) + '</li>'; }).join('') + '</ul></div>';
    }).join(''));
  }

  function renderRoadmap(d) {
    var actual = d.estado.sprintActual;
    html($('#sprints'), d.sprints.map(function (s) {
      var st = estadoSprint(s, actual);
      var tot = puntosTotales(s), done = puntosHechos(s);
      var pct = tot ? Math.round(done / tot * 100) : 0;
      var tareas = (s.tareas || []).map(function (t) {
        return '<li class="task task--' + esc(t.estado) + '"><span class="task__id">' + esc(t.id) + '</span><span class="task__t">' +
          esc(t.titulo) + '</span><span class="task__p">' + esc(t.puntos) + ' pts</span><span class="sr-only">, ' + esc(ESTADOS[t.estado] || t.estado) + '</span></li>';
      }).join('');
      return '<li class="sprint sprint--' + st + (s.numero === actual ? ' is-current' : '') + '"' + (s.numero === actual ? ' aria-current="step"' : '') + '>' +
        '<span class="sprint__marker" aria-hidden="true"></span>' +
        '<div class="sprint__body card">' +
          '<div class="sprint__head"><span class="sprint__n">Sprint ' + esc(s.numero) + '</span>' +
            '<span class="status status--' + st + '">' + ESTADOS[st] + '</span>' +
            (s.provisional ? '<span class="status status--prov">Provisional</span>' : '') +
            '<span class="sprint__dates">' + fmt(s.fechaInicio) + ' – ' + fmt(s.fechaFin, true) + '</span></div>' +
          '<h4>' + esc(s.entregable || s.nombre) + '</h4>' +
          '<div class="progress"><div class="progress__bar" role="progressbar" aria-label="Progreso del sprint ' + esc(s.numero) + '" aria-valuemin="0" aria-valuemax="' + tot + '" aria-valuenow="' + done + '">' +
            '<span style="width:' + pct + '%"></span></div><span class="progress__txt">' + done + ' / ' + tot + ' pts · ' + pct + '%</span></div>' +
          (tareas ? '<details' + (s.numero === actual ? ' open' : '') + '><summary>Tareas (' + s.tareas.length + ')</summary><ul class="tasks">' + tareas + '</ul></details>' : '') +
        '</div></li>';
    }).join(''));

    html($('#fases-s2'), (d.fasesS2 || []).map(function (f, i) {
      return '<li><span>' + (i + 1) + '</span>' + esc(f) + '</li>';
    }).join(''));
    var c = $('#cierre-s2');
    if (d.cierreS2) c.innerHTML = '<strong>Cierre de S2:</strong> ' + esc(d.cierreS2); else c.hidden = true;
  }

  function renderCalendario(d) {
    var hoy = today();
    var eventos = d.calendario.slice().sort(function (a, b) { return parseDate(a.fecha) - parseDate(b.fecha); });
    var esEntrega = function (e) { return /entrega|defensa/i.test(e.tipo); };
    var siguiente = eventos.filter(function (e) { return esEntrega(e) && parseDate(e.fecha) >= hoy; })[0];

    var cd = $('#countdown');
    if (siguiente) {
      var dias = daysBetween(hoy, parseDate(siguiente.fecha));
      cd.innerHTML = '<p class="countdown__label">Siguiente entrega</p>' +
        '<p class="countdown__num">' + (dias === 0 ? '¡Hoy!' : dias + '<small>' + (dias === 1 ? ' día' : ' días') + '</small>') + '</p>' +
        '<p class="countdown__what">' + esc(siguiente.titulo) + '</p>' +
        '<p class="countdown__date"><time datetime="' + esc(siguiente.fecha) + '">' + fmt(siguiente.fecha, true) + '</time></p>';
    } else {
      cd.innerHTML = '<p class="countdown__label">Siguiente entrega</p><p class="countdown__what">No quedan entregas en el calendario.</p>';
    }

    html($('#cal-list'), eventos.map(function (e) {
      var f = parseDate(e.fecha);
      var cls = +f === +hoy ? 'is-today' : (f < hoy ? 'is-past' : (e === siguiente ? 'is-next' : ''));
      return '<li class="cal ' + cls + '"><time datetime="' + esc(e.fecha) + '"><b>' + f.getDate() + '</b>' + MESES[f.getMonth()] + ' ' + String(f.getFullYear()).slice(2) + '</time>' +
        '<span class="cal__t">' + esc(e.titulo) + '</span><span class="tag tag--' + esc(String(e.tipo).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')) + '">' + esc(e.tipo) + '</span>' +
        (e === siguiente ? '<span class="sr-only"> (siguiente entrega)</span>' : '') + '</li>';
    }).join(''));

    html($('#contenido-entrega'), (d.contenidoEntregaSprint || []).map(function (c) { return '<li>' + esc(c) + '</li>'; }).join(''));
    html($('#festivos'), (d.festivos || []).map(function (f) {
      var txt = f.desde === f.hasta || !f.hasta ? fmt(f.desde, true) : fmt(f.desde, true) + ' – ' + fmt(f.hasta, true);
      return '<li>' + esc(txt) + '</li>';
    }).join(''));
  }

  function renderEquipo(d) {
    var actual = d.estado.sprintActual;
    var rot = (d.rotacionScrum || []).filter(function (r) { return r.sprint === actual; })[0] || {};
    var e = d.empresa;
    var emp = $('#empresa');
    if (e) emp.innerHTML = '<strong>' + esc(e.nombre) + '</strong>' + (e.tipo ? ' (' + esc(e.tipo) + ')' : '') + '. ' + esc(e.descripcion); else emp.hidden = true;

    html($('#equipo-list'), (d.equipo || []).map(function (p) {
      var ini = p.nombre.split(/\s+/).map(function (w) { return w[0]; }).slice(0, 2).join('');
      var rol = p.nombre === rot.productOwner ? 'Product Owner' : (p.nombre === rot.scrumMaster ? 'Scrum Master' : 'Desarrollo');
      return '<li class="card member"><span class="member__av" aria-hidden="true">' + esc(ini) + '</span><div><h3>' + esc(p.nombre) + '</h3>' +
        '<p class="member__role">' + rol + ' · Sprint ' + esc(actual) + '</p>' +
        (p.github ? '<a href="https://github.com/' + esc(p.github) + '" target="_blank" rel="noopener">@' + esc(p.github) + '<span class="sr-only"> en GitHub (pestaña nueva)</span></a>' : '') +
        '</div></li>';
    }).join(''));

    html($('#rotacion'), (d.rotacionScrum || []).map(function (r) {
      var cur = r.sprint === actual;
      return '<tr' + (cur ? ' class="is-current" aria-current="true"' : '') + '><th scope="row">Sprint ' + esc(r.sprint) +
        (cur ? ' <span class="status status--en-curso">Actual</span>' : '') + '</th><td>' + esc(r.productOwner) + '</td><td>' + esc(r.scrumMaster) + '</td></tr>';
    }).join(''));
  }

  var galeria = [];
  function renderGaleria(d) {
    galeria = d.galeria || [];
    var grupos = [];
    galeria.forEach(function (g, i) {
      var grupo = grupos.filter(function (x) { return x.tipo === g.tipo; })[0];
      if (!grupo) { grupo = { tipo: g.tipo, items: [] }; grupos.push(grupo); }
      grupo.items.push({ g: g, i: i });
    });
    html($('#galeria'), grupos.map(function (gr) {
      return '<h3 class="sub-h">' + esc(gr.tipo) + 's</h3><ul class="gallery">' + gr.items.map(function (x) {
        return '<li><button type="button" class="shot" data-i="' + x.i + '" aria-label="Ampliar: ' + esc(x.g.titulo) + '">' +
          '<img src="' + esc(x.g.thumb || x.g.src) + '" alt="' + esc(x.g.alt || x.g.titulo) + '" loading="lazy" decoding="async" width="720" height="450">' +
          '<span>' + esc(x.g.titulo) + '</span></button></li>';
      }).join('') + '</ul>';
    }).join(''));
  }

  function renderDecisiones(d) {
    html($('#decisiones-list'), (d.decisiones || []).map(function (x) {
      var st = String(x.estado || '').toLowerCase();
      return '<li class="decision decision--' + esc(st) + '"><time datetime="' + esc(x.fecha) + '">' + fmt(x.fecha, true) + '</time>' +
        '<div><h3>' + esc(x.decision) + ' <span class="status status--' + esc(st) + '">' + esc(x.estado) + '</span></h3>' +
        '<p>' + esc(x.motivo) + '</p></div></li>';
    }).join(''));
    html($('#pendientes'), (d.pendientes || []).map(function (p) { return '<li>' + esc(p) + '</li>'; }).join(''));
  }

  function renderODS(d) {
    html($('#ods-list'), (d.ods || []).map(function (o) {
      return '<li class="card ods__item"><span class="ods__n">ODS<b>' + esc(o.numero) + '</b></span><h3>' + esc(o.nombre) + '</h3><p>' + esc(o.texto) + '</p></li>';
    }).join(''));
  }

  function renderEnlaces(d) {
    html($('#enlaces-list'), Object.keys(ENLACES).filter(function (k) {
      // La carpeta compartida solo aparece si existe
      return k !== 'carpetaCompartida' || d.enlaces[k];
    }).map(function (k) {
      var url = d.enlaces[k];
      var host = '';
      try { host = url ? new URL(url).host.replace(/^www\./, '') : ''; } catch (e) {}
      var inner = '<h3>' + esc(ENLACES[k]) + '</h3>' + (host ? '<p class="link-card__host">' + esc(host) + '</p>' : '');
      if (!url) return '<div class="card link-card is-disabled" aria-disabled="true">' + inner + '<span class="link-card__cta">Próximamente</span></div>';
      return '<a class="card link-card" href="' + esc(url) + '" target="_blank" rel="noopener">' + inner +
        '<span class="link-card__cta">Abrir <svg class="ext" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17L17 7M9 7h8v8"/></svg></span><span class="sr-only"> (pestaña nueva)</span></a>';
    }).join(''));
  }

  function renderFooter(d) {
    var a = d.asignatura || {};
    html($('#footer-asignatura'), [a.nombre, a.grado, a.universidad, a.curso ? 'Curso ' + a.curso : '', a.docente ? 'Docente: ' + a.docente : '']
      .filter(Boolean).map(esc).join('<br>'));
    html($('#footer-update'), 'Última actualización: <time datetime="' + esc(d.meta.ultimaActualizacion) + '">' + fmt(d.meta.ultimaActualizacion, true) + '</time>' +
      (d.meta.version ? ' · v' + esc(d.meta.version) : ''));
  }

  /* ---------- interacción ---------- */

  function initTheme() {
    var btn = $('#theme-toggle');
    var mq = window.matchMedia('(prefers-color-scheme: dark)');
    function isDark() {
      var t = document.documentElement.dataset.theme;
      return t ? t === 'dark' : mq.matches;
    }
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

  function initNav() {
    var btn = $('#nav-toggle'), nav = $('#nav');
    function close() { nav.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-label', 'Abrir menú'); }
    btn.addEventListener('click', function () {
      var open = !nav.classList.contains('is-open');
      nav.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', String(open));
      btn.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
    });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });

    // Resalta la sección visible en la navegación
    if (!('IntersectionObserver' in window)) return;
    var links = {};
    $$('#nav-list a').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && links[en.target.id]) {
          $$('#nav-list a').forEach(function (a) { a.removeAttribute('aria-current'); });
          links[en.target.id].setAttribute('aria-current', 'true');
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    $$('section[data-nav]').forEach(function (s) { io.observe(s); });
  }

  function initLightbox() {
    var dlg = $('#lightbox'), img = $('#lb-img'), title = $('#lb-title'), idx = 0;
    if (!dlg.showModal) return; // navegadores muy antiguos: la galería sigue visible sin ampliar
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
    d.sprints.forEach(function (s) {
      (s.tareas || []).forEach(function (t) { if (!ESTADOS[t.estado]) malos.push(t.id + ' ("' + t.estado + '")'); });
    });
    if (malos.length) console.warn('[OMERO] Estados de tarea no válidos (usa pendiente | en-curso | hecho): ' + malos.join(', '));
    return null;
  }

  function render(d) {
    if (d.proyecto.nombre) document.title = d.proyecto.nombre;
    renderBindings(d);
    hideEmptySections(d);
    renderLinks(d);
    renderHero(d);
    renderProblema(d);
    renderSistema(d);
    renderRoles(d);
    renderZonas(d);
    renderArquitectura(d);
    renderRoadmap(d);
    renderCalendario(d);
    renderEquipo(d);
    renderGaleria(d);
    renderDecisiones(d);
    renderODS(d);
    renderEnlaces(d);
    renderFooter(d);
    renderNav();
    initNav();
    initLightbox();
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
