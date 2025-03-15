import os
import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

class InterfaceTest(unittest.TestCase):
    """InterfaceTest contains UI tests for the interface using Selenium.

    This test suite verifies that the interface correctly sends user messages and
    displays them on the page.
    """
    @classmethod
    def setUpClass(cls):
        """Set up the Selenium WebDriver for UI testing.
        
        This method initializes a headless Chrome WebDriver with appropriate options,
        opens the interface's index.html page, and sets up necessary resources.
        """
        options = Options()
        options.add_argument('--headless')
        # Initialize Chrome webdriver in headless mode.
        cls.log_file = open(os.devnull, 'w')
        service = Service(log_output=cls.log_file)
        cls.service = service
        cls.driver = webdriver.Chrome(service=service, options=options)
        cls.driver.implicitly_wait(5)
        # Construct the file URL for the interface's index.html.
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../src/interface')
        )
        file_path = 'file://' + os.path.join(base_path, 'index.html')
        cls.driver.get(file_path)
    
    @classmethod
    def tearDownClass(cls):
        """Tear down the Selenium WebDriver and cleanup resources.
        
        This method quits the WebDriver, stops the Chrome service, and closes the log file.
        """
        cls.driver.quit()
        cls.service.stop()
        cls.log_file.close()
    
    def test_send_message(self):
        """Test that a user message is sent and displayed correctly.
        
        This method simulates entering a message into the input field, clicking the send
        button, and then waiting for the message to appear in the messages container.
        """
        driver = self.driver
        # Locate the input field, send button, and messages container.
        user_input = driver.find_element(By.ID, 'user-input')
        send_button = driver.find_element(By.ID, 'send-button')
        messages = driver.find_element(By.ID, 'messages')
        
        # Enter a test message.
        test_message = "Hello world"
        user_input.send_keys(test_message)
        send_button.click()
        
        # Wait until the message from the user is rendered.
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element(
                (By.ID, 'messages'),
                f"User: {test_message}"
            )
        )
        
        # Verify that the sent message is displayed.
        messages_text = messages.text
        self.assertIn(f"User: {test_message}", messages_text)

if __name__ == '__main__':
    unittest.main()
