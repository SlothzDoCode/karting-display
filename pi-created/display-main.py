import sys
import threading
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtCore import pyqtSlot
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
from datetime import datetime
import socket
import eventlet
from shapely.geometry import LineString, Point

active = None

#-------------------- PyQt6 GUI ---------------------#

class stateManager:
	_instance = None
	
	def __new__(cls):
		if cls._instance == None:
			cls._instance = super().__new__(cls)
			cls._instance.current_bg = "black"
			cls._instance.fg_dark = "black"
			cls._instance.fg_light = "white"
			cls._instance.positions = [f"pos {i}" for i in range(1,17)]
			cls._instance.countdown_timer = [f"timer{i*5}" for i in range(1,288)]
			cls._instance.current_pos = "0"
			cls._instance.now = datetime.now()
		return cls._instance

class Communicate(QObject):
	update_label = pyqtSignal(object)
	
class MainWindow(QMainWindow): #? main menu window
	def __init__(self):
		super().__init__()
		self.tempLock = True
		
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
		self.enduroOption.setEnabled(True) #! remove once section is complete
		self.enduroOption.setStyleSheet("font-size: 20px")
		self.enduroOption.setFixedSize(220, 70)
		self.enduroOption.clicked.connect(lambda: self.switch_screen(enduroMode()))
		menu_layout.addWidget(self.enduroOption)
		
		self.setCentralWidget(self.menu_widget)
		
	def switch_screen(self, screen_widget):
		global active
		active = screen_widget
		self.setCentralWidget(screen_widget)
			
class sprintMode(QWidget): #? shows flag state, time left in session, position
	
		def __init__(self):
			super().__init__()
		
			#fixed variable names
			self.state = stateManager()
			
			self.comm = Communicate()
			self.comm.update_label.connect(self.handle_flag_input)
			
			self.layout = QVBoxLayout(self)
			
			self.positionTxt = QLabel("0", self)
			self.positionTxt.setStyleSheet("font-size: 40px")
			self.positionTxt.move(200,400)
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
			if self.reSec > 3600:
				hour = self.reSec // 3600
				mins = (self.reSec % 3600) // 60
				secs = self.reSec % 60
				self.timerTxt.setText(f"{hour:02}:{mins:02}:{secs:02}")
				self.timerTxt.adjustSize()
			else:
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
				self.state.current_bg = "#009639"
				self.window().setStyleSheet(f"background-color: {self.state.current_bg}")
			
			elif data == "Yellow Flag":
				self.state.current_bg = "#ffd100"
				self.flash_flag([self.state.current_bg, "#000000"], 800)
				
			elif data == "Red Flag":
				self.state.current_bg = "#da291c"
				self.flash_flag([self.state.current_bg, "#000000"], 1200)
			
			elif data == "Blue Flag":
				self.window().setStyleSheet("background-color: #00a3e0")
				QTimer.singleShot(5000, lambda: self.window().setStyleSheet(f"background-color: {self.state.current_bg}"))
				
			elif data == "PB":
				self.window().setStyleSheet("background-color: #dcb023")
				QTimer.singleShot(5000, lambda: self.window().setStyleSheet(f"background-color: {self.state.current_bg}"))
				
			elif data == "Pitstop":
				self.window().setStyleSheet("background-color: #800080")
				QTimer.singleShot(5000, lambda: self.window().setStyleSheet(f"background-color: {self.state.current_bg}"))
				
			elif data in self.state.countdown_timer:
				self.startTimer(int(data[4:]) * 60)
			
			elif data in self.state.positions:
				self.positionTxt.setText(data[3:] + self.posEnd(int(data[3:].strip())))
				self.positionTxt.adjustSize()

class basicQualiMode(QWidget):
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
		self.window().setStyleSheet(f"background-color: {color}; color:{text_color}")
		self.flash_index = (self.flash_index + 1) % len(self.flash_colors)
		
	def flash_flag(self, colors, interval_ms):
		self.flash_colors = colors
		self.flash_index = 0
		self.flash_timer.start(interval_ms)
	
	def startLapTimer(self):
		self.lap_start_time = datetime.now()
		self.running = True
		self.lap_timer.start(10)
		
	def stopLapTimer(self):
		self.running= False
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
		Expected data = "Lap Start" or other flagstrings.
		When "Lap Start" arrives:
		- If a lap was running, store the just-finished lap text and display it for 3s.
		- Immediately start the next lap.
		- color the lap time:
			- purple = fastest lap so far
			- green = quicker than previous lap
			- yellow = slower than previous lap
		"""
		if data  == "Lap Start" or data == "End Session":
			if self.running:
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
						color = "purple" #fastest lap
						self.fastest_lap_ms = total_ms
					elif total_ms < self.previous_lap_ms:
						color = "green"
					else:
						color = "yellow"
				else:
					self.fastest_lap_ms = total_ms
					color = "purple"
				
				self.previous_lap_ms = total_ms
				self.last_lap_time_text = self.current_lap_text
				
				self.lapTimerTxt.setText(self.last_lap_time_text)
				self.lapTimerTxt.setStyleSheet(f"font-size: 40px; color: {color}")
				QTimer.singleShot(3000, self.restore_current_lap_display)
				
				if data == "End Session":
					self.running = False
				else:
					self.lap_start_time = datetime.now()
				
			else:
				self.startLapTimer()
		
		elif data == "Green Flag":
			self.flash_timer.stop()
			self.state.current_bg = "#009639"
			self.window().setStyleSheet(f"background-color: {self.state.current_bg}")
		
		elif data == "Yellow Flag":
			self.state.current_bg = "#ffd100"
			self.flash_flag([self.state.current_bg, "#000000"], 800)
			
		elif data == "Red Flag":
			self.state.current_bg ="#da291c"
			self.flash_flag([self.state.current_bg, "#000000"], 1200)

class advancedQualiMode(QWidget):
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
		secs = (tital_ms % 60000) // 1000
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
		
		if data == "Lap Start": 
			if self.running:
				
				elapsed = datetime.now() - self.lap_start_time
				total_ms = int(elapsed.total_seconds() * 1000)
				
				mins = total_ms // 60000
				secs = (total_ms % 60000) * 1000
				ms = total_ms % 1000
				
				self.current_lap_text = f"{mins:02}:{secs:02}.{ms:03}"
				
				color = "black"
				if hasattr(self, "fastest_lap_ms"):
					if total_ms < self.fastest_lap_ms:
						color = "purple"
						self.fastest_lap_ms = total_ms
					elif total_ms < self.previous_lap_ms:
						color = "green"
					else: 
						color = "Yellow"
				else:
					self.fastest_lap_ms = total_ms
					color = "purple"
				
				self.previous_lap_ms = total_ms
				self.last_lap_time_text = self.current_lap_text
				
				self.lapTimerTxt.setText(self.last_lap_time_text)
				self.lapTimerTxt.setStyleSheet(f"font-size: 40px; color: {color}")
				Qtimer.singleShot(3000, self.restore_current_)
				
				self.lap_start_time = datetime.now()
			else:
				self.startLapTimer()
		
		elif data == "Green Flag":
			self.flash_timer.stop()
			self.state.current_bg = "#009639"
			self.window().setStyleSheet(f"background-color: {self.state.current_bg}")
		
		elif data == "Yellow Flag":
			self.state.current_bg = "#ffd100"
			self.flash_flag([self.state.current_bg, "#000000"], 800)
			
		elif data == "Red Flag":
			self.state.current_bg ="#da291c"
			self.flash_flag([self.state.current_bg, "#000000"], 1200)

class enduroMode(QWidget):
	def __init__(self):
		super().__init__()
		
		self.state = stateManager()
		
		self.comm = Communicate()
		self.comm.update_label.connect(self.handle_flag_input)
		
		self.layout = QVBoxLayout(self)
		
		self.session_time = 0
		
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
		if self.reSec > 3600:
			hour = self.reSec // 3600
			mins = (self.reSec % 3600) // 60
			secs = self.reSec % 60
			self.timerTxt.setText(f"{hour:02}:{mins:02}:{secs:02}")
			self.timerTxt.adjustSize()
		else:
			mins = self.reSec // 60
			secs = self.reSec % 60
			self.timerTxt.setText(f"{mins:02}:{secs:02}")
			self.timerTxt.adjustSize()
		
		if self.reSec > 0:
			self.reSec -= 1
		else:
			self.timer.stop()
			
	def posEnd(self, pos):
		if 10 <= pos % 100 <= 20:
			return "th"
		else:
			return {1: 'st', 2: 'nd', 3: 'rd'}.get(pos % 10, 'th')
		
	def createTable(self, driverNames, stintLength):
		self.table = QTableWidget(len(driverNames)-1,2)
		self.table.setHorizontalHeaderLabels(["Name", "Stint Time"])
			
		for i in range(len(driverNames)-1):
			self.table.setItem(i,0, QTableWidgetItem(driverNames[i]))
			self.table.setItem(i,1, QTableWidgetItem(stintLength))
		
		self.startTimer(self.session_time)
	
	@pyqtSlot(object)
	def handle_flag_input(self, data):
		print(f"!!!{data}!!!")
		if data == "Green Flag":
			self.flash_timer.stop()
			self.state.current_bg = "#009639"
			self.window().setStyleSheet(f"background-color: {self.state.current_bg}")
		
		elif data == "Yellow Flag":
			self.state.current_bg = "#ffd100"
			self.flash_flag([self.state.current_bg, "#000000"], 800)
			
		elif data == "Red Flag":
			self.state.current_bg = "#da291c"
			self.flash_flag([self.state.current_bg, "#000000"], 1200)
			
		elif data == "Blue Flag":
			self.window().setStyleSheet("background-color: #00a3e0")
			QTimer.singleShot(5000, lambda: self.window().setStyleSheet(f"background-color: {self.state.current_bg}"))
			
		elif data == "PB":
			self.window().setStyleSheet("background-color: #dcb023")
			QTimer.singleShot(5000, lambda: self.window().setStyleSheet(f"background-color: {self.state.current_bg}"))
			
		elif data == "Pitstop":
			self.window().setStyleSheet("background-color: #800080")
			QTimer.singleShot(5000, lambda: self.window().setStyleSheet(f"background-color: {self.state.current_bg}"))
		
		elif data in self.state.countdown_timer:
			self.session_time = int(data[5:]) * 60
			
		elif data in self.state.positions:
			self.positionTxt.setText(data[3:] + self.posEnd(int(data[3:].strip())))
			self.positionTxt.adjustSize()
		
		elif isinstance(data, dict):
			self.createTable(data, self.session_time)
				
#--------------- flask+socketio ----------------#
flask_app = Flask(__name__)
CORS(flask_app)
socketio = SocketIO(flask_app, cors_allowed_origins="*", manage_session=True, async_mode="threading")

@socketio.on('flag_status')
def handle_flag(data):
	print(f"Recived: {data} \n data type: {type(data)}")
	global active
	
	if active:
		if isinstance(data, str):
			print(1)
			QMetaObject.invokeMethod(
				active,
				"handle_flag_input",
				Qt.ConnectionType.QueuedConnection,
				Q_ARG(object,data)
			)
		elif isinstance(data, dict):
			print(2)
			QMetaObject.invokeMethod(
				active,
				"handle_flag_input",
				Qt.ConnectionType.QueuedConnection,
				Q_ARG(object,data)
			)
		
#------------------- Run Flask -----------------#

def run_flask():
	socketio.run(flask_app, debug=True, use_reloader=False, host='192.168.1.76', port=5000)

#----------------- run pyqt GUI ----------------#

if __name__ == "__main__":
	threading.Thread(target=run_flask, daemon=True).start()
	
	#? Start PyQt app
	
	qt_app = QApplication(sys.argv)
	window = MainWindow()
	window.showFullScreen()
	sys.exit(qt_app.exec())
