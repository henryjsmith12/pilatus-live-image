import pyqtgraph as pg
from pyqtgraph import QtGui
from pyqtgraph.dockarea import Dock, DockArea
import xml.etree.ElementTree as ET

tree = ET.parse('config.xml')
root = tree.getroot()
for child in root:
    if child.tag == "detector":
        IMAGE_PV = child.find("image").attrib["pv"]
        IMAGE_TOTAL_PV = child.find("image_total").attrib["pv"]
        IMAGE_MAX_PV = child.find("image_max").attrib["pv"]
        PIXEL_DIR_1 = child.find("pixel_direction_1").text 
        PIXEL_DIR_2 = child.find("pixel_direction_2").text   
        C_CH_1 = int(child.find("center_channel_pixel").text.split()[0])
        C_CH_2 = int(child.find("center_channel_pixel").text.split()[1])
        N_CH_1 = int(child.find("n_pixels").text.split()[0])
        N_CH_2 = int(child.find("n_pixels").text.split()[1])
        PIXEL_WIDTH_1 = float(child.find("size").text.split()[0]) / N_CH_1
        PIXEL_WIDTH_2 = float(child.find("size").text.split()[1]) / N_CH_2
    elif child.tag == "instrument":
        ...
    elif child.tag == "rois":
        ...
    elif child.tag == "energy":
        ...
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

'''
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
'''
'''
app = pg.mkQApp("Live Image")
window = MainWindow()
window.show()
pg.mkQApp().exec_()
'''