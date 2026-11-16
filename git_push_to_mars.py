"""
===============================================================================
TEAM: Git Push to Mars
PROJECT: NASA Space Apps Challenge 2026 - Space Mission Design Game
FILE: git_push_to_mars.py (Unified with working mars_live.py Flight Engine)
CONTROLS:
  - Click [LAUNCH MISSION] or press [ENTER / SPACE / TAB] to toggle Design <-> Flight
  - Press [1, 2, 3, 4] to switch Design Tabs or Mission Control Stations
  - Press [T] in Flight for GMAT Trans-Mars Injection Burn (or let Autopilot fire)
  - Press [F9] in Flight to trigger a live Solar Flare team negotiation event
  - Press [R] in Flight to reset the orbital trajectory
DEPENDENCIES: Python 3.9+, pygame (pip install pygame)
===============================================================================
"""

import json
import math
import os
import random
import sys
import time

# Ensure 1:1 mouse coordinate mapping on macOS Retina displays
os.environ["SDL_VIDEO_HIGHDPI_DISABLED"] = "1"
import pygame

# -----------------------------------------------------------------------------
# 1. GLOBAL CONSTANTS & COLORS (1100x640 — FITS ALL MACBOOK SCREENS)
# -----------------------------------------------------------------------------
WIDTH, HEIGHT = 1100, 640
FPS = 60
G0 = 9.80665
SOLAR_1AU = 1361.0
HISTORY_FILE = "git_push_to_mars_history.json"
GMAT_FILE = "git_push_to_mars_mission.script"

BG_DARK = (9, 13, 22)
PANEL_BG = (16, 23, 38)
CARD_BG = (23, 33, 52)
BORDER = (46, 66, 98)
TEXT_MAIN = (234, 242, 255)
TEXT_MUTED = (146, 166, 198)
CYAN = (56, 189, 248)
GREEN = (52, 211, 153)
AMBER = (251, 191, 36)
RED = (248, 113, 113)
PURPLE = (167, 139, 250)

# GMAT Scaled Orbital Physics Parameters
MU_SUN = 2.8e7
MU_EARTH = 1.6e5
MU_MARS = 9.5e4
R_EARTH = 145.0
R_MARS = 230.0

# -----------------------------------------------------------------------------
# 2. NASA DATA-BACKED MISSION & HARDWARE CATALOGS
# -----------------------------------------------------------------------------
DIFFICULTY_LEVELS = [
    {"name": "Cadet (Guided)", "budget_mult": 1.30, "sci_mult": 1.15},
    {"name": "Engineer (Standard)", "budget_mult": 1.00, "sci_mult": 1.00},
    {"name": "Flight Director (Hard)", "budget_mult": 0.82, "sci_mult": 0.90},
]

SCENARIOS = [
    {
        "id": "EARTH_CLIMATE",
        "name": "Earth Climate & Albedo Observatory",
        "orbit": "SSO",
        "body": "Earth",
        "budget": 260.0,
        "sci_target": 140.0,
        "min_life": 3.0,
        "summary": "Monitor polar ice sheets and aerosols from Sun-Synchronous Orbit (EOS ref).",
        "focus": "High Data Generation & Ground Downlink",
        "edu": "JPL Ref: SSO passes over every latitude at constant local solar time.",
    },
    {
        "id": "LUNAR_SCOUT",
        "name": "Lunar Polar Ice & Relay Scout",
        "orbit": "LUNAR",
        "body": "Moon",
        "budget": 320.0,
        "sci_target": 175.0,
        "min_life": 2.0,
        "summary": "Map permanently shadowed lunar craters for water ice (VIPER PDS ref).",
        "focus": "Trans-Lunar Delta-V & Launch Capacity",
        "edu": "JPL Horizons Ref: Lunar orbit requires ~4,050 m/s delta-v from LEO.",
    },
    {
        "id": "MARS_EXPLORER",
        "name": "Mars Atmospheric & Subsurface Explorer",
        "orbit": "MARS",
        "body": "Mars",
        "budget": 460.0,
        "sci_target": 210.0,
        "min_life": 2.5,
        "summary": "Transfer to Mars (1.524 AU), capture into orbit, and map subsurface ice.",
        "focus": "Propellant Mass, Solar Flux (43%) & DSN Comms",
        "edu": "JPL Horizons Ref: At Mars (1.524 AU), solar flux drops to 43% (586 W/m^2).",
    },
    {
        "id": "SANDBOX",
        "name": "Sandbox Mode (Open Systems Lab)",
        "orbit": "ANY",
        "body": "Any",
        "budget": 9999.0,
        "sci_target": 100.0,
        "min_life": 1.0,
        "summary": "Experiment freely without budget caps across any orbit, rocket, and payload.",
        "focus": "Open Experimentation & GMAT Script Export",
        "edu": "Sandbox removes funding caps for testing extreme instrument stacks.",
    },
]

ORBITS = [
    {"code": "LEO", "name": "Low Earth Orbit (400 km | ISS)", "body": "Earth", "sma": 6778.1, "inc": 51.6, "dv": 250.0, "solar": 1.00, "eclipse": 0.36, "comms": 1.40, "edu": "Low launch energy and strong signal; 36% of every orbit in shadow."},
    {"code": "SSO", "name": "Sun-Synchronous (705 km | EOS)", "body": "Earth", "sma": 7083.1, "inc": 98.2, "dv": 650.0, "solar": 1.00, "eclipse": 0.22, "comms": 1.25, "edu": "Constant local solar lighting angle for global polar climate imaging."},
    {"code": "GEO", "name": "Geostationary Orbit (35,786 km)", "body": "Earth", "sma": 42164.1, "inc": 0.1, "dv": 3950.0, "solar": 1.00, "eclipse": 0.05, "comms": 0.90, "edu": "Continuous 24/7 hemisphere view; requires high circularization delta-V."},
    {"code": "LUNAR", "name": "Lunar Polar Orbit (100 km | LRO)", "body": "Luna", "sma": 1837.4, "inc": 89.8, "dv": 4050.0, "solar": 1.00, "eclipse": 0.30, "comms": 0.55, "edu": "384,400 km away; requires Trans-Lunar Injection and Lunar Orbit Insertion."},
    {"code": "MARS", "name": "Mars Science Orbit (300 km | MRO)", "body": "Mars", "sma": 3696.2, "inc": 92.7, "dv": 5100.0, "solar": 0.43, "eclipse": 0.32, "comms": 0.32, "edu": "1.524 AU distance (43% solar flux); requires high dV and Deep Space Network."},
]

ROCKETS = [
    {"name": "SmallSat Light (Electron-Class)", "cost": 16.0, "cap": {"LEO": 320, "SSO": 240, "GEO": 0, "LUNAR": 0, "MARS": 0}, "edu": "Low cost ($16M) for compact LEO/SSO satellites; cannot reach deep space."},
    {"name": "Medium Reusable (Falcon 9-Class)", "cost": 65.0, "cap": {"LEO": 2400, "SSO": 1850, "GEO": 1150, "LUNAR": 950, "MARS": 820}, "edu": "Workhorse medium-lift rocket; launches <820 kg to Mars or <1,850 kg to SSO."},
    {"name": "Heavy-Lift Tri-Core (Falcon Heavy)", "cost": 115.0, "cap": {"LEO": 5800, "SSO": 4600, "GEO": 2900, "LUNAR": 2300, "MARS": 1950}, "edu": "High interplanetary capacity (1,950 kg to Mars) for multi-instrument orbiters."},
    {"name": "Super Heavy Deep-Space (SLS Ref)", "cost": 195.0, "cap": {"LEO": 12000, "SSO": 9500, "GEO": 6200, "LUNAR": 4800, "MARS": 4100}, "edu": "Flagship throw weight (4,100 kg to Mars) at high launch cost."},
]

BUS_OPTIONS = [
    {"name": "Standard Aluminum Bus (TRL-9)", "mass": 180.0, "batt": 900.0, "pwr": 65.0, "cost": 24.0, "edu": "Proven aluminum structure, 900 Wh battery pack, and reaction wheel ADCS."},
    {"name": "Composite Rad-Hard Bus (BAE)", "mass": 145.0, "batt": 1650.0, "pwr": 85.0, "cost": 52.0, "edu": "Carbon composite cuts dry mass by 35 kg and doubles battery to 1,650 Wh."},
]

PROP_OPTIONS = [
    {"name": "Monopropellant Hydrazine", "isp": 235.0, "thrust": 180.0, "mass": 95.0, "cost": 12.0, "pwr": 15.0, "edu": "Simple hydrazine thrusters for LEO/SSO; low Isp (235s)."},
    {"name": "Bipropellant NTO/MMH (HiPAT)", "isp": 322.0, "thrust": 440.0, "mass": 165.0, "cost": 28.0, "pwr": 25.0, "edu": "High-thrust planetary insertion engine (Isp 322s, 440 N) with low power draw."},
    {"name": "Solar Electric (NEXT-C SEP)", "isp": 1650.0, "thrust": 85.0, "mass": 210.0, "cost": 46.0, "pwr": 240.0, "edu": "Ultra-high Isp (1650s) slashes fuel mass, but draws 240 W of electrical power!"},
]

COMMS_OPTIONS = [
    {"name": "S-Band Omni (2 Mbps)", "rate": 2.0, "mass": 18.0, "pwr": 25.0, "cost": 10.0, "dish": "Near-Earth Net (11m)", "edu": "Low data rate (2 Mbps)—fine for telemetry, bottlenecks high-res imagers."},
    {"name": "X-Band High-Gain (18 Mbps)", "rate": 18.0, "mass": 36.0, "pwr": 55.0, "cost": 24.0, "dish": "DSN 34m Waveguide", "edu": "Standard Deep Space Network X-Band link (18 Mbps); balanced mass & throughput."},
    {"name": "Ka-Band & Optical (65 Mbps)", "rate": 65.0, "mass": 54.0, "pwr": 110.0, "cost": 48.0, "dish": "DSN 70m + Optical", "edu": "Ultra-fast 65 Mbps Ka-Band / Optical link; prevents recorder overflow."},
]

INSTRUMENTS = [
    {"id": "OPT_CAM", "name": "Multispectral Surface Imager (PDS HiRISE)", "mass": 48.0, "pwr": 42.0, "cost": 22.0, "data": 14.0, "sci": 65.0, "edu": "High-res visible/IR camera; delivers strong science with 14 Gb/day data."},
    {"id": "SAR_RADAR", "name": "Subsurface Ice Radar (PDS SHARAD)", "mass": 78.0, "pwr": 95.0, "cost": 38.0, "data": 22.0, "sci": 90.0, "edu": "Penetrates regolith to map buried water ice; heavy mass (78 kg) & power (95 W)."},
    {"id": "ATMOS_SPEC", "name": "IR Atmospheric Spectrometer (PDS TES)", "mass": 34.0, "pwr": 30.0, "cost": 19.0, "data": 6.5, "sci": 55.0, "edu": "Profiles greenhouse gases and aerosols with modest data volume (6.5 Gb/day)."},
    {"id": "MAG_PLASMA", "name": "Magnetometer & Plasma Suite (PDS MAVEN)", "mass": 22.0, "pwr": 18.0, "cost": 14.0, "data": 3.0, "sci": 42.0, "edu": "Lightweight (22 kg), low-power (18 W) magnetometer and solar wind sensor."},
    {"id": "LASER_ALT", "name": "Topographic LiDAR Altimeter (PDS MOLA)", "mass": 56.0, "pwr": 68.0, "cost": 31.0, "data": 11.0, "sci": 72.0, "edu": "Laser altimeter for 3D planetary elevation grids and polar ice thickness."},
]

STATIONS = [
    {"id": 0, "code": "FDO", "title": "Mission Planner & FDO", "prio": "Orbit fit, Launch capacity & dV margin", "col": CYAN},
    {"id": 1, "code": "BUS", "title": "Spacecraft & Power Eng.", "prio": "Solar/SEP power balance & eclipse battery", "col": GREEN},
    {"id": 2, "code": "SCI", "title": "Lead Payload Scientist", "prio": "PDS instrument synergy & target SOI science", "col": PURPLE},
    {"id": 3, "code": "COM", "title": "DSN Comms & Ops Director", "prio": "Downlink throughput > Data gen & Budget", "col": AMBER},
]


# -----------------------------------------------------------------------------
# 3. UNIFIED GAME ENGINE (4-TAB DESIGN STUDIO + LIVE ORBITAL FLIGHT)
# -----------------------------------------------------------------------------
class MarsMissionGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(
            "Team Git Push to Mars — [Click LAUNCH MISSION or Press ENTER / TAB to Fly]"
        )
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.f_title = pygame.font.SysFont("menlo,consolas,monospace", 14, bold=True)
        self.f_h2 = pygame.font.SysFont("menlo,consolas,monospace", 11, bold=True)
        self.f_body = pygame.font.SysFont("menlo,consolas,monospace", 10)
        self.f_small = pygame.font.SysFont("menlo,consolas,monospace", 9)

        # Design Studio Configuration State
        self.scen_idx = 2
        self.diff_idx = 1
        self.team_mode = True
        self.design_tab = 0  # 0:Objective/Orbit, 1:Bus/Comms, 2:Payloads, 3:Team Sign-Off
        self.orbit_idx = 4
        self.lv_idx = 2
        self.bus_idx = 1
        self.prop_idx = 1
        self.comms_idx = 1
        self.selected_insts = {"OPT_CAM", "ATMOS_SPEC"}
        self.fuel_cfg = 620.0
        self.solar_cfg = 12.0
        self.life_cfg = 2.5
        self.approved = [True, True, True, True]
        self.edu_text = "Configure your spacecraft and click LAUNCH MISSION (or press ENTER / SPACE)!"
        self.gmat_banner = ""

        # Starts on DESIGN studio; clicking LAUNCH MISSION (or pressing ENTER/SPACE/TAB) enters FLIGHT
        self.mode = "DESIGN"  # DESIGN | FLIGHT | DEBRIEF | HISTORY
        self.station = 0
        self.warp = 2
        self.autopilot = True
        self.buttons = []

        random.seed(42)
        self.stars = [
            (random.randint(20, 650), random.randint(20, 620), random.choice([(70, 90, 130), (120, 150, 200)]))
            for _ in range(90)
        ]
        self.reset_flight()

    def launch_mission(self):
        """Guaranteed Launch handler invoked by the Launch buttons or ENTER/SPACE keys."""
        if not self.selected_insts:
            self.selected_insts.add("OPT_CAM")
        self.approved = [True, True, True, True]
        self.reset_flight()
        self.mode = "FLIGHT"
        print(">>> [Git Push to Mars] LAUNCH MISSION triggered -> Active mode: FLIGHT <<<", flush=True)

    def compute_budget(self):
        sc = SCENARIOS[self.scen_idx]
        df = DIFFICULTY_LEVELS[self.diff_idx]
        orb = ORBITS[self.orbit_idx]
        lv = ROCKETS[self.lv_idx]
        bus = BUS_OPTIONS[self.bus_idx]
        prop = PROP_OPTIONS[self.prop_idx]
        com = COMMS_OPTIONS[self.comms_idx]
        insts = [i for i in INSTRUMENTS if i["id"] in self.selected_insts]

        inst_mass = sum(i["mass"] for i in insts)
        dry_mass = bus["mass"] + prop["mass"] + com["mass"] + inst_mass + self.solar_cfg * 3.8
        wet_mass = dry_mass + self.fuel_cfg
        max_pay = lv["cap"][orb["code"]]
        mass_ok = (max_pay > 0) and (wet_mass <= max_pay)

        cost = (
            lv["cost"]
            + bus["cost"]
            + prop["cost"]
            + com["cost"]
            + sum(i["cost"] for i in insts)
            + self.solar_cfg * 1.1
            + self.life_cfg * 14.0
        )
        cap = round(sc["budget"] * df["budget_mult"], 1)
        budget_ok = cost <= cap

        gen_w = self.solar_cfg * 280.0 * orb["solar"] * (1.0 - orb["eclipse"])
        draw_w = bus["pwr"] + com["pwr"] * 0.6 + sum(i["pwr"] for i in insts) * 0.75 + prop["pwr"] * 0.45
        pwr_ok = gen_w >= draw_w

        data_gen = sum(i["data"] for i in insts)
        downlink = (com["rate"] * orb["comms"] * 16200.0) / 8000.0
        comms_ok = downlink >= data_gen * 0.85

        dv_avail = prop["isp"] * G0 * math.log(wet_mass / max(1.0, dry_mass))
        dv_req = orb["dv"] + self.life_cfg * 45.0
        dv_ok = dv_avail >= dv_req

        sci_pot = sum(i["sci"] for i in insts) * df["sci_mult"]

        notes = []
        if not mass_ok:
            notes.append(f"Overweight ({int(wet_mass)}/{max_pay}kg)")
        if not budget_ok:
            notes.append(f"Over Budget (${cost:.0f}M/${cap:.0f}M)")
        if not pwr_ok:
            notes.append(f"Power Deficit ({int(gen_w)}W<{int(draw_w)}W)")
        if not comms_ok:
            notes.append("Comms Bottleneck")
        if not dv_ok:
            notes.append(f"Low dV ({int(dv_avail)}<{int(dv_req)}m/s)")

        return {
            "dry": dry_mass,
            "wet": wet_mass,
            "max_pay": max_pay,
            "mass_ok": mass_ok,
            "cost": cost,
            "cap": cap,
            "budget_ok": budget_ok,
            "gen_w": gen_w,
            "draw_w": draw_w,
            "pwr_ok": pwr_ok,
            "data_gen": data_gen,
            "downlink": downlink,
            "comms_ok": comms_ok,
            "dv_avail": dv_avail,
            "dv_req": dv_req,
            "dv_ok": dv_ok,
            "sci_pot": sci_pot,
            "notes": notes,
        }

    def export_gmat(self):
        b = self.compute_budget()
        orb = ORBITS[self.orbit_idx]
        prop = PROP_OPTIONS[self.prop_idx]
        com = COMMS_OPTIONS[self.comms_idx]
        script = f"""% NASA GMAT Script — Team Git Push to Mars
Create Spacecraft GitPushSat;
GMAT GitPushSat.CoordinateSystem = {orb['body']}MJ2000Eq;
GMAT GitPushSat.SMA = {orb['sma']:.2f};
GMAT GitPushSat.INC = {orb['inc']:.2f};
GMAT GitPushSat.DryMass = {b['dry']:.1f};
Create ChemicalTank MainTank;
GMAT MainTank.FuelMass = {self.fuel_cfg:.1f};
Create ChemicalThruster Engine;
GMAT Engine.C1 = {prop['thrust']:.1f};
GMAT Engine.K1 = {prop['isp']:.1f};
Create GroundStation DSN;
GMAT DSN.Id = '{com['dish']}';
BeginMissionSequence;
Propagate RK89Prop(GitPushSat) {{GitPushSat.ElapsedDays = {int(self.life_cfg * 365)}}};
"""
        with open(GMAT_FILE, "w", encoding="utf-8") as f:
            f.write(script)
        self.gmat_banner = f"Exported {GMAT_FILE}!"

    def reset_flight(self):
        b = self.compute_budget()
        orb = ORBITS[self.orbit_idx]
        prop = PROP_OPTIONS[self.prop_idx]
        bus = BUS_OPTIONS[self.bus_idx]

        self.earth_ang = 0.0
        self.mars_ang = math.radians(44.0)
        self.earth_w = math.sqrt(MU_SUN / (R_EARTH ** 3))
        self.mars_w = math.sqrt(MU_SUN / (R_MARS ** 3))

        self.ex = R_EARTH
        self.ey = 0.0
        self.mx = R_MARS * math.cos(self.mars_ang)
        self.my = R_MARS * math.sin(self.mars_ang)

        self.x = self.ex + 18.0
        self.y = self.ey
        v_orb = math.sqrt(MU_SUN / R_EARTH) + 22.0
        self.vx = 0.0
        self.vy = v_orb
        self.heading = math.pi / 2.0
        self.throttle = 0.0

        self.dry_mass = b["dry"]
        self.fuel = float(self.fuel_cfg)
        self.isp = prop["isp"]
        self.battery = bus["batt"]
        self.max_batt = bus["batt"]
        self.budget_rem = b["cap"] - b["cost"]
        self.data_buf = 8.0
        self.data_tx = 0.0
        self.data_lost = 0.0
        self.science = 0.0
        self.target_sci = SCENARIOS[self.scen_idx]["sci_target"]
        self.years = 0.0
        self.target_years = self.life_cfg
        self.health = 100.0
        self.safe_mode = False
        self.sensors_on = True
        self.dsn_on = True

        self.trail = [(self.x, self.y)]
        self.pred = []
        self.active_event = None
        self.transfer_done = False
        self.logs = [
            f"T+0.00y: Launched on {ROCKETS[self.lv_idx]['name'][:22]} into {orb['code']} mission.",
            "TIP: Press [TAB] for 4-Tab Design Studio | [T] Transfer Burn | [F9] Solar Flare.",
        ]
        self.update_prediction()

    def panel(self, rect, title=None, bd=BORDER):
        pygame.draw.rect(self.screen, PANEL_BG, rect, border_radius=6)
        pygame.draw.rect(self.screen, bd, rect, width=2, border_radius=6)
        if title:
            self.screen.blit(self.f_h2.render(title, True, CYAN), (rect.x + 8, rect.y + 5))

    def add_btn(self, rect, text, cb, active=False, col=CYAN):
        bg = (34, 62, 98) if active else CARD_BG
        bd = col if active else BORDER
        pygame.draw.rect(self.screen, bg, rect, border_radius=5)
        pygame.draw.rect(self.screen, bd, rect, width=2 if active else 1, border_radius=5)
        s = self.f_body.render(text, True, TEXT_MAIN)
        self.screen.blit(
            s,
            (rect.x + (rect.width - s.get_width()) // 2, rect.y + (rect.height - s.get_height()) // 2),
        )
        self.buttons.append((rect, cb))

    def wrap_text(self, text, x, y, max_w, font, col=TEXT_MUTED, lh=12):
        words = text.split(" ")
        line = ""
        cy = y
        for w in words:
            t = (line + " " + w).strip()
            if font.size(t)[0] <= max_w:
                line = t
            else:
                self.screen.blit(font.render(line, True, col), (x, cy))
                cy += lh
                line = w
        if line:
            self.screen.blit(font.render(line, True, col), (x, cy))

    def accel(self, px, py, ex, ey, mx, my):
        rs = math.hypot(px, py) + 1e-5
        ax = -MU_SUN * px / (rs ** 3)
        ay = -MU_SUN * py / (rs ** 3)
        de = math.hypot(px - ex, py - ey) + 1e-5
        if de < 55.0:
            ax -= MU_EARTH * (px - ex) / (de ** 3)
            ay -= MU_EARTH * (py - ey) / (de ** 3)
        dm = math.hypot(px - mx, py - my) + 1e-5
        if dm < 50.0:
            ax -= MU_MARS * (px - mx) / (dm ** 3)
            ay -= MU_MARS * (py - my) / (dm ** 3)
        return ax, ay

    def update_prediction(self):
        px, py, vx, vy = self.x, self.y, self.vx, self.vy
        ea, ma = self.earth_ang, self.mars_ang
        dt = 0.06
        pts = []
        for i in range(140):
            ea += self.earth_w * dt
            ma += self.mars_w * dt
            ex, ey = R_EARTH * math.cos(ea), R_EARTH * math.sin(ea)
            mx, my = R_MARS * math.cos(ma), R_MARS * math.sin(ma)
            ax, ay = self.accel(px, py, ex, ey, mx, my)
            vx += ax * dt
            vy += ay * dt
            px += vx * dt
            py += vy * dt
            if i % 2 == 0:
                pts.append((px, py))
        self.pred = pts

    def trigger_transfer_burn(self):
        if self.fuel <= 20:
            return
        spd = math.hypot(self.vx, self.vy) + 1e-5
        self.heading = math.atan2(self.vy, self.vx)
        self.vx += (self.vx / spd) * 24.0
        self.vy += (self.vy / spd) * 24.0
        self.fuel = max(0.0, self.fuel - 110.0)
        self.transfer_done = True
        self.logs.insert(0, f"T+{self.years:.2f}y: GMAT Trans-Mars Injection (TMI) Burn Executed!")
        self.update_prediction()

    def trigger_flare(self):
        self.active_event = {
            "title": "SOLAR FLARE RADIATION SURGE",
            "desc": "Coronal mass ejection inbound! High proton flux threatens avionics.",
            "a": "[BUS] Enter Safe Mode (Protects Bus Health, pauses sensors)",
            "b": "[SCI] Keep Sensors Active (+25 Science, -15% Bus Health)",
        }
        self.logs.insert(0, f"T+{self.years:.2f}y: ALERT — SOLAR FLARE RADIATION SURGE!")

    def resolve_event(self, choice):
        if not self.active_event:
            return
        if choice == "A":
            self.safe_mode = True
            self.logs.insert(0, "Team coordinated Safe Mode — spacecraft shielded.")
        else:
            self.science += 25.0
            self.health = max(10.0, self.health - 15.0)
            self.logs.insert(0, "Sensors kept active during flare (+25 Sci, -15% Health).")
        self.active_event = None

    def finish_mission(self):
        b = self.compute_budget()
        total_score = min(
            1000,
            int(420 + min(350, self.science * 1.6) + self.health * 1.3 + (80 if b["budget_ok"] else 20)),
        )
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            "scenario": SCENARIOS[self.scen_idx]["name"],
            "orbit": ORBITS[self.orbit_idx]["code"],
            "cost": b["cost"],
            "science": self.science,
            "total": total_score,
        }
        hist = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    hist = json.load(f)
            except Exception:
                hist = []
        hist.insert(0, entry)
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(hist[:12], f, indent=2)
        except Exception:
            pass
        self.mode = "DEBRIEF"

    def step_physics(self, real_dt):
        if self.mode != "FLIGHT":
            return

        if self.autopilot and not self.transfer_done and self.years > 0.08:
            self.trigger_transfer_burn()

        b = self.compute_budget()
        steps = 4 * self.warp
        dt = (real_dt * self.warp) / steps
        for _ in range(steps):
            self.earth_ang = (self.earth_ang + self.earth_w * dt) % (2 * math.pi)
            self.mars_ang = (self.mars_ang + self.mars_w * dt) % (2 * math.pi)
            self.ex = R_EARTH * math.cos(self.earth_ang)
            self.ey = R_EARTH * math.sin(self.earth_ang)
            self.mx = R_MARS * math.cos(self.mars_ang)
            self.my = R_MARS * math.sin(self.mars_ang)

            ax, ay = self.accel(self.x, self.y, self.ex, self.ey, self.mx, self.my)
            if self.throttle > 0 and self.fuel > 0:
                thrust_acc = (PROP_OPTIONS[self.prop_idx]["thrust"] * self.throttle) / (self.dry_mass + self.fuel)
                ax += thrust_acc * math.cos(self.heading)
                ay += thrust_acc * math.sin(self.heading)
                self.fuel = max(0.0, self.fuel - 12.0 * self.throttle * dt)

            self.vx += ax * dt
            self.vy += ay * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.heading = math.atan2(self.vy, self.vx)

            dyr = dt * 0.045
            self.years += dyr
            self.battery = max(100.0, min(self.max_batt, self.battery + (b["gen_w"] - b["draw_w"]) * dyr * 4.0))

            if self.sensors_on and not self.safe_mode:
                self.data_buf += b["data_gen"] * 2.2 * dyr
                if self.data_buf > 120.0:
                    self.data_lost += self.data_buf - 120.0
                    self.data_buf = 120.0
            if self.dsn_on and self.data_buf > 0:
                tx = min(self.data_buf, b["downlink"] * 2.5 * dyr)
                self.data_buf -= tx
                self.data_tx += tx
                self.science += (b["sci_pot"] / max(1.0, self.target_years)) * dyr * 1.15

            if self.years >= self.target_years:
                self.finish_mission()
                return

        if not self.trail or math.hypot(self.x - self.trail[-1][0], self.y - self.trail[-1][1]) > 3.0:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 300:
                self.trail.pop(0)
        self.update_prediction()

    # -------------------------------------------------------------------------
    # SCREEN 1: FULL 4-TAB SYSTEMS ENGINEERING DESIGN STUDIO
    # -------------------------------------------------------------------------
    def draw_design(self):
        self.screen.fill(BG_DARK)
        self.buttons.clear()
        b = self.compute_budget()

        self.screen.blit(self.f_title.render("GIT PUSH TO MARS | 4-TAB MISSION DESIGN STUDIO", True, CYAN), (14, 8))
        self.add_btn(
            pygame.Rect(390, 5, 110, 24),
            f"Mode: {'Team' if self.team_mode else 'Solo'}",
            lambda: setattr(self, "team_mode", not self.team_mode),
            True,
            PURPLE,
        )
        self.add_btn(
            pygame.Rect(508, 5, 130, 24),
            f"Diff: {DIFFICULTY_LEVELS[self.diff_idx]['name'].split()[0]}",
            lambda: setattr(self, "diff_idx", (self.diff_idx + 1) % 3),
            True,
            AMBER,
        )
        self.add_btn(pygame.Rect(646, 5, 105, 24), "GMAT .script", self.export_gmat, False, GREEN)
        self.add_btn(pygame.Rect(758, 5, 105, 24), "Leaderboard", lambda: setattr(self, "mode", "HISTORY"))
        self.add_btn(
            pygame.Rect(870, 5, 216, 24),
            "LAUNCH MISSION [ENTER]",
            self.launch_mission,
            True,
            GREEN,
        )

        tabs = [
            "1. OBJECTIVE, ORBIT & LAUNCH",
            "2. SPACE & GROUND SEGMENTS",
            "3. PDS SCIENCE PAYLOADS",
            "4. 4-PLAYER ROLES & SIGN-OFF",
        ]
        for i, t in enumerate(tabs):
            self.add_btn(
                pygame.Rect(14 + i * 269, 34, 262, 24),
                t,
                lambda idx=i: setattr(self, "design_tab", idx),
                active=(self.design_tab == i),
                col=CYAN,
            )

        if self.design_tab == 0:
            self._tab_orbit_launch()
        elif self.design_tab == 1:
            self._tab_bus_comms(b)
        elif self.design_tab == 2:
            self._tab_instruments()
        else:
            self._tab_team()

        # Bottom 6-Resource Bar
        bar = pygame.Rect(14, 438, 1072, 190)
        self.panel(bar, "6-RESOURCE INTEGRATED DASHBOARD & LAUNCH CONTROL")
        cards = [
            ("1. MASS", f"{int(b['wet'])}/{b['max_pay']} kg", b["mass_ok"]),
            ("2. POWER", f"{int(b['gen_w'])}W/{int(b['draw_w'])}W", b["pwr_ok"]),
            ("3. BUDGET", f"${b['cost']:.0f}M/${b['cap']:.0f}M", b["budget_ok"]),
            ("4. DATA GEN", f"{b['data_gen']:.1f} Gb/d", b["comms_ok"]),
            ("5. COMMS CAP", f"{b['downlink']:.1f} Gb/d", b["comms_ok"]),
            ("6. TIME & dV", f"{self.life_cfg:.1f}y|{int(b['dv_avail'])}m/s", b["dv_ok"]),
        ]
        for i, (k, v, ok) in enumerate(cards):
            rx = 24 + i * 128
            rc = pygame.Rect(rx, 464, 122, 58)
            col = GREEN if ok else RED
            pygame.draw.rect(self.screen, CARD_BG, rc, border_radius=5)
            pygame.draw.rect(self.screen, col, rc, width=2 if not ok else 1, border_radius=5)
            self.screen.blit(self.f_small.render(k, True, TEXT_MUTED), (rx + 6, 472))
            self.screen.blit(self.f_body.render(v, True, col), (rx + 6, 492))

        if b["notes"]:
            msg = "TRADE-OFF ALERT: " + " | ".join(b["notes"][:2]) + " (Click LAUNCH or press ENTER to fly anyway)"
            mcol = AMBER
        else:
            msg = f"ALL 6 RESOURCES NOMINAL! Est. Science Yield: {int(b['sci_pot'])} pts. Click LAUNCH MISSION!"
            mcol = GREEN
        self.screen.blit(self.f_h2.render(msg, True, mcol), (24, 540))
        if self.gmat_banner:
            self.screen.blit(self.f_body.render(self.gmat_banner, True, GREEN), (24, 565))

        self.add_btn(
            pygame.Rect(800, 464, 272, 148),
            "LAUNCH MISSION [ENTER / SPACE]",
            self.launch_mission,
            True,
            GREEN,
        )

    def _tab_orbit_launch(self):
        p1 = pygame.Rect(14, 64, 348, 366)
        self.panel(p1, "STEP 1A: CHOOSE TARGET MISSION")
        for i, sc in enumerate(SCENARIOS):
            def sel_sc(idx=i):
                self.scen_idx = idx
                self.life_cfg = SCENARIOS[idx]["min_life"]
                self.edu_text = SCENARIOS[idx]["edu"]
                for oi, o in enumerate(ORBITS):
                    if o["code"] == SCENARIOS[idx]["orbit"]:
                        self.orbit_idx = oi
            self.add_btn(
                pygame.Rect(22, 88 + i * 66, 332, 58),
                f"{sc['name'][:28]} (${int(sc['budget'])}M)",
                sel_sc,
                active=(self.scen_idx == i),
                col=GREEN,
            )
            self.wrap_text(sc["summary"], 28, 124 + i * 66, 320, self.f_small, TEXT_MUTED, 11)

        cur_sc = SCENARIOS[self.scen_idx]
        self.screen.blit(self.f_h2.render(f"Focus: {cur_sc['focus']}", True, AMBER), (22, 358))
        self.wrap_text(cur_sc["edu"], 22, 376, 332, self.f_small, TEXT_MAIN, 11)

        p2 = pygame.Rect(370, 64, 356, 366)
        self.panel(p2, "STEP 1B: TARGET ORBIT (JPL HORIZONS)")
        for i, orb in enumerate(ORBITS):
            self.add_btn(
                pygame.Rect(378, 88 + i * 56, 340, 50),
                f"{orb['name'][:26]} | dV:{int(orb['dv'])}m/s",
                lambda idx=i: (setattr(self, "orbit_idx", idx), setattr(self, "edu_text", ORBITS[idx]["edu"])),
                active=(self.orbit_idx == i),
                col=CYAN,
            )
            sub = f"SMA:{int(orb['sma'])}km | Inc:{orb['inc']}d | Solar:{int(orb['solar']*100)}%"
            self.screen.blit(self.f_small.render(sub, True, TEXT_MUTED), (384, 122 + i * 56))
        self.wrap_text(ORBITS[self.orbit_idx]["edu"], 378, 376, 340, self.f_small, CYAN, 11)

        p3 = pygame.Rect(734, 64, 352, 366)
        self.panel(p3, "STEP 1C: LAUNCH VEHICLE & LIFETIME")
        ocode = ORBITS[self.orbit_idx]["code"]
        for i, lv in enumerate(ROCKETS):
            cap = lv["cap"][ocode]
            self.add_btn(
                pygame.Rect(742, 88 + i * 58, 336, 50),
                f"{lv['name'][:26]} (${int(lv['cost'])}M)",
                lambda idx=i: (setattr(self, "lv_idx", idx), setattr(self, "edu_text", ROCKETS[idx]["edu"])),
                active=(self.lv_idx == i),
                col=AMBER,
            )
            self.screen.blit(
                self.f_small.render(f"Max Payload to {ocode}: {cap} kg", True, GREEN if cap > 0 else RED),
                (750, 122 + i * 58),
            )
        self.screen.blit(self.f_h2.render(f"Planned Lifetime: {self.life_cfg:.1f} Yrs", True, TEXT_MAIN), (742, 330))
        self.add_btn(pygame.Rect(742, 348, 75, 22), "-0.5 yr", lambda: setattr(self, "life_cfg", max(1.0, round(self.life_cfg - 0.5, 1))))
        self.add_btn(pygame.Rect(826, 348, 75, 22), "+0.5 yr", lambda: setattr(self, "life_cfg", min(6.0, round(self.life_cfg + 0.5, 1))))
        self.wrap_text(ROCKETS[self.lv_idx]["edu"], 742, 378, 336, self.f_small, TEXT_MUTED, 11)

    def _tab_bus_comms(self, b):
        p1 = pygame.Rect(14, 64, 352, 366)
        self.panel(p1, "STEP 2A: SPACE SEGMENT (BUS & PROPULSION)")
        for i, bus in enumerate(BUS_OPTIONS):
            self.add_btn(
                pygame.Rect(22, 88 + i * 50, 336, 44),
                f"{bus['name'][:26]} (${int(bus['cost'])}M)",
                lambda idx=i: setattr(self, "bus_idx", idx),
                active=(self.bus_idx == i),
                col=GREEN,
            )
        self.screen.blit(self.f_h2.render("Spacecraft Propulsion:", True, AMBER), (22, 194))
        for i, pr in enumerate(PROP_OPTIONS):
            self.add_btn(
                pygame.Rect(22, 212 + i * 45, 336, 40),
                f"{pr['name'][:22]} | Isp {int(pr['isp'])}s (${int(pr['cost'])}M)",
                lambda idx=i: setattr(self, "prop_idx", idx),
                active=(self.prop_idx == i),
                col=AMBER,
            )
        self.screen.blit(self.f_body.render(f"Propellant: {int(self.fuel_cfg)} kg", True, TEXT_MAIN), (22, 356))
        self.add_btn(pygame.Rect(185, 352, 65, 22), "-100 kg", lambda: setattr(self, "fuel_cfg", max(100.0, self.fuel_cfg - 100.0)))
        self.add_btn(pygame.Rect(256, 352, 65, 22), "+100 kg", lambda: setattr(self, "fuel_cfg", min(2800.0, self.fuel_cfg + 100.0)))

        self.screen.blit(self.f_body.render(f"Solar Area: {int(self.solar_cfg)} m^2", True, TEXT_MAIN), (22, 384))
        self.add_btn(pygame.Rect(185, 380, 65, 22), "-2 m^2", lambda: setattr(self, "solar_cfg", max(4.0, self.solar_cfg - 2.0)))
        self.add_btn(pygame.Rect(256, 380, 65, 22), "+2 m^2", lambda: setattr(self, "solar_cfg", min(32.0, self.solar_cfg + 2.0)))

        p2 = pygame.Rect(374, 64, 352, 366)
        self.panel(p2, "STEP 2B: GROUND SEGMENT (DSN COMMS)")
        for i, cm in enumerate(COMMS_OPTIONS):
            self.add_btn(
                pygame.Rect(382, 88 + i * 58, 336, 48),
                f"{cm['name']} (${int(cm['cost'])}M)",
                lambda idx=i: (setattr(self, "comms_idx", idx), setattr(self, "edu_text", COMMS_OPTIONS[idx]["edu"])),
                active=(self.comms_idx == i),
                col=CYAN,
            )
            self.screen.blit(self.f_small.render(f"Dish: {cm['dish']} | Mass: {int(cm['mass'])}kg", True, TEXT_MUTED), (390, 122 + i * 58))
        self.screen.blit(self.f_h2.render("Systems Engineering Guide:", True, CYAN), (382, 274))
        self.wrap_text(self.edu_text, 382, 294, 336, self.f_body, TEXT_MAIN, 13)

        p3 = pygame.Rect(734, 64, 352, 366)
        self.panel(p3, "LIVE SPACECRAFT SCHEMATIC")
        cx, cy = p3.centerx, p3.y + 150
        ww = int(28 + self.solar_cfg * 2.1)
        wcol = CYAN if b["pwr_ok"] else RED
        pygame.draw.rect(self.screen, (20, 62, 105), (cx - 32 - ww, cy - 15, ww, 30), border_radius=4)
        pygame.draw.rect(self.screen, wcol, (cx - 32 - ww, cy - 15, ww, 30), width=2, border_radius=4)
        pygame.draw.rect(self.screen, (20, 62, 105), (cx + 32, cy - 15, ww, 30), border_radius=4)
        pygame.draw.rect(self.screen, wcol, (cx + 32, cy - 15, ww, 30), width=2, border_radius=4)
        pygame.draw.rect(self.screen, (36, 48, 74), (cx - 30, cy - 38, 60, 76), border_radius=6)
        pygame.draw.rect(self.screen, GREEN, (cx - 30, cy - 38, 60, 76), width=2, border_radius=6)

        info = [
            f"Rocket: {ROCKETS[self.lv_idx]['name'][:28]}",
            f"Bus: {BUS_OPTIONS[self.bus_idx]['name'][:28]}",
            f"Power: {int(b['gen_w'])}W Gen vs {int(b['draw_w'])}W Draw",
            f"DSN: {COMMS_OPTIONS[self.comms_idx]['dish']}",
            f"Payloads: {len(self.selected_insts)} / 3 Mounted",
        ]
        for i, ln in enumerate(info):
            self.screen.blit(self.f_small.render(ln, True, TEXT_MUTED), (p3.x + 12, p3.y + 230 + i * 20))

    def _tab_instruments(self):
        p = pygame.Rect(14, 64, 1072, 366)
        self.panel(p, "STEP 3: SELECT NASA PDS SCIENTIFIC INSTRUMENTS (MAX 3)")
        for i, inst in enumerate(INSTRUMENTS):
            sel = inst["id"] in self.selected_insts
            ry = 92 + i * 62
            card = pygame.Rect(24, ry, 1052, 54)
            pygame.draw.rect(self.screen, (28, 42, 68) if sel else CARD_BG, card, border_radius=6)
            pygame.draw.rect(self.screen, PURPLE if sel else BORDER, card, width=1, border_radius=6)

            def tog(iid=inst["id"], ed=inst["edu"]):
                self.edu_text = ed
                if iid in self.selected_insts:
                    self.selected_insts.remove(iid)
                elif len(self.selected_insts) < 3:
                    self.selected_insts.add(iid)

            self.add_btn(pygame.Rect(34, ry + 10, 110, 32), "MOUNTED [ON]" if sel else "MOUNT PAYLOAD", tog, sel, PURPLE)
            self.screen.blit(
                self.f_h2.render(f"{inst['name']} | +{int(inst['sci'])} Science Pts", True, PURPLE if sel else TEXT_MAIN),
                (156, ry + 6),
            )
            specs = f"Trade-Offs: Mass +{int(inst['mass'])}kg | Power +{int(inst['pwr'])}W | Cost +${int(inst['cost'])}M | Data +{inst['data']}Gb/day"
            self.screen.blit(self.f_body.render(specs, True, AMBER), (156, ry + 22))
            self.screen.blit(self.f_small.render(inst["edu"], True, TEXT_MUTED), (156, ry + 37))

    def _tab_team(self):
        p = pygame.Rect(14, 64, 1072, 366)
        self.panel(p, "STEP 4: 4-PLAYER MISSION CONTROL ROLES & SIGN-OFF")
        for i, st in enumerate(STATIONS):
            cx = 24 + (i % 2) * 525
            cy = 98 + (i // 2) * 120
            box = pygame.Rect(cx, cy, 510, 108)
            pygame.draw.rect(self.screen, CARD_BG, box, border_radius=6)
            pygame.draw.rect(self.screen, st["col"], box, width=1, border_radius=6)
            self.screen.blit(self.f_h2.render(f"STATION {i+1}: {st['title'].upper()}", True, st["col"]), (cx + 12, cy + 10))
            self.screen.blit(self.f_body.render(f"Priority: {st['prio']}", True, TEXT_MAIN), (cx + 12, cy + 32))
            ok = self.approved[i]
            self.add_btn(
                pygame.Rect(cx + 12, cy + 58, 230, 34),
                "APPROVED [READY]" if ok else "CLICK TO APPROVE",
                lambda idx=i: self.approved.__setitem__(idx, not self.approved[idx]),
                ok,
                GREEN,
            )

    # -------------------------------------------------------------------------
    # SCREEN 2: LIVE ORBITAL FLIGHT & 4-STATION MISSION CONTROL
    # -------------------------------------------------------------------------
    def draw_flight(self):
        self.screen.fill(BG_DARK)
        self.buttons.clear()

        vp = pygame.Rect(12, 12, 650, 616)
        pygame.draw.rect(self.screen, (6, 9, 16), vp, border_radius=6)
        for sx, sy, col in self.stars:
            self.screen.set_at((sx, sy), col)

        cx, cy = vp.centerx, vp.centery

        pygame.draw.circle(self.screen, (32, 48, 76), (cx, cy), int(R_EARTH), 1)
        pygame.draw.circle(self.screen, (56, 36, 56), (cx, cy), int(R_MARS), 1)
        pygame.draw.circle(self.screen, (253, 224, 71), (cx, cy), 18)
        self.screen.blit(self.f_small.render("SUN", True, AMBER), (cx + 22, cy - 5))

        ex_s, ey_s = int(cx + self.ex), int(cy + self.ey)
        pygame.draw.circle(self.screen, (28, 62, 92), (ex_s, ey_s), 36, 1)
        pygame.draw.circle(self.screen, CYAN, (ex_s, ey_s), 9)
        self.screen.blit(self.f_small.render("Earth", True, CYAN), (ex_s + 12, ey_s - 10))

        mx_s, my_s = int(cx + self.mx), int(cy + self.my)
        pygame.draw.circle(self.screen, (92, 38, 45), (mx_s, my_s), 34, 1)
        pygame.draw.circle(self.screen, RED, (mx_s, my_s), 8)
        self.screen.blit(self.f_small.render("Mars (Target)", True, RED), (mx_s + 12, my_s - 10))

        for i in range(0, len(self.pred) - 1, 2):
            p1 = (int(cx + self.pred[i][0]), int(cy + self.pred[i][1]))
            p2 = (int(cx + self.pred[i + 1][0]), int(cy + self.pred[i + 1][1]))
            if vp.collidepoint(p1) and vp.collidepoint(p2):
                pygame.draw.line(self.screen, (75, 130, 175), p1, p2, 1)

        tpts = [(int(cx + px), int(cy + py)) for px, py in self.trail if vp.collidepoint(int(cx + px), int(cy + py))]
        if len(tpts) > 2:
            pygame.draw.lines(self.screen, CYAN, False, tpts, 2)

        scx = max(vp.left + 16, min(vp.right - 16, int(cx + self.x)))
        scy = max(vp.top + 16, min(vp.bottom - 16, int(cy + self.y)))
        nose = (scx + math.cos(self.heading) * 12, scy + math.sin(self.heading) * 12)
        left = (scx + math.cos(self.heading + 2.4) * 8, scy + math.sin(self.heading + 2.4) * 8)
        right = (scx + math.cos(self.heading - 2.4) * 8, scy + math.sin(self.heading - 2.4) * 8)
        pygame.draw.polygon(self.screen, TEXT_MAIN, [nose, left, right])
        pygame.draw.circle(self.screen, GREEN, (scx, scy), 14, 1)
        self.screen.blit(self.f_small.render("GitPushSat", True, GREEN), (scx + 16, scy - 4))

        pygame.draw.rect(self.screen, BORDER, vp, width=2, border_radius=6)

        self.screen.blit(
            self.f_h2.render(
                f"LIVE ORBITAL SIMULATION | MET: {self.years:.2f}/{self.target_years:.1f} yrs | WARP: {self.warp}x",
                True,
                GREEN,
            ),
            (24, 22),
        )
        self.screen.blit(
            self.f_small.render(
                "Keys: [TAB] 4-Tab Design Studio | [T] Transfer Burn | [F9] Solar Flare | [1-4] Stations",
                True,
                CYAN,
            ),
            (24, 38),
        )

        if self.active_event:
            ev = pygame.Rect(24, 460, 626, 154)
            pygame.draw.rect(self.screen, (38, 24, 52), ev, border_radius=6)
            pygame.draw.rect(self.screen, AMBER, ev, width=2, border_radius=6)
            self.screen.blit(self.f_h2.render("TEAM DECISION: " + self.active_event["title"], True, AMBER), (36, 470))
            self.screen.blit(self.f_body.render(self.active_event["desc"], True, TEXT_MAIN), (36, 492))
            self.add_btn(pygame.Rect(36, 518, 600, 34), self.active_event["a"], lambda: self.resolve_event("A"), True, CYAN)
            self.add_btn(pygame.Rect(36, 562, 600, 34), self.active_event["b"], lambda: self.resolve_event("B"), True, PURPLE)

        con = pygame.Rect(674, 12, 414, 616)
        self.panel(con, "6-RESOURCE MISSION CONTROL CONSOLE")

        dv_rem = self.isp * G0 * math.log((self.dry_mass + self.fuel) / max(1.0, self.dry_mass))
        rows = [
            ("1. Mass & Fuel", f"{self.fuel:.0f} kg fuel ({int(self.dry_mass + self.fuel)} kg wet)", AMBER),
            ("2. Power / Battery", f"{int(self.battery)} / {int(self.max_batt)} Wh", GREEN),
            ("3. Budget Reserve", f"${self.budget_rem:.1f} M remaining", TEXT_MAIN),
            ("4. Data Buffer", f"{self.data_buf:.1f} / 120.0 Gb (Lost: {self.data_lost:.1f})", CYAN),
            ("5. DSN Downlink", f"{COMMS_OPTIONS[self.comms_idx]['dish'][:16]} ({self.data_tx:.1f} Gb)", CYAN),
            ("6. Time & Delta-V", f"Health {self.health:.0f}% | dV {int(dv_rem)} m/s", GREEN),
            ("PDS Science Score", f"{self.science:.1f} / {self.target_sci:.0f} pts", PURPLE),
        ]
        for i, (k, v, col) in enumerate(rows):
            y = 38 + i * 22
            self.screen.blit(self.f_body.render(k, True, TEXT_MUTED), (686, y))
            vs = self.f_h2.render(v, True, col)
            self.screen.blit(vs, (1074 - vs.get_width(), y))

        for i, st in enumerate(STATIONS):
            self.add_btn(
                pygame.Rect(686 + i * 98, 198, 92, 26),
                f"{i+1}:{st['code']}",
                lambda idx=i: setattr(self, "station", idx),
                active=(self.station == i),
                col=st["col"],
            )

        self.add_btn(
            pygame.Rect(686, 234, 388, 34),
            "OPEN 4-TAB MISSION DESIGN STUDIO [PRESS TAB]",
            lambda: setattr(self, "mode", "DESIGN"),
            active=True,
            col=CYAN,
        )
        self.add_btn(
            pygame.Rect(686, 276, 388, 34),
            "EXECUTE GMAT MARS TRANSFER BURN [PRESS T]",
            self.trigger_transfer_burn,
            active=True,
            col=GREEN,
        )
        for i, w in enumerate([1, 2, 5, 10]):
            self.add_btn(
                pygame.Rect(686 + i * 98, 318, 92, 26),
                f"Warp {w}x",
                lambda wp=w: setattr(self, "warp", wp),
                active=(self.warp == w),
            )
        self.add_btn(
            pygame.Rect(686, 352, 190, 28),
            f"Safe Mode: {'ON' if self.safe_mode else 'OFF'}",
            lambda: setattr(self, "safe_mode", not self.safe_mode),
            active=self.safe_mode,
            col=AMBER,
        )
        self.add_btn(
            pygame.Rect(884, 352, 190, 28),
            "Trigger Solar Flare [F9]",
            self.trigger_flare,
            active=True,
            col=PURPLE,
        )
        self.add_btn(
            pygame.Rect(686, 388, 190, 28),
            f"Sensors: {'ON' if self.sensors_on else 'PAUSED'}",
            lambda: setattr(self, "sensors_on", not self.sensors_on),
            active=self.sensors_on,
            col=PURPLE,
        )
        self.add_btn(
            pygame.Rect(884, 388, 190, 28),
            "Reset Orbit [R]",
            self.reset_flight,
            col=AMBER,
        )

        self.screen.blit(self.f_h2.render("MISSION TELEMETRY LOG:", True, TEXT_MUTED), (686, 426))
        for i, line in enumerate(self.logs[:5]):
            self.screen.blit(self.f_small.render(line[:54], True, TEXT_MAIN), (686, 444 + i * 16))

        self.add_btn(
            pygame.Rect(686, 562, 388, 50),
            "COMPLETE MISSION & VIEW SCORE DEBRIEF",
            self.finish_mission,
            active=True,
            col=GREEN,
        )

    # -------------------------------------------------------------------------
    # SCREEN 3: POST-MISSION DEBRIEF & DIAGNOSTICS
    # -------------------------------------------------------------------------
    def draw_debrief(self):
        self.screen.fill(BG_DARK)
        self.buttons.clear()
        b = self.compute_budget()
        box = pygame.Rect(50, 24, 1000, 592)
        self.panel(box, "POST-MISSION SYSTEMS ANALYSIS & ENGINEERING DEBRIEF", GREEN)

        total_score = min(
            1000,
            int(420 + min(350, self.science * 1.6) + self.health * 1.3 + (80 if b["budget_ok"] else 20)),
        )
        grade = "GRADE S — NASA FLAGSHIP SUCCESS" if total_score >= 800 else "GRADE A — MISSION OBJECTIVES MET"
        self.screen.blit(self.f_title.render(f"TOTAL SCORE: {total_score} / 1000 PTS  |  {grade}", True, GREEN), (80, 62))

        rows = [
            f"• Scenario & Orbit: {SCENARIOS[self.scen_idx]['name']} ({ORBITS[self.orbit_idx]['code']}) via {ROCKETS[self.lv_idx]['name']}",
            f"• PDS Science Data Downlinked: {self.science:.1f} / {self.target_sci:.0f} pts ({self.data_tx:.1f} Gb transmitted)",
            f"• Mission Cost vs. Budget Cap: ${b['cost']:.1f}M / ${b['cap']:.1f}M  |  Remaining Fuel: {self.fuel:.0f} kg",
            f"• Spacecraft Health: {self.health:.0f}%  |  Ground Segment Dish: {COMMS_OPTIONS[self.comms_idx]['dish']}",
            "• Systems Lesson 1: High-gain DSN link prevented onboard solid-state recorder overflow during Mars capture.",
            "• Systems Lesson 2: Solar array sizing & Composite Rad-Hard Bus sustained battery charge at 1.524 AU (43% flux).",
        ]
        for i, r in enumerate(rows):
            self.screen.blit(self.f_h2.render(r, True, TEXT_MAIN if i < 4 else AMBER), (80, 115 + i * 42))

        self.add_btn(
            pygame.Rect(80, 530, 300, 48),
            "OPEN 4-TAB DESIGN STUDIO [TAB]",
            lambda: setattr(self, "mode", "DESIGN"),
            True,
            CYAN,
        )
        self.add_btn(
            pygame.Rect(400, 530, 300, 48),
            "VIEW LEADERBOARD",
            lambda: setattr(self, "mode", "HISTORY"),
            True,
            PURPLE,
        )
        self.add_btn(
            pygame.Rect(720, 530, 300, 48),
            "FLY AGAIN [ENTER]",
            self.launch_mission,
            True,
            GREEN,
        )

    # -------------------------------------------------------------------------
    # SCREEN 4: LEADERBOARD & RUN HISTORY
    # -------------------------------------------------------------------------
    def draw_history(self):
        self.screen.fill(BG_DARK)
        self.buttons.clear()
        box = pygame.Rect(50, 24, 1000, 592)
        self.panel(box, "TEAM MISSION LEADERBOARD & DESIGN COMPARISON", CYAN)

        hist = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    hist = json.load(f)
            except Exception:
                hist = []

        if not hist:
            self.screen.blit(
                self.f_h2.render("No completed missions yet — complete a flight to log your score!", True, TEXT_MUTED),
                (80, 90),
            )
        else:
            hdr = f"{'RANK':<6}{'DATE':<18}{'SCENARIO':<34}{'ORBIT':<8}{'COST':<10}{'SCI':<9}{'SCORE':<8}"
            self.screen.blit(self.f_h2.render(hdr, True, CYAN), (80, 75))
            for i, h in enumerate(sorted(hist, key=lambda x: x.get("total", 0), reverse=True)[:10]):
                line = (
                    f"#{i+1:<5}{h.get('timestamp',''):<18}{h.get('scenario','')[:32]:<34}"
                    f"{h.get('orbit',''):<8}${h.get('cost',0):<9.0f}{h.get('science',0):<9.0f}{h.get('total',0):<8}"
                )
                self.screen.blit(self.f_body.render(line, True, GREEN if i == 0 else TEXT_MAIN), (80, 108 + i * 34))

        self.add_btn(
            pygame.Rect(80, 530, 420, 48),
            "RETURN TO 4-TAB DESIGN STUDIO [TAB]",
            lambda: setattr(self, "mode", "DESIGN"),
            True,
            CYAN,
        )
        self.add_btn(
            pygame.Rect(540, 530, 420, 48),
            "LAUNCH LIVE FLIGHT [ENTER]",
            self.launch_mission,
            True,
            GREEN,
        )

    # -------------------------------------------------------------------------
    # MAIN LOOP
    # -------------------------------------------------------------------------
    def run(self):
        print(
            ">>> Git Push to Mars Ready! Click [LAUNCH MISSION] or press [ENTER / SPACE / TAB] to fly. <<<",
            flush=True,
        )
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    w, h = pygame.display.get_window_size()
                    mx = int(ev.pos[0] * (WIDTH / max(1, w)))
                    my = int(ev.pos[1] * (HEIGHT / max(1, h)))
                    for rect, cb in self.buttons:
                        if rect.collidepoint((mx, my)) or rect.collidepoint(ev.pos):
                            cb()
                            break
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_TAB:
                        if self.mode == "DESIGN":
                            self.launch_mission()
                        else:
                            self.mode = "DESIGN"
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_l):
                        if self.mode != "FLIGHT":
                            self.launch_mission()
                    elif ev.key == pygame.K_t and self.mode == "FLIGHT":
                        self.trigger_transfer_burn()
                    elif ev.key == pygame.K_r and self.mode == "FLIGHT":
                        self.reset_flight()
                    elif ev.key == pygame.K_F9 and self.mode == "FLIGHT":
                        self.trigger_flare()
                    elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        if self.mode == "DESIGN":
                            self.design_tab = ev.key - pygame.K_1
                        else:
                            self.station = ev.key - pygame.K_1

            self.step_physics(dt)
            if self.mode == "FLIGHT":
                self.draw_flight()
            elif self.mode == "DESIGN":
                self.draw_design()
            elif self.mode == "DEBRIEF":
                self.draw_debrief()
            else:
                self.draw_history()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    MarsMissionGame().run()