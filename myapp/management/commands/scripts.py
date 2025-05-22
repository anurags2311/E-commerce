from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.core.management.base import BaseCommand
from myapp.models import Products, Category
import re
import time

class Command(BaseCommand):
    help = "Scrapes all men-scoks from Brooks Brothers and saves to DB"

    def handle(self, *args, **options):
        driver = webdriver.Chrome()
        driver.get("https://brooksbrothers.in/collection/men-socks")

        wait = WebDriverWait(driver, 20)

        # Scroll to load all products
        SCROLL_PAUSE_TIME = 2
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card")))
        product_cards = driver.find_elements(By.CLASS_NAME, "product-card")

        category_name = "Men-Socks" 
        category_obj, _ = Category.objects.get_or_create(name=category_name)

        for card in product_cards:
            try:
                name = card.find_element(By.CLASS_NAME, "product-name").text.strip()
                img_element = card.find_element(By.TAG_NAME, "img")
                image_url = img_element.get_attribute("src")

                price_text = card.find_element(By.CLASS_NAME, "discount-price").text.strip()
                price = re.sub(r'[^\d.]', '', price_text)

                Products.objects.create(
                    name=name,
                    description=name,
                    price=price,
                    image=image_url,
                    category=category_obj
                )
                self.stdout.write(self.style.SUCCESS(f"✔ Saved: {name}"))

            except Exception as e:
                self.stderr.write(f"⚠ Error on product: {e}")
                continue

        driver.quit()
        self.stdout.write(self.style.SUCCESS('✅ Finished scraping all products from Men - Polos and T-Shirts!'))
