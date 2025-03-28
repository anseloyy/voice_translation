import os
import logging
import json
import subprocess
import tempfile
import time
import threading
from functools import wraps

logger = logging.getLogger(__name__)

def run_in_thread(func):
    """Decorator to run a function in a separate thread"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

def create_directory_if_not_exists(directory):
    """Create a directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def get_language_name(lang_code, config):
    """Get the human-readable language name from code"""
    return config.LANGUAGES.get(lang_code, lang_code)

def get_language_code(lang_name, config):
    """Get the language code from the human-readable name"""
    for code, name in config.LANGUAGES.items():
        if name.lower() == lang_name.lower():
            return code
    return lang_name  # Return as-is if not found

def save_audio_data(audio_data, file_format="wav"):
    """Save audio data to a temporary file"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_format}')
    temp_file.write(audio_data)
    temp_file.close()
    return temp_file.name

def read_file_safe(file_path, default_value=None):
    """Safely read a file, returning default_value if any error occurs"""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return default_value

def write_file_safe(file_path, content):
    """Safely write content to a file"""
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        return False

def json_load_safe(file_path, default_value=None):
    """Safely load JSON from a file, returning default_value if any error occurs"""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return default_value if default_value is not None else {}

def json_save_safe(file_path, data):
    """Safely save data as JSON to a file"""
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def is_process_running(process_name):
    """Check if a process is running by name"""
    try:
        subprocess.check_output(["pgrep", "-f", process_name])
        return True
    except subprocess.CalledProcessError:
        return False

def retry_with_backoff(func, max_retries=3, initial_backoff=1, backoff_multiplier=2):
    """Retry a function with exponential backoff"""
    retries = 0
    backoff = initial_backoff
    
    while retries < max_retries:
        try:
            return func()
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                raise e
            
            logger.warning(f"Retry {retries}/{max_retries} after error: {e}. Backing off for {backoff}s")
            time.sleep(backoff)
            backoff *= backoff_multiplier

class SimpleCache:
    """A simple in-memory cache with expiration"""
    def __init__(self, default_ttl=300):  # default 5 min TTL
        self.cache = {}
        self.expiry = {}
        self.default_ttl = default_ttl
    
    def get(self, key, default=None):
        """Get value for key if it exists and is not expired"""
        if key in self.cache:
            if self.expiry[key] > time.time():
                return self.cache[key]
            else:
                # Expired
                del self.cache[key]
                del self.expiry[key]
        return default
    
    def set(self, key, value, ttl=None):
        """Set value for key with optional TTL (in seconds)"""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = value
        self.expiry[key] = time.time() + ttl
    
    def delete(self, key):
        """Delete a key from the cache"""
        if key in self.cache:
            del self.cache[key]
            del self.expiry[key]
    
    def clear(self):
        """Clear all cache entries"""
        self.cache = {}
        self.expiry = {}
