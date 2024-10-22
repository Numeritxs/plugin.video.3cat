from __future__ import division

from builtins import object
from collections import defaultdict

from bs4 import BeautifulSoup


from resources.lib.tv3cat import DirAZemisio
from resources.lib.tv3cat import DirAZtots
from resources.lib.tv3cat import Home
from resources.lib.tv3cat.Images import Images
from resources.lib.tv3cat import Sections
from resources.lib.utils import Urls
from resources.lib.utils.Urls import url_base
from resources.lib.video.FolderVideo import FolderVideo
from resources.lib.video.Video import Video
from resources.lib.tv3cat.TV3Strings import TV3Strings
from resources.lib.utils.Utils import *


class TV3cat(object):
    def __init__(self, addon_path, addon):
        xbmc.log("plugin.video.3cat classe TV3cat - init() ")
        self.strs = TV3Strings(addon)
        self.images = Images(addon_path)
        self.addon_path = addon_path

    # mode = None
    def listHome(self):
        xbmc.log("plugin.video.3cat classe Tv3cat - listHome() ")

        return Home.getList(self.strs)

    def getJsonDataNextData(self, url):
        link = getHtml(url)

        if link:
            soup = BeautifulSoup(link, "html.parser")

            script_tag = soup.find('script', id='__NEXT_DATA__')
            if script_tag:
                xbmc.log("plugin.video.3cat - found script")

                # Find all items with 'titol' and 'id'
                # Extract the JSON content from the script tag
                json_content = script_tag.string
                # print(json_content)
                # Extract the data from the JSON content
                data = json.loads(json_content)

                # Extract the required information
                return data

        return []

    def getTotsProgrames(self):
        data = self.getJsonDataNextData(Urls.url_coleccions)
        if not data:
            return []
        # Extract the required information
        return data['props']['pageProps']['layout']['structure'][4]['children'][0]['finalProps']['items']

    def getProgramaId(self, titolPrograma):
        data = self.getJsonDataNextData(Urls.url_base + titolPrograma)
        if not data:
            return []

        return data['props']['pageProps']['layout']['structure'][3]['children'][0]['finalProps']['programaId']

    # mode = coleccions
    def listProgrames(self, nomCategoria):
        xbmc.log("plugin.video.3cat - programes per categoria " + nomCategoria)
        lFolderVideos = []
        categories = self.getTotsProgrames()
        for categoria in categories:
            if nomCategoria == categoria['valor']:
                xbmc.log("plugin.video.3cat - Found categoria " + nomCategoria)
                items = categoria['item']
                for item in items:
                    if 'titol' in item and 'id' in item:
                        xbmc.log("plugin.video.3cat - element " + str(item))
                        titol = item['titol']
                        nombonic = item['nombonic']
                        img = self.extractImageIfAvailable(item, "IMG_POSTER")
                        foldVideo = FolderVideo(titol, nombonic, 'getTemporades', img, img)
                        lFolderVideos.append(foldVideo)

                return lFolderVideos

        return lFolderVideos


    # mode = coleccions
    def listColeccions(self):
        xbmc.log("plugin.video.3cat - listColeccions")
        lFolderVideos = []

        for categoria in self.getTotsProgrames():
            print(categoria)
            nom_categoria = categoria['valor']
            xbmc.log("plugin.video.3cat - Found categoria " + nom_categoria)
            foldVideo = FolderVideo(nom_categoria, nom_categoria, 'getProgrames')
            lFolderVideos.append(foldVideo)

        return lFolderVideos


    # mode = programes
    def dirSections(self):
        return Sections.getList(self.strs)

    # mode = directe
    def listDirecte(self):
        xbmc.log("plugin.video.3cat listDirecte")

        tv3Directe = Video(self.strs.get('tv3'), self.images.thumb_tv3, self.images.thumb_tv3, "TV3", Urls.url_directe_tv3, "")
        c324Directe = Video(self.strs.get('canal324'), self.images.thumb_324, self.images.thumb_324, "324", Urls.url_directe_324, "")
        sx3Directe = Video(self.strs.get('sx3'), self.images.thumb_sx3, self.images.thumb_sx3, "SX3", Urls.url_directe_sx3, "")
        sps3Directe = Video(self.strs.get('esport3'), self.images.thumb_esp3, self.images.thumb_esp3, "E3", Urls.url_directe_esport3, "")
        c33Directe = Video("C33", self.images.thumb_c33, self.images.thumb_c33, "E3", Urls.url_directe_c33, "")

        return [tv3Directe, sx3Directe, c324Directe, sps3Directe, c33Directe]


    def getProgramaData(self, programaId):
        apiUrl = ("https://api.3cat.cat/videos?version=2.0&_format=json&items_pagina=1000&capitol=1|&tipus_contingut=PPD&ordre=capitol&idioma=PU_CATALA&programatv_id={}&perfil=pc"
                  .format(programaId))

        with urllib.request.urlopen(apiUrl) as response:
            data = response.read()
            json_data = json.loads(data)
            return json_data['resposta']['items']['item']

    #mode getTemporades
    def getListTemporades(self, programaTitol):
        xbmc.log("plugin.video.3cat llista temporades " + programaTitol)
        lFolderVideos = []
        programaId = self.getProgramaId(programaTitol)
        items = self.getProgramaData(programaId)

        # Set to store unique temporades
        unique_temporades = set()

        # Count items without temporades
        sense_temporada_count = 0

        for item in items:
            if item.get('temporades'):
                # Only consider the first temporada
                first_temporada = item['temporades'][0]['desc']
                unique_temporades.add(first_temporada)
            else:
                sense_temporada_count += 1

        # Add "Sense Temporada" if there are items without temporades
        if sense_temporada_count > 0:
            unique_temporades.add("Sense Temporada")

        for temporada in unique_temporades:
            foldVideo = FolderVideo(temporada, str(programaId) + "_" + str(temporada), 'getlistvideos', '', '')
            lFolderVideos.append(foldVideo)

        return lFolderVideos

    def extractImageIfAvailable(self, item, keyimatge):
        # Extract image links if available
        if 'imatges' in item and isinstance(item['imatges'], list):
            for image in item['imatges']:
                if 'text' in image and image['text'].startswith('http') \
                        and image['rel_name'] == keyimatge:
                    return image['text']

    # mode = getlistvideos
    def getListVideos(self, url):
        xbmc.log("plugin.video.3cat - get list videos " + str(url))
        (programaId, target_temporada) = url.split('_')
        lVideos = []
        matching_items = []

        for item in self.getProgramaData(programaId):
            if item.get('temporades'):
                # Only consider the first temporada
                first_temporada = item['temporades'][0]['desc']
                if first_temporada == target_temporada:
                    matching_items.append(item)
            elif target_temporada == "Sense Temporada":
                matching_items.append(item)

        # Display results
        if matching_items:
            print(f"Items matching temporada '{target_temporada}':")
            for item in matching_items:
                img = self.extractImageIfAvailable(item, "KEYVIDEO")
                video = Video(item['titol'], img, img, item.get('entradeta'), item['id'], item['durada'])
                lVideos.append(video)
        else:
            print(f"No items found for temporada '{target_temporada}'")

        return lVideos

<<<<<<< HEAD
    def getVideo(self, data):
        linkvideo = None
        media = data.get('media', {})

        if type(media) is list and len(media) > 0:
            media_dict = media[0]
            linkvideo = media_dict.get('url', None)
        else:
            linkvideo = media.get('url', None)

        if linkvideo != None:
            if type(linkvideo) is list and len(linkvideo) > 0:
                linkvideo_item = linkvideo[0]
                urlVideo = linkvideo_item.get('file', None)

            titol = data.get('informacio', {}).get('titol', None)
            image = data.get('imatges', {}).get('url', None)
            descripcio = data.get('informacio', {}).get('descripcio', None)
            programa = data.get('informacio', {}).get('programa', None)
            capitol = data.get('informacio', {}).get('capitol', None)
            tematica = data.get('informacio', {}).get('tematica', {}).get('text', None)
            data_emisio = data.get('informacio', {}).get('data_emissio', {}).get('text', None)
            milisec = data.get('informacio', {}).get('durada', {}).get('milisegons', None)
            durada = ""

            if milisec != None:
                durada = milisec // 1000


            if descripcio == None:
                descripcio = ''
            else:
                descripcio = descripcio.replace('<br />', '')

            header = ""
            if programa != None:
                if type(programa) is int or type(programa) is float:
                    programa = str(programa)
                header = '[B]' + programa + '[/B]' + '[CR]'

            infolabels = {}
            if data_emisio != None:
                dt = data_emisio[0:10]
                year = data_emisio[6:10]
                infolabels['aired'] = dt
                infolabels['year'] = year
                header = header + dt + '[CR]'

            descripcio = header + descripcio

            if titol != None:
                infolabels['title'] = titol


            if capitol != None:
                infolabels['episode'] = capitol


            if descripcio != None:
                infolabels['plot'] = descripcio

            if tematica != None:
                infolabels['genre'] = tematica

            video = Video(titol, image, image, infolabels, urlVideo, durada )

            return video

        else:
            return None

=======
>>>>>>> b61338052579a171752565819369c4aa00a05a7d
    #mode = cercar
    def search(self):
        xbmc.log("plugin.video.3cat - cercar")
        keyboard = xbmc.Keyboard('', self.strs.get('cercar'))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            search_string = keyboard.getText().replace(" ", "+")
            url = "https://www.3cat.cat/3cat/cercador/?cerca=" + search_string
            titolPrograma = url.split('=')[1].replace("+", "-")
            lVideos = self.listProgramesNom(titolPrograma)

        return lVideos
    
    def listProgramesNom(self, titolPrograma):
            xbmc.log("plugin.video.3cat - programes per nom " + str(titolPrograma))
            lFolderVideos = []
            programaId = self.getProgramaId(titolPrograma)
            programes = self.getProgramaData(programaId)
            for programa in programes:
                 if titolPrograma == programa['programes_tv'][0]['nom_bonic']:
                    xbmc.log("plugin.video.3cat - Found programa " + str(titolPrograma))
                    titol = programa['programes_tv'][0]['titol']
                    nombonic = programa['programes_tv'][0]['nom_bonic']
                    img = self.extractImageIfAvailable(programa['programes_tv'][0], "IMG_POSTER")
                    foldVideo = FolderVideo(titol, nombonic, 'getTemporades', img, img)
                    lFolderVideos.append(foldVideo)

                    return lFolderVideos

            return lFolderVideos

