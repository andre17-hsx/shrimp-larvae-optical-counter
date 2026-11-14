# FASE 0 — Banco hidráulico: protocolo de validación

**Premisa:** el canal, el cajón, el vertedero y la bomba son **idénticos** para el enfoque estroboscópico y para line-scan. Validar la hidráulica primero no es trabajo perdido en ningún escenario, y es lo que determina qué cámara es viable.

**Regla:** no se compra la cámara hasta que esta fase pase los criterios de la sección 4.

---

## 1. Qué construir (versión mínima)

| Elemento | Especificación mínima |
|---|---|
| Tanque / estanque de prueba | Recipiente de ~100–200 L |
| Bomba | **Bajo cizallamiento** (air-lift o similar). Es la variable a validar |
| Cajón de entrada | ~270 × 430 × 240 mm, con tabiques enderezadores |
| **Rebosadero de retorno** | A altura fija → mantiene el nivel constante |
| Vertedero | Labio nivelado a todo el ancho, **enrasado** con el canal |
| Canal inclinado | Acrílico transparente, ancho 150 mm, pendiente **ajustable** 25–45° |
| Colector | Recipiente simple con retorno al tanque |

> **Haz la pendiente ajustable.** Es la variable que más vas a mover durante los ensayos.

**No se necesita:** cámara, luz lineal, PC industrial, capó. Nada de eso todavía.

---

## 2. Instrumentación (todo de bajo costo)

| Medición | Método |
|---|---|
| **Velocidad** | Celular grabando a **120–240 fps** un flotador sobre una distancia marcada → `v = d / t` |
| **Caudal (Q)** | Balde graduado + cronómetro en la salida |
| **Espesor de lámina (h)** | Directo con calibrador/varilla, y verificación cruzada: `h = Q ÷ (ancho × v)` |
| **Régimen de flujo** | Observación + video en cámara lenta (buscar ondas, saltos, zonas secas) |
| **Uniformidad transversal** | Trazas de colorante en varios puntos del ancho |
| **Nivel del cajón** | Regla fija pegada a la pared del cajón |
| **Supervivencia** | Conteo manual antes/después + evaluación de condición |

> La verificación cruzada `h = Q/(w·v)` es importante: si el valor calculado y el medido no coinciden, alguna medición está mal.

---

## 3. Ensayos a realizar

### 3.1 Barrido de pendiente y caudal (sin larvas)
Para cada combinación de pendiente (25°, 30°, 35°, 40°) y 3 caudales:
- Medir v, h, Q
- Anotar dónde se estabiliza el flujo a lo largo del plano
- Anotar si aparecen ondas, saltos hidráulicos o zonas secas

**Salida:** tabla que relaciona pendiente + caudal → velocidad y espesor. Con eso eliges el punto de operación.

### 3.2 Estabilidad temporal (sin larvas)
En el punto de operación elegido, medir la velocidad **cada 2 minutos durante 30 minutos**.
- ¿Se mantiene? ¿Deriva al bajar el nivel del tanque?
- Probar **con y sin** el rebosadero de retorno para cuantificar cuánto ayuda.

**Este es el ensayo que decide la cámara.**

### 3.3 Uniformidad transversal
Inyectar colorante en 3 puntos del ancho y verificar que las trazas bajen **paralelas y a la misma velocidad**. Si una se adelanta, hay desnivel lateral.

### 3.4 Aire y burbujas
Observar si la bomba arrastra aire. Las burbujas en la lámina **arruinan la imagen** (se ven como objetos). Si aparecen: bajar la entrada de succión, añadir cámara de calma, reducir turbulencia en la entrada.

### 3.5 Prueba biológica (la más importante)
Pasar un **lote contado** de postlarvas vivas por el sistema completo.

Medir:
- **Supervivencia** (contar a la salida, y a las 24 h para mortalidad diferida)
- **Condición** (observar bajo lupa: antenas rotas, daño físico)
- **Distribución**: ¿se separan o forman grumos?
- **Orientación**: ¿se alinean con el flujo? (afecta mucho la densidad máxima)
- **Densidad máxima**: aumentar la carga hasta que empiecen a tocarse

### 3.6 Ensayo de densidad (define el caudal máximo)
Pasar lotes de densidad creciente y observar (a ojo o con el celular) a partir de qué densidad las larvas empiezan a solaparse. Este número es **el límite real de tu sistema**, más importante que cualquier spec de cámara.

---

## 4. Criterios de aceptación

| # | Criterio | Meta |
|---|---|---|
| A | Espesor de lámina | **3–6 mm**, variación < ±1 mm a lo ancho |
| B | Cobertura transversal | Lámina presente en **≥ 90 %** del ancho, sin franjas secas |
| C | Régimen | **Sin ondas estacionarias ni saltos** en la zona de imagen prevista |
| D | Burbujas | **Ninguna** visible en la lámina |
| E | **Estabilidad de velocidad** | **±5 % en 30 min** ← *el criterio decisivo* |
| F | Nivel del cajón | Constante con el rebosadero activo |
| G | **Supervivencia de larvas** | **> 99 %** (inmediata y a 24 h) |
| H | Distribución | Larvas separadas, sin grumos, a la densidad objetivo |

---

## 5. Cómo el resultado decide la cámara

| Resultado del ensayo 3.2 | Implicación |
|---|---|
| **Velocidad estable ±5 %** | **Line-scan viable en free-run**, sin encoder. Se puede usar su máxima resolución. Confirma la decisión con datos. |
| **Velocidad varía > 10 %** | Line-scan se deforma → necesitará caudalímetro/encoder (más costo y complejidad). El **estrobo + tracking** lo absorbe sin problema. Tendrás argumento técnico sólido. |

| Resultado del ensayo 3.6 | Implicación |
|---|---|
| Densidad alcanzable **alta** | Justifica line-scan (su resolución y throughput se aprovechan) |
| Densidad alcanzable **baja** | El caudal lo limita la hidráulica, no la cámara → una cámara más barata basta |

| Resultado del ensayo 3.5 | Implicación |
|---|---|
| **Mortalidad > 1 %** | 🚩 **Parar.** Hay que cambiar la bomba o pasar a alimentación por gravedad/sifón antes de seguir con cualquier cámara |

---

## 6. Por qué esta fase es la de mayor retorno

| Riesgo que elimina | Costo si se descubre después |
|---|---|
| La bomba daña las larvas | Rediseño hidráulico completo |
| No se logra lámina fina y uniforme | Todo el diseño óptico queda inválido |
| La velocidad es inestable | Cámara equivocada comprada (~$1500+) |
| Las larvas se amontonan | El caudal real es una fracción del proyectado |
| Burbujas en la lámina | Falsos positivos permanentes en el conteo |

**Costo de esta fase:** unos cientos de dólares en acrílico, PVC, bomba y accesorios.
**Costo de equivocarse en la cámara:** más de $1500, más el tiempo perdido.

---

## 7. Entregable de la Fase 0

1. Tabla pendiente × caudal → velocidad y espesor
2. Gráfico de estabilidad de velocidad (30 min)
3. Resultado de supervivencia (inmediata y a 24 h)
4. Densidad máxima antes de solapamiento
5. **Recomendación de cámara respaldada con datos medidos**
6. Videos de referencia del flujo (útiles para mostrar a la gerencia)

Con esto, la elección de cámara deja de ser una opinión y pasa a ser una conclusión.
