from ctypes.wintypes import HKL
import numpy as np
import pyqtgraph as pg
from pyqtgraph import QtGui
from pyqtgraph.dockarea import Dock, DockArea
import xml.etree.ElementTree as ET

global HKL_MODE
global ROI_MODE

HKL_MODE, ROI_MODE = True, True

tree = ET.parse('config.xml')
root = tree.getroot()
for child in root:
    if child.tag == "detector":
        IMAGE_PV = child.find("image").attrib["pv"]
        try:
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
            DISTANCE = float(child.find("distance").text)
            ROI = [0, N_CH_1, 0, N_CH_2]
        except:
            HKL_MODE = False
    elif child.tag == "instrument":
        try:
            sample_circles = child.find("sample_circles")
            SAMPLE_CIRCLE_DIRECTIONS, SAMPLE_CIRCLE_NAMES, SAMPLE_CIRCLE_PV_LIST = [], [], []
            for circle_axis in sample_circles:
                SAMPLE_CIRCLE_NAMES.append(circle_axis.attrib["spec_motor_name"])
                SAMPLE_CIRCLE_DIRECTIONS.append(circle_axis.attrib["direction_axis"])
                SAMPLE_CIRCLE_PV_LIST.append(circle_axis.attrib["pv"])
            detector_circles = child.find("detector_circles")
            DET_CIRCLE_DIRECTIONS, DET_CIRCLE_NAMES, DET_CIRCLE_PV_LIST = [], [], []
            for circle_axis in detector_circles:
                DET_CIRCLE_NAMES.append(circle_axis.attrib["spec_motor_name"])
                DET_CIRCLE_DIRECTIONS.append(circle_axis.attrib["direction_axis"])
                DET_CIRCLE_PV_LIST.append(circle_axis.attrib["pv"])
            PRIMARY_BEAM_DIR = [int(axis.text) for axis in child.find("primary_beam_direction")]
            INPLANE_REF_DIR = [int(axis.text) for axis in child.find("inplane_reference_direction")]
            SAMPLE_NORM_DIR = [int(axis.text) for axis in child.find("sample_surface_normal_direction")]
            UB_MATRIX_PV = child.find("ub_matrix").attrib["pv"]
        except:
            HKL_MODE = False
    elif child.tag == "rois":
        try:
            ROI_PV_LIST = [{}, {}, {}, {}]
            for roi in child:
                ...
        except:
            ROI_MODE = False
    elif child.tag == "energy":
        try:
            ENERGY_PV = child.attrib["pv"]
        except:
            HKL_MODE = False


if HKL_MODE:
    ...

if ROI_MODE:
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