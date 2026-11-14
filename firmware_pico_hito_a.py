# firmware_pico_hito_a.py
# Hito A — generador de pulsos para el flash IR estroboscopico (sin trigger de camara)
# Placa: Raspberry Pi Pico (MicroPython)
# Conexion: GP15 -> Rg(47R) -> gate del MOSFET (Q1). GND del Pico -> GND comun.
#
# Cargar con Thonny (interprete MicroPython / Raspberry Pi Pico).
# El pin arranca en LOW: el LED queda APAGADO por seguridad.

from machine import Pin
import time

# ----------------------------------------------------------------------
# SELECCION DE MODO
#   "STROBE" -> pulsos de microsegundos (uso normal del Hito A)
#   "BLINK"  -> parpadeo lento para MEDIR CORRIENTE con el multimetro (paso 5)
# ----------------------------------------------------------------------
MODE = "STROBE"

# Parametros del estrobo
PULSE_US  = 50     # ancho del flash en microsegundos (rango util 30-80)
PERIOD_MS = 20     # periodo entre flashes (20 ms = 50 Hz)

# Parametro del modo BLINK (medicion de corriente)
BLINK_MS  = 100    # ON 100 ms / OFF 100 ms -> facil de medir con el multimetro

led = Pin(15, Pin.OUT)   # GP15
led.off()                # arranque seguro: LED apagado


def run_strobe():
    while True:
        led.on()
        time.sleep_us(PULSE_US)
        led.off()
        time.sleep_ms(PERIOD_MS)


def run_blink():
    # Para medir la caida en un Rs (56R) con el multimetro: I = V / 56
    # Esperado ~0.13 A por string. NO dejar en este modo mucho rato.
    while True:
        led.on()
        time.sleep_ms(BLINK_MS)
        led.off()
        time.sleep_ms(BLINK_MS)


if MODE == "STROBE":
    run_strobe()
elif MODE == "BLINK":
    run_blink()
else:
    led.off()
