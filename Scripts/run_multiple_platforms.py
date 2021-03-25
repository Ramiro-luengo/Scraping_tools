import os
import argparse
import json
from threading import Thread
import traceback
import time

def run_command(command):
    print(command)
    try:
        os.system(command)
    except Exception as e:
        print('No pudo terminar el comando: ', command)
        print(e)

        with open("errors.log",'w') as f:
            f.write("Comando: ",command)
            f.write("\n")
            f.write("   Error:" + traceback.format_exc())

def control_threads(thread_list,max_thread_count):
    running_threads = []
    sleeping_threads = []
    
    for idx,thread in enumerate(thread_list):
        if idx < max_thread_count:
            running_threads.append(thread)
        else:
            sleeping_threads.append(thread)
                
    for thread in running_threads:
        thread.start()
    
    for thread in running_threads:
        thread.join()
    
    if sleeping_threads:
        control_threads(sleeping_threads,max_thread_count)

def get_command(country_code,commandpairs):
    for command in commandpairs:
        if command['CountryCode'] == country_code:
            return command['Commands']

def analizeVPN(command_tuple):
    """ 
        Analiza todos los countrycodes distintos y los agrupa en un lista 
        a los comandos con mismo countrycode.
    """
    unique_vpns = set()
    for command,country_code in command_tuple:
        unique_vpns.add(country_code)

    commandpairs = []
    for vpn in unique_vpns:
        commandpairs.append({ 'CountryCode' : vpn, 'Commands' : []})
    
    for commandpair in commandpairs:
        vpn_code = commandpair['CountryCode']
        for command,country_code in command_tuple:
            if country_code == vpn_code and (command not in [c1 for c1 in get_command(country_code,commandpairs)]):
                for c in commandpairs:
                    if c['CountryCode'] == country_code:
                        c['Commands'].append(command)

    print(commandpairs)
    return commandpairs
    
def run_commands(max_thread_count, commands):
    threads = []
    for command in commands:
        try:
            thread = Thread(target = run_command, args = (command,))
            threads.append(thread)
        except:
            print('Error de hilo en comando: ' + command)
    if threads:
        control_threads(threads,max_thread_count)

if __name__ == '__main__':
    """
        This script is used to run multiple platform scripts from different regions and different
        classes. It only works with the current system using all platform imports on "Main". 
    """
    print("Este programa requiere un archivo .json con la configuracion de cada plataforma a correr.\n")
    print("     La operacion(--o) por defecto es scraping y la cantidad de threads maxima(--c) por default es 10.")
    parser =  argparse.ArgumentParser()
    parser.add_argument('file', help = 'Archivo de platformcodes',type=str, nargs="+")
    parser.add_argument('--o', help = 'Operacion: scraping o testing', type=str, default='scraping')
    parser.add_argument('--c', help = 'Cantidad de threads maxima',type=int,default=10)

    try:
        args = parser.parse_args()
        file = args.file
        if len(file) > 1:
            pass
        file=file[0]
        operation = args.o
        if operation != 'scraping' or operation != 'testing':
            raise Exception("Wrong operation: {operation}")
        cantidad_de_threads = args.c
        if cantidad_de_threads > 15:
            print("La cantidad de threads maxima es muy alta({cantidad_de_threads}), consumira mucha memoria y procesador")
            time.sleep(5)
    except:
        print('Error de argumentos, use -h para ver los argumentos que lleva el programa')
    
    if file:
        with open(file,'r') as fjson:
            configurations = json.load(fjson)

            needVPN = []
            commands = []
            for f in configurations['Configurations']:
                class_name =  f['ClassName']
                for country in f['Countries']:
                    print("PlatformCode : "+ country["CountryCode"]) 
                    
                    country_code = country["CountryCode"].split('.')[0]
                    need_vpn = False

                    if country.get('NeedVPN'):
                        need_vpn = country.get('NeedVPN')
                    
                    command = 'py main.py "--c"'+ ' "{}" '.format(country_code.upper()) + '"--o"' + ' "{}" '.format(operation) + class_name
                    
                    if not need_vpn:
                        commands.append(command)
                    else:
                        needVPN.append((command,country_code))
            print("Corriendo paises que no necesitan VPN")
            run_commands(cantidad_de_threads, commands)
            
            # Si tiene VPN se corre al final en caso de haber alguno sin VPN.
            commands_with_vpn = analizeVPN(needVPN)

            if commands_with_vpn:
                for command in commands_with_vpn:
                    print("Usar el vpn del pais con codigo: " + command['CountryCode'].upper())
                    input("Apretar Enter luego de conectar el VPN...")
                    run_commands(cantidad_de_threads,command['Commands'])

    print("Todos los codigos fueron ejecutados correctamente.")