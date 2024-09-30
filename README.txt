AI Voice Assistant Setup and Usage Instructions

1. Prerequisites:
   - Python 3.7 or higher installed
   - pip (Python package manager) installed

2. Installation:
   a. Update Python:
      - Download and install the latest version of Python from https://www.python.org/downloads/
      - Make sure to check "Add Python to PATH" during installation

   b. Upgrade pip and setuptools:
      pip install --upgrade pip setuptools wheel

   c. Install required libraries:
      pip install SpeechRecognition pyttsx3 pyautogui google-generativeai pygetwindow selenium PyAudio

   d. If PyAudio installation fails:
      Option 1: Try direct installation
      - Run: pip install pyaudio

      Option 2: Install using unofficial wheel for Python 3.12
      - Run the following commands:
        pip install --upgrade pip
        pip install --upgrade wheel
        pip install https://github.com/Azure-Samples/cognitive-services-speech-sdk/raw/master/samples/python/console/python-whl/pyaudio-0.2.11-cp312-cp312-win_amd64.whl

      Option 3: Build from source
      - Run: pip install pipwin
      - Run: pipwin install portaudio
      - Run: pip install pyaudio

   e. If PyAudio still doesn't work, the assistant will use text input instead of voice commands.

3. Gemini API Setup:
   - Sign up for the Gemini API at https://makersuite.google.com/app/apikey
   - Replace 'YOUR_GEMINI_API_KEY' in the code with your actual Gemini API key

4. Running the Assistant:
   - Open a terminal or command prompt
   - Navigate to the directory containing ai_voice_assistant.py
   - Run the script: python ai_voice_assistant.py

5. Using the Assistant:
   - The assistant will start listening for the wake word "hey assistant"
   - After saying the wake word, give your command when prompted
   - To exit, say "exit" or "quit" after the wake word or directly

6. Available Commands:
   a. Computer Control:
      - "Open [application name]"
      - "Close [application name]"
      - "Type [text]"
      - "Take a screenshot"

   b. Web Actions:
      - "Search for [query]"
      - "Go to [website]"
      - "Fill form on [website]" (basic implementation)

   c. File Management:
      - "Create folder [folder name]"
      - "Delete file [file name]"
      - "List files"

   d. System Settings:
      - "Volume up"
      - "Volume down"
      - "Mute"

7. Logging:
   - Logs are saved in ai_assistant.log in the same directory as the script
   - Check this file for detailed information about the assistant's actions and any errors

8. Customization:
   - You can modify the WAKE_WORD variable in the script to change the activation phrase
   - Add or modify functions to expand the assistant's capabilities

9. Troubleshooting:
   - If you encounter issues with speech recognition, ensure your microphone is properly connected and configured
   - For web action issues, make sure you have the correct version of ChromeDriver installed
   - Check the log file for detailed error messages if the assistant isn't working as expected

10. Security Note:
    - Be cautious when using commands that can modify your system or delete files
    - The assistant has access to your computer, so use it responsibly

11. Improvements and Contributions:
    - Feel free to expand on this implementation by adding more actions, improving natural language processing, or integrating with other services
    - If you make improvements, consider sharing them with the community!

Enjoy using your AI Voice Assistant!

Additional Installation Steps:

1. Install PyAudio:
   a. For Windows:
      - Go to https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
      - Download the appropriate wheel file for your Python version and system architecture
        (e.g., PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl for Python 3.9 on 64-bit Windows)
      - Open a command prompt in the directory where you downloaded the wheel file
      - Run: pip install PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl (replace with your downloaded filename)

   b. For macOS:
      - Run: brew install portaudio
      - Then run: pip install pyaudio

   c. For Linux:
      - Run: sudo apt-get install python3-pyaudio

2. After installing PyAudio, run the script again.