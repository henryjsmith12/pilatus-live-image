import epics
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
    if child.tag == "pv_prefix":
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
            CONFIG["C_CH_1"] = int(child.find("center_channel_pixel").text.split()[0])
            CONFIG["C_CH_2"] = int(child.find("center_channel_pixel").text.split()[1])
            CONFIG["N_CH_1"] = int(child.find("n_pixels").text.split()[0])
            CONFIG["N_CH_2"] = int(child.find("n_pixels").text.split()[1])
            CONFIG["PIXEL_WIDTH_1"] = float(child.find("size").text.split()[0]) / CONFIG["N_CH_1"]
            CONFIG["PIXEL_WIDTH_2"] = float(child.find("size").text.split()[1]) / CONFIG["N_CH_2"]
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
    elif child.tag == "energy":
        CONFIG["ENERGY_PRESENT"] = True

    