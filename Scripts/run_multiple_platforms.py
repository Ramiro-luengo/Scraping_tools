import argparse
import json
import subprocess
from threading import Thread
import time
import re

def run_command(command):
    print(command)
    # cmd = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    cmd = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, error = cmd.communicate()
    if(error):
        print('No pudo terminar el comando: ', command)
        with open("errors.log",'a') as f:
            f.write("Comando: " + command)
            f.write("\n")
            f.write("   Error:" + error.decode("utf-8"))
    if(output):
        regex = re.findall(r'[A-Z]+\w+', command)
        var_1 = regex[0]
        var_2 = regex[1]
        if len(var_1) > 2:
            fileName = var_2 + '.' + var_1
        else:
            fileName = var_1.lower() + '.' + var_2.lower() 
        with open(fileName +".log",'w') as f:
            f.write(output.decode("utf-8"))

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
    print(" Este programa requiere un archivo .json con la configuracion de cada plataforma a correr.\n")
    print("     La operacion(--o) por defecto es scraping")
    print("     La cantidad de threads maxima(--c) por default es 5.")
    parser =  argparse.ArgumentParser()
    parser.add_argument('file', help = 'Archivo de platformcodes',type=str, nargs="+")
    parser.add_argument('--o', help = 'Operacion: scraping o testing', type=str, default='scraping')
    parser.add_argument('--c', help = 'Cantidad de threads maxima',type=int,default=5)

    try:
        args = parser.parse_args()
        files = args.file
        file=files[0]
        if file.split(".")[1] != "json":
            raise Exception("La estension del archivo debe ser .json")
        if len(files) > 1:
            raise Exception("Solo se puede tener un archivo de plataformas")
        operation = args.o
        if operation != 'scraping' and operation != 'testing':
            raise Exception("Wrong operation: {operation}")
        cantidad_de_threads = args.c
        if cantidad_de_threads > 15:
            print("La cantidad de threads maxima es muy alta({cantidad_de_threads}), consumira mucha memoria y procesador")
            print("Tiene 5 segs para reconsiderarlo, sino el programa avanzara normalmente")
            time.sleep(5)
    except Exception as e:
        print('Error de argumentos, use -h para ver los argumentos que lleva el programa\n')
        print(e)
        exit()
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

    print("Todos los codigos fueron ejecutados")