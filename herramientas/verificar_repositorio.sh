#!/usr/bin/env bash
# Verifica que el REPOSITORIO sea coherente y utilizable por alguien que lo
# acaba de descargar, sin instalar nada ni lanzar ningun nodo.
#
# Para que existe: 'verificar_instalacion.sh' comprueba que el CODIGO compila y
# funciona en el equipo de quien lo instala. Nadie comprobaba lo otro: que los
# documentos digan la verdad, que las rutas no sean las de una maquina concreta
# y que los archivos citados existan. Por eso el codigo convergia y la
# documentacion divergia.
#
# La regla que impone: una version descargada tiene que funcionar ENTERA, sin
# depender de donde se haya clonado ni de que exista ninguna carpeta concreta.
#
# Uso:  herramientas/verificar_repositorio.sh
# Devuelve 0 si todo pasa, 1 si algo falla.

# Sin 'set -u' ni 'pipefail', por lo mismo que el otro verificador: debe llegar
# al final y contar los fallos, no abortar en el primero.

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

OK=0
FALLOS=0

paso()   { printf '  %-52s' "$1"; }
bien()   { printf '\033[32m[ OK ]\033[0m\n';   OK=$((OK+1)); }
mal()    { printf '\033[31m[FALLO]\033[0m\n'; FALLOS=$((FALLOS+1)); [ -n "${1:-}" ] && printf '%s\n' "$1" | sed 's/^/         -> /'; }
titulo() { printf '\n\033[1m%s\033[0m\n' "$1"; }

echo "Repositorio: $REPO"

# Archivos de texto versionados. Se excluyen binarios y el propio verificador,
# que necesita nombrar las rutas prohibidas para poder buscarlas.
mapfile -t TEXTOS < <(git ls-files -- ':!*.pdf' ':!*.pgm' ':!*.png' ':!*.jpg' ':!*.jpeg' ':!*.dae' ':!*.stl' ':!*.zip' ':!herramientas/verificar_repositorio.sh')

# ------------------------------------------------- 1. independencia de la ruta
titulo '1. El repositorio no depende de donde se clone'

# Se persiguen dos formas del mismo error: la ruta con el nombre de usuario
# incrustado, y la que asume que el repositorio se clono en 'Documents/Tesis'.
# La segunda es mas traicionera porque parece portable al llevar $HOME.
#
# Se perdonan las lineas que nombran la ruta fija para explicar por que se
# quito: igual que en la comprobacion de 'cp -r', documentar el error pasado
# es lo contrario de cometerlo.
paso 'ningun archivo lleva rutas de una maquina concreta'
HITS=$(grep -n '/home/[a-z]\|HOME/Documents/Tesis\|~/Documents/Tesis' "${TEXTOS[@]}" 2>/dev/null \
       | grep -vi 'ruta fija' | head -14)
if [ -z "$HITS" ]; then bien
else mal "$(printf '%s\n' "$HITS")
Sustituir por rutas relativas al repositorio, por \$HOME/Tesis o por <ruta>."; fi

paso 'las herramientas deducen la raiz del repositorio'
HITS=$(grep -n 'HOME/Documents\|HOME/Tesis' herramientas/* 2>/dev/null \
       | grep -vi 'ruta fija' | cut -d: -f1 | sort -u | grep -v verificar_repositorio.sh)
if [ -z "$HITS" ]; then bien
else mal "$HITS
Deducirla del propio script:  REPO=\"\$(cd \"\$(dirname \"\${BASH_SOURCE[0]}\")/..\" && pwd)\""; fi

# ------------------------------------------------------ 2. montaje del entorno
titulo '2. Una sola forma de montar el workspace'

# El workspace se ENLAZA. Copiarlo provoca el incidente R7: se compila una copia
# mientras se edita el repositorio, y los arreglos nunca llegan a ejecutarse.
# Se permiten las lineas que advierten contra la copia.
paso 'ningun documento manda copiar el workspace'
# 'cp -r' con frontera de palabra: 'scp -r' es traer un archivo del vehiculo por
# red, no copiar el workspace, y lo daba por malo (GUIA_PASADA_MAPEO.md).
HITS=$(grep -nE '(^|[^[:alnum:]])cp -r|rsync' -- *.md Documentos/*.md Robot/*.md 2>/dev/null \
       | grep -viv 'nunca\|jamas\|jamás\|no copiar\|en vez de\|R7' | head -8)
if [ -z "$HITS" ]; then bien
else mal "$(printf '%s\n' "$HITS")
El workspace se enlaza con 'ln -s', no se copia."; fi

# ------------------------------------------------------- 3. archivos que citan
titulo '3. Todo lo que se cita existe'

# Solo se miran los documentos que dan instrucciones para HOY: el README, las
# guias operativas, el README del robot y las herramientas. Los planes y el
# cronograma nombran a proposito mundos que todavia no existen
# ('laboratorio_ged.world'): eso es trabajo previsto, no una cita rota.
# 'primer_piso_dos_niveles.world' estuvo en esa lista hasta el 2026-08-14; ya
# existe, asi que ahora lo cubre la comprobacion como cualquier otro.
paso 'los .world citados en las instrucciones existen'
FALTAN=''
INSTRUCCIONES=(README.md Documentos/guia_*.md Robot/README.md)
for s in herramientas/*.sh; do
  [ "$s" = 'herramientas/verificar_repositorio.sh' ] && continue
  INSTRUCCIONES+=("$s")
done
for w in $(grep -oh '[A-Za-z0-9_]*\.world' -- "${INSTRUCCIONES[@]}" 2>/dev/null | sort -u); do
  [ "$w" = 'empty.world' ] && continue
  # '.world' a secas viene de marcadores tipo '<ruta>/<mundo>.world'.
  [ "$w" = '.world' ] && continue
  find . -name "$w" -not -path './.git/*' | grep -q . || FALTAN="$FALTAN $w"
done
if [ -z "$FALTAN" ]; then bien
else mal "no existen en el repositorio:$FALTAN"; fi

paso 'los enlaces entre documentos no estan rotos'
ROTOS=''
while read -r md; do
  dir=$(dirname "$md")
  while read -r destino; do
    case "$destino" in http*|'#'*|mailto:*|'') continue ;; esac
    destino="${destino%%#*}"
    [ -z "$destino" ] && continue
    [ -e "$dir/$destino" ] || ROTOS="$ROTOS
    $md -> $destino"
  done < <(grep -o ']([^)]*)' "$md" | sed 's/^](//; s/)$//')
done < <(printf '%s\n' "${TEXTOS[@]}" | grep '\.md$')
if [ -z "$ROTOS" ]; then bien
else mal "enlaces que no resuelven:$ROTOS"; fi

# La comprobacion anterior mira el enlace desde el lado del que apunta. Esta lo
# mira desde el lado del apuntado, que es donde estaba el agujero: un documento
# al que no llega ningun enlace no lo abre nadie, no lo revisa nadie y se queda
# obsoleto en silencio. Paso de teoria a hecho dos veces el mismo dia:
# 'nav2_robot1_view.rviz' llevaba sin versionar desde S17, y 'DESARROLLO_NAV2.md'
# un mes sin tocar afirmando cosas que el proyecto ya habia refutado.
#
# Se busca por nombre de archivo, no por ruta, porque un enlace relativo se
# escribe de muchas formas ('../ESTADO.md', 'Documentos/X.md') y todas valen.
paso 'ningun documento ni configuracion queda sin citar'
HUERFANOS=''
for f in $(git ls-files '*.md' '*.rviz'); do
  case "$f" in
    # Puertas de entrada: nadie tiene que enlazarlas para que se lean.
    README.md|*/README.md) continue ;;
    # Vienen del repositorio original de AWS; no son documentos del proyecto.
    */CODE_OF_CONDUCT.md|*/CONTRIBUTING.md) continue ;;
  esac
  if ! grep -rlF --include='*.md' --include='*.tex' --include='*.py' \
                 --include='*.xml' --include='*.sh' \
                 "$(basename "$f")" . 2>/dev/null \
       | grep -qv "^\./$f$"; then
    HUERFANOS="$HUERFANOS
    $f"
  fi
done
if [ -z "$HUERFANOS" ]; then bien
else mal "no los cita ningun documento, launch ni herramienta:$HUERFANOS
Enganchar cada uno donde se use, o borrarlo. Un archivo que nadie abre se pudre sin avisar."; fi

# --------------------------------------------------------- 4. una sola verdad
titulo '4. Los documentos no se contradicen'

# El mundo vigente lo declara el README, y el codigo tiene una sola constante que
# lo fija para todos los launch. Si se separan, se mapea y se navega contra
# geometrias distintas, y las metricas dejan de ser comparables entre si.
RAIZ_PY=Robot/aws-deepracer/deepracer_bringup/launch/deepracer_raiz_repo.py
NAV_PY=Robot/aws-deepracer/deepracer_bringup/launch/nav_amcl_demo_sim.launch.py

VIGENTE=$(grep -o 'El vigente es `[^`]*`' README.md | head -1 | sed 's/.*`\(.*\)`/\1/')
paso 'el README declara un mundo vigente'
if [ -n "$VIGENTE" ]; then bien
else mal "no se encontro la frase 'El vigente es \`<archivo>.world\`' en README.md"; fi

paso "los launch usan el mundo vigente ($VIGENTE)"
EN_CODIGO=$(grep -o "^MUNDO_VIGENTE = '[^']*'" "$RAIZ_PY" | sed "s/.*'\(.*\)'/\1/")
if [ "$EN_CODIGO" = "$VIGENTE" ]; then bien
else mal "$RAIZ_PY declara MUNDO_VIGENTE='$EN_CODIGO' y el README declara vigente '$VIGENTE'"; fi

# El mapa se construyo mapeando un .world concreto. Emparejarlo con otro hace que
# AMCL localice contra una geometria que no es la simulada, y la deriva resultante
# no se parece a un error de configuracion: parece un problema de sintonizacion.
paso 'el mapa por defecto de Nav2 es el par del mundo vigente'
MAPA=$(grep -o "'maps', '[^']*'" "$NAV_PY" | sed "s/.*'\(.*\)'/\1/")
RUTA_MAPA="Robot/aws-deepracer/deepracer_bringup/maps/$MAPA"

# Como se decide si el mapa "es el par" del mundo:
#
#   - Los mapas generados desde la geometria del .world declaran su origen en la
#     cabecera del .yaml ('# mundo: <archivo>.world'). Ese es el dato fiable, y
#     permite que el mapa se llame como convenga.
#   - Los mapas hechos con SLAM no llevan esa linea, porque nadie la escribe al
#     guardarlos. Para esos la unica pista disponible es el nombre del archivo,
#     asi que se sigue exigiendo que coincida con el del mundo.
#
# Antes solo existia la segunda regla, y rechazaba un mapa CORRECTO por llamarse
# distinto del mundo del que habia salido.
MUNDO_DEL_MAPA=$(grep -m1 '^# mundo: ' "$RUTA_MAPA" 2>/dev/null | sed 's/^# mundo: //')
ESPERADO="${VIGENTE%.world}.yaml"

if [ ! -f "$RUTA_MAPA" ]; then
  mal "el launch carga 'maps/$MAPA', que no existe en el repositorio"
elif [ -n "$MUNDO_DEL_MAPA" ] && [ "$MUNDO_DEL_MAPA" = "$VIGENTE" ]; then
  bien
elif [ -n "$MUNDO_DEL_MAPA" ]; then
  mal "el mapa '$MAPA' declara venir de '$MUNDO_DEL_MAPA' y el mundo vigente es '$VIGENTE'"
elif [ "$MAPA" = "$ESPERADO" ]; then
  bien
else
  mal "el launch carga '$MAPA' sobre el mundo '$VIGENTE'; como no declara de que mundo salio, tendria que llamarse '$ESPERADO'"
fi

# La pose de nacimiento vivio en tres archivos a la vez -robot.sh y los dos
# launch- y al cambiar de mundo se actualizaron dos. La que se quedo vieja hacia
# nacer al vehiculo en la explanada entre los dos pasillos, y eso NO da error:
# Gazebo abre, los siete controladores quedan activos y no hay pasillo alrededor.
# Se delega en la herramienta porque hay que leer el .pgm para saberlo.
paso 'cada robot nace en celda libre de su mapa'
SALIDA_POSE=$(python3 herramientas/verificar_pose_spawn.py 2>&1)
if [ $? -eq 0 ]; then
  bien
else
  mal "$(printf '%s\n' "$SALIDA_POSE" | grep -E 'FALLO|Error|error' | head -5)"
fi

# ---------------------------------------------------------- 5. estado al dia
titulo '5. El tablero de estado refleja la realidad'

paso 'ESTADO.md cita el ultimo entregable que existe'
ULTIMO=$(ls Documentos/Entregables/Entregable_semana_*.pdf 2>/dev/null \
         | sed 's/.*semana_0*\([0-9]*\)\.pdf/\1/' | sort -n | tail -1)
DECLARADO=$(grep -o 'Último entregable formal.*| Semana [0-9]*' ESTADO.md | grep -o '[0-9]*$')
if [ "$ULTIMO" = "$DECLARADO" ]; then bien
else mal "ESTADO.md dice 'Semana $DECLARADO' pero el ultimo PDF en Documentos/Entregables es el de la semana $ULTIMO"; fi

paso 'ESTADO.md se actualizo con el trabajo mas reciente'
CORTE=$(grep -o 'Fecha de corte.*| [0-9-]*' ESTADO.md | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}')
ULTIMO_COMMIT=$(git log -1 --format=%cs)
if [ -z "$CORTE" ]; then
  mal "ESTADO.md no declara 'Fecha de corte'"
# La tolerancia es de dos dias -un fin de semana-, no de una semana: ESTADO.md
# dice de si mismo que se actualiza al cerrar cada sesion, y con siete dias de
# margen un tablero atrasado seis dias pasaba la comprobacion.
elif [ "$(date -d "$CORTE" +%s 2>/dev/null)" -ge "$(date -d "$ULTIMO_COMMIT -2 days" +%s 2>/dev/null)" ]; then bien
else mal "la fecha de corte es $CORTE y el ultimo commit es del $ULTIMO_COMMIT: hay trabajo sin registrar. ESTADO.md dice de si mismo que se actualiza al cerrar cada sesion"; fi

# ---------------------------------------------------------------- resultado
titulo 'Resultado'
echo "  $OK comprobaciones pasan, $FALLOS fallan."
if [ "$FALLOS" -eq 0 ]; then
  echo
  echo "  El repositorio es coherente: cualquiera puede descargarlo y las"
  echo "  instrucciones que lea seran ciertas en su equipo."
  exit 0
else
  echo
  echo "  Corregir los fallos de arriba y volver a ejecutar este script."
  exit 1
fi
