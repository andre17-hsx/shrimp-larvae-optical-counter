# Cadena de adquisición — especificación y puesta a punto

**Objetivo:** dejar el hardware y la adquisición en un estado en el que la data de entrada sea **confiable y repetible**, ANTES de escribir el software de conteo.

**Regla del proyecto:** no se escribe el contador hasta que la sección 9 (ensayos de aceptación) pase completa.

---

## 1. Qué hay que dejar fijo (resumen)

| # | Elemento | Estado |
|---|---|---|
| 1 | Cámara + lente (modelo definitivo) | Pendiente de cotización |
| 2 | Distancia de trabajo y enfoque | Se fija tras elegir lente |
| 3 | Potencia y uniformidad de la luz lineal | **Sección 3** |
| 4 | Tasa de línea ↔ velocidad del flujo | **Sección 4** — el parámetro crítico |
| 5 | Estabilidad hidráulica (nivel, lámina, pendiente) | **Sección 5** |
| 6 | Ruta de datos sin pérdida de paquetes | **Sección 6** |
| 7 | Referencias de calibración capturadas | **Sección 7** |
| 8 | Alineación cámara ↔ luz | **Sección 8** |

---

## 2. Cadena óptica

| Parámetro | Valor / criterio |
|---|---|
| Ancho de canal (FOV) | 150 mm (alta resolución) o 300 mm (alto caudal) |
| Resolución objetivo | 0,073 mm/px (2048 px) · 0,037 mm/px (4096 px) |
| Distancia de trabajo | `WD ≈ f × (1 + 1/m)`, con `m = sensor / FOV` |
| Apertura | Abrir lo más posible (la luz es el limitante). Verificar profundidad de campo ≥ espesor de lámina + 10 mm |
| Montaje | Rígido, ajuste fino en 3 ejes; **una vez enfocado, fijar con contratuerca** |

> La profundidad de campo debe cubrir el espesor de lámina (3–6 mm) **más** la variación de altura del agua. En line-scan con magnificación baja esto sobra, pero hay que verificarlo con el lente real.

---

## 3. Iluminación — el punto más subestimado

### Por qué el line-scan necesita tanta luz

El tiempo de exposición por línea es el período de línea. A 13,7 kHz → **73 µs por línea**.

Comparación honesta con el enfoque estroboscópico:

| | Estrobo (Propuesta A) | Line-scan |
|---|---|---|
| Exposición efectiva | ~50 µs | ~73 µs |
| **Ciclo de trabajo del LED** | **0,25 %** | **100 %** |
| Consecuencia | Se puede sobreexcitar el LED 10–20× | El LED va a corriente nominal continua |

Es decir: **la exposición es parecida, pero el estrobo puede "hacer trampa" con pulsos**. La luz lineal debe entregar de forma **continua** lo que el estrobo entrega a ráfagas. Por eso es grande, cara y genera calor.

### Especificación a pedir al proveedor

- **Longitud iluminada** ≥ ancho del canal + 25 % (ej. 200 mm para canal de 150 mm)
- **Tipo:** line light / barra de retroiluminación de alta intensidad, con óptica concentradora
- **Pedir explícitamente:** "recomendada para cámara line-scan de N kHz a X mm de distancia de trabajo"
- **Uniformidad:** ±10 % sobre el FOV (el flat-field corrige el resto)
- **Difusor** integrado (nunca LED desnudo)

### Criterio de aceptación (medible)

> Con exposición = período de línea y **ganancia 1×**, el fondo debe alcanzar **~70 % de la escala completa** (≈180/255 en 8 bits).

- Si no llega → falta luz. Subir ganancia es el último recurso (agrega ruido).
- Si satura (255) → bajar intensidad o cerrar diafragma.

### Palancas si falta luz

1. Abrir diafragma (menor f-number)
2. **Activar "2-line SUM" o TDI** si la cámara lo tiene (×2 a ×4 sin costo de ruido)
3. Luz más potente
4. Bajar la tasa de línea (implica bajar la velocidad del flujo)
5. Ganancia (último recurso)

---

## 4. Sincronía tasa de línea ↔ velocidad

```
tasa_línea = velocidad ÷ resolución
```

Si no coinciden, la imagen sale estirada o comprimida (ver diagrama). **El conteo tolera algo de deformación; la medición de talla no.** Y si comprime demasiado, las larvas se fusionan y se pierde conteo.

### Tres estrategias

| Estrategia | Cómo | Cuándo |
|---|---|---|
| **A · Free-run + velocidad estable** ✅ | Tasa fija; la hidráulica garantiza v constante | **Recomendada** (ver §5) |
| B · Trigger por caudalímetro | Salida de pulsos → entrada de trigger de línea | Si el caudal no se puede estabilizar |
| C · Corrección por software | Medir v y corregir la relación de aspecto | Complemento, no sustituto |

---

## 5. Estabilidad hidráulica — es lo que realmente define la calidad

Esta sección es **más importante que el software**. Si la lámina es inestable, ningún algoritmo compensa.

### 5.1 Rebosadero de nivel constante (recomendación nueva)

**Añadir al cajón de entrada un rebosadero de retorno a altura fija**, ligeramente por encima de la cresta del vertedero:

- La bomba entrega **más caudal del necesario**
- El exceso vuelve al estanque por el rebosadero
- → El nivel del cajón queda **clavado**, sin importar variaciones de la bomba
- → Carga constante sobre el vertedero → **velocidad constante**

Esto convierte un problema electrónico (sincronía) en un problema mecánico resuelto. Con esto, la estrategia A (free-run) es viable y no necesitas encoder.

### 5.2 Posición de la línea de imagen

En un plano inclinado el agua **acelera** hasta alcanzar velocidad terminal (gravedad = fricción).

- **Demasiado cerca del vertedero** → la velocidad todavía cambia → deformación variable
- **Correcto** → ubicar la línea donde el flujo ya se estabilizó
- **Demasiado abajo** → la lámina puede romperse o formar ondas

→ **Hay que determinarlo experimentalmente** midiendo la velocidad a distintas distancias (método §7.4).

### 5.3 Nivelación transversal

El labio del vertedero y el lecho del canal deben estar **perfectamente nivelados en el eje transversal**. Un desnivel lateral hace que la lámina se corra hacia un lado → densidad desigual → sesgo de conteo. Usar los niveladores del bastidor y verificar con nivel de burbuja de precisión.

### 5.4 Checklist hidráulico

- [ ] Rebosadero de nivel constante instalado y funcionando
- [ ] Labio del vertedero nivelado transversalmente (±0,5 mm)
- [ ] Lámina uniforme a todo lo ancho (verificar visualmente y con la imagen)
- [ ] Sin ondas estacionarias ni saltos hidráulicos en la zona de imagen
- [ ] Sin burbujas de aire arrastradas (revisar la entrada de la bomba)

---

## 6. Ruta de datos — cero pérdida de paquetes

**Un paquete perdido = líneas perdidas = huecos en la cinta = conteo erróneo.** No es negociable.

### Configuración

| Ítem | Valor |
|---|---|
| NIC | **Intel** dedicada exclusivamente a la cámara |
| Jumbo frames | **MTU 9000** (en la NIC y en la cámara) |
| Buffers de recepción | Al máximo que permita el driver |
| Tráfico | La NIC de la cámara **sin** otro tráfico (usar 2ª NIC para red/internet) |
| Antivirus / firewall | Excluir la interfaz de la cámara |

### Presupuesto de ancho de banda

| Config | Flujo | vs. límite GigE (~118 MB/s) |
|---|---|---|
| 2048 px @ 13,7 kHz | 28 MB/s | 24 % ✅ |
| 4096 px @ 13,7 kHz | 56 MB/s | 47 % ✅ |
| 4096 px @ 27,5 kHz | 113 MB/s | 96 % ⚠️ al límite |

### Criterio de aceptación

> **0 líneas perdidas en 10 minutos de adquisición continua.**

El SDK expone contadores de paquetes perdidos / buffers incompletos. Registrarlos y verificar que quedan en cero. Si no, revisar jumbo frames, buffers y cableado antes de continuar.

---

## 7. Referencias de calibración a capturar

Estas capturas son **insumo obligatorio del software**. Hay que tomarlas y guardarlas antes de programar.

### 7.1 Referencia oscura (dark)
Lente tapado, luz apagada. Promediar ~1000 líneas → perfil de offset del sensor.

### 7.2 Referencia de fondo (flat-field)
**Con agua fluyendo y sin larvas.** Promediar ~1000 líneas → perfil de ganancia.

> Corrección: `imagen_corregida = (cruda − dark) / (fondo − dark)`
> Esto elimina la falta de uniformidad de la luz, el viñeteo del lente y la suciedad de la ventana. **Es lo que permite usar un umbral global.**
>
> Re-capturar el fondo al inicio de cada jornada y tras cada limpieza.

### 7.3 Calibración espacial (mm/px)
Colocar sobre el canal un objeto de ancho conocido (regla o patrón impreso) que cruce todo el campo.
```
resolución_mm_px = ancho_real_mm ÷ n.º de píxeles que ocupa
```

### 7.4 Verificación de velocidad (autocalibración elegante)
Dejar pasar un objeto flotante de **largo conocido** (ej. marca de 20 mm) y contar cuántas líneas ocupa:

```
velocidad = (largo_real × tasa_línea) ÷ n.º_de_líneas
```

*Ejemplo:* marca de 20 mm que ocupa 273 líneas a 13,7 kHz → v = 20 × 13700 / 273 = **1003 mm/s ≈ 1,0 m/s**

Repetir varias veces para medir la **estabilidad** de la velocidad. Este mismo método sirve para ajustar la tasa de línea hasta que la marca salga con proporción correcta.

---

## 8. Procedimiento de alineación cámara ↔ luz

Es el ajuste mecánico más delicado. Con agua limpia y sin larvas:

1. Montar la luz enfrentada a la cámara, ambas apuntando a la misma franja del canal.
2. Ver el **perfil de línea en vivo** (gráfico de intensidad vs. píxel) que ofrece el SDK.
3. **Mover la luz** (lateral y en ángulo) hasta que el perfil sea **lo más alto y plano posible**. Si la luz está desalineada, el perfil cae en los extremos.
4. **Enfocar:** colocar un borde recto opaco cruzando el canal y ajustar el foco hasta que la transición claro→oscuro ocupe **el menor número de píxeles** posible (idealmente 1–2 px).
5. Verificar que el perfil sea uniforme a lo ancho (±10 %) antes del flat-field.
6. **Fijar todo mecánicamente** (contratuercas / fijador de roscas) y marcar las posiciones.

---

## 9. Ensayos de aceptación — el "gate" antes del software

No se escribe el contador hasta que **todos** pasen.

| # | Ensayo | Criterio |
|---|---|---|
| A | **Enfoque** | Transición de borde en ≤ 2 px |
| B | **Nivel de señal** | Fondo a ~70 % de escala, ganancia 1× |
| C | **Uniformidad** | Tras flat-field, desviación del fondo < 2 % |
| D | **Contraste** | Silueta de larva claramente separada del fondo (histograma bimodal) |
| E | **Integridad de datos** | 0 líneas perdidas en 10 min continuos |
| F | **Geometría** | Objeto conocido con relación de aspecto 1,0 ± 5 % |
| G | **Estabilidad de velocidad** | Repetir F durante 10 min; variación < 5 % |
| H | **Hidráulica** | Checklist §5.4 completo |

**Entregable de esta etapa:** un conjunto de imágenes crudas (bloques) con larvas reales, más las referencias dark y flat-field, y el registro de los ensayos A–H.

Con eso, el software se desarrolla sobre datos reales y verificados — no sobre suposiciones.

---

## 10. Riesgos que esta etapa previene

| Si no se hace… | Consecuencia en el conteo |
|---|---|
| Flat-field no capturado | El umbral falla en los bordes → conteo sesgado |
| Pérdida de paquetes | Huecos en la cinta → larvas perdidas |
| Velocidad inestable | Deformación variable → talla inservible, fusiones |
| Luz insuficiente | Poco contraste → hay que subir ganancia → ruido → falsos positivos |
| Lámina desnivelada | Densidad desigual → sesgo sistemático |
| Foco flojo | Bordes difusos → larvas pequeñas se pierden |
