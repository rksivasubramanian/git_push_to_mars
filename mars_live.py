import math
import os
import random
import sys
import time

os.environ["SDL_VIDEO_HIGHDPI_DISABLED"] = "1"
import pygame

WIDTH, HEIGHT = 1100, 640
FPS = 60
G0 = 9.80665

# Colors
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

# Orbital Physics (GMAT Scaled Units)
MU_SUN = 2.8e7
MU_EARTH = 1.6e5
MU_MARS = 9.5e4
R_EARTH = 145.0
R_MARS = 230.0


class MarsMissionGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(
            "Team Git Push to Mars — LIVE FLIGHT [TAB: Switch View | T: Transfer Burn | F9: Solar Flare]"
        )
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.f_title = pygame.font.SysFont("menlo,consolas,monospace", 15, bold=True)
        self.f_h2 = pygame.font.SysFont("menlo,consolas,monospace", 12, bold=True)
        self.f_body = pygame.font.SysFont("menlo,consolas,monospace", 11)
        self.f_small = pygame.font.SysFont("menlo,consolas,monospace", 10)

        # Starts directly in FLIGHT mode so you never get stuck on a Launch button!
        self.mode = "FLIGHT"  # FLIGHT | DESIGN | DEBRIEF
        self.station = 0      # 0:FDO, 1:BUS, 2:SCI, 3:COM
        self.warp = 2
        self.autopilot = True
        self.buttons = []

        random.seed(42)
        self.stars = [
            (random.randint(20, 650), random.randint(20, 620), random.choice([(70, 90, 130), (120, 150, 200)]))
            for _ in range(90)
        ]
        self.reset_flight()

    def reset_flight(self):
        self.earth_ang = 0.0
        self.mars_ang = math.radians(44.0)
        self.earth_w = math.sqrt(MU_SUN / (R_EARTH ** 3))
        self.mars_w = math.sqrt(MU_SUN / (R_MARS ** 3))

        self.ex = R_EARTH
        self.ey = 0.0
        self.mx = R_MARS * math.cos(self.mars_ang)
        self.my = R_MARS * math.sin(self.mars_ang)

        # Spawn spacecraft in Earth orbit with initial prograde velocity
        self.x = self.ex + 18.0
        self.y = self.ey
        v_orb = math.sqrt(MU_SUN / R_EARTH) + 22.0
        self.vx = 0.0
        self.vy = v_orb
        self.heading = math.pi / 2.0
        self.throttle = 0.0

        # 6 Core Resources
        self.dry_mass = 520.0
        self.fuel = 620.0
        self.isp = 322.0
        self.battery = 1550.0
        self.max_batt = 1650.0
        self.budget_rem = 68.0
        self.data_buf = 12.0
        self.data_tx = 0.0
        self.science = 0.0
        self.target_sci = 210.0
        self.years = 0.0
        self.target_years = 2.5
        self.health = 100.0
        self.safe_mode = False
        self.sensors_on = True
        self.dsn_on = True

        self.trail = [(self.x, self.y)]
        self.pred = []
        self.active_event = None
        self.transfer_done = False
        self.logs = [
            "T+0.00y: LIVE FLIGHT ACTIVE! AI Autopilot & GMAT RK4 Propagator running.",
            "TIP: Press [T] for Mars Transfer Burn, [F9] for Solar Flare, [TAB] for Studio.",
        ]
        self.update_prediction()

    def add_btn(self, rect, text, cb, active=False, col=CYAN):
        bg = (34, 62, 98) if active else CARD_BG
        bd = col if active else BORDER
        pygame.draw.rect(self.screen, bg, rect, border_radius=5)
        pygame.draw.rect(self.screen, bd, rect, width=2 if active else 1, border_radius=5)
        s = self.f_body.render(text, True, TEXT_MAIN)
        self.screen.blit(s, (rect.x + (rect.width - s.get_width()) // 2, rect.y + (rect.height - s.get_height()) // 2))
        self.buttons.append((rect, cb))

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

    def step_physics(self, real_dt):
        if self.mode != "FLIGHT":
            return

        # Auto-execute TMI burn shortly after launch if Autopilot is ON
        if self.autopilot and not self.transfer_done and self.years > 0.08:
            self.trigger_transfer_burn()

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
                thrust_acc = (440.0 * self.throttle) / (self.dry_mass + self.fuel)
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
            if self.sensors_on and not self.safe_mode:
                self.data_buf = min(120.0, self.data_buf + 45.0 * dyr)
            if self.dsn_on and self.data_buf > 0:
                tx = min(self.data_buf, 52.0 * dyr)
                self.data_buf -= tx
                self.data_tx += tx
                self.science += tx * 2.4

            if self.years >= self.target_years:
                self.mode = "DEBRIEF"
                return

        if not self.trail or math.hypot(self.x - self.trail[-1][0], self.y - self.trail[-1][1]) > 3.0:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 300:
                self.trail.pop(0)
        self.update_prediction()

    def draw_flight(self):
        self.screen.fill(BG_DARK)
        self.buttons.clear()

        vp = pygame.Rect(12, 12, 650, 616)
        pygame.draw.rect(self.screen, (6, 9, 16), vp, border_radius=6)
        for sx, sy, col in self.stars:
            self.screen.set_at((sx, sy), col)

        cx, cy = vp.centerx, vp.centery

        # Orbits & Sun
        pygame.draw.circle(self.screen, (32, 48, 76), (cx, cy), int(R_EARTH), 1)
        pygame.draw.circle(self.screen, (56, 36, 56), (cx, cy), int(R_MARS), 1)
        pygame.draw.circle(self.screen, (253, 224, 71), (cx, cy), 18)
        self.screen.blit(self.f_small.render("SUN", True, AMBER), (cx + 22, cy - 5))

        # Earth
        ex_s, ey_s = int(cx + self.ex), int(cy + self.ey)
        pygame.draw.circle(self.screen, (28, 62, 92), (ex_s, ey_s), 36, 1)
        pygame.draw.circle(self.screen, CYAN, (ex_s, ey_s), 9)
        self.screen.blit(self.f_small.render("Earth", True, CYAN), (ex_s + 12, ey_s - 10))

        # Mars
        mx_s, my_s = int(cx + self.mx), int(cy + self.my)
        pygame.draw.circle(self.screen, (92, 38, 45), (mx_s, my_s), 34, 1)
        pygame.draw.circle(self.screen, RED, (mx_s, my_s), 8)
        self.screen.blit(self.f_small.render("Mars (Target)", True, RED), (mx_s + 12, my_s - 10))

        # Predicted GMAT Path
        for i in range(0, len(self.pred) - 1, 2):
            p1 = (int(cx + self.pred[i][0]), int(cy + self.pred[i][1]))
            p2 = (int(cx + self.pred[i + 1][0]), int(cy + self.pred[i + 1][1]))
            if vp.collidepoint(p1) and vp.collidepoint(p2):
                pygame.draw.line(self.screen, (75, 130, 175), p1, p2, 1)

        # Flight Trail
        tpts = [(int(cx + px), int(cy + py)) for px, py in self.trail if vp.collidepoint(int(cx + px), int(cy + py))]
        if len(tpts) > 2:
            pygame.draw.lines(self.screen, CYAN, False, tpts, 2)

        # Spacecraft
        scx = max(vp.left + 16, min(vp.right - 16, int(cx + self.x)))
        scy = max(vp.top + 16, min(vp.bottom - 16, int(cy + self.y)))
        nose = (scx + math.cos(self.heading) * 12, scy + math.sin(self.heading) * 12)
        left = (scx + math.cos(self.heading + 2.4) * 8, scy + math.sin(self.heading + 2.4) * 8)
        right = (scx + math.cos(s_h := self.heading - 2.4) * 8, scy + math.sin(s_h) * 8)
        pygame.draw.polygon(self.screen, TEXT_MAIN, [nose, left, right])
        pygame.draw.circle(self.screen, GREEN, (scx, scy), 14, 1)
        self.screen.blit(self.f_small.render("GitPushSat", True, GREEN), (scx + 16, scy - 4))

        pygame.draw.rect(self.screen, BORDER, vp, width=2, border_radius=6)

        # Viewport HUD
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
                "Controls: [T] Mars Transfer Burn | [F9] Solar Flare Event | [1-4] Stations | [TAB] Design Studio",
                True,
                CYAN,
            ),
            (24, 40),
        )

        # Active Event Popup
        if self.active_event:
            ev = pygame.Rect(24, 460, 626, 154)
            pygame.draw.rect(self.screen, (38, 24, 52), ev, border_radius=6)
            pygame.draw.rect(self.screen, AMBER, ev, width=2, border_radius=6)
            self.screen.blit(self.f_h2.render("TEAM DECISION: " + self.active_event["title"], True, AMBER), (36, 470))
            self.screen.blit(self.f_body.render(self.active_event["desc"], True, TEXT_MAIN), (36, 492))
            self.add_btn(pygame.Rect(36, 518, 600, 34), self.active_event["a"], lambda: self.resolve_event("A"), True, CYAN)
            self.add_btn(pygame.Rect(36, 562, 600, 34), self.active_event["b"], lambda: self.resolve_event("B"), True, PURPLE)

        # Right Mission Control Console
        con = pygame.Rect(674, 12, 414, 616)
        pygame.draw.rect(self.screen, PANEL_BG, con, border_radius=6)
        pygame.draw.rect(self.screen, BORDER, con, width=2, border_radius=6)
        self.screen.blit(self.f_h2.render("6-RESOURCE MISSION CONTROL CONSOLE", True, CYAN), (686, 20))

        dv_rem = self.isp * G0 * math.log((self.dry_mass + self.fuel) / self.dry_mass)
        rows = [
            ("1. Mass & Fuel", f"{self.fuel:.0f} kg fuel ({int(self.dry_mass + self.fuel)} kg wet)", AMBER),
            ("2. Power / Battery", f"{int(self.battery)} / {int(self.max_batt)} Wh (Solar 43%)", GREEN),
            ("3. Budget Reserve", f"${self.budget_rem:.1f} M remaining", TEXT_MAIN),
            ("4. Data Buffer", f"{self.data_buf:.1f} / 120.0 Gb", CYAN),
            ("5. DSN Downlink", f"DSN 34m Online ({self.data_tx:.1f} Gb downlinked)", CYAN),
            ("6. Time & Delta-V", f"Health {self.health:.0f}% | dV {int(dv_rem)} m/s", GREEN),
            ("PDS Science Score", f"{self.science:.1f} / {self.target_sci:.0f} pts", PURPLE),
        ]
        for i, (k, v, col) in enumerate(rows):
            y = 48 + i * 22
            self.screen.blit(self.f_body.render(k, True, TEXT_MUTED), (686, y))
            vs = self.f_h2.render(v, True, col)
            self.screen.blit(vs, (1074 - vs.get_width(), y))

        # 4-Player Station Buttons
        st_names = ["1:FDO", "2:BUS", "3:SCI", "4:COM"]
        for i, name in enumerate(st_names):
            self.add_btn(
                pygame.Rect(686 + i * 98, 210, 92, 28),
                name,
                lambda idx=i: setattr(self, "station", idx),
                active=(self.station == i),
                col=CYAN,
            )

        # Interactive Controls
        self.add_btn(
            pygame.Rect(686, 250, 388, 36),
            "EXECUTE GMAT MARS TRANSFER BURN [PRESS T]",
            self.trigger_transfer_burn,
            active=True,
            col=GREEN,
        )
        for i, w in enumerate([1, 2, 5, 10]):
            self.add_btn(
                pygame.Rect(686 + i * 98, 296, 92, 28),
                f"Warp {w}x",
                lambda wp=w: setattr(self, "warp", wp),
                active=(self.warp == w),
            )
        self.add_btn(
            pygame.Rect(686, 334, 190, 30),
            f"Safe Mode: {'ON' if self.safe_mode else 'OFF'}",
            lambda: setattr(self, "safe_mode", not self.safe_mode),
            active=self.safe_mode,
            col=AMBER,
        )
        self.add_btn(
            pygame.Rect(884, 334, 190, 30),
            "Trigger Solar Flare [F9]",
            self.trigger_flare,
            active=True,
            col=PURPLE,
        )
        self.add_btn(
            pygame.Rect(686, 374, 190, 30),
            "Open Design Studio [TAB]",
            lambda: setattr(self, "mode", "DESIGN"),
            col=CYAN,
        )
        self.add_btn(
            pygame.Rect(884, 374, 190, 30),
            "Reset Orbit [R]",
            self.reset_flight,
            col=AMBER,
        )

        # Logs
        self.screen.blit(self.f_h2.render("MISSION TELEMETRY LOG:", True, TEXT_MUTED), (686, 420))
        for i, line in enumerate(self.logs[:5]):
            self.screen.blit(self.f_small.render(line[:54], True, TEXT_MAIN), (686, 442 + i * 18))

        self.add_btn(
            pygame.Rect(686, 560, 388, 52),
            "COMPLETE MISSION & VIEW SCORE DEBRIEF",
            lambda: setattr(self, "mode", "DEBRIEF"),
            active=True,
            col=GREEN,
        )

    def draw_design(self):
        self.screen.fill(BG_DARK)
        self.buttons.clear()
        box = pygame.Rect(40, 30, 1020, 580)
        pygame.draw.rect(self.screen, PANEL_BG, box, border_radius=8)
        pygame.draw.rect(self.screen, CYAN, box, width=2, border_radius=8)
        self.screen.blit(self.f_title.render("SPACECRAFT & MISSION CONFIGURATION STUDIO", True, CYAN), (70, 55))
        self.screen.blit(
            self.f_body.render("Scenario: Mars Atmospheric & Subsurface Explorer | Target: Mars Orbit (1.524 AU)", True, TEXT_MAIN),
            (70, 95),
        )
        self.add_btn(
            pygame.Rect(70, 140, 260, 42),
            f"Fuel Mass: {int(self.fuel)} kg (+100 kg)",
            lambda: setattr(self, "fuel", min(1800.0, self.fuel + 100.0)),
            True,
            AMBER,
        )
        self.add_btn(
            pygame.Rect(350, 140, 260, 42),
            "RETURN TO LIVE FLIGHT [PRESS TAB / ENTER]",
            lambda: setattr(self, "mode", "FLIGHT"),
            True,
            GREEN,
        )

    def draw_debrief(self):
        self.screen.fill(BG_DARK)
        self.buttons.clear()
        box = pygame.Rect(80, 40, 940, 560)
        pygame.draw.rect(self.screen, PANEL_BG, box, border_radius=8)
        pygame.draw.rect(self.screen, GREEN, box, width=2, border_radius=8)

        total_score = min(1000, int(450 + self.science * 1.8 + self.health * 1.5))
        self.screen.blit(
            self.f_title.render(f"POST-MISSION DEBRIEF — TOTAL SCORE: {total_score} / 1000 (GRADE S)", True, GREEN),
            (110, 75),
        )
        metrics = [
            f"• PDS Science Data Collected & Downlinked: {self.science:.1f} / {self.target_sci:.0f} pts",
            f"• Propellant Remaining: {self.fuel:.1f} kg  |  Spacecraft Health: {self.health:.0f}%",
            "• Systems Lesson: High-gain X/Ka-Band DSN link prevented recorder overflow during Mars capture.",
            "• GMAT Verification: RK4 trajectory & Tsiolkovsky mass depletion nominal across 4 stations.",
        ]
        for i, m in enumerate(metrics):
            self.screen.blit(self.f_h2.render(m, True, TEXT_MAIN), (110, 140 + i * 45))

        self.add_btn(
            pygame.Rect(110, 480, 380, 52),
            "FLY AGAIN / RETURN TO LIVE ORBIT",
            lambda: (self.reset_flight(), setattr(self, "mode", "FLIGHT")),
            True,
            CYAN,
        )

    def run(self):
        print(">>> LIVE FLIGHT STARTED! Window is open in FLIGHT mode. <<<", flush=True)
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
                        self.mode = "DESIGN" if self.mode == "FLIGHT" else "FLIGHT"
                    elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.mode = "FLIGHT"
                    elif ev.key == pygame.K_t:
                        self.trigger_transfer_burn()
                    elif ev.key == pygame.K_r:
                        self.reset_flight()
                    elif ev.key == pygame.K_F9:
                        self.trigger_flare()
                    elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        self.station = ev.key - pygame.K_1

            self.step_physics(dt)
            if self.mode == "FLIGHT":
                self.draw_flight()
            elif self.mode == "DESIGN":
                self.draw_design()
            else:
                self.draw_debrief()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    MarsMissionGame().run()
