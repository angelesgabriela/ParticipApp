import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="ParticipApp", page_icon="🗳️", layout="wide")

FILAS = 15
COLUMNAS = 20
PADRON_FILE = "mesa_orden.xlsx"
VOTOS_FILE = "votos_global.json"

COORDINADORES = {
    "Saryd": [1, 2, 3, 4, 5],
    "Tatiana": [6, 7, 8, 9, 10],
    "Andrea": [11, 12, 13, 14, 15],
    "Nathalia": [16, 17, 18, 19, 20],
    "Evelyn": [21, 22, 23, 24, 25],
}


@st.cache_data
def cargar_padron():
    df = pd.read_excel(PADRON_FILE)
    df.columns = df.columns.str.lower().str.strip()
    return df


def cargar_votos():
    if not os.path.exists(VOTOS_FILE):
        return {}
    with open(VOTOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_votos(votos):
    with open(VOTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(votos, f, ensure_ascii=False, indent=2)


df = cargar_padron()
votos = cargar_votos()

st.title("🗳️ ParticipApp")
st.subheader("Monitoreo de participación")

coordinador = st.selectbox("Soy", list(COORDINADORES.keys()))
mesas_permitidas = COORDINADORES[coordinador]

mesa = st.selectbox("Mesa asignada", mesas_permitidas)

mesa_key = str(mesa)

if mesa_key not in votos:
    votos[mesa_key] = []

votos_mesa = set(votos[mesa_key])

st.write(f"### Mesa {mesa}")

for fila in range(1, FILAS + 1):
    cols = st.columns(COLUMNAS)

    for col in range(COLUMNAS):
        orden = fila + col * FILAS

        if orden > 300:
            continue

        seleccionado = orden in votos_mesa
        texto = f"✅ {orden}" if seleccionado else str(orden)

        if cols[col].button(texto, key=f"m{mesa}_o{orden}"):
            if seleccionado:
                votos_mesa.remove(orden)
            else:
                votos_mesa.add(orden)

            votos[mesa_key] = sorted(list(votos_mesa))
            votos["_ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            guardar_votos(votos)
            st.rerun()

if mesa <= 18:
    voto_301 = st.checkbox(
        "Orden 301 votó",
        value=301 in votos_mesa,
        key=f"m{mesa}_301"
    )

    if voto_301 and 301 not in votos_mesa:
        votos_mesa.add(301)
        votos[mesa_key] = sorted(list(votos_mesa))
        votos["_ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        guardar_votos(votos)
        st.rerun()

    if not voto_301 and 301 in votos_mesa:
        votos_mesa.remove(301)
        votos[mesa_key] = sorted(list(votos_mesa))
        votos["_ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        guardar_votos(votos)
        st.rerun()

st.divider()

# Resumen por mesa
resumen = []

for m in sorted(df["mesa"].unique()):
    total_mesa = len(df[df["mesa"] == m])
    votaron_mesa = len(votos.get(str(m), []))
    faltan_mesa = total_mesa - votaron_mesa
    participacion_mesa = votaron_mesa / total_mesa * 100 if total_mesa else 0

    resumen.append({
        "mesa": m,
        "total": total_mesa,
        "votaron": votaron_mesa,
        "faltan": faltan_mesa,
        "participacion_%": round(participacion_mesa, 2)
    })

resumen_df = pd.DataFrame(resumen)

total_padron = resumen_df["total"].sum()
total_votaron = resumen_df["votaron"].sum()
total_faltan = resumen_df["faltan"].sum()
participacion_total = total_votaron / total_padron * 100 if total_padron else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total local", int(total_padron))
c2.metric("Votaron", int(total_votaron))
c3.metric("No votaron", int(total_faltan))
c4.metric("Participación total", f"{participacion_total:.2f}%")

st.write("### Participación por mesa")
st.dataframe(resumen_df, use_container_width=True)

if "_ultima_actualizacion" in votos:
    st.caption(f"Última actualización: {votos['_ultima_actualizacion']}")

# Archivo consolidado descargable solo como respaldo
detalle = df.copy()
detalle["voto"] = detalle.apply(
    lambda row: "SI" if int(row["orden"]) in votos.get(str(int(row["mesa"])), []) else "NO",
    axis=1
)

csv = detalle.to_csv(index=False).encode("utf-8")

st.download_button(
    "Descargar respaldo CSV",
    data=csv,
    file_name="participapp_respaldo.csv",
    mime="text/csv"
)
