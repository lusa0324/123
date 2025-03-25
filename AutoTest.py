from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

# 設定多開選項
edge_options = Options()
edge_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.127 Mobile Safari/537.36")
edge_options.add_argument("--window-size=390,844")

drivers = []  # 存放所有 WebDriver

# 讀取帳號列表
with open('accounts.csv', mode='r') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        account = row['account']
        print(f"帳號: {account}")

        driver = webdriver.Edge(service=Service("/Users/qa-1/Downloads/edgedriver_mac64_m1/msedgedriver"), options=edge_options)
        driver.get("https://www.client88.me/home/")
        driver.set_window_position(-1000, -1920)

        time.sleep(3)
        
        # 找到同意按鈕
        play_button = driver.find_element(By.CSS_SELECTOR, ".btn.btn-accept")  
        play_button.click()

        time.sleep(1)
        
        # 找到遊戲開始按鈕
        play_button = driver.find_element(By.CLASS_NAME, "btn-white")  
        play_button.click()

        time.sleep(1)

        # 找到password切換
        play_button = driver.find_element(By.XPATH, "//span[contains(text(), 'Password')]").click()

        time.sleep(1)

        # 輸入帳號
        phone_input = driver.find_element(By.XPATH, "(//input[@placeholder='Enter Phone Number'])[last()]")
        if phone_input.is_displayed():
            phone_input.send_keys(account)
            print(f"帳號: {account}")
        else:
            print("元素未顯示，可能需要滾動或等待")

        time.sleep(1)

        driver.find_element(By.XPATH, "//input[@placeholder='Enter Password']").send_keys("888888")

        time.sleep(1)

        # 同意書點擊
        btn = driver.find_element(By.XPATH, "//span[contains(@class, 'rmb-btn') and contains(@class, 'no-absolute')]")
        driver.execute_script("arguments[0].click();", btn)

        time.sleep(1)

        # 按登入
        # 等待並找到目標的 button 元素
        btn = WebDriverWait(driver, 10).until(
              EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'r-btn btn-big btn-color-2 no-margin-top')]"))
            )
        # 滾動到元素可見位置
        driver.execute_script("arguments[0].scrollIntoView();", btn)

        # 點擊按鈕
        btn.click()
        print(f"帳號 {account} 已登入")

        time.sleep(3)
    
        try:
            # 等待 close-btn 出現並可點擊
            close_button = WebDriverWait(driver, 10).until(
                           EC.element_to_be_clickable((By.CLASS_NAME, "close-btn"))
                           )
            # 點擊關閉按鈕
            close_button.click()
            print("已成功點擊 close-btn")

            time.sleep(1)
            # 等待 close-btn 出現並可點擊2
            close_button2 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "close-btn"))
                )
            # 點擊關閉按鈕
            close_button2.click()
            print("已成功點擊 close-btn")
            time.sleep(1)
        except Exception as e:
            # 如果 5 秒內找不到 close-btn，直接忽略並繼續執行
            print("未找到 close-btn，繼續執行其他操作")
    
        # 等待目標元素可點擊
        element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//li[contains(@style, 'background-image: url(\"https://cp-images.client88.me/images/cp/h5nav/1307-1/games.svg\")')]")))
        # 點擊元素
        element.click()

        time.sleep(3)

        liveSlots = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/div/ul/li[4]')))
        liveSlots.click()

        time.sleep(3)

        # 等待該元素可點擊
        element1 = WebDriverWait(driver, 10).until(
           EC.element_to_be_clickable((By.XPATH, "//div[@data-v-125568d0]"))
        )
    
        # 點擊元素
        element1.click()
        print("已進入OSM")

        time.sleep(5)

        # **1. 切換到 iframe**
        WebDriverWait(driver, 10).until(
          EC.frame_to_be_available_and_switch_to_it((By.ID, "iframe_id"))
        )
    
        # **2. 找到所有 `grid_gm_item`**
        items = WebDriverWait(driver, 10).until(
          EC.presence_of_all_elements_located((By.ID, "grid_gm_item"))
        )
    
        # **3. 遍歷並點擊 "873-JJBXGOLD-1001"**
        for item in items:
             if "873-JJBXGOLD-1001" in item.get_attribute("title"):
                   driver.execute_script("arguments[0].scrollIntoView();", item)  # 滾動到可視範圍
                   driver.execute_script("arguments[0].click();", item)  # 強制點擊
                   break  # 點擊後跳出迴圈

        time.sleep(3)

        join = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[2]/div/div[3]/div[2]/div[2]')))
        join.click()

        time.sleep(5)

        # 等待 "1.00" 出現
        WebDriverWait(driver, 10).until(
          EC.text_to_be_present_in_element((By.CLASS_NAME, "btn-text"), "1.00")
        )
    
        # 找到並點擊 "1.00"
        button = driver.find_element(By.XPATH, "//div[@class='btn-text' and text()='1.00']")
        button.click()
        time.sleep(1)

    
        # 等待它變成 "YES"
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, "btn-text"), "YES")
            )
    
        # 再次點擊 "YES"
        yes_button = driver.find_element(By.XPATH, "//div[@class='btn-text' and text()='YES']")
        yes_button.click()
        time.sleep(1)

        click_times = 10  

        for _ in range(click_times):
            try:
                # 等待按鈕可點擊
                spin_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='my-button my-button--normal btn_spin']"))
               )
                spin_button.click()
                print("按鈕已點擊")
                time.sleep(1.5)
            except Exception as e:
                print("發生錯誤:", e)
    
        time.sleep(10)

        buttons = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "header_btn_item"))
        )
        buttons[3].click()  # 這裡選擇第 3 個按鈕
        print("已點擊 header_btn_item")

        time.sleep(1)

        try:
            # 等待所有按鈕出現並可見
            quit_confirm = WebDriverWait(driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".van-button.box-btn.app_trickortreats"))
               )
            # 確保至少有 2 個按鈕
            if len(quit_confirm) > 1:
              quit_confirm[1].click()  # 點擊第二個按鈕
              print("已點擊第二個 van-button")
            else:
              print("沒有足夠的按鈕可點擊")

        except Exception as e:
           print("未找到按鈕，繼續執行其他操作")

        time.sleep(1)

        # 存入 WebDriver 陣列
        drivers.append(driver)

        time.sleep(10)
        driver.quit()
        print(f"帳號 {account} 已完成")
    
    