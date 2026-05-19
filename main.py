elif modulo == "Procesador KMZ":
    st.subheader("Convertidor a KMZ profesional")
    archivo = st.file_uploader("Subir archivo CSV de traza:", type=["csv"])

    if archivo:
        try:
            df = pd.read_csv(archivo)
            lat_cols = [c for c in df.columns if 'lat' in c.lower()]
            lon_cols = [c for c in df.columns if 'lon' in c.lower()]
            alt_cols = [c for c in df.columns if 'alt' in c.lower()]

            if not lat_cols or not lon_cols or not alt_cols:
                st.error("No se encontraron columnas con latitud, longitud o altitud en el archivo.")
            else:
                lat_col = lat_cols[0]
                lon_col = lon_cols[0]
                alt_col = alt_cols[0]

                coords = []
                for _, fila in df.iterrows():
                    lat = float(fila[lat_col])
                    lon = float(fila[lon_col])
                    alt = float(fila[alt_col]) * 0.3048  # pies a metros
                    coords.append((lon, lat, alt))

                kml = simplekml.Kml()
                ruta = kml.newlinestring(name="Traza", coords=coords)
                ruta.altitudemode = simplekml.AltitudeMode.absolute
                ruta.extrude = 1

                kmz_bytes = BytesIO()
                kml.savekmz(kmz_bytes)
                kmz_bytes.seek(0)

                st.download_button(
                    label="Descargar KMZ generado",
                    data=kmz_bytes,
                    file_name="traza_procesada.kmz",
                    mime="application/vnd.google-earth.kmz"
                )
                st.success("¡Archivo listo para Google Earth!")
        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")
            print(f"Error detalle: {e}")
