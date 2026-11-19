# Estaciones conflictivas, causas y efecto en la afluencia

Responde a dos preguntas:

1. ¿Qué líneas y estaciones son más conflictivas y por qué causas? Sirve para dar información a las
   instituciones responsables (STC, SEMOVI, SSC, alcaldías) para planificación y atención.
2. ¿Cómo afecta cada causa a la afluencia? Es la base del sistema de alerta propuesto como trabajo a futuro.

No genera datos nuevos. Combina dos fuentes del repo:

| Fuente | Qué aporta | Alcance |
|---|---|---|
| `master_auditoria_consenso_MAD.csv` | Dónde y cuánto: las 8,575 anomalías CRÍTICAS del detector actual y su desviación en pasajeros | 196 estaciones, 2022 a jul-2026 (población completa) |
| `bitacora_investigacion_anomalias_criticas.csv` | Por qué y cuánto mueve cada causa: OSINT manual | 371 anomalías críticas, muestra proporcional por línea y dirección |

Se corre desde la raíz del repo con `python estaciones_y_causas/estaciones_y_causas.py`. Deja las tablas
en `resultados/` y las gráficas en `img/`.

**Definiciones.** *Pasajeros afectados* es la suma de |afluencia real − afluencia esperada por Prophet|
en los días CRÍTICOS. Cuenta tanto pasajeros de menos (caídas) como de más (alzas), porque las dos
cosas requieren atención. Por línea se divide entre el número de estaciones, para comparar líneas de distinto tamaño.

## 1. Líneas más conflictivas

| Línea | Días críticos | Por estación | Pasajeros afectados por estación | % caídas | Falsas alarmas (OSINT) | Causa principal (OSINT) | Segunda causa |
|---|---|---|---|---|---|---|---|
| 2 | 1,244 | 52 | 547 mil | 63% | 12% | Feriado (22%) | Evento Masivo |
| 9 | 551 | 46 | 445 mil | 55% | 10% | Falla Oculta (35%) | Evento Masivo |
| 3 | 991 | 47 | 434 mil | 69% | 14% | Falla Oculta (17%) | Feriado |
| A | 473 | 47 | 350 mil | 73% | 25% | Feriado (25%) | Falla Oculta |
| 8 | 989 | 52 | 322 mil | 55% | 11% | Feriado (17%) | Evento Masivo |
| 7 | 582 | 42 | 286 mil | 67% | 11% | Feriado (22%) | Evento Masivo |
| B | 950 | 45 | 262 mil | 66% | 16% | Falla Oculta (18%) | Clima Extremo |
| 1 | 691 | 33 | 260 mil | 58% | 3% | Falla Oculta (21%) | Feriado |
| 6 | 526 | 48 | 199 mil | 65% | 33% | Falla Oculta (17%) | Evento Masivo |
| 5 | 547 | 42 | 193 mil | 74% | 38% | Feriado (24%) | Evento Masivo |
| 12 | 564 | 28 | 147 mil | 77% | 39% | Falla Oculta (14%) | Feriado |
| 4 | 467 | 47 | 119 mil | 61% | 50% | Feriado (17%) | Falla Oculta |

Lectura:

- **El número de días críticos por estación casi no distingue líneas.** Todas tienen entre 42 y 52,
  porque el detector marca desviaciones relativas a cada estación. Las excepciones son la Línea 1 (33)
  y la Línea 12 (28), que estuvieron cerradas largos periodos. Lo que sí distingue es el **volumen
  de pasajeros afectados**.
- **Las Líneas 2, 9 y 3 son las más conflictivas.** Concentran más pasajeros afectados por estación
  y tienen pocas falsas alarmas (10% a 14%), así que sus anomalías casi siempre tienen una causa.
  En la 2 dominan feriados y eventos masivos (Centro Histórico). En la 9 dominan las fallas sin
  reporte y los eventos masivos (Ciudad Deportiva, Palacio de los Deportes). En la 3, fallas sin
  reporte, feriados y fallas mecánicas.
- **Las Líneas 4, 12, 5 y 6 son las menos conflictivas.** Tienen menos pasajeros afectados, y entre
  33% y 50% de sus anomalías investigadas resultaron falsas alarmas.
- **"Falla Oculta" es la causa más frecuente en 6 de las 12 líneas.** Significa que la afluencia se
  comportó como en una falla pero no hay reporte oficial. Para las instituciones, esto es un
  hallazgo en sí mismo: hay incidentes que afectan la afluencia y no se registran públicamente.

## 2. Estaciones más conflictivas

Las 15 con más pasajeros afectados, con las causas que encontró la OSINT en cada una
(`resultados/estaciones_conflictivas.csv` tiene las 196):

| Estación | Línea | Días críticos | Pasajeros afectados | % caídas | Causas documentadas (OSINT) |
|---|---|---|---|---|---|
| Zócalo/Tenochtitlan | 2 | 56 | 1.59 M | 93% | Evento Masivo, Feriado |
| Allende | 2 | 94 | 1.54 M | 19% | Efecto Sustitución, Incidente Externo |
| Constitución de 1917 | 8 | 48 | 1.42 M | 65% | Feriado (2) |
| Cuatro Caminos | 2 | 49 | 1.20 M | 84% | Feriado, Falla Oculta |
| Indios Verdes | 3 | 47 | 1.20 M | 81% | sin registros |
| Universidad | 3 | 40 | 1.06 M | 92% | Falla Oculta |
| Tasqueña | 2 | 46 | 0.96 M | 87% | sin registros |
| Copilco | 3 | 45 | 0.88 M | 91% | Falla Mecánica (2), Feriado (2), Falla Oculta, Clima, Falsa Alarma |
| Tacubaya | 9 | 46 | 0.82 M | 80% | Evento Masivo |
| Pino Suárez | 2 | 52 | 0.80 M | 54% | Incidente Externo, Evento Masivo |
| Velódromo | 9 | 39 | 0.69 M | 38% | Falla Oculta |
| Pantitlán | 5 | 45 | 0.69 M | 78% | Falla Oculta, Feriado, Contingencia |
| Buenavista | B | 37 | 0.69 M | 86% | Evento Masivo, Efecto Sustitución |
| Bellas Artes | 2 | 52 | 0.68 M | 50% | Evento Masivo (5), Contingencia |
| Puebla | 9 | 51 | 0.66 M | 45% | Evento Masivo |

Se ven tres perfiles:

- **Centro Histórico (Zócalo, Allende, Pino Suárez, Bellas Artes).** Cuando hay eventos en la plancha
  del Zócalo, la estación Zócalo pierde pasajeros (93% de sus anomalías son caídas) y Allende, la
  alterna, los gana (81% son alzas; la OSINT la registra como Efecto Sustitución). En 13 de los 76
  días con alza crítica en Allende, Zócalo tuvo una caída crítica ese mismo día. La coincidencia
  real es mayor, porque los días en que Zócalo cerró por completo cuentan como cierre y no aparecen
  en la tabla de anomalías.
- **Terminales y estaciones de destino estudiantil (Cuatro Caminos, Indios Verdes, Tasqueña,
  Universidad, Copilco, Constitución de 1917, Pantitlán, Buenavista).** Casi todo son caídas
  (78% a 92%). Su volumen es tan alto que un feriado o un periodo vacacional mueve cientos de miles
  de pasajeros. Que Universidad y Copilco dependan del calendario de la UNAM es una interpretación
  nuestra que no está verificada en la OSINT.
- **Zonas de espectáculos (Velódromo, Puebla, Tacubaya).** Hay más alzas que en el resto, por los
  eventos en Ciudad Deportiva, Foro Sol y Palacio de los Deportes.

Por estación, la OSINT tiene de 0 a 7 registros, así que las causas por estación son indicios y
no un reparto confiable. El reparto confiable es por línea (18 a 51 registros cada una).

## 3. Efecto de cada causa en la afluencia

Cambio típico (mediana) frente a la afluencia esperada, separado según si la causa bajó o subió la
afluencia (`resultados/efecto_por_causa.csv`, gráfica `img/04`):

| Causa | Registros | Baja la afluencia | Cambio típico al bajar | Pasajeros típicos al bajar | Cambio típico al subir | Pasajeros típicos al subir |
|---|---|---|---|---|---|---|
| Cierre Programado | 18 | 83% | −41% | 8,100 | +36% | 5,200 |
| Falla Técnica / Eléctrica | 18 | 83% | −30% | 2,400 | +25% | 4,900 |
| Feriado No Oficial / Cultural | 56 | 80% | −35% | 3,900 | +94% | 4,400 |
| Falla Mecánica | 29 | 76% | −28% | 4,400 | +25% | 2,800 |
| Falla Oculta | 55 | 64% | −32% | 5,300 | +24% | 3,300 |
| Clima Extremo | 33 | 64% | −27% | 3,300 | +32% | 4,900 |
| Incidente Externo | 17 | 59% | −38% | 6,400 | +24% | 4,100 |
| Evento Masivo | 44 | 41% | −34% | 7,900 | +48% | 6,200 |
| Contingencia Ambiental | 10 | 30% | −31% | 2,900 | +56% | 3,700 |
| Efecto Sustitución | 10 | 30% | −30% | 6,800 | +52% | 3,800 |
| Evento Cívico / Jornada Electoral | 3 | 0% | n/a | n/a | +76% | 2,600 |
| *Falsa Alarma (referencia)* | 74 | 72% | −31% | 2,400 | +35% | 2,300 |

Lectura:

- **Lo que distingue a las causas es la dirección, no la magnitud.**
  - Cierres, fallas y feriados bajan la afluencia 4 de cada 5 veces.
  - Eventos masivos, contingencias ambientales, sustitución y jornadas electorales la suben en la
    mayoría de los casos.
  - En magnitud, casi todas mueven la afluencia entre 25% y 40%, igual que las falsas alarmas.
- **Las que más pasajeros mueven por evento** son los cierres programados (unos 8,100 pasajeros
  menos), los eventos masivos (6,000 a 8,000 de más o de menos, según si cierran la estación o
  atraen gente) y los incidentes externos (6,400 menos).
- **Un evento masivo puede bajar la afluencia de una estación y subir la de la vecina.** Es el
  patrón Zócalo–Allende. Por eso el efecto conviene medirlo por zona y no solo por estación.

**Por qué no se usa la OSINT de 2026.** En los días en alerta de 2026, Prophet sobreestimó la
afluencia en cerca de 20% (ver `validacion_predicciones/ANALISIS.md`). Con ese sesgo, todas las
causas salen negativas, así que no sirve para medir el efecto de cada una.

## 4. Causas cíclicas, programadas y esporádicas

Para la prevención importa si una causa se puede anticipar. Las causas se agrupan en tres tipos
(`resultados/causas_ciclicas_programadas_esporadicas.csv`, gráfica `img/05`):

| Tipo | Causas | % de la OSINT | Cómo se atiende |
|---|---|---|---|
| **Cíclica** | Feriados y vacaciones, clima (temporada de lluvias), contingencias ambientales | 27% | Se repiten con el calendario: se pueden prevenir cada año |
| **Programada** | Eventos masivos, cierres programados, jornadas electorales | 18% | No son cíclicas pero se anuncian antes: se pueden prevenir si hay coordinación |
| **Esporádica** | Fallas mecánicas, técnicas y ocultas, incidentes externos, sustitución | 35% | Imprevistas: requieren detección y respuesta rápida |
| Falsa alarma | | 20% | |

La ciclicidad se ve en los datos:

- **En la OSINT.** El clima concentra 64% de sus registros en julio a septiembre. Las contingencias
  concentran 80% en diciembre, abril y enero. Los feriados concentran 59% en marzo a mayo (Semana Santa).
- **En el detector.** 24% de los días críticos se repiten en la misma estación y la misma fecha en
  al menos dos años. Es un piso, porque las fechas móviles como Semana Santa no cuentan.
  - Las fechas que más se repiten son 2-nov, 24-dic, 1-ene, 31-dic, 10-may (Día de las Madres),
    25-dic, 1-nov, 8-mar y 1-may (`resultados/fechas_recurrentes.csv`).
  - El 8-mar tiene días críticos los cinco años (2022 a 2026), repartidos en 22 estaciones. Coincide con la marcha del 8M: un evento masivo
    que además es cíclico.
  - Una fecha única como el 11-jun-2026 (inauguración del Mundial, 153 estaciones) no cuenta como recurrente.
- **Por línea.** Casi la mitad de las anomalías de la red (45%) tienen causa cíclica o programada,
  es decir, prevenible. La Línea 9 es la excepción, con 60% esporádicas, sobre todo fallas sin reporte.

Las fallas mecánicas y ocultas se concentran de noviembre a febrero. Puede ser desgaste real o puede
ser que parte de lo que se registró como "falla oculta" sea efecto del periodo vacacional. Vale la
pena revisarlo antes de llamarlas esporádicas sin matiz.

Propuesta de orden para el trabajo a futuro: empezar por las cíclicas (calendario fijo, efecto
conocido por estación), seguir con las programadas (requieren un catálogo de eventos) y dejar las
esporádicas para la fase de detección en tiempo real.

## ¿Y las anomalías que solo detecta MAD?

El análisis usa solo las CRÍTICAS (Prophet y MAD de acuerdo). Las de solo MAD (49,742) se dejaron
fuera por tres razones:

- **Desviaciones chicas.** Su desviación típica frente a Prophet es de 8%, dentro de la banda
  esperada, contra 37% en las CRÍTICAS.
- **z robusto inflado.** En 18% de ellas el z robusto pasa de 10,000. Eso pasa porque la MAD de
  esas semanas fue casi cero, no porque la desviación sea grande.
- **No cambian el resultado.** Sumarlas al ranking de estaciones da casi el mismo orden
  (correlación de 0.98; 13 de las 15 estaciones principales se repiten).

Sirven como señal temprana o de contexto, pero no para medir conflictividad.

## Límites

- **Solo días con anomalía.** El efecto se mide en días que el detector marcó como críticos, así que
  responde "cuánto se movió la afluencia cuando la causa sí produjo una anomalía". No es el efecto
  promedio de la causa. Muchos eventos masivos o lluvias no generan anomalía y no entran aquí. Por
  eso la magnitud se parece a la de las falsas alarmas: el detector solo deja pasar desviaciones grandes.
- **La OSINT histórica es de una versión anterior del detector.** De sus 371 registros, 103 siguen
  siendo CRÍTICA con el detector actual, 119 quedaron como ALTA o MEDIA y 149 ya no son anomalía.
  El efecto por causa usa la afluencia esperada de esa versión.
- **Muestra chica por estación.** Las causas por estación son indicios. Para afirmarlas se necesita
  investigar más días en las estaciones de la lista.
- **Pasajeros afectados no es pasajeros únicos.** Es la suma de desviaciones diarias contra lo esperado.

## Trabajo a futuro: sistema de alerta y gestión de la demanda

La idea es la misma que la de los sistemas de tránsito que detectan un vehículo mal estacionado,
estiman cuánto afecta la circulación y actúan antes de que se forme el embudo (aviso al conductor o
multa). Aplicada al Metro sería un ciclo de cuatro pasos:

1. **Detectar la causa antes o al inicio.** Primero las cíclicas y programadas (sección 4), que se
   conocen con días de anticipación; después las esporádicas. Integrar fuentes en tiempo real y clasificar cada hecho
   con el catálogo de causas de este trabajo:
   - Agenda de eventos masivos y marchas.
   - Alertas del C5 y la SSC.
   - Avisos de @MetroCDMX.
   - Pronóstico del SMN y Protección Civil (lluvia).
   - Contingencias de la CAMe.
   - Calendario de feriados y vacaciones escolares.
2. **Estimar el efecto.** Combinar el pronóstico de Prophet de ese día con la tabla de efecto por
   causa y estación. La tabla dice la dirección y una magnitud típica, por ejemplo: evento en el
   Zócalo, −35% en Zócalo y +50% en Allende. Con eso se obtiene la afluencia esperada ajustada y las
   estaciones que absorberán la demanda.
3. **Actuar.**
   - Usuarios: mensajes en la app, pantallas y redes con la estación alterna y la hora recomendada.
   - Operación: refuerzo de trenes y personal, control de accesos y coordinación con Metrobús y RTP.
   - Organizadores de eventos masivos: aviso obligatorio y plan de movilidad. El equivalente a la
     multa sería una sanción o condición en el permiso cuando el evento no se coordina con el STC.
4. **Medir y aprender.** Comparar la afluencia real con la esperada ajustada y actualizar la tabla
   de efectos. Así el sistema mejora con cada evento.

Para pasar de este prototipo a un sistema real hacen falta:

- **Afluencia por hora y en tiempo casi real.** SEMOVI publica totales diarios con meses de retraso.
- **Registro oficial de incidentes del STC**, que eliminaría la categoría "Falla Oculta".
- **Catálogo de eventos geolocalizado con fecha y aforo.**
- **Días con evento y sin anomalía**, para estimar el efecto promedio de cada causa y no solo el de
  los días extremos. Lo ideal es un diseño de comparación (días con y sin evento en la misma
  estación y temporada).
 Integrar fuentes en tiempo real y clasificar cada hecho
   con el catálogo de causas de este trabajo:
   - Agenda de eventos masivos y marchas.
   - Alertas del C5 y la SSC.
   - Avisos de @MetroCDMX.
   - Pronóstico del SMN y Protección Civil (lluvia).
   - Contingencias de la CAMe.
   - Calendario de feriados y vacaciones escolares.
2. **Estimar el efecto.** Combinar el pronóstico de Prophet de ese día con la tabla de efecto por
   causa y estación. La tabla dice la dirección y una magnitud típica, por ejemplo: evento en el
   Zócalo, −35% en Zócalo y +50% en Allende. Con eso se obtiene la afluencia esperada ajustada y las
   estaciones que absorberán la demanda.
3. **Actuar.**
   - Usuarios: mensajes en la app, pantallas y redes con la estación alterna y la hora recomendada.
   - Operación: refuerzo de trenes y personal, control de accesos y coordinación con Metrobús y RTP.
   - Organizadores de eventos masivos: aviso obligatorio y plan de movilidad. El equivalente a la
     multa sería una sanción o condición en el permiso cuando el evento no se coordina con el STC.
4. **Medir y aprender.** Comparar la afluencia real con la esperada ajustada y actualizar la tabla
   de efectos. Así el sistema mejora con cada evento.

Para pasar de este prototipo a un sistema real hacen falta:

- **Afluencia por hora y en tiempo casi real.** SEMOVI publica totales diarios con meses de retraso.
- **Registro oficial de incidentes del STC**, que eliminaría la categoría "Falla Oculta".
- **Catálogo de eventos geolocalizado con fecha y aforo.**
- **Días con evento y sin anomalía**, para estimar el efecto promedio de cada causa y no solo el de
  los días extremos. Lo ideal es un diseño de comparación (días con y sin evento en la misma
  estación y temporada).
