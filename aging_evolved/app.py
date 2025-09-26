import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import time
import threading
import random

from evolution import Evolution
from utils import load_config

CONFIG_PATH = "/Users/wojciechciezobka/projects/aging-evolved/aging_evolved/configs/test_config.yml"

# --- 2. Create Global Instance and a Thread Lock ---
# This object will be shared between the simulation thread and Dash callbacks.
config = load_config(CONFIG_PATH)
max_episodes = config.pop("episodes", 100)
refresh_rate = config.pop("refresh_rate", 200)
simulation_speed = config.pop("simulation_speed", 0)

print(f"max_episodes: {max_episodes}, refresh_rate: {refresh_rate}, simulation_speed: {simulation_speed}")


evolution = Evolution(**config)
lock = threading.Lock()

# --- 3. Define the App Layout (Same as before) ---
app = dash.Dash(__name__)
app.layout = html.Div(children=[
    html.H1(children='Evolution Simulator Dashboard'),
    dcc.Interval(
        id='interval-component',
        interval=refresh_rate,
        n_intervals=0,
        max_intervals=max_episodes  # Stop after max_episodes
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

# --- 4. Define the Callback to READ Data ---
@app.callback(
    [Output('graph-1', 'figure'), Output('graph-2', 'figure'),
     Output('graph-3', 'figure'), Output('graph-4', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    # The callback now only reads the data. The simulation runs elsewhere.
    with lock: # Use the lock to safely read data
        # Create a deep copy of the data to avoid issues while plotting
        episodes = evolution.history.episodes[:]
        population_size = evolution.history.population_size[:]

    # Create figures (same plotting logic as before)
    print(f"Updating for the {n}th time")
    fig1 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Population Size'))
    fig2 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Average Fitness'))
    fig3 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Genetic Diversity'))
    fig4 = go.Figure(data=go.Scatter(x=episodes, y=population_size, mode='lines'),
                     layout=go.Layout(title='Environment Hostility'))

    return fig1, fig2, fig3, fig4

# --- 5. Define the function that runs the simulation loop ---
def run_simulation_loop():
    """This function runs in a background thread."""
    while True:
        with lock: # Use lock to safely update data
            evolution.step()
        time.sleep(simulation_speed / 1000)

# --- 6. Run the App and Start the Thread ---
if __name__ == '__main__':
    # Start the simulation loop in a background thread
    sim_thread = threading.Thread(target=run_simulation_loop)
    sim_thread.daemon = True  # Allows main thread to exit even if this thread is running
    sim_thread.start()
    
    # Run the Dash app
    # IMPORTANT: Use debug=False when using background threads
    app.run(debug=False)