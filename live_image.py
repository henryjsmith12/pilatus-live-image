import epics
import numpy as np
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
from sklearn import preprocessing
import sys
import xml.etree.ElementTree as ET
import xrayutilities as xu

# =====================================================================
# Global configuration dictionary used for all PV reading

CONFIG = {
    "HKL_MODE": True, "ROI_MODE": True,
    "DET_PRESENT": False, "INSTR_PRESENT": False, "ROI_PRESENT": False, "ENERGY_PRESENT": False,
    "PV_PREFIX": None,
    "IMAGE_PV": None, "IMAGE_TOTAL_PV": None, "IMAGE_MAX_PV": None, 
    "PIXEL_DIR_1": None, "PIXEL_DIR_2": None,
    "C_CH_1": None, "C_CH_2": None,
    "N_CH_1": None, "N_CH_2": None,
    "PIXEL_WIDTH_1": None, "PIXEL_WIDTH_2": None,
    "DISTANCE": None,
    "DET_ROI": None,
    "SAMPLE_CIRCLE_DIR": None, "SAMPLE_CIRCLE_NAMES": None, "SAMPLE_CIRCLE_PV_LIST": None,
    "DET_CIRCLE_DIR": None, "DET_CIRCLE_NAMES": None, "DET_CIRCLE_PV_LIST": None,
    "CIRCLE_PV_LIST": None,
    "PRIMARY_BEAM_DIR": None, "INPLANE_REF_DIR": None, "SAMPLE_NORM_DIR": None,
    "Q_CONV": None,
    "UB_MATRIX_PV": None,
    "ROI_PV_LIST": None,
    "ENERGY_PV": None
}

# =====================================================================
# Reads configuration values from XML file (config.xml)
def configure():
    tree = ET.parse("config.xml")
    root = tree.getroot()
    tags = [child.tag for child in root]

    if "pv_prefix" not in tags:
        raise KeyError("Missing PV prefix.") 
    if "detector" not in tags:
        raise KeyError("Missing detector config values.") 
    if "instrument" not in tags:
        CONFIG["INSTR_PRESENT"] = False
        CONFIG["HKL_MODE"] = False
    if "rois" not in tags:
        CONFIG["ROI_PRESENT"] = False
        CONFIG["ROI_MODE"] = False  
    if "energy" not in tags:
        CONFIG["ENERGY_PRESENT"] = False
        CONFIG["HKL_MODE"] = False

    # Preliminary walkthrough to get PV prefix
    for child in root:
        if child.tag == "pv_prefix" and CONFIG["PV_PREFIX"] is None:
            CONFIG["PV_PREFIX"] = child.text
            break

    for child in root:        
        if child.tag == "detector":
            CONFIG["DET_PRESENT"] = True
            try:
                CONFIG["IMAGE_PV"] = epics.PV(CONFIG["PV_PREFIX"] + ":" + child.find("image").attrib["pv"])
            except:
                raise KeyError("Missing detector image PV.")
            try:
                CONFIG["IMAGE_TOTAL_PV"] = epics.PV(CONFIG["PV_PREFIX"] + ":" + child.find("image_total").attrib["pv"])
                CONFIG["IMAGE_MAX_PV"] = epics.PV(CONFIG["PV_PREFIX"] + ":" + child.find("image_max").attrib["pv"])
                CONFIG["PIXEL_DIR_1"] = child.find("pixel_direction_1").text 
                CONFIG["PIXEL_DIR_2"] = child.find("pixel_direction_2").text
                if CONFIG["C_CH_1"] is None:
                    CONFIG["C_CH_1"] = int(child.find("center_channel_pixel").text.split()[0])
                if CONFIG["C_CH_2"] is None:
                    CONFIG["C_CH_2"] = int(child.find("center_channel_pixel").text.split()[1])
                CONFIG["N_CH_1"] = int(child.find("n_pixels").text.split()[0])
                CONFIG["N_CH_2"] = int(child.find("n_pixels").text.split()[1])
                CONFIG["PIXEL_WIDTH_1"] = float(child.find("size").text.split()[0]) / CONFIG["N_CH_1"]
                CONFIG["PIXEL_WIDTH_2"] = float(child.find("size").text.split()[1]) / CONFIG["N_CH_2"]
                if CONFIG["DISTANCE"] is None:
                    CONFIG["DISTANCE"] = float(child.find("distance").text)
                CONFIG["DET_ROI"] = [0, CONFIG["N_CH_1"], 0, CONFIG["N_CH_2"]]
            except:
                CONFIG["DET_PRESENT"] = False

        elif child.tag == "instrument":
            CONFIG["INSTR_PRESENT"] = True
            try:
                sample_circles = child.find("sample_circles")
                CONFIG["SAMPLE_CIRCLE_DIR"], CONFIG["SAMPLE_CIRCLE_NAMES"], CONFIG["SAMPLE_CIRCLE_PV_LIST"] = [], [], []
                for circle_axis in sample_circles:
                    CONFIG["SAMPLE_CIRCLE_NAMES"].append(circle_axis.attrib["spec_motor_name"])
                    CONFIG["SAMPLE_CIRCLE_DIR"].append(circle_axis.attrib["direction_axis"])
                    CONFIG["SAMPLE_CIRCLE_PV_LIST"].append(epics.PV(circle_axis.attrib["pv"]))
                detector_circles = child.find("detector_circles")
                CONFIG["DET_CIRCLE_DIR"], CONFIG["DET_CIRCLE_NAMES"], CONFIG["DET_CIRCLE_PV_LIST"] = [], [], []
                for circle_axis in detector_circles:
                    CONFIG["DET_CIRCLE_NAMES"].append(circle_axis.attrib["spec_motor_name"])
                    CONFIG["DET_CIRCLE_DIR"].append(circle_axis.attrib["direction_axis"])
                    CONFIG["DET_CIRCLE_PV_LIST"].append(epics.PV(circle_axis.attrib["pv"]))
                CONFIG["CIRCLE_PV_LIST"] = CONFIG["SAMPLE_CIRCLE_PV_LIST"] + CONFIG["DET_CIRCLE_PV_LIST"]
                CONFIG["PRIMARY_BEAM_DIR"] = [int(axis.text) for axis in child.find("primary_beam_direction")]
                CONFIG["INPLANE_REF_DIR"] = [int(axis.text) for axis in child.find("inplane_reference_direction")]
                CONFIG["SAMPLE_NORM_DIR"] = [int(axis.text) for axis in child.find("sample_surface_normal_direction")]
                CONFIG["Q_CONV"] = xu.experiment.QConversion(CONFIG["SAMPLE_CIRCLE_DIR"], CONFIG["DET_CIRCLE_DIR"], CONFIG["PRIMARY_BEAM_DIR"])
                CONFIG["UB_MATRIX_PV"] = epics.PV(child.find("ub_matrix").attrib["pv"])
            except:
                CONFIG["HKL_MODE"] = False

        elif child.tag == "rois":
            CONFIG["ROI_PRESENT"] = True
            try:
                CONFIG["ROI_PV_LIST"] = [{}, {}, {}, {}]
                for roi, roi_pv_dict in zip(child, CONFIG["ROI_PV_LIST"]):
                    for roi_attr in roi:
                        pv = CONFIG["PV_PREFIX"] + ":" + roi_attr.attrib["pv"]
                        roi_pv_dict[roi_attr.tag] = epics.PV(pv)
            except:
                CONFIG["ROI_MODE"] = False

        elif child.tag == "energy":
            CONFIG["ENERGY_PRESENT"] = True
            try:
                CONFIG["ENERGY_PV"] = epics.PV(child.attrib["pv"])
            except:
                CONFIG["HKL_MODE"] = False

# =====================================================================
# Initial dialog to manually determine PV prefix, detector distance, and the center pixel
class OptionsDialog(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.prefix_lbl, self.prefix_txt = QtWidgets.QLabel("PV Prefix: "), QtWidgets.QLineEdit()
        self.distance_lbl, self.distance_sbx = QtWidgets.QLabel("Distance: "), QtWidgets.QDoubleSpinBox()
        self.center_x_lbl, self.center_x_sbx = QtWidgets.QLabel("Center (x): "), QtWidgets.QSpinBox()
        self.center_y_lbl, self.center_y_sbx = QtWidgets.QLabel("Center (y): "), QtWidgets.QSpinBox()
        self.btn_bx = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)

        self.distance_sbx.setRange(0, 1000000) 
        self.center_x_sbx.setRange(-1000, 1000) 
        self.center_y_sbx.setRange(-1000, 1000)


        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.prefix_lbl, 0, 0)
        self.layout.addWidget(self.prefix_txt, 0, 1)
        self.layout.addWidget(self.distance_lbl, 1, 0)
        self.layout.addWidget(self.distance_sbx, 1, 1)
        self.layout.addWidget(self.center_x_lbl, 2, 0)
        self.layout.addWidget(self.center_x_sbx, 2, 1)
        self.layout.addWidget(self.center_y_lbl, 3, 0)
        self.layout.addWidget(self.center_y_sbx, 3, 1)
        self.layout.addWidget(self.btn_bx, 4, 0, 1, 2)

        if CONFIG["PV_PREFIX"] is not None:
            self.prefix_txt.setText(CONFIG["PV_PREFIX"])
        if CONFIG["DISTANCE"] is not None:
            self.distance_sbx.setValue(CONFIG["DISTANCE"])
        if CONFIG["C_CH_1"] is not None:
            self.center_x_sbx.setValue(CONFIG["C_CH_1"])
        if CONFIG["C_CH_2"] is not None:
            self.center_y_sbx.setValue(CONFIG["C_CH_2"])

        self.btn_bx.accepted.connect(self.accept)
        
    def accept(self):

        CONFIG["PV_PREFIX"] = self.prefix_txt.text()
        CONFIG["DISTANCE"] = self.distance_sbx.value()
        CONFIG["C_CH_1"] = self.center_x_sbx.value()
        CONFIG["C_CH_2"] = self.center_y_sbx.value()
        self.close()
        configure()
        mw = MainWindow()
        mw.show()
        
    def reject(self):
        sys.exit()

# =====================================================================

class MainWindow(DockArea):
    def __init__(self) -> None:
        super().__init__()

        self.resize(500, 500)

        self.image_plot = ImagePlot(parent=self)
        self.x_line_plot = pg.PlotWidget(parent=self)
        self.y_line_plot = pg.PlotWidget(parent=self)
        self.slice_line_plot = pg.PlotWidget(parent=self)
        self.options_widget =  ColorMapController(parent=self)
        self.mouse_widget = MouseInfoWidget(parent=self)
        self.line_roi_widget = LineROIInfoWidget(parent=self)

        self.image_dock = Dock(name="Image", hideTitle=True, widget=self.image_plot, size=(3, 3))
        self.x_dock = Dock(name="x", hideTitle=True, widget=self.x_line_plot, size=(3, 3))
        self.y_dock = Dock(name="y", hideTitle=True, widget=self.y_line_plot, size=(3, 3))
        self.slice_dock = Dock(name="slice", hideTitle=True, widget=self.slice_line_plot, size=(3, 3))
        self.options_dock = Dock(name="Options", hideTitle=True, widget=self.options_widget, size=(3, 1))
        self.mouse_dock = Dock(name="Mouse", hideTitle=True, widget=self.mouse_widget, size=(3, 3))
        self.line_roi_dock = Dock(name="Line ROI", hideTitle=True, widget=self.line_roi_widget, size=(3, 3))

        self.addDock(self.image_dock)
        self.addDock(self.y_dock, "right", self.image_dock)
        self.addDock(self.x_dock, "bottom", self.image_dock)
        self.addDock(self.slice_dock, "right", self.x_dock)
        self.addDock(self.mouse_dock, "right", self.y_dock)
        self.addDock(self.options_dock, "bottom", self.slice_dock)
        self.addDock(self.y_dock, "top", self.slice_dock)
        self.addDock(self.y_dock, "right", self.image_dock)
        #self.addDock(self.line_roi_dock, "bottom", self.mouse_dock)

        self.image_dock.setMinimumSize(400, 275)
        self.x_dock.setMinimumSize(400, 275)
        self.y_dock.setMinimumSize(400, 275)
        self.slice_dock.setMinimumSize(300, 275)
        self.mouse_dock.setMinimumSize(200, 275)
        
        self.image_plot.getView().setXLink(self.x_line_plot)
        self.image_plot.getView().setYLink(self.y_line_plot)
        self.image_plot.getView().invertY(False)
        self.y_line_plot.invertY(False)
        self.slice_line_plot.hideAxis("bottom")
        #self.x_line_plot.plotItem.setLogMode(y=True)
        #self.y_line_plot.plotItem.setLogMode(x=True)
        #self.slice_line_plot.plotItem.setLogMode(y=True)

        if CONFIG["HKL_MODE"]:
            self.qx, self.qy, self.qz = createRSM()
            
        if CONFIG["ROI_MODE"]:
            self.rois = []
            self.roi_colors = ["ff0000", "0000ff", "4CBB17", "ff00ff"]
            for i in range(4):
                roi = pg.ROI(
                    pos=(CONFIG["ROI_PV_LIST"][i]["min_x"].get(), CONFIG["ROI_PV_LIST"][i]["min_y"].get()),
                    size=(CONFIG["ROI_PV_LIST"][i]["size_x"].get(), CONFIG["ROI_PV_LIST"][i]["size_y"].get()),
                    movable=False,
                    resizable=False,
                    pen=pg.mkPen({"color": self.roi_colors[i], "width": 2})
                )
                self.rois.append(roi)
                self.image_plot.addItem(roi)
            self.roi_widget = ROIInfoWidget(parent=self)
            self.roi_dock = Dock(name="ROI", hideTitle=True, widget=self.roi_widget, size=(3, 3))
            self.addDock(self.roi_dock, "bottom", self.mouse_dock)
            
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        self.options_widget.colorMapChanged.connect(self._setColorMap)

    def update(self):
        self.image_plot.update()
        if CONFIG["HKL_MODE"]:
            self.qx, self.qy, self.qz = createRSM()
        if CONFIG["ROI_MODE"]:
            self.roi_widget.update()

    def _setColorMap(self):
        color_map = self.options_widget.color_map
        range = (0, self.options_widget.color_map_max)

        self.image_plot._setColorMap(color_map, range)

# =====================================================================

class ImagePlot(pg.ImageView):
    def __init__(self, parent) -> None:
        super(ImagePlot, self).__init__(imageItem=pg.ImageItem(), view=pg.PlotItem())
        self.parent = parent

        self.ui.histogram.hide()
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        self.getView().setAspectLocked(False)
        self.getView().ctrlMenu = None

        self.image_data = None
        self.color_map = None
        self.color_bar = None
        self.line_roi = pg.LineSegmentROI([[0, 0], [CONFIG["N_CH_1"], CONFIG["N_CH_2"]]])
        self.addItem(self.line_roi)

    def update(self):
        image = np.reshape(CONFIG["IMAGE_PV"].get(), (CONFIG["N_CH_2"], CONFIG["N_CH_1"])).T
        #image = (np.random.rand(195, 487).T * 1.5) ** 4
        self.image_data = image
        if self.color_map is None:
            self.parent._setColorMap()

        norm_image = np.copy(self.image_data)
        if self.color_map_range is None:
            norm_max = 1
        else:
            norm_max = self.color_map_range[-1]
        norm_image[norm_image > norm_max] = norm_max
        norm_image = norm_image / norm_max
        self.norm_image = norm_image

        self.setImage(self.norm_image, autoRange=False, autoLevels=False)
        self.parent.x_line_plot.plot(x=np.linspace(0, CONFIG["N_CH_1"], CONFIG["N_CH_1"]), y=np.mean(image, 1), clear=True)
        self.parent.y_line_plot.plot(x=np.mean(image, 0), y=np.linspace(0, CONFIG["N_CH_2"], CONFIG["N_CH_2"]), clear=True)
        
        slice_data, slice_coords = self.line_roi.getArrayRegion(data=image, img=self.getImageItem(),  returnMappedCoords=True)
        self.parent.slice_line_plot.plot(x=np.linspace(slice_coords[0][0], slice_coords[0][-1], len(slice_coords[0])), y=slice_data, clear=True)

    def _setColorMap(self, color_map, range):
        self.color_map = color_map
        self.color_map_range = range

        if self.color_bar is None:
            self.color_bar = pg.ColorBarItem(
                values=range,
                cmap=color_map, 
                interactive=False,
                width=15,
                orientation="v"
            )
            self.color_bar.setImageItem(
                img=self.image_data,
                insert_in=self.getView()
            )
        self.setColorMap(color_map)
        self.color_bar.setCmap(color_map)
        self.color_bar.setLevels(range)

# =====================================================================

class OptionsWidget(QtWidgets.QWidget):
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

        self.color_map = None

        self.color_map_cbx = QtWidgets.QComboBox()
        self.color_map_cbx.addItems(self.color_map_list)
        self.color_map_cbx.setCurrentText("viridis")
        self.scale_cbx = QtWidgets.QComboBox()
        self.scale_cbx.addItems(self.scale_list)
        self.scale_cbx.setCurrentText("power")
        self.max_lbl = QtWidgets.QLabel("Max: ")
        self.max_sbx = QtWidgets.QSpinBox()
        self.max_sbx.setMaximum(1000000)
        self.max_sbx.setMinimum(1)
        self.max_sbx.setValue(10000)

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.color_map_cbx, 0, 0)
        self.layout.addWidget(self.scale_cbx, 0, 1)
        self.layout.addWidget(self.max_lbl, 0, 2)
        self.layout.addWidget(self.max_sbx, 0, 3)

        self.color_map_cbx.currentTextChanged.connect(self.setColorMap)
        self.scale_cbx.currentTextChanged.connect(self.setColorMap)

        self.setColorMap()

class MouseInfoWidget(QtWidgets.QWidget):
    def __init__(self, parent) -> None:
        super(MouseInfoWidget, self).__init__()
        self.parent = parent

        self.scene_point = None

        labels = ["x-pos: ", "y-pos: ", "Value: "]
        hkl_labels = ["H: ", "K: ", "L: ", ]
        if CONFIG["HKL_MODE"]:
            labels = labels + hkl_labels

        self.lbls, self.txts = [], []
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 3)
        for i in range(len(labels)):
            label = labels[i]
            lbl, txt = QtWidgets.QLabel(label), QtWidgets.QLineEdit()
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
            img = self.parent.image_plot.image_data
            if 0 <= x < img.shape[0] and 0 <= y < img.shape[1]:
                self.txts[2].setText(str(round(img[int(x)][int(y)], 5)))
                if CONFIG["HKL_MODE"]:
                    self.txts[3].setText(str(round(self.parent.qx[int(x)][int(y)], 7)))
                    self.txts[4].setText(str(round(self.parent.qy[int(x)][int(y)], 7)))
                    self.txts[5].setText(str(round(self.parent.qz[int(x)][int(y)], 7)))
            else:
                self.txts[2].setText("")
                if CONFIG["HKL_MODE"]:
                    self.txts[3].setText("")
                    self.txts[4].setText("")
                    self.txts[5].setText("")

class ROIInfoWidget(QtWidgets.QWidget):
    def __init__(self, parent) -> None:
        super(ROIInfoWidget, self).__init__()
        self.parent = parent

        self.lbls, self.txts = [], []
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 3)
        self.layout.setColumnStretch(2, 1)
        for i in range(len(self.parent.rois)):
            label = f"ROI #{i + 1} Total: "
            color = self.parent.roi_colors[i]
            lbl, txt = QtWidgets.QLabel(label), QtWidgets.QLineEdit()
            lbl.setStyleSheet(f"color: #{color}")
            txt.setReadOnly(True)
            self.lbls.append(lbl)
            self.txts.append(txt)
            self.layout.addWidget(lbl, i, 0)
            self.layout.addWidget(txt, i, 1)
        self.show_chkbx = QtWidgets.QCheckBox("Show Regions")
        self.show_chkbx.setChecked(True)
        
        self.img_total_lbl = QtWidgets.QLabel("Image Total: ")
        self.img_total_txt = QtWidgets.QLineEdit()
        self.img_total_txt.setReadOnly(True)
        self.layout.addWidget(self.img_total_lbl, 5, 0)
        self.layout.addWidget(self.img_total_txt, 5, 1)

        self.img_max_lbl = QtWidgets.QLabel("Image Max: ")
        self.img_max_txt = QtWidgets.QLineEdit()
        self.img_max_txt.setReadOnly(True)
        self.layout.addWidget(self.img_max_lbl, 6, 0)
        self.layout.addWidget(self.img_max_txt, 6, 1)

        self.layout.addWidget(self.show_chkbx, 7, 0)

        self.show_chkbx.stateChanged.connect(self.toggleROIVisibility)

    def update(self):
        for roi, roi_pvs, txt in zip(self.parent.rois, CONFIG["ROI_PV_LIST"], self.txts):
            txt.setText(str(roi_pvs["total"].get()))
            roi.setPos((roi_pvs["min_x"].get(), roi_pvs["min_y"].get()))
            roi.setSize((roi_pvs["size_x"].get(), roi_pvs["size_y"].get()))

        self.img_total_txt.setText(str(CONFIG["IMAGE_TOTAL_PV"].get()))
        self.img_max_txt.setText(str(CONFIG["IMAGE_MAX_PV"].get()))
        
    def toggleROIVisibility(self):
        if self.show_chkbx.isChecked():
            for roi in self.parent.rois:
                roi.show()
        else:
            for roi in self.parent.rois:
                roi.hide()

# =====================================================================

class LineROIInfoWidget(QtWidgets.QWidget):
    def __init__(self, parent) -> None:
        super(LineROIInfoWidget, self).__init__()
        self.parent = parent  

        self.color_btn = pg.ColorButton(color=(255, 255, 255))
        self.show_chkbx = QtWidgets.QCheckBox("Show Line ROI")
        self.show_chkbx.setChecked(True)

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.color_btn, 0, 0)
        self.layout.addWidget(self.show_chkbx, 1, 0)

# =====================================================================
# Utility functions

class ColorMapController(QtWidgets.QWidget):
    """Allows user to apply a colormap to an image."""

    colorMapChanged = QtCore.pyqtSignal()

    def __init__(self, parent) -> None:
        super(ColorMapController, self).__init__()

        self.parent = parent
        self.color_map = None
        self.color_map_max = None

        available_color_maps = [
            'magma', 'inferno', 'plasma', 'viridis', 'cividis', 'twilight',
            'turbo', 'cool', 'coolwarm', 'afmhot', 'autumn', 'copper',
            'cubehelix', 'gnuplot', 'gnuplot2', 'gray', 'hot', 'hsv', 'jet',
            'nipy_spectral', 'ocean', 'pink', 'prism', 'rainbow',
            'spring', 'summer', 'winter'
        ]
        available_color_maps = sorted(available_color_maps)
        scales = ["linear", "log", "power"]

        self.name = available_color_maps[0]
        self.scale = scales[0]
        self.n_pts = 16
        self.base = 2.0
        self.gamma = 2.0

        # Child widgets
        self.name_cbx = QtWidgets.QComboBox()
        self.name_cbx.addItems(available_color_maps)
        self.scale_cbx = QtWidgets.QComboBox()
        self.scale_cbx.addItems(scales)
        self.n_pts_lbl = QtWidgets.QLabel("# Points:")
        self.n_pts_sbx = QtWidgets.QSpinBox()
        self.n_pts_sbx.setMinimum(2)
        self.n_pts_sbx.setMaximum(256)
        self.n_pts_sbx.setValue(16)
        self.base_lbl = QtWidgets.QLabel("Base:")
        self.base_lbl.setAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
        )
        self.base_lbl.hide()
        self.base_sbx = QtWidgets.QDoubleSpinBox()
        self.base_sbx.setMinimum(0.0001)
        self.base_sbx.setMaximum(1000)
        self.base_sbx.setSingleStep(0.1)
        self.base_sbx.hide()
        self.base_sbx.setValue(2.0)
        self.gamma_lbl = QtWidgets.QLabel("Gamma:")
        self.gamma_lbl.setAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
        )
        self.gamma_lbl.hide()
        self.gamma_sbx = QtWidgets.QDoubleSpinBox()
        self.gamma_sbx.setMinimum(0.0001)
        self.gamma_sbx.setMaximum(1000)
        self.gamma_sbx.setSingleStep(0.1)
        self.gamma_sbx.hide()
        self.gamma_sbx.setValue(2.0)
        self.max_value_lbl = QtWidgets.QLabel("Max: ")
        self.max_value_lbl.setAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
        )
        self.max_value_sbx = QtWidgets.QSpinBox()
        self.max_value_sbx.setMinimum(1)
        self.max_value_sbx.setMaximum(1000000)
        self.max_value_sbx.setSingleStep(1)
        self.max_value_sbx.setValue(1000)

        # Layout
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.name_cbx, 0, 0, 1, 2)
        self.layout.addWidget(self.scale_cbx, 1, 0, 1, 2)
        self.layout.addWidget(self.base_lbl, 2, 0)
        self.layout.addWidget(self.base_sbx, 2, 1)
        self.layout.addWidget(self.gamma_lbl, 2, 0)
        self.layout.addWidget(self.gamma_sbx, 2, 1)
        self.layout.addWidget(self.max_value_lbl, 3, 0)
        self.layout.addWidget(self.max_value_sbx, 3, 1)

        # Connections
        self.name_cbx.currentIndexChanged.connect(self._setColorMap)
        self.scale_cbx.currentIndexChanged.connect(self._setColorMap)
        self.scale_cbx.currentIndexChanged.connect(self._toggleScaleOptions)
        self.n_pts_sbx.valueChanged.connect(self._setColorMap)
        self.base_sbx.valueChanged.connect(self._setColorMap)
        self.gamma_sbx.valueChanged.connect(self._setColorMap)
        self.max_value_sbx.valueChanged.connect(self._setColorMapBounds)

        # Sets initial color map
        self._setColorMap()
        self._setColorMapBounds()

    def _setColorMap(self) -> None:
        """Sets parameters for color map creation and emits signal."""

        self.name = self.name_cbx.currentText()
        self.scale = self.scale_cbx.currentText()
        self.n_pts = self.n_pts_sbx.value()
        self.base = self.base_sbx.value()
        self.gamma = self.gamma_sbx.value()

        self.color_map = createColorMap(
            name=self.name,
            scale=self.scale,
            base=self.base,
            gamma=self.gamma
        )

        self.colorMapChanged.emit()

    def _toggleScaleOptions(self) -> None:
        """Hides/shows respective options for each color map scale."""

        if self.scale_cbx.currentText() == "linear":
            self.base_lbl.hide()
            self.base_sbx.hide()
            self.gamma_lbl.hide()
            self.gamma_sbx.hide()
        elif self.scale_cbx.currentText() == "log":
            self.base_lbl.show()
            self.base_sbx.show()
            self.gamma_lbl.hide()
            self.gamma_sbx.hide()
        elif self.scale_cbx.currentText() == "power":
            self.base_lbl.hide()
            self.base_sbx.hide()
            self.gamma_lbl.show()
            self.gamma_sbx.show()

    def _setColorMapBounds(self) -> None:
        """Sets maximum pixel value for color map."""

        self.color_map_max = self.max_value_sbx.value()
        self.colorMapChanged.emit()

def createColorMap(
    name: str,
    scale: str,
    min: float=0.0,
    max: float=1.0,
    n_pts: int=16,
    base: float=1.75,
    gamma: float=2
) -> pg.ColorMap:
    """Returns a color map object created from given parameters."""

    if name in pg.colormap.listMaps(source="matplotlib"):
        colors = pg.colormap.getFromMatplotlib(name).getLookupTable(nPts=n_pts)
    elif name in pg.colormap.listMaps(source="colorcet"):
        colors = pg.colormap.getFromColorcet(name).getLookupTable(nPts=n_pts)
    elif name in pg.colormap.listMaps():
        colors = pg.get(name).getLookupTable(nPts=n_pts)
    else:
        raise KeyError("Color map not found.")

    if scale == "linear":
        stops = np.linspace(start=min, stop=max, num=n_pts)
        stops = np.array([list(stops)])
        stops = preprocessing.normalize(stops, norm="max")
        stops = list(stops[0])
    elif scale == "log":
        stops = np.logspace(
            start=0,
            stop=7.5,
            endpoint=True,
            num=n_pts,
            base=base
        )
        stops = np.array([list(stops)])
        stops = preprocessing.normalize(stops, norm="max")
        stops = list(stops[0])
    elif scale == "power":
        stops = np.linspace(start=min, stop=max, num=n_pts)
        stops -= min
        stops[stops < 0] = 0
        np.power(stops, gamma, stops)
        stops /= (max - min) ** gamma
        stops = np.array([list(stops)])
        stops = preprocessing.normalize(stops, norm="max")
        stops = list(stops[0])
    else:
        raise ValueError("Scale type not valid.")

    return pg.ColorMap(pos=stops, color=colors)

def createRSM():
    hxrd = xu.HXRD(CONFIG["INPLANE_REF_DIR"], CONFIG["SAMPLE_NORM_DIR"], en=CONFIG["ENERGY_PV"].get()*1000, qconv=CONFIG["Q_CONV"])
    hxrd.Ang2Q.init_area(CONFIG["PIXEL_DIR_1"], CONFIG["PIXEL_DIR_2"], cch1=CONFIG["C_CH_1"], cch2=CONFIG["C_CH_2"],
        Nch1=CONFIG["N_CH_1"], Nch2=CONFIG["N_CH_2"], pwidth1=CONFIG["PIXEL_WIDTH_1"], pwidth2=CONFIG["PIXEL_WIDTH_2"],
        distance=CONFIG["DISTANCE"], roi=CONFIG["DET_ROI"])
    angles = [pv.get() for pv in CONFIG["CIRCLE_PV_LIST"]]
    ub = np.reshape(CONFIG["UB_MATRIX_PV"].get(), (3, 3))
    return hxrd.Ang2Q.area(*angles, UB=ub)

app = pg.mkQApp("Live Image")
configure()
od = OptionsDialog()
od.show()
pg.mkQApp().exec_()

configure()
