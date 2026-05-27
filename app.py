import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd

# 1. Simulación de Datos (Capa de Datos temporal)
# Esto es lo que luego se conectará a la BD Relacional de Claudio
inventario_inicial = [
    {"id": 1, "producto": "Arroz Costeño 1kg", "categoria": "Abarrotes", "precio": 4.50, "stock": 50},
    {"id": 2, "producto": "Leche Gloria Azul", "categoria": "Lácteos", "precio": 4.20, "stock": 30},
    {"id": 3, "producto": "Aceite Primor 1L", "categoria": "Abarrotes", "precio": 11.00, "stock": 15},
]
df_inventario = pd.DataFrame(inventario_inicial)

# 2. Inicializar la App de Dash
app = dash.Dash(__name__, title="Control de Bodega")

# 3. Diseño de la Interfaz (Frontend)
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#f4f6f9'}, children=[
    
    html.H1("Sistema de Gestión: Bodega Digital", style={'textAlign': 'center', 'color': '#2c3e50'}),
    html.Hr(),
    
    # Sección de Formulario para Registrar Venta / Modificar Stock
    html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'marginBottom': '20px', 'boxShadow': '0px 2px 4px rgba(0,0,0,0.1)'}, children=[
        html.H3("Registrar Movimiento de Inventario", style={'marginTop': '0', 'color': '#34495e'}),
        html.Div(style={'display': 'flex', 'gap': '15px', 'flexWrap': 'wrap'}, children=[
            html.Div([
                html.Label("ID del Producto:"),
                dcc.Input(id='input-id', type='number', placeholder='Ej. 1', style={'padding': '8px', 'width': '100px'})
            ]),
            html.Div([
                html.Label("Cantidad a Vender/Retirar:"),
                dcc.Input(id='input-cantidad', type='number', placeholder='Ej. 5', style={'padding': '8px', 'width': '150px'})
            ]),
            html.Button('Registrar Venta', id='btn-venta', n_clicks=0, style={
                'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'padding': '10px 20px', 'borderRadius': '4px', 'cursor': 'pointer', 'alignSelf': 'flex-end'
            })
        ]),
        html.Div(id='output-mensaje', style={'marginTop': '15px', 'fontWeight': 'bold', 'color': '#27ae60'})
    ]),
    
    # Tabla de Inventario en Tiempo Real
    html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0px 2px 4px rgba(0,0,0,0.1)'}, children=[
        html.H3("Inventario Actual", style={'marginTop': '0', 'color': '#34495e'}),
        dash_table.DataTable(
            id='tabla-inventario',
            columns=[{"name": i.capitalize(), "id": i} for i in df_inventario.columns],
            data=df_inventario.to_dict('records'),
            style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'},
            style_cell={'padding': '10px', 'textAlign': 'left'},
            style_data_conditional=[{
                'if': {'column_id': 'stock', 'filter_query': '{stock} < 20'},
                'backgroundColor': '#ffdfdf', 'color': '#c0392b'
            }]
        )
    ])
])

# 4. Lógica del Servidor / Callbacks (Backend)
@app.callback(
    [Output('tabla-inventario', 'data'),
     Output('output-mensaje', 'children')],
    Input('btn-venta', 'n_clicks'),
    [State('input-id', 'value'),
     State('input-cantidad', 'value')]
)
def actualizar_inventario(n_clicks, prod_id, cantidad):
    global df_inventario
    if n_clicks == 0 or prod_id is None or cantidad is None:
        return df_inventario.to_dict('records'), ""
    
    # Buscar el producto en el DataFrame
    if prod_id in df_inventario['id'].values:
        idx = df_inventario[df_inventario['id'] == prod_id].index[0]
        stock_actual = df_inventario.loc[idx, 'stock']
        
        if stock_actual >= cantidad:
            # Restar del inventario (Simulación de Venta)
            df_inventario.loc[idx, 'stock'] = stock_actual - cantidad
            producto_nombre = df_inventario.loc[idx, 'producto']
            mensaje = f"✅ Venta registrada: {cantidad} unid. de '{producto_nombre}'."
        else:
            mensaje = "❌ Error: Stock insuficiente para realizar la venta."
    else:
        mensaje = "❌ Error: ID de producto no encontrado."
        
    return df_inventario.to_dict('records'), mensaje

# 5. Ejecutar Servidor
if __name__ == '__main__':
    # Usamos el puerto 8050 por defecto de Dash
    app.run(debug=True, host='0.0.0.0', port=8050)