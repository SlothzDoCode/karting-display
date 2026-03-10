import sys
import os
import threading
from datetime import datetime
import requests

import socket
import socketio
import eventlet
import psycopg2

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


# ==========================================================
# --------------------- STATE ------------------------------
# ==========================================================

class AppState:
    def __init__(self):
        self.current_bg = "black"
        self.fg_dark = "black"
        self.fg_light = "white"
        self.positions = [f"pos {i}" for i in range(1, 17)]
        self.countdown_timer = [f"time{i*5}" for i in range(1, 20)]


# ==========================================================
# ----------------- GLOBAL SIGNAL BRIDGE -------------------
# ==========================================================

class GlobalSignals(QObject):
    socket_event = pyqtSignal(str)


global_signals = GlobalSignals()


# ==========================================================
# ------------------ BASE SESSION WIDGET -------------------
# ==========================================================

class BaseSessionWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state

        # Clock label (we'll reposition in subclasses)
        self.clock = QLabel(self)
        self.clock.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.clock.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # Clock timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

        # Flashing / background
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self._flash_background)
        self.flash_colors = []
        self.flash_index = 0

    def update_clock(self):
        self.clock.setText(datetime.now().strftime("%H:%M:%S"))

    def _flash_background(self):
        if not self.flash_colors:
            self.flash_timer.stop()
            return

        color = self.flash_colors[self.flash_index]
        text_color = self.state.fg_light if color == "#000000" else self.state.fg_dark

        # Apply to main window
        self.window().setStyleSheet(f"background-color: {color}; color: {text_color}")

        self.flash_index = (self.flash_index + 1) % len(self.flash_colors)

    def flash(self, colors, interval):
        self.flash_colors = colors
        self.flash_index = 0
        self.flash_timer.start(interval)

    def handle_flag_input(self, data: str):
        # Green flag
        if data == "green-flag":
            self.flash_timer.stop()
            self.state.current_bg = "#00FF00"
            self.window().setStyleSheet(f"background-color: {self.state.current_bg}")

        # Yellow flag
        elif data == "yellow-flag":
            self.state.current_bg = "#FFFF00"
            self.flash([self.state.current_bg, "#000000"], 800)

        # Red flag
        elif data == "red-flag":
            self.state.current_bg = "#FF0000"
            self.flash([self.state.current_bg, "#000000"], 1200)

        # Blue flag (temporary 5 seconds)
        elif data == "blue-flag":
            self.window().setStyleSheet("background-color: #0000FF")
            QTimer.singleShot(
                5000,
                lambda: self.window().setStyleSheet(f"background-color: {self.state.current_bg}"),
            )

        # PB alert (temporary 5 seconds)
        elif data == "PB-alert":
            self.window().setStyleSheet("background-color: #DAA520")
            QTimer.singleShot(
                5000,
                lambda: self.window().setStyleSheet(f"background-color: {self.state.current_bg}"),
            )

        # Pitstop alert (temporary 10 seconds)
        elif data == "pitstop-alert":
            self.window().setStyleSheet("background-color: #C115D4")
            QTimer.singleShot(
                    10000,
                    lambda: self.window().setStyleSheet(f"background-color: {self.state.current_bg}"),
                )


# ==========================================================
# ------------------- SPRINT MODE --------------------------
# ==========================================================

class SprintMode(BaseSessionWidget):    
    def __init__(self, state):
        super().__init__(state)

        # Main grid layout
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(40, 40, 40, 40)
        self.grid.setSpacing(20)

        # Remove clock from old parent and add to layout (top-right)
        self.clock.setParent(None)
        self.grid.addWidget(self.clock, 0, 2, alignment=Qt.AlignmentFlag.AlignRight)

        # Position (center-left)
        self.position_label = QLabel("0")
        self.position_label.setStyleSheet("font-size: 100px; font-weight: bold;")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid.addWidget(self.position_label, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        # Countdown timer (center-right)
        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet("font-size: 100px; font-weight: bold;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid.addWidget(self.timer_label, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        # Stretches for proper centering
        self.grid.setRowStretch(0, 1)
        self.grid.setRowStretch(1, 2)
        self.grid.setRowStretch(2, 1)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 2)
        self.grid.setColumnStretch(2, 1)

        # Countdown timer logic
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.remaining_seconds = 0

        # ----------------- Fullscreen Checkerboard -----------------
        self.checkerboard_widget = QWidget(self)
        self.checkerboard_widget.setGeometry(0, 0, self.width(), self.height())
        self.checkerboard_widget.lower()  # behind labels
        self.checkerboard_widget.hide()

        self.checker_squares = []
        self.rows, self.cols = 8, 8  # default grid
        self._create_checkerboard()

        self.checker_anim_timer = QTimer(self)
        self.checker_anim_timer.timeout.connect(self._animate_checkerboard)
        self.checker_anim_index = 0

        # Track resize to scale checkerboard
        self.installEventFilter(self)

    # ----------------- Countdown Timer -----------------
    def start_timer(self, seconds):
        self.remaining_seconds = seconds
        self.update_timer()
        self.timer.start(1000)

    def update_timer(self):
        mins = self.remaining_seconds // 60
        secs = self.remaining_seconds % 60
        self.timer_label.setText(f"{mins:02}:{secs:02}")

        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
        else:
            self.timer.stop()
            self.show_checkerboard()

    # ----------------- Checkerboard -----------------
    def _create_checkerboard(self):
        # Clear previous squares
        for sq_row in self.checker_squares:
            for sq in sq_row:
                sq.setParent(None)
        self.checker_squares = []

        w = self.checkerboard_widget.width() // self.cols
        h = self.checkerboard_widget.height() // self.rows

        for r in range(self.rows):
            row_squares = []
            for c in range(self.cols):
                square = QWidget(self.checkerboard_widget)
                square.setGeometry(c * w, r * h, w, h)
                color = "#FFFFFF" if (r + c) % 2 == 0 else "#000000"
                square.setStyleSheet(f"background-color: {color};")
                row_squares.append(square)
            self.checker_squares.append(row_squares)

    def show_checkerboard(self):
        self.checkerboard_widget.show()
        self.checker_anim_index = 0
        self.checker_anim_timer.start(300)  # flip every 300ms
        QTimer.singleShot(5000, self.stop_checkerboard)  # stop after 5s

    def _animate_checkerboard(self):
        for r, row in enumerate(self.checker_squares):
            for c, square in enumerate(row):
                if (r + c + self.checker_anim_index) % 2 == 0:
                    square.setStyleSheet("background-color: #FFFFFF;")
                else:
                    square.setStyleSheet("background-color: #000000;")
        self.checker_anim_index += 1

    def stop_checkerboard(self):
        self.checker_anim_timer.stop()
        self.checkerboard_widget.hide()
        self.setStyleSheet(f"background-color: {self.state.current_bg}")

    # ----------------- Handle Flags -----------------
    def handle_flag_input(self, data: str):
        super().handle_flag_input(data)

        if data in self.state.countdown_timer:
            minutes = int(data[4:])
            self.start_timer(minutes * 60)
        elif data in self.state.positions:
            pos = int(data[3:])
            suffix = "th"
            if not 10 <= pos % 100 <= 20:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(pos % 10, "th")
            self.position_label.setText(f"{pos}{suffix}")

    # ----------------- Event Filter to handle resizing -----------------
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Resize:
            self.checkerboard_widget.setGeometry(0, 0, self.width(), self.height())
            self._create_checkerboard()
        return super().eventFilter(obj, event)


# ==========================================================
# ------------------- BASIC QUALI --------------------------
# ==========================================================

class BasicQualiMode(BaseSessionWidget):
    def __init__(self, state):
        super().__init__(state)

        self.lap_start = None
        self.running = False
        self.fastest_lap = None
        self.previous_lap = None
        
        # Main grid layout
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(40, 40, 40, 40)
        self.grid.setSpacing(20)

        # Remove clock from old parent and add to layout (top-right)
        self.clock.setParent(None)
        self.grid.addWidget(self.clock, 0, 2, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Stretches for proper centering
        self.grid.setRowStretch(0, 1)
        self.grid.setRowStretch(1, 2)
        self.grid.setRowStretch(2, 1)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 2)
        self.grid.setColumnStretch(2, 1)


# ==========================================================
# ---------------------- MAIN WINDOW -----------------------
# ==========================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.state = AppState()
        self.current_screen = None

        global_signals.socket_event.connect(self.route_socket_event)

        self.show_menu()

    def show_menu(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        sprint_btn = QPushButton("Sprint Mode")
        sprint_btn.clicked.connect(
            lambda: self.switch_screen(SprintMode(self.state))
            )

        quali_btn = QPushButton("Basic Quali Mode")
        quali_btn.clicked.connect(
            lambda: self.switch_screen(BasicQualiMode(self.state))
        )

        layout.addWidget(sprint_btn)
        layout.addWidget(quali_btn)

        self.setCentralWidget(widget)

    def switch_screen(self, screen):
        self.current_screen = screen
        self.setCentralWidget(screen)

    def route_socket_event(self, data):
        if self.current_screen:
            self.current_screen.handle_flag_input(data)


# ==========================================================
# -------------------- SOCKET SERVER -----------------------
# ==========================================================

sio = socketio.Server(cors_allowed_origins="*")
app = socketio.WSGIApp(
    sio,
    static_files={
        '/': os.path.join(os.getcwd(), 'templates', 'index.html'),
        '/static': os.path.join(os.getcwd(), 'static')
    }
)

github_token = os.getenv("GITHUB_TOKEN")
repo = "SlothzDoCode/karting-display"

headers = {
    "Authorization": f"Bearer {github_token}",
    "Accept": "application/vnd.github+json"
}


def add_tracks(): 
    conn = psycopg2.connect( dbname='KDisplay database', user='sql test', password='admin', host='127.0.0.1', port=5432) 
    cur = conn.cursor() 
    script = "INSERT INTO track_info (track_name, start_long, start_lat, track_map_location) VALUES ('Teamsport Leicester', 52.6634236214469, -1.0852487112926859, 'https://images.prismic.io/teamsport/aCsFJSdWJ-7kSSSj_Teamsport_Trackmap_LEICESTER_1440px.png?auto=format,compress')" 
    cur.execute(script) 
    conn.commit() 

def get_track_info(): 
    conn = psycopg2.connect( dbname='KDisplay database', user='sql test', password='admin', host='127.0.0.1', port=5432) 
    cur = conn.cursor() 
    script = "SELECT track_name FROM track_info" 
    cur.execute(script) 
    rows = cur.fetchall() 
    return rows 

def get_track_map(location): 
    conn = psycopg2.connect( dbname='KDisplay database', user='sql test', password='admin', host='127.0.0.1', port=5432) 
    print(location)
    cur = conn.cursor() 
    script = "SELECT track_map_location FROM track_info WHERE track_name=%s" 
    cur.execute(script,(location,)) 
    rows = cur.fetchone() 
    print(rows) 
    return rows


@sio.event
def connect(sid, environ):
    print("Client connected:", sid)
    sio.emit("Track-setup",get_track_info())

@sio.event
def bug_report(sid, data):
    print("Token:", github_token)
    title = data["title"]
    description = data["description"]
    ua = data.get("user_agent", "unknown")
    
    body = f"""
    ### Bug Report
    
    {description}
    
    ### User Agent
    
    {ua}
    """
    
    issue_data = {
        "title":title,
        "body":body,
        "labels": ["bug"]
    }
    
    r = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        json=issue_data,
        headers=headers
    )
    
    if r.status_code == 201:
        sio.emit("bug_report_status", {"status": "ok"}, to=sid)
    else:
        sio.emit("bug_report_status", {"status": "error"}, to=sid)


@sio.event
def index_handle_input(sid, data):
    if data in [item[0] for item in get_track_info()]:
        url = get_track_map(data) 
        if url: sio.emit("return-values", url)
    else:
        global_signals.socket_event.emit(data)

@sio.event 
def login_handle_input(sid, data): 
    #login validation goes here 
    response = True #this is a testing variable remove when doing the login validation if response == True: 
    sio.emit("login_response", "valid login") 

@sio.event 
def signup_handle_input(sid, data): 
    pass

@sio.event
def disconnect(sid):
    print("Client disconnected:", sid)


def run_server():
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    eventlet.wsgi.server(eventlet.listen((IPAddr, 5000)), app)


# ==========================================================
# ------------------------- RUN ----------------------------
# ==========================================================

if __name__ == "__main__":

    threading.Thread(target=run_server, daemon=True).start()

    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(qt_app.exec())
