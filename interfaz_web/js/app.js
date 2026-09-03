"use strict";
/**
 * HRI de OE3 (RF-17 a RF-20). Habla solo con /coordinacion (RF-19):
 *
 *   /coordinacion/puntos_interes   ListaPuntosInteres, latched   -> catalogo
 *   /coordinacion/estado_mision    EstadoMision, 1 Hz            -> panel
 *   /coordinacion/guiar_usuario    accion GuiarUsuario           -> lanzar/cancelar
 *
 * "mensaje_usuario" se muestra literal (RF-18): lo redacta el coordinador,
 * este archivo no le agrega ni le quita una palabra. La etiqueta grande del
 * panel SI se calcula aqui, a partir de "etapa" y de comparar
 * destino_actual.id con origen_id -nunca del texto-, siguiendo la misma
 * regla que fija Documentos/CONTRATO_INTERFACES.md seccion 5 para RECIBIDA.
 */

const ETAPA = { INACTIVA: 0, TRAMO_1: 1, TRANSFERENCIA: 2, TRAMO_2: 3, COMPLETADA: 4, FALLIDA: 5, RECIBIDA: 6 };
const NOMBRE_ETAPA = { 0: "INACTIVA", 1: "TRAMO_1", 2: "TRANSFERENCIA", 3: "TRAMO_2", 4: "COMPLETADA", 5: "FALLIDA", 6: "RECIBIDA" };

const $ = (id) => document.getElementById(id);
const escapar = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const sinAcentos = (t) => t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

// --------------------------------------------------------------- servidor --
// Por omision, el mismo host desde el que se cargo la pagina: el laptop que
// sirve estos archivos es tambien donde corren rosbridge_server y el
// coordinador. ?ws=host:puerto lo sustituye cuando no coincidan.
function urlPuente() {
  const qs = new URLSearchParams(location.search).get("ws");
  if (qs) return (qs.includes("://") ? qs : "ws://" + qs);
  return "ws://" + location.hostname + ":9090";
}

const estado = {
  puntos: [],
  origenSel: "",
  destinoSel: null,
  filtro: "",
  metaId: null,        // id de la meta en curso, o null
  ultimoEstadoMision: null,
};

const puente = new Puente(urlPuente());

puente.onEstadoConexion = (conectado) => {
  $("led").classList.toggle("ok", conectado);
  $("led").classList.toggle("mal", !conectado);
  $("txt-conexion").textContent = conectado ? "conectado" : "sin conexion, reintentando...";
  if (!conectado) pintarPanelSinDatos("Buscando el coordinador...");
};

puente.suscribir(
  "/coordinacion/puntos_interes", "coordinacion_msgs/msg/ListaPuntosInteres",
  (msg) => { estado.puntos = msg.puntos || []; pintarOrigen(); pintarDestinos(); },
  { history: "keep_last", depth: 1, reliability: "reliable", durability: "transient_local" },
);

puente.suscribir(
  "/coordinacion/estado_mision", "coordinacion_msgs/msg/EstadoMision",
  (msg) => { estado.ultimoEstadoMision = msg; pintarPanel(msg); },
);

// ------------------------------------------------------------- catalogo ---
function pintarOrigen() {
  const sel = $("origen"), previo = sel.value;
  if (!estado.puntos.length) {
    sel.innerHTML = `<option value="">Esperando el catalogo del coordinador...</option>`;
    return;
  }
  sel.innerHTML = estado.puntos
    .map((p) => `<option value="${p.id}">${escapar(p.nombre)}${p.es_transferencia ? " (escaleras)" : ""} · piso ${p.nivel}</option>`)
    .join("");
  sel.value = estado.puntos.some((p) => p.id === previo) ? previo : estado.puntos[0].id;
  estado.origenSel = sel.value;
}

function pintarDestinos() {
  const cont = $("lista-destinos");
  const aguja = sinAcentos(estado.filtro.trim());
  const candidatos = estado.puntos.filter((p) => p.id !== estado.origenSel);
  const hallados = aguja
    ? candidatos.filter((p) => sinAcentos(`${p.nombre} ${p.id}`).includes(aguja))
    : candidatos;

  if (!estado.puntos.length) {
    cont.innerHTML = `<p class="vacio">Esperando el catalogo del coordinador...</p>`;
  } else if (!hallados.length) {
    cont.innerHTML = `<p class="vacio">Ningun destino contiene "${escapar(estado.filtro)}".</p>`;
  } else {
    const origen = estado.puntos.find((p) => p.id === estado.origenSel);
    cont.innerHTML = hallados.map((p) => `
      <button class="opcion" type="button" role="option" data-id="${p.id}"
              aria-selected="${p.id === estado.destinoSel}">
        <span class="nombre">${escapar(p.nombre)}</span>
        <span class="etiquetas">
          <span class="etq">piso ${p.nivel}</span>
          ${origen && p.nivel !== origen.nivel ? '<span class="etq relevo">con relevo</span>' : ""}
        </span>
      </button>`).join("");
  }
  refrescarBotonIr();
}

function refrescarBotonIr() {
  const listo = !!estado.destinoSel && !!estado.origenSel && estado.metaId === null;
  $("btn-ir").disabled = !listo;
  $("btn-ir").textContent = estado.metaId !== null ? "Guiado en curso..." : "Iniciar guiado";
  $("btn-cancelar").disabled = estado.metaId === null;
}

// -------------------------------------------------------------- eventos ---
$("origen").addEventListener("change", (ev) => {
  estado.origenSel = ev.target.value;
  if (estado.destinoSel === estado.origenSel) {
    estado.destinoSel = null;
    $("destino-elegido").textContent = "";
  }
  pintarDestinos();
});

$("buscador").addEventListener("input", (ev) => { estado.filtro = ev.target.value; pintarDestinos(); });

// En el teclado de un telefono, el primer toque fuera del campo de busqueda a
// veces solo cierra el teclado y no llega a disparar el "click" del boton que
// hay debajo (el bug clasico de Safari/iOS en listas largas). Cerrando el
// teclado en cuanto el dedo toca la lista, el toque que elige el destino ya
// no tiene que competir con eso.
$("lista-destinos").addEventListener("touchstart", () => $("buscador").blur(), { passive: true });

$("lista-destinos").addEventListener("click", (ev) => {
  const b = ev.target.closest(".opcion");
  if (!b) return;
  estado.destinoSel = b.dataset.id;
  for (const el of $("lista-destinos").children) {
    if (el.setAttribute) el.setAttribute("aria-selected", el === b ? "true" : "false");
  }
  // Confirmacion visible del toque, independiente de si el boton de abajo
  // queda o no a la vista: sin esto, en una lista larga no hay ninguna senal
  // inmediata de que la seleccion se registro.
  $("destino-elegido").textContent = "Destino elegido: " + b.querySelector(".nombre").textContent;
  refrescarBotonIr();
});

$("btn-ir").addEventListener("click", () => {
  $("nota").textContent = "";
  estado.metaId = puente.enviarMeta(
    "/coordinacion/guiar_usuario", "coordinacion_msgs/action/GuiarUsuario",
    { origen_id: estado.origenSel, destino_id: estado.destinoSel },
    { onFeedback: (valores) => pintarPanel(valores.estado), onResult: alTerminar },
  );
  refrescarBotonIr();
});

$("btn-cancelar").addEventListener("click", () => {
  if (estado.metaId === null) return;
  $("nota").textContent = "Enviando la cancelacion...";
  puente.cancelarMeta("/coordinacion/guiar_usuario", estado.metaId);
});

function alTerminar(valores, exitoLlamada) {
  estado.metaId = null;
  refrescarBotonIr();
  if (!exitoLlamada) {
    $("nota").textContent = "El coordinador no aceptó la solicitud. Intenta de nuevo.";
    return;
  }
  $("nota").textContent = valores.exito
    ? `Misión completada en ${valores.tiempo_total_s.toFixed(1)} s, con ${valores.num_relevos} relevo(s).`
    : "Misión no completada: " + (valores.motivo_fallo || "sin motivo reportado.");
}

// ---------------------------------------------------------------- panel ---
// Deriva la etiqueta grande de "etapa" (nunca del texto). "de_esta_sesion" no
// existe como tal: como el navegador solo escucha mientras esta abierto, todo
// EstadoMision que llega mientras hay una pagina cargada es, por definicion,
// vigente para esa pagina.
function claveYTitulo(e) {
  switch (e.etapa) {
    case ETAPA.COMPLETADA: return ["llegada", "Hemos llegado"];
    case ETAPA.FALLIDA: return ["bloqueado", "Camino bloqueado"];
    case ETAPA.RECIBIDA: return ["preparando", "Preparando"];
    case ETAPA.TRANSFERENCIA: return ["transferencia", "Cambia de piso"];
    case ETAPA.TRAMO_1:
    case ETAPA.TRAMO_2:
      return e.destino_actual.id && e.destino_actual.id === e.origen_id
        ? ["espera", "Espera al robot"] : ["sigueme", "Sígueme"];
    default: return ["inactiva", "Sin misión activa"];
  }
}

const ORDEN_ETAPAS = [[6, "Preparando"], [1, "Tramo 1"], [2, "Relevo"], [3, "Tramo 2"], [4, "Fin"]];

function pintarPanel(e) {
  const [clave, titulo] = claveYTitulo(e);
  const panel = $("panel");
  panel.className = "panel " + clave;
  $("panel-etiqueta").textContent = NOMBRE_ETAPA[e.etapa] || ("desconocida (" + e.etapa + ")");
  $("panel-titulo").textContent = titulo;
  $("panel-frase").textContent = e.mensaje_usuario || "—";

  const filas = [];
  if (e.robot_activo) filas.push(["Robot", e.robot_activo]);
  if (e.destino_actual && e.destino_actual.nombre) filas.push(["Va hacia", e.destino_actual.nombre]);
  if (e.destino_id) filas.push(["Destino final", nombreDe(e.destino_id)]);
  if (e.distancia_restante !== null && e.distancia_restante !== undefined) {
    filas.push(["Distancia", e.distancia_restante.toFixed(2) + " m"]);
  }
  $("panel-datos").innerHTML = filas
    .map(([k, v]) => `<span class="chip">${k}: <b>${escapar(String(v))}</b></span>`).join("");

  $("panel-etapas").innerHTML = ORDEN_ETAPAS.map(([n, txt]) => {
    let clase = "et";
    if (e.etapa === ETAPA.FALLIDA) clase += n === 6 ? " mal" : "";
    else if (n === e.etapa) clase += " on";
    return `<span class="${clase}">${txt}</span>`;
  }).join("");
}

function pintarPanelSinDatos(mensaje) {
  const panel = $("panel");
  panel.className = "panel inactiva";
  $("panel-etiqueta").textContent = "estado";
  $("panel-titulo").textContent = mensaje;
  $("panel-frase").textContent = "—";
  $("panel-datos").innerHTML = "";
  $("panel-etapas").innerHTML = "";
}

function nombreDe(id) {
  const p = estado.puntos.find((p) => p.id === id);
  return p ? p.nombre : id;
}

pintarPanelSinDatos("Conectando con el coordinador...");
pintarOrigen();
pintarDestinos();
