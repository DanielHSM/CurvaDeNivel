# -*- coding: utf-8 -*-

"""
/***************************************************************************
 CurvaDeNivel
                                 A QGIS plugin
 Cria curvas de nivel a partir de dados geomorféticos do INPE
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-10-08
        copyright            : (C) 2024 by Daniel Hulshof Saint Martin
        email                : daniel.hulshof@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Daniel Hulshof Saint Martin'
__date__ = '2024-10-08'
__copyright__ = '(C) 2024 by Daniel Hulshof Saint Martin'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsProcessingAlgorithm, QgsApplication
import processing

from qgis.core import QgsProcessingAlgorithm, QgsApplication
from .curva_de_nivel_provider import CurvaDeNivelProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

class CurvaDeNivelPlugin(object):

    def __init__(self, iface):
        self.provider = None
        self.iface = iface

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = CurvaDeNivelProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()
        
        icon = os.path.join(os.path.join(cmd_folder, 'logo.png'))
        self.action = QAction(
            QIcon(icon),
            "Curva de Nivel", 
            self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&Curva de Nivel", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.iface.removePluginMenu("&Curva de Nivel", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        processing.execAlgorithmDialog("Curva de Nivel:Curva de Nivel")