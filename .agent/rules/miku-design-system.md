---
name: miku-design-system
description: Sistema de diseño único de Miku Desktop Suite (Configuración y Miku-Link). Monocromo sobre negro, verde como único acento, rojo solo para peligro/error, movimiento con resorte y blur de entrada. Úsala SIEMPRE que crees o modifiques UI, componentes, ventanas, animaciones o estilos.
trigger: always_on
---

# Miku Design System

Fuente visual de verdad: `miku-catalogo.html` (abrirlo y leer su código). Si esta regla y el catálogo difieren, gana el catálogo y se corrige la regla.

## 1. Principios
1. **Monocromo.** Negro y grises. Un solo acento: verde. Rojo solo para peligro o error.
2. **Todo reacciona.** Cada control responde a hover, foco, presión y cambio de estado con movimiento.
3. **Movimiento suave.** Resorte para lo físico (tamaño, posición, escala), ease para lo óptico (color, opacidad, blur).
4. **Nada decorativo.** Si un elemento no comunica estado o jerarquía, se quita.
5. **100 % funcional.** Ningún dato, texto de negocio, color o duración hardcodeado en componentes (ver sección 9).

## 2. Color (únicos valores permitidos, definidos como variables)
| Token | Valor | Uso |
|---|---|---|
| `--s0` | `#000` | Fondo base |
| `--s1` | `#0e0f11` | Ventanas, paneles |
| `--s2` | `#17181b` | Menús, toasts, superficies elevadas |
| `--s3` | `#1d1d20` | Indicadores, elementos activos |
| `--ln` | `rgba(255,255,255,.08)` | Líneas y bordes |
| `--ln2` | `rgba(255,255,255,.14)` | Bordes enfatizados |
| `--tx` | `#f5f5f7` | Texto y acción principal |
| `--mu` | `rgba(235,235,245,.45)` | Texto secundario |
| `--ink` | `#0b0b0c` | Texto sobre fondo claro |
| `--ok` / `--okbg` | `#30d158` / `rgba(48,209,88,.12)` | Éxito, confirmación, actividad, conectado |
| `--er` / `--erbg` | `#ff453a` / `rgba(255,69,58,.10)` | Peligro, error, destructivo |

Reglas de acento:
- Verde: confirmar, conectado, en línea, progreso completado, barra de expiración del QR, línea de escaneo. Nunca decorativo.
- Rojo: acciones destructivas (botón de mantener rojo), errores, llamadas perdidas, colgar, zona de peligro. Nunca decorativo.
- **Única excepción de color libre:** el encabezado con partículas (sección 6). Ahí se admite cualquier tono.
- Prohibido: gradientes de color en UI, sombras de color, cualquier otro hex, emojis como íconos.
- Los íconos son SVG de trazo (`stroke: currentColor; stroke-width: 2; round caps/joins`).

## 3. Tipografía y forma
- Fuente **Nunito** pesos 500, 700, 800, **empaquetada localmente** (la app debe funcionar sin internet). Fallback `system-ui`.
- Tamaños: 11 (etiquetas), 12.5 (secundario), 13–14 (cuerpo y controles), 16–18 (títulos de bloque), 20–26 (títulos de sección).
- Radios: botón 11–12, tarjeta 18, ventana 20, chip 13 (píldora), toast 20, teléfono 36.
- Alturas de control: botón 36 (pequeño 30), campo 44, botón de mantener 40, fila de ajuste padding 12 vertical.
- Bordes de 1 px con `--ln`. Sin sombras salvo elementos elevados (menús, ventanas, toasts).

## 4. Movimiento
```css
--spring: linear(0,.17 3%,.52 7%,.86 12%,1.04 17%,1.1 22%,1.07 28%,1.01 36%,.99 46%,1);
--e: cubic-bezier(.2,.8,.2,1);
```
| Situación | Propiedad | Curva y duración |
|---|---|---|
| Escala, posición, tamaño, toggles, indicadores | `scale`, `translate`, `width`, `height` | `--spring` 0.45–0.6 s |
| Color, opacidad, desenfoque | `background`, `color`, `opacity`, `filter` | `--e` 0.15–0.35 s |
| Presionar | `scale: .93–.97` | bajada `.15s --e`, regreso `--spring` |
| Salir | opacidad + blur | `0.2 s --e`, siempre más rápido que entrar |
| Carga | arco continuo con `cubic-bezier(.45,.05,.55,.95)` 1.6 s | nunca saltos |

**Regla de blur de entrada (obligatoria).** Toda ventana, panel, vista, sección, pestaña, aviso o animación de apertura entra de `opacity 0, blur(12px), scale .97, translateY(10px)` a nítido en `.6 s --e`. Sale con `blur(10px)` y `opacity 0` en `.2 s`. Ninguna vista aparece de golpe. Existe una sola utilidad compartida (`enter(el)` / `exit(el)`); no se reimplementa por componente.

Otras reglas:
- Animar solo `transform`/`translate`/`scale`/`opacity`/`filter`. Excepción: tamaños de contenedores que se expanden (acordeón con `grid-template-rows`, ventanas).
- El indicador de segmentados y pestañas se estira hacia el destino (un borde primero, el otro con retraso de 40 ms).
- Listas que cambian (avisos, mensajes) entran con blur y salen colapsando su altura con `grid-template-rows: 1fr → 0fr`.
- `prefers-reduced-motion: reduce` lleva toda duración a ~0 ms y detiene partículas animadas (se dibuja un solo cuadro).
- Foco visible en todo: `outline: 2px solid var(--tx); outline-offset: 2px`.

## 5. Componentes (todos deben existir como componente reutilizable único)
Botones (principal, neutro, confirmar verde, fantasma, destructivo rojo, ícono, inactivo, cargando) · botón de mantener (relleno lineal al mantener, retroceso con resorte al soltar, check dibujado al completar; variantes neutro, blanco, verde, rojo) · segmentado · pestañas · interruptor · casilla · radio · deslizador (relleno blanco; verde opcional) · campo con etiqueta flotante · buscador con limpiar y atajo · selector/menú desplegable · menú contextual · tooltip · chips · insignias · avatares con presencia · barra de progreso (determinada e indeterminada) · anillo de progreso · cargador de arco · cargador de puntos en ola · skeleton · aviso (toast) · alerta en línea (neutra, ok, error) · estado vacío · estado de error con reintento · zona de soltar archivos · grabador de atajos · pasos (stepper) · acordeón · tarjeta con elevación al hover · lista reordenable por arrastre · fila de ajuste · ventana modal · panel lateral · diálogo de confirmación con botón de mantener rojo · encabezado de sección con partículas · emparejamiento con QR · teléfono (maqueta).

Cada componente define y anima: reposo, hover, foco (teclado), presionado, deshabilitado, cargando, error y vacío cuando aplique. Todos accesibles por teclado y con `role`/`aria-*` correctos (`role="switch"`, `aria-pressed`, `aria-expanded`, `aria-live` en avisos).

## 6. Encabezado con partículas (por sección de Configuración)
- Lienzo 2D a DPR hasta 2, con capas de profundidad (3 tamaños), campo de flujo suave, estelas por desvanecimiento, mezcla aditiva (`lighter`), estrellas fugaces cada 3.5–7 s, líneas entre partículas cercanas al cursor y remolino suave alrededor del cursor.
- Fondo: aurora de 3 manchas difuminadas (CSS, `mix-blend-mode: screen`) y un orbe de anillos giratorios; todo teñido por una sola variable `--h`.
- Color por sección: un único mapa `SECTION_HUES` (tono, saturación, luminosidad) en el módulo de tokens. Variación sutil por partícula (±30° con oscilación lenta). El cambio entre secciones interpola el tono por el camino más corto de forma continua.
- Máximo 150 partículas; pausar cuando el encabezado no es visible (IntersectionObserver) o la ventana está oculta; recalcular al redimensionar (ResizeObserver).
- El texto del encabezado (etiqueta «MIKU DESKTOP SUITE», título, descripción) siempre legible: degradado oscuro a la izquierda.

## 7. Ventanas y vistas
- Modal: máx. 420 px, radio 20, fondo `--s1`, borde `--ln2`, velo `rgba(0,0,0,.62)` con `backdrop-filter: blur(8px)`. Cierra con Escape, clic fuera y botón X.
- Panel lateral: entra desde la derecha con resorte.
- Cambio de sección o pestaña: la vista saliente hace `exit` (0.2 s) y la entrante `enter` (0.6 s).
- Avisos: abajo al centro, apilados, entran con resorte + blur, salen colapsando; incluyen barra de tiempo; variantes neutra, ok y error; duración 3 s, pausa al hover.

## 8. Miku-Link dentro de Configuración
Es una sección más de Configuración (no una ventana aparte). Comportamiento tipo Phone Link: estados sin vincular / vinculando / conectado; en conectado, pestañas Inicio, Mensajes, Llamadas, Fotos, Avisos, Apps. El teléfono muestra el fondo real del teléfono o «Sin imagen». El QR es real (ver el prompt de implementación para especificación).

## 9. Prohibido hardcodear (aplica a todo el código de UI)
- Colores, duraciones, curvas, radios, tamaños: solo desde tokens (`tokens.css` / `tokens.ts`). Cero hex o `ms` sueltos dentro de componentes.
- Textos visibles: solo desde el diccionario de i18n (`es`), nunca literales en componentes.
- Datos (mensajes, contactos, llamadas, fotos, notificaciones, batería, modelos, agentes, estados): siempre desde comandos de Tauri, eventos o stores persistentes. Los datos de ejemplo viven solo en pruebas o storybook, nunca en el build.
- Cada control está enlazado a un ajuste real, persistido (`tauri-plugin-store` o el almacén del proyecto) y aplicado en vivo.
- Estados de carga, vacío, error y desconectado reflejan el estado asíncrono real; prohibido simularlos con `setTimeout` o `Math.random()`.
- Temporizadores (p. ej. expiración del QR) se calculan con la marca de tiempo del backend, no con contadores locales inventados.

## 10. Lista de verificación antes de dar algo por terminado
- [ ] Solo colores de la tabla (más el encabezado con partículas).
- [ ] Todo entra con blur y sale rápido; sin vistas que aparezcan de golpe.
- [ ] Resorte y ease usados según la tabla; presionar encoge.
- [ ] Estados hover, foco, presionado, deshabilitado, cargando, error y vacío.
- [ ] Teclado completo y `prefers-reduced-motion` probado.
- [ ] Cero valores hardcodeados (comprobado con búsqueda en el código).
- [ ] Sin emojis, sin sombras de color, sin gradientes de color en UI.

