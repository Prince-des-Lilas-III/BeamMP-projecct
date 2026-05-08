from datetime import datetime
import socket
import csv
import shlex
import os
import json
from colorama import init, just_fix_windows_console
import shutil
import subprocess
from tabulate import tabulate
from termcolor import colored


# Définitions du chemin absolu actuel du projet
os.chdir(os.path.abspath(os.path.join("Luncher")))

def getIP():
    """Récupère l'adresse IP de la machine hôte.

    Returns:
        str: Adresse IP de la machine
    """
    ip = socket.gethostbyname(socket.gethostname())
    return ip

def getDate():
    """Retourne la date actuelle formatée en JJ/MM/AAAA.

    Returns:
        str: Date au format "JJ/MM/AAAA"
    """
    return datetime.now().strftime("%d/%m/%Y")

def getTime():
    """Retourne l'heure actuelle formatée en HH:MM:SS.

    Returns:
        str: Heure au format "HH:MM:SS"
    """
    return datetime.now().strftime("%H:%M:%S")

def getDataCommand():
    return "[" +colored(getIP(), rgb("yellow")) + "] [" + colored(getDate(), rgb("lightgreen")) + "] [" + colored(getTime(), rgb("lightgreen")) + "]"


def debug(message):
    """Affiche un message de débogage formaté.

    Args:
        message (str): Message à afficher
    """
    print("[" + colored("DEBUG", rgb("red"), attrs=["bold"]) + "] " + message)

def warn(message):
    """Affiche un message d'avertissement formaté.

    Args:
        message (str): Message à afficher
    """
    print("[" + colored("WARNING", rgb("orange"), attrs=["bold"]) + "] " + message)

def error(message):
    """Affiche un message d'erreur formaté.

    Args:
        message (str): Message à afficher
    """
    print("[" + colored("ERROR", rgb("red"), attrs=["bold"]) + "] " + message)

def info(message):
    """Affiche un message d'information formaté.

    Args:
        message (str): Message à afficher
    """
    print("[" + colored("INFO", rgb("green"), attrs=["bold"]) + "] " + message)



rgbData = {}
def rgb(*args):
    global rgbData
    """Crée un tuple RGB pour la coloration du texte.

    Args:
        *args: Valeurs rouge, verte et bleue (0-255) ou nom de couleur

    Returns:
        tuple: Tuple RGB (r, g, b)
    """
    if len(args) == 3 and all(0 <= arg <= 255 for arg in args):
        return (args[0], args[1], args[2])
    elif len(args) == 1 and isinstance(args[0], str):
        if not(args[0].lower() in rgbData):
            try:
                with open(os.path.abspath("color.csv"), "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        rgbData[row["color"].lower()] = (int(row["r"]), int(row["g"]), int(row["b"]))
                        if row["color"].lower() == args[0].lower():
                            r = int(row["r"])
                            g = int(row["g"])
                            b = int(row["b"])
                            return (r, g, b)
                error(f"Color '{colored(args[0], rgb('red'))}' not found in color.csv")
            except FileNotFoundError:
                error("color.csv file not found")
        
        return rgbData[args[0].lower()]
    else:
        error("RGB values must be in the range 0-255 or invalid color format")

class Mod:
    def __init__(self, link):
        self.link = link
        self.name_zip = os.path.basename(link)
        self.name = self.name_zip
        with open(os.path.abspath(os.path.join("data.json")), "r", encoding="utf-8") as f:
            data = json.load(f)
            for mod_name, mod_zip in data.get("mods", {}).items():
                if mod_zip == self.name_zip:
                    self.name = mod_name
                    break
class Config:
    def __init__(self, link, defaultKeys = ""):
        self.link = link
        self.mods = []
        
        data_path = os.path.join(self.link, "data.json")
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.name = data.get("name", "")
                self.authKey = data.get("authKey", "")
                if (self.authKey == ""):
                    self.authKey = defaultKeys
                self.error = None
                self.ip = data.get("ip", "")
                self.port = data.get("port", "")
                self.maxPlayer = data.get("maxPlayers", "")
                self.map = data.get("map", "")
                self.maxVehicles = data.get("maxVehicles", "")
                self.allowGuest = data.get("allowGuest", "")
                self.logChat = data.get("logChat", "")
                self.debug = data.get("debug", "")
                self.informationPacket = data.get("informationPacket", "")
                self.tags = data.get("tags", [])
                self.description = data.get("description", "")
                self.resourceFolder = os.path.abspath(data.get("resourceFolder", "")).replace("\\", "/")
                self.modsFolder = data.get("modsFolder", "")
                self.enableMod = data.get("enableMod", "")
                self.ImScaredOfUpdates = data.get("ImScaredOfUpdates", "")
                self.UpdateReminderTime = data.get("UpdateReminderTime", "")
                self.private = data.get("private", False)
                '''
                "name": "BeamMP Server",
                "ip" : "::",
                "port" : 30814,
                "maxPlayers" : 8,
                "maxVehicles" : 1,
                "allowGuest" : true,
                "logChat" : true,
                "debug" : false,
                "informationPacket" : true,
                "tags" : ["BeamMP", "Multiplayer"],
                "map" : "/levels/gridmap_v2/info.json",
                "description" : "BeamMp Server",
                "resourceFolder" : "Resources",
                "modsFolder" : "mods",
                "enableMod" : false,
                "ImScaredOfUpdates" : true,
                "UpdateReminderTime" : "30s",
                "authKey" : ""
                '''
        else:
            data = {}
            error("data.json file not found in " + colored(data_path, rgb("lightcyan")) + ", using default values")
    
    def reloadMods(self):
        """Recharge la liste des mods à partir du dossier mods de la configuration.
        """
        self.mods = []
        for folder in os.listdir(os.path.join(self.link, "Resources\\Client")):
            doc_path = os.path.join(self.link, "Resources\\Client", folder)
            if os.path.isfile(doc_path):
                self.mods.append(Mod(doc_path))

    def updateData(self, data, value):
        """Met à jour une valeur spécifique dans la configuration.

        Args:
            data (str): Clé de la donnée à mettre à jour
            value: Nouvelle valeur à assigner
        """
        if hasattr(self, data):
            if type(getattr(self, data)) == type(value):
                setattr(self, data, value)
            else:
                warn(f"Type mismatch for '{colored(data, rgb('yellow'), attrs=['bold'])}': expected {colored(type(getattr(self, data)).__name__, rgb('green'))}, got {colored(type(value).__name__, rgb('red'))}, updating value anyway")
                value = type(getattr(self, data))(value)
                setattr(self, data, value)
            self.saveData()
            self.setTOML()
            info(f"{colored(data, rgb('yellow'), attrs=['bold'])} updated to {colored(value, rgb('lightgreen'))} in configuration '{colored(str(self), rgb('lightcyan'))}'")
        else:
            error(f"Data '{colored(data, rgb('yellow'), attrs=['bold'])}' not found in configuration")
            info("Available data:")
            for attr in vars(self):
                print(f"  - {colored(attr, rgb('yellow'))} type:{colored(type(getattr(self, attr)).__name__, rgb('green'))}")

    def saveData(self):
        """Enregistre les données actuelles de la configuration dans le fichier data.json.
        """
        data = {
            "name": self.name,
            "ip" : self.ip,
            "port" : self.port,
            "maxPlayers" : self.maxPlayer,
            "maxVehicles" : self.maxVehicles,
            "allowGuest" : self.allowGuest,
            "logChat" : self.logChat,
            "debug" : self.debug,
            "informationPacket" : self.informationPacket,
            "tags" : self.tags,
            "map" : self.map,
            "description" : self.description,
            "resourceFolder" : self.resourceFolder,
            "modsFolder" : self.modsFolder,
            "enableMod" : self.enableMod,
            "ImScaredOfUpdates" : self.ImScaredOfUpdates,
            "UpdateReminderTime" : self.UpdateReminderTime,
            "authKey" : self.authKey,
            "private" : self.private
        }
        with open(os.path.join(self.link, "data.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


    def printConfig(self):
        print(f'Configuration: "{colored(self.link, rgb("lightcyan"))}",')
        print(f'Name: {colored('"' + self.name + '"', rgb("lightgreen"))},')
        print(f'IP: {colored(self.ip, rgb("yellow"))},')
        print(f'Port: {colored(self.port, rgb("lightred"))},')
        print(f'AuthKey: {colored('"' + self.authKey + '"', rgb("lightgreen"))},')
        print(f'Max Players: {colored(self.maxPlayer, rgb("lightred"))},')
        print(f'Max Vehicles: {colored(self.maxVehicles, rgb("lightred"))},')
        print(f'Allow Guest: {colored(self.allowGuest, rgb("blue"))},')
        print(f'Log Chat: {colored(self.logChat, rgb("blue"))},')
        print(f'Debug: {colored(self.debug, rgb("blue"))},')
        print(f'Information Packet: {colored(self.informationPacket, rgb("blue"))},')

        print("Tags: ", end="")
        for tag in self.tags:
            print(colored('"' + tag + '"', rgb("lightgreen")), end=", ")
        print()

        print(f'Map: {colored('"' + self.map + '"', rgb("lightgreen"))},')
        print(f"Description: {colored('"' + self.description + '"', rgb("lightgreen"))},")
        print(f"Resource Folder: {colored('"' + self.resourceFolder + '"', rgb("lightgreen"))},")
        print(f"Mods Folder: {colored('"' + self.modsFolder + '"', rgb("lightgreen"))},")
        print(f"Enable Mod: {colored(self.enableMod, rgb("blue"))},")
        print(f"I'm Scared Of Updates: {colored(self.ImScaredOfUpdates, rgb("blue"))},")
        print(f"Update Reminder Time: {colored('"' + self.UpdateReminderTime + '"', rgb("lightgreen"))}")
        print(f"Private: {colored(self.private, rgb("blue"))}")

    def __str__(self):
        return self.link
    
    def setTOML(self):
        """Génère une configuration TOML à partir des données de la configuration.
        """
        with open(os.path.join(self.link, "ServerConfig.toml"), "w", encoding="utf-8") as f:
            f.write("# This is the BeamMP-Server config file.\n")
            f.write("# Help & Documentation: `https://docs.beammp.com/server/server-maintenance/`\n")
            f.write("# IMPORTANT: Fill in the AuthKey with the key you got from `https://keymaster.beammp.com/` on the left under \"Keys\"\n")
            f.write("[General]\n")
            f.write(f"Port = {self.port}\n")
            f.write("# AuthKey has to be filled out in order to run the server\n")
            f.write(f"AuthKey = \"{self.authKey}\"\n")
            f.write("# Whether to allow guests\n")
            f.write(f"AllowGuests = {str(self.allowGuest).lower()}\n")
            f.write("# Whether to log chat messages in the console / log\n")
            f.write(f"LogChat = {str(self.logChat).lower()}\n")
            f.write(f"Debug = {str(self.debug).lower()}\n")
            f.write("# The IP address to bind the server to, this is NOT related to your public IP. Can be used if your machine has multiple network interfaces\n")
            f.write(f"IP = \"{self.ip}\"\n")
            f.write(f"Private = {str(self.private).lower()}\n")
            f.write("# Whether to allow unconnected clients to get the public server information without joining\n")
            f.write(f"InformationPacket = {str(self.informationPacket).lower()}\n")
            f.write(f"Name = \"{self.name}\"\n")
            f.write("# Add custom identifying tags to your server to make it easier to find. Format should be TagA,TagB,TagC. Note the comma seperation.\n")
            f.write(f"Tags = \"{','.join(self.tags)}\"\n")
            f.write(f"MaxCars = {self.maxVehicles}\n")
            f.write(f"MaxPlayers = {self.maxPlayer}\n")
            f.write(f"Map = \"{self.map}\"\n")
            f.write(f"Description = \"{self.description}\"\n")
            f.write(f"ResourceFolder = \"{self.resourceFolder}\"\n")

            f.write("[Misc]\n")
            f.write("# Hides the periodic update message which notifies you of a new server version. You should really keep this on and always update as soon as possible. For more information visit https://wiki.beammp.com/en/home/server-maintenance#updating-the-server. An update message will always appear at startup regardless.\n")
            f.write(f"ImScaredOfUpdates = {str(self.ImScaredOfUpdates).lower()}\n")
            f.write("# Specifies the time between update reminders. You can use any of \"s, min, h, d\" at the end to specify the units seconds, minutes, hours or days. So 30d or 0.5min will print the update message every 30 days or half a minute.\n")
            f.write(f"UpdateReminderTime = \"{self.UpdateReminderTime}\"\n")
    
    def deleteConfig(self):
        """Supprime la configuration actuelle en supprimant le dossier de la configuration.
        """
        try:
            shutil.rmtree(self.link)
            if str(self) in self.GeneralData.get("lastServeurConfig", ""):
                self.GeneralData["lastServeurConfig"] = ""
                with open("data.json", "w", encoding="utf-8") as f:
                    json.dump(self.GeneralData, f, indent=4)
            info(f"Configuration '{colored(str(self), rgb('lightcyan'))}' deleted successfully")
        except Exception as e:
            error(f"Error occurred while deleting configuration '{colored(str(self), rgb('lightcyan'))}': {e}")
    
    def start(self):
        print(f"Starting server with configuration:")
        self.printConfig()
        if not(os.path.exists(os.path.abspath(os.path.join(self.link, "ServerConfig.toml")))):
            self.setTOML()
            self.error = f"self.link: {self.link}, ServerConfig.toml not found, generating configuration file..."
        shutil.copy(os.path.abspath(os.path.join(self.link, "ServerConfig.toml")), os.path.abspath("../ServerConfig.toml")) # Déplace le fichier de configuration généré à la racine du projet
        
        info("Starting server...")
        resultat = subprocess.run(["Luncher/BeamMP-Server.exe", "--config=" + "ServerConfig.toml", "--working-directory=" + os.path.abspath(os.path.join(self.link))], stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True) #, capture_output=True
        # info(f"Result of server execution: {resultat}")
        print(resultat.stdout)
        shutil.copy(os.path.abspath("server.log"), os.path.abspath(os.path.join(self.link, "log", datetime.now().strftime("%d-%m-%Y %H-%M-%S") + ".log"))) 
        print("Server stopped, log saved to " + colored(os.path.join(self.link, "log"), rgb("lightcyan")) + ",\n", colored("PLEASE LEAVE PANEL", "red", attrs=["bold"]))


class Server:
    def __init__(self):
        init()
        just_fix_windows_console()

        # list des configurations disponibles
        self.config = {}
        self.mods = []
        config_path = "Config"
        if os.path.exists(config_path):
            for folder in os.listdir(config_path):
                folder_path = os.path.join(config_path, folder)
                if os.path.isdir(folder_path):
                    self.config[folder] = Config(folder_path)

        if os.path.exists("data.json"):
            with open("data.json", "r", encoding="utf-8") as f:
                self.GeneralData = json.load(f)
        else:
            self.GeneralData = {}

        # Server console start
        
        self.execute("clear")
        print(colored("Welcome to the BeamMP Server Launcher!", "cyan", attrs=["bold"]))

        # Charge la dernière configuration utilisée

        lastConfig = self.GeneralData.get("lastServeurConfig", "")
        if lastConfig in self.config:
            self.config = self.config[lastConfig]
            info(f"Last configuration '{colored(str(self.config), rgb('lightcyan'))}' loaded successfully")
        else:
            self.config = self.config.get("default", None)
            warn("No last configuration found, configuration default used")

        # Initialize server console loop
        while True:
            try:
                self.execute(input(getDataCommand() + " > "))
            except KeyboardInterrupt:
                print("\nInterrupted by user")
                break
            except Exception as e:
                error(f"An error occurred: {e}")

    def reloadMods(self):
        """Recharge la liste des mods à partir du dossier mods de la configuration.
        """
        self.mods = []
        for folder in os.listdir(os.path.join("mods")):
            doc_path = os.path.join("mods", folder)
            if os.path.isfile(doc_path):
                self.mods.append(Mod(doc_path))
    
    def Config(self, cmd, data):
        if cmd == "list":
            print("Liste des configurations disponibles:")
            for key in self.config.keys():
                print("  - " + colored(key, rgb("lightyellow")))
        elif cmd == "load":
            if (len(data) == 0):
                print("Usage: config load [config_name]")
            else:
                self.config = self.loadConfig(os.path.join("Config", data[0]))
                print(f"Configuration '{str(self.config)}' chargée avec succès")
        elif cmd == "regenerateTOML":
            if type(self.config) == Config:
                self.config.setTOML()
                print(f"Configuration TOML régénérée pour '{str(self.config)}'")
            else:
                error("No configuration loaded")
        elif cmd == "start":
            if type(self.config) == Config:
                self.config.start()
            else:
                error("No configuration loaded")
        elif cmd == "print":
            if type(self.config) == Config:
                self.config.printConfig()
            else:
                error("No configuration loaded")
        elif cmd == "log":
            if type(self.config) == Config:
                self.getlog()
            else:
                error("No configuration loaded")
        elif cmd == "update":
            if type(self.config) == Config:
                if len(data) >= 2:
                    self.config.updateData(data[0], data[1])
                else:
                    warn("Usage: config update [data] [value]")
            else:
                error("No configuration loaded")
        elif cmd == "save":
            if type(self.config) == Config:
                self.config.saveData()
                info(f"Configuration '{colored(str(self.config), rgb('lightcyan'))}' saved successfully")
            else:
                error("No configuration loaded")
        elif cmd == "delete":
            if type(self.config) == Config:
                self.config.deleteConfig()
                self.config = self.loadConfig(os.path.join("Config", "default"))
            else:
                error("No configuration loaded")
        else:
            error("Unknown config command: " + colored(cmd, rgb("purple")))

    def createConfig(self, name):
        """Crée une nouvelle configuration avec le nom spécifié.

        Args:
            name (str): Nom de la nouvelle configuration
        """
        config_path = os.path.join("Config", name)
        if not os.path.exists(config_path):
            try:
                shutil.copytree(os.path.join("Config", "default"), config_path)
                self.loadConfig(config_path)
                self.config.name = name
                self.config.link = config_path
                self.config.saveData()
                self.GeneralData["lastServeurConfig"] = name
                with open("data.json", "w", encoding="utf-8") as f:
                    json.dump(self.GeneralData, f, indent=4)
                self.config.setTOML()
                shutil.rmtree(os.path.join(config_path, "log"))
                os.mkdir(os.path.join(config_path, "log"))
            except Exception as e:
                error(f"Error occurred while creating configuration '{colored(name, rgb('lightcyan'))}': {e}")
            info(f"Configuration '{colored(name, rgb('lightcyan'))}' created successfully (copy default configuration)")
        else:
            error(f"Configuration '{colored(name, rgb('lightcyan'))}' already exists")


    def getlog(self, date = None):
        if date is None:
            listlog = []
            if os.path.exists(os.path.join(self.config.link, "log")):
                for folder in os.listdir(os.path.join(self.config.link, "log")):
                    folder_path = os.path.join(self.config.link, "log", folder)
                    if os.path.isfile(folder_path):
                        listlog.append(f"[{colored(os.path.basename(folder_path)[:-4], rgb('lightyellow'))}]")
            print(f"List of logs for configuration '{colored(str(self.config), rgb('lightcyan'), attrs=['bold'])}':")
            for date in listlog:
                print(date)
        else:
            try:
                print(f"=== Log for configuration '{colored(str(self.config), rgb('lightcyan'), attrs=['bold'])}' on date '{colored(date, rgb('lightcyan'))}' ===")
                with open(os.path.join(self.config.link, "log", date + ".log"), "r", encoding="utf-8") as f:
                    log = f.read()
                    print(log)
            except FileNotFoundError:
                error("Log file not found")

    def loadConfig(self, path):
        """Charge une configuration à partir d'un chemin spécifié.

        Args:
            path (str): Chemin vers la configuration à charger

        Returns:
            Config: Instance de la classe Config avec les données chargées
        """
        if os.path.exists(path):
            return Config(path, defaultKeys=self.GeneralData.get("defaultAuthKey", ""))
        else:
            error("Configuration file "+ colored('"' + path + '"', "cyan") +" not found")

    

    def display_help(self):
        """Affiche la liste des commandes disponibles sous forme de tableau.

        Lit le fichier command.csv et affiche un tableau formaté avec tabulate.
        Gère les erreurs de fichier et affiche des messages appropriés.
        """
        try:
            print(colored("Available commands:", "cyan"))
            with open("command.csv", "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                commands = list(reader)
                if len(commands) > 0:
                    headers = commands[0]
                    rows = commands[1:]
                    print(tabulate(rows, headers=headers, tablefmt="grid"))
                    print(f"For more information on a specific command, use {colored('command_name', rgb('yellow'))} -help")
                else:
                    print("Aucune commande disponible")
        except FileNotFoundError:
            print("Fichier command.csv introuvable")
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier: {e}")

    def test_command(self, command, data):
        """Affiche les informations de débogage pour une commande.

        Args:
            command (str): Nom de la commande
            data (list): Liste des arguments passés à la commande
        """
        print(colored("\n=== TEST COMMAND ===", "magenta"))
        print(colored(f"Commande: ", "cyan") + colored(f"{command}", "green"))
        if len(data) > 0:
            print(colored(f"Nombre d'options: ", "cyan") + colored(f"{len(data)}", "yellow"))
            print(colored("Options:", "cyan"))
            for i, option in enumerate(data, 1):
                print(f"  [{i}] {colored(option, 'white')}")
        else:
            print(colored("Aucune option fournie", "yellow"))
        print(colored("===================\n", "magenta"))
        print(os.path.join("Config", "default", "ServerConfig.toml"))

    def color_text(self, text="", color = "white"):
        """Colorie le texte avec la couleur spécifiée.

        Args:
            text (str): Texte à colorier
            color (tuple): Tuple RGB (r, g, b) pour la couleur

        Returns:
            str: Texte coloré
        """
        return colored(text, color)

    def execute(self, cmd):
        """Traite et exécute une commande utilisateur.

        Parse la commande avec shlex.split(), identifie la commande et exécute
        la fonction appropriée avec les arguments fournis.

        Args:
            cmd (str): Commande complète saisie par l'utilisateur
        """
        cmd = shlex.split(cmd)
        command = cmd[0]
        data = cmd[1:]
        if command == "clear":
            if len(data) > 0 and data[0] == "-help":
                print(f"Clear the console")
                print(f"Usage: clear")
            else:
                print("\033c", end="")
        elif command == "help":
            if len(data) > 0 and data[0] == "-help":
                print(f"Affiche la liste des commandes disponibles")
                print(f"Usage: help")
            else:
                self.display_help()
        elif command == "test":
            if len(data) > 0 and data[0] == "-help":
                print(f"Affiche les informations de débogage pour une commande")
                print(f"Usage: test [{colored('command', 'yellow')}] [{colored('options', rgb('purple'))}] [{colored('...', rgb('purple'))}]")
            else:
                self.test_command(command, data)
        elif command == "colorText":
            if len(data) > 0 and data[0] == "-help":
                print(f"Affiche un message coloré dans la console")
                print(f"Usage: colorText [{colored('message', 'yellow')}] [{colored('color', 'purple')}]")
            if len(data) >= 2:
                color = data[-1]
                text = " ".join(data[:-1])
                try:
                    rgb_color = rgb(color)
                    colored_text = self.color_text(text, rgb_color)
                    print(colored_text)
                except ValueError as e:
                    print(e)
            else:
                warn(f"Bad request for {colored('colorText', rgb('lightblue'))} command !")
                self.execute("colorText -help")
        elif command == "print":
            if len(data) > 0 and data[0] == "-help":
                print(f"Affiche un message dans la console")
                print(f"Usage: print [message]")
            if len(data) > 0:
                print(" ".join(data))
            else:
                warn(f"Bad request for {colored('print', rgb('lightblue'))} command !")
                self.execute("print -help")
        elif command == "Hello_World":
            if len(data) > 0 and data[0] == "-help":
                print(f"Affiche le message 'Hello World!'")
                print(f"Usage: Hello_World")
            else:
                print("Hello World!")
        elif command == "exit":
            if len(data) > 0 and data[0] == "-help":
                print(f"Quitte le programme")
                print(f"Usage: exit")
            else:
                exit()
        elif command == "date":
            if len(data) > 0 and data[0] == "-help":
                print(f"Affiche la date et l'heure actuelle")
                print(f"Usage: date")
            else:
                print(getDate(), getTime())
        elif command == "status":
            if (len(data) > 0 and data[0] == "-help"):
                print(f"Affiche les informations de statut du serveur")
                print(f"Usage: status")
            else:
                print(f"Server IP: {getIP()}")
                print(f"Current Date: {getDate()}")
                print(f"Current Time: {getTime()}")
        elif command == "log":
            if len(data) > 0 and data[0] == "-help":
                print(f"Manage logs for the current configuration")
                print(f"Usage: config log [{colored('date', rgb('purple'))}]")
                print(f"  > config log => List all available logs for the current configuration")
                print(f"  > config log [{colored('date', rgb('purple'))}] => Display the log for the specified date (format: DD-MM-YYYY HH-MM-SS)")
            else:
                if type(self.config) == Config:
                    if len(data) == 0:
                        self.getlog()
                    else:
                        self.getlog(data[0])
                else:
                    error("No configuration loaded")
                    warn(f"Bad request for {colored('log', rgb('lightblue'))} command !")
                    self.execute("log -help")
        elif command == "mods":
            self.reloadMods()
            conf = False
            if type(self.config) == Config:
                self.config.reloadMods()
                conf = True
            else:
                warn("No configuration loaded")
            if len(data) == 0:
                print(f"==== List of mods ====")
                if (conf):
                    print(f"If mod are included in configuration [{colored(str(self.config), rgb('lightcyan'))}], mods list is marked with '{colored('*', rgb('green'))}' ====")
                
                for mod in self.mods:
                    if conf and mod.name_zip in [m.name_zip for m in self.config.mods]:
                        print(f"  - {colored('*', rgb('green'))} [{colored(mod.name, rgb('yellow'), attrs=['bold'])}]")
                    else:
                        print(f"  -   [{colored(mod.name, rgb('yellow'), attrs=['bold'])}]")
            elif data[0] == "-help":
                print(f"Manage mods for the server configuration")
                print(f"Usage: mods [{colored('add', rgb('yellow'))}|{colored('remove', rgb('yellow'))}|{colored('rename', rgb('yellow'))}] [{colored('mod_name', rgb('purple'))}] [{colored('data', rgb('purple'))}]")
                print(f"When configuration is required, command are anoted with {colored('*', rgb('green'))}...")
                print(f"     > mods => List all available mods in 'mods' folder, if a configuration is loaded, mods included in the configuration are marked with '{colored('*', rgb('green'))}'")
                print(f"  {colored('*', rgb('green'))} > mods [{colored('add', rgb('yellow'))}] [{colored('mod_name', rgb('purple'))}] => Add a mod to the current configuration (mod file must be in 'mods' folder)")
                print(f"  {colored('*', rgb('green'))} > mods [{colored('remove', rgb('yellow'))}] [{colored('mod_name', rgb('purple'))}] => Remove a mod from the current configuration")
                print(f"  {colored('*', rgb('green'))} > mods [{colored('rename', rgb('yellow'))}] [{colored('old_name', rgb('purple'))}] [{colored('new_name', rgb('purple'))}] => Rename a mod in the current configuration (only for display, doesn't change the actual mod file name)")
            elif data[0] == "add" and len(data) == 2 and conf:
                try:
                    mod_name = data[1]
                    name_zip = self.GeneralData.get("mods", {}).get(mod_name, mod_name)
                    debug(f"mod_name: '{colored(mod_name, rgb('yellow'))}', name_zip: '{colored(name_zip, rgb('yellow'))}'")
                    debug(f"GeneralData mods: {json.dumps(self.GeneralData.get('mods', {}))}")
                    if name_zip in [m.name_zip for m in self.config.mods]:
                        warn(f"Mod '{colored(mod_name, rgb('yellow'))}' is already included in configuration '{colored(str(self.config), rgb('lightcyan'))}'")
                    else:
                        mod_path = os.path.join("mods", name_zip)
                        if os.path.exists(mod_path):
                            new_mod = Mod(name_zip)
                            self.config.mods.append(new_mod)
                            shutil.copy(mod_path, os.path.join(self.config.link, "Resources\\Client", name_zip))
                            info(f"Mod [{colored(mod_name, rgb('yellow'))}] added to configuration '{colored(str(self.config), rgb('lightcyan'))}' successfully")
                        else:
                            error(f"Mod file '{colored(mod_path, rgb('yellow'))}' not found")
                except Exception as e:
                    error(f"Error occurred while adding mod: {e}")
            elif data[0] == "remove" and len(data) == 2 and conf:
                try:
                    mod_name = data[1]
                    name_zip = self.GeneralData.get("mods", {}).get(mod_name, mod_name)
                    mod_to_remove = None
                    for mod in self.config.mods:
                        if mod.name == mod_name or mod.name_zip == mod_name:
                            mod_to_remove = mod
                            break
                    if mod_to_remove:
                        self.config.mods.remove(mod_to_remove)
                        os.remove(os.path.join(self.config.link, "Resources\\Client", name_zip))
                        info(f"Mod [{colored(mod_name, rgb('yellow'))}] removed from configuration '{colored(str(self.config), rgb('lightcyan'))}' successfully")
                    else:
                        warn(f"Mod [{colored(mod_name, rgb('yellow'))}] is not included in configuration '{colored(str(self.config), rgb('lightcyan'))}'")
                except Exception as e:
                    error(f"Error occurred while removing mod: {e}")
            elif ((data[0] == "rename") and (len(data) >= 3) and conf):
                print(f"Trying to rename mod '{colored(data[1], rgb('yellow'))}' to '{colored(data[2], rgb('yellow'))}' in configuration '{colored(str(self.config), rgb('lightcyan'))}'")
                try:
                    for mod in self.mods:
                        debug(f"Checking mod '{colored(mod.name, rgb('yellow'))}' (zip name: '{colored(mod.name_zip, rgb('yellow'))}') against '{colored(data[1], rgb('yellow'))}'")
                        if mod.name == data[1] or mod.name_zip == data[1]:
                            if "mods" not in self.GeneralData:
                                self.GeneralData["mods"] = {}
                            self.GeneralData["mods"][mod.name] = mod.name_zip
                            with open(os.path.abspath("data.json"), "w", encoding="utf-8") as f:
                                json.dump(self.GeneralData, f, indent=4)
                            mod.name = data[2]
                            info(f"Mod [{colored(data[1], rgb('yellow'))}] renamed to [{colored(data[2], rgb('yellow'))}] in configuration '{colored(str(self.config), rgb('lightcyan'))}' successfully")
                            break  # Sortir de la boucle après avoir trouvé et renommé
                except Exception as e:
                    error(f"Error occurred while renaming mod: {e}")
            else:
                warn(f"Bad request for {colored('mods', rgb('lightblue'))} command !")
                self.execute("mods -help")
            self.config.reloadMods()

        elif command == "debug":
            if len(data) > 0 and data[0] == "-help":
                print(f"Affiche un message en mode debug dans la console")
                print(f"Usage: debug [{colored('message', rgb('purple'))}]")
            elif len(data) == 0:
                warn(f"Bad request for {colored('debug', rgb('lightblue'))} command !")
                self.execute("debug -help")
            else:
                debug(" ".join(data))

        elif command == "info":
            if len(data) > 0 and data[0] == "-help":
                print(f"Affiche un message en mode info dans la console")
                print(f"Usage: info [{colored('message', rgb('purple'))}]")
            elif len(data) == 0:
                warn(f"Bad request for {colored('info', rgb('lightblue'))} command !")
                self.execute("info -help")
            else:
                info(" ".join(data))

        elif command == "warn":
            if len(data) > 0 and data[0] == "-help":
                print(f"Affiche un message en mode warn dans la console")
                print(f"Usage: warn [{colored('message', rgb('purple'))}]")
            elif len(data) == 0:
                warn(f"Bad request for {colored('warn', rgb('lightblue'))} command !")
                self.execute("warn -help")
            else:
                warn(" ".join(data))

        elif command == "error":
            if len(data) > 0 and data[0] == "-help":
                print(f"Affiche un message en mode error dans la console")
                print(f"Usage: error [{colored('message', rgb('purple'))}]")
            elif len(data) == 0:
                warn(f"Bad request for {colored('error', rgb('lightblue'))} command !")
                self.execute("error -help")
            else:
                error(" ".join(data))

        elif command == "config":
            if (len(data) == 0 or data[0] == "-help"):
                # Commande help
                print(f"Manage actual loaded configuration")
                print(f"Usage: config [{colored("delete", rgb("yellow"))}|{colored("list", rgb("yellow"))}|{colored("load", rgb("yellow"))}|{colored("log", rgb("yellow"))}|{colored("print", rgb("yellow"))}|{colored("regenerateTOML", rgb("yellow"))}|{colored("save", rgb("yellow"))}|{colored("start", rgb("yellow"))}|{colored("update", rgb("yellow"))}] [{colored("data", rgb("purple"))}]")
                print(f"When configuration is required, command are anoted with {colored("*", rgb("green"))}...")
                print(f"  {colored("*", rgb("green"))} > config [{colored("delete", rgb("yellow"))}] => Supprime la configuration actuelle")
                print(f"  {colored("*", rgb("green"))} > config [{colored("list", rgb("yellow"))}] => Liste les configurations disponibles")
                print(f"    > config [{colored("load", rgb("yellow"))}] [{colored("config_name", rgb("purple"))}] => Charge une configuration spécifique")
                print(f"  {colored("*", rgb("green"))} > config [{colored("log", rgb("yellow"))}] - [{colored("log", rgb("yellow"))}] [{colored("date", rgb("purple"))}] => Affiche le journal des événements")
                print(f"  {colored("*", rgb("green"))} > config [{colored("print", rgb("yellow"))}] => Affiche les détails d'une configuration")
                print(f"  {colored("*", rgb("green"))} > config [{colored("regenerateTOML", rgb("yellow"))}] => Recrée le fichier TOML d'une configuration")
                print(f"  {colored("*", rgb("green"))} > config [{colored("save", rgb("yellow"))}] => Enregistre la configuration actuelle")
                print(f"  {colored("*", rgb("green"))} > config [{colored("start", rgb("yellow"))}] => Démarre le serveur avec la configuration actuelle")
                print(f"  {colored("*", rgb("green"))} > config [{colored("update", rgb("yellow"))}] => Met à jour la configuration actuelle")
            else:
                self.Config(data[0], data[1:])
        elif command == "new":
            if (len(data) == 0 or data[0] == "-help"):
                # Commande help
                print(f"Create a new configuration and load it")
                print(f"Usage: new [{colored("config_name", rgb("purple"))}]")
            elif len(data) == 1:
                self.createConfig(data[0])
            else:
                warn(f"Bad request for {colored('new', rgb('lightblue'))} command !")
                self.execute("new -help")
        elif command == "doc":
            if (len(data) > 0 and data[0] == "-help"):
                # Commande help
                print(f"Open the documentation in the default web browser")
                print(f"Usage: doc")
            else:
                os.startfile("https://docs.beammp.com/server/server-maintenance/")
                resultat = subprocess.run(["../BeamMP-Server.exe", "--help"], stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True) #, capture_output=True
                # info(f"Result of server execution: {resultat}")
                print(resultat.stdout)

        else:
            error("Unknown command: " + colored(command, rgb("purple")))

server = Server()