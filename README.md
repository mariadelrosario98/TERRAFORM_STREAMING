Resumen del Análisis de Datos en Streaming
==========================================

Introducción: El Problema de los Logs
-------------------------------------

Estamos trabajando con un sistema que gestiona **logs de microservicios** generados como eventos JSON. La información clave es el **nombre del servicio**, la **marca de tiempo** (timestamp) y un **mensaje**. El estándar crucial es la **detección de errores**, identificada por la cadena "HTTP Status Code: XXX" donde XXX **no es** 200.

🎯 Task 1 & 2: Estadísticas a lo Largo del Tiempo
-------------------------------------------------

Estas tareas se centran en cómo calcular métricas sobre un conjunto de datos que nunca se detiene (ever growing dataset).

### Task 1: Promedios Móviles (_Running Averages_)

**Concepto ClaveInsight PrincipalCálculo Simple**La forma más sencilla de calcular estadísticas sobre un _stream_ sin límite.**Fórmula (Estado)**Se basa en el principio de **mantener dos contadores** en memoria de forma persistente: la **suma acumulada** ($\\sum x\_i$) y el **conteo total** ($n$).**Objetivo**Implementar un algoritmo que calcule el **promedio de peticiones exitosas por servicio** hasta el momento actual ($t$).**Limitación**Es una estadística **global** que nunca olvida el pasado, por lo que los datos muy viejos tienen el mismo peso que los datos recientes.

### Task 2: Ventanas Deslizantes (_Sliding Windows_)

**Concepto ClaveInsight PrincipalCálculo Temporal**Permite obtener estadísticas relevantes sobre un **período fijo de tiempo** (ej., los últimos 60 segundos).**Mecanismo (Poda)**Se requiere un algoritmo de **poda (**_**pruning**_**)** que haga dos cosas en cada paso: **1.** Ingresar nuevos registros y **2.** **Eliminar de la memoria** los registros que han quedado fuera de la ventana.**Ventaja**La memoria consumida está **limitada por el tamaño de la ventana** (ej. 1 minuto), no por el tamaño total del _dataset_.**Objetivo**Implementar un algoritmo para calcular el **promedio de peticiones fallidas** en la **última minute**.

🎲 Task 3 & 4: Muestreo y Filtrado Eficiente
--------------------------------------------

Estas tareas abordan la dificultad de tomar decisiones sobre datos sin tener el conjunto completo disponible o sin gastar demasiada memoria.

### Task 3: Muestreo (_Sampling_) y _Reservoir Sampling_

**Concepto ClaveInsight PrincipalMuestreo Justo**Cuando trabajas con un _stream_ infinito, no puedes esperar a que terminen los datos para tomar una muestra representativa.**Reservoir Sampling**Este algoritmo garantiza que cada elemento del _stream_ (pasado y presente) tenga la **misma probabilidad** de ser seleccionado para la muestra final, sin conocer el tamaño total del _stream_ ($N$) de antemano.**Objetivo**Utilizar _Reservoir Sampling_ para determinar el **código de estado HTTP más común** en todo el conjunto de datos.

### Task 4: Filtrado y _Bloom Filter_

**Concepto ClaveInsight PrincipalFiltrado Rápido**Necesitamos decidir si un mensaje entrante (en el _stream_) es de interés _sin_ tener que cargar una lista gigante de mensajes deseados en la memoria.**Bloom Filter**Una estructura de datos **probabilística** y **altamente eficiente en memoria** para determinar si un elemento **probablemente pertenece** a un conjunto o **definitivamente no pertenece** a él.**Objetivo**Usar el _Bloom Filter_ para determinar si un mensaje debe ser reenviado a otro sistema, basado en una lista de mensajes de interés que **es demasiado grande para caber en memoria**.

📈 Task 5 & 6: Frameworks de _Big Data_
---------------------------------------

Estas tareas abordan cómo los _frameworks_ modernos de _Big Data_ resuelven los problemas de las Tareas 1 y 2 de forma nativa y a gran escala.

### Task 5: Polars Streaming (Procesamiento en una Sola Máquina)

**Concepto ClaveInsight PrincipalMotor LazyFrame**Polars utiliza el **LazyFrame** para definir un plan de ejecución **sin cargar los datos**.**Modo Streaming**Al ejecutar con **.collect(streaming=True)**, Polars procesa archivos grandes en **lotes (**_**chunks**_**)** y libera la memoria de los grupos terminados.**Estadísticas Clave**Ideal para métricas de una sola máquina con **uso limitado de memoria**, como: **Tasa de Fallos por Servicio** (group\_by("service").agg(pl.mean())) o **Media Móvil** (rolling\_mean()).

### Task 6: Spark Streaming (Procesamiento Distribuido)

**Concepto ClaveInsight PrincipalEstructura Distribuida**Spark utiliza **Structured Streaming** sobre un clúster de máquinas (varios nodos de EC2, por ejemplo) para escalar el procesamiento de _streaming_ horizontalmente.**Operaciones con Estado**Maneja el estado de la ventana o la agregación **distribuyéndolo** entre los nodos del clúster.**Estadísticas Clave**Utilizado para los mismos tipos de métricas (ventanas, agregaciones), pero diseñado para volúmenes de datos que **superan la capacidad de una sola máquina**.