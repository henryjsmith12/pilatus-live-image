import epics
import numpy as np
import pyqtgraph as pg
from pyqtgraph import QtGui
from pyqtgraph.dockarea import Dock, DockArea
from sklearn import preprocessing
import xml.etree.ElementTree as ET
import xrayutilities as xu

HKL_MODE, ROI_MODE = True, True

# =====================================================================
# Reads config.xml

tree = ET.parse('config.xml')
root = tree.getroot()
for child in root:
    if child.tag == "detector":
        IMAGE_PV = epics.PV(child.find("image").attrib["pv"])
        try:
            IMAGE_TOTAL_PV = epics.PV(child.find("image_total").attrib["pv"])
            IMAGE_MAX_PV = epics.PV(child.find("image_max").attrib["pv"])
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
            SAMPLE_CIRCLE_DIR, SAMPLE_CIRCLE_NAMES, SAMPLE_CIRCLE_PV_LIST = [], [], []
            for circle_axis in sample_circles:
                SAMPLE_CIRCLE_NAMES.append(circle_axis.attrib["spec_motor_name"])
                SAMPLE_CIRCLE_DIR.append(circle_axis.attrib["direction_axis"])
                SAMPLE_CIRCLE_PV_LIST.append(epics.PV(circle_axis.attrib["pv"]))
            detector_circles = child.find("detector_circles")
            DET_CIRCLE_DIR, DET_CIRCLE_NAMES, DET_CIRCLE_PV_LIST = [], [], []
            for circle_axis in detector_circles:
                DET_CIRCLE_NAMES.append(circle_axis.attrib["spec_motor_name"])
                DET_CIRCLE_DIR.append(circle_axis.attrib["direction_axis"])
                DET_CIRCLE_PV_LIST.append(epics.PV(circle_axis.attrib["pv"]))
            CIRCLE_PV_LIST = SAMPLE_CIRCLE_PV_LIST + DET_CIRCLE_PV_LIST
            PRIMARY_BEAM_DIR = [int(axis.text) for axis in child.find("primary_beam_direction")]
            INPLANE_REF_DIR = [int(axis.text) for axis in child.find("inplane_reference_direction")]
            SAMPLE_NORM_DIR = [int(axis.text) for axis in child.find("sample_surface_normal_direction")]
            Q_CONV = xu.experiment.QConversion(SAMPLE_CIRCLE_DIR, DET_CIRCLE_DIR, PRIMARY_BEAM_DIR)
            UB_MATRIX_PV = epics.PV(child.find("ub_matrix").attrib["pv"])
        except:
            HKL_MODE = False
    elif child.tag == "rois":
        try:
            ROI_PV_LIST = [{}, {}, {}, {}]
            for roi, roi_pv_dict in zip(child, ROI_PV_LIST):
                for roi_attr in roi:
                    roi_pv_dict[roi_attr.tag] = epics.PV(roi_attr.attrib["pv"])
        except:
            ROI_MODE = False
    elif child.tag == "energy":
        try:
            ENERGY_PV = epics.PV(child.attrib["pv"])
        except:
            HKL_MODE = False

# =====================================================================
# UI classes

class MainWindow(DockArea):
    def __init__(self) -> None:
        super().__init__()

        self.resize(500, 500)

        self.image_plot = ImagePlot(parent=self)
        self.x_line_plot = pg.PlotWidget(parent=self)
        self.y_line_plot = pg.PlotWidget(parent=self)
        self.options_widget = OptionsWidget(parent=self)
        self.mouse_widget = MouseInfoWidget(parent=self)

        self.image_dock = Dock(name="Image", hideTitle=True, widget=self.image_plot, size=(3, 3))
        self.x_dock = Dock(name="x", hideTitle=True, widget=self.x_line_plot, size=(3, 3))
        self.y_dock = Dock(name="y", hideTitle=True, widget=self.y_line_plot, size=(3, 3))
        self.options_dock = Dock(name="Options", hideTitle=True, widget=self.options_widget, size=(3, 1))
        self.mouse_dock = Dock(name="Mouse", hideTitle=True, widget=self.mouse_widget, size=(3, 3))

        self.addDock(self.image_dock)
        self.addDock(self.y_dock, "right", self.image_dock)
        self.addDock(self.x_dock, "bottom", self.image_dock)
        self.addDock(self.options_dock, "right", self.x_dock)
        self.moveDock(self.options_dock, "bottom", self.y_dock)
        self.addDock(self.mouse_dock, "bottom", self.y_dock)
        self.image_dock.setMinimumSize(400, 275)
        self.y_dock.setMinimumSize(400, 275)
        self.x_dock.setMinimumSize(400, 275)
        
        self.image_plot.getView().setXLink(self.x_line_plot)
        self.image_plot.getView().setYLink(self.y_line_plot)
        self.y_line_plot.invertY(True)

        if HKL_MODE:
            self.qx, self.qy, self.qz = createRSM()
            
        if ROI_MODE:
            self.rois = []
            for i in range(4):
                roi = pg.ROI(
                    pos=(ROI_PV_LIST[i]["min_x"].get(), ROI_PV_LIST[i]["min_y"].get()),
                    size=(ROI_PV_LIST[i]["size_x"].get(), ROI_PV_LIST[i]["size_y"].get()),
                    movable=False,
                    resizable=False
                )
                self.rois.append(roi)
                self.image_plot.addItem(roi)
            self.roi_widget = ROIInfoWidget(parent=self)
            self.roi_dock = Dock(name="ROI", hideTitle=True, widget=self.roi_widget, size=(3, 3))
            self.addDock(self.roi_dock, "right", self.mouse_dock)
            
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def update(self):
        self.image_plot.update()
        if HKL_MODE:
            self.qx, self.qy, self.qz = createRSM()
        if ROI_MODE:
            self.roi_widget.update()

class ImagePlot(pg.ImageView):
    def __init__(self, parent) -> None:
        super(ImagePlot, self).__init__(imageItem=pg.ImageItem(), view=pg.PlotItem())
        self.parent = parent

        self.ui.histogram.hide()
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        self.getView().setAspectLocked(False)
        self.getView().ctrlMenu = None

        self.image = None
        self.color_map = None

    def update(self):
        image = np.reshape(IMAGE_PV.get(), (N_CH_2, N_CH_1)).T
        #image = np.random.rand(195, 487).T
        self.image = image
        self.setImage(image, autoRange=False)
        self.parent.x_line_plot.plot(x=np.linspace(0, N_CH_1, N_CH_1), y=np.mean(image, 1), clear=True)
        self.parent.y_line_plot.plot(x=np.mean(image, 0), y=np.linspace(0, N_CH_2, N_CH_2), clear=True)


class OptionsWidget(QtGui.QWidget):
    def __init__(self, parent) -> None:
        super(OptionsWidget, self).__init__()
        self.parent = parent

        color_map_names = [
            'magma', 'inferno', 'plasma', 'viridis', 'cividis', 'twilight', 'turbo', 'coolwarm', 
            'cubehelix', 'gnuplot', 'gnuplot2', 'gray', 'hot', 'hsv', 'jet', 'nipy_spectral', 'rainbow'
        ]
        scales = ["linear", "log", "power"]
        self.color_map_list = sorted(color_map_names)
        self.scale_list = sorted(scales)

        self.color_map_cbx = QtGui.QComboBox()
        self.color_map_cbx.addItems(self.color_map_list)
        self.color_map_cbx.setCurrentText("viridis")
        self.scale_cbx = QtGui.QComboBox()
        self.scale_cbx.addItems(self.scale_list)
        self.scale_cbx.setCurrentText("power")

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.color_map_cbx, 0, 0)
        self.layout.addWidget(self.scale_cbx, 0, 1)

        self.color_map_cbx.currentTextChanged.connect(self.setColorMap)
        self.scale_cbx.currentTextChanged.connect(self.setColorMap)

        self.setColorMap()

    def setColorMap(self):
        name = self.color_map_cbx.currentText()
        scale = self.scale_cbx.currentText()
        color_map = createColorMap(name, scale)
        self.parent.image_plot.setColorMap(color_map)

class MouseInfoWidget(QtGui.QWidget):
    def __init__(self, parent) -> None:
        super(MouseInfoWidget, self).__init__()
        self.parent = parent

        self.scene_point = None

        labels = ["x-pos: ", "y-pos: ", "Value: "]
        hkl_labels = ["H: ", "K: ", "L: ", ]
        if HKL_MODE:
            labels = labels + hkl_labels

        self.lbls, self.txts = [], []
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 3)
        for i in range(len(labels)):
            label = labels[i]
            lbl, txt = QtGui.QLabel(label), QtGui.QLineEdit()
            txt.setReadOnly(True)
            self.lbls.append(lbl)
            self.txts.append(txt)
            self.layout.addWidget(lbl, i, 0)
            self.layout.addWidget(txt, i, 1)

        self.parent.image_plot.getView().scene().sigMouseMoved.connect(self.update)

    def update(self, scene_point=None):
        if scene_point is not None:
            self.scene_point = scene_point
        if self.scene_point is not None:
            view_point = self.parent.image_plot.getView().vb.mapSceneToView(self.scene_point)
            x, y = view_point.x(), view_point.y()
            self.txts[0].setText(str(round(x, 7)))
            self.txts[1].setText(str(round(y, 7)))
            img = self.parent.image_plot.image
            if 0 <= x < img.shape[0] and 0 <= y < img.shape[1]:
                self.txts[2].setText(str(round(img[int(x)][int(y)], 5)))
                if HKL_MODE:
                    self.txts[3].setText(str(round(self.parent.qx[int(x)][int(y)], 7)))
                    self.txts[4].setText(str(round(self.parent.qy[int(x)][int(y)], 7)))
                    self.txts[5].setText(str(round(self.parent.qz[int(x)][int(y)], 7)))
            else:
                self.txts[2].setText("")
                if HKL_MODE:
                    self.txts[3].setText("")
                    self.txts[4].setText("")
                    self.txts[5].setText("")

class ROIInfoWidget(QtGui.QWidget):
    def __init__(self, parent) -> None:
        super(ROIInfoWidget, self).__init__()
        self.parent = parent

        self.lbls, self.txts = [], []
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 3)
        for i in range(len(self.parent.rois)):
            label = f"ROI #{i + 1} Total: "
            lbl, txt = QtGui.QLabel(label), QtGui.QLineEdit()
            txt.setReadOnly(True)
            self.lbls.append(lbl)
            self.txts.append(txt)
            self.layout.addWidget(lbl, i, 0)
            self.layout.addWidget(txt, i, 1)
        self.show_chkbx = QtGui.QCheckBox("Show")
        self.show_chkbx.setChecked(True)
        self.layout.addWidget(self.show_chkbx)

        self.show_chkbx.stateChanged.connect(self.toggleROIVisibility)

    def update(self):
        for roi, roi_pvs, txt in zip(self.parent.rois, ROI_PV_LIST, self.txts):
            txt.setText(str(roi_pvs["total"].get()))
            roi.setPos((roi_pvs["min_x"].get(), roi_pvs["min_y"].get()))
            roi.setSize((roi_pvs["size_x"].get(), roi_pvs["size_y"].get()))
        
    def toggleROIVisibility(self):
        if self.show_chkbx.isChecked():
            for roi in self.parent.rois:
                roi.show()
        else:
            for roi in self.parent.rois:
                roi.hide()
            
# =====================================================================
# Utility functions

def createColorMap(name, scale):
    n_pts, base, gamma = 16, 2, 2

    if name in pg.colormap.listMaps(source="matplotlib"):
        colors = pg.getFromMatplotlib(name).getLookupTable(nPts=n_pts, alpha=False)
    elif name in pg.colormap.listMaps():
        colors = pg.get(name).getLookupTable(nPts=n_pts, alpha=False)
    else:
        raise KeyError("Color map not found.")
    
    if scale == "linear":
        stops = np.array([list(np.linspace(start=0, stop=1, num=n_pts))])
    elif scale == "log":
        stops = np.array([list(np.logspace(start=0, stop=7.5, endpoint=True, num=n_pts, base=base))])
    elif scale == "power":
        stops = np.linspace(start=0, stop=1, num=n_pts)
        stops[stops < 0] = 0
        np.power(stops, gamma, stops)
        stops = np.array([list(stops)])
    else:
        raise ValueError("Scale type not valid.")

    stops = preprocessing.normalize(stops, norm="max")
    stops = list(stops[0])
    return pg.ColorMap(pos=stops, color=colors)

def createRSM():
    hxrd = xu.HXRD(INPLANE_REF_DIR, SAMPLE_NORM_DIR, en=ENERGY_PV.get()*1000, qconv=Q_CONV)
    hxrd.Ang2Q.init_area(PIXEL_DIR_1, PIXEL_DIR_2, cch1=C_CH_1, cch2=C_CH_2,
        Nch1=N_CH_1, Nch2=N_CH_2, pwidth1=PIXEL_WIDTH_1, pwidth2=PIXEL_WIDTH_2,
        distance=DISTANCE, roi=ROI)
    angles = [pv.get() for pv in CIRCLE_PV_LIST]
    ub = np.reshape(UB_MATRIX_PV.get(), (3, 3))
    return hxrd.Ang2Q.area(*angles, UB=ub)

# =====================================================================

app = pg.mkQApp("Live Image")
MainWindow().show()
pg.mkQApp().exec_()
