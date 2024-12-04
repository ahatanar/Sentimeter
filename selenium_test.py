
# Selenium End-to-End Test Script

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Configure the WebDriver
driver = webdriver.Chrome()  # Make sure you have the ChromeDriver installed and added to PATH

# Frontend URL
url = "http://localhost:3000"  # Update with the actual frontend URL

# Test Steps
try:
    # Step 1: Navigate to the Frontend
    driver.get(url)
    time.sleep(2)

    # Step 2: Navigate to the Sign-In Page
    signin_link = driver.find_element(By.LINK_TEXT, "Sign In")
    signin_link.click()
    time.sleep(2)

    # Step 3: Log In
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    login_button = driver.find_element(By.ID, "login-btn")

    username_field.send_keys("test_user")  # Replace with a test username
    password_field.send_keys("test_password")  # Replace with a test password
    login_button.click()
    time.sleep(2)

    # Step 4: Navigate to the Journal Page
    journal_link = driver.find_element(By.LINK_TEXT, "Journal")
    journal_link.click()
    time.sleep(2)

    # Step 5: Create a New Journal Entry
    new_entry_button = driver.find_element(By.ID, "new-entry-btn")
    new_entry_button.click()
    time.sleep(2)

    title_field = driver.find_element(By.ID, "title")
    content_field = driver.find_element(By.ID, "content")
    save_button = driver.find_element(By.ID, "save-btn")

    title_field.send_keys("Test Journal Entry")
    content_field.send_keys("This is a test entry created by Selenium.")
    save_button.click()
    time.sleep(2)

    # Step 6: Verify Entry is Created
    entries = driver.find_elements(By.CLASS_NAME, "journal-entry")
    assert any("Test Journal Entry" in entry.text for entry in entries), "Journal entry not found!"

    print("End-to-end test passed successfully!")

finally:
    # Close the browser
    driver.quit()
