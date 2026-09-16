import sys
import regex as re
import math
import random

# Expresiones regulares
telefono_re = re.compile(
    r'^(?:\d{3}-\d{3}-\d{3}'           # formato 999-999-999
    r'|\+?\d{1,4}(?: ?\d{1,5}){2,6}'   # formato +34 999 999 999
    r'|\d{9})$')                       # formato 999999999

nif_re = re.compile(
    r'^(?:(?P<dni>\d{8})|(?P<nie>[XYZ]\d{7}))-(?P<letra>[A-Z])$')    # acepta el dni normal y el nie

tempo_re = re.compile(
    r'(?i)^(?P<formato1>(?P<fecha1>\d{4}-\d{2}-\d{2}) (?P<hora1>\d{2}:\d{2}))$'                                         # formato YYYY-MM-DD HH:MM
    r'|^(?P<formato2>(?P<mes>january|february|march|april|may|june|july|august|september|october|november|december)\s+' # formato Month D, Y HH:MM AM/PM
    r'(?P<dia>\d{1,2}),\s*(?P<anio>\d{1,4})\s+(?P<hora2>\d{1,2}:\d{2}\s*[AP]M))$'
    r'|^(?P<formato3>(?P<hora3>\d{2}:\d{2}:\d{2})\s+(?P<fecha2>\d{2}/\d{2}/\d{4}))$'                                    # formato HH:MM:SS DD/MM/YYYY
)

coord_re = re.compile(
    r'^(?P<coordenadas1>(?P<latitud>[+-]?\d+(?:\.\d+)?),\s*(?P<longitud>[+-]?\d+(?:\.\d+)?))$'              # formato decimal
    r'|^(?P<coordenadas2>(?P<latitud_sexa>\d{1,2}(?:°|\u00B0)\s*\d{1,2}\'\s*\d{1,2}\.\d{4}"\s*[NS])\s*,\s*' # formato sexagesimal
    r'(?P<longitud_sexa>\d{1,3}(?:°|\u00B0)\s*\d{1,2}\'\s*\d{1,2}\.\d{4}"\s*[EW]))$'
    r'|^(?P<coordenadas3>(?P<latitud_gps>\d{7}\.\d{4}[NS])(?P<longitud_gps>\d{7}\.\d{4}[EW]))$')            # formato GPS

precio_re = re.compile(r'^(?:[1-9]\d*(?:\.\d+)?)[€$]$') # formato del precio con . separador decimales y euro o dolar

#Funcion auxiliar que vamos a crear para -generate pero que también vamos a utilizar en vnif
def calcula_letra_dni(n):
    """Ayuda para calcular la letra del NIF para vnif"""
    letras = "TRWAGMYFPDXBNJZSQVHLCKET"
    return letras[n % 23]

# Funciones de validación
def vtelef(num):
    """Valida un número de telefono español e internacional """
    return bool(telefono_re.fullmatch(num))

def vnif(nif):
    """Valída un NIF o NIE además de la comprobación de la letra"""
    match = nif_re.fullmatch(nif.upper())
    if not match:
        return False
    dni_str = match.group('dni') or match.group('nie')
    if not dni_str:
        return False
    dni_str = dni_str.replace('X', '0').replace('Y', '1').replace('Z', '2')
    dni = int(dni_str)
    letra_calculada = calcula_letra_dni(dni)
    return letra_calculada == match.group('letra')
#Funcion uxiliar para vtempo
def fecha_valida(a, m, d):
    """Comprueba si una fecha es real (considera años bisiestos)."""
    if not (1 <= m <= 12):
        return False
    dias_mes = [31, 29 if (a % 4 == 0 and (a % 100 != 0 or a % 400 == 0)) else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= d <= dias_mes[m - 1]

def vtempo(t):
    """Valída si una cadena cumple uno de los tres formatos de tiempo permitidos."""
    return bool(tempo_re.fullmatch(t))

def vgeo(coord):
    """Valída una coordenada geográfica en cualquier formato."""
    return bool(coord_re.fullmatch(coord))

def vprecio(p):
    """Valída un precio correcto (entero o real, con € o $)."""
    return bool(precio_re.fullmatch(p.strip()))

# Funciones auxiliares de pasar
def pasartelefono(num):
    telf = re.sub(r'[\s-]', '', num)
    if len(telf) == 9 and telf[0] != '+':
        telf = '+34' + telf
    return telf

def pasartiempo(tiempo):
    """Convierte un tiempo válido a un diccionario con datos numéricos."""
    meses = {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6, 'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12}
    match = tempo_re.fullmatch(tiempo)
    if match:
        if match.group('formato1'):  # Formato 1: 'YYYY-MM-DD HH:MM'
            fecha = match.group('fecha1').split('-') #separadores
            hora = match.group('hora1').split(':')
            anio, mes, dia = int(fecha[0]), int(fecha[1]), int(fecha[2])
            hora, minutos = int(hora[0]), int(hora[1])
            comparar = anio * 100000000 + mes * 1000000 + dia * 10000 + hora * 100 + minutos
            return {"año": anio, "mes": mes, "dia": dia, "hora": hora, "minutos": minutos, "comparar": comparar}

        elif match.group('formato2'):  # Formato 2: 'Mes DD, YYYY HH:MM AM/PM'
            mes = meses[match.group('mes').lower()]
            dia = int(match.group('dia'))
            anio = int(match.group('anio'))
            hora2 = match.group('hora2').split(':')
            h = int(hora2[0])
            resto = hora2[1].split()
            minutos = int(resto[0])
            ampm = resto[1].upper()
            if ampm == 'PM' and h != 12:
                h = h + 12
            if ampm == 'AM' and h == 12:
                h = 0
            if not fecha_valida(anio, mes, dia):
                return None
            comparar = anio * 100000000 + mes * 1000000 + dia * 10000 + h * 100 + minutos
            return {"año": anio, "mes": mes, "dia": dia, "hora": h, "minutos": minutos,
                    "comparar": comparar}

        elif match.group('formato3'):  # Formato 3: 'HH:MM:SS DD/MM/YYYY'
            hora3 = match.group('hora3').split(':')
            h = int(hora3[0])
            minutos = int(hora3[1])
            segundos = int(hora3[2])
            fecha2 = match.group('fecha2').split('/')
            dia = int(fecha2[0])
            mes = int(fecha2[1])
            anio = int(fecha2[2])
            if not fecha_valida(anio, mes, dia):
                return None
            comparar = anio * 100000000 + mes * 1000000 + dia * 10000 + h * 100 + minutos
            return {"año": anio, "mes": mes, "dia": dia, "hora": h, "minutos": minutos, "segundos": segundos, "comparar": comparar}
    return None

def pasaradecimal(coord):
    """Convierte coordenadas a decimal"""
    match = coord_re.fullmatch(coord)
    if not match:
        return None

    if match.group('coordenadas1'):
        partes = match.group('coordenadas1').split(',')
        lat = float(partes[0])
        lon = float(partes[1])
        return {"lat": lat, "lon": lon}

    if match.group('coordenadas2'):
        trozos = re.split(r'[°,\'"]+', match.group('coordenadas2'))
        lat_g = float(trozos[0])
        lat_m = float(trozos[1])
        lat_s = float(trozos[2])
        lon_g = float(trozos[4])
        lon_m = float(trozos[5])
        lon_s = float(trozos[6])
        lat = lat_g + lat_m / 60 + lat_s / 3600
        lon = lon_g + lon_m / 60 + lon_s / 3600
        if 'S' in match.group('coordenadas2'):
            lat = -lat
        if 'W' in match.group('coordenadas2'):
            lon = -lon
        return {"lat": lat, "lon": lon}

    if match.group('coordenadas3'):
        lat = match.group('coordenadas3')[:13]
        lon = match.group('coordenadas3')[13:]

        def convertir(c):
            g = int(c[:3])
            m = int(c[3:5])
            s = float(c[5:10])
            total = g + m / 60 + s / 3600
            if c[-1] in 'SW':
                total = -total
            return total

        return {"lat": convertir(lat), "lon": convertir(lon)}

    return None
#Para la opcion -sloction
def harvensine (lat1, lon1, lat2, lon2):
    """Calcula la distancia entre dos puntos geográficos"""
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r =  6367.45
    return c * r

# Función Normalizar -n
def normalizar(archivo, formato_tiempo=2, formato_coord=3):
    """Normaliza las líneas del archivo si son válidas y omita las incorrectas"""
    try:
        f= open(archivo, 'r', encoding='utf8')
        for linea in f:
            linea = linea.strip()
            if linea != "":
                columnas = linea.split(';')
                if len(columnas) == 6:
                    telefono = columnas[0].strip()
                    nif = columnas[1].strip()
                    tiempo = columnas[2].strip()
                    coord = columnas[3].strip()
                    producto = columnas[4].strip()
                    precio = columnas[5].strip()

                    linea_valida = True
                    tiempo_norm =""
                    coord_norm = ""

                    if not (vtelef(telefono) and vnif(nif) and vtempo(tiempo) and vgeo(coord) and vprecio(precio)):
                        linea_valida = False

                    if linea_valida:
                        #Normalizamos el teléfono
                        telefono = pasartelefono(telefono)
                        if len(telefono) == 9 and telefono[0] != '+':
                            telefono = '+34' + telefono

                        #Normalizamos el tiempo
                        tiempo_nuevo = pasartiempo(tiempo)
                        if tiempo_nuevo:
                            segundos = tiempo_nuevo.get('segundos', 0)
                            if formato_tiempo == 1:
                                tiempo_norm = f"{tiempo_nuevo['año']:04d}-{tiempo_nuevo['mes']:02d}-{tiempo_nuevo['dia']:02d} {tiempo_nuevo['hora']:02d}:{tiempo_nuevo['minutos']:02d}"
                            elif formato_tiempo == 2:
                                meses = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
                                         7: "July", 8: "August", 9: "September", 10: "October", 11: "November",
                                         12: "December"}
                                hora12 = tiempo_nuevo['hora'] % 12 or 12
                                ampm = "AM" if tiempo_nuevo['hora'] < 12 else "PM"
                                tiempo_norm = f"{meses[tiempo_nuevo['mes']]} {tiempo_nuevo['dia']}, {tiempo_nuevo['año']} {hora12}:{tiempo_nuevo['minutos']:02d} {ampm}"
                            else:
                                tiempo_norm = f"{tiempo_nuevo['hora']:02d}:{tiempo_nuevo['minutos']:02d}:{segundos:02d} {tiempo_nuevo['dia']:02d}/{tiempo_nuevo['mes']:02d}/{tiempo_nuevo['año']:04d}"
                        else:
                            linea_valida = False

                        #Normalizamos las coordenadas
                        coorde_nueva = pasaradecimal(coord)
                        if coorde_nueva:
                            lat = abs(coorde_nueva['lat'])
                            lon = abs(coorde_nueva['lon'])
                            lat_dir = 'N' if coorde_nueva['lat'] >= 0 else 'S'
                            lon_dir = 'E' if coorde_nueva['lon'] >= 0 else 'W'

                            if formato_coord == 1:
                                coord_norm = f"{coorde_nueva['lat']:.6f}, {coorde_nueva['lon']:.6f}"
                            elif formato_coord == 2:
                                grados_lat = int(lat)
                                minutos_lat_dec = (lat - grados_lat) * 60
                                minutos_lat = int(minutos_lat_dec)
                                segundos_lat = (minutos_lat_dec - minutos_lat) * 60
                                grados_lon = int(lon)
                                minutos_lon_dec = (lon - grados_lon) * 60
                                minutos_lon = int(minutos_lon_dec)
                                segundos_lon = (minutos_lon_dec - minutos_lon) * 60
                                coord_norm = (f'{grados_lat}° {minutos_lat}\' {segundos_lat:.4f}" {lat_dir}, '
                                              f'{grados_lon}° {minutos_lon}\' {segundos_lon:.4f}" {lon_dir}')
                            else:
                                lat_g = int(lat)
                                lat_m = int((lat - lat_g) * 60)
                                lat_s = ((lat - lat_g) * 3600) - (lat_m * 60)
                                lon_g = int(lon)
                                lon_m = int((lon - lon_g) * 60)
                                lon_s = ((lon - lon_g) * 3600) - (lon_m * 60)
                                coord_norm = (f"{lat_g:03d}{lat_m:02d}{lat_s:07.4f}{lat_dir}"
                                            f"{lon_g:03d}{lon_m:02d}{lon_s:07.4f}{lon_dir}")
                        else:
                            linea_valida = False

                    if linea_valida:
                        print(f"{telefono};{nif};{tiempo_norm};{coord_norm};{producto};{precio}")
        f.close()
    except FileNotFoundError:
        print(f"Error: el archivo {archivo} no existe.")
        sys.exit(1)

#Búsquedas
def buscarnum(numero,archivo):
    """Realiza una búsqueda de un número de teléfono en el archivo"""
    if not vtelef(numero):
        print(f"Error: Formato de numero no valido {numero}")
        return # se termina
    num = pasartelefono(numero)
    try:
         f=open(archivo, 'r', encoding='utf8')
         encontrado = False
         for linea in f:
             columnas = linea.split(';')
             telefono = columnas[0].strip()# las separaciones
             telef = pasartelefono(telefono)
             if num == telef:
                 print(linea.strip())  # imprimimos la linea tal cual
                 encontrado = True
         if not encontrado:
                print(f"El número {numero} no se encontró en el archivo.")
         f.close()
    except FileNotFoundError:
        print(f"Error: el archivo {archivo} no existe.")
        sys.exit(1)


def buscarnif(nif,archivo):
    """Realiza una búsqueda del DNI en el archivo"""
    if not vnif(nif):
        print(f"Error: Formato NIF no valido {nif}")
        return
    try:
        f = open(archivo, 'r', encoding='utf8')
        encontrado = False
        for linea in f:
            columnas = linea.split(";")
            dni_columna = columnas[1].strip()
            if nif == dni_columna:
                print(linea.strip())
                encontrado = True
        if not encontrado :
            print(f"El número {nif} no se encontró en el archivo.")
        f.close()
    except FileNotFoundError:
        print(f"Error: el archivo {archivo} no existe.")
        sys.exit(1)

def filtrarportiempo(archivo, desde, hasta):
    """Se realiza una búsqueda del tiempo en el archivo y se compara"""
    tdesde = pasartiempo(desde)
    thasta = pasartiempo(hasta)

    if not tdesde or not thasta:
        print("Error: Formato de tiempo no válido")
        sys.exit(1)

    try:
        f = open(archivo, 'r', encoding='utf8')
        encontrado = False
        for linea in f:
            columnas = linea.split(';')# el separador ';'
            tiempo_linea = columnas[2].strip()
            tlinea = pasartiempo(tiempo_linea)
            if tlinea:
                if tdesde['comparar'] <= tlinea['comparar'] <= thasta['comparar']:
                    print(linea.strip())
                    encontrado = True
        if not encontrado:
            print(f"No se han econtrado resultados")
        f.close()
    except FileNotFoundError:
        print(f"Error: el archivo {archivo} no existe.")
        sys.exit(1)

def filtrarporcoordenadas(archivo, desde, hasta):
    """Se realiza una búsqueda de las coordenadas en el archivo"""
    coords_desde = pasaradecimal(desde)
    if not coords_desde:
        print("Error: Formato de coordenada no valida")
        sys.exit(1)
    try:
        distanciamax = float(hasta)
    except ValueError:
        print("Error: La distancia máxima debe ser un número válido.")
        return
    try:
        f = open(archivo, 'r', encoding='utf8')
        encontrado = False
        for linea in f:
            columnas = linea.split(';')
            if len(columnas) > 3:
                c2 = pasaradecimal(columnas[3].strip())
                if c2:
                    d = harvensine(coords_desde['lat'], coords_desde['lon'], c2['lat'], c2['lon'])
                    if d <= distanciamax:
                        print(linea.strip())
                        encontrado = True
        if not encontrado:
            print("No se encontraron coordenadas dentro del rango.")
        f.close()
    except FileNotFoundError:
        print(f"Error: el archivo {archivo} no existe.")
        sys.exit(1)

#Funciones auxiliares para generar registros aleatorios, para el comando -generate
def generar_dni():
    """Generamos un número de 8 dígitos y su letra"""
    num = random.randint(10000000, 99999999)
    letra = calcula_letra_dni(num)
    return f"{num}-{letra}"

def generar_telefono():
    """Generamos tres formatos válidos, 1:999-999-999, 2:+34 999 999 999, 3:999999999 """
    tipo = random.randint(1,3)
    if tipo == 1:
        t1 = random.randint(100,999)
        t2 = random.randint(100,999)
        t3 = random.randint(100,999)
        return f"{t1}-{t2}-{t3}"
    elif tipo == 2:
        t1 = random.randint(100, 999)
        t2 = random.randint(100, 999)
        t3 = random.randint(100, 999)
        return f"+34 {t1} {t2} {t3}"
    elif tipo == 3:
        numero = random.randint(100000000, 999999999)
        return f"{numero}"

def fecha_aleatoria():
    """Calculamos una fecha aleatoria, en este caso desde 1900 hasta ahora 2025"""
    anio = random.randint(1900, 2025)
    mes = random.randint(1, 12)
    if mes == 2:
        if anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0):
            dias = 29
        else:
            dias = 28
    elif mes in (4, 6, 9, 11):
        dias = 30
    else:
        dias = 31

    dia = random.randint(1, dias)
    hora = random.randint(0, 23)
    minuto = random.randint(0, 59)
    segundo = random.randint(0, 59)
    return anio, mes, dia, hora, minuto, segundo

def generar_tiempo_aleatorio():
    """Ahora vamos a moldearlo en un formato aleatorio de los tres formatos que aceptamos
    1:YYYY-MM-DD HH:MM, 2:Month D, Y HH:MM AM/PM, 3:HH:MM:SS DD/MM/YYYY"""
    anio, mes, dia, hora, minuto, segundo = fecha_aleatoria()
    tipo = random.randint(1, 3)
    if tipo == 1:
        return f"{anio:04d}-{mes:02d}-{dia:02d} {hora:02d}:{minuto:02d}"
    elif tipo == 2:
        meses = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
                 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
        h12 = hora % 12 or 12
        ampm = "AM" if hora < 12 else "PM"
        return f"{meses[mes]} {dia}, {anio} {h12:02d}:{minuto:02d} {ampm}"
    elif tipo == 3:
        return f"{hora:02d}:{minuto:02d}:{segundo:02d} {dia:02d}/{mes:02d}/{anio:04d}"

def generar_coord():
    """Generamos coordenadas en los tres formatos que tenemos
    1:Decimal, 2:Sexagesimal, 3:GPS"""
    tipo = random.randint(1, 3)
    if tipo == 1:
        lat = random.uniform(-90.0, 90.0)
        lon = random.uniform(-180.0, 180.0)
        return f"{lat:.4f}, {lon:.4f}"
    elif tipo == 2:
        lat_g = random.randint(0, 90)
        lat_m = random.randint(0, 59)
        lat_s = random.uniform(0, 59.9999)
        lat_dir = random.choice(['N', 'S'])

        lon_g = random.randint(0, 180)
        lon_m = random.randint(0, 59)
        lon_s = random.uniform(0, 59.9999)
        lon_dir = random.choice(['E', 'W'])
        lat_str = f"{lat_g}° {lat_m}' {lat_s:.4f}\" {lat_dir}"
        lon_str = f"{lon_g}° {lon_m}' {lon_s:.4f}\" {lon_dir}"
        return f"{lat_str}, {lon_str}"
    elif tipo == 3:
        lat_g = random.randint(0, 90)
        lat_m = random.randint(0, 59)
        lat_s = random.uniform(0, 59.9999)
        lat_dir = random.choice(['N', 'S'])

        lon_g = random.randint(0, 180)
        lon_m = random.randint(0, 59)
        lon_s = random.uniform(0, 59.9999)
        lon_dir = random.choice(['E', 'W'])
        lat = f"{lat_g:02d}{lat_m:02d}{lat_s:07.4f}{lat_dir}"
        lon = f"{lon_g:03d}{lon_m:02d}{lon_s:07.4f}{lon_dir}"
        return f"{lat}{lon}"

def generar_productos():
    """Generamos el producto"""
    productos =["iMac", "iPad", "Apple Watch", "MacBook", "iPhone", "Airpods"]
    return random.choice(productos)

def generar_precio():
    """Generamos un precio con separador . para decimal"""
    p1 = random.randint(1, 9999)
    p2 = random.randint(0, 99)
    simbolo = random.choice(['€', '$'])
    if p2 == 0:
        return f"{p1}{simbolo}"
    else:
        return f"{p1}.{p2:02d}{simbolo}"

#Funcion generate para -generate
def generate(fichero, n):
    """Vamos a generar un nuevo fichero con el nombre designado con las n líneas indicadas"""
    try:
        n_int = int(n)
    except ValueError:
        print("Error: el número de líneas debe ser un entero")
        sys.exit(1)

    try:
        f = open(fichero, 'w',encoding='utf8')
        i = 0
        while i < n_int:
            telefono = generar_telefono()
            nif = generar_dni()
            tiempo = generar_tiempo_aleatorio()
            coord = generar_coord()
            producto = generar_productos()
            precio = generar_precio()
            linea = f"{telefono};{nif};{tiempo};{coord};{producto};{precio}"
            f.write(linea + "\n")
            i = i+1
        f.close()
        print(f"Se han generado {n_int} registros en {fichero}")
    except OSError:
        print(f"Error: no se pudo escribir en {fichero}")


# Función principal
def main():
    if len(sys.argv) < 2:
        print("Uso: main.py <comando> [argumentos]")
        sys.exit(1)

    comando = sys.argv[1]
#cuando el comando es -n realiza una normalizacion del fichero
    if comando == "-n":
        if len(sys.argv) not in (3,5):
            print("Error: número de argumentos inválido para -n")
            sys.exit(1)
        ruta_archivo = sys.argv[2]
        if len(sys.argv) == 5:
            f1 = int(sys.argv[3])
            f2 = int(sys.argv[4])
            if not (1<= f1 <=3 and 1<=f2<=3):
                print("Error: f1 y f2 deben ser un número del 1 al 3")
                sys.exit(1)
            else:
                normalizar(ruta_archivo, f1, f2)
        else:
            normalizar(ruta_archivo,2,3)

#Cuando este comando sea -sphone será llamado el teléfono el cual buscaremos en la función y en la ruta del archivo
    elif comando == "-sphone":
        if len(sys.argv) != 4:
            print("Error: número de argumentos inválido para -sphone")
            sys.exit(1)
        telefono = sys.argv[2]
        ruta_archivo = sys.argv[3]
        buscarnum(telefono, ruta_archivo)

#Cuando el comando sea -snif será el nif proporcionado según el orden validado y la ruta también pasádo al buscarnif
    elif comando == "-snif":
        if len(sys.argv) != 4:
            print("Error: número de argumentos inválido para -snif")
            sys.exit(1)
        nif = sys.argv[2]
        ruta_archivo = sys.argv[3]
        buscarnif(nif,ruta_archivo)
#Cuando el comando sea -stime serán dos parámetros que pasaremos, realizando una búsqueda
    elif comando == "-stime":
        if len(sys.argv) != 5:
            print("Error: número de argumentos inválido para -stime")
            sys.exit(1)
        tiempo1 = sys.argv[2]
        tiempo2 = sys.argv[3]
        ruta_archivo = sys.argv[4]
        filtrarportiempo(ruta_archivo, tiempo1, tiempo2)

#Cuando el comando sea -slocation serán dos parámetros que pasaremos, realizando una búsqueda
    elif comando == "-slocation":
        if len(sys.argv) != 5:
            print("Error: número de argumentos inválido para -slocation")
            sys.exit(1)
        coordenadas1 = sys.argv[2]
        distancia = sys.argv[3]
        ruta_archivo = sys.argv[4]
        filtrarporcoordenadas(ruta_archivo,coordenadas1,distancia)
#Cuando el comando sea -generate serán dos parámetros, el primero el nombre del fichero y el segundo cuantas líneas que se generarán
    elif comando == "-generate":
        if len(sys.argv) != 4:
            print("Error: número de argumentos inválido para -generate")
            sys.exit(1)
        fichero = sys.argv[2]
        lineas = sys.argv[3]
        generate(fichero,lineas)
#Por si introduce un comando inválido o ha introducido mal el nombre
    else:
        print("Comando no válido. Usa uno de los siguientes:")
        print("-n, -sphone, -snif, -stime, -slocation, -generate")
        sys.exit(1)

if __name__ == "__main__":
    main()


"""
-n <fichero> [f1] [f2] 
-sphone <teléfono> <fichero>
-snif  <NIF> <fichero>
-stime <desde> <hasta> <fichero>
-slocation <desde> <hasta> <fichero>
-generate <fichero> <líneas> 

-rmphone <telefono> <fichero>  -> funcion que imprime por pantalla solamente los registros que no sean iguales al introducido 
                                    (quitas los telefonos iguales al argumento del fichero)

"""