from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

import maya.OpenMayaUI as mui
import shiboken2
import maya.cmds as cmds

def get_maya_main_window():
    main_window_ptr = mui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(main_window_ptr), QWidget)

class CuCo(QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super(CuCo, self).__init__(parent)
        self.setWindowTitle("CuCo")
        self.setMinimumWidth(300)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)

        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("Nom de base")

        self.num_points = QSpinBox()
        self.num_points.setMinimum(2)
        self.num_points.setValue(5)

        self.num_joints = QSpinBox()
        self.num_joints.setMinimum(1)
        self.num_joints.setValue(3)

        self.orientation = QComboBox()
        self.orientation.addItems(["x", "y", "z"])

        self.build_button = QPushButton("Créer la courbe correctrice")
        self.build_button.clicked.connect(self.create_corrective_curve)

        layout.addWidget(self.name_field)
        layout.addWidget(QLabel("Nombre de CVs (points sur la courbe)"))
        layout.addWidget(self.num_points)
        layout.addWidget(QLabel("Nombre de joints correctifs"))
        layout.addWidget(self.num_joints)
        layout.addWidget(QLabel("Orientation des joints"))
        layout.addWidget(self.orientation)
        layout.addWidget(self.build_button)
    
    def create_corrective_curve(self):
        # Récupérer les paramètres de l'interface
        name = self.name_field.text()
        if not name:
            cmds.warning("Veuillez entrer un nom de base.")
            return
        
        num_cvs = self.num_points.value()
        num_joints = self.num_joints.value()
        axis = self.orientation.currentText()
        
        # Nom de la courbe
        curve_name = f"CC_{name}"
    
        # Générer les points de la courbe de manière linéaire
        points = self.generate_curve_points(num_cvs, axis)
    
        # Créer la courbe avec les points générés
        curve = self.create_curve(points, curve_name)
    
        # Créer le groupe pour les clusters
        cluster_group = self.create_cluster_group(curve, num_cvs, name)
    
        # Créer le groupe pour les joints
        joint_group = self.create_joint_group(curve, num_joints, name, axis)
    
        # Regrouper la courbe, les clusters et les joints dans un groupe final
        final_group = cmds.group([curve, cluster_group, joint_group], name=f"Jc_c_{name}")
        cmds.select(final_group)
    
    def generate_curve_points(self, num_cvs, axis):
        """Génère les points de la courbe en fonction de l'axe choisi."""
        spacing = 10  # Espacement entre les points
        points = []
        
        if axis == "x":
            points = [(i * spacing, 0, 0) for i in range(num_cvs)]
        elif axis == "y":
            points = [(0, i * spacing, 0) for i in range(num_cvs)]
        elif axis == "z":
            points = [(0, 0, i * spacing) for i in range(num_cvs)]
        
        return points
    
    def create_curve(self, points, curve_name):
        """Crée une courbe NURBS à partir des points."""
        curve = cmds.curve(d=2, p=points, k=[0] + list(range(1, len(points))) + [len(points)], name=curve_name)
        return curve
    
    def create_cluster_group(self, curve, num_cvs, name):
        """Crée un groupe de clusters pour la courbe."""
        cluster_group = cmds.group(empty=True, name=f"Clusters_{name}_GRP")
        
        for i in range(num_cvs):
            cluster, handle = cmds.cluster(f"{curve}.cv[{i}]", name=f"Cluster_{curve}_CV_{i+1}")
            cmds.parent(handle, cluster_group)
        
        return cluster_group
    
        
    def create_joint_group(self, curve, num_joints, name, axis):
        """Crée un groupe de joints, les place via motion path, et les parent ensuite."""
        
        joint_group = cmds.group(empty=True, name=f"Joints_{name}_GRP")
        
        # Calcul des valeurs U pour motion path
        param_values = [i / float(num_joints - 1) for i in range(num_joints)]
        
        joints = []
        for i in range(num_joints):
            joint_name = f"D_{name}_{str(i+1).zfill(2)}"
            joint = self.create_joint(joint_name, axis)
            joints.append(joint)
    
        for joint, u in zip(joints, param_values):
            self.create_motion_path(joint, curve, u)
    
        cmds.parent(joints, joint_group)
        
        return joint_group

    
    
    
    
    
    
    def create_joint(self, joint_name, axis):
        """Crée un joint avec une orientation définie selon l'axe choisi."""
        joint = cmds.joint(name=joint_name)
        
        if axis == "x":
            cmds.joint(joint, e=True, oj="xyz", sao="yup", ch=True, zso=True)
        elif axis == "y":
            cmds.joint(joint, e=True, oj="yzx", sao="zup", ch=True, zso=True)
        elif axis == "z":
            cmds.joint(joint, e=True, oj="zxy", sao="xup", ch=True, zso=True)
        
        return joint
    
    def create_motion_path(self, joint, curve, u_value):
        """Crée un motion path pour un joint sur la courbe donnée."""
        try:
            motion_path = cmds.pathAnimation(joint, c=curve, fractionMode=True, follow=True)
            cmds.setAttr(f"{motion_path}.uValue", u_value)
        except Exception as e:
            cmds.warning(f"Erreur lors de la création du motion path pour {joint}: {e}")

    


    


def show_tool():
    if cmds.window("CuCoWin", exists=True):
        cmds.deleteUI("CuCoWin")

    win = CuCo()
    win.setObjectName("CuCoWin")
    win.show()

show_tool()
