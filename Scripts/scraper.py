import time
import requests
# import sys
# sys.path.append('..')
from handle.datamanager     import Datamanager
from handle.mongo           import mongo
from handle.replace         import _replace
from common                 import config
from abc                    import ABC, abstractmethod

class Scraper(ABC):
    def __init__(self, ott_site_uid, ott_site_country, type):
        self._test                  = True if type == 'testing' else False
        self._config                = config()['ott_sites'][ott_site_uid]
        self._platform_code         = self._config['countries'][ott_site_country]
        self._created_at            = time.strftime("%Y-%m-%d")
        self.mongo                  = mongo()
        self.titanPreScraping       = config()['mongo']['collections']['prescraping']
        self.titanScraping          = config()['mongo']['collections']['scraping']
        self.titanScrapingEpisodios  = config()['mongo']['collections']['episode']
        self.skippedTitles = 0
        self.skippedEpis = 0

        self.payloads_shows = []
        self.payloads_episodes = []
        self.saved_show_ids = Datamanager._getListDB(self,self.titanScraping)
        self.saved_epis_ids = Datamanager._getListDB(self,self.titanScrapingEpisodios)

        self.sesion = requests.session()
        self.headers  = {"Accept":"application/json",
                         "Content-Type":"application/json; charset=utf-8"}

        if type == 'return':
            '''
            Retorna a la Ultima Fecha
            '''
            params = {"PlatformCode" : self._platform_code}
            lastItem = self.mongo.lastCretedAt(self.titanScraping, params)
            if lastItem.count() > 0:
                for lastContent in lastItem:
                    self._created_at = lastContent['CreatedAt']
                    
            self._scraping()
        
        if type == 'scraping' or type == 'testing':
            self._scraping(testing = self._test)

    @abstractmethod
    def _scraping(self,testing=False):
        pass