/* Gráficas del sitio, en SVG y sin bibliotecas.
 *
 * Cada gráfica es un <div class="grafica" data-grafica='{...}'> con sus datos en
 * JSON. Los colores salen de variables CSS (sitio.css), así que cambian solos con
 * el modo claro u oscuro. Cada gráfica trae su tabla de datos debajo, plegada.
 */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const num = (v, d = 1) => Number(v).toLocaleString("es-CO", { minimumFractionDigits: d, maximumFractionDigits: d });

  function el(nombre, attrs = {}, padre) {
    const n = document.createElementNS(NS, nombre);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (padre) padre.appendChild(n);
    return n;
  }
  function texto(padre, x, y, cadena, attrs = {}) {
    const t = el("text", { x, y, ...attrs }, padre);
    t.textContent = cadena;
    return t;
  }

  let tip;
  function mostrarTip(ev, html) {
    if (!tip) { tip = document.createElement("div"); tip.className = "g-tip"; document.body.appendChild(tip); }
    tip.innerHTML = html;
    tip.style.left = Math.min(ev.clientX + 14, window.innerWidth - 270) + "px";
    tip.style.top = ev.clientY + 14 + "px";
    tip.style.opacity = 1;
  }
  function ocultarTip() { if (tip) tip.style.opacity = 0; }
  function interactivo(nodo, html) {
    nodo.classList.add("marca");
    nodo.addEventListener("mousemove", (ev) => mostrarTip(ev, html));
    nodo.addEventListener("mouseleave", ocultarTip);
    nodo.addEventListener("touchstart", (ev) => mostrarTip(ev.touches[0], html), { passive: true });
  }

  // ------------------------------------------------ barras horizontales ---
  function barrasH(svgPadre, d, ancho) {
    const apilado = ancho < 520, filas = d.datos, alto = apilado ? 46 : 30;
    const izq = apilado ? 8 : Math.min(d.izquierda || 230, Math.round(ancho * .45)), der = 70;
    const h = filas.length * alto + 34;
    const svg = el("svg", { viewBox: `0 0 ${ancho} ${h}`, role: "img", "aria-label": d.titulo }, svgPadre);
    const x = (v) => izq + (v - d.min) / (d.max - d.min) * (ancho - izq - der);
    if (d.banda) {
      el("rect", { class: "banda", x: x(d.banda[0]), y: 0, width: x(d.banda[1]) - x(d.banda[0]), height: h - 26 }, svg);
      texto(svg, (x(d.banda[0]) + x(d.banda[1])) / 2, h - 30, d.bandaTexto || "", { "text-anchor": "middle", class: "fuerte" });
    }
    for (const t of d.marcas || []) {
      el("line", { class: "rejilla", x1: x(t), x2: x(t), y1: 0, y2: h - 26 }, svg);
      texto(svg, x(t), h - 10, `${num(t, 0)}${d.unidad || ""}`, { "text-anchor": "middle" });
    }
    filas.forEach((f, i) => {
      const y = i * alto + (apilado ? 18 : 6);
      if (apilado) texto(svg, izq, y - 4, f.etiqueta, { class: "fuerte" });
      else texto(svg, izq - 10, y + 15, f.etiqueta, { "text-anchor": "end", class: "fuerte" });
      const ancho0 = Math.max(2, x(f.valor) - x(d.min));
      const barra = el("rect", { class: f.serie === 2 ? "s2" : "s1", x: x(d.min), y: y + 3, width: ancho0, height: 18, rx: 4 }, svg);
      texto(svg, x(f.valor) + 6, y + 16, f.texto || `${num(f.valor, d.decimales ?? 1)}${d.unidad || ""}`);
      interactivo(barra, `<b>${f.etiqueta}</b><br>${f.texto || num(f.valor, d.decimales ?? 1) + (d.unidad || "")}${f.nota ? "<br>" + f.nota : ""}`);
    });
  }

  // --------------------------------------------- punto con intervalo ------
  function intervalos(svgPadre, d, ancho) {
    const apilado = ancho < 520, filas = d.datos, alto = apilado ? 56 : 40;
    const izq = apilado ? 16 : Math.min(d.izquierda || 210, Math.round(ancho * .42)), der = 28;
    const h = filas.length * alto + 34;
    const svg = el("svg", { viewBox: `0 0 ${ancho} ${h}`, role: "img", "aria-label": d.titulo }, svgPadre);
    const x = (v) => izq + (v - d.min) / (d.max - d.min) * (ancho - izq - der);
    for (const t of d.marcas || []) {
      el("line", { class: "rejilla", x1: x(t), x2: x(t), y1: 0, y2: h - 26 }, svg);
      texto(svg, x(t), h - 10, `${num(t, 0)} %`, { "text-anchor": "middle" });
    }
    filas.forEach((f, i) => {
      const y = i * alto + (apilado ? 34 : 20), clase = f.serie === 2 ? "2" : "1";
      if (apilado) texto(svg, 8, y - 20, f.etiqueta, { class: "fuerte" });
      else texto(svg, izq - 12, y + 4, f.etiqueta, { "text-anchor": "end", class: "fuerte" });
      el("line", { class: "l" + clase, x1: x(f.bajo), x2: x(f.alto), y1: y, y2: y }, svg);
      for (const v of [f.bajo, f.alto]) el("line", { class: "l" + clase, x1: x(v), x2: x(v), y1: y - 6, y2: y + 6 }, svg);
      const p = el("circle", { class: "s" + clase, cx: x(f.valor), cy: y, r: 6, stroke: "var(--md-default-bg-color)", "stroke-width": 2 }, svg);
      texto(svg, x(f.valor), y - 11, f.texto, { "text-anchor": "middle" });
      interactivo(p, `<b>${f.etiqueta}</b><br>${f.texto}<br>intervalo del 95 %: ${num(f.bajo)} – ${num(f.alto)} %`);
    });
  }

  // ------------------------------------------------ barras verticales -----
  function barrasV(svgPadre, d, ancho) {
    const n = d.datos.length, alto = 230, abajo = 40, arriba = 18, izq = 44;
    const svg = el("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": d.titulo }, svgPadre);
    const y = (v) => alto - abajo - (v - d.min) / (d.max - d.min) * (alto - abajo - arriba);
    const paso = (ancho - izq - 10) / n, b = Math.min(56, paso * .62);
    for (const t of d.marcas || []) {
      el("line", { class: "rejilla", x1: izq, x2: ancho - 10, y1: y(t), y2: y(t) }, svg);
      texto(svg, izq - 8, y(t) + 4, num(t, d.decimalesEje ?? 0), { "text-anchor": "end" });
    }
    if (d.umbral !== undefined) {
      el("line", { class: "umbral", x1: izq, x2: ancho - 10, y1: y(d.umbral), y2: y(d.umbral) }, svg);
      texto(svg, ancho - 12, y(d.umbral) - 6, d.umbralTexto, { "text-anchor": "end", class: "fuerte" });
    }
    d.datos.forEach((f, i) => {
      const cx = izq + paso * i + paso / 2;
      let marca;
      if (d.estilo === "puntos") {
        el("line", { class: "rejilla", x1: cx, x2: cx, y1: y(d.min), y2: y(f.valor) }, svg);
        marca = el("circle", { class: "s1", cx, cy: y(f.valor), r: 6, stroke: "var(--md-default-bg-color)", "stroke-width": 2 }, svg);
      } else {
        marca = el("rect", { class: "s1", x: cx - b / 2, y: y(f.valor), width: b, height: Math.max(2, y(d.min) - y(f.valor)), rx: 4 }, svg);
      }
      if (d.rotulos !== false) texto(svg, cx, y(f.valor) - 9, f.texto || num(f.valor, d.decimales ?? 1), { "text-anchor": "middle" });
      texto(svg, cx, alto - abajo + 16, f.etiqueta, { "text-anchor": "middle", class: "fuerte" });
      interactivo(marca, `<b>${f.nombre || f.etiqueta}</b><br>${f.texto || num(f.valor, d.decimales ?? 1)} ${d.unidad || ""}`);
    });
    el("line", { class: "eje", x1: izq, x2: ancho - 10, y1: y(d.min), y2: y(d.min) }, svg);
    if (d.ejeX) texto(svg, (ancho + izq) / 2, alto - 4, d.ejeX, { "text-anchor": "middle" });
  }

  function tabla(cont, d) {
    const det = document.createElement("details");
    det.className = "note";
    const cols = d.columnas || ["Elemento", "Valor"];
    const filas = d.datos.map((f) => (d.filaTabla ? d.filaTabla(f) : [f.nombre || f.etiqueta, f.texto || num(f.valor, d.decimales ?? 1) + (d.unidad || "")]));
    det.innerHTML = `<summary>Ver los datos en una tabla</summary><table><thead><tr>${cols.map((c) => `<th>${c}</th>`).join("")}</tr></thead><tbody>${
      filas.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
    cont.appendChild(det);
  }

  function dibujar() {
    document.querySelectorAll(".grafica[data-grafica]").forEach((cont) => {
      if (cont.dataset.lista) return;
      cont.dataset.lista = "1";
      const d = JSON.parse(cont.dataset.grafica);
      cont.insertAdjacentHTML("afterbegin", `<div class="g-titulo">${d.titulo}</div>${d.sub ? `<div class="g-sub">${d.sub}</div>` : ""}`);
      const lienzo = document.createElement("div");
      cont.appendChild(lienzo);
      const fn = d.tipo === "barras-h" ? barrasH : d.tipo === "intervalos" ? intervalos : barrasV;
      if (d.tipo === "intervalos") {
        d.columnas = ["Grupo", "Éxitos", "Intervalo del 95 %"];
        d.filaTabla = (f) => [f.etiqueta, f.texto, `${num(f.bajo)} – ${num(f.alto)} %`];
      }
      // Se dibuja al ancho real en píxeles: con un viewBox fijo el texto se
      // encogía a 6 px en un teléfono. Se redibuja si cambia el ancho.
      let ultimo = 0;
      const pintar = () => {
        const w = Math.max(280, Math.round(lienzo.clientWidth));
        if (w === ultimo) return;
        ultimo = w;
        lienzo.innerHTML = "";
        fn(lienzo, d, w);
      };
      pintar();
      if (window.ResizeObserver) new ResizeObserver(pintar).observe(lienzo);
      if (d.leyenda) {
        cont.insertAdjacentHTML("beforeend", `<div class="leyenda">${d.leyenda.map(([c, t]) => `<span><i style="background:var(--serie-${c})"></i>${t}</span>`).join("")}</div>`);
      }
      tabla(cont, d);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", dibujar);
  else dibujar();
  if (window.document$) window.document$.subscribe(dibujar);
})();
