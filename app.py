import streamlit as st
import pandas as pd

# Configuración principal de la página web
st.set_page_config(page_title="Sistema de Comisiones", page_icon="💰", layout="centered")

# Inicializar la memoria temporal (para que guarde los extras al actualizar la página)
if 'extras' not in st.session_state:
    st.session_state.extras = []
if 'comision_base' not in st.session_state:
    st.session_state.comision_base = 0.0
if 'calculo_realizado' not in st.session_state:
    st.session_state.calculo_realizado = False

# Título de la Aplicación
st.title("💰 Sistema de Comisiones")
st.write("Sube tus archivos Excel para realizar el cruce de datos y calcular tu comisión.")

# 1. Zona de Botones para subir archivos
st.header("1. Carga de Archivos")
col1, col2 = st.columns(2)
with col1:
    archivo_ventas = st.file_uploader("📂 1. Cargar Excel Ventas", type=['xlsx', 'xls'])
with col2:
    archivo_productos = st.file_uploader("📂 2. Cargar Excel Productos", type=['xlsx', 'xls'])

# Botón Generar
if st.button("🚀 3. GENERAR RESULTADOS", use_container_width=True):
    if archivo_ventas is None or archivo_productos is None:
        st.error("Por favor, sube ambos archivos Excel antes de generar el resultado.")
    else:
        try:
            # Leer las columnas exactas de Ventas: P (0), T (1), X (2), AO (3)
            df_ventas = pd.read_excel(archivo_ventas, usecols="P,T,X,AO")
            # Leer las columnas exactas de Productos: A (0), E (1)
            df_productos = pd.read_excel(archivo_productos, usecols="A,E")

            # Asignar variables por su posición en la lectura para evitar errores de nombres
            col_cod_v = df_ventas.columns[0]
            col_cant = df_ventas.columns[1]
            col_monto = df_ventas.columns[2]
            col_vend = df_ventas.columns[3]

            col_cod_p = df_productos.columns[0]
            col_precio_c = df_productos.columns[1]

            # Filtrar exactamente por el vendedor indicado
            filtro_vendedor = df_ventas[col_vend].astype(str).str.strip().str.lower().str.contains("antonio enrique mart", na=False)
            df_ventas_filtrado = df_ventas[filtro_vendedor]

            if df_ventas_filtrado.empty:
                st.warning("No se encontraron ventas asociadas a 'Antonio Enrique Martínez Toledo' en el Excel.")
            else:
                # Cruzar los datos (Código Ventas = Código Productos)
                df_cruce = pd.merge(
                    df_ventas_filtrado, 
                    df_productos, 
                    left_on=col_cod_v, 
                    right_on=col_cod_p, 
                    how='inner'
                )

                if df_cruce.empty:
                    st.error("No hubo coincidencias de códigos entre las ventas y los productos.")
                else:
                    # Limpiar datos y convertirlos a números para la matemática
                    df_cruce[col_cant] = pd.to_numeric(df_cruce[col_cant], errors='coerce').fillna(0)
                    df_cruce[col_monto] = pd.to_numeric(df_cruce[col_monto], errors='coerce').fillna(0)
                    df_cruce[col_precio_c] = pd.to_numeric(df_cruce[col_precio_c], errors='coerce').fillna(0)

                    # Matemáticas
                    df_cruce['Costo_Total'] = df_cruce[col_precio_c] * df_cruce[col_cant]
                    df_cruce['Ganancia_Real'] = df_cruce[col_monto] - df_cruce['Costo_Total']
                    df_cruce['Comision_Parcial'] = df_cruce['Ganancia_Real'] * 0.07

                    # Sumar la comisión total base y guardarla en sesión
                    st.session_state.comision_base = df_cruce['Comision_Parcial'].sum()
                    st.session_state.calculo_realizado = True
                    st.success("¡Cruce y cálculo base completado con éxito!")

        except Exception as error:
            st.error(f"Error al procesar los archivos: {str(error)}")

# 2. Zona de Ajustes (Solo aparece después de apretar Generar)
if st.session_state.calculo_realizado:
    st.markdown("---")
    st.header("2. Resultados y Ajustes")
    
    st.metric(label="Comisión Base (7%)", value=f"${st.session_state.comision_base:,.2f}")
    
    st.subheader("Agregar Ajustes Extras")
    st.write("Escribe el nombre y el monto. Usa un número normal (positivo) para sumar, o ponle un signo menos (-) para restar un descuento.")
    
    # Formulario para los extras
    with st.form("formulario_extras", clear_on_submit=True):
        col_c, col_m = st.columns([2, 1])
        with col_c:
            concepto_nuevo = st.text_input("Concepto (Ej: Almuerzo, Petróleo):")
        with col_m:
            monto_nuevo = st.number_input("Monto:", value=0.0, format="%.2f")
            
        boton_agregar = st.form_submit_button("Agregar Ítem")
        
        if boton_agregar:
            if concepto_nuevo.strip() != "" and monto_nuevo != 0:
                st.session_state.extras.append({"concepto": concepto_nuevo, "monto": monto_nuevo})
                st.rerun() # Actualizar página para mostrar el nuevo ítem
            else:
                st.warning("Debes ingresar un nombre y un monto válido.")

    # Listar los extras ingresados
    st.subheader("Detalle de Ajustes Manuales")
    total_extras = 0.0
    if not st.session_state.extras:
        st.info("Aún no hay ajustes registrados.")
    else:
        for extra in st.session_state.extras:
            signo = "+" if extra["monto"] > 0 else ""
            color = "green" if extra["monto"] > 0 else "red"
            st.markdown(f"• **{extra['concepto']}**: <span style='color:{color}'>{signo}${extra['monto']:,.2f}</span>", unsafe_allow_html=True)
            total_extras += extra["monto"]
            
        if st.button("Limpiar todos los ajustes"):
            st.session_state.extras = []
            st.rerun()

    # Cálculo Final
    st.markdown("---")
    total_final = st.session_state.comision_base + total_extras
    
    st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>TOTAL A RECIBIR:<br>${total_final:,.2f}</h1>", unsafe_allow_html=True)
