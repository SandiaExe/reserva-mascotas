import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
from datetime import datetime

# Importamos tu Capa de Datos y Seguridad
from db import SessionLocal, Reserva, Dueno, Mascota, cifrar_dato, descifrar_dato, inicializar_base_de_datos

# Intentar crear las tablas al arrancar el contenedor
try:
    inicializar_base_de_datos()
except Exception as e:
    print(f"Esperando a que la base de datos esté lista... ({e})")

# Función para consultar los datos reales de PostgreSQL mediante SQLAlchemy
def obtener_calendario_reservas():
    db = SessionLocal()
    try:
        reservas_db = db.query(Reserva).all()
        datos_limpios = []
        for r in reservas_db:
            mascota_obj = r.mascota
            dueno_obj = Glen_obj = mascota_obj.dueno
            
            # Desciframos el dato sensible en tiempo de ejecución para mostrarlo en la interfaz
            tel_descifrado = descifrar_dato(dueno_obj.telefono_cifrado)
            
            datos_limpios.append({
                "id_reserva": r.id_reserva,
                "mascota": f"{mascota_obj.nombre_mascota} ({mascota_obj.especie})",
                "dueño": f"{dueno_obj.nombre} (Tel: {tel_descifrado})",
                "fecha_ingreso": str(r.fecha_ingreso),
                "dieta_restriccion": r.dieta_restriccion
            })
        return pd.DataFrame(datos_limpios)
    except Exception as e:
        print(f"Error al leer BD: {e}")
        return pd.DataFrame(columns=["id_reserva", "mascota", "dueño", "fecha_ingreso", "dieta_restriccion"])
    finally:
        db.close()

# 2. Inicializar la Aplicación de Dash
app = dash.Dash(__name__, title="Control Guardería Exótica")

# 3. Diseño de la Interfaz Visual (Frontend de la Capa de Aplicación - Mantenido de tus compañeros)
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#fcfaf7'}, children=[
    html.H1("Plataforma de Gestión: Guardería de Animales Exóticos 🦎🦉", style={'textAlign': 'center', 'color': '#2c3e50'}),
    html.Hr(),
    
    html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'marginBottom': '20px', 'boxShadow': '0px 2px 4px rgba(0,0,0,0.05)'}, children=[
        html.H3("Programar Cita de Cuidado / Actualizar Dieta Específica", style={'marginTop': '0', 'color': '#16a085'}),
        html.Div(style={'display': 'flex', 'gap': '15px', 'flexWrap': 'wrap'}, children=[
            html.Div([html.Label("ID Reserva:"), html.Br(), dcc.Input(id='input-id-reserva', type='number', placeholder='Ej. 104', style={'padding': '8px', 'width': '100px'})]),
            html.Div([html.Label("Mascota y Especie:"), html.Br(), dcc.Input(id='input-mascota', type='text', placeholder='Ej. Spike (Erizo)', style={'padding': '8px', 'width': '200px'})]),
            html.Div([html.Label("Dueño:"), html.Br(), dcc.Input(id='input-dueno', type='text', placeholder='Ej. Juan Pérez', style={'padding': '8px', 'width': '150px'})]),
            html.Div([html.Label("Fecha Ingreso:"), html.Br(), dcc.Input(id='input-fecha', type='text', placeholder='AAAA-MM-DD', style={'padding': '8px', 'width': '120px'})]),
            html.Div([html.Label("Restricción Alimentaria / Dieta:"), html.Br(), dcc.Input(id='input-dieta', type='text', placeholder='Detalles de alimentación...', style={'padding': '8px', 'width': '350px'})]),
            html.Button('Registrar Reserva', id='btn-registrar', n_clicks=0, style={'backgroundColor': '#16a085', 'color': 'white', 'border': 'none', 'padding': '10px 20px', 'borderRadius': '4px', 'cursor': 'pointer', 'alignSelf': 'flex-end'})
        ]),
        html.Div(id='output-mensaje-reserva', style={'marginTop': '15px', 'fontWeight': 'bold', 'color': '#27ae60'})
    ]),
    
    html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0px 2px 4px rgba(0,0,0,0.05)'}, children=[
        html.H3("Calendario de Reservas y Dietas Activas", style={'marginTop': '0', 'color': '#2c3e50'}),
        dash_table.DataTable(
            id='tabla-reservas',
            columns=[
                {"name": "ID Reserva", "id": "id_reserva"},
                {"name": "Mascota (Especie)", "id": "mascota"},
                {"name": "Dueño / Contacto", "id": "dueño"},
                {"name": "Fecha de Ingreso", "id": "fecha_ingreso"},
                {"name": "Restricción Alimentaria / Dieta", "id": "dieta_restriccion"}
            ],
            data=obtener_calendario_reservas().to_dict('records'), # Carga dinámica inicial
            style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'},
            style_cell={'padding': '12px', 'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
            style_data_conditional=[{
                'if': {'column_id': 'dieta_restriccion', 'filter_query': '{dieta_restriccion} contains "Estricta"'},
                'backgroundColor': '#fff2cc', 'color': '#b78103', 'fontWeight': 'bold'
            }]
        )
    ])
])

# 4. Lógica del Servidor / Callbacks (Modificado con SQLAlchemy ORM real)
@app.callback(
    [Output('tabla-reservas', 'data'),
     Output('output-mensaje-reserva', 'children')],
    Input('btn-registrar', 'n_clicks'),
    [State('input-id-reserva', 'value'),
     State('input-mascota', 'value'),
     State('input-dueno', 'value'),
     State('input-fecha', 'value'),
     State('input-dieta', 'value')]
)
def gestionar_reservas(n_clicks, id_res, masc, owner, date, dieta):
    df_actual = obtener_calendario_reservas()
    if n_clicks == 0 or id_res is None or not masc or not owner or not date or not dieta:
        return df_actual.to_dict('records'), ""
    
    if id_res in df_actual['id_reserva'].values:
        return df_actual.to_dict('records'), f"❌ Error: El ID de Reserva {id_res} ya está ocupado."
    
    db = SessionLocal()
    try:
        # Formatear la fecha ingresada
        fecha_valida = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Cifrar datos sensibles antes de enviarlos a la BD (Capa de Seguridad en Reposo)
        telefono_cifrado = cifrar_dato("999-EXOTIC-CARE")
        correo_cifrado = cifrar_dato(f"{owner.lower().replace(' ', '')}@mail.com")
        
        # Procesar cadena de Mascota para separar Nombre y Especie si viene como "Spike (Erizo)"
        if "(" in masc and ")" in masc:
            nom_m, esp_m = masc.replace(")", "").split("(")
            nom_m, esp_m = nom_m.strip(), esp_m.strip()
        else:
            nom_m, esp_m = masc, "Exótica"

        # Crear registros vinculados relacionalmente mediante el ORM
        nuevo_dueno = Dueno(nombre=owner, correo_cifrado=correo_cifrado, telefono_cifrado=telefono_cifrado)
        nueva_mascota = Mascota(nombre_mascota=nom_m, especie=esp_m, dueno=nuevo_dueno)
        nueva_reserva = Reserva(id_reserva=id_res, fecha_ingreso=fecha_valida, dieta_restriccion=dieta, mascota=nueva_mascota)
        
        # Agregar a la sesión y confirmar la transacción
        db.add(nuevo_dueno)
        db.add(nueva_mascota)
        db.add(nueva_reserva)
        db.commit()
        
        # Retornar la tabla actualizada leyendo directo de la BD
        df_actual = obtener_calendario_reservas()
        return df_actual.to_dict('records'), f"✅ Reserva {id_res} guardada en PostgreSQL de forma relacional."
    except Exception as e:
        db.rollback()
        return df_actual.to_dict('records'), f"❌ Error transaccional: {str(e)}"
    finally:
        db.close()

# 5. Ejecutar Servidor
if __name__ == '__main__':
    import os
    # Railway asigna un puerto dinámico en la nube. Si no existe, usa el 8050 por defecto.
    puerto = int(os.environ.get("PORT", 8050))
    
    # IMPORTANTE: Desactivamos el debug en producción para evitar que se cuelgue el contenedor
    app.run(debug=False, host='0.0.0.0', port=puerto)
