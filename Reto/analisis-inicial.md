# Análisis inicial

## Desglose de historias

| Historia                                                     | ¿Qué está pasando?                                           | ¿Qué decisión queremos entender?                             | ¿Qué cosas podrían explicarla?                               |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Elegir siempre al transportista más barato puede terminar saliendo más caro si tarda mucho en aceptar el viaje o provoca que este se cicle. | - Los transportistas no se ven atraídos por ofertas muy bajas<br />- No resulta rentable el costo de transporte (en tiempo y dinero) para las compañías y trabajadores<br />- Reconocen la inviabilidad y esperan a que otros lo rechacen en búsqueda de una mejora de precio | No es ideal construir una solución que solo considere el precio como un bien a maximizar. Al ser un problema de la vida real, se deben de considerar factores externos y difíciles de cuantificar como la satisfacción de los transportistas o el balance de intereses entre ambas partes. | - ¿Qué hace una ruta más atractiva incluso a un precio bajo?<br />- ¿Cuál es el menor precio al que se puede ofertar un viaje sin afectar la tasa de aceptación? |
| Un transportista puede parecer lento o poco eficiente no porque lo sea realmente, sino porque recibe rutas menos atractivas o más difíciles de asignar. | - Un transportista parece arrojar resultados poco óptimos (más caros o mayor tardanza en entrega) pero puede ser inherente al tipo de ruta<br />- Al pertenecer a una categoría más baja (precios más altos), la oferta de viajes que recibe es más limitada, lo que no la hace una opción inicial de elección<br />- La elección de ciertas rutas puede “arruinar” este promedio, pero puede que sea viable y una mejor opción para rutas en concreto y menos para otras | No se puede categorizar a un transportista como malo o bueno, pues esta categoría se da en función de múltiples factores como la ruta (la distancia de esta, problemas de seguridad, entre otros). No es un problema de blanco y negro, sino de escalas. | - ¿Se debe de dividir la solución por rutas?<br />- ¿Es posible que se consideren factores como los mencionados a la hora de construir una solución para abarcar la mayor cantidad de escenarios? |
| Los transportistas juegan un juego, observan a Ternium, y si siempre les mandan las rutas “malas” dejan de contestar; mantener transportistas aparentemente ineficientes puede ser lo óptimo a dos años. | - Los transportistas deben de velar también por sus intereses, por lo que se debe de considerar un balance entre los intereses de Ternium y los de terceros<br />- Una mala relación con transportistas se traduce en poco interés en los viajes y pérdidas de ciertos beneficios de lealtad<br />- Existe el antecedente de la red de transportistas operando bajo esquemas informales que quebrantan las políticas de Ternium y afectan las operaciones.<br />- La ineficiencia de los transportistas puede comprometer las operaciones a corto plazo y afectar las relaciones con clientes | Si bien se busca optimizar las operaciones de transporte de la empresa, no se debe optar por una solución que reduzca costos sin considerar las consecuencias que pueda tener a nivel relación entre transportistas y la empresa. | - ¿Cómo minimizar los costos de transporte sin minimizar la satisfacción de las empresas y trabajadores transportistas sin sacrificar la satisfacción de los clientes finales?<br />- ¿Los rechazos son simplemente una respuesta a una oferta poco atractiva, o los transportistas están aprendiendo el comportamiento de Ternium y esperando mejores condiciones? |

## Relaciones encontradas

Historia 1:

* Si el precio ofertado y el atractivo de la ruta son bajos, entonces aumenta la probabilidad de rechazo cuando no hay un incentivo adicional para que los transportistas tomen ese viaje

* Si el precio ofertado es relativamente alto y el atractivo de la ruta e bajo, aumenta la probabilidad de aceptación dado que los transportistas se ven incentivados por el precio. 
* Teoría de juegos

Historia 2:

* Si se ofertan viajes complejos (tiempo y distancia), entonces aumenta la probabilidad de rechazo por las primeras capas de transportistas cuando la ruta no tiene una alternativa de retorno atractiva.
* Si los viajes complejos son rechazados por las primeras capas de transportistas, entonces aumenta la probabilidad de que estos sean aceptados por transportistas caros, lo que los mantiene en el estatus “caro y última categoría”, pues solo reciben rutas complejas.
* Si se espera un tiempo de aceptación bajo, entonces se debe de buscar primero en los mejores candidatos en función de las características de la ruta para evitar excluir a transportistas con buenos precios para esta.

Historia 3:

* Si los transportistas están aprendiendo el comportamiento de Ternium, entonces los rechazos son la respuesta a una oferta poco atractiva cuando los transportistas esperan mejores condiciones
* Si la satisfacción de los transportistas es baja, entonces la tasa de rechazos aumenta cuando saben que no se ofertará el viaje a un precio que balancee el costo neto del viaje y su tiempo

## Hipótesis iniciales

### Hipótesis 1 — Interacción

> **El efecto del precio ofertado sobre la probabilidad de aceptación depende del atractivo de la ruta**
> **Una oferta de menor precio tendrá un efecto negativo mayor sobre la aceptación cuando la ruta sea poco atractiva que cuando sea atractiva.**

**¿Qué tendría que observar para creerla?**

Al comparar viajes similares, la relación entre precio y aceptación cambie dependiendo del atractivo de la ruta.

**Espejo peligroso**

Mezcla con otras variables. Las rutas poco atractivas también podrían ser más largas, más peligrosas, tener peores tiempos de retorno o concentrarse en determinados destinos.

**¿Cómo lo detectaríamos?**

Comparando rutas bajo características similares y controlando variables como distancia, origen/destino, duración, horario, etc., según los datos disponibles.

**Si fuera cierta:**

> Ternium debería dejar de utilizar un precio único como criterio principal y ajustar la oferta considerando el atractivo de la ruta.

### Hipótesis 2

> **Cuando una oferta es poco atractiva por las características de la ruta, aumentar el precio puede incrementar la aceptación, pero no necesariamente compensar el costo generado por los rechazos y las sucesivas reasignaciones.**

**¿Qué tendría que observar?**

Que ofertas con mayor precio tengan mayor aceptación, pero que el costo total esperado del viaje no mejore necesariamente cuando se consideran otros costos asociados.

**Espejo peligroso**

Que los viajes a los que Ternium ofrece precios más altos sean precisamente los viajes que ya tienen mayor dificultad. Ternium solo está pagando más precisamente en los casos más difíciles.

El aumento de precio no sea la causa de la aceptación, sino que coincida con una temporada, ruta o tipo de transportista particular.

**Si fuera cierta:**

> Ternium debería optimizar el costo total hasta conseguir un viaje aceptado, no únicamente el precio inicial de la oferta.

### Hipótesis 3 — Contraintuitiva

> **Parte de la menor eficiencia de los transportistas de mayor costo se explica por la dificultad de las rutas que reciben, por lo que su desempeño relativo mejora cuando se compara a los transportistas bajo rutas de características similares.**

**¿Qué tendría que observar?**

1. Los transportistas caros reciben proporcionalmente más viajes complejos.
2. Presentan peores indicadores.
3. Cuando se controla/compara por características de las rutas, la diferencia de desempeño se reduce significativamente.

**Espejo peligroso**

Las rutas difíciles efectivamente explican parte del peor desempeño. Pero podría seguir existiendo una diferencia real entre transportistas.

Ternium asigna determinadas rutas a ciertos transportistas precisamente porque históricamente tienen peor desempeño o porque son la última alternativa disponible. Entonces la asignación de rutas no sería una causa independiente del problema; estaría relacionada con el desempeño previo.

**Si fuera cierta:**

> Ternium debería evaluar a los transportistas considerando la dificultad y el tipo de rutas que reciben, en lugar de compararlos únicamente por sus promedios globales.

### Hipótesis 4

> **Para determinados tipos de viajes, la probabilidad de aceptación depende más de la compatibilidad entre las características del viaje y las características del transportista que de la posición general del transportista en la jerarquía de costos.**

> ¿Realmente el ranking general de transportistas es menos informativo que el matching viaje–transportista?

**¿Qué tendría que observar?**

Que un transportista que no está entre los primeros candidatos por precio tenga una probabilidad de aceptación particularmente alta para ciertos tipos de viajes, mientras que otro transportista aparentemente mejor posicionado tenga una probabilidad baja.

```text
"mejor transportista en general"
        ≠
"mejor transportista para este viaje"
```

**Espejo peligroso**

El modelo puede encontrar esa relación simplemente porque está copiando la política de asignación actual. Ternium ya manda cierto tipo de viajes a ciertos transportistas, por ende el modelo aprende:  “Este transportista funciona para esta ruta.”

Solo observamos el desempeño de los transportistas a los que Ternium decidió ofrecerles el viaje.

**Si fuera cierta:**

> Ternium debería evaluar candidatos según la compatibilidad viaje–transportista antes que aplicar un ranking general basado únicamente en costo.

------

### Hipótesis 5 — Interacción estratégica

> **El comportamiento de aceptación de un transportista en una nueva oferta depende de sus experiencias previas con Ternium, de manera que una secuencia repetida de ofertas poco atractivas se asocia con una menor probabilidad de aceptación o una mayor demora en responder a ofertas posteriores.**

```text
calidad de ofertas previas × nueva oferta → aceptación actual
```

**¿Qué tendría que observar?**

- Transportistas que históricamente reciben/rechazan ciertas ofertas.
- Cambios posteriores en su tasa de aceptación.
- Cambios en su tiempo de respuesta.
- Diferencias entre transportistas con experiencias previas distintas ante ofertas similares.

**Espejo peligroso**

Los transportistas con muchos rechazos anteriores simplemente reciben viajes más difíciles posteriormente. No es “rechazó antes → ahora rechaza más”, en realidad es “recibe viajes difíciles → rechaza más”.

**Si fuera cierta:**

> Ternium debería considerar el historial de interacción con cada transportista al diseñar futuras ofertas, en lugar de tratar cada oferta como una decisión independiente.
