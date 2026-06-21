# -*- coding: utf-8 -*-
import os
import configparser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")

DEFAULT_DRIVE = "G:"
DEFAULT_ROOT_DIR = "GRV"
DEFAULT_SUB_DIR = "Wikki K"
DEFAULT_SERIES = "MetArtX Wikki K - Purple Dawn 1 - x177 - (26 Feb, 2026)"
DEFAULT_SIZE_LIMIT = 300
DEFAULT_ENABLE_MOVE = True
DEFAULT_RENAME_FORMAT = "{序号:03d}.jpg"

def load_config():
    cfg = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            cfg.read(CONFIG_FILE, encoding='utf-8')
            return {
                'drive': cfg.get('Paths', 'drive', fallback=DEFAULT_DRIVE),
                'root_dir': cfg.get('Paths', 'root_dir', fallback=DEFAULT_ROOT_DIR),
                'sub_dir': cfg.get('Paths', 'sub_dir', fallback=DEFAULT_SUB_DIR),
                'series': cfg.get('Paths', 'series', fallback=DEFAULT_SERIES),
                'size_limit': int(cfg.get('Settings', 'size_limit', fallback=str(DEFAULT_SIZE_LIMIT))),
                'enable_move': cfg.getboolean('Settings', 'enable_move', fallback=DEFAULT_ENABLE_MOVE),
                'rename_format': cfg.get('Settings', 'rename_format', fallback=DEFAULT_RENAME_FORMAT),
                'source_folders': cfg.get('Paths', 'source_folders', fallback='').split('|') if cfg.get('Paths', 'source_folders', fallback='') else []
            }
        except:
            pass
    return {
        'drive': DEFAULT_DRIVE,
        'root_dir': DEFAULT_ROOT_DIR,
        'sub_dir': DEFAULT_SUB_DIR,
        'series': DEFAULT_SERIES,
        'size_limit': DEFAULT_SIZE_LIMIT,
        'enable_move': DEFAULT_ENABLE_MOVE,
        'rename_format': DEFAULT_RENAME_FORMAT,
        'source_folders': []
    }

def save_config(data):
    cfg = configparser.ConfigParser()
    if not cfg.has_section('Paths'):
        cfg.add_section('Paths')
    cfg.set('Paths', 'drive', data.get('drive', DEFAULT_DRIVE))
    cfg.set('Paths', 'root_dir', data.get('root_dir', DEFAULT_ROOT_DIR))
    cfg.set('Paths', 'sub_dir', data.get('sub_dir', DEFAULT_SUB_DIR))
    cfg.set('Paths', 'series', data.get('series', DEFAULT_SERIES))
    cfg.set('Paths', 'source_folders', '|'.join(data.get('source_folders', [])))
    if not cfg.has_section('Settings'):
        cfg.add_section('Settings')
    cfg.set('Settings', 'size_limit', str(data.get('size_limit', DEFAULT_SIZE_LIMIT)))
    cfg.set('Settings', 'enable_move', str(data.get('enable_move', DEFAULT_ENABLE_MOVE)))
    cfg.set('Settings', 'rename_format', data.get('rename_format', DEFAULT_RENAME_FORMAT))
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            cfg.write(f)
    except:
        pass