# Diseño explicado paso a paso

## 1. El problema que resuelve

Queremos detectar una secuencia corta dentro de una señal digital. En comunicaciones puede representar una marca de sincronización; en instrumentación puede representar una forma de pulso conocida. Este núcleo compara formas mediante una suma de productos. Su funcionamiento se verifica con señales que generamos nosotros.

El correlador no identifica por sí mismo el origen físico de una señal. Una detección significa que una ventana produjo una puntuación mayor o igual al umbral elegido. La amplitud de entrada afecta esa puntuación porque esta versión no normaliza.

## 2. Qué representa una muestra

Una muestra es un número que representa el valor de una señal en un instante. Usamos ocho bits en complemento a dos: valores de -128 a 127. Por ejemplo, +32 se transmite como `0x20` y -32 como `0xE0`. El ADC sería externo; para la primera demo una computadora genera los números.

El reloj del chip y la tasa de muestras son distintos. Esta arquitectura necesita aceptar la muestra y luego realizar ocho operaciones. Con funcionamiento continuo admite como máximo una muestra cada nueve ciclos. Con un reloj objetivo de 10 MHz, el límite del núcleo sería aproximadamente 1.11 millones de muestras por segundo; las lecturas y la velocidad del host pueden reducirlo. No se promete ese rendimiento antes del cierre de temporización.

## 3. La ventana y el patrón

El chip conserva las últimas ocho muestras. Al llegar una nueva, las antiguas se desplazan y la más vieja se descarta. El peso `h[0]` corresponde a la muestra más reciente.

Usaremos este patrón en orden temporal, de antiguo a nuevo:

`[+1,+1,-1,-1,+1,-1,+1,-1]`

Para encontrarlo, los coeficientes en orden de memoria, de nuevo a antiguo, son:

`[-1,+1,-1,+1,-1,-1,+1,+1]`

La inversión del orden es esencial. Enviar `[32,32,-32,-32,32,-32,32,-32]` produce ocho productos positivos de 32 cuando la ventana está completa. Su suma es 256. El umbral inicial es 160. El patrón es una elección didáctica; no se afirma que sea un código de sincronización óptimo.

## 4. Cómo se convierte en hardware

Hay un banco de registros para muestras y otro para coeficientes. Un contador elige una pareja por ciclo. Un multiplicador produce el producto y un acumulador conserva la suma parcial. Después del octavo producto, otro registro conserva el resultado y un comparador determina HIT.

La multiplicación no se ejecuta como una instrucción de Python. La síntesis construye un circuito lógico que recibe los bits de ambas entradas y produce los bits del producto. El reloj determina cuándo los registros capturan los resultados.

Compartir un multiplicador reduce el paralelismo y obliga a esperar. Esa decisión permite estudiar el compromiso entre espacio y velocidad. Una futura versión con varios multiplicadores podría aceptar muestras más rápido, usando más área y potencialmente más energía.

## 5. Precisión y límites

| Elemento | Formato | Rango |
|---|---|---|
| Muestra | Entero con signo, 8 bits | -128 a 127 |
| Coeficiente | Entero con signo, 4 bits | -8 a 7 |
| Producto | Entero con signo, 12 bits | Rango efectivo -1016 a 1024 |
| Acumulador | Entero con signo, 15 bits | Rango efectivo -8128 a 8192 |
| Umbral | Entero sin signo, 14 bits | 0 a 16383 |
| Lectura del resultado | Entero con signo, 16 bits | Extensión de signo del acumulador |

Un acumulador de 14 bits con signo llega hasta +8191: no alcanza para ocho productos de (-128)*(-8), que suman +8192. Esta diferencia de un valor es suficiente para causar un fallo si no se diseña correctamente.

Esta versión usa enteros, sin bits fraccionarios. Las mismas decisiones de representación, ancho de registro y redondeo serán necesarias cuando trabajemos con punto fijo.

## 6. Verificación sin laboratorio

`scripts/demo.py` genera ruido de amplitud pequeña y una secuencia conocida. El modelo independiente calcula la respuesta. Las pruebas cocotb envían números al circuito convertido desde VHDL y comparan cada respuesta con el modelo.

Las pruebas deben mostrar que el circuito hace exactamente lo especificado. No bastaría con observar que se enciende HIT una vez. También comprobamos valores negativos, límites, ventanas incompletas y pausas del control.

Los datos sintéticos sirven para demostrar aritmética y protocolo. Para atribuir rendimiento sobre descargas parciales reales, necesitaríamos datos experimentales y una validación diferente.

## 7. Qué aprenderás de semiconductores

El flujo convierte VHDL en una red de celdas lógicas de una biblioteca CMOS, coloca esas celdas y conecta sus terminales. Inspeccionaremos cuántos registros y puertas aparecen, qué trayectoria limita la velocidad y cómo cambia el área cuando cambiamos la arquitectura.

Para conectar esto con dispositivos, estudiaremos un inversor CMOS, la carga capacitiva de una salida, los retardos y el consumo por conmutación. El flujo digital utiliza transistores ya diseñados dentro de las celdas; comprender sus propiedades requiere estudiar esas celdas, además del VHDL.

## 8. Qué debe pasar antes de fabricar

1. Simulación funcional correcta y reproducible.
2. Síntesis sin latches ni errores estructurales.
3. Implementación física que quepa en el tile declarado y cumpla el reloj objetivo.
4. Precheck correcto y revisión del protocolo, documentación y commit seleccionado.

La rama de trabajo contiene la propuesta. Seleccionar una revisión para fabricación es un paso posterior a estas comprobaciones.
