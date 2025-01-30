#! /usr/local/bin/python
#-*- coding: utf-8 -*-
import gps, os, time

# Crear la sesión GPS
gpsd = gps.gps(host="127.0.0.1", port="2947")
gpsd.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

while True:
    try:
        os.system("clear") # Limpiar la pantalla
        report = gpsd.next() # Obtener el siguiente reporte del GPS

        if report['class'] == 'TPV': # Verificar si el reporte es de tipo TPV (Time/Position/Velocity)
            print
            print " GPS reading "
            print "—————————————"
            if hasattr(report, 'lat'): # Verificamos si existe el atributo lat antes de accederlo.
                print "latitude " , report.lat
            if hasattr(report, 'lon'): # Verificamos si existe el atributo lon antes de accederlo.
                print "longitude " , report.lon
            # Imprimir otros datos si están disponibles:
            # if hasattr(report, 'time'):
            #     print "time utc", report.time
            # if hasattr(report, 'alt'):
            #     print "altitude", report.alt
            # if hasattr(report, 'speed'):
            #     print "speed", report.speed
            # if hasattr(report, 'track'):
            #     print "track", report.track

    except StopIteration:
        print "GPSD ha terminado"
        break
    except KeyboardInterrupt:
        print "Programa terminado por el usuario"
        break
    except AttributeError:
        pass # Ignorar errores de atributos que faltan en algunos reportes
    time.sleep(1)