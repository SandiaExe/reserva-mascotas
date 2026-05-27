import jwt
import datetime
import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd

# Importamos la Capa de Datos y Seguridad
from db import (
    SessionLocal, Reserva, Dueno, Mascota,
    cifrar_dato, descifrar_dato,
    inicializar_base_de_datos,
    verificar_credenciales
)

# Intentar crear las tablas al arrancar el contenedor
try:
    inicializar_base_de_datos()
except Exception as e:
    print(f"Esperando a que la base de datos esté lista... ({e})")

# Clave secreta para firmar los tokens JWT (en producción, usar variable de entorno)
JWT_SECRET = "clave_secreta_academica"

# --- Función para consultar reservas desde PostgreSQL ---
def obtener_calendario_reservas():
    db = SessionLocal()
    try:
        reservas_db = db.query(Reserva).all()
        datos_limpios = []
        for r in reservas_db:
            mascota_obj = r.mascota
            dueno_obj   = mascota_obj.dueno

            # Desciframos el dato sensible en tiempo de ejecución para mostrarlo
            tel_descifrado = descifrar_dato(dueno_obj.telefono_cifrado)

            datos_limpios.append({
                "id_reserva":       r.id_reserva,
                "mascota":          f"{mascota_obj.nombre_mascota} ({mascota_obj.especie})",
                "dueño":            f"{dueno_obj.nombre} (Tel: {tel_descifrado})",
                "fecha_ingreso":    str(r.fecha_ingreso),
                "dieta_restriccion": r.dieta_restriccion
            })
        return pd.DataFrame(datos_limpios)
    except Exception as e:
        print(f"Error al leer BD: {e}")
        return pd.DataFrame(columns=["id_reserva", "mascota", "dueño", "fecha_ingreso", "dieta_restriccion"])
    finally:
        db.close()

# --- Inicializar la Aplicación Dash ---
app = dash.Dash(__name__, title="Control Guardería Exótica")

# --- Estilos reutilizables ---
ESTILO_CARD = {
    'backgroundColor': 'white',
    'padding': '20px',
    'borderRadius': '8px',
    'marginBottom': '20px',
    'boxShadow': '0px 2px 4px rgba(0,0,0,0.05)'
}

# --- Layout de la Aplicación ---
app.layout = html.Div(
    style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#fcfaf7'},
    children=[

        html.H1(
            "Plataforma de Gestión: Guardería de Animales Exóticos 🦎🦉",
            style={'textAlign': 'center', 'color': '#2c3e50'}
        ),

        # ── Token JWT almacenado en memoria del navegador (invisible) ──
        dcc.Store(id='store-token', storage_type='memory'),

        # ── Panel de Login ─────────────────────────────────────────────
        html.Div(
            id='panel-login',
            style={**ESTILO_CARD, 'maxWidth': '360px', 'margin': '40px auto'},
            children=[
                html.H3("Iniciar Sesión", style={'textAlign': 'center', 'color': '#2c3e50', 'marginTop': '0'}),

                html.Label("Usuario:"),
                dcc.Input(
                    id='input-usuario', type='text', placeholder='Ej. boris',
                    style={'width': '100%', 'padding': '8px', 'marginBottom': '12px', 'boxSizing': 'border-box'}
                ),

                html.Label("Contraseña:"),
                dcc.Input(
                    id='input-password', type='password', placeholder='••••••••',
                    style={'width': '100%', 'padding': '8px', 'marginBottom': '16px', 'boxSizing': 'border-box'}
                ),

                html.Button(
                    'Ingresar', id='btn-login', n_clicks=0,
                    style={
                        'width': '100%', 'backgroundColor': '#2c3e50', 'color': 'white',
                        'border': 'none', 'padding': '10px', 'borderRadius': '4px', 'cursor': 'pointer'
                    }
                ),

                html.Div(id='mensaje-login', style={'marginTop': '12px', 'color': 'red', 'textAlign': 'center'})
            ]
        ),

        # ── Contenido principal (oculto hasta hacer login) ─────────────
        html.Div(
            id='contenido-principal',
            style={'display': 'none'},
            children=[
                html.Hr(),

                # Formulario de registro de reservas
                html.Div(style=ESTILO_CARD, children=[
                    html.H3(
                        "Programar Cita de Cuidado / Actualizar Dieta Específica",
                        style={'marginTop': '0', 'color': '#16a085'}
                    ),
                    html.Div(
                        style={'display': 'flex', 'gap': '15px', 'flexWrap': 'wrap'},
                        children=[
                            html.Div([
                                html.Label("ID Reserva:"),
                                html.Br(),
                                dcc.Input(id='input-id-reserva', type='number', placeholder='Ej. 104',
                                          style={'padding': '8px', 'width': '100px'})
                            ]),
                            html.Div([
                                html.Label("Mascota y Especie:"),
                                html.Br(),
                                dcc.Input(id='input-mascota', type='text', placeholder='Ej. Spike (Erizo)',
                                          style={'padding': '8px', 'width': '200px'})
                            ]),
                            html.Div([
                                html.Label("Dueño:"),
                                html.Br(),
                                dcc.Input(id='input-dueno', type='text', placeholder='Ej. Juan Pérez',
                                          style={'padding': '8px', 'width': '150px'})
                            ]),
                            html.Div([
                                html.Label("Fecha Ingreso:"),
                                html.Br(),
                                dcc.Input(id='input-fecha', type='text', placeholder='AAAA-MM-DD',
                                          style={'padding': '8px', 'width': '120px'})
                            ]),
                            html.Div([
                                html.Label("Restricción Alimentaria / Dieta:"),
                                html.Br(),
                                dcc.Input(id='input-dieta', type='text', placeholder='Detalles de alimentación...',
                                          style={'padding': '8px', 'width': '350px'})
                            ]),
                            html.Button(
                                'Registrar Reserva', id='btn-registrar', n_clicks=0,
                                style={
                                    'backgroundColor': '#16a085', 'color': 'white',
                                    'border': 'none', 'padding': '10px 20px',
                                    'borderRadius': '4px', 'cursor': 'pointer', 'alignSelf': 'flex-end'
                                }
                            )
                        ]
                    ),
                    html.Div(id='output-mensaje-reserva', style={'marginTop': '15px', 'fontWeight': 'bold', 'color': '#27ae60'})
                ]),

                # Tabla de reservas activas
                html.Div(style=ESTILO_CARD, children=[
                    html.H3("Calendario de Reservas y Dietas Activas", style={'marginTop': '0', 'color': '#2c3e50'}),
                    dash_table.DataTable(
                        id='tabla-reservas',
                        columns=[
                            {"name": "ID Reserva",                    "id": "id_reserva"},
                            {"name": "Mascota (Especie)",              "id": "mascota"},
                            {"name": "Dueño / Contacto",              "id": "dueño"},
                            {"name": "Fecha de Ingreso",              "id": "fecha_ingreso"},
                            {"name": "Restricción Alimentaria / Dieta", "id": "dieta_restriccion"}
                        ],
                        data=obtener_calendario_reservas().to_dict('records'),
                        style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'},
                        style_cell={'padding': '12px', 'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
                        style_data_conditional=[{
                            'if': {
                                'column_id': 'dieta_restriccion',
                                'filter_query': '{dieta_restriccion} contains "Estricta"'
                            },
                            'backgroundColor': '#fff2cc', 'color': '#b78103', 'fontWeight': 'bold'
                        }]
                    )
                ])
            ]
        )
    ]
)

# ── Callback 1: Manejo de Login ────────────────────────────────────────────────
@app.callback(
    [Output('store-token',         'data'),
     Output('panel-login',         'style'),
     Output('contenido-principal', 'style'),
     Output('mensaje-login',       'children')],
    Input('btn-login', 'n_clicks'),
    [State('input-usuario',  'value'),
     State('input-password', 'value')],
    prevent_initial_call=True
)
def manejar_login(n_clicks, usuario, password):
    """
    Valida credenciales con bcrypt.
    Si son correctas: genera un token JWT, oculta el login y muestra el contenido.
    Si son incorrectas: muestra mensaje de error y mantiene el login visible.
    """
    estilo_login_visible    = {**ESTILO_CARD, 'maxWidth': '360px', 'margin': '40px auto'}
    estilo_login_oculto     = {'display': 'none'}
    estilo_contenido_visible = {'display': 'block'}
    estilo_contenido_oculto  = {'display': 'none'}

    if not usuario or not password:
        return None, estilo_login_visible, estilo_contenido_oculto, "⚠️ Ingresa usuario y contraseña."

    if verificar_credenciales(usuario, password):
        # Generar token JWT con tiempo de expiración de 1 hora
        payload = {
            "sub": usuario,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        return token, estilo_login_oculto, estilo_contenido_visible, ""
    else:
        return None, estilo_login_visible, estilo_contenido_oculto, "❌ Usuario o contraseña incorrectos."


# ── Callback 2: Registro de Reservas ──────────────────────────────────────────
@app.callback(
    [Output('tabla-reservas',        'data'),
     Output('output-mensaje-reserva', 'children')],
    Input('btn-registrar', 'n_clicks'),
    [State('input-id-reserva', 'value'),
     State('input-mascota',    'value'),
     State('input-dueno',      'value'),
     State('input-fecha',      'value'),
     State('input-dieta',      'value'),
     State('store-token',      'data')],   # Verifica que el token JWT exista
)
def gestionar_reservas(n_clicks, id_res, masc, owner, date, dieta, token):
    """
    Registra una nueva reserva en PostgreSQL.
    Cifra los datos de contacto del dueño con Fernet antes de guardarlos.
    Solo opera si existe un token JWT válido en el store.
    """
    df_actual = obtener_calendario_reservas()

    # Verificar que el usuario esté autenticado
    if not token:
        return df_actual.to_dict('records'), "⛔ Acceso denegado: no hay sesión activa."

    # Validar que el token JWT no haya expirado
    try:
        jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return df_actual.to_dict('records'), "⛔ Sesión expirada. Por favor, vuelve a iniciar sesión."
    except jwt.InvalidTokenError:
        return df_actual.to_dict('records'), "⛔ Token inválido."

    if n_clicks == 0 or id_res is None or not masc or not owner or not date or not dieta:
        return df_actual.to_dict('records'), ""

    if id_res in df_actual['id_reserva'].values:
        return df_actual.to_dict('records'), f"❌ Error: El ID de Reserva {id_res} ya está ocupado."

    db = SessionLocal()
    try:
        fecha_valida = datetime.datetime.strptime(date, "%Y-%m-%d").date()

        # Cifrar datos sensibles con Fernet antes de guardar en la BD
        telefono_cifrado = cifrar_dato("999-EXOTIC-CARE")
        correo_cifrado   = cifrar_dato(f"{owner.lower().replace(' ', '')}@mail.com")

        # Parsear "Nombre (Especie)" si viene en ese formato
        if "(" in masc and ")" in masc:
            nom_m, esp_m = masc.replace(")", "").split("(")
            nom_m, esp_m = nom_m.strip(), esp_m.strip()
        else:
            nom_m, esp_m = masc, "Exótica"

        # Crear registros relacionales mediante el ORM
        nuevo_dueno   = Dueno(nombre=owner, correo_cifrado=correo_cifrado, telefono_cifrado=telefono_cifrado)
        nueva_mascota = Mascota(nombre_mascota=nom_m, especie=esp_m, dueno=nuevo_dueno)
        nueva_reserva = Reserva(id_reserva=id_res, fecha_ingreso=fecha_valida, dieta_restriccion=dieta, mascota=nueva_mascota)

        db.add(nuevo_dueno)
        db.add(nueva_mascota)
        db.add(nueva_reserva)
        db.commit()

        df_actual = obtener_calendario_reservas()
        return df_actual.to_dict('records'), f"✅ Reserva {id_res} guardada en PostgreSQL con datos cifrados."

    except Exception as e:
        db.rollback()
        return df_actual.to_dict('records'), f"❌ Error transaccional: {str(e)}"
    finally:
        db.close()


# --- Ejecutar Servidor ---
if __name__ == '__main__':
    import os
    puerto = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host='0.0.0.0', port=puerto)
