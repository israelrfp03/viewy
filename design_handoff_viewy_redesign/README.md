# Handoff: Rediseño visual de Viewy + sistema de mascota «Popi»

## Resumen
Rediseño completo del frontend de Viewy (Django templates + Tailwind v4 + JS simple): paso del tema oscuro zinc actual a una identidad **papel / tinta / azul de marca**, tipografía display grande, composición editorial asimétrica y una mascota de palomitas (Popi) con variantes por contexto.

**No se cambia la lógica de backend** salvo los pocos añadidos de contexto listados en cada pantalla (marcados como `CONTEXTO NUEVO`). Todos son opcionales: la plantilla debe funcionar si el dato no llega.

## Sobre los archivos de diseño
Los `.dc.html` de `designs/` son **referencias de diseño hechas en HTML** (mockups con estilos inline), no código de producción. La tarea es **recrearlos en los templates Django existentes con Tailwind CSS**, siguiendo los patrones del repo (`{% extends "base.html" %}`, `{% querystring %}`, `data-reveal`, `data-counter`, forms de Django). Se abren directamente en el navegador (necesitan `support.js` en la misma carpeta).

No añadir React, Vue ni librerías nuevas. Chart.js ya está en el proyecto y se mantiene.

## Fidelidad
**Alta fidelidad.** Colores, tipografía, espaciado, radios y copy son finales. Recrear con la mayor precisión posible usando clases Tailwind.

## Cómo trabajar (respeta CLAUDE.md)
- Trabaja en una rama: `git checkout -b feat/redesign`.
- **Una fase cada vez.** Al terminar cada fase: `npm run build:css`, `pytest`, revisar a mano en desktop (1280) y móvil (390), commit pequeño en inglés, **y DETENTE** hasta que el usuario pida la siguiente.
- Antes de tocar un template, léelo y reutiliza toda la lógica de plantilla (bucles, condiciones, URLs, nombres de campos de formulario). Solo cambia el marcado y las clases.

### Fases
| # | Fase | Archivos principales | Diseño de referencia |
|---|---|---|---|
| 1 | Tokens + base layout + navbar + tab bar móvil + toasts | `static/css/input.css`, `templates/base.html`, `templates/partials/*`, `static/js/nav.js`, `static/images/mascot/*` | `Viewy Design System.dc.html` (opción **1a**) |
| 2 | Componentes reutilizables | `templates/components/*` | `Viewy Componentes.dc.html` |
| 3 | Home pública | `templates/home.html` | `Viewy Home.dc.html` |
| 4 | Biblioteca | `templates/library/list.html` | `Viewy Biblioteca.dc.html` |
| 5 | Detalle + editar + eliminar | `templates/library/detail.html`, `edit.html`, `confirm_delete.html` | `Viewy Detalle.dc.html` |
| 6 | Analytics | `templates/analytics/dashboard.html`, `static/js/analytics/*` | `Viewy Analytics.dc.html` |
| 7 | Recomendaciones | `templates/recommendations/form.html` | `Viewy Recomendaciones.dc.html` |
| 8 | Asistente | `templates/assistant/chat.html` | `Viewy Asistente.dc.html` |
| 9 | Importación | `templates/imports/start.html`, `preview.html`, `result.html` | `Viewy Importar.dc.html` |
| 10 | Auth + perfil + 404/500 | `templates/accounts/*`, `templates/404.html`, `templates/500.html` | `Viewy Auth.dc.html`, `Viewy Perfil.dc.html`, `Viewy Componentes.dc.html` |

Las pantallas restantes (`library/create.html`, `search.html`, `anime_search.html`) no tienen mockup propio: aplicarles el mismo encabezado de página, inputs, pósters y estados vacíos.

---

## Design tokens

### `static/css/input.css` — sustituir el bloque `@theme`
```css
@import "tailwindcss";
@source "../../templates/**/*.html";

@theme {
  --font-display: "Bricolage Grotesque", ui-sans-serif, sans-serif;
  --font-sans: "Geist", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "Geist Mono", ui-monospace, monospace;

  --color-paper: #F6F6F3;
  --color-surface: #FFFFFF;
  --color-line: #E4E4DF;
  --color-line-soft: #EEEEEA;
  --color-faint: #A9ABB0;
  --color-muted: #6B6D73;
  --color-ink-2: #2A2C33;
  --color-ink: #0D0E12;

  --color-brand-50: #EEF2FD;
  --color-brand-100: #DCE4FA;
  --color-brand-200: #A6B9E8;
  --color-brand-300: #7392DB;
  --color-brand-400: #406ACE;
  --color-brand-500: #0038BE;
  --color-brand-600: #002FA0;
  --color-brand-700: #00257D;

  /* estados: misma luminosidad/croma, cambia el tono */
  --color-watching: #0038BE;   --color-watching-bg: #E8EEFC;  --color-watching-fg: #0038BE;
  --color-completed: #2E9E6A;  --color-completed-bg: #E4F4EB; --color-completed-fg: #1B6E47;
  --color-planned: #C08F1E;    --color-planned-bg: #F7EFD9;   --color-planned-fg: #7A5A0C;
  --color-dropped: #D0584A;    --color-dropped-bg: #F9E6E2;   --color-dropped-fg: #9A3325;

  --text-display-xl: 9.75rem;  --text-display-xl--line-height: .84;  /* 156px hero home */
  --text-display-lg: 8rem;     --text-display-lg--line-height: .85;  /* 128px título de página */
  --text-display-md: 3.5rem;   --text-display-md--line-height: .9;   /* 56px secciones */

  --radius-poster: 4px;
  --radius-card: 10px;

  --animate-fade-in-up: fade-in-up 0.5s ease-out both;
}
```
Mantener `@keyframes fade-in-up`, `[data-reveal]`, `prefers-reduced-motion`. Eliminar `.styled-form` cuando ya no se use `form.as_p` (fase 10).

### Fuentes (`base.html`, sustituye Inter)
```html
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Escala tipográfica
| Rol | Fuente | Tamaño / interlineado | Peso | Tracking |
|---|---|---|---|---|
| display-xl (hero home) | Bricolage | 156px / .84 (móvil 76px) | 800 | -0.055em |
| display-lg (título de página) | Bricolage | 128px / .85 (tablet 88–96, móvil 56–64) | 800 | -0.05em |
| título detalle | Bricolage | 152px / .82 (móvil 76px) | 800 | -0.055em |
| display-md (sección) | Bricolage | 56px / .9 | 800 | -0.045em |
| h3 de bloque | Bricolage | 28–32px | 700 | -0.03em |
| número de stat | Bricolage | 112px (analytics), 72px (perfil), 56px (móvil) | 800 | -0.055em |
| title | Geist | 22px / 1.2 | 600 | -0.01em |
| body | Geist | 16–18px / 1.55 | 400 | 0 |
| ui | Geist | 14px / 1.4 | 500–600 | 0 |
| meta / eyebrow | Geist Mono | 10–12px, MAYÚSCULAS | 500 | +0.1em |

Regla: nada en tamaños intermedios entre 32 y 56px salvo excepciones. Metadata (año, tipo, episodios, estudio) siempre en mono y mayúsculas.

### Espaciado y layout
- Base 4px (escala Tailwind). Componentes 8–24px; secciones 96px en móvil / 160px en desktop.
- Contenedor: `max-w-[1360px] mx-auto px-5 md:px-10 xl:px-14`.
- Grid: 4 col móvil, 8 tablet, 12 desktop, `gap-6` (24px). Composición típica 7/5 o 5/7 con 1 columna de aire.
- Radios: 4px pósters e inputs pequeños, 8px inputs, 10px cards, 14px modales, `rounded-full` botones/chips.
- Sombras: póster en hover `0 18px 36px rgba(13,14,18,.2)`; modal `0 24px 64px rgba(13,14,18,.3)`; dropdown `0 12px 40px rgba(13,14,18,.12)` + `ring-1 ring-line`.
- Reparto de color por pantalla: 80% papel, 15% tinta, 5% azul. El azul solo para acción primaria, estado activo, dato destacado y mascota.

---

## Sistema de mascota «Popi»
Mismo PNG base siempre; **nunca redibujar**. Cada variante = pose (transform) + filtro + accesorio CSS superpuesto (formas simples, azul `brand-500` o tinta `ink`, bordes redondeados). Máximo una mascota visible por pantalla.

### Assets (en `assets/`, copiar a `static/images/mascot/`)
- `mascot.png` → `base.png` — mascota azul con relleno blanco (fondos claros). 1254×1254, transparente.
- `mascot-line-white.png` → `line-white.png` — versión de línea blanca (fondos azules / negros).
- `wordmark-white.png` → `wordmark-white.png` — logotipo «viewy» blanco. Sobre fondo claro se usa como máscara CSS teñida de azul:
  `class="h-6 w-[76px] bg-brand-500 [mask:url(...)_center/contain_no-repeat]"`.
- Los favicons existentes (`static/images/favicon-*.png`) se mantienen.

### Partial `templates/components/mascot.html`
Uso: `{% include "components/mascot.html" with variant="search" size="spot" %}`
- `size`: `sticker` (24–40px), `spot` (96–160px), `hero` (280–520px).
- `variant`:

| variant | pose (transform / filtro) | accesorio | dónde |
|---|---|---|---|
| default | — | — | logo, footer |
| happy | rotate(-8deg) translateY(-6px) | pill azul «+1» arriba-dcha | toasts de éxito, añadir |
| thinking | rotate(7deg) translate(-10px,8px) | burbuja: 2 círculos + pill con 3 puntos, borde 3px azul | cargando recomendaciones / asistente |
| search | rotate(-4deg) translateX(-12px) | lupa: círculo borde 7px tinta + mango 26×9 rotado 45° | buscador, sin resultados, 404 |
| error | rotate(-10deg) translateY(12px) grayscale(1) opacity .85 | círculo tinta con «!» | errores, 500, alerts de error |
| celebrate | translateY(8px) scale(1.04) | confeti: rectángulos 6×14 en brand/verde/ámbar/rojo | serie completada, importación ok |
| sleep | rotate(12deg) saturate(.55) | «z z Z» en Bricolage 800, tonos brand-300→500 | sin actividad, «Viendo» vacío |
| analytics | translateX(-18px) | tarjeta blanca borde 3px tinta con 3 barras | analytics sin datos |
| ai | rotate(-3deg) translateY(10px) | 3 «✦» en brand-500/400/300 | recomendaciones, avatar asistente |
| import | translateX(18px) rotate(4deg) | portapapeles blanco borde 3px con 3 líneas y puntos | importación |
| favorite | translateY(12px) | 3 «★» azules en arco | favoritos vacío |
| loader | rebote 2px en bucle | 3 puntos con opacidad 1/.6/.3 | loader de página |

Movimiento (≤400ms, ease-out, desactivado con `prefers-reduced-motion`): happy = salto 6px; thinking = puntos en secuencia; sleep = Z flotando 3s; loader = rebote 2px.

Expresiones faciales distintas (sorpresa, triste, dormida) requieren ilustración nueva; dejar en el partial un hueco opcional `face` para futuros `mascot-face-*.svg`.

---

## Componentes (fase 2) — recetas Tailwind
Ver `Viewy Componentes.dc.html`.

- **Botón primario**: `h-12 px-[22px] rounded-full bg-brand-500 text-white font-semibold text-[15px] transition hover:bg-brand-600 hover:-translate-y-px hover:shadow-[0_6px_16px_rgba(0,56,190,.3)] active:scale-[.98]`. Sustituye todos los `hover:scale-105`.
- **Tinta**: igual con `bg-ink hover:bg-brand-500`. **Secundario**: `ring-[1.5px] ring-inset ring-ink bg-transparent`. **Ghost**: sin fondo. **Peligro**: texto `text-dropped-fg`; en modal de confirmación `bg-dropped text-white`.
- **Outline azul pequeño** (+1 episodio, + Añadir): `h-9 px-3.5 rounded-full ring-[1.5px] ring-inset ring-brand-500 text-brand-500 text-[13px] font-semibold`.
- Alturas: 36 / 44 / 48 / 52px. **Cargando**: `bg-brand-200` + 3 puntos + «Pensando», deshabilitado.
- **Badge de estado**: `inline-flex items-center gap-1.5 h-7 px-3 rounded-full text-xs font-semibold bg-{estado}-bg text-{estado}-fg` + punto 6px `bg-{estado}`. Crear un filtro o `{% if %}` que mapee `planned/watching/completed/dropped` a estas clases.
- **Tag de género**: `h-7 px-3 rounded-full ring-1 ring-inset ring-[#D6D6D1] text-xs font-medium`. **Meta chip**: `h-6 px-2 rounded bg-ink text-white font-mono text-[10px] tracking-[.08em] uppercase`.
- **Nota compacta**: Bricolage 700; color ≥8 `text-brand-500`, 5–7 `text-ink`, ≤4 `text-dropped`, sin nota «—» `text-faint`. Nada de estrellas ámbar.
- **Escala de nota 1–10** (detalle): 10 celdas `h-7 rounded` `bg-brand-100 text-brand-500`; la seleccionada `bg-brand-500 text-white`. Nota grande 96px Bricolage azul al lado.
- **Input** `components/field.html`: label `text-[13px] font-semibold mb-2`; widget `h-12 (52 en auth) rounded-lg bg-white ring-1 ring-inset ring-line px-4 text-[15px] (16px en móvil)`; foco `ring-2 ring-brand-500 shadow-[0_0_0_4px_#DCE4FA]`; error `ring-[1.5px] ring-dropped` + mensaje `text-xs font-medium text-dropped-fg`. Las clases se añaden en los forms con `widget.attrs` (sin lógica nueva).
- **Select**: mismo estilo que el input + chevron. **Toggle**: 44×26 `rounded-full`, on `bg-brand-500`. **Checkbox/radio**: `accent-brand-500` o estilizados, 20px.
- **Póster** `components/poster.html` (args: entry o media, size, show_meta): `aspect-[2/3] rounded-[4px] overflow-hidden`, **sin borde ni degradados de color**. Hover: `-translate-y-1` + sombra y overlay `bg-gradient-to-t from-ink/90` con sinopsis (3 líneas) + «Ver ficha» + ♡. Favorito: círculo blanco 28px arriba-dcha con ♥ azul. Sin `poster_url`: bloque `bg-brand-500` con mascota línea blanca 26px arriba y «Sin póster todavía» en Bricolage 800 18px. Skeleton: `bg-[#EFEFEB]` + shimmer. Debajo del póster: título `text-sm font-semibold truncate` + nota compacta a la derecha; meta mono 10px; estado como punto + texto 11px.
- **Alerts** `partials/_toasts.html`, mapeo por `message.tags`: success → toast negro `rounded-full bg-ink text-white` abajo-dcha, mascota happy en círculo blanco 36px, auto-cierre 4s, acción opcional «Deshacer» `text-brand-200`. warning/error/info → inline `rounded-card px-4 py-3.5 text-sm font-medium` en `planned-bg/fg`, `dropped-bg/fg` (+ mascota error), `brand-50/brand-700`.
- **Paginación**: «← Anterior» · números 40px (actual `bg-ink text-white rounded-full`) · «Siguiente →», línea superior `border-t border-line`. Móvil: «← 2 / 9 →».
- **Loaders**: página = mascot-loader; inline = spinner 36px `border-3 border-brand-100 border-t-brand-500`; barra superior 4px.
- **Chart card** `components/chart_card.html`: `bg-white rounded-card p-8`, slots eyebrow (mono), title (Bricolage 28px, escrito como conclusión), canvas, footnote (mono faint). Un dato destacado en azul, el resto tinta.
- **Modal**: overlay `bg-ink/45`, panel `bg-white rounded-[14px] p-8 shadow-modal`. Confirmar eliminación con mascota error 72px, título Bricolage 30px, botones Cancelar / «Sí, quitar» (`bg-dropped`). En móvil = bottom sheet. JS simple con `<dialog>`.
- **Estado vacío** `components/empty_state.html` (variant, title, text, cta_url, cta_label): fondo papel, mascota spot, título Bricolage 800 26–44px, texto muted 13–15px, CTA tinta.

---

## Pantallas

### 1 · Base layout + navbar (opción 1a)
**Desktop (≥1024px)** — sustituye la sidebar por **barra superior** `h-[72px] px-14 flex items-center gap-10 border-b border-line bg-paper` (sticky; el borde aparece al hacer scroll).
- Izquierda: mascota 34px + wordmark azul enmascarado 76×24.
- Nav: Biblioteca · Descubrir (recomendaciones) · Asistente · Estadísticas. `text-sm font-medium text-muted hover:text-ink`; activo `text-ink` + punto 4px `bg-brand-500` centrado debajo. Activo por `request.resolver_match.app_name` / `url_name` (no comparar paths).
- Derecha: búsqueda pill 280×40 blanca `ring-1 ring-line` (placeholder «Buscar películas, series, anime», tecla `/` como atajo, GET a `library:search`); botón «+ Añadir» primario 40px (→ `library:search`); avatar 40px `bg-ink` con inicial Bricolage 700 y anillo azul (`shadow-[0_0_0_3px_#F6F6F3,0_0_0_5px_#0038be]`).
- Menú de avatar (dropdown 240px): nombre + meta mono «248 TÍTULOS · 31 FAVORITOS», Mi perfil, Importar lista, separador, Cerrar sesión (form POST existente).
- Sin sesión: nav «Cómo funciona · Funciones · Recomendaciones IA» (anclas de la home) + «Iniciar sesión» texto + «Crear mi biblioteca» botón tinta.
- Quitar emojis de la navegación.

**Tablet (768–1023)**: barra 64px, solo mascota (sin wordmark), 4 destinos con subrayado inferior 2px azul en el activo, búsqueda y + como iconos circulares de 40px. La búsqueda abre un overlay a pantalla completa.

**Móvil (<768)**: cabecera 56px (logo + botón de búsqueda 44px). **Tab bar inferior flotante** `fixed left-3 right-3 bottom-4 h-16 rounded-[22px] bg-ink` con 5 huecos: Biblioteca · Descubrir · **botón central Añadir** (círculo 56px `bg-brand-500`, elevado −26px, anillo del color de fondo, mascota línea blanca 36px) · Asistente · Más. Activo = texto blanco + barra 18×3 `bg-brand-400`. «Más» abre bottom sheet: avatar + «VER PERFIL →», Estadísticas, Importar lista, Favoritos, Cerrar sesión y un aviso con mascota sleep si no hay actividad reciente. Dejar `pb-28` en `<main>` para que la barra no tape contenido. La tab bar se oculta en el detalle (tiene barra de acciones propia) y en el asistente (composer fijo).

**Encabezado de página estándar**: eyebrow mono muted + título display-lg a 7 columnas; entradilla a la derecha (col 8–12) alineada abajo.

**JS**: `static/js/nav.js` para dropdown, bottom sheet, atajo `/` y borde al hacer scroll. `animations.js` se mantiene.

### 2 · Home (`home.html`)
Hero en 12 col: izquierda (8 col) eyebrow «PELÍCULAS · SERIES · ANIME», H1 «Todo lo / que **ves**, / en orden.» a 156px («ves» azul), texto 18px máx. 340px y CTAs «Crear mi biblioteca →» (primario 52px) + «Ya tengo cuenta» (secundario). Derecha (cols 8–12): dos pósters inclinados (−7° y 4°, 210 y 250px) y mascota 230px con claqueta. Parallax suave de 8px (`data-parallax`).
Después: fila «Lo que la gente está registrando» (anchos 2fr 1fr 1fr 1.4fr 1fr 1fr, alineados abajo; en móvil scroll horizontal con snap) → «Registra. Puntúa. Recuerda.» 88px + 3 pasos numerados 01/02/03 → features (card blanca de 7 col con 4 pósters + badges de estado; card de progreso «Frieren · episodio 18 de 28»; card negra de importación con mascota línea) → **bloque azul a sangre** de estadísticas (números 144px blancos «248 títulos registrados» / «1.204 horas de películas» + mini gráfico de 12 barras, mascota línea abajo-dcha) → bloque de IA (póster de 5 col con mascota ai, titular «No otra lista. **Tu** siguiente.» 96px, cita en card blanca) → CTA final centrado con mascota 180px «¿Qué estás viendo ahora?» 120px → footer tinta.
Con sesión iniciada: `/` redirige a Biblioteca (cambio mínimo en `library.views.home`) o muestra la cabecera de Biblioteca. Consultar con el usuario antes de cambiarlo.

### 3 · Biblioteca (`library/list.html`)
- Encabezado: «Biblioteca» 128px + frase de stats con `quick_stats` a la derecha: «**248 títulos.** 12 viendo, 64 pendientes, 31 favoritos y una nota media de **7,8**». Se eliminan las 6 tarjetas de stats.
- Barra de filtros entre `border-t border-ink` y `border-b border-line`, `py-3.5`: pestañas de estado (Todos / Viendo / Pendiente / Terminado / Abandonado) con punto de color y contador mono; activa `bg-ink text-white`. Separador. Tipo (Todo / Películas / Series / Anime) como segmento secundario (activo con `ring-1 ring-ink`). A la derecha: «♡ Favoritos» toggle, búsqueda 200px «En mi biblioteca…», orden «Orden: Recientes ▾». Todo sigue usando `{% querystring %}` y los forms GET actuales (el select de orden mantiene `onchange="this.form.submit()"`).
- **Viendo ahora** (solo con estado = Todos y página 1): 3 cards blancas (la primera más ancha, grid 1.3fr 1fr 1fr) con póster, meta, título Bricolage 24px, «Ep. 18 de 28», barra de progreso 6px `bg-brand-50` / `bg-brand-500` y «+1 episodio» (POST a `library:update` o endpoint pequeño). `CONTEXTO NUEVO: watching_now` (≤3 entradas en estado watching, 1 query).
- Grid de pósters: 6 col desktop / 4 tablet / 2 móvil, `gap-x-6 gap-y-10`, componente póster con meta debajo. Encabezado «Todo» + mono «248 TÍTULOS · PÁGINA 1 DE 9».
- Paginación del sistema.
- **Tablet**: botón «Filtros (n)» abre panel lateral 340px con chips de estado/tipo, toggle favoritos y «Ver N títulos».
- **Móvil**: título 60px, frase corta, pestañas de estado en scroll horizontal (40px de alto), fila de «Tipo · Favoritos» (abre bottom sheet) + orden, grid 2 col.
- Vacíos: biblioteca vacía (mascota default hero, «No has añadido nada todavía.», CTAs «Buscar un título» + «Importar lista»); sin resultados con filtros (mascota search, «Nada con «{q}» en {estado}.» + «Quitar filtros»); «Viendo» vacío (mascota sleep, «No estás viendo nada ahora.» + «Tienes N pendientes. Elige uno»).

### 4 · Detalle (`library/detail.html`)
- «← Biblioteca» 13px muted.
- Grid 12: **póster 4 col sticky** (sombra `0 32px 64px rgba(13,14,18,.2)`) con «Editar registro» primario + botón ♥ circular 48px y «Eliminar de mi biblioteca» (texto `dropped-fg`) debajo. **Columna 6–12**: meta mono «ANIME · 2023 · 28 EPISODIOS · 24 MIN» · título 152px · títulos alternativos (romaji / english) 17px muted · tags de género · sinopsis 18px máx. 600px.
- **Tu registro** (card blanca, p-8): eyebrow + badge de estado con ▾ (cambio rápido); nota gigante 96px azul + «TU NOTA / 10»; escala 1–10; progreso «Episodio 18 de 28» + «+1 episodio» + barra 8px; fechas en 3 col (Empezado, Terminado, Añadido) con eyebrow mono; reseña como cita en Bricolage 500 24px.
- **Anime** (`media_type == "anime"`): separador `border-t border-ink`, eyebrow «FICHA · ANILIST», «Detrás de la serie» 56px; Estudio / Origen / Episodios en Bricolage 700 32px. Personajes: 6 col, imagen circular, nombre + rol mono. Staff (5 col, filas con `border-b`) y Relacionado (7 col, mini pósters con tipo de relación mono azul). Episodios en 2 col con número mono y «VISTO» azul para `number ≤ current_episode`. Sin metadata: estado vacío con mascota search + «Buscar en AniList». `anime_provider_unavailable`: alert warning.
- **Editar** (`edit.html`): mismo formulario, presentado como modal en desktop / bottom sheet en móvil (o página con ese panel centrado si se prefiere sin JS): estado como 4 botones segmentados (radio), nota, episodio actual con −/+, fechas inicio/fin, reseña, toggle favorito, Cancelar / Guardar.
- **Celebración**: al guardar con `current_episode == episodes` o al pasar a completed, mostrar el banner azul «Frieren, completado.» con mascota celebrate y CTAs «Ponerle nota» / «¿Qué veo ahora?» (vía `messages` con tag `celebrate`).
- **Móvil**: póster a sangre de 420px con fundido a papel, botones circulares ← y ♥ flotando, título 76px superpuesto −72px, nota 48px + progreso en línea, sinopsis; **barra de acciones fija** abajo (Editar secundario + «+1 episodio» primario).

### 5 · Analytics (`analytics/dashboard.html`)
- «Tu año en / pantalla.» 128px + selector de año (2024 / 2025 / 2026 / Siempre; activo `bg-ink`). `CONTEXTO NUEVO opcional: ?year=`; sin él se muestra «Siempre» y se oculta el selector.
- Fila de 4 números de 112px entre `border-t border-ink` y `border-b border-line`: total, terminados este año (subtítulo «· N este mes»), nota media en azul («· N puntuados»), horas de películas (`movie_watch_minutes/60`, sufijo «h» 48px).
- Grid 12: **Actividad mensual** (8 col, barras dobles añadidos `brand-200` / terminados `ink`, el mes máximo en `brand-500`, titular «Octubre fue tu mes: 9 terminados»); **Por tipo** (4 col, card `bg-ink`, barra apilada 16px blanco / brand-300 / brand-500 y porcentajes en Bricolage 40px); **Tus notas** (5 col, histograma 1–10, la moda en azul, fila Mejor/Peor/Moda); **Evolución anual** (7 col, barras con valor encima, el mejor año azul, el año en curso rayado).
- «Cómo ves.» (datos de pandas `advanced` + `anime_stats`): filas clave–valor con `border-b` (días medios para terminar, género mejor puntuado, estudio top, origen top, tasa de abandono).
- «Terminado recientemente»: 5 pósters (`recent_completed`).
- Chart.js: configuración global en `static/js/analytics/` — `font.family = 'Geist'`, sin grid ni bordes de eje, `borderRadius: 3`, sin leyenda nativa (leyenda en HTML). Los titulares-conclusión se generan en la vista a partir de los datos ya calculados.
- **Móvil**: título 56px, stats en grid 2×2 (56px) con separadores, gráficos en carrusel horizontal con snap e indicador de puntos.
- **Sin datos** (<3 terminados con nota): mascota analytics, «Aún no hay nada que contar.», «Termina y puntúa 3 títulos y Popi empieza a hacer cuentas.» + barra de progreso 1/3.

### 6 · Recomendaciones (`recommendations/form.html`)
- Encabezado 6 col «Recomiéndame algo.» 104px (eyebrow «BASADO EN TUS N TÍTULOS»). A la derecha: input pill 60px (el `textarea request_text` pasa a una sola línea que crece) con botón «✦ Recomendar» dentro; presets como chips **sin emoji** (mismo `data-preset` y mismo JS).
- `results[0]` = **principal**: póster 5 col con chip «✦ Encaje 94%» (solo si el dato existe), columna 7–12 con mascota ai 52px + «LA RECOMENDACIÓN DE HOY», meta mono, título 112px, card «POR QUÉ ENCAJA CONTIGO» con `rec.reason` en Bricolage 500 22px, CTA «Añadir a Pendiente» + select de tipo («como Serie ▾») dentro del mismo form POST a `library:add_from_tmdb`, «Otra ↻» (reenvía el form).
- `results[1:]`: «También podría gustarte», 4 col: póster, meta, título Bricolage 22px, razón 14px, «+ Añadir» outline.
- `is_thin_profile`: alert warning con mascota thinking. `error_message`: alert error con mascota error.
- **Cargando**: al enviar, sustituir los resultados por la pantalla de mascota thinking + «Revisando tus N títulos…» + pasos en mono (texto estático).
- **Móvil**: chips en scroll, póster 4:5 a ancho completo, título 52px, razón corta, barra fija abajo (↻ + «Añadir a Pendiente»).

### 7 · Asistente (`assistant/chat.html`)
- **Vacío**: 7 col con eyebrow, «¿Qué quieres / saber de ti?» 112px, composer pill 64px con botón circular azul ↑, presets como 4 cards de 2 col (mismo `data-question`). 4 col derecha: mascota ai 240px + aviso «Cada pregunta va por separado…».
- **Conversación** (columna máx. 760px centrada): pregunta del usuario en burbuja `bg-ink text-white rounded-[22px_22px_6px_22px]` a la derecha; respuesta **sin burbuja**: avatar mascota 40px en círculo blanco + texto 17px/1.6. Bloques de datos opcionales: ranking con barras (card blanca), fila de 5 pósters + enlace, número grande. Pie de fuente mono faint («CALCULADO CON 196 NOTAS · DJANGO ORM»). Error: texto en `planned-fg` con mascota error. Pensando: 3 puntos + «Mirando tus películas…».
- `CONTEXTO NUEVO opcional: turn.data` (estructura que ya calcula `assistant/responses.py`) para pintar los bloques; si no existe, solo texto.
- Composer fijo abajo con degradado a papel; sugerencias encima; «Borrar historial» (form POST existente) a la derecha.
- **Móvil**: cabecera 56px (← mascota «Asistente»), sin tab bar, composer 52px y chips encima.

### 8 · Importación (`imports/*`)
Stepper común: 1 Pegar · 2 Revisar · 3 Listo (actual con círculo 24px `bg-brand-500`, resto con anillo `ring-[#D6D6D1]`).
- **start.html**: 5 col con «Pega tu lista.» 96px, texto «**Nada se guarda todavía**» y mascota import. 7 col: textarea 420px blanco, Geist Mono 15px/1.9, foco azul, contador «8 / 100 TÍTULOS» abajo-dcha (JS), ayuda de formatos + «Analizar lista →». Mantener el JS de «Analizando…».
- **preview.html**: título «Revisa antes / de confirmar.» 80px, contadores por estado a la derecha (encontrados verde, elegir ámbar, no encontrado rojo, ya lo tienes azul; Bricolage 48px). Tabla densa (`border-t border-ink`): columnas punto de estado · tu línea (mono) · coincidencia (mini póster 32×48 + título + nota de estado) · Tipo · Estado · Nota · Incluir (toggle = checkbox `exclude_i` invertido). Filas `not_found` con fondo `#FBEFEC`, `ambiguous` con fondo `#FBF6E8` y panel de candidatos debajo (radios `candidate_i` como cards 240px, seleccionada con `ring-2 ring-brand-500` vía `has-[:checked]`). `already_in_library` con opacidad .65 y select `duplicate_action_i` en la nota. **Barra fija inferior** `bg-ink`: mascota línea + «Se añadirán **N títulos**. X se ignoran…» (JS que cuenta) + «← Volver a editar» + «Confirmar importación» blanco. Mantener todos los nombres de campo.
- **result.html**: panel azul, número de títulos importados a 160px, «títulos nuevos en tu biblioteca.», desglose, CTAs «Ver mi biblioteca» / «Importar otra», mascota celebrate línea blanca.
- **Móvil**: cada fila como card (póster 40×60, título, línea original mono, selects en grid 1fr 1fr 64px), not_found con `ring-dropped`, barra de confirmación fija abajo.

### 9 · Auth (`accounts/login.html`, `register.html`)
- **Login**: split 5/7. Izquierda `bg-brand-500`: wordmark blanco, mascota línea 300px, «Vuelve a / lo que / estabas / viendo.» 88px, meta «FRIEREN · EP. 18 DE 28 TE ESPERA» (estático o genérico). Derecha papel: «¿Nuevo en Viewy? Crea tu cuenta» arriba-dcha; formulario máx. 420px: eyebrow, «Hola de nuevo.» 56px, Usuario, Contraseña (con «Mostrar»), «Entrar» 52px a ancho completo; pie «Tus datos solo los ves tú.».
- **Registro**: split invertido 7/5. Izquierda con formulario («Empieza tu biblioteca.»; usuario, email, contraseña + repetir en 2 col, medidor de fuerza de 4 segmentos opcional por JS). Derecha `bg-ink` con muro de pósters girado −6° y card papel con mascota happy «¿Traes una lista vieja?».
- `non_field_errors` → alert error con mascota error desaturada.
- **Móvil**: banda azul de 280px arriba con mascota y titular 44px; formulario debajo con inputs de 52px y texto de 16px.
- Renderizar campos a mano con `components/field.html`; clases vía `attrs` en `accounts/forms.py`.

### 10 · Perfil (`accounts/profile.html`)
- Avatar 160px `bg-brand-500` con inicial Bricolage 88px; «MIEMBRO DESDE …» + nombre 128px; «Editar perfil» secundario + «Cerrar sesión» texto a la derecha.
- **Resumen personal** en Bricolage 500 32px, con palabras clave en azul, generado en la vista con plantillas simples a partir de `get_dashboard_stats` (tipo más visto, tipo mejor puntuado, tasa de abandono, `top_studio`). Sin LLM. Bio debajo en muted.
- 4 stats de 72px entre líneas (títulos, terminados, nota media azul, favoritos).
- «Favoritos» 56px: `get_favorites(limit=4)`, el primero a doble ancho (grid 2fr 1fr 1fr 1fr).
- «Actividad reciente»: 5 últimas `UserMedia` por `updated_at` → fecha mono · mini póster · verbo según estado («Terminó», «Empezó», «Añadió», «Abandonó», «Avanzó a ep. N en») · estado con punto. `CONTEXTO NUEVO: recent_activity`. Sin actividad en 14 días → mascota sleep.
- **Móvil**: avatar 84px + nombre 52px en línea, resumen 21px, stats 4 col compactas, favoritos en scroll horizontal, actividad en lista.

### 404 / 500
- `404.html`: papel, «ERROR 404», «Esta escena se cortó en montaje.» 96px, texto, CTAs «Ir a mi biblioteca» / «Buscar»; «404» gigante en `line` de fondo y mascota search con «?».
- `500.html`: **autónomo** (no extiende base.html, CSS mínimo inline o `output.css` directo), fondo `ink`, mascota línea blanca con opacidad .55 + «!», «Se nos ha quemado la palomita.», «Tu biblioteca está a salvo.», «Volver al inicio».

---

## Interacciones y microinteracciones
- Pósters: hover `-translate-y-1` + sombra (200ms ease-out); overlay de metadata con fundido (200ms).
- Botones: `-translate-y-px` + sombra en hover; `scale-[.98]` al pulsar.
- Hero de la home: parallax de 8px en los pósters; mascota con rotación de ±2° al hacer scroll (opcional).
- Contadores: `data-counter` existente. Aparición al hacer scroll: `data-reveal` existente, con retrasos de 40–80ms por elemento.
- Toasts: entran desde abajo (240ms), se cierran a los 4s.
- Todo desactivado con `prefers-reduced-motion`.

## Accesibilidad
- Contraste: texto sobre azul siempre blanco; texto muted `#6B6D73` sobre papel cumple AA para 13px+.
- Zonas táctiles de 44px como mínimo en móvil. Foco visible: `ring-2 ring-brand-500 ring-offset-2`.
- Mascotas decorativas con `alt=""`; con significado (botón Añadir) con `alt`/`aria-label`.

## Archivos en este paquete
- `designs/*.dc.html` — mockups de referencia (abrir en el navegador; requieren `support.js` en la misma carpeta).
  - `Viewy Design System.dc.html` — índice, dirección visual, color, tipografía, espaciado, mascota, navbar 1a/1b, responsive, tokens.
  - `Viewy Home`, `Auth`, `Biblioteca`, `Detalle`, `Analytics`, `Recomendaciones`, `Asistente`, `Importar`, `Perfil`, `Componentes`.
- `designs/assets/` — `mascot.png`, `mascot-line-white.png`, `wordmark-white.png` (se usan tanto en los mockups como en producción).
