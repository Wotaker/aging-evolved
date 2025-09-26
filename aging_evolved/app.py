import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import time
import threading

# Assuming Evolution and load_config are available
from evolution import Evolution
from utils import load_config 

# --- Configuration (Use your actual path/values) ---
CONFIG_PATH = "/Users/wojciechciezobka/projects/aging-evolved/aging_evolved/configs/test_config.yml"

config = load_config(CONFIG_PATH)

max_episodes = config.pop("episodes", 100)
refresh_rate = config.pop("refresh_rate", 100)
simulation_speed = config.pop("simulation_speed", 500)

# --- Global State for Thread Communication ---
# These are initialized to None/False and populated upon button click.
evolution = None
lock = threading.Lock()
evolution_running = False 

# --- Define the App Layout ---
app = dash.Dash(__name__)
app.layout = html.Div(children=[
    html.H1(children='Evolution Simulator Dashboard'),
    
    html.Button('Start Simulation', id='start-button', n_clicks=0),
    
    # Stores a flag indicating if the thread has been started
    dcc.Store(id='sim-started-flag', data=False),

    # Interval starts as disabled
    dcc.Interval(
        id='interval-component',
        interval=refresh_rate,
        n_intervals=0,
        disabled=True
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

# --- Callback for Starting the Simulation Thread ---
@app.callback(
    [Output('sim-started-flag', 'data'),  
     Output('start-button', 'disabled'),  
     Output('interval-component', 'disabled')], 
    [Input('start-button', 'n_clicks')],
    [State('sim-started-flag', 'data')]
)
def start_simulation(n_clicks, sim_started):
    global evolution, evolution_running, config
    
    if n_clicks > 0 and not sim_started:
        
        # 1. Re-initialize global simulation state (ensures a fresh run)
        local_config = load_config(CONFIG_PATH)
        local_config.pop("episodes", 100)
        local_config.pop("refresh_rate", 100)
        local_config.pop("simulation_speed", 500)
        evolution = Evolution(**local_config)
        evolution_running = True
        
        # 2. Start the simulation thread
        sim_thread = threading.Thread(target=run_simulation_loop)
        sim_thread.daemon = True
        sim_thread.start()
        
        # 3. Return outputs: mark as started, disable button, enable interval
        return True, True, False
    
    return sim_started, (n_clicks > 0), True

# --- The Simulation Loop ---
def run_simulation_loop():
    """Runs the simulation steps in a background thread."""
    global evolution_running 
    
    while evolution.episode_count < max_episodes: 
        with lock: 
            evolution.step()
        # Sleep time is in seconds
        time.sleep(simulation_speed / 1000)

    # Signal the end of the simulation
    with lock:
        evolution_running = False 

# --- Update Callback (Plotting and Termination Control) ---
@app.callback(
    [Output('graph-1', 'figure'), Output('graph-2', 'figure'),
     Output('graph-3', 'figure'), Output('graph-4', 'figure'),
     Output('interval-component', 'disabled', allow_duplicate=True)],
    [Input('interval-component', 'n_intervals')],
    [State('interval-component', 'disabled'),
     State('sim-started-flag', 'data')],
    prevent_initial_call=True
)
def update_graphs(n, is_disabled, sim_started):
    global evolution_running 

    # Do nothing if the simulation hasn't been started by the button
    if not sim_started:
        return (dash.no_update, ) * 5
    
    # 1. Read Data safely
    with lock:
        episodes = evolution.history.episodes[:]
        population_size = evolution.history.population_size[:]
        sim_is_running = evolution_running 

    # 2. Check for Termination Signal (set timer to disabled if sim is finished)
    timer_disabled = True if not sim_is_running and not is_disabled else is_disabled
        
    # 3. Create Figures
    fig1 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Population Size'))
    fig2 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Average Fitness'))
    fig3 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Genetic Diversity'))
    fig4 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Environment Hostility'))

    return fig1, fig2, fig3, fig4, timer_disabled


# --- Run the App ---
if __name__ == '__main__':
    # The thread is started only upon the button click in the callback
    app.run(debug=False)