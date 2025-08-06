import psutil
from py3nvml import py3nvml as nvml
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QStatusBar, QLineEdit, QLabel

from tools.desktop import CPU_DEVICE, GPU_NAME, CPU_USAGE_UPDATE_RATE


class StatusBar(QStatusBar):

    def __init__(self, parent=None):
        super(StatusBar, self).__init__(parent)

        self.handle = nvml.nvmlDeviceGetHandleByIndex(0)

        self.ram_last = 0

        self.ram_percent = QLineEdit()
        self.cpu_usage = QLineEdit()
        self.cpu_state = QLineEdit(CPU_DEVICE.upper())
        self.gpu_name = QLineEdit(GPU_NAME)
        self.gpu_core_usage = QLineEdit()
        self.gpu_ram_usage = QLineEdit()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_sensors)
        self.timer.start(CPU_USAGE_UPDATE_RATE)

        self.config()

    def config(self):
        self.ram_percent.setReadOnly(True)
        self.ram_percent.setFixedWidth(100)
        self.ram_percent.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.cpu_usage.setReadOnly(True)
        self.cpu_usage.setFixedWidth(50)
        self.cpu_usage.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Label in der Statusleiste für dynamische Inhalte
        self.cpu_state = QLineEdit(CPU_DEVICE.upper())
        self.cpu_state.setReadOnly(True)
        self.cpu_state.setFixedWidth(50)

        self.gpu_name = QLineEdit(GPU_NAME)
        self.gpu_name.setReadOnly(True)
        self.gpu_name.setFixedWidth(150)

        self.gpu_core_usage.setReadOnly(True)
        self.gpu_core_usage.setFixedWidth(50)
        self.gpu_core_usage.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.gpu_ram_usage.setReadOnly(True)
        self.gpu_ram_usage.setFixedWidth(50)
        self.gpu_ram_usage.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Widgets hinzufügen
        self.addPermanentWidget(QLabel("CPU-Last:"))
        self.addPermanentWidget(self.cpu_usage)
        self.addPermanentWidget(QLabel("RAM-Rate:"))
        self.addPermanentWidget(self.ram_percent)
        self.addPermanentWidget(QLabel("Architektur:"))
        self.addPermanentWidget(self.cpu_state)
        self.addPermanentWidget(QLabel("GPU:"))
        self.addPermanentWidget(self.gpu_name)
        self.addPermanentWidget(QLabel("GPU-Last:"))
        self.addPermanentWidget(self.gpu_core_usage)
        self.addPermanentWidget(QLabel("VRAM-Last:"))
        self.addPermanentWidget(self.gpu_ram_usage)

    def update_system_sensors(self):
        usage = psutil.cpu_percent(interval=None)
        ram_used = psutil.virtual_memory().used
        ram_current = abs(ram_used - self.ram_last) / 1024 ** 3
        self.cpu_usage.setText(f"{usage:.1f} %")
        self.ram_percent.setText(f"{ram_current:.3f} GB/s")
        self.ram_last = ram_used

        util = nvml.nvmlDeviceGetUtilizationRates(self.handle)
        self.gpu_core_usage.setText(f"{util.gpu:.1f} %")
        self.gpu_ram_usage.setText(f"{util.memory:.1f} %")