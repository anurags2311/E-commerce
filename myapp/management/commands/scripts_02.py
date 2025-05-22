from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.core.management.base import BaseCommand
from myapp.models import Products, Category
import re
import time



class Command(BaseCommand):
    help = "Scrapes all men-socks from Brooks Brothers and saves to DB"

    def handle(self, *args, **options):
        driver = webdriver.Chrome()
        driver.get("https://brooksbrothers.in/collection/men-sport-shirts")
        wait = WebDriverWait(driver, 20)
        time.sleep(5)
        print("Page loaded")

        # Scroll down to ensure all products load (if needed)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Get all product cards
        product_cards = driver.find_elements(By.CLASS_NAME, "product-card")

        for index in range(len(product_cards)):
            try:
                # Refetch all product cards each time because DOM gets refreshed on back
                product_cards = driver.find_elements(By.CLASS_NAME, "product-card")
                                          
                product = product_cards[index]

                # Scroll to the element to avoid click interception
                driver.execute_script("arguments[0].scrollIntoView(true);", product)
                time.sleep(1)

                print(f"\n🔍 Clicking product #{index + 1}")

                product.click()
                time.sleep(2)
               
                try:
                    slick_track = driver.find_element(By.CLASS_NAME, "slick-track")
                    image_elements = slick_track.find_elements(By.TAG_NAME, "img")
                    print("🖼️ Image URLs:")
                    for img in image_elements:
                        print("  ➤", img.get_attribute("src"))
                except Exception as e:
                    print("❌ Error extracting images:", str(e))

                # Wait for the size dropdown to be present
                size_dropdown = wait.until(EC.presence_of_element_located((By.ID, "size-select")))

                # Get all the options
                options = size_dropdown.find_elements(By.TAG_NAME, "option")

                # Filter and print available sizes (excluding placeholders like "Select Size")
                available_sizes = [opt.text.strip() for opt in options if opt.get_attribute("value").strip() and "inactive" not in opt.get_attribute("class")]
                print("🧵 Available Sizes:", available_sizes)

                # Wait for the button containing the specific SVG path to be clickable


                button = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[.//path[@d='M18 15l-6-6-6 6h12z']]"
                )))
                button.click()
                time.sleep(2)
                print("✅ Button clicked.")





                driver.back()
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-container")))
                time.sleep(2)

            except Exception as e:
                print(f"⚠️ Error with product #{index + 1}: {str(e)}")
                driver.back()
                time.sleep(2)

        driver.quit()
        self.stdout.write(self.style.SUCCESS('✅ Finished scraping all product details!'))