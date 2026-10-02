# Correlador programable para Tiny Tapeout

ASIC digital en VHDL para buscar patrones cortos en muestras de señales. Calcula un FIR de ocho posiciones usando una unidad compartida de multiplicación y acumulación.

- Muestras con signo de 8 bits; pesos configurables con signo de 4 bits.
- Acumulación exacta de 15 bits, resultado leído como entero con signo de 16 bits.
- Umbral positivo configurable; salida `HIT` inhibida durante las primeras siete muestras.
- Ocho ciclos de cálculo después de aceptar cada muestra; intervalo mínimo de nueve ciclos entre muestras.
- Objetivo inicial: un tile y reloj de 10 MHz. La implementación física determina si se cumplen ambos.

## Empieza aquí

Lee [el diseño explicado paso a paso](docs/diseno.md) y luego [el protocolo de pines](docs/info.md).

El procesamiento está en [src/tt_um_3d2yy_correlator.vhdl](src/tt_um_3d2yy_correlator.vhdl). `info.yaml` selecciona ese archivo y Tiny Tapeout lo convierte automáticamente con GHDL. La extensión `.vhdl` es necesaria para que el flujo lo reconozca. El antiguo archivo de celdas Wokwi no participa en el diseño HDL.

## Verificación local

En Ubuntu, instala `ghdl`, `iverilog`, `yosys`, `make` y los paquetes de `test/requirements.txt`.

```sh
python -m pip install -r test/requirements.txt
bash scripts/build_verilog.sh
make -C test
python scripts/check_results.py test/results.xml
python scripts/demo.py
```

GHDL convierte el VHDL a Verilog y cocotb prueba ese circuito contra un modelo entero independiente. La conversión no crea un segundo diseño mantenido a mano. El flujo de GitHub vuelve a ejecutar la simulación y la síntesis. El flujo GDS del repositorio intenta la implementación física y el precheck.

La demo genera una señal conocida con ruido reproducible y escribe `build/demo.csv`. Verifica la operación del correlador; no demuestra detección de descargas parciales.

## Estado

Primera versión experimental para aprendizaje de arquitectura digital y ASIC. La frecuencia indicada es un objetivo de implementación, no una medición del silicio. Consulta los resultados del flujo GDS y del precheck antes de seleccionar un commit para fabricación.
