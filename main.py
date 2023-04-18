from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select

import time
import datetime
import slack_sdk
import yaml
    
class SC():
    
    #####--- INIT ---#####
    
    def __init__(self):

        ##### cst #####         
        with open("config.yml", "r") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
            
        self.credentials = self.config['credentials']
        self.client = slack_sdk.WebClient(token=self.credentials['slack']['token'])
        #####     ######
        
        ### init + options of driver ###
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        self.driver = webdriver.Remote(command_executor=self.credentials['url'],options=options)

        ### get to the page ###
        self.driver.get("https://www.simcompanies.com/fr/")
        self.login()
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'test-exchange.css-1iai8pv.eofzx9a4')))
        
    def login(self):
        ##### cst ######
        driver = self.driver
        login = self.credentials['simcompanies']
        client= self.client
        slack_channel = self.credentials['slack']['channel']
        #####     ######
        
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-1k72xvm')))
            driver.find_element(By.CLASS_NAME, 'css-1k72xvm').click()
            driver.find_element(By.NAME, 'email').send_keys(login['email'])
            driver.find_element(By.NAME, 'password').send_keys(login['password'])
            driver.find_element(By.CLASS_NAME, 'text-right.mt5').click()
            client.chat_postMessage(channel=slack_channel, text="login successful")
            print('login successful')
        except:
            client.chat_postMessage(channel=slack_channel, text="already logged")
            print('already logged')
            pass
        
    #####--- $$$ ---#####
        
    def calculate(self,eth=1,security=3,boost=0.10):
        ##### cst ######
        driver = self.driver
        #####     ######
        
        if not hasattr(A, 'inventory'):
            self.fetch_inventory()
        inventory = self.inventory
            
        if hasattr(A,'eta') and (datetime.datetime.now() - self.eta).total_seconds() < 600 and hasattr(A,'calc'):
            D = {'ethanol' : [eth,0,0], 
                 'energy' : [0,self.calc['energy'][1],0], 
                 'transport' : [0,self.calc['transport'][1],0],
                 'sugarcane' : [0,0,0],
                 'water' : [0,0,0],
                 'seeds' : [0,0,0]
                }
        else:
            self.eta = datetime.datetime.now()
            D = {'ethanol' : [eth,0,0], 
                 'energy' : [0,self.fetch(63),0], 
                 'transport' : [0,self.fetch(103),0],
                 'sugarcane' : [0,0,0],
                 'water' : [0,0,0],
                 'seeds' : [0,0,0]
                }
        #####     ######
        
        ##### production #
          
        # ethanol production #
        if inventory['sugarcane'][0] <= security*D['ethanol'][0]*10:
            D['sugarcane'][0] = D['ethanol'][0]*10
        if inventory['energy'][0] <= security*D['ethanol'][0]*20:
            D['energy'][0] += D['ethanol'][0]*20
                
        # sugarcane production #
        if inventory['water'][0] <= 2*security*D['sugarcane'][0]*3:
            D['water'][0] = D['sugarcane'][0]*3
        if inventory['seeds'][0] <= security*D['sugarcane'][0]:
            D['seeds'][0] = D['sugarcane'][0]
        
        # water production #
        if inventory['energy'][0] <= security*D['water'][0]/5:
            D['energy'][0] += D['water'][0]/5 
            
        # transport buy #
        if inventory['transport'][0] <= security*eth:
            D['transport'][0] = eth

            
        ###### price calculation ######
        
        # water price #
        if D['water'][0] != 0:
            D['water'][1] = D['energy'][1]/5 + 0.2120
            D['water'][2] = D['water'][1]*D['water'][0]
            
        # seeds price #
        if D['seeds'][0] != 0:
            D['seeds'][1] = D['water'][1]/10 + 0.12
            D['seeds'][2] = D['seeds'][1]*D['seeds'][0]
            
        # sugarcane price #
        if D['sugarcane'][0] != 0:
            D['sugarcane'][1] = 3*D['water'][1] +  D['seeds'][1] + 0.16
            D['sugarcane'][2] =  D['sugarcane'][1]* D['sugarcane'][0]
        
        # ethanol price #
        if D['energy'][0] != 0:
            D['ethanol'][1] = D['energy'][1]*20 + D['sugarcane'][1]*10 + 4.1
            D['ethanol'][2] = D['ethanol'][1]*D['ethanol'][0]
        else:
            D['ethanol'][1] = D['sugarcane'][1]*10 + 4.1
            D['ethanol'][2] = D['ethanol'][1]*D['ethanol'][0]
                                                           
        # energy / transport price #
        D['energy'][2] = D['energy'][1]*D['energy'][0]
        if D['transport'][0] != 0:
            D['transport'][2] = D['transport'][0]*D['transport'][1]
        
        # boost #
        D['ethanol'][0] -= int(D['ethanol'][0]*boost)
        
        self.calc = D
        
    def make_ethanol(self,eth=1,boost=0.10):
        ##### cst ######
        driver = self.driver
        with open("config.yml", "r") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
            
        data = self.config['data']
        location = self.config['location']
        client = self.client
        slack_channel = self.credentials['slack']['channel']
        
        ethp = data['eth']
        self.wait_time = 0
        L = ['ethanol','sugarcane','seeds','water']
        #####     #####
        
        ##### init check #####
        
        self.checkifactive()
        if eth == 0 or self.wait_time != 0: 
            return
        
        if not hasattr(A, 'inventory'):
            self.fetch_inventory()
        inventory = self.inventory
        
        #####    ######
        
        self.calculate(eth)

        ##### buy energy & transport ######
        self.buy(63,int(self.calc['energy'][0]))
        client.chat_postMessage(channel=slack_channel, text=f"Bought {self.calc['energy'][0]} :energy: for {self.calc['energy'][1]} on market")
        self.buy(103,int(self.calc['transport'][0]))
        client.chat_postMessage(channel=slack_channel, text=f"Bought {self.calc['transport'][0]} :transport: for {self.calc['transport'][1]} on market")
        
        ##### make loop #####
        for k,v in data.items():
            if k in L:
                level = v['level']
                loc = v['location']
                total = sum(level)
                for i in range(len(loc)):
                    if k == 'ethanol':
                        self.make(location[loc[i]]+'.eofzx9a4',int(level[i]*ethp/total))
                    else: 
                        self.make(location[loc[i]]+'.eofzx9a4',int(level[i]*self.calc[k][0]/total))
                        
                if k != 'ethanol':
                    client.chat_postMessage(channel=slack_channel, text=f"Make {self.calc[k][0]} :{k}: for {self.calc[k][1]} each")
                else:
                    client.chat_postMessage(channel=slack_channel, text=f"Make {ethp} :ethanol: for {self.calc['ethanol'][1]} each")
        
        data['eth'] = self.calc['ethanol'][0]
        
        with open("config.yml", "w") as f:
            yaml.dump(
                self.config, stream=f, default_flow_style=False, sort_keys=False
            )
        
        
        client.chat_postMessage(channel=slack_channel, text="----------------------------------------------")
        
    #####--- FETCH/MAKE ---#####
    
    def fetch(self,N,small=False,level=0):
        ##### cst ######
        driver = self.driver
        #####     ######
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'menu-map'))).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'test-exchange.css-1iai8pv.eofzx9a4'))).click()
        try:
            driver.find_element(By.CLASS_NAME, 'fas.fa-sync').click()
        except:
            pass
        driver.execute_script("arguments[0].click();", driver.find_elements(By.CLASS_NAME, 'hover-effect.css-16vs401')[N])
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'quantity'))).clear()
        if small:
            driver.find_elements(By.NAME, 'quantity')[0].send_keys("5000")
            if N!= 103:
                Select(WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "quality")))).select_by_value(f'{level}')
            return int(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-15vd52a'))).text.replace("\u202f","")[1:])/5000
        else:
            driver.find_elements(By.NAME, 'quantity')[0].send_keys("1 000 000")
            if N!= 103:
                Select(WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "quality")))).select_by_value(f'{level}')
            return int(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-15vd52a'))).text.replace("\u202f","")[1:])/1000000
        
        
    
    def make(self,class_name,amount):
        ##### cst ######
        driver = self.driver
        #####     ###### 
        if amount == 0:
            return
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'menu-map'))).click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, class_name))).click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-6bdmpg.form-control'))).send_keys(amount)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-1fq0e5y.btn.btn-primary'))).click()
            time.sleep(2.5)
            self.waiting(class_name)
        except:
            self.waiting(class_name)
    
        
        
    def fetch_inventory(self):
        ##### cst ######
        driver = self.driver
        self.inventory = {'seeds' : [0,0,'SEMENCES'],
                          'sugarcane' : [0,1,'CANNE'],
                          'energy' : [0,2,'ÉNERGIE'],
                          'ethanol' : [0,3,'ÉTHANOL'],
                          'water' : [0,4,'EAU'],
                          'transport' : [0,5,'TRANSPORT'],
                         }
        #####     ######
        
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'menu-warehouse'))).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'e14va4ca4.css-psis2w')))
        l = len(driver.find_elements(By.CLASS_NAME, 'e14va4ca4.css-psis2w'))
        for i in list(self.inventory.keys()):
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'e14va4ca4.css-psis2w')))
            for j in range(l):
                b = driver.find_elements(By.CLASS_NAME, 'e14va4ca4.css-psis2w')[j].text.split('\n')
                if self.inventory[i][2] in b[0]:
                    self.inventory[i][0] = self.value_to_float(b[2].replace("\u202f",""))
                    self.inventory[i][1] = j
                    break
                self.inventory[i][1] = 'none'
        
        

        
    #####--- MIN/MAX ---#####
    
    def minmax(self,security=3,boost=0.10):
        ##### cst ######
        driver = self.driver
        
        self.get_money()
        money = int(self.money[1:])
        #####     ######
        y = 0
        self.calculate(y,security,boost)
        cost = self.calc['ethanol'][2] + self.calc['transport'][2]
        
        while money*0.95 >= cost: 
            y += 1
            self.calculate(y,security,boost)
            cost = self.calc['ethanol'][2] + self.calc['transport'][2]
            
        if cost > money*0.95:
            y -=1
            self.calculate(y,security,boost)
            cost = self.calc['ethanol'][2] + self.calc['transport'][2]

        print(money,money*0.95,cost, y)
        print(self.calc)
    
        
    
    #####--- MISC ---#####
        
    def get_bonus(self):
        ##### cst ######
        driver = self.driver
        #####     ######
        
        try:
            WebDriverWait(A.driver, 10).until(EC.presence_of_element_located((By.ID, 'menu-map'))).click()
            WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CLASS_NAME, 'anim-swipein.css-1uc9yyw'))).click()
            WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-1fq0e5y.btn.btn-primary'))).click()
        except:
            pass
        
    def get_money(self):
        ##### cst ######
        driver = self.driver
        #####     ######
        
        self.money = driver.find_element(By.CLASS_NAME, 'css-ncv1ml').text.replace("\u202f","")
        
    def checkifactive(self):
        ##### cst ######
        driver = self.driver
        data = self.config['data']
        L = ['ethanol','sugarcane','seeds','water']
        location = self.config['location']
        #####     ######
        
        for k,v in data.items():
            if k in L:
                level = v['level']
                loc = v['location']
                print(loc,level)
                for i in range(len(loc)):
                    self.waiting(location[loc[i]]+'.eofzx9a4')
        
    
    def checkifsell(self):
        ##### cst ######
        driver = self.driver
        #####     ######
        
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'menu-map'))).click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'test-exchange.css-1iai8pv.eofzx9a4'))).click()
            driver.execute_script("arguments[0].click();", driver.find_elements(By.CLASS_NAME, 'hover-effect.css-16vs401')[64])
            WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CLASS_NAME, 'svg-inline--fa.fa-xmark ')))
            return True
        except:
            pass
        return False
        
    
    def value_to_float(self,x):
        if type(x) == float or type(x) == int:
            return x
        if 'k' in x:
            if len(x) > 1:
                return float(x.replace('k', '').replace(',','.')) * 1000
            return 1000.0
        if 'm' in x:
            if len(x) > 1:
                return float(x.replace('m', '').replace(',','.')) * 1000000
            return 1000000.0
        else:
            return float(x)
        
    def waiting(self,class_name):
        ##### cst ######
        driver = self.driver
        #####     ######
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'menu-map'))).click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, class_name))).click()
            time = 60 + (datetime.datetime.strptime( WebDriverWait(A.driver, 1.5).until(EC.presence_of_element_located((By.CLASS_NAME, 'mt20'))).text[13:], '%d/%m/%Y %H:%M') - datetime.datetime.now() ).seconds
            time = time%86400
            if self.wait_time < time:   
                self.wait_time = time
            print(str(datetime.timedelta(seconds=time)))
        except:pass
    
    #####--- BUY / sell ---#####
                 
    def buy(self,N,amount=0):
        ##### cst ######
        driver = self.driver
        #####     ######
        if amount == 0:
            return
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'menu-map'))).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'test-exchange.css-1iai8pv.eofzx9a4'))).click()
        try:
            driver.find_element(By.CLASS_NAME, 'fas.fa-sync').click()
        except:
            pass
        driver.execute_script("arguments[0].click();", driver.find_elements(By.CLASS_NAME, 'hover-effect.css-16vs401')[N])
        driver.find_elements(By.NAME, 'quantity')[0].clear()
        driver.find_elements(By.NAME, 'quantity')[0].send_keys(amount)
        driver.find_element(By.CLASS_NAME, 'css-1oeybf6.btn.btn-primary').click()
    
    def sell(self,min_amount=100):
        ##### cst ######
        driver = self.driver
        client = self.client
        slack_channel = self.credentials['slack']['channel']

        self.fetch_inventory()
        price = self.fetch(64,True,level=self.config['data']['ethanol']['prod_level'])
        price = int(price) + (1+(price-int(price))//0.25)*0.25
        #####     ######
        
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'menu-warehouse'))).click()
        if self.inventory['ethanol'][0] >= min_amount:
            driver.find_elements(By.CLASS_NAME, 'e14va4ca4.css-psis2w')[self.inventory['ethanol'][1]].click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-h0kkmm.btn.btn-secondary')))
            driver.find_elements(By.CLASS_NAME, 'css-h0kkmm.btn.btn-secondary')[0].click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'price'))).send_keys(price)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-1fq0e5y.btn.btn-primary'))).click()
            client.chat_postMessage(channel=slack_channel, text=f"Sell {self.inventory['ethanol'][0]} :ethanol: for {price}")
            
            client.chat_postMessage(channel=slack_channel, text="----------------------------------------------")    
