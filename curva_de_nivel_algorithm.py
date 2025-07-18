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
import re
import inspect
from urllib.parse import urlparse  
from requests.auth import HTTPProxyAuth
import zipfile
import tempfile
import processing
from typing import List
from osgeo import gdal, ogr
import osgeo_utils.gdal_merge
from .gdal_calc import Calc
from qgis.PyQt.QtGui import (QIcon,
                            QColor)
from  qgis.PyQt.QtNetwork import (QNetworkProxy,
                                    QNetworkReply,
                                    QNetworkRequest)
from qgis.PyQt.QtCore import (QCoreApplication,
                                QSettings,
                                QUrl)
from qgis.core import ( Qgis,
                        QgsApplication,
                        QgsAuthManager,
                        QgsAuthMethodConfig,
                        QgsCoordinateReferenceSystem,
                        QgsFeatureSink,
                        QgsFeature,
                        QgsGeometry,
                        QgsNetworkAccessManager,
                        QgsPalLayerSettings,
                        QgsPointXY,
                        QgsProcessing,
                        QgsProcessingAlgorithm,
                        QgsProcessingParameterFeatureSource,
                        QgsProcessingParameterAuthConfig,
                        QgsProcessingParameterFeatureSink,
                        QgsProcessingParameterExtent,
                        QgsProcessingParameterCrs,
                        QgsProcessingParameterDefinition,
                        QgsProcessingParameterNumber,
                        QgsProcessingParameterColor,
                        QgsProcessingParameterEnum,
                        QgsProcessingUtils,
                        QgsRuleBasedRenderer,
                        QgsSymbol,
                        QgsSymbolLayerReference,
                        QgsSymbolLayerId,
                        QgsTextMaskSettings,
                        QgsTextMaskSettings,
                        QgsTextFormat,
                        QgsVectorLayer,
                        QgsVectorLayerSimpleLabeling
                        )



'''
    TODO: 

    Adicionar suavização das curvas de nivel. Ferramentas necessárias:
    - gdal_translate
    - gdaldem
    - gdalbuildvrt
    - gdalinfo
    - gdal_calc.py
    - gdal_contour
    - ogr2ogr

'''

class CurvaDeNivelAlgorithm(QgsProcessingAlgorithm):

    # Define constantes
    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    AREA_INTERESSE = 'AREA_INTERESSE'
    INTERVALO = 'INTERVALO'
    SUAVIZACAO = 'SUAVIZACAO'
    COR_CURVAS = 'COR_CURVAS'
    AUTENTIC = 'AUTENTIC'
    
    
    # Carrega caminho da pasta de armazenamento temporario
    temp_dir = os.path.join(tempfile.gettempdir(), 'CurvaDeNivel')
    status_total = 0.0
    progresso = 0.0

    def initAlgorithm(self, config):
        
        # Adiciona entrada da área de interesse
        self.addParameter(QgsProcessingParameterExtent(self.AREA_INTERESSE, "Área de Interesse (selecionar)", optional=False))
        
        # Adiciona intervalo entre curvas
        self.addParameter(
            QgsProcessingParameterNumber(
                name = self.INTERVALO,
                description = self.tr('Intervalo entre curvas'),
                type = QgsProcessingParameterNumber.Integer,
                defaultValue = 10,
                minValue=1, 
                maxValue=1000, 
                optional = False
            )
        )
        
        # Adiciona nível de suavização
        self.addParameter(
            QgsProcessingParameterEnum(
                name = self.SUAVIZACAO,
                description = self.tr('Nível de suavização das curvas'),
                options = ['Nenhum', 'Baixo', 'Médio', 'Alto'], 
                defaultValue = 'Médio', 
                usesStaticStrings = True,
                optional = False
            )
        )
        
        # Adiciona cor da curva de nivel
        self.addParameter(
            QgsProcessingParameterColor(
                name = self.COR_CURVAS,
                description = self.tr('Coloração das curvas'),
                defaultValue = "#cc7700cc",
                opacityEnabled=True,
                optional = False
            )
        )
        
        # Adiciona autenticação
        self.addParameter(
            QgsProcessingParameterAuthConfig(
                name = self.AUTENTIC,
                description = self.tr('Usar autenticação de Proxy'),
                optional = True
            )
        )
        
        # Adiciona arquivo sink de saida
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT,self.tr('Curvas de Nível')))

    def processAlgorithm(self, parameters, context, feedback):
        
        # Cria pasta temporário para armazenar arquivos
        os.makedirs(self.temp_dir, exist_ok = True)  
        feedback.pushInfo ('\nAbrindo pasta temporária: ' + self.temp_dir)
                
        # Carrega poligono da area de interesse e cria shapefile temporario
        area_interesse = self.parameterAsExtent(parameters, self.AREA_INTERESSE, context, crs=QgsCoordinateReferenceSystem("EPSG:4326"))
        geometria_area_interesse = QgsGeometry.fromRect(area_interesse)
        caminho_shp_area_interesse = os.path.join(self.temp_dir, 'area_interesse.shp')
        shp_area_interesse = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(caminho_shp_area_interesse)
        layer_area_interesse = shp_area_interesse.CreateLayer("layer")
        featureDefn = layer_area_interesse.GetLayerDefn()
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(ogr.CreateGeometryFromWkt(geometria_area_interesse.asWkt()))
        layer_area_interesse.CreateFeature(feature)
        shp_area_interesse = None

        # Carrega o intervalo entre as curvas de nível
        intervalo = self.parameterAsInt(parameters, self.INTERVALO, context)
        
        # Carrega a opção de suavização das curvas
        suavizar = self.parameterAsString(parameters, self.SUAVIZACAO, context)
        
        # Carrega a cor das curvas de nível
        cor_curva = self.parameterAsColor(parameters, self.COR_CURVAS, context)
        
        # Carrega dados de autenticação para proxy
        usar_proxy = 0
        proxy = QNetworkProxy()
        autentic = self.parameterAsString(parameters, self.AUTENTIC, context)
        if (autentic == ''):
            feedback.pushInfo ('\nSem autenticação de proxy')
        else:
            auth_mgr = QgsApplication.authManager()
            auth_cfg = QgsAuthMethodConfig()
            auth_mgr.loadAuthenticationConfig(autentic, auth_cfg, True)
            auth_info = auth_cfg.configMap()
            try:                    
                proxy.setType(QNetworkProxy.HttpProxy)
                proxy.setHostName(urlparse(auth_info['realm']).hostname)
                proxy.setPort(urlparse(auth_info['realm']).port)
                proxy.setUser(auth_info['username'])
                proxy.setPassword(auth_info['password'])
                usar_proxy = 1
                feedback.pushInfo ('\nUtilizando autenticação de proxy para usuário: ' + auth_info['username'])
            except:
                feedback.pushInfo ('\nErro ao carregar dados de autenticação de proxy')

        # Define o caminho para baixar os rasters do INPE
        caminho_raster = 'http://www.dsr.inpe.br/topodata/data/geotiff/'
        
        # Inicializa variaveis
        lista_rasters = []
        lat_norte = 6.0
        lon_oeste = -75.0
                
        # Verifica quais arquivos raster serão utilizados
        feedback.pushInfo ('\nCalculando arquivos raster que serão utilizados')
        while (lat_norte > -34.0):
            lon_oeste = -75.0
            while (lon_oeste < -34.5):
                points = [QgsPointXY(lon_oeste, lat_norte), QgsPointXY(lon_oeste + 1.5, lat_norte), QgsPointXY(lon_oeste + 1.5, lat_norte - 1.0), QgsPointXY(lon_oeste, lat_norte - 1.0)]
                poly = QgsGeometry.fromPolygonXY([points])
                
                # Testa sobreposição do polígono de interesse com os rasters
                if not poly.intersection(geometria_area_interesse).isEmpty():

                    # Contrói nome do arquivo raster 
                    nome_raster = list("00S00_ZN")
                    nome_raster[0] = str(abs(int(lat_norte / 10)))
                    nome_raster[1] = str(abs(int(lat_norte)) % 10)
                    if lat_norte > 0:
                        nome_raster[2] = 'N'
                    nome_raster[3] = str(abs(int(lon_oeste / 10)))
                    nome_raster[4] = str(abs(int(lon_oeste)) % 10)
                    if lon_oeste % 1.0 == 0:
                        nome_raster[5] = '_'
                    else:
                        nome_raster[5] = '5'
                
                    if ''.join(nome_raster) not in lista_rasters:
                        lista_rasters.append(''.join(nome_raster))
                        feedback.pushInfo ('Arquivo necessário: ' + ''.join(nome_raster) + '.tif')
                        
                lon_oeste += 1.5
            lat_norte -= 1.0
                
        # Calcula numero de etapas para barra de progresso
        numeroDeEtapas = 5 + 2*len(lista_rasters)
        self.status_total = 100.0 / numeroDeEtapas
        self.progresso = 0.0
        
        # Atualiza progresso e barra
        self.progresso += 1
        feedback.setProgress(int(self.progresso * self.status_total))

        # Define funções de callback do download
        def proxyAuthenticationRequired(proxy, authenticator):
            feedback.pushInfo('Solicitando autenticação de proxy')
        def downloadProgress(requestId: int, bytesReceived: int, bytesTotal: int):
            progresso_download = self.progresso + bytesReceived/bytesTotal
            feedback.setProgress(int(progresso_download * self.status_total))
            
        # Busca os rasters necessários na memória, se não encontrar faz o download
        for raster in lista_rasters[:]:
            if feedback.isCanceled():
                feedback.pushInfo ('\nCancelado pelo usuário')
                return {self.OUTPUT: None}
            
            feedback.pushInfo ('\nBuscando arquivo Raster: ' + raster + '.tif')
            if os.path.exists(os.path.join(self.temp_dir, raster + '.tif')):
                feedback.pushInfo ('Arquivo localizado no disco')
            else:
                feedback.pushInfo ('Baixando arquivo raster: ' + raster + '.zip')
                raster_url = caminho_raster + raster + '.zip'
           
                networkAccessManager = QgsNetworkAccessManager.instance()
                networkAccessManager.proxyAuthenticationRequired.connect(proxyAuthenticationRequired)
                networkAccessManager.downloadProgress.connect(downloadProgress)
                networkAccessManager.setTimeout (5000)
                networkAccessManager.setFallbackProxyAndExcludes (proxy, [], [])
                raster_zip = networkAccessManager.blockingGet(QNetworkRequest(QUrl(raster_url)), forceRefresh=True, feedback=feedback)
                if raster_zip.error() == QNetworkReply.NoError and raster_zip.content():
                    with tempfile.TemporaryFile() as zip:
                        zip.write(raster_zip.content())
                        with zipfile.ZipFile(zip) as zf:
                            files = zf.namelist()
                            for filename in files:
                                feedback.pushInfo ('Descompactando arquivo: ' + filename)
                                file_path = os.path.join(self.temp_dir, filename)
                                f = open(file_path, 'wb')
                                f.write(zf.read(filename))
                                f.close()
                else:
                    feedback.pushInfo ('\nErro ao baixar o arquivo: ' + raster_url)
                    feedback.pushInfo ('\nVerifique o proxy ou a conexão com a internet')
                    feedback.pushInfo ('\nCopie e cole o link acima no navegador para testar manualmente')
                    lista_rasters.remove(raster)
                                
            # Atualiza progresso e barra
            self.progresso += 1
            feedback.setProgress(int(self.progresso * self.status_total))
       
        # Verifica se baixou algum arquivo para prosseguir com processamento, mesmo que parcial
        if (len(lista_rasters)):
            # Para cada raster baixado faz o corte para a área de sobreposição com a área de interesse
            feedback.pushInfo ('\nRecortando arquivos raster pela área de interesse')
            raster_clips = []
            
            # Define callback da biblioteca gdal
            def callback_gdal(info, *args):
                progresso_warp = self.progresso + info
                feedback.setProgress(int(progresso_warp * self.status_total))

            for raster in lista_rasters:                    
                raster_clips.append(os.path.join(self.temp_dir, raster + '_clip.tif'))
                fn_in = os.path.join(self.temp_dir, raster + '.tif')
                fn_clip = os.path.join(self.temp_dir, raster + '_clip.tif')
                
                feedback.pushInfo ('Recortando: ' + raster + '.tif')
                result = gdal.Warp(fn_clip, fn_in, cutlineDSName=caminho_shp_area_interesse, cropToCutline=True, dstNodata=0, srcSRS='EPSG:4326', dstSRS='EPSG:4326', format='GTiff', callback=callback_gdal)
                result = None
                
                if feedback.isCanceled():
                    feedback.pushInfo ('\nCancelado pelo usuário')
                    return {self.OUTPUT: None}
                
                # Atualiza progresso e barra
                self.progresso += 1
                feedback.setProgress(int(self.progresso * self.status_total))
            
            # Verifica se existem rasters cortados para unificar
            if (len(raster_clips)):
                # Unifica todas as partes recortadas dos rasters
                feedback.pushInfo ('\nJuntando arquivos raster recortados pela área de interesse')
                g = gdal.Warp(os.path.join(self.temp_dir, 'merged.tif'), raster_clips, format="GTiff", callback=callback_gdal)
                g = None
                
                if feedback.isCanceled():
                    feedback.pushInfo ('\nCancelado pelo usuário')
                    return {self.OUTPUT: None}
                
                # Atualiza progresso e barra
                self.progresso += 1
                feedback.setProgress(int(self.progresso * self.status_total))
                
                # Faz suavização
                self.suavizaTerreno (suavizar, feedback)
                
                if feedback.isCanceled():
                    feedback.pushInfo ('\nCancelado pelo usuário')
                    return {self.OUTPUT: None}
          
                # Atualiza progresso e barra
                self.progresso += 1
                feedback.setProgress(int(self.progresso * self.status_total))
               
                # Gera as curvas de nível a partir da imagem unificada
                feedback.pushInfo ('\nGerando curvas de nível')
                caminho_shp_temp = os.path.join(self.temp_dir, 'curvasdenivel.shp')
                shp_temp = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(caminho_shp_temp)
                layer_temp = shp_temp.CreateLayer("Curvas De Nivel")
                field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
                layer_temp.CreateField(field_defn)
                field_defn = ogr.FieldDefn("ELEV", ogr.OFTReal)
                layer_temp.CreateField(field_defn)
                raster_merged = gdal.Open(os.path.join(self.temp_dir, 'merged.tif'))
                gdal.ContourGenerate(raster_merged.GetRasterBand(1), intervalo, 0, [], 0, 0, layer_temp, 0, 1, callback=callback_gdal)
                shp_temp = None
                raster_merged = None
                
                if feedback.isCanceled():
                    feedback.pushInfo ('\nCancelado pelo usuário')
                    return {self.OUTPUT: None}
          
                # Atualiza progresso e barra
                self.progresso += 1
                feedback.setProgress(int(self.progresso * self.status_total))
                
                # Grava dados no arquivo de saída
                layer = QgsVectorLayer(caminho_shp_temp, 'Curvas De Nivel')
                feedback.pushInfo ('Numero de curvas geradas: ' + str(len(list(layer.getFeatures()))))
                (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                        context, layer.fields(), layer.wkbType(), QgsCoordinateReferenceSystem("EPSG:4326"))
                for feature in layer.getFeatures():
                    sink.addFeature(feature, QgsFeatureSink.FastInsert)
                                        
                # Modifica a simbologia
                layer_curvas = QgsProcessingUtils.mapLayerFromString(dest_id, context)
                symbol = QgsSymbol.defaultSymbol(layer_curvas.geometryType())
                renderer = QgsRuleBasedRenderer(symbol)
                root_rule = renderer.rootRule()
                
                # Curva Mestra
                rule = root_rule.children()[0]
                rule.setLabel("Curva Mestra")
                rule.setFilterExpression(f'"ELEV" % {intervalo*5} = 0')
                rule.symbol().setColor(cor_curva)
                rule.symbol().setWidth(0.5)
                  
                # Curva Normal           
                rule = root_rule.children()[0].clone()
                rule.setLabel("Curva Normal")
                rule.setFilterExpression('ELSE')
                rule.symbol().setColor(cor_curva)
                rule.symbol().setWidth(0.25)
                root_rule.appendChild(rule)
                
                # Salva as regras de curva
                layer_curvas.setRenderer(renderer)
                layer_curvas.triggerRepaint()
                
                # Cria os rotulos e mascara
                mask = QgsTextMaskSettings()
                mask.setSize(2)
                if Qgis.QGIS_VERSION_INT < 33000:
                    mask.setMaskedSymbolLayers([QgsSymbolLayerReference(layer_curvas.id(), QgsSymbolLayerId(root_rule.children()[0].ruleKey(), 0)), ])
                else:
                    mask.setMaskedSymbolLayers([QgsSymbolLayerReference(layer_curvas.id(), rule.symbol().symbolLayer(0).id())])
                    
                mask.setEnabled(True)
               
                # Configura texto
                textFormat = QgsTextFormat()
                textFormat.setSize(10)
                textFormat.setColor(cor_curva)
                textFormat.setMask(mask)
                # Salva configurações
                settings = QgsPalLayerSettings()
                settings.fieldName = f'CASE WHEN "ELEV" % {intervalo*5} = 0 THEN "ELEV" ELSE \'\' END'
                settings.enabled = True
                settings.drawLabels = True
                settings.repeatDistance = 50
                settings.isExpression = True
                settings.placement = QgsPalLayerSettings.Line
                settings.placementFlags = QgsPalLayerSettings.OnLine
                settings.setFormat(textFormat)
                # Grava configurações no layer e atualiza
                layer_curvas.setLabelsEnabled(True)
                layer_curvas.setLabeling(QgsVectorLayerSimpleLabeling(settings))
                layer_curvas.triggerRepaint()
                
                # Atualiza progresso e barra
                self.progresso += 1
                feedback.setProgress(int(self.progresso * self.status_total))
                
                feedback.pushInfo ('\n')
                #retorna vetor de resultado com as curvas de nivel
                return {self.OUTPUT: dest_id}
        else:
            feedback.pushInfo ('\nErro ao baixar os arquivos raster')
        
        # Retorna sem vetor de resultado
        return {self.OUTPUT: None}

    def suavizaTerreno(self, suavizar, feedback):
        # TODO: Adicionar progressão da barra de status

        if suavizar == 'Nenhum':
            return

        feedback.pushInfo('\nCalculando suavização')

        # Inicializa variáveis
        inputDEM = os.path.join(self.temp_dir, 'merged.tif')
        path = self.temp_dir  # Use apenas o diretório, sem barra extra
        method = "gaussain"
        smooth = 9

        # Gera tmp_dem.tif
        gdal.Translate(
            os.path.join(path, 'dem.tif'),
            inputDEM,
            options="-ot Float32 -a_nodata -32768"
        )

        # Constroi VRT 3x3
        gdal.BuildVRT(
            os.path.join(path, 'dem_blur_3x3.vrt'),
            os.path.join(path, 'dem.tif')
        )

        with open(os.path.join(path, "dem_blur_3x3.vrt"), "rt") as file:
            data = file.read()
        data = data.replace("ComplexSource", "KernelFilteredSource")
        data = data.replace(
            "<NODATA>-32768</NODATA>",
            '<NODATA>-32768</NODATA><Kernel normalized="1"><Size>3</Size><Coefs>0.077847 0.123317 0.077847 0.123317 0.195346 0.123317 0.077847 0.123317 0.077847</Coefs></Kernel>'
        )
        with open(os.path.join(path, "dem_blur_3x3.vrt"), "wt") as file:
            file.write(data)

        feedback.setProgress(int((self.progresso + 0.2) * self.status_total))

        # Calcula TPI
        gdal.DEMProcessing(
            destName=os.path.join(path, 'dem_tpi.tif'),
            srcDS=inputDEM,
            processing='TPI'
        )

        # Reclassifica TPI
        Calc(
            calc="((-1)*A*(A<0))+(A*(A>=0))",
            A=os.path.join(path, 'dem_tpi.tif'),
            outfile=os.path.join(path, 'tpi_pos.tif'),
            NoDataValue=-32768,
            overwrite=True
        )

        feedback.setProgress(int((self.progresso + 0.4) * self.status_total))

        # gera VRT do TPI
        gdal.BuildVRT(
            os.path.join(path, 'tpi_blur_3x3.vrt'),
            os.path.join(path, 'tpi_pos.tif')
        )

        with open(os.path.join(path, "tpi_blur_3x3.vrt"), "rt") as file:
            data = file.read()
        data = data.replace("ComplexSource", "KernelFilteredSource")
        data = data.replace(
            "<NODATA>-32768</NODATA>",
            '<NODATA>-32768</NODATA><Kernel normalized="1"><Size>9</Size><Coefs>0 0.000001 0.000014 0.000055 0.000088 0.000055 0.000014 0.000001 0 0.000001 0.000036 0.000362 0.001445 0.002289 0.001445 0.000362 0.000036 0.000001 0.000014 0.000362 0.003672 0.014648 0.023205 0.014648 0.003672 0.000362 0.000014 0.000055 0.001445 0.014648 0.058434 0.092566 0.058434 0.014648 0.001445 0.000055 0.000088 0.002289 0.023205 0.092566 0.146634 0.092566 0.023205 0.002289 0.000088 0.000055 0.001445 0.014648 0.058434 0.092566 0.058434 0.014648 0.001445 0.000055 0.000014 0.000362 0.003672 0.014648 0.023205 0.014648 0.003672 0.000362 0.000014 0.000001 0.000036 0.000362 0.001445 0.002289 0.001445 0.000362 0.000036 0.000001 0 0.000001 0.000014 0.000055 0.000088 0.000055 0.000014 0.000001 0</Coefs></Kernel>'
        )
        with open(os.path.join(path, "tpi_blur_3x3.vrt"), "wt") as file:
            file.write(data)

        feedback.setProgress(int((self.progresso + 0.6) * self.status_total))

        # Pega informações sobre o vrt do tpi
        vrt_path = os.path.join(path, 'tpi_blur_3x3.vrt')
        if not os.path.exists(vrt_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {vrt_path}")
        info = gdal.Info(ds=vrt_path, options="-hist -stats")

        # Normaliza o vrt do tpi
        try:
            maxValue = re.findall('[0-9]*\.[0-9]*', re.findall('STATISTICS_MAXIMUM=\d*.\d*', info)[0])[0]
            Calc(
                calc=f"A / {maxValue}",
                A=os.path.join(path, 'tpi_blur_3x3.vrt'),
                outfile=os.path.join(path, 'tpi_norm.tif'),
                NoDataValue=-32768,
                overwrite=True
            )
        except Exception:
            gdal.Translate(
                destName=os.path.join(path, 'tpi_norm.tif'),
                srcDS=os.path.join(path, 'tpi_blur_3x3.vrt')
            )

        feedback.setProgress(int((self.progresso + 0.8) * self.status_total))

        # Faz a suavização usando as entradas suavizadas e o TPI reclassificado
        if suavizar == "Baixo":
            Calc(
                calc="A*B+(1-A)*C",
                A=os.path.join(path, 'tpi_norm.tif'),
                B=os.path.join(path, 'dem_blur_3x3.vrt'),
                C=os.path.join(path, 'dem_blur_3x3.vrt'),
                outfile=os.path.join(path, 'merged.tif'),
                overwrite=True
            )
        elif suavizar == "Médio":
            # Constroi VRT 7x7
            gdal.BuildVRT(
                os.path.join(path, 'dem_blur_7x7.vrt'),
                os.path.join(path, 'dem.tif')
            )

            with open(os.path.join(path, "dem_blur_7x7.vrt"), "rt") as file:
                data = file.read()
            data = data.replace("ComplexSource", "KernelFilteredSource")
            data = data.replace(
                "<NODATA>-32768</NODATA>",
                '<NODATA>-32768</NODATA><Kernel normalized="1"><Size>7</Size><Coefs>0.000036 0.000363 0.001446 0.002291 0.001446 0.000363 0.000036 0.000363 0.003676 0.014662 0.023226 0.014662 0.003676 0.000363 0.001446 0.014662 0.058488 0.092651 0.058488 0.014662 0.001446 0.002291 0.023226 0.092651 0.146768 0.092651 0.023226 0.002291 0.001446 0.014662 0.058488 0.092651 0.058488 0.014662 0.001446 0.000363 0.003676 0.014662 0.023226 0.014662 0.003676 0.000363 0.000036 0.000363 0.001446 0.002291 0.001446 0.000363 0.000036</Coefs></Kernel>'
            )
            with open(os.path.join(path, "dem_blur_7x7.vrt"), "wt") as file:
                file.write(data)

            Calc(
                calc="A*B+(1-A)*C",
                A=os.path.join(path, 'tpi_norm.tif'),
                B=os.path.join(path, 'dem_blur_3x3.vrt'),
                C=os.path.join(path, 'dem_blur_7x7.vrt'),
                outfile=os.path.join(path, 'merged.tif'),
                overwrite=True
            )
        else:
            # Constroi VRT 13x13
            gdal.BuildVRT(
                os.path.join(path, 'dem_blur_13x13.vrt'),
                os.path.join(path, 'dem.tif')
            )

            with open(os.path.join(path, "dem_blur_13x13.vrt"), "rt") as file:
                data = file.read()
            data = data.replace("ComplexSource", "KernelFilteredSource")
            data = data.replace(
                "<NODATA>-32768</NODATA>",
                '<NODATA>-32768</NODATA><Kernel normalized="1"><Size>13</Size><Coefs>0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.000001 0.000001 0.000001 0 0 0 0 0 0 0 0 0.000001 0.000014 0.000055 0.000088 0.000055 0.000014 0.000001 0 0 0 0 0.000014 0.000362 0.003672 0.014648 0.023204 0.014648 0.003672 0.000362 0.000014 0 0 0 0.000001 0.000055 0.001445 0.014648 0.058433 0.092564 0.058433 0.014648 0.001445 0.000055 0.000001 0 0 0.000001 0.000088 0.002289 0.023204 0.092564 0.146632 0.092564 0.023204 0.002289 0.000088 0.000001 0 0 0.000001 0.000055 0.001445 0.014648 0.058433 0.092564 0.058433 0.014648 0.001445 0.000055 0.000001 0 0 0 0.000014 0.000362 0.003672 0.014648 0.023204 0.014648 0.003672 0.000362 0.000014 0 0 0 0 0.000001 0.000036 0.000362 0.001445 0.002289 0.001445 0.000362 0.000036 0.000001 0 0 0 0 0 0.000001 0.000014 0.000055 0.000088 0.000055 0.000014 0.000001 0 0 0 0 0 0 0 0 0.000001 0.000001 0.000001 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0</Coefs></Kernel>'
            )
            with open(os.path.join(path, "dem_blur_13x13.vrt"), "wt") as file:
                file.write(data)

            Calc(
                calc="A*B+(1-A)*C",
                A=os.path.join(path, 'tpi_norm.tif'),
                B=os.path.join(path, 'dem_blur_3x3.vrt'),
                C=os.path.join(path, 'dem_blur_13x13.vrt'),
                outfile=os.path.join(path, 'merged.tif'),
                overwrite=True
            )

        feedback.setProgress(int((self.progresso + 1.0) * self.status_total))
       
    def icon(self):
        cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
        icon = QIcon(os.path.join(os.path.join(cmd_folder, 'logo.png')))
        return icon
        
    def name(self):

        return 'Curva de Nivel'

    def displayName(self):

        return self.tr(self.name())

    def group(self):

        return self.tr(self.groupId())

    def groupId(self):

        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CurvaDeNivelAlgorithm()
