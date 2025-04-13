from datetime import datetime, timedelta
import json
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

with open("camping_list.json", "r", encoding="utf-8") as file:
    camping_list = json.load(file)

with open("login.json", "r", encoding="utf-8") as file:
    login = json.load(file)

# Chemin vers EdgeDriver
edge_driver_path = login["path_to_driver"]

# Chemin vers l'extension edge "Captcha Buster"
extension_path = login["path_to_extension"]


# Configuration du driver
service = Service(edge_driver_path)
options = Options()
options.add_argument(f"--load-extension={extension_path}")
driver = webdriver.Edge(service=service, options=options)
driver.maximize_window()

base_url = "https://www.recreation.gov"
email = login["email"]
pswd = login["pswd"]
camping = camping_list[1]
login = True

def get_json_from_local_storage(driver, key):
    json_string = driver.execute_script(f"return window.localStorage.getItem('{key}');")
    return json.loads(json_string) if json_string else None

def set_json_in_local_storage(driver, key, data):
    json_string = json.dumps(data)
    driver.execute_script(f"window.localStorage.setItem('{key}', '{json_string}');")

def scroll_to(row):
    driver.execute_script("arguments[0].scrollIntoView({ block: \"center\"});", row)

for camping in camping_list:
    if camping.get("status") == "pending":
        end_url = ""
        url = base_url + "/camping/campgrounds/" + camping["id"]
        driver.get(url)

        try:
            # login
            print("login")
            if login:
                login_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'ga-global-nav-log-in-link')))
                login_button.click()
                email_input = driver.find_element(By.ID, 'email')
                email_input.send_keys(email)
                pswd_input = driver.find_element(By.ID, 'rec-acct-sign-in-password')
                pswd_input.send_keys(pswd)
                pswd_input.send_keys(Keys.RETURN)

            # filtre tente
            print("filtre tente")
            filter_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'legend-icon-dropdown')))

            filter_button.click()
            tent_filter_button = driver.find_element(By.CSS_SELECTOR, 'label[for="tent"]')
            scroll_to(tent_filter_button)
            tent_filter_button.click()
            filter_button.click()
            
            # filtre date
            print("filtre date")
            date_arrivee = datetime.strptime(camping['date_arrivee'], "%Y-%m-%d")
            date_depart = datetime.strptime(camping['date_depart'], "%Y-%m-%d")
            date_resa = datetime.strptime(camping['date_resa'], "%Y-%m-%dT%H:%M:%S")

            calendar_start = driver.find_element(By.CSS_SELECTOR, '.date-field.start')
            calendar_end = driver.find_element(By.CSS_SELECTOR, '.date-field.end')

            calendar_start_children = calendar_start.find_elements(By.XPATH, './*')
            calendar_end_children = calendar_end.find_elements(By.XPATH, './*')

            calendar_start_children[4].send_keys(date_arrivee.year)
            calendar_start_children[2].send_keys(date_arrivee.month)
            calendar_start_children[0].send_keys(date_arrivee.day)

            calendar_end_children[4].send_keys(date_depart.year)
            calendar_end_children[2].send_keys(date_depart.month)
            calendar_end_children[0].send_keys(date_depart.day)

            # refresh la page
            print("refresh")
            driver.refresh()

            # selectionne date
            print("date1")
            deltatime = date_depart - date_arrivee
            nb_nuit = deltatime.days
            print("nb_nuit: ", nb_nuit)
            nb_panier = 0
            WebDriverWait(driver, 5).until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(1)
            rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
            nb_favoris = len(camping["site_favoris"])
            print(camping["site_favoris"])
            if nb_favoris > 0:
                print(f"nb_favoris: {nb_favoris}")
                for row in rows:
                    if nb_panier < 4 and nb_panier < nb_favoris :
                        column = row.find_elements(By.XPATH, './*')
                        numero_site = column[0].text.strip()
                        if numero_site in camping["site_favoris"]:
                            is_new = True
                            if "available" == column[2].get_attribute("class"):
                                if is_new == True :
                                    nb_panier += 1
                                    is_new = False
                                first_date = column[2].find_element(By.TAG_NAME, 'button')
                                scroll_to(row)
                                first_date.click()
                                print(f"date1-favoris-{nb_panier}")

                            if "available" == column[2+1].get_attribute("class"):
                                if is_new == True :
                                    nb_panier += 1
                                    is_new = False
                                first_date = column[2+1].find_element(By.TAG_NAME, 'button')
                                scroll_to(row)
                                first_date.click()
                                print(f"date2-favoris-{nb_panier}")

            # for row in rows:
            #     if nb_panier < 4:
            #         column = row.find_elements(By.XPATH, './*')
            #         if "available" == column[2].get_attribute("class"):
            #             nb_panier += 1
            #             first_date = column[2].find_element(By.TAG_NAME, 'button')
            #             scroll_to(row)
            #             first_date.click()
            #             print(f"date1-{nb_panier}")

            # x = 0
            # if nb_nuit > 1 :
            #     print("date2")
            #     selected_lines = driver.find_elements(By.CLASS_NAME, "row-selected")
            #     for line in selected_lines:
            #         x += 1
            #         column2 = line.find_elements(By.XPATH, './*')
            #         last_date = column2[2+nb_nuit].find_element(By.TAG_NAME, 'button')
            #         scroll_to(line)
            #         last_date.click()
            #         print(f"date2-{x}")

            # ajouter au panier
            if login:
                print("Panier")
                panier = driver.find_element(By.CLASS_NAME, "availability-grid-book-now-button-tracker")

                # attendre 16h
                while True:
                    now = datetime.now()
                    print(f"{now.hour}:{now.minute:02}")
                    if now >= date_resa:
                        break

                panier.click()

            # fin, tous c'est bien passé !!!
            print("Page Title:", driver.title)

            # attendre 16h20
            while True:
                now = datetime.now()
                # print(f"{now.hour}:{now.minute:02}")
                if now >= date_resa + timedelta(minutes=20):
                        break
                
        except Exception as e:
            print(f"Erreur lors du chargement de la page pour {camping['nom']} ({camping['id']}) : {e}")

        break

driver.quit()