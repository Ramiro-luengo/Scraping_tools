from handle.scraper import Scraper

class Algo(Scraper):
    def __init__(self, ott_site_uid, ott_site_country, type):
        super().__init__(ott_site_uid, ott_site_country, type)
    
    def _scraping(self,testing=False):
        print('hola')


algo = Algo("TvDOrange","FR","scraping")