# Battle Bots - GA driven Neural Network Agents 
# main rev 0.2

<img width="760" height="814" src="https://github.com/user-attachments/assets/79f178d2-2cce-4211-b4da-09c0bbd17e6f" />
*Early version testing*

---

Usage: `python main.py`  
*Removing `*.npy` files will reset to `0` or copy over the `blue.npy` & `red.npy` files*  


## File Structures

```
/src/config.py            # central config data
/src/audio.py             # primitive audio driver, 16-channels, capped n-samples per frame
/src/main.py              # main application file
/src/models.py            # structural classes
/src/sfx/*                # raw audio files
/src/samples/*            # pre-trained network (numpy) artifacts, grouped by layout sequence
/src/samples/36-38-4/*    # Network revision artifacts: 0.4 (initial prototypes)
/src/samples/36-42-4/*    # Network revision artifacts: 0.5 (planned: HeatMap/MapData awareness)

/src/ai/__init__.py   
/src/ai/genetics.py       # genetic algorithm operators, selection, crossover, mutation
/src/ai/network.py        # neural network class and back-propagation logic
/src/ai/population.py     # discrete team & population management

/src/core/__init__.py
/src/core/heatmap.py      # (not implemented yet)
/src/core/physics.py      # physics engine for movement, collision, and obstacle interactions
/src/core/sensors.py      # sensor system for agent perception via raycasting
/src/core/simulation.py   # main simulation management 
/src/core/world.py        # world state management, spawning, and arena rules

/src/renderer/__init__.py
/src/renderer/hud.py      # visual interface, helpers, debuggers
/src/renderer/renderer.py # render harness for PyGame
```

## Neural Networks

sub-rev: 0.4
```
  # 8 Rays * 4 Channels (32) + Health + Cooldown + Boost Charge + Bias = 36 Inputs (booster added)
  # Outputs: Move, Turn, Shoot, Boost = 4 Outputs
  N_IN, N_HID, N_OUT = 36, 38, 4
  N_WEIGHTS = N_IN * N_HID + N_HID + N_HID * N_OUT + N_OUT
```

sub-rev: 0.5 Map Data (Planned)
```
  # 8 Rays * 5 Channels (Wall, Enemy, Teammate, Bullet, Death) = 40
  # + Health + Cooldown + Boost Charge + Bias = 44 Inputs
  # Outputs: Move, Turn, Shoot, Boost = 4 Outputs
  #N_IN, N_HID, N_OUT = 44, 46, 4
  #N_WEIGHTS = N_IN * N_HID + N_HID + N_HID * N_OUT + N_OUT
```
