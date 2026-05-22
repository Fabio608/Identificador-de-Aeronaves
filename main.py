import folium

# 1. Definimos coordenadas de ejemplo (Ruta Santa Rosa a Bariloche)
# Valores de ejemplo de "Corrección de Inyector" (Cuanto más alto, peor el inyector)
ruta_ejemplo = [
    {"lat": -36.62, "lon": -64.29, "valor": 2.0},   # Santa Rosa (Verde - OK)
    {"lat": -37.50, "lon": -66.00, "valor": 4.5},   # En ruta (Verde - OK)
    {"lat": -39.00, "lon": -68.00, "valor": 9.0},   # Zona de carga (Amarillo - Atención)
    {"lat": -40.50, "lon": -70.50, "valor": 15.0}  # Cerca de Bariloche (Rojo - Falla)
]

# 2. Creamos el mapa centrado en el medio de la ruta
m = folium.Map(location=[-38.5, -67.0], zoom_start=6)

# 3. Función para asignar colores según el valor
def get_color(valor):
    if valor < 5:
        return 'green'
    elif valor < 12:
        return 'orange'
    else:
        return 'red'

# 4. Dibujamos los puntos en el mapa
for punto in ruta_ejemplo:
    folium.CircleMarker(
        location=[punto['lat'], punto['lon']],
        radius=10,
        color=get_color(punto['valor']),
        fill=True,
        fill_color=get_color(punto['valor']),
        fill_opacity=0.7,
        popup=f"Corrección: {punto['valor']}"
    ).add_to(m)

# 5. Guardar o mostrar el mapa
# Si estás en un Jupyter Notebook, simplemente escribe 'm'
# Si quieres guardarlo como archivo HTML:
m.save("mapa_inyectores.html")

# Para visualizarlo aquí (instrucción simbólica):
m
