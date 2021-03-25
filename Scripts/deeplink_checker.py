from re import M
import pymongo
import argparse
import time
import random
import requests
from handle.datamanager                         import Datamanager
from selenium                                   import webdriver
import sshtunnel
from pathlib      import Path

def sshConnect():
    base_path = Path(__file__).parent
    file_path = (base_path / "misato")
    __file = str(file_path)

    sshtunnel.SSH_TIMEOUT = sshtunnel.TUNNEL_TIMEOUT = 10.0

    server = sshtunnel.open_tunnel(
        ('168.61.73.89', 31415),
        ssh_username='bb',
        ssh_pkey=__file,
        ssh_private_key_password ='KLM2012a',
        remote_bind_address=('127.0.0.1', 27017)
    )
    return server

class Deeplink_check():
    def __init__(self,platform:str,created_at:str,selenium:bool,sample:int,timeout:int,mongodb:str,file:str):
        self._platform_code = platform
        self._created_at = created_at
        self.selenium = selenium
        self.sample = sample
        self.timeout = timeout
        self.sesion = requests.session()
        self.mongodb = mongodb
        self.file = file

    def start(self):
        listDb = self.obtener_de_mongo()
        listDb = random.sample(listDb,self.sample)

        for idx,item in enumerate(listDb):
            print("\n \x1b[1;33;40m Title number: \x1b[0m",idx)
            print(" \x1b[1;33;40m Title: \x1b[0m"+item['Title'])
            self.openDeeplink(item)
            

    def obtener_de_mongo(self):
        if self.mongodb != 'misato':
            client_local = pymongo.MongoClient("mongodb://localhost:27017")
            db_local = client_local["titan"]
            collection = db_local["titanScraping"]

            if self._created_at == 'last':
                params = {'PlatformCode': self._platform_code}
                sort   = [("CreatedAt", pymongo.DESCENDING)]
                limit = 1
                lastItem = collection.find(params).sort(sort).limit(limit)
                if collection.count_documents(params,limit=limit) > 0:
                    for lastContent in lastItem:
                        created_at = lastContent['CreatedAt']
            print('Mongo local: ' + created_at)
            payload = {
            'PlatformCode'  : self._platform_code,
            'CreatedAt'     : created_at
            }
            cursor = collection.find(payload, no_cursor_timeout=True, projection={'_id': 0, 'Title': 1, 'Deeplinks' : 1})
            listDb = list(cursor)
            return listDb
        else:
            server = sshConnect()
            server.start()
            time.sleep(11)
            client   = pymongo.MongoClient('127.0.0.1', server.local_bind_port)
            business = client['business']
            db_api = business['apiPresence']

            payload_api = {
            'PlatformCode'  : self._platform_code
            }

            print('Obteniendo DB de apiPresence ...')
            
            col = 'Title'
            api = db_api.find(payload_api, no_cursor_timeout=True, projection=[col, 'Deeplinks','Status']).batch_size(10)
            api = [dict(item) for item in api if item['Status'] != 'inactive']
            
            with open(self.file,'r') as f:
                lines = f.readlines()
                
                flag1 = False
                flag2 = False
                titles = []
                for line in lines:
                    line = line.strip()
                    if 'Titulos apiPresence que no estan en Local' in line:
                        flag1 = True
                    elif 'Titulos Local que no estan en apiPresence' in line:
                        flag2 = True

                    if flag1 and not flag2 and 'Titulos apiPresence que no estan en Local' not in line:
                        titles.append(line)

            titles_to_review = []
            for title in titles:
                for row in api:
                    if row.get('Title') == title:
                        titles_to_review.append(row)

            return titles_to_review
    
    def openDeeplink(self,dict:dict):
        url = dict.get('Deeplinks').get('Web')
        browser = None
        if self.selenium:
            browser = webdriver.Firefox()
            try:
                print("     \x1b[1;33;40m Intentando URL ----> \x1b[0m"+url)
                browser.get(url)
            except:
                browser.close()
        else:
            soup = Datamanager._getSoup(self,url)
            print(soup)
            
        time.sleep(self.timeout)
        if browser:
            try:
                browser.close()
            except:
                pass


if __name__ == '__main__':
    args = None
    parser =  argparse.ArgumentParser()
    parser.add_argument('file',help='Archivo de deeplinks',type=str)
    parser.add_argument('-p', '-platformCode',help='PlatformCode',type=str,required=True)
    parser.add_argument('--samp','--sample',help='Cantidad de muestras para revisar',type=int,default=10)
    parser.add_argument('--at',help ='CreatedAt', type=str,default='last')
    parser.add_argument('--sel', '--selenium',help = 'Si se quiere revisar con selenium', action='store_true', default=False)
    parser.add_argument('--timeout', help='Tiempo de espera en cada pagina con selenium',type=int,default=15)
    try:
        args            = parser.parse_args()
        file            = args.file
        platformCode    = args.p
        sample          = int(args.samp)
        created_at      = args.at
        selenium        = args.sel
        timeout         = args.timeout

        print("PlatformCode: " + platformCode)
        if file:
            mongodb = 'misato'
        else:
            mongodb = 'local'
        if created_at:
            print("CreatedAt: " + created_at)
        if selenium:
            print("Selenium: " + str(selenium))
        if sample:
            print("Sample: ",sample)
        if timeout:
            print("Timeout: ",timeout)

    except Exception as e:
        print("Argumentos erroneos, revisar sintaxis.\n")
        print("Error: " ,e)
        
        print("\nNombre del archivo de comparacion de seba.")
        print("PlatformCode para obtener de la titanscraping.")
        print("--sample Para setear la cantidad de muestras a revisar(Por defecto es 10).")
        print("--at Para obtener links con un created_at especifico.")
        print("--sel Para revisar los links con selenium.")
        raise e

    if args:
        deeplink_checker = Deeplink_check(platformCode,created_at,selenium,sample,timeout,mongodb,file)
        deeplink_checker.start()

