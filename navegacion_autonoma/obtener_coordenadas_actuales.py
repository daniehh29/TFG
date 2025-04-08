import serial
import pynmea2

def leer_gps(puerto="/dev/ttyUSB0", baudrate=4800):
    ser = None  # Inicializamos la variable para evitar el UnboundLocalError
    try:
        # Configurar el puerto serie
        ser = serial.Serial(puerto, baudrate, timeout=1, bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        print(f"Leyendo datos de {puerto} a {baudrate} baudios...")
        
        while True:
            linea = ser.readline().decode('ascii', errors='replace').strip()

            if any(linea.startswith(prefix) for prefix in ('$GPGGA', '$GNGGA', '$GPRMC', '$GNRMC')):
                try:
                    msg = pynmea2.parse(linea)
                    lat = msg.latitude
                    lon = msg.longitude
                    print(f"Latitud: {lat}, Longitud: {lon}")
                except pynmea2.ParseError:
                    print("Error al analizar la línea NMEA.")

    except serial.SerialException as e:
        print(f"Error de conexión con el puerto {puerto}: {e}")
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.")
    finally:
        if ser is not None:
            ser.close()
            print("Puerto cerrado.")

if __name__ == "__main__":
    leer_gps()
