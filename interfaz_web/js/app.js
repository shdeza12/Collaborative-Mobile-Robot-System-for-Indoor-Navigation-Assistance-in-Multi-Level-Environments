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

const ETAPA = { INACTIVA: 0, TRAMO_1: 1, TRANSFERENCIA: 2, TRAMO_2: 3, COMPLETADA: 4, FALLIDA: 5, RECIBIDA: 6, ESPERANDO_CONFIRMACION: 7, CANCELANDO: 8 };
const NOMBRE_ETAPA = { 0: "INACTIVA", 1: "TRAMO_1", 2: "TRANSFERENCIA", 3: "TRAMO_2", 4: "COMPLETADA", 5: "FALLIDA", 6: "RECIBIDA", 7: "ESPERANDO_CONFIRMACION", 8: "CANCELANDO" };

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
  (msg) => {
    estado.puntos = msg.puntos || [];
    pintarOrigen();
    campoDestino.refrescarCatalogo();
  },
  { history: "keep_last", depth: 1, reliability: "reliable", durability: "transient_local" },
);

puente.suscribir(
  "/coordinacion/estado_mision", "coordinacion_msgs/msg/EstadoMision",
  (msg) => { estado.ultimoEstadoMision = msg; pintarPanel(msg); },
);

// ------------------------------------------------------------- catalogo ---
// Un solo widget de "campo con busqueda", reutilizado para origen y destino:
// las dos listas se veian distintas -un <select> nativo contra esta lista
// propia- y la propia solo se podia dejar siempre abierta, ocupando espacio
// permanente. Aqui las dos usan el mismo look, y las dos se pliegan: al
// enfocar se despliega mostrando TODO (no lo ya escrito, que filtraria a un
// solo resultado), al escribir filtra, y al elegir o al tocar fuera se
// repliega. El input nunca deja de poder escribirse.
class CampoBuscable {
  constructor({ input, lista, obtenerOpciones, renderizarOpcion, vacioTexto, onSeleccion }) {
    this.input = input;
    this.lista = lista;
    this.obtenerOpciones = obtenerOpciones;
    this.renderizarOpcion = renderizarOpcion;
    this.vacioTexto = vacioTexto;
    this.onSeleccion = onSeleccion;
    this.seleccionId = null;
    this.seleccionNombre = "";

    this.input.addEventListener("focus", () => this._abrir());
    this.input.addEventListener("input", () => this._pintar(this.input.value));
    // Mismo arreglo que ya tenia el listado de destino: en un telefono, el
    // primer toque fuera del campo a veces solo cierra el teclado (bug
    // conocido de iOS Safari) y no llega a marcar la opcion. Cerrando el
    // teclado en cuanto el dedo toca la lista, el toque que elige ya no
    // compite con eso. OJO: esto no oculta la lista, solo el teclado -si
    // ocultara la lista aqui, el click de seleccion nunca llegaria a disparar.
    this.lista.addEventListener("touchstart", () => this.input.blur(), { passive: true });
    this.lista.addEventListener("click", (ev) => {
      const b = ev.target.closest(".opcion");
      if (!b) return;
      this._seleccionar(b.dataset.id, b.querySelector(".nombre").textContent);
    });
    document.addEventListener("click", (ev) => {
      if (this.lista.hidden) return;
      if (!this.input.contains(ev.target) && !this.lista.contains(ev.target)) this._cerrar();
    });
  }

  /** Fija la seleccion sin pasar por el click del usuario (p. ej. el defecto inicial). */
  seleccionar(id, nombre) { this.seleccionId = id; this.seleccionNombre = nombre; this.input.value = nombre; }

  refrescarCatalogo() {
    if (!this.lista.hidden) this._pintar(this.input.value);
    else if (!this.input.value) this.input.value = this.seleccionNombre;
  }

  _abrir() {
    this.lista.hidden = false;
    this._pintar("");   // se abre mostrando TODO, no filtrado por la seleccion previa
    this.input.select();
  }

  _cerrar() {
    this.lista.hidden = true;
    // Sin una seleccion valida, el texto tecleado y no confirmado se descarta:
    // el campo vuelve a mostrar la ultima seleccion real (o queda vacio).
    this.input.value = this.seleccionNombre;
  }

  _seleccionar(id, nombre) {
    this.seleccionId = id;
    this.seleccionNombre = nombre;
    this.input.value = nombre;
    this._cerrar();
    this.onSeleccion(id);
  }

  _pintar(filtro) {
    if (!estado.puntos.length) {
      this.lista.innerHTML = `<p class="vacio">Esperando el catalogo del coordinador...</p>`;
      return;
    }
    const aguja = sinAcentos(filtro.trim());
    const opciones = this.obtenerOpciones();
    const hallados = aguja
      ? opciones.filter((p) => sinAcentos(`${p.nombre} ${p.id}`).includes(aguja))
      : opciones;
    this.lista.innerHTML = !hallados.length
      ? `<p class="vacio">${this.vacioTexto(filtro)}</p>`
      : hallados.map((p) => `
        <button class="opcion" type="button" role="option" data-id="${p.id}"
                aria-selected="${p.id === this.seleccionId}">
          ${this.renderizarOpcion(p)}
        </button>`).join("");
  }
}

const opcionEstandar = (p) => `
  <span class="nombre">${escapar(p.nombre)}${p.es_transferencia ? " (escaleras)" : ""}</span>
  <span class="etiquetas"><span class="etq">piso ${p.nivel}</span></span>`;

const campoOrigen = new CampoBuscable({
  input: $("origen-buscador"), lista: $("lista-origen"),
  obtenerOpciones: () => estado.puntos,
  renderizarOpcion: opcionEstandar,
  vacioTexto: (filtro) => `Ningun punto contiene "${escapar(filtro)}".`,
  onSeleccion: (id) => {
    estado.origenSel = id;
    if (estado.destinoSel === estado.origenSel) campoDestino.seleccionar(null, "");
    campoDestino.refrescarCatalogo();
    refrescarBotonIr();
  },
});

const campoDestino = new CampoBuscable({
  input: $("buscador"), lista: $("lista-destinos"),
  obtenerOpciones: () => estado.puntos.filter((p) => p.id !== estado.origenSel),
  renderizarOpcion: (p) => {
    const origen = estado.puntos.find((o) => o.id === estado.origenSel);
    const conRelevo = origen && p.nivel !== origen.nivel;
    return `
      <span class="nombre">${escapar(p.nombre)}</span>
      <span class="etiquetas">
        <span class="etq">piso ${p.nivel}</span>
        ${conRelevo ? '<span class="etq relevo">con relevo</span>' : ""}
      </span>`;
  },
  vacioTexto: (filtro) => filtro
    ? `Ningun destino contiene "${escapar(filtro)}".`
    : "No hay destinos en otros puntos del catalogo.",
  onSeleccion: (id) => { estado.destinoSel = id; refrescarBotonIr(); },
});

function pintarOrigen() {
  // El defecto -el primer punto del catalogo- solo se fija la primera vez que
  // llega el catalogo; si el usuario ya eligio otro origen, un refresco del
  // catalogo (p. ej. al reconectar) no se lo pisa.
  if (!estado.origenSel && estado.puntos.length) {
    estado.origenSel = estado.puntos[0].id;
    campoOrigen.seleccionar(estado.puntos[0].id, estado.puntos[0].nombre);
  }
  campoOrigen.refrescarCatalogo();
}

function refrescarBotonIr() {
  const listo = !!estado.destinoSel && !!estado.origenSel && estado.metaId === null;
  $("btn-ir").disabled = !listo;
  $("btn-ir").textContent = estado.metaId !== null ? "Guiado en curso..." : "Iniciar guiado";
  $("btn-cancelar").disabled = estado.metaId === null;
}

// -------------------------------------------------------------- eventos ---
$("btn-ir").addEventListener("click", () => {
  $("nota").textContent = "";
  estado.metaId = puente.enviarMeta(
    "/coordinacion/guiar_usuario", "coordinacion_msgs/action/GuiarUsuario",
    { origen_id: estado.origenSel, destino_id: estado.destinoSel },
    { onFeedback: (valores) => { estado.ultimoEstadoMision = valores.estado; pintarPanel(valores.estado); }, onResult: alTerminar },
  );
  refrescarBotonIr();
});

$("btn-cancelar").addEventListener("click", () => {
  if (estado.metaId === null) return;
  $("nota").textContent = "Enviando la cancelacion...";
  puente.cancelarMeta("/coordinacion/guiar_usuario", estado.metaId);
});

$("btn-confirmar").addEventListener("click", () => {
  const e = estado.ultimoEstadoMision;
  if (!e || !e.mision_id) return;
  // El mision_id va en el cuerpo para que el coordinador pueda descartar una
  // pulsacion de una mision anterior. Ver Enganche en espera_confirmacion.py.
  puente.publicar("/coordinacion/confirmacion_piso", "std_msgs/msg/String",
                  { data: e.mision_id });
  $("nota").textContent = "Confirmacion enviada.";
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
    case ETAPA.ESPERANDO_CONFIRMACION: return ["confirmar", "¿Ya subió?"];
    case ETAPA.CANCELANDO: return ["cancelando", "Cancelando"];
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

  // RF-28: el boton de confirmar existe solo mientras el coordinador lo espera.
  // Visible en cualquier otra etapa seria una forma de confirmar una mision que
  // no esta preguntando nada.
  $("acciones-confirmar").hidden = e.etapa !== ETAPA.ESPERANDO_CONFIRMACION;

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
    // La etapa 7 no tiene paso propio en la barra: es la pausa DENTRO del
    // relevo, asi que ilumina "Relevo" y el usuario no ve la barra apagarse.
    else if (n === e.etapa || (e.etapa === ETAPA.ESPERANDO_CONFIRMACION && n === 2)) clase += " on";
    return `<span class="${clase}">${txt}</span>`;
  }).join("");
}

function pintarPanelSinDatos(mensaje) {
  const panel = $("panel");
  $("acciones-confirmar").hidden = true;
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
campoDestino.refrescarCatalogo();
