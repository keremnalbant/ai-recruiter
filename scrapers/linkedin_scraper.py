import logging
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config import settings
from storage.models import LinkedInProfile

logger = logging.getLogger(__name__)


class LinkedInScraper:
    def __init__(self):
        self.is_logged_in = False
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )

    async def login(self):
        if self.is_logged_in:
            return

        self.driver.get("https://www.linkedin.com/login")

        try:
            email_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_elem.send_keys(settings.LINKEDIN_EMAIL)

            password_elem = self.driver.find_element(By.ID, "password")
            password_elem.send_keys(settings.LINKEDIN_PASSWORD)

            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

            # Wait for login to complete
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )

            self.is_logged_in = True
            logger.info("Successfully logged in to LinkedIn")

        except TimeoutException as e:
            logger.error(f"Failed to login to LinkedIn: {str(e)}")
            raise

    async def find_profile(self, name: str) -> Optional[LinkedInProfile]:
        if not self.is_logged_in:
            await self.login()

        try:
            search_url = (
                f"https://www.linkedin.com/search/results/people/?keywords={name}"
            )
            self.driver.get(search_url)

            # Wait for search results
            results = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".reusable-search__result-container")
                )
            )

            if not results:
                return None

            # Click on first result
            results[0].click()

            # Wait for profile page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pv-top-card"))
            )

            profile_name = self._get_element_text(
                ".pv-top-card--list .text-heading-xlarge"
            )
            if not profile_name:
                return None

            return LinkedInProfile(
                profile_url=self.driver.current_url,
                name=profile_name,
                current_position=self._get_element_text(
                    ".pv-top-card--list .text-body-medium"
                ),
                company=self._get_element_text(".pv-top-card--experience-list-item"),
                location=self._get_element_text(".pv-top-card--list .text-body-small"),
            )

        except Exception as e:
            logger.error(f"Error finding LinkedIn profile for {name}: {str(e)}")
            return None

    def _get_element_text(self, selector: str) -> Optional[str]:
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except NoSuchElementException:
            return None

    def __del__(self):
        if hasattr(self, "driver"):
            self.driver.quit()

    async def get_profile_from_url(self, url: str) -> Optional[LinkedInProfile]:
        """Get LinkedIn profile directly from URL."""
        if not self.is_logged_in:
            await self.login()

        try:
            self.driver.get(url)

            # Wait for profile page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pv-top-card"))
            )

            profile_name = self._get_element_text(
                ".pv-top-card--list .text-heading-xlarge"
            )
            if not profile_name:
                return None

            return LinkedInProfile(
                profile_url=url,
                name=profile_name,
                current_position=self._get_element_text(
                    ".pv-top-card--list .text-body-medium"
                ),
                company=self._get_element_text(".pv-top-card--experience-list-item"),
                location=self._get_element_text(".pv-top-card--list .text-body-small"),
            )

        except Exception as e:
            logger.error(f"Error getting LinkedIn profile from URL {url}: {str(e)}")
            return None
