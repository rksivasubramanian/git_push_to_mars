# 🚀 Git Push to Mars — Space Mission Design Game

![NASA Space Apps Challenge](https://img.shields.io/badge/NASA_Space_Apps-2026_Challenge-0B3D91?style=for-the-badge&logo=nasa)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Engine-Pygame_2.x-00C853?style=for-the-badge)
![GMAT Aligned](https://img.shields.io/badge/Astrodynamics-NASA_GMAT_Aligned-FC3D21?style=for-the-badge)

**Team:** Git Push to Mars  
**Challenge:** 2026 NASA Space Apps Challenge — *Space Mission Design Game*

An interactive **4-tab Systems Engineering Mission Studio and 4-player cooperative Mission Control simulator** built in Python and Pygame. Inspired by NASA's **General Mission Analysis Tool (GMAT)**, **JPL Horizons** ephemeris data, and the **NASA Planetary Data System (PDS)**, *Git Push to Mars* lets solo players or teams of up to four participants design spacecraft, balance six interdependent engineering resources, fly multi-body orbital trajectories, resolve mid-mission anomalies, and export valid GMAT `.script` files.

---

## 📋 Table of Contents
1. [Complete Setup Instructions (From Scratch)](#1-complete-setup-instructions-from-scratch)
2. [How to Play & Step-by-Step Walkthrough](#2-how-to-play--step-by-step-walkthrough)
3. [Keyboard & Mouse Controls](#3-keyboard--mouse-controls)
4. [The 6-Resource Systems Engineering Model](#4-the-6-resource-systems-engineering-model)
5. [4-Player Cooperative Mission Control Stations](#5-4-player-cooperative-mission-control-stations)
6. [NASA Data & GMAT Physics Architecture](#6-nasa-data--gmat-physics-architecture)
7. [Troubleshooting (macOS, VS Code & Retina Displays)](#7-troubleshooting-macos-vs-code--retina-displays)

---

## 1. Complete Setup Instructions (From Scratch)

Follow these steps from a brand-new machine or terminal window to install Python dependencies and launch the simulator.

### Step 1: Verify Python 3.9+ is Installed
Open **Terminal** (on macOS/Linux) or **Command Prompt / PowerShell** (on Windows) and check your Python version:
```bash
python3 --version
```
*(If Python is not installed, download Python 3.11 or 3.12 from [python.org](https://www.python.org/downloads/) or run `brew install python` on macOS).*

### Step 2: Clone or Create the Project Folder
If cloning from GitHub:
```bash
git clone [https://github.com/](https://github.com/)<your-username>/git-push-to-mars.git
cd git-push-to-mars
```
Or if starting in a local folder containing `git_push_to_mars.py`:
```bash
cd /path/to/your/project-folder
```

### Step 3: Create and Activate a Virtual Environment
Creating a `.venv` virtual environment keeps `pygame` isolated and prevents macOS `externally-managed-environment` or `No module named 'pygame'` errors:

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (PowerShell):**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 4: Install Pygame
Upgrade `pip` and install `pygame` inside the active virtual environment:
```bash
python -m pip install --upgrade pip
python -m pip install pygame
```
*(Note: If you are using Python 3.13+ on Apple Silicon macOS and see an SDL2 wheel compilation error, run `python -m pip install pygame-ce` instead—it is a drop-in precompiled replacement).*

### Step 5: Run the Game
```bash
python git_push_to_mars.py
```

---

## 2. How to Play & Step-by-Step Walkthrough

### Phase 1: Configure Your Mission (4-Tab Design Studio)
The game opens in the **4-Tab Mission Design Studio** (`1100x640` MacBook-safe resolution):
* **Tab 1 — `1. OBJECTIVE, ORBIT & LAUNCH`:**
  * **Step 1A:** Select one of the 4 mission scenarios (*Earth Climate & Albedo Observatory*, *Lunar Polar Ice & Relay Scout*, *Mars Atmospheric & Subsurface Explorer*, or *Sandbox Mode*).
  * **Step 1B:** Select your target orbit (`LEO`, `SSO`, `GEO`, `LUNAR`, or `MARS`).
  * **Step 1C:** Choose a Launch Vehicle (*Electron-Class*, *Falcon 9-Class*, *Falcon Heavy*, or *SLS*) and adjust your **Planned Mission Lifetime** (`-0.5 yr` / `+0.5 yr`).
* **Tab 2 — `2. SPACE & GROUND SEGMENTS`:**
  * **Step 2A:** Select your Spacecraft Bus (*Standard Aluminum* vs. *Composite Rad-Hard*), Propulsion system (*Monopropellant*, *Bipropellant NTO/MMH*, or *Solar Electric SEP*), **Propellant Mass** (`-100 kg` / `+100 kg`), and **Solar Array Area** (`-2 m²` / `+2 m²`).
  * **Step 2B:** Select your NASA Deep Space Network (DSN) communications link (*S-Band Omni*, *X-Band High-Gain*, or *Ka-Band & Optical*).
* **Tab 3 — `3. PDS SCIENCE PAYLOADS`:**
  * Mount up to **3 NASA PDS scientific instruments** (*HiRISE Surface Imager*, *SHARAD Subsurface Ice Radar*, *TES IR Spectrometer*, *MAVEN Magnetometer*, or *MOLA LiDAR Altimeter*). Watch the bottom **6-Resource Dashboard** update in real time as each sensor adds mass, power draw, cost, and daily data volume.
* **Tab 4 — `4. 4-PLAYER ROLES & SIGN-OFF`:**
  * Review the competing engineering priorities across the 4 Mission Control stations and click **`APPROVED [READY]`** for each station.

### Phase 2: Launch into Live Orbital Flight
* Click either green **`LAUNCH MISSION`** button (top-right bar or bottom-right dashboard), or press **`ENTER`**, **`SPACEBAR`**, or **`TAB`** on your keyboard.
* Your spacecraft (`GitPushSat`) spawns in Low Earth orbit with live multi-body gravitational physics (Sun, Earth, and Mars) and a dashed GMAT trajectory prediction curve.
* Press **`T`** (or click **`EXECUTE GMAT MARS TRANSFER BURN`**) to fire your Trans-Mars Injection burn and watch your trajectory curve outward toward Mars's Sphere of Influence (SOI). *(Note: AI Autopilot will also execute this transfer burn automatically at `T+0.08 yrs` if you don't press anything).*
* Use **`Warp 1x / 2x / 5x / 10x`** to control simulation speed, and press **`F9`** at any time during a live demo to trigger a **Solar Flare Radiation Surge** team negotiation event.

### Phase 3: Post-Mission Debrief & Leaderboard
* When Mission Elapsed Time (`MET`) reaches your planned lifetime (or when you click **`COMPLETE MISSION & VIEW SCORE DEBRIEF`**), the game calculates your **Total Score (`/ 1000 pts`)** and **Mission Grade (`S` / `A`)**.
* Review the engineering diagnostic lessons explaining how your power balance, DSN comms link, and budget reserves performed, then click **`VIEW LEADERBOARD`** to compare your run against past designs.

---

## 3. Keyboard & Mouse Controls

| Key / Input | Screen | Action |
| :--- | :--- | :--- |
| **`ENTER` / `SPACE`** | Design / Debrief / History | **Launch Mission** immediately into Live Orbital Flight |
| **`TAB`** | Any Screen | Toggle instantly between **4-Tab Design Studio** $\leftrightarrow$ **Live Flight** |
| **`1` / `2` / `3` / `4`** | Design Studio | Switch between Configuration Tabs `1` through `4` |
| **`1` / `2` / `3` / `4`** | Live Flight | Switch active Mission Control Station (`1:FDO`, `2:BUS`, `3:SCI`, `4:COM`) |
| **`T`** | Live Flight | Execute GMAT **Trans-Mars Injection (TMI)** prograde transfer burn |
| **`F9`** | Live Flight | Trigger deterministic **Solar Flare Radiation Surge** team decision event |
| **`R`** | Live Flight | Reset orbital trajectory back to `T+0.00 yrs` at Earth |
| **Left Mouse Click** | All Screens | Click any hardware card, resource button, time-warp setting, or event choice |

---

## 4. The 6-Resource Systems Engineering Model

Every design decision in the studio and during flight is evaluated across six coupled aerospace constraints:

| Card | Resource | Engineering Rule & Coupled Trade-Off |
| :--- | :--- | :--- |
| **`1. MASS`** | Wet Mass (`kg`) | Dry bus + propulsion + antenna + solar wings + instruments + fuel must fit within the selected **Launch Vehicle's** payload limit for the target orbit. |
| **`2. POWER`** | Electrical Balance (`W` / `Wh`) | Solar array generation (scaled by $1/r^2$ solar distance—43% flux at Mars—and orbital eclipse fraction) must exceed continuous bus, comms, payload, and SEP thruster draw. |
| **`3. BUDGET`** | Total Cost (`$M`) | Launch vehicle + spacecraft bus + propulsion + comms + instruments + operations (`$14M/yr`) must stay within the scenario funding cap. |
| **`4. DATA GEN`** | Recorder Input (`Gb/day`) | Active PDS instruments fill the onboard `120 Gb` solid-state data buffer; buffer overflow permanently loses science data. |
| **`5. COMMS CAP`** | DSN Downlink (`Gb/day`) | Ground-station downlink capacity (`S-Band`, `X-Band`, or `Ka-Band/Optical` scaled by orbital distance) must keep pace with daily instrument data generation. |
| **`6. TIME & dV`** | Lifetime (`yrs`) & $\Delta v$ (`m/s`) | Onboard propellant must satisfy the **Tsiolkovsky Rocket Equation** ($\Delta v = I_{sp} g_0 \ln(m_0/m_f)$) for orbital insertion plus multi-year station-keeping. |

---

## 5. 4-Player Cooperative Mission Control Stations

Up to four participants can collaborate on the same mission by dividing responsibilities across the four NASA Mission Control stations:

1. **Station 1 — `FDO` (Mission Planner & Flight Dynamics):** Selects the target orbit and launch vehicle, manages the $\Delta v$ propellant budget, executes orbital transfer burns (`[T]`), and controls simulation time-warp.
2. **Station 2 — `BUS` (Spacecraft & Power Engineer):** Sizes solar arrays and batteries for Mars's $43\%$ solar irradiance and planetary eclipses, and toggles **Safe Mode** during Solar Flare radiation storms.
3. **Station 3 — `SCI` (Lead Payload Scientist):** Selects up to 3 complementary NASA PDS instruments and manages sensor duty cycles (`Sensors: ON / PAUSED`) to maximize science points without overflowing the data recorder.
4. **Station 4 — `COM` (DSN Comms & Operations Director):** Selects the Deep Space Network dish/band (`11m Near-Earth`, `34m Waveguide`, or `70m + Optical`), monitors downlink throughput, and manages the operations budget reserve.

---

## 6. NASA Data & GMAT Physics Architecture

* **NASA GMAT (General Mission Analysis Tool) Alignment:** Uses real-time numerical trajectory propagation across coupled gravitational fields ($\mu_{\text{Sun}}, \mu_{\text{Earth}}, \mu_{\text{Mars}}$) with a 140-step forward trajectory predictor. Clicking **`GMAT .script`** in the top bar exports a valid `git_push_to_mars_mission.script` file containing `Spacecraft`, `ChemicalTank`, `ChemicalThruster`, `GroundStation`, and `RungeKutta89` blocks.
* **NASA JPL Horizons Ephemeris Parameters:** Orbits use real semi-major axes (`SMA`), inclinations (`INC`), and heliocentric distances ($1.000\text{ AU}$ for Earth/Lunar, $1.524\text{ AU}$ and $586\text{ W/m}^2$ solar irradiance for Mars).
* **NASA Planetary Data System (PDS) Payloads:** Instrument mass, power, and data-rate profiles are modeled after flight-proven NASA instruments (**HiRISE**, **SHARAD**, **TES**, **MAVEN MAG**, and **MOLA/LOLA**).

### Generated Files
* `git_push_to_mars_mission.script`: Exported NASA GMAT mission script created when you click **`GMAT .script`**.
* `git_push_to_mars_history.json`: Persistent local leaderboard file storing your top 12 completed mission runs.

---

## 7. Troubleshooting (macOS, VS Code & Retina Displays)

* **`ModuleNotFoundError: No module named 'pygame'` when clicking the VS Code Play Button:**
  * VS Code is running macOS's global `/usr/bin/python3` instead of your `.venv`. Press **`Cmd + Shift + P`** in VS Code, type **`Python: Select Interpreter`**, and select **`./.venv/bin/python`**, or run `./.venv/bin/python git_push_to_mars.py` directly in the terminal.
* **VS Code runs an older cached version of the file:**
  * Press **`Cmd + S`** to save the active tab (ensure the solid dot next to the filename disappears), or enable **File $\rightarrow$ Auto Save** in the top menu bar.
* **Window size or mouse alignment on MacBook Retina screens:**
  * The script automatically sets `os.environ["SDL_VIDEO_HIGHDPI_DISABLED"] = "1"`, uses a compact `1100x640` window that fits cleanly above the macOS Dock, and normalizes mouse click coordinates against `pygame.display.get_window_size()`.