import pyqtgraph as pg
from pyqtgraph import QtGui
from pyqtgraph.dockarea import Dock, DockArea
import xml.etree.ElementTree as ET

tree = ET.parse('config.xml')
root = tree.getroot()

# Check for detector
# Check for instrument
# Check for energy
    # Process variables for HKL reading if necessary
# Check for ROI's
    # Create ROI's if necessary
# Create necessary docks

class MainWindow(DockArea):
    def __init__(self) -> None:
        super().__init__()

class ImagePlot(pg.ImageView):
    def __init__(self) -> None:
        super().__init__()

class LinePlot(pg.PlotWidget):
    def __init__(self) -> None:
        super().__init__()

class MouseInfoWidget(QtGui.QGroupBox):
    def __init__(self) -> None:
        super().__init__()

class StatsInfoWidget(QtGui.QGroupBox):
    def __init__(self) -> None:
        super().__init__()

class OptionsWidget(QtGui.QWidget):
    def __init__(self) -> None:
        super().__init__()

app = pg.mkQApp("Live Image")
window = MainWindow()
window.show()
pg.mkQApp().exec_()
