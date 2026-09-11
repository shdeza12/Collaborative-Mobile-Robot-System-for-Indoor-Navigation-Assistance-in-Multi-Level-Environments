"use strict";
/**
 * Banco de pruebas del paso 9 de PLAN_RF28_CONFIRMACION.md sin navegador.
 *
 * Carga los DOS archivos reales de interfaz_web/js sobre un DOM minimo y el
 * WebSocket nativo de Node, contra el rosbridge y el coordinador reales. Lo
 * unico que no cubre es el dibujado de pixeles, que ya quedo verificado con
 * una captura de pantalla.
 *
 * No hace falta servidor HTTP ni navegador: esta maquina no tiene ninguno
 * automatizable (solo Firefox, sin geckodriver, selenium ni playwright), y
 * Node >=22 trae WebSocket nativo, asi que el JS de la pagina se ejecuta tal
 * cual, sin copiarlo ni adaptarlo.
 *
 * Montaje, tres procesos en segundo plano antes de correrlo:
 *
 *   source ~/deepracer_sim_ws/install/setup.bash
 *   ros2 run coordinacion coordinador --ros-args -p prefijo_mision:=PRUEBARF28 &
 *   ros2 launch rosbridge_server rosbridge_websocket_launch.xml &
 *   ros2 topic echo /coordinacion/confirmacion_piso > /tmp/rf28_eco.txt &
 *   node interfaz_web/prueba_confirmacion_piso.js
 *
 * El 'topic pub' del estado falso de etapa 7 lo lanza y lo mata este archivo.
 * Sale 0 si las 18 comprobaciones pasan.
 */
const fs = require("fs");
const vm = require("vm");
const { spawn } = require("child_process");

const RAIZ = process.env.RAIZ_HRI || __dirname;
const ECO = process.env.ARCHIVO_ECO || "/tmp/rf28_eco.txt";

// ------------------------------------------------------------------- DOM ---
const nodos = new Map();
function nodo(id) {
  if (!nodos.has(id)) {
    const clases = new Set();
    nodos.set(id, {
      id, textContent: "", innerHTML: "", value: "", hidden: false,
      disabled: false, className: "", dataset: {}, children: [],
      manejadores: {},
      classList: {
        toggle(c, on) { if (on === undefined ? clases.has(c) : !on) clases.delete(c); else clases.add(c); },
        contains: (c) => clases.has(c),
        _lista: () => [...clases].sort().join(" "),
      },
      addEventListener(ev, fn) { (this.manejadores[ev] ||= []).push(fn); },
      querySelector: () => null,
      setAttribute() {},
      blur() {},
      closest: () => null,
    });
  }
  return nodos.get(id);
}

const contexto = {
  document: { getElementById: nodo },
  location: { search: "", hostname: "localhost" },
  URLSearchParams, WebSocket, setTimeout, clearTimeout, console, JSON,
};
contexto.window = contexto;
vm.createContext(contexto);
for (const f of ["rosbridge.js", "app.js"]) {
  vm.runInContext(fs.readFileSync(`${RAIZ}/js/${f}`, "utf8"), contexto, { filename: f });
}

// -------------------------------------------------------- comprobaciones ---
let pasan = 0, fallan = 0;
function comprueba(nombre, ok, detalle = "") {
  if (ok) { pasan++; console.log(`  ok   ${nombre}`); }
  else { fallan++; console.log(`  FALLA ${nombre}${detalle ? " -> " + detalle : ""}`); }
}
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
async function hasta(cond, ms = 15000) {
  const fin = Date.now() + ms;
  while (Date.now() < fin) { if (cond()) return true; await esperar(100); }
  return false;
}

// -------------------------------------------------------------- guion -----
(async () => {
  console.log("\n== 1. conexion con rosbridge ==");
  const conectado = await hasta(() => nodo("txt-conexion").textContent === "conectado");
  comprueba("el puente abre el socket y la pagina dice 'conectado'", conectado,
            `textContent='${nodo("txt-conexion").textContent}'`);
  comprueba("el LED queda en 'ok' y no en 'mal'",
            nodo("led").classList.contains("ok") && !nodo("led").classList.contains("mal"),
            nodo("led").classList._lista());
  if (!conectado) { console.log("\nSin rosbridge no hay nada mas que probar."); process.exit(1); }

  console.log("\n== 2. con el coordinador en INACTIVA, el boton no existe ==");
  const inactiva = await hasta(() => nodo("panel-etiqueta").textContent === "INACTIVA");
  comprueba("llega EstadoMision con etapa INACTIVA", inactiva,
            `etiqueta='${nodo("panel-etiqueta").textContent}'`);
  comprueba("acciones-confirmar esta oculto en INACTIVA", nodo("acciones-confirmar").hidden === true);

  console.log("\n== 3. estado falso de etapa 7: el panel dibuja la pregunta ==");
  const pub = spawn("ros2", ["topic", "pub", "-r", "5", "/coordinacion/estado_mision",
    "coordinacion_msgs/msg/EstadoMision",
    "{mision_id: 'FALSA_1', etapa: 7, robot_activo: 'robot2', mensaje_usuario: 'Prueba de etapa 7'}"],
    { stdio: "ignore" });
  const et7 = await hasta(() => nodo("panel-etiqueta").textContent === "ESPERANDO_CONFIRMACION");
  comprueba("la etiqueta dice ESPERANDO_CONFIRMACION y no 'desconocida (7)'", et7,
            `etiqueta='${nodo("panel-etiqueta").textContent}'`);
  comprueba("el titulo dice '¿Ya subió?'", nodo("panel-titulo").textContent === "¿Ya subió?",
            `titulo='${nodo("panel-titulo").textContent}'`);
  comprueba("la clase del panel es 'panel confirmar'", nodo("panel").className === "panel confirmar",
            `className='${nodo("panel").className}'`);
  comprueba("mensaje_usuario se muestra literal",
            nodo("panel-frase").textContent === "Prueba de etapa 7",
            `frase='${nodo("panel-frase").textContent}'`);
  comprueba("el chip del robot activo no queda vacio",
            nodo("panel-datos").innerHTML.includes("Robot: <b>robot2</b>"),
            nodo("panel-datos").innerHTML);
  comprueba("la barra ilumina 'Relevo' y solo 'Relevo'",
            /<span class="et on">Relevo<\/span>/.test(nodo("panel-etapas").innerHTML) &&
            (nodo("panel-etapas").innerHTML.match(/et on/g) || []).length === 1,
            nodo("panel-etapas").innerHTML);
  comprueba("acciones-confirmar queda visible", nodo("acciones-confirmar").hidden === false);

  console.log("\n== 4. el panel se queda estable (no parpadea) ==");
  await esperar(4000);
  comprueba("sigue en etapa 7 tras 4 s con el pub a 5 Hz",
            nodo("panel-etiqueta").textContent === "ESPERANDO_CONFIRMACION" &&
            nodo("acciones-confirmar").hidden === false,
            `etiqueta='${nodo("panel-etiqueta").textContent}' hidden=${nodo("acciones-confirmar").hidden}`);

  console.log("\n== 5. pulsar el boton publica en ROS ==");
  const clics = nodo("btn-confirmar").manejadores.click || [];
  comprueba("btn-confirmar tiene un manejador de click", clics.length === 1, `n=${clics.length}`);
  for (const fn of clics) fn();
  comprueba("la nota avisa que se envio", nodo("nota").textContent === "Confirmacion enviada.",
            `nota='${nodo("nota").textContent}'`);
  await esperar(2000);
  const eco = fs.existsSync(ECO) ? fs.readFileSync(ECO, "utf8") : "";
  comprueba("el 'topic echo' recibio data: FALSA_1", /data:\s*FALSA_1/.test(eco),
            eco.trim().split("\n").slice(-3).join(" | ") || "(archivo vacio)");

  console.log("\n== 6. al dejar de preguntar, el boton desaparece ==");
  pub.kill("SIGINT");
  const oculto = await hasta(() => nodo("acciones-confirmar").hidden === true, 8000);
  comprueba("acciones-confirmar vuelve a ocultarse", oculto,
            `hidden=${nodo("acciones-confirmar").hidden} etiqueta='${nodo("panel-etiqueta").textContent}'`);
  comprueba("el panel vuelve a 'Sin misión activa'",
            nodo("panel-titulo").textContent === "Sin misión activa",
            `titulo='${nodo("panel-titulo").textContent}'`);
  comprueba("la clase del panel vuelve a 'panel inactiva'",
            nodo("panel").className === "panel inactiva", nodo("panel").className);

  console.log(`\n${pasan} comprobaciones pasan, ${fallan} fallan.`);
  process.exit(fallan ? 1 : 0);
})();
