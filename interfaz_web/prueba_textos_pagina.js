"use strict";
/**
 * Textos de la pagina, sin red: node interfaz_web/prueba_textos_pagina.js
 *
 * Carga los dos archivos reales de interfaz_web/js sobre un DOM minimo y un
 * WebSocket falso que nunca conecta, y comprueba dos cosas que el 16-oct
 * fallaron en campo:
 *
 *  - el titulo de la espera de confirmacion dice si el usuario sube o baja;
 *  - dos puntos con el mismo nombre en pisos distintos se distinguen: en el
 *    sorteo se pidio el Ascensor del piso 4 en vez del 3, porque al elegirlo
 *    el campo solo decia "Ascensor".
 *
 * prueba_confirmacion_piso.js, en cambio, necesita rosbridge y el coordinador.
 */
const fs = require("fs");
const vm = require("vm");

const RAIZ = process.env.RAIZ_HRI || __dirname;
const nodos = new Map();
function nodo(id) {
  if (!nodos.has(id)) {
    const clases = new Set();
    nodos.set(id, {
      id, textContent: "", innerHTML: "", value: "", hidden: false, disabled: false,
      className: "", dataset: {}, manejadores: {},
      classList: { toggle(c, on) { (on ? clases.add(c) : clases.delete(c)); }, contains: (c) => clases.has(c) },
      addEventListener(ev, fn) { (this.manejadores[ev] ||= []).push(fn); },
      querySelector: () => null, setAttribute() {}, blur() {}, select() {}, contains: () => false,
      closest: () => null, scrollIntoView() {},
    });
  }
  return nodos.get(id);
}
class WebSocketFalso { constructor() { this.readyState = 0; } send() {} close() {} }
const contexto = {
  document: { getElementById: nodo, addEventListener() {} },
  location: { search: "", hostname: "localhost" },
  URLSearchParams, WebSocket: WebSocketFalso, setTimeout: () => 0, clearTimeout() {}, console, JSON,
};
contexto.window = contexto;
vm.createContext(contexto);
for (const f of ["rosbridge.js", "app.js"]) {
  vm.runInContext(fs.readFileSync(`${RAIZ}/js/${f}`, "utf8"), contexto, { filename: f });
}
const en = (expr) => vm.runInContext(expr, contexto);

let fallos = 0;
function comprueba(nombre, ok, detalle = "") {
  fallos += !ok;
  console.log(`  [${ok ? "OK " : "MAL"}] ${nombre}${detalle ? " -> " + detalle : ""}`);
}

en(`estado.puntos = [
  {id: "piso3_salon_302", nombre: "Salón 302", nivel: 3},
  {id: "piso3_ascensor", nombre: "Ascensor", nivel: 3},
  {id: "piso3_escalera", nombre: "Escaleras", nivel: 3, es_transferencia: true},
  {id: "piso4_salon_401", nombre: "Salón 401", nivel: 4},
  {id: "piso4_ascensor", nombre: "Ascensor", nivel: 4},
  {id: "piso4_escalera", nombre: "Escaleras", nivel: 4, es_transferencia: true},
]`);

console.log("== título de la espera de confirmación ==");
const titulo = (o, n) => en(`tituloConfirmacion({origen_id: ${JSON.stringify(o)}, destino_actual: {nivel: ${n}}})`);
comprueba("subida del 3 al 4", titulo("piso3_salon_302", 4) === "Suba con calma al piso 4", titulo("piso3_salon_302", 4));
comprueba("bajada del 4 al 3", titulo("piso4_salon_401", 3) === "Baje con calma al piso 3", titulo("piso4_salon_401", 3));
comprueba("sin origen conocido, neutro", titulo("", 4) === "Confirme el cambio de piso", titulo("", 4));

console.log("== nombres que se repiten entre pisos ==");
const visible = (id) => en(`nombreVisible(estado.puntos.find((p) => p.id === ${JSON.stringify(id)}))`);
comprueba("el Ascensor del piso 3 lleva su piso", visible("piso3_ascensor") === "Ascensor (piso 3)", visible("piso3_ascensor"));
comprueba("el Ascensor del piso 4 lleva su piso", visible("piso4_ascensor") === "Ascensor (piso 4)", visible("piso4_ascensor"));
comprueba("las Escaleras también", visible("piso4_escalera") === "Escaleras (piso 4)", visible("piso4_escalera"));
comprueba("un nombre único queda igual", visible("piso3_salon_302") === "Salón 302", visible("piso3_salon_302"));
comprueba("el destino final del panel usa el mismo nombre",
          en(`nombreDe("piso4_ascensor")`) === "Ascensor (piso 4)", en(`nombreDe("piso4_ascensor")`));

console.log(`\n${fallos} fallo(s).`);
process.exit(fallos ? 1 : 0);
