import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import time
import threading

# Assuming Evolution and load_config are available
from evolution import Evolution
from utils import load_config 

CONFIG_PATH = "/Users/wojciechciezobka/projects/aging-evolved/aging_evolved/configs/test_config.yml"

# --- 1. Global State and Configuration ---
config = load_config(CONFIG_PATH)

max_episodes = config.pop("episodes", 100)
refresh_rate = config.pop("refresh_rate", 100)
simulation_speed = config.pop("simulation_speed", 500) # Sim time per step in ms

evolution = Evolution(**config)
lock = threading.Lock()
evolution_running = True # Flag to control the background thread

# --- 2. Define the App Layout ---
app = dash.Dash(__name__)
app.layout = html.Div(children=[
    html.H1(children='Aging Evolved Simulator Dashboard'),
    
    dcc.Interval(
        id='interval-component',
        interval=refresh_rate,
        n_intervals=0,
    ),
    
    html.Div(
        className='graph-container',
        children=[
            dcc.Graph(id='graph-1'), dcc.Graph(id='graph-2'),
            dcc.Graph(id='graph-3'), dcc.Graph(id='graph-4'),
        ],
        style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr'}
    )
])

# --- 3. Define the Callback to READ Data and CONTROL Termination ---
@app.callback(
    [Output('graph-1', 'figure'), Output('graph-2', 'figure'),
     Output('graph-3', 'figure'), Output('graph-4', 'figure'),
     Output('interval-component', 'disabled')], # Output to disable the timer
    [Input('interval-component', 'n_intervals')],
    [State('interval-component', 'disabled')] # State to check current disabled status
)
def update_graphs(n, is_disabled):
    global evolution_running 

    # 1. Read Data
    with lock:
        episodes = evolution.history.episodes[:]
        population_size = evolution.history.population_size[:]
        sim_is_running = evolution_running 

    # 2. Check for Termination Signal
    if not sim_is_running and not is_disabled:
        # Simulation finished, disable the timer
        timer_disabled = True
    else:
        # Simulation running or timer already disabled
        timer_disabled = is_disabled
        
    # 3. Create Figures
    fig1 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Population Size'))
    fig2 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Average Fitness'))
    fig3 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Genetic Diversity'))
    fig4 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Environment Hostility'))

    # Return the figures and the new state of the timer
    return fig1, fig2, fig3, fig4, timer_disabled

# --- 4. Define the Simulation Loop ---
def run_simulation_loop():
    """This function runs in a background thread and controls termination."""
    global evolution_running 
    
    while evolution.episode < max_episodes: 
        with lock: 
            evolution.step()
        # Sleep time is in seconds, so divide simulation_speed (ms) by 1000
        time.sleep(simulation_speed / 1000)

    # Signal the end of the simulation
    with lock:
        evolution_running = False 

# --- 5. Run the App and Start the Thread ---
if __name__ == '__main__':
    sim_thread = threading.Thread(target=run_simulation_loop)
    sim_thread.daemon = True
    sim_thread.start()
    
    # Use debug=False when using background threads
    app.run(debug=False)
