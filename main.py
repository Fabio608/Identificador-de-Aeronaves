from FlightRadar24 import FlightRadar24API
import matplotlib.pyplot as plt

fr_api = FlightRadar24API()

# 1. Buscar los detalles del vuelo en el playback
# (Suponiendo que tenemos el ID del vuelo histórico)
flight_details = fr_api.get_flight_details("ID_DEL_VUELO")
trail = flight_details['trail'] # Esto contiene la trayectoria

# 2. Extraer Latitudes y Longitudes
longitudes = [point['lng'] for point in trail]
latitudes = [point['lat'] for point in trail]

# 3. Dibujar la trayectoria
plt.plot(longitudes, latitudes, marker='o', color='blue')
plt.title("Trayectoria del Vuelo")
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.show()
