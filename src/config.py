import configparser
import os

config = configparser.ConfigParser()

config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'settings.ini'))