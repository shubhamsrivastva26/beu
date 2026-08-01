from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import threading
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global variables to keep Chrome alive permanently for MAXIMUM SPEED
driver = None
driver_lock = threading.Lock()

def get_driver():
    global driver
    if driver is None:
        print("Initializing Global Chrome Browser...")
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,1024")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Load a dummy page to initialize it
        driver.get("about:blank")
    return driver

@app.route('/')
def health_check():
    return "API is awake and running!"

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    reg_no = data.get('regNo')
    exam_choice = data.get('examChoice')
    
    if not reg_no or not exam_choice:
        return jsonify({"error": "Missing regNo or examChoice"}), 400
        
    url = ""
    if exam_choice == "1":
        url = "https://beu-bih.ac.in/result-two/B.Tech%201st%20Semester%20Examination%202025?d=eyJzZW1lc3RlciI6MSwic2Vzc2lvbiI6IjIwMjUiLCJleGFtX2hlbGQiOiJKYW51YXJ5LzIwMjYiLCJleGFtX2lkIjoiMjUwMTAxTiJ9"
    elif exam_choice == "2":
        url = "https://beu-bih.ac.in/result-two/B.Tech%202nd%20Semester%20Examination%202025?d=eyJzZW1lc3RlciI6Miwic2Vzc2lvbiI6IjIwMjUiLCJleGFtX2hlbGQiOiJKYW51YXJ5LzIwMjYiLCJleGFtX2lkIjoiMjUwMTAyTiJ9"
    elif exam_choice == "3":
        url = "https://beu-bih.ac.in/result-two/M.Tech%203rd%20Semester%20Examination%202025?d=eyJzZW1lc3RlciI6Mywic2Vzc2lvbiI6IjIwMjUiLCJleGFtX2hlbGQiOiJNYXkvMjAyNiIsImV4YW1faWQiOiIyNTA0MDMifQ%3D%3D"
    elif exam_choice == "4":
        url = "https://beu-bih.ac.in/result-two/M.Tech%201st%20Semester%20Examination%202025?d=eyJzZW1lc3RlciI6MSwic2Vzc2lvbiI6IjIwMjUiLCJleGFtX2hlbGQiOiJKYW51YXJ5LzIwMjYiLCJleGFtX2lkIjoiMjUwMTAxTiJ9"
    elif exam_choice == "5":
        url = "https://beu-bih.ac.in/result-two/M.Tech%202nd%20Semester%20Examination%202025?d=eyJzZW1lc3RlciI6Miwic2Vzc2lvbiI6IjIwMjUiLCJleGFtX2hlbGQiOiJKYW51YXJ5LzIwMjYiLCJleGFtX2lkIjoiMjUwMTAyTiJ9"
    else:
        url = "https://beu-bih.ac.in/result-one"

    # Use a lock so multiple users don't conflict on the same browser instance
    with driver_lock:
        try:
            d = get_driver()
            d.get(url)
            
            # Wait for elements to load
            time.sleep(2) 
            
            input_el = d.find_element(By.CSS_SELECTOR, "input[type=text], input[placeholder*='Registration']")
            
            # Clear field in case it was used previously
            input_el.clear()
            input_el.send_keys(reg_no)
            
            d.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", input_el)
            d.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", input_el)
            
            btn = d.find_element(By.CSS_SELECTOR, "button.btn-dark")
            d.execute_script("arguments[0].click();", btn)
            
            # Wait up to 15 seconds for the table to appear (Turnstile auto-solve window)
            table_found = False
            for _ in range(15):
                time.sleep(1)
                body_text = d.find_element(By.TAG_NAME, "body").text
                if "SGPA" in body_text:
                    table_found = True
                    break
                elif "not found" in body_text.lower() or "invalid" in body_text.lower():
                    # Clear out the page so it's fresh for next user
                    d.get("about:blank")
                    return jsonify({"error": "Result Not Found or Invalid Registration Number"})
            
            if not table_found:
                d.get("about:blank")
                return jsonify({"error": "Anti-Bot Protection Active. Could not bypass Cloudflare Turnstile automatically. Try again."})
                
            # Extract tables
            tables = d.find_elements(By.TAG_NAME, "table")
            resultData = {}
            
            for idx, table in enumerate(tables):
                rows = table.find_elements(By.TAG_NAME, "tr")
                tableData = []
                for row in rows:
                    cols = row.find_elements(By.CSS_SELECTOR, "th, td")
                    col_texts = [c.text.strip() for c in cols]
                    if any(col_texts):
                        tableData.append(col_texts)
                resultData[f"Table_{idx+1}"] = tableData
                
            # Reset page for the next person
            d.get("about:blank")
            
            return jsonify(resultData)
            
        except Exception as e:
            # If the driver crashed, kill it so it restarts next time
            global driver
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
            return jsonify({"error": "Scraping failed: " + str(e)})

if __name__ == '__main__':
    # Initialize the browser immediately on startup so the very first user has zero delay
    get_driver()
    app.run(host='0.0.0.0', port=5000)
