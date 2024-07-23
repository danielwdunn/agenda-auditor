from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import datetime
import time

# Read config file and get variables
with open('config.json', 'r') as file:
    config = json.load(file)

url = config['site_to_scrape']['url']

# Function to take full-page screenshot
def take_fullpage_screenshot():
    # Chrome options to run in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off

    # Set up the webdriver
    driver = webdriver.Chrome(options=chrome_options)

    # Open webpage
    driver.get(url)

    # Wait for page to fully load
    time.sleep(10)  # Adjust this wait time according to page load time

    # Get current date and time for naming the screenshot
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_name = f"screenshot_{current_datetime}.png"

    #Combine variables to create directory name
    directory = current_date
    file_path = os.path.join(directory, screenshot_name)

    #Create directory if it does not exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Get page height
    body_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")

    # Ensure the entire page is captured by adjusting viewport height
    if body_height > viewport_height:
        total_sections = int(body_height / viewport_height) + 1
        for i in range(total_sections):
            driver.execute_script(f"window.scrollTo(0, {i * viewport_height})")
            time.sleep(2)  # Adjust sleep time if necessary
            driver.save_screenshot(f"{file_path[:-4]}_{i + 1}.png")
    else:
        driver.save_screenshot(file_path)

    # Close the webdriver
    driver.quit()


# Call the function to take full-page screenshot immediately when the script is run
if __name__ == "__main__":
    take_fullpage_screenshot()