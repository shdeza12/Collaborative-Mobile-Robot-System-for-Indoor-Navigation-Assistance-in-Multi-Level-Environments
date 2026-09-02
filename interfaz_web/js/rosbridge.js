"use strict";
/**
 * Cliente minimo del protocolo de rosbridge (JSON sobre WebSocket), a medida
 * del contrato de Documentos/CONTRATO_INTERFACES.md seccion 4.
 *
 * No se usa roslib.js: su clase de acciones habla el protocolo de actionlib
 * de ROS 1 (goal/cancel/status/result por topicos), y rosbridge_suite 2.x
 * para ROS 2 expone en su lugar los ops "send_action_goal", "action_feedback"
 * y "action_result" (confirmado contra el paquete instalado,
 * rosbridge_library/capabilities/send_action_goal.py). Forzar roslib.js
 * contra ese protocolo distinto fallaria en silencio; un cliente a medida
 * para los pocos mensajes de este contrato es mas fiable.
 */
class Puente {
  constructor(url) {
    this.url = url;
    this.socket = null;
    this.suscripciones = new Map(); // topic -> {type, qos, cb}
    this.acciones = new Map();      // id -> {onFeedback, onResult}
    this.contador = 0;
    this.onEstadoConexion = null;   // (conectado: boolean) => void
    this._conectar();
  }

  _conectar() {
    this.socket = new WebSocket(this.url);
    this.socket.onopen = () => {
      this.onEstadoConexion && this.onEstadoConexion(true);
      // Un socket nuevo no hereda las suscripciones del anterior: hay que
      // volver a pedirlas todas.
      for (const [topic, s] of this.suscripciones) this._enviarSuscripcion(topic, s);
    };
    this.socket.onclose = () => {
      this.onEstadoConexion && this.onEstadoConexion(false);
      setTimeout(() => this._conectar(), 2000);
    };
    this.socket.onerror = () => this.socket.close();
    this.socket.onmessage = (ev) => this._recibir(ev.data);
  }

  _recibir(texto) {
    let msg;
    try {
      msg = JSON.parse(texto);
    } catch {
      // "distancia_restante" llega NaN mientras no ha llegado ningun /odom
      // del robot activo (documentado en EstadoRobot.msg). Python serializa
      // eso como el token NaN, que no es JSON valido y rompe JSON.parse. Se
      // sustituye por null y se reintenta en vez de descartar el mensaje.
      try { msg = JSON.parse(texto.replace(/:\s*NaN/g, ":null")); }
      catch { return; }
    }
    if (msg.op === "publish") {
      const s = this.suscripciones.get(msg.topic);
      if (s) s.cb(msg.msg);
    } else if (msg.op === "action_feedback") {
      const a = this.acciones.get(msg.id);
      if (a && a.onFeedback) a.onFeedback(msg.values);
    } else if (msg.op === "action_result") {
      const a = this.acciones.get(msg.id);
      if (a) {
        if (a.onResult) a.onResult(msg.result ? msg.values : null, !!msg.result);
        this.acciones.delete(msg.id);
      }
    }
  }

  _enviar(obj) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(obj));
    }
  }

  _enviarSuscripcion(topic, s) {
    const m = { op: "subscribe", topic, type: s.type };
    if (s.qos) m.qos = s.qos;
    this._enviar(m);
  }

  /** qos, si se pasa: {history,depth,reliability,durability} en minuscula. */
  suscribir(topic, type, cb, qos = null) {
    const s = { type, qos, cb };
    this.suscripciones.set(topic, s);
    this._enviarSuscripcion(topic, s);
  }

  /** Llama una accion. Devuelve el id de la peticion, para poder cancelarla. */
  enviarMeta(accion, tipo, args, { onFeedback, onResult } = {}) {
    const id = "hri_" + (++this.contador) + "_" + Date.now();
    this.acciones.set(id, { onFeedback, onResult });
    this._enviar({
      op: "send_action_goal", action: accion, action_type: tipo,
      id, args, feedback: true,
    });
    return id;
  }

  cancelarMeta(accion, id) {
    this._enviar({ op: "cancel_action_goal", action: accion, id });
  }
}
