import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Comisiones", page_icon="🔐", layout="centered")

# --- SEGURIDAD Y PANTALLA DE BLOQUEO ---
def check_password():
    """Retorna True si el usuario ingresó la contraseña correcta."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.title("🔐 Acceso Restringido")
    password = st.text_input("Introduce la contraseña para continuar:", type="password")
    if st.button("Entrar", use_container_width=True):
        if password == "antonio2026": # Esta es tu contraseña, puedes cambiarla si deseas
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    return False

# Solo si la contraseña es correcta, se ejecuta el resto del programa
if check_password():
    
    # --- INICIALIZAR LA MEMORIA DE LA SESIÓN ---
    if 'extras' not in st.session_state:
        st.session_state.extras = []
    if 'comision_base' not in st.session_state:
        st.session_state.comision_base = 0.0
    if 'calculo_realizado' not in st.session_state:
        st.session_state.calculo_realizado = False
    if 'porcentaje' not in st.session_state:
        st.session_state.porcentaje = 7.0 # Porcentaje por defecto

    # --- ENGRANE OCULTO DE CONFIGURACIÓN ---
    with st.expander("⚙️ Configuración del Motor"):
        st.session_state.porcentaje = st.number_input(
            "Ajustar porcentaje de ganancia a calcular:",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.porcentaje,
            step=0.1
        )
        st.info("Nota: Este porcentaje se utilizará para el cálculo, pero se mantendrá oculto en la pantalla de resultados finales.")

    st.title("💰 Panel de Comisiones")

    # --- 1. ZONA DE CARGA DE ARCHIVOS ---
    st.header("1. Carga de Archivos")
    col1, col2 = st.columns(2)
    with col1:
        archivo_ventas = st.file_uploader("📂 1. Cargar Excel Ventas", type=['xlsx', 'xls'])
    with col2:
        archivo_productos = st.file_uploader("📂 2. Cargar Excel Productos", type=['xlsx', 'xls'])

    # --- 2. MOTOR DE CÁLCULO ---
    if st.button("🚀 3. GENERAR RESULTADOS", use_container_width=True):
        if archivo_ventas is None or archivo_productos is None:
            st.error("Por favor, sube ambos archivos Excel antes de generar el resultado.")
        else:
            try:
                # Leer columnas por posición física: Ventas (P, T, X, AO) y Productos (A, E)
                df_ventas = pd.read_excel(archivo_ventas, usecols="P,T,X,AO")
                df_productos = pd.read_excel(archivo_productos, usecols="A,E")

                col_cod_v = df_ventas.columns[0]
                col_cant = df_ventas.columns[1]
                col_monto = df_ventas.columns[2]
                col_vend = df_ventas.columns[3]

                col_cod_p = df_productos.columns[0]
                col_precio_c = df_productos.columns[1]

                # Filtrar vendedor
                filtro_vendedor = df_ventas[col_vend].astype(str).str.strip().str.lower().str.contains("antonio enrique mart", na=False)
                df_ventas_filtrado = df_ventas[filtro_vendedor]

                if df_ventas_filtrado.empty:
                    st.warning("No se encontraron ventas asociadas a tu nombre en el archivo cargado.")
                else:
                    # Cruce exacto por código
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
                        df_cruce[col_cant] = pd.to_numeric(df_cruce[col_cant], errors='coerce').fillna(0)
                        df_cruce[col_monto] = pd.to_numeric(df_cruce[col_monto], errors='coerce').fillna(0)
                        df_cruce[col_precio_c] = pd.to_numeric(df_cruce[col_precio_c], errors='coerce').fillna(0)

                        # Matemática
                        df_cruce['Costo_Total'] = df_cruce[col_precio_c] * df_cruce[col_cant]
                        df_cruce['Ganancia_Real'] = df_cruce[col_monto] - df_cruce['Costo_Total']
                        
                        # Aquí usa el número del engrane de configuración dividido por 100
                        df_cruce['Comision_Parcial'] = df_cruce['Ganancia_Real'] * (st.session_state.porcentaje / 100)

                        st.session_state.comision_base = df_cruce['Comision_Parcial'].sum()
                        st.session_state.calculo_realizado = True
                        st.success("¡Cruce y cálculo completado con éxito!")

            except Exception as error:
                st.error(f"Error al procesar los archivos: {str(error)}")

    # --- 3. ZONA DE RESULTADOS Y AJUSTES ---
    if st.session_state.calculo_realizado:
        st.markdown("---")
        st.header("2. Resultados y Ajustes")
        
        # El título ya no menciona el porcentaje
        st.metric(label="Comisión Base", value=f"${st.session_state.comision_base:,.2f}")
        
        st.subheader("Agregar Ajustes Extras")
        st.write("Escribe el nombre y el monto (+ para sumar, - para restar un descuento).")
        
        with st.form("formulario_extras", clear_on_submit=True):
            col_c, col_m = st.columns([2, 1])
            with col_c:
                concepto_nuevo = st.text_input("Concepto:")
            with col_m:
                monto_nuevo = st.number_input("Monto:", value=0.0, format="%.2f")
                
            boton_agregar = st.form_submit_button("Agregar Ítem")
            
            if boton_agregar:
                if concepto_nuevo.strip() != "" and monto_nuevo != 0:
                    st.session_state.extras.append({"concepto": concepto_nuevo, "monto": monto_nuevo})
                    st.rerun()
                else:
                    st.warning("Debes ingresar un nombre y un monto válido.")

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

        st.markdown("---")
        total_final = st.session_state.comision_base + total_extras
        st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>TOTAL A RECIBIR:<br>${total_final:,.2f}</h1>", unsafe_allow_html=True)

        # --- 4. ZONA DE GUARDADO EN LA NUBE ---
        st.markdown("---")
        st.header("3. Respaldo en la Nube")
        
        if st.button("💾 Guardar Registro en Drive", use_container_width=True):
            try:
                # Conexión con el archivo específico de Drive
                url_hoja = "https://docs.google.com/spreadsheets/d/1zSY4fs77m-wNln45IEgGmNNE29KNUQdFP99hyCIZw2s/edit"
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                # Intentar leer la base histórica
                df_historico = conn.read(spreadsheet=url_hoja, usecols=[0, 1, 2, 3, 4])
                
                # Crear la nueva fila con los datos de hoy
                nueva_fila = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Vendedor": "Antonio Enrique Martínez Toledo",
                    "Comision_Base": round(st.session_state.comision_base, 2),
                    "Total_Ajustes": round(total_extras, 2),
                    "Total_Final": round(total_final, 2)
                }])
                
                # Agregar y actualizar la hoja
                df_actualizado = pd.concat([df_historico, nueva_fila], ignore_index=True)
                conn.update(spreadsheet=url_hoja, data=df_actualizado)
                
                st.success("✅ ¡El registro de este cálculo se ha guardado permanentemente en tu Google Drive!")
            except Exception as e:
                st.error("Error al sincronizar con Drive. Asegúrate de configurar los permisos del archivo para que cualquiera con el enlace pueda editar.")
