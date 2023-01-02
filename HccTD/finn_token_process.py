import datetime
import os.path

from selenium.webdriver.common.by import By
import time
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import yaml
from typing import Dict

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

work_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def get_finn_token_from_yaml(symbol:str) -> str:

    yaml_path = os.path.join(work_dir,"config","finn_token","finn_token.yaml")

    with open(yaml_path, "r") as f:
        token_set = yaml.safe_load(f)
        if token_set.get(symbol,None) is None:
            raise "token is None"

        print("update date: %s" % token_set.get("update",None))
        print(f"finnToken: {token_set.get(symbol,None)}")

        return token_set.get(symbol,None)


class Get_API_token():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    path = os.path.join("/usr/bin","chromedriver")
    s = Service(path)

    def __init__(self, email: str = None, pwd: str = None):
        self.__driver = webdriver.Chrome(service=self.s,options=Get_API_token.options)
    #     self.__driver = webdriver.Remote(
    #     command_executor='http://localhost:4444/wd/hub',
    #     options=webdriver.ChromeOptions()
    # )
        self.email = email
        self.pwd = pwd
        self.token = None

    def __get_delay(self):
        time.sleep(random.random() * random.randint(3, 6))

    def __get_redirect_dalay(self):
        time.sleep(random.randint(5, 8))

    def __next_dalay(self):
        time.sleep(random.randint(2, 7))

    def __login(self):
        self.__get_delay()
        self.__driver.get("https://finnhub.io/login")
        WebDriverWait(self.__driver, 5).until(
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[@id='root']/div[2]/div/div/div/form/input[1]")))
        self.__get_delay()
        self.__driver.find_element(By.XPATH, "//*[@id='root']/div[2]/div/div/div/form/input[1]").send_keys(self.email)
        self.__driver.find_element(By.XPATH, "//*[@id='root']/div[2]/div/div/div/form/input[2]").send_keys(self.pwd)
        self.__get_delay()
        self.__driver.find_element(By.XPATH, "//*[@id='root']/div[2]/div/div/div/a").click()

    def __get_token(self):
        self.__get_redirect_dalay()
        self.__driver.find_element(By.XPATH,"//*[@id='root']/div[2]/div/div/div[2]/div[1]/div/div[3]/a[2]").click() #修改token
        self.__get_delay()
        self.token = self.__driver.find_element(By.XPATH,
                                                "//*[@id='root']/div[2]/div/div/div[2]/div[1]/div/div[2]/input").get_attribute(
            "value")
        self.__get_delay()
        # self.__driver.close()

    def run(self):
        self.__login()
        self.__get_token()
        self.__next_dalay()

    def close(self):
        self.__driver.close()
        self.__driver.quit()



def save_to_yaml(token_set:Dict[str,str]):
    today = datetime.datetime.now().strftime("%Y%m%d")

    save_path = "config/finn_token/finn_token.yaml"
    save_path = os.path.join(work_dir,save_path)
    token_set["update"] = today

    if os.path.exists(save_path):
        os.rename(save_path,save_path + "_" + today)

    with open(save_path, "w") as yaml_f:
        yaml.dump(token_set,yaml_f)

    print(f"output to {save_path}")



def get_token_from_finnhub():

    with open(os.path.join(work_dir,"config","finn_token","finntokenConf.yaml"),"r") as f:
        data = yaml.safe_load(f)
        symbol_set = data.get("symbol_set",None)
        email_set = data.get("email_set",None)


    if not symbol_set or not email_set:
        raise "symbol_set or email_set not exits"
    elif len(symbol_set) != len(email_set):
        raise "wrong size for email set and symol set!"


    token_yaml = {}
    token_process = Get_API_token()
    for index, each_email_set in enumerate(email_set):
        print(f"Process {(index+1)}/{len(email_set)}...")
        token_process.email = each_email_set[0]
        token_process.pwd = each_email_set[1]
        token_process.run()
        token_yaml.update({symbol_set[index]: token_process.token})
    save_to_yaml(token_yaml)
    token_process.close()
    print("finish getting finn_token process...")



if __name__ == "__main__":


    get_token_from_finnhub()