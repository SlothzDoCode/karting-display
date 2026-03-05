import sys
import threading
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
from datetime import datetime

active = None

# ---------------- PyQt6 GUI ----------------

class stateManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance == None:
            cls._instance = super().__new__(cls)
            cls._instance.current_bg = "black"
            cls._instance.fg_dark = "black"
            cls._instance.fg_light = "white"
            cls._instance.positions = [f"pos {i}" for i in range(1, 17)]
            cls._instance.countdown_timer = [f"time{i*5}" for i in range(1, 20)]
            cls._instance.current_pos = "0"
            cls._instance.now = datetime.now()
        return cls._instance

class Communicate(QObject):
    update_label = pyqtSignal(str)

class MainWindow(QMainWindow): #? main menu window
    def __init__(self):
        super().__init__()
        self.tempLock = False

        self.show_menu()

    def show_menu(self):
        self.menu_widget = QWidget()
        menu_layout = QVBoxLayout(self.menu_widget)

        self.sprintOption = QPushButton("Sprint Mode")
        self.sprintOption.setStyleSheet("font-size: 20px")
        self.sprintOption.setFixedSize(220, 70)
        self.sprintOption.clicked.connect(lambda: self.switch_screen(sprintMode()))
        self.sprintOption.setEnabled(self.tempLock)
        menu_layout.addWidget(self.sprintOption)

        self.BasicQualiOption = QPushButton("Basic Quali Mode")
        self.BasicQualiOption.setStyleSheet("font-size: 20px")
        self.BasicQualiOption.setFixedSize(220, 70)
        self.BasicQualiOption.clicked.connect(lambda: self.switch_screen(basicQualiMode()))
        self.BasicQualiOption.setEnabled(self.tempLock)
        menu_layout.addWidget(self.BasicQualiOption)
        
        self.AdvancedQualiOption = QPushButton("Advanced Quali Mode")
        self.AdvancedQualiOption.setEnabled(False) #! remove once section is complete
        self.AdvancedQualiOption.setStyleSheet("font-size: 20px")
        self.AdvancedQualiOption.setFixedSize(220, 70)
        self.AdvancedQualiOption.clicked.connect(lambda: self.switch_screen(advancedQualiMode()))
        menu_layout.addWidget(self.AdvancedQualiOption)
        
        self.enduroOption = QPushButton("Enduro Mode")
        self.enduroOption.setEnabled(False) #! remove once section is complete
        self.enduroOption.setStyleSheet("font-size: 20px")
        self.enduroOption.setFixedSize(220, 70)
        self.enduroOption.clicked.connect(lambda: self.switch_screen(enduroMode()))
        menu_layout.addWidget(self.enduroOption)

        self.setCentralWidget(self.menu_widget)

    def switch_screen(self, screen_widget):
        self.setCentralWidget(screen_widget)

class sprintMode(QWidget): #? shows flag state, time left in position, position
        
    def __init__(self):
        super().__init__()
        
        # Fixed variable names 
        self.state = stateManager()
        
        self.comm = Communicate() 
        self.comm.update_label.connect(self.handle_flag_input)
        
        self.layout = QVBoxLayout(self)

        self.positionTxt = QLabel("0", self)
        self.positionTxt.setStyleSheet("font-size: 40px")
        self.positionTxt.move(200, 400)
        self.positionTxt.adjustSize()

        self.timerTxt = QLabel("Session Timer", self)
        self.timerTxt.setStyleSheet("font-size: 40px")
        self.timerTxt.move(800, 400)
        self.timerTxt.adjustSize()
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateTimer)

        self.clock = QLabel(self)
        self.clock.setText(self.state.now.strftime('%H:%M'))
        self.clock.move(1365, 0)
        self.clock.setStyleSheet("font-size: 20px")
        self.clock.adjustSize()
        self.clockTimer = QTimer()
        self.clockTimer.timeout.connect(self.updateClock)
        self.clockTimer.start(1000)
            
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self._flash_background)
        self.flash_colors = []
        self.flash_index = 0
        self.state.current_bg = "black"

    def updateClock(self):
        self.state.now = datetime.now()
        self.clock.setText(self.state.now.strftime('%H:%M'))
        self.clock.adjustSize()
    
    def _flash_background(self):
        if not self.flash_colors:
            self.flash_timer.stop()
            return
        color = self.flash_colors[self.flash_index]
        if color == "#000000":
            text_color = self.state.fg_light
        else:
            text_color = self.state.fg_dark 
        self.window().setStyleSheet(f"background-color: {color}; color: {text_color}")   
        self.flash_index = (self.flash_index + 1) % len(self.flash_colors)

    def flash_flag(self, colors, interval_ms):
        self.flash_colors = colors
        self.flash_index = 0
        self.flash_timer.start(interval_ms)
        
    def startTimer(self, sec):
        self.reSec = sec
        self.updateTimer()
        self.timer.start(1000)
        
    def updateTimer(self):
        mins = self.reSec // 60
        secs = self.reSec % 60
        self.timerTxt.setText(f"{mins:02}:{secs:02}")
        self.timerTxt.adjustSize()

        if self.reSec > 0:
            self.reSec -= 1
        else:
            self.timer.stop()
            
    def posEnd(self, pos):
        if 10 <= pos % 100 <=20:
            return "th"
        else:
            return {1: 'st', 2: 'nd', 3: 'rd'}.get(pos % 10, 'th')

    @pyqtSlot(str)
    def handle_flag_input(self, data):
        if data == "Green Flag":
            self.flash_timer.stop()
            self.state.current_bg = "#00FF00"
            self.window().setStyleSheet(f"background-color: {self.state.current_bg}")
        
        elif data == "Yellow Flag":
            self.state.current_bg = "#FFFF00"
            self.flash_flag([self.state.current_bg, "#000000"], 800)
        
        elif data == "Red Flag":
            self.state.current_bg = "#FF0000"
            self.flash_flag([self.state.current_bg, "#000000"], 1200)
        
        elif data == "Blue Flag":
            self.window().setStyleSheet("background-color: #0000FF")
            QTimer.singleShot(5000, lambda: self.window().setStyleSheet(f"background-color: {self.state.current_bg}"))
        
        elif data == "PB":
            self.window().stylesheet("background-color: #a28834")
            QTimer.singleShot(5000, lambda: self.window().styleSheet(f"background-color: {self.state.current_bg}"))
        
        elif data == "Pitstop":
            self.window.stylesheet("background-color: #c115d4")
            QTimer.singleShot(5000, lambda: self.window().styleSheet(f"background-color: {self.state.current_bg}"))
        
        elif data in self.state.countdown_timer:
            self.startTimer(int(data[4:]) * 60)
        
        elif data in self.state.positions:
            self.positionTxt.setText(data[3:] + self.posEnd(int(data[3:].strip())))
            self.positionTxt.adjustSize()    

class basicQualiMode(QWidget): #? shows flag states, laptimes, how it was relative to overall session and previous lap
    def __init__(self):
        super().__init__()
        
        self.state = stateManager()
        
        self.comm = Communicate() 
        self.comm.update_label.connect(self.handle_flag_input)
        
        self.layout = QVBoxLayout(self)
        
        self.lapTimerTxt = QLabel("00:00.000", self)
        self.lapTimerTxt.setStyleSheet("font-size: 40px")
        self.lapTimerTxt.move(570,400)
        self.lapTimerTxt.adjustSize()
    
        self.lap_timer = QTimer()
        self.lap_timer.timeout.connect(self.updateLapTimer)
        self.lap_timer.setTimerType(Qt.TimerType.PreciseTimer)

        self.lap_start_time = None
        self.running = False
        self.current_lap_text = "00:00.000"
        self.last_lap_time_text = None
        
        self.clock = QLabel(self)
        self.clock.setText(self.state.now.strftime('%H:%M'))
        self.clock.move(1365, 0)
        self.clock.setStyleSheet("font-size: 20px")
        self.clock.adjustSize()
        self.clockTimer = QTimer()
        self.clockTimer.timeout.connect(self.updateClock)
        self.clockTimer.start(1000)
            
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self._flash_background)
        self.flash_colors = []
        self.flash_index = 0
        self.state.current_bg = "black"

    def updateClock(self):
        self.state.now = datetime.now()
        self.clock.setText(self.state.now.strftime('%H:%M'))
        self.clock.adjustSize()
    
    def _flash_background(self):
        if not self.flash_colors:
            self.flash_timer.stop()
            return
        color = self.flash_colors[self.flash_index]
        if color == "#000000":
            text_color = self.state.fg_light
        else:
            text_color = self.state.fg_dark 
        self.window().setStyleSheet(f"background-color: {color}; color: {text_color}")   
        self.flash_index = (self.flash_index + 1) % len(self.flash_colors)

    def startLapTimer(self):
        self.lap_start_time = datetime.now()
        self.running = True
        self.lap_timer.start(10)

    def stopLapTimer(self):
        self.running = False
        self.lap_timer.stop()

    def updateLapTimer(self):
        if not self.running or self.lap_start_time is None:
            return

        elapsed = datetime.now() - self.lap_start_time
        total_ms = int(elapsed.total_seconds() * 1000)

        mins = total_ms // 60000
        secs = (total_ms % 60000) // 1000
        ms = total_ms % 1000

        self.current_lap_text = f"{mins:02}:{secs:02}.{ms:03}"
        if self.last_lap_time_text is None:
            self.lapTimerTxt.setText(self.current_lap_text)

    def restore_current_lap_display(self):
        self.last_lap_time_text = None
        self.lapTimerTxt.setText(self.current_lap_text)
        self.lapTimerTxt.setStyleSheet("font-size: 40px; color: black")

    @pyqtSlot(str)
    def handle_flag_input(self, data):
        """
        Expected data = "Lap Start" or other flag strings.
        When "Lap Start" arrives:
        - If a lap was running, store the just-finished lap text and display it for 3s.
        - Immediately start the next lap.
        - Color the lap time:
            - Purple = fastest lap so far
            - Green = quicker than previous lap
            - Yellow = slower than previous lap
        """
        if data == "Lap Start":
            if self.running:
                # compute current lap time
                elapsed = datetime.now() - self.lap_start_time
                total_ms = int(elapsed.total_seconds() * 1000)

                mins = total_ms // 60000
                secs = (total_ms % 60000) // 1000
                ms = total_ms % 1000

                self.current_lap_text = f"{mins:02}:{secs:02}.{ms:03}"

                # Determine color
                color = "black"
                if hasattr(self, "fastest_lap_ms"):
                    if total_ms < self.fastest_lap_ms:
                        color = "purple"  # fastest lap
                        self.fastest_lap_ms = total_ms
                    elif total_ms < self.previous_lap_ms:
                        color = "green"  # faster than previous
                    else:
                        color = "yellow"  # slower than previous
                else:
                    # First lap ever
                    self.fastest_lap_ms = total_ms
                    color = "purple"

                self.previous_lap_ms = total_ms
                self.last_lap_time_text = self.current_lap_text

                # Show finished lap for 3 seconds
                self.lapTimerTxt.setText(self.last_lap_time_text)
                self.lapTimerTxt.setStyleSheet(f"font-size: 40px; color: {color}")
                QTimer.singleShot(3000, self.restore_current_lap_display)

                # Start next lap immediately
                self.lap_start_time = datetime.now()

            else:
                self.startLapTimer()
                
        elif data == "Green Flag":
            self.flash_timer.stop()
            self.state.current_bg = "#00FF00"
            self.window().setStyleSheet(f"background-color: {self.state.current_bg}")
        
        elif data == "Yellow Flag":
            self.state.current_bg = "#FFFF00"
            self.flash_flag([self.state.current_bg, "#000000"], 800)
        
        elif data == "Red Flag":
            self.state.current_bg = "#FF0000"
            self.flash_flag([self.state.current_bg, "#000000"], 1200)        

class advancedQualiMode(QWidget): #? this will do all that basic does + live time delta tracking
    def __init__(self):
        
        self.state = stateManager()
        
        self.comm = Communicate() 
        self.comm.update_label.connect(self.handle_flag_input)
        
        self.layout = QVBoxLayout(self)
        
        self.lapTimerTxt = QLabel("00:00.000", self)
        self.lapTimerTxt.setStyleSheet("font-size: 40px")
        self.lapTimerTxt.move(570,400)
        self.lapTimerTxt.adjustSize()
    
        self.lap_timer = QTimer()
        self.lap_timer.timeout.connect(self.updateLapTimer)
        self.lap_timer.setTimerType(Qt.TimerType.PreciseTimer)

        self.lap_start_time = None
        self.running = False
        self.current_lap_text = "00:00.000"
        self.last_lap_time_text = None
        
        self.clock = QLabel(self)
        self.clock.setText(self.state.now.strftime('%H:%M'))
        self.clock.move(1365, 0)
        self.clock.setStyleSheet("font-size: 20px")
        self.clock.adjustSize()
        self.clockTimer = QTimer()
        self.clockTimer.timeout.connect(self.updateClock)
        self.clockTimer.start(1000)
            
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self._flash_background)
        self.flash_colors = []
        self.flash_index = 0
        self.state.current_bg = "black"

    def updateClock(self):
        self.state.now = datetime.now()
        self.clock.setText(self.state.now.strftime('%H:%M'))
        self.clock.adjustSize()
    
    def _flash_background(self):
        if not self.flash_colors:
            self.flash_timer.stop()
            return
        color = self.flash_colors[self.flash_index]
        if color == "#000000":
            text_color = self.state.fg_light
        else:
            text_color = self.state.fg_dark 
        self.window().setStyleSheet(f"background-color: {color}; color: {text_color}")   
        self.flash_index = (self.flash_index + 1) % len(self.flash_colors)

    def startLapTimer(self):
        self.lap_start_time = datetime.now()
        self.running = True
        self.lap_timer.start(10)

    def stopLapTimer(self):
        self.running = False
        self.lap_timer.stop()

    def updateLapTimer(self):
        if not self.running or self.lap_start_time is None:
            return

        elapsed = datetime.now() - self.lap_start_time
        total_ms = int(elapsed.total_seconds() * 1000)

        mins = total_ms // 60000
        secs = (total_ms % 60000) // 1000
        ms = total_ms % 1000

        self.current_lap_text = f"{mins:02}:{secs:02}.{ms:03}"
        if self.last_lap_time_text is None:
            self.lapTimerTxt.setText(self.current_lap_text)

    def restore_current_lap_display(self):
        self.last_lap_time_text = None
        self.lapTimerTxt.setText(self.current_lap_text)
        self.lapTimerTxt.setStyleSheet("font-size: 40px; color: black")

    @pyqtSlot(str)
    def handle_flag_input(self, data):
        """
        Expected data = "Lap Start" or other flag strings.
        When "Lap Start" arrives:
        - If a lap was running, store the just-finished lap text and display it for 3s.
        - Immediately start the next lap.
        - Color the lap time:
            - Purple = fastest lap so far
            - Green = quicker than previous lap
            - Yellow = slower than previous lap
        """
        if data == "Lap Start":
            if self.running:
                # compute current lap time
                elapsed = datetime.now() - self.lap_start_time
                total_ms = int(elapsed.total_seconds() * 1000)

                mins = total_ms // 60000
                secs = (total_ms % 60000) // 1000
                ms = total_ms % 1000

                self.current_lap_text = f"{mins:02}:{secs:02}.{ms:03}"

                # Determine color
                color = "black"
                if hasattr(self, "fastest_lap_ms"):
                    if total_ms < self.fastest_lap_ms:
                        color = "purple"  # fastest lap
                        self.fastest_lap_ms = total_ms
                    elif total_ms < self.previous_lap_ms:
                        color = "green"  # faster than previous
                    else:
                        color = "yellow"  # slower than previous
                else:
                    # First lap ever
                    self.fastest_lap_ms = total_ms
                    color = "purple"

                self.previous_lap_ms = total_ms
                self.last_lap_time_text = self.current_lap_text

                # Show finished lap for 3 seconds
                self.lapTimerTxt.setText(self.last_lap_time_text)
                self.lapTimerTxt.setStyleSheet(f"font-size: 40px; color: {color}")
                QTimer.singleShot(3000, self.restore_current_lap_display)

                # Start next lap immediately
                self.lap_start_time = datetime.now()

            else:
                self.startLapTimer()
                
        elif data == "Green Flag":
            self.flash_timer.stop()
            self.state.current_bg = "#00FF00"
            self.window().setStyleSheet(f"background-color: {self.state.current_bg}")
        
        elif data == "Yellow Flag":
            self.state.current_bg = "#FFFF00"
            self.flash_flag([self.state.current_bg, "#000000"], 800)
        
        elif data == "Red Flag":
            self.state.current_bg = "#FF0000"
            self.flash_flag([self.state.current_bg, "#000000"], 1200)

class enduroMode(QWidget):
    def __init__(self):
        super().__init__()
        
        self.state = stateManager()
        
        self.comm = Communicate() 
        self.comm.update_label.connect(self.handle_flag_input)
        
        self.layout = QVBoxLayout(self)
        
        def createTable(self, driverNames, stintLength):
            self.table = QTableWidget(len(driverNames)-1,2)
            self.table.setHorizontalHeaderLabels(["Name", "Stint Time"])
            
            for i in range(len(driverNames)-1):
                self.table.setItem(i,0, QTableWidgetItem(driverNames[i]))
                self.table.setItem(i,1, QTableWidgetItem(stintLength))
                
        

# ---------------- Flask + SocketIO ----------------

flask_app = Flask(
    __name__,
    static_folder=r"C:\Users\harry\OneDrive - Nord Anglia Education\Desktop 1\karting display\static",
    template_folder=r"C:\Users\harry\OneDrive - Nord Anglia Education\Desktop 1\karting display\templates"
)
flask_app.url_map.strict_slashes = False
flask_app.secret_key = "aohfeurhljbrklhvei"
CORS(flask_app, supports_credentials=True)
socketio = SocketIO(flask_app, cors_allowed_origins="*", manage_session=True, async_mode="threading")

@flask_app.route('/')
def index():
    return render_template('ControllerFrontend.html')

@socketio.on('flag_status')
def handle_flag(data):
    print(f"Revived: {data}")
    global active
    
    if active:
        QMetaObject.invokeMethod(
            active,
            "handle_flag_input",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str,data)
        )

# ---------------- Run Flask in a separate thread ----------------

def run_flask():
    socketio.run(flask_app, debug=True, use_reloader=False, host='0.0.0.0', port=5000)

# ---------------- Run PyQt GUI ----------------

if __name__ == "__main__":
    #? Start Flask server in daemon thread
    threading.Thread(target=run_flask, daemon=True).start()

    #? Start PyQt app
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(qt_app.exec())



#TODO: Sprint mode (rename default)
#TODO: Longer race mode (pit strategy options)
#TODO: practice mode (everything)
#TODO: speed
#TODO: lap deltas?