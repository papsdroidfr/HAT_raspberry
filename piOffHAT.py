#!/usr/bin/env python3
########################################################################
# Filename    : piOffHAT.py
# Description : carte HAT avec bouton extinction Raspberry Pi et contrôle FAN
# auther      : papsdroid.fr
# modification: 2019/09/20
########################################################################

import RPi.GPIO as GPIO
import time, os, threading

# Classe qui gère le bouton poussoir Off: extinction du raspi
#-------------------------------------------------------------------------------
class Button_quit():
    def __init__(self, appl, powerOff):
        #------------------------------------------------------------------------
        # appl: instance de l'application principale
        # powerOff: True (extinction du raspi) ou False (arret du pgm)
        #------------------------------------------------------------------------
        self.appl = appl                # application principale qui instancie un Button_quit
        self.powerOff = powerOff        # True: extinction du raspberry, False=Raspberry reste allumé (pour faire des tests)
        self.buttonPin=10               # Pin GPIO connecté au bouton
        self.on=False                   # etat off au début: bouton non appuyé
        GPIO.setup(self.buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set buttonPin's mode is input, and pull up to high level(3.3V)
        GPIO.add_event_detect(self.buttonPin,GPIO.FALLING,callback=self.buttonEventQuit, bouncetime=300)

    #méthode exécutée lors de l'appui sur le bouton quit = "OFF"
    def buttonEventQuit(self,channel): 
        self.on = True
        print('button Off pressé')
        if self.powerOff:
           print('Extinction Raspberry...')
           os.system('sudo halt')   #provoque l'extinction du raspberry
        #code exécuté si mode powerOff=False
        self.appl.destroy()   
        raise SystemExit
        

#classe de lecture de T° CPU pour contrôle FAN (via un thread)
#-----------------------------------------------------------------------------------------
class ReadT(threading.Thread):
    def __init__(self, tFanMin, tFanMax, verbose):
        #---------------------------------------------------------------------------------
        # tFanMin: T° d'arrêt du ventilateur quand il est allumé
        # tFanMax: T° de déclenchement du ventilateur quand il est à l'arrêt
        # verbose: True (active les print à la console) ou False
        #---------------------------------------------------------------------------------

        threading.Thread.__init__(self)  # appel au constructeur de la classe mère Thread
        self.verbose = verbose           # True active les print
        self.etat=False                  # état du thread False(non démarré), True (démarré)
        self.delay = 30                  # délay en secondes entre chaque nouvelle lecture
        self.fan_tOn  = tFanMax          # température d'activation du ventilateur
        self.fan_tOff = tFanMin          # température d'extinction du ventilateur
        self.cpu_t=0                     # température du CPU  
        self.fanPin   = 8                # GPIO pin: control fan power
        GPIO.setup(self.fanPin, GPIO.OUT)
        GPIO.output(self.fanPin,GPIO.LOW) # fan off au début
        self.fanOn    = False             # True: ventilateur en marche, False: ventilateur à l'arrêt

    #lecture de la température CPU
    def get_cpu_temp(self):     
        tmp = open('/sys/class/thermal/thermal_zone0/temp')
        cpu = tmp.read()
        tmp.close()
        return (float(cpu)/1000)

    #converti la t° CPU en % entre t_min et t_max
    def convert_cpu_pct(self):
        return (float)(self.cpu_t-self.t_min)/(self.t_max-self.t_min)*100

    #active ou désactive le ventilateur
    def fan_chg(self, activation:True):
        GPIO.output(self.fanPin, activation and GPIO.HIGH or GPIO.LOW)
        self.fanOn = activation
        if self.verbose:
            print('Ventilateur', self.fanOn, 'cpu_t:',self.cpu_t,'°C')
        
    
    #démarrage du thread
    def run(self):
        self.etat=True
        if self.verbose:
            print('Thread lecture température démarré')
        while (self.etat):
            #lecture et stockage des informations système
            self.cpu_t = self.get_cpu_temp()
            if self.verbose:
                print ('CPU T°:', self.cpu_t,'°C')
            #ctrl du ventilateur
            if not(self.fanOn) and (self.cpu_t >= self.fan_tOn):
                self.fan_chg(True)
            elif self.fanOn and (self.cpu_t < self.fan_tOff): #extinction ventilateur
                self.fan_chg(False)
            #mise en veille
            time.sleep(self.delay)

    #arrêt du thread
    def stop(self):
        self.etat=False
        if self.verbose:
            print('Thread lecture info système stoppé')

#classe d'Application principale
#------------------------------------------------------------------------------------------------------
class Application:
    def __init__(self, tFanMin=40, tFanMax=55, verbose=False, powerOff=True):
        #----------------------------------------------------------------------------------------------
        # tFanMin: T° d'arrêt du ventilateur quand il est allumé, par défaut 40°C
        # tFanMax: T° de déclenchement du ventilateur quand il est à l'arrêt, par défaut 55°C
        # verbose: True (active les print à la console) ou False par défaut
        # powerOff: True pzr défaut (etteind le raspi si appui sur bouton Off) ou False (arrêt fu pgm)
        #-----------------------------------------------------------------------------------------------
        print('Démarrage PiOff. CTRL+C pour interrompre, ou appuyer sur le bouton Off.')
        GPIO.setmode(GPIO.BOARD)                            # identification des GPIOs par location physique
        self.buttonQuit = Button_quit(self, powerOff)       # mettre powerOff=False pour des tests sans extinction du rpi
        self.readT = ReadT(tFanMin, tFanMax, verbose)       # thread de lecture T° CPU 
        self.readT.start()                                  # démarrage du thread de lecture des info systèmes

    #boucle principale du prg
    def loop(self):
        while True :
            #todo ... code du programme à ajouter ici  ... 
            time.sleep(1)  # mise en attente 1s (sinon boucle infinie qui sature un proc).

    #méthode de destruction    
    def destroy(self):
        print ('bye')
        self.readT.stop()   #arrêt du thread lecture T° CPU
        #todo code à ajouter ici avant de sortir du programme
        GPIO.cleanup()
        
    
if __name__ == '__main__':
    appl=Application()                             # mode par défaut: extinction du raspi si appui sur Off
    #appl=Application(verbose=True, powerOff=False)  # mode test
    
    try:
        appl.loop()
    except KeyboardInterrupt:  # interruption clavier CTRL-C: appel à la méthode destroy() de appl.
        appl.destroy()
