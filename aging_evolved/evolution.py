from dataclasses import dataclass, field
from typing import List

@dataclass
class History:
    """Holds the history of simulation metrics over episodes."""
    episodes: List[int] = field(default_factory=list)
    population_size: List[int] = field(default_factory=list)

class Evolution:

    def __init__(
        self,
        initial_population_size: int = 1000,
        death_rate_external: float = 0.05,
        reproduction_rate: float = 1.0
    ):
        
        # Simulation parameters from config
        self.initial_population_size = initial_population_size
        self.death_rate_external = death_rate_external
        self.reproduction_rate = reproduction_rate

        # Metrics to track over time
        self.episode_count = 0
        self.population_size = self.initial_population_size
        self.history: History = History()
        self._update_history()

    def _update_history(self):
        """Records the current state of the simulation."""
        self.history.episodes.append(self.episode_count)
        self.history.population_size.append(self.population_size)

    def step(self):
        self.episode_count += 1

        # Simple simulation logic for demonstration purposes
        # 1. Mutation
        
        # 2. Reproduction
        self.population_size += int(self.population_size * self.reproduction_rate)

        # 3. Death
        self.population_size = int(self.population_size * (1 - self.death_rate_external))

        # Record the state after this step
        self._update_history()
