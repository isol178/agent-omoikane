import os
import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

class InterfaceTest(unittest.TestCase):
    """InterfaceTest contains UI tests for the interface using Selenium.

    This test suite verifies that the interface correctly sends user messages and
    displays them on the page.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the Selenium WebDriver for UI testing.
        
        Initializes a headless Chrome WebDriver with appropriate options, opens the
        interface's index.html page, and sets up necessary resources.
        """
        options = Options()
        options.add_argument('--headless')
        # Initialize Chrome WebDriver in headless mode.
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
    def tearDownClass(cls) -> None:
        """Tear down the Selenium WebDriver and cleanup resources.
        
        Quits the WebDriver, stops the Chrome service, and closes the log file.
        """
        cls.driver.quit()
        cls.service.stop()
        cls.log_file.close()
    
    def test_send_message_click(self) -> None:
        """Test sending a message via clicking the send button.
        
        Simulates entering a message into the input field, clicking the send button,
        and waits for the message to appear in the messages container.
        """
        driver = self.driver
        # Locate the input field, send button, and messages container.
        user_input = driver.find_element(By.ID, 'user-input')
        send_button = driver.find_element(By.ID, 'send-button')
        messages = driver.find_element(By.ID, 'messages')
        
        # Enter a test message.
        test_message = "Hello world"
        user_input.clear()
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

    def test_send_message_keyboard(self) -> None:
        """Test sending a message using the keyboard shortcut (Command + Enter).
        
        Simulates entering a message into the input field, triggering the send action
        via the key combination, and waits for the message to appear.
        """
        driver = self.driver
        user_input = driver.find_element(By.ID, 'user-input')
        messages = driver.find_element(By.ID, 'messages')
        
        # Enter a test message.
        test_message = "Keyboard test"
        user_input.clear()
        user_input.send_keys(test_message)
        # Simulate pressing Command (Meta) + Enter.
        user_input.send_keys(Keys.META, Keys.ENTER)
        
        # Wait until the message is rendered in the messages container.
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element(
                (By.ID, 'messages'),
                f"User: {test_message}"
            )
        )
        
        # Verify that the sent message is displayed.
        messages_text = messages.text
        self.assertIn(f"User: {test_message}", messages_text)

    def test_ai_response_is_non_empty(self) -> None:
        """Test that the AI response contains non-empty content.
        
        Sends a message and waits until an AI response appears in the messages container.
        Accepts either a valid AI response beginning with "AI:" or an error message.
        Then, extracts the AI response text and verifies that it contains content beyond the prefix.
        """
        driver = self.driver
        user_input = driver.find_element(By.ID, 'user-input')
        send_button = driver.find_element(By.ID, 'send-button')
        messages = driver.find_element(By.ID, 'messages')
        
        # Enter a test message.
        test_message = "Test AI response content"
        user_input.clear()
        user_input.send_keys(test_message)
        send_button.click()
        
        # Wait until an AI-related response is rendered.
        WebDriverWait(driver, 30).until(
            lambda d: ("AI:" in d.find_element(By.ID, "messages").text) or
                      ("Sorry, there was an error processing your request." in d.find_element(By.ID, "messages").text)
        )
        
        # Retrieve all messages and extract the AI response.
        messages_text = messages.text
        ai_lines = [line for line in messages_text.splitlines() if line.startswith("AI:")]
        self.assertTrue(len(ai_lines) > 0, "No AI response found in messages.")
        ai_response = ai_lines[-1][len("AI:"):].strip()
        self.assertTrue(len(ai_response) > 0, "AI response is empty.")

if __name__ == '__main__':
    unittest.main()
