import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ==============================================================================
# 1. CARGA Y TRATAMIENTO DE DATOS (Lógica de tu script original)
# ==============================================================================
print("--- Cargando Dataset de Fondos (FICs) ---")
url_datos = "https://www.datos.gov.co/resource/qhpu-8ixx.json"
# Limitamos a 30,000 para mantener el dashboard rápido en la nube
df = pd.read_json(f"{url_datos}?$limit=30000")

# Conversión de tipos numéricos
cols_numericas = ['aportes_recibidos', 'retiros_redenciones', 
                  'valor_unidad_operaciones', 'numero_inversionistas', 
                  'rentabilidad_diaria']

for col in cols_numericas:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Conversión de fecha
df['fecha_corte'] = pd.to_datetime(df['fecha_corte'])

# Limpieza de nulos y creación de variable clave
df_tratado = df.dropna(subset=['aportes_recibidos', 'retiros_redenciones', 'rentabilidad_diaria'])
df_tratado['Flujo_Neto'] = df_tratado['aportes_recibidos'] - df_tratado['retiros_redenciones']

# Filtramos rentabilidades absurdas (errores de digitación mayores al 50% diario) para que las gráficas se vean bien
df_tratado = df_tratado[df_tratado['rentabilidad_diaria'].between(-0.5, 0.5)]

print("--- Datos cargados y limpios ---")

# ==============================================================================
# 2. CONFIGURACIÓN DE LA APP DASH
# ==============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # <--- AGREGA ESTA LÍNEA OBLIGATORIAMENTE
app.title = "FICs Colombia Analytics"
server = app.server # Necesario para despliegue en Render

# Paleta de colores Financiera (Verde/Azul/Morado)
colors = {
    'background': 'rgba(0,0,0,0)',
    'text': '#e2e8f0',
    'green': '#34d399',  # Rentabilidad
    'blue': '#3b82f6',   # Aportes
    'red': '#f87171',    # Retiros
    'purple': '#8b5cf6'
}

# ==============================================================================
# 3. DISEÑO (LAYOUT)
# ==============================================================================
app.layout = dbc.Container([
    dbc.Row([
        
        # --- BARRA LATERAL (FILTROS) ---
        dbc.Col([
            html.Div([
                html.H4("FICs Analytics", className="gradient-text mb-4", style={'fontSize': '1.8rem'}),
                html.P("Monitor de Fondos de Inversión Colectiva", className="text-white-50 mb-5"),
                
                html.Label("FILTRAR POR TIPO DE FONDO", className="kpi-title"),
                dcc.Dropdown(
                    id='filtro-tipo',
                    options=[{'label': str(i), 'value': i} for i in df_tratado['nombre_subtipo_patrimonio'].unique()],
                    placeholder="Todos los fondos...",
                    className="mb-4"
                ),

                html.Label("FILTRAR POR ENTIDAD", className="kpi-title"),
                dcc.Dropdown(
                    id='filtro-entidad',
                    options=[{'label': str(i), 'value': i} for i in df_tratado['nombre_entidad'].unique()[:50]],
                    placeholder="Seleccione Entidad...",
                    className="mb-4"
                ),
                
                html.Div([
                    html.Hr(style={'borderColor': 'rgba(255,255,255,0.1)'}),
                    html.Small("Datos: Superintendencia Financiera de Colombia via datos.gov.co", className="text-white-50"),
                ], style={'marginTop': 'auto'})
                
            ], className="filter-panel d-flex flex-column")
        ], width=12, lg=3, className="p-0 m-0"),

        # --- CONTENIDO PRINCIPAL ---
        dbc.Col([
            # Título
            dbc.Row([
                dbc.Col(html.H2("Visión de Mercado", className="text-white fw-bold mt-4 mb-4"), width=12),
            ]),
            
            # FILA DE KPIs (Tarjetas de Cristal)
            dbc.Row([
                dbc.Col(html.Div([
                    html.H6("FLUJO NETO TOTAL", className="kpi-title"),
                    html.H3(id="kpi-flujo", className="kpi-value", style={'color': colors['blue']})
                ], className="glass-card h-100"), width=12, md=4, className="mb-4"),
                
                dbc.Col(html.Div([
                    html.H6("RENTABILIDAD PROM. DIA", className="kpi-title"),
                    html.H3(id="kpi-rentabilidad", className="kpi-value", style={'color': colors['green']})
                ], className="glass-card h-100"), width=12, md=4, className="mb-4"),
                
                dbc.Col(html.Div([
                    html.H6("INVERSIONISTAS ACTIVOS", className="kpi-title"),
                    html.H3(id="kpi-inversionistas", className="kpi-value", style={'color': colors['purple']})
                ], className="glass-card h-100"), width=12, md=4, className="mb-4"),
            ]),

            # GRÁFICA 1: SERIE DE TIEMPO (Sentimiento de Mercado)
            dbc.Row([
                dbc.Col(html.Div([
                    html.Div([
                        html.H5("Sentimiento de Mercado (Flujo Neto)", className="fw-bold mb-0"),
                        html.Small("Evolución de entradas (Aportes) vs Salidas (Retiros)", className="text-white-50")
                    ], className="mb-3"),
                    dcc.Graph(id="grafica-serie", style={"height": "350px"}, config={'displayModeBar': False})
                ], className="glass-card mb-4"), width=12)
            ]),

            # FILA INFERIOR DE GRÁFICAS
            dbc.Row([
                # GRÁFICA 2: HISTOGRAMA (Distribución de Riesgo/Rentabilidad)
                dbc.Col(html.Div([
                    html.H5("Distribución de Rentabilidad", className="fw-bold mb-3"),
                    dcc.Graph(id="grafica-hist", style={"height": "350px"}, config={'displayModeBar': False})
                ], className="glass-card mb-4"), width=12, lg=6),

                # GRÁFICA 3: SCATTER 3D (Análisis Multidimensional)
                dbc.Col(html.Div([
                    html.H5("Mapa de Inversión (3D)", className="fw-bold mb-3"),
                    dcc.Graph(id="grafica-3d", style={"height": "350px"}, config={'displayModeBar': True})
                ], className="glass-card mb-4"), width=12, lg=6),
            ]),
            
            dbc.Row([
                dbc.Col(html.Small("Dashboard desarrollado con Python Dash & Plotly.", className="text-muted text-center d-block mb-4"), width=12)
            ])

        ], width=12, lg=9, className="px-4")
    ], className="g-0")
], fluid=True, style={'minHeight': '100vh'})


# ==============================================================================
# 4. LÓGICA (CALLBACKS)
# ==============================================================================
@app.callback(
    [Output("kpi-flujo", "children"), Output("kpi-rentabilidad", "children"), Output("kpi-inversionistas", "children"),
     Output("grafica-serie", "figure"), Output("grafica-hist", "figure"), Output("grafica-3d", "figure")],
    [Input("filtro-tipo", "value"), Input("filtro-entidad", "value")]
)
def update_dashboard(tipo_fondo, entidad):
    # 1. Filtrar datos
    dff = df_tratado.copy()
    if tipo_fondo:
        dff = dff[dff['nombre_subtipo_patrimonio'] == tipo_fondo]
    if entidad:
        dff = dff[dff['nombre_entidad'] == entidad]
    
    if dff.empty: return "0", "0%", "0", {}, {}, {}

    # 2. Calcular KPIs
    flujo_total = dff['Flujo_Neto'].sum()
    rent_promedio = dff['rentabilidad_diaria'].mean() * 100 # En porcentaje
    total_inversores = dff['numero_inversionistas'].max() # Tomamos el maximo registrado en el periodo

    # Formato KPIs
    kpi_f = f"${flujo_total/1e9:,.1f} B" if abs(flujo_total) > 1e9 else f"${flujo_total/1e6:,.1f} M"
    kpi_r = f"{rent_promedio:,.2f}%"
    kpi_i = f"{total_inversores:,.0f}"

    # 3. GRÁFICAS

    # A) SERIE DE TIEMPO (Flujo Neto)
    # Agrupamos por fecha para sumar aportes de todos los fondos seleccionados
    df_tiempo = dff.groupby('fecha_corte')['Flujo_Neto'].sum().reset_index()
    fig_serie = px.line(df_tiempo, x='fecha_corte', y='Flujo_Neto', 
                        title="Dinámica de Liquidez Diaria",
                        color_discrete_sequence=[colors['blue']])
    # Añadimos área bajo la curva para efecto "neón"
    fig_serie.update_traces(fill='tozeroy', line=dict(width=3))
    fig_serie.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font_color=colors['text'],
        xaxis_title="", yaxis_title="Flujo Neto (COP)",
        margin=dict(l=20, r=20, t=30, b=20)
    )

    # B) HISTOGRAMA (Rentabilidad) - Reemplaza el análisis de normalidad de SciPy
    fig_hist = px.histogram(dff, x="rentabilidad_diaria", nbins=50,
                            marginal="box", # Boxplot arriba
                            color_discrete_sequence=[colors['green']],
                            title="Volatilidad")
    fig_hist.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font_color=colors['text'],
        showlegend=False,
        xaxis_title="Rentabilidad Diaria",
        margin=dict(l=20, r=20, t=30, b=20)
    )

    # C) SCATTER 3D (Aportes vs Retiros vs Inversionistas)
    # Para que no sea muy pesado, tomamos una muestra si hay muchos datos
    sample_dff = dff.sample(min(1000, len(dff))) 
    fig_3d = px.scatter_3d(sample_dff, x='aportes_recibidos', y='retiros_redenciones', z='rentabilidad_diaria',
                           color='nombre_subtipo_patrimonio', size='numero_inversionistas',
                           size_max=20, opacity=0.8,
                           color_discrete_sequence=px.colors.qualitative.Bold)
    fig_3d.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font_color=colors['text'],
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor='rgba(255,255,255,0.1)', title="Aportes"),
            yaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor='rgba(255,255,255,0.1)', title="Retiros"),
            zaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor='rgba(255,255,255,0.1)', title="Rentabilidad")
        )
    )

    return kpi_f, kpi_r, kpi_i, fig_serie, fig_hist, fig_3d

# ==============================================================================
# 5. EJECUCIÓN
# ==============================================================================
if __name__ == '__main__':
    app.run(debug=True, port=8050)
