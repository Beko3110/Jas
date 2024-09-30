import sys
import logging
import pyttsx3
import pyautogui
import webbrowser
import google.generativeai as genai
import os
import json
import subprocess
import pygetwindow as gw
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import speech_recognition as sr
import psutil
import shutil
import requests
import zipfile
import time
import platform
import socket
import speedtest
import cv2
import numpy as np
from PIL import Image
import pytesseract
import pywhatkit
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import threading
import queue
import win32gui
import win32com.client
import ctypes
import winreg
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
import win32api
import win32con
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import keyboard

# Configure logging
logging.basicConfig(filename='ai_assistant.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

try:
    import pyttsx3
    import pyautogui
    import webbrowser
    import google.generativeai as genai
    import os
    import json
    import subprocess
    import pygetwindow as gw
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import speech_recognition as sr
except ImportError as e:
    logging.error(f"Failed to import required module: {e}")
    print(f"Error: Failed to import required module: {e}")
    print("Please make sure all required packages are installed.")
    sys.exit(1)

# Configure Gemini API
genai.configure(api_key='')
model = genai.GenerativeModel('gemini-pro')

# Initialize text-to-speech
engine = pyttsx3.init()

# Print available voices
voices = engine.getProperty('voices')
for idx, voice in enumerate(voices):
    print(f"Voice {idx}:")
    print(f" - ID: {voice.id}")
    print(f" - Name: {voice.name}")
    print(f" - Languages: {voice.languages}")
    print(f" - Gender: {voice.gender}")
    print(f" - Age: {voice.age}")

# Initialize speech recognition
recognizer = sr.Recognizer()

# Web driver for advanced web actions
driver = None

conversation_history = []

# Add these global variables at the top of the file
speaking = False
speech_queue = queue.Queue()
stop_speaking = threading.Event()

# Replace the Dialogflow setup with a flag to indicate if it's available
use_dialogflow = False
print("Using basic intent detection.")

def detect_intent(text):
    # Basic intent detection
    if "exit" in text or "quit" in text:
        return SimpleIntent("exit")
    elif any(action in text for action in ['open', 'close', 'type', 'click', 'move mouse', 'press', 'hotkey', 'activate window', 'minimize', 'maximize', 'scroll', 'drag', 'screenshot', 'shutdown', 'restart', 'lock', 'volume', 'brightness', 'clipboard', 'run']):
        return SimpleIntent("computer_action")
    elif any(action in text for action in ['create folder', 'delete file', 'list files']):
        return SimpleIntent("file_action")
    elif "open a text file" in text:
        return SimpleIntent("open_text_file")
    else:
        return SimpleIntent("unknown")

class SimpleIntent:
    def __init__(self, display_name):
        self.intent = SimpleIntentInfo(display_name)

class SimpleIntentInfo:
    def __init__(self, display_name):
        self.display_name = display_name

WAKE_WORD = "hey jasper"
INTERRUPT_WORD = "stop talking"

class ModernAssistantGUI:
    def __init__(self, master):
        self.master = master
        master.title("Jasper AI Assistant")
        master.geometry("600x400")
        master.configure(bg="#f0f0f0")

        style = ttk.Style()
        style.theme_use("clam")

        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=70, height=20, font=("Arial", 10))
        self.text_area.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.input_field = ttk.Entry(master, width=50, font=("Arial", 10))
        self.input_field.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.submit_button = ttk.Button(master, text="Submit", command=self.process_input)
        self.submit_button.grid(row=1, column=1, padx=10, pady=10, sticky="e")

        self.status_label = ttk.Label(master, text="Sleeping... Say 'Hey Jasper' to wake me up", font=("Arial", 10))
        self.status_label.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)

        self.is_listening = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Perform initial microphone check
        with self.microphone as source:
            print("Adjusting for ambient noise. Please wait...")
            self.recognizer.adjust_for_ambient_noise(source, duration=3)
        
        self.listening_thread = threading.Thread(target=self.continuous_listen, daemon=True)
        self.listening_thread.start()

        self.update_queue = queue.Queue()
        self.master.after(100, self.process_queue)

        self.stop_speaking = threading.Event()
        self.is_speaking = False

    def process_queue(self):
        try:
            while True:
                task = self.update_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.process_queue)

    def update_status(self, text):
        self.update_queue.put(lambda: self.status_label.config(text=text))

    def update_text_area(self, text):
        self.update_queue.put(lambda: self.text_area.insert(tk.END, text + "\n"))

    def process_input(self):
        user_input = self.input_field.get()
        self.update_text_area(f"You: {user_input}")
        self.input_field.delete(0, tk.END)
        threading.Thread(target=self.process_command, args=(user_input,)).start()

    def continuous_listen(self):
        while True:
            if not self.is_listening:
                self.listen_for_wake_word()
            else:
                command = self.listen()
                if command:
                    self.update_text_area(f"You: {command}")
                    threading.Thread(target=self.process_command, args=(command,)).start()
            time.sleep(0.1)

    def listen_for_wake_word(self):
        print("Listening for wake word...")  # Debug print
        with self.microphone as source:
            self.update_status("Sleeping... Say 'Hey Jasper' to wake me up")
            try:
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                print("Audio captured, attempting to recognize...")  # Debug print
                text = self.recognizer.recognize_google(audio, show_all=True)
                print(f"Recognized: {text}")  # Debug print
                if text and WAKE_WORD in text['alternative'][0]['transcript'].lower():
                    print("Wake word detected!")  # Debug print
                    self.is_listening = True
                    self.update_status("I'm awake! How can I help you?")
                    self.speak("I'm awake! How can I help you?")
            except sr.WaitTimeoutError:
                print("Listen timeout")  # Debug print
            except sr.UnknownValueError:
                print("Speech not recognized")  # Debug print
            except Exception as e:
                print(f"An error occurred: {str(e)}")

    def listen(self):
        print("Listening for command...")  # Debug print
        with self.microphone as source:
            self.update_status("Listening...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print("Audio captured, attempting to recognize...")  # Debug print
                text = self.recognizer.recognize_google(audio).lower()
                print(f"Recognized: {text}")  # Debug print
                if WAKE_WORD in text:
                    return ""
                if "stop" in text:
                    self.stop_speaking.set()
                    self.is_speaking = False
                    self.update_status("Stopped speaking. Waiting for command...")
                    return ""
                return text
            except sr.WaitTimeoutError:
                print("Listen timeout")  # Debug print
                self.is_listening = False
                self.update_status("Sleeping... Say 'Hey Jasper' to wake me up")
                return ""
            except sr.UnknownValueError:
                print("Speech not recognized")  # Debug print
                return ""
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                return ""

    def process_command(self, command):
        if not command:
            return

        processed_command = process_natural_language(command)
        intent = detect_intent(processed_command)
        
        if intent.intent.display_name == "exit":
            self.update_text_area("Jasper: Goodbye!")
            self.master.quit()
        elif intent.intent.display_name == "computer_action":
            threading.Thread(target=perform_computer_action, args=(processed_command,)).start()
            self.update_text_area(f"Jasper: Performing computer action: {processed_command}")
        elif intent.intent.display_name == "file_action":
            threading.Thread(target=perform_file_action, args=(processed_command,)).start()
            self.update_text_area(f"Jasper: Performing file action: {processed_command}")
        elif intent.intent.display_name == "open_text_file":
            threading.Thread(target=open_text_file).start()
            self.update_text_area("Jasper: Opening a new text file on your desktop.")
        else:
            response = process_command(processed_command)
            self.update_text_area(f"Jasper: {response}")
            self.speak(response)

    def speak(self, text):
        if self.is_speaking:
            return
        self.is_speaking = True
        self.stop_speaking.clear()
        try:
            print(f"Jasper: {text}")
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[1].id)  # Female voice
            engine.setProperty('volume', 0.8)  # 80% volume
            engine.setProperty('rate', 170)  # Adjust speaking rate

            sentences = text.split('.')
            for sentence in sentences:
                if self.stop_speaking.is_set():
                    break
                
                if random.random() < 0.2:  # 20% chance
                    filler = random.choice(["Um, ", "Ah, ", "Well, ", "You see, ", "So, "])
                    engine.say(filler)
                    engine.runAndWait()
                    if self.stop_speaking.is_set():
                        break
                
                engine.say(sentence.strip())
                engine.runAndWait()
                
                if self.stop_speaking.is_set():
                    break
                
                pause_time = random.uniform(0.3, 0.7)
                time.sleep(pause_time)
            
            logging.info(f"Jasper response: {text}")
        except Exception as e:
            logging.error(f"Error in text-to-speech: {str(e)}")
        finally:
            self.is_speaking = False
            self.stop_speaking.clear()

def listen():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            text = recognizer.recognize_google(audio)
            print(f"You: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            print("Sorry, there was an error with the speech recognition service.")
            return ""
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return ""

def speak(text):
    global speaking
    try:
        print(f"Jasper: {text}")
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)  # Female voice
        engine.setProperty('volume', 0.8)  # 70% volume for a quieter voice
        engine.setProperty('rate', 170)  # Adjust speaking rate

        sentences = text.split('.')
        for sentence in sentences:
            if stop_speaking.is_set():
                break
            speaking = True
            
            if random.random() < 0.2:  # 20% chance
                filler = random.choice(["Um, ", "Ah, ", "Well, ", "You see, ", "So, "])
                engine.say(filler)
                engine.runAndWait()
                time.sleep(0.2)
            
            engine.say(sentence.strip())
            engine.runAndWait()
            
            pause_time = random.uniform(0.3, 0.7)
            time.sleep(pause_time)
        
        speaking = False
        logging.info(f"Jasper response: {text}")
    except Exception as e:
        logging.error(f"Error in text-to-speech: {str(e)}")
    finally:
        speaking = False

def interrupt_handler():
    global speaking, stop_speaking
    while True:
        if keyboard.is_pressed('ctrl+c'):
            if speaking:
                stop_speaking.set()
                speaking = False
                print("Jasper: I'm sorry for interrupting. What would you like me to do?")
                speak("I'm sorry for interrupting. What would you like me to do?")
            else:
                stop_speaking.clear()
        time.sleep(0.1)

def listen_command():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        
    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"You said: {command}")
        
        # New: Display the command and ask for confirmation
        print("Is this correct? (yes/no)")
        speak("Is this correct?")
        confirmation = listen_confirmation()
        
        if confirmation == 'yes':
            logging.info(f"User command: {command}")
            return command
        elif confirmation == 'no':
            print("Please repeat your command.")
            speak("Please repeat your command.")
            return None
        else:
            print("I didn't understand. Please try again.")
            speak("I didn't understand. Please try again.")
            return None
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that. Could you please repeat?")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

def listen_confirmation():
    with sr.Microphone() as source:
        print("Listening for confirmation...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        
    try:
        confirmation = recognizer.recognize_google(audio).lower()
        print(f"Confirmation: {confirmation}")
        return confirmation
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

def display_command(command):
    print(f"\rYou: {command}", end='', flush=True)

def listen_and_display():
    partial_command = ""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        while True:
            try:
                audio = recognizer.listen(source, phrase_time_limit=2)
                part = recognizer.recognize_google(audio, show_all=False).lower()
                partial_command += part + " "
                display_command(partial_command)
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                break

def process_command(command):
    global conversation_history
    try:
        # Add user's command to conversation history
        conversation_history.append(f"Human: {command}")
        
        # Prepare the conversation context
        context = "\n".join(conversation_history[-5:])  # Keep last 5 exchanges for context
        
        # Generate a response using the Gemini API
        response = model.generate_content(f"""
        You are an AI assistant named Jasper. Respond to the following command or question, 
        taking into account the conversation history. If more information is needed, ask a 
        follow-up question. Be concise but helpful. When presenting lists:
        - Use numbers (1., 2., 3., etc.) for ordered lists
        - Use dashes (-) for unordered lists
        - Avoid using asterisks (*) for list items

        Conversation history:
        {context}

        Human: {command}
        Jasper: """)
        
        # Extract the assistant's response
        assistant_response = response.text.strip()
        
        # Format the response for better readability
        formatted_response = format_response(assistant_response)
        
        # Add assistant's response to conversation history
        conversation_history.append(f"Jasper: {formatted_response}")
        
        # Speak the response
        speak(formatted_response)
        
        # Check if the response contains a question and prompt for user input if it does
        if '?' in formatted_response:
            follow_up = listen_command()
            if follow_up:
                process_command(follow_up)
    except Exception as e:
        logging.error(f"Error in processing command: {str(e)}")
        speak("I'm sorry, I encountered an error while processing your command.")

def format_response(response):
    # Split the response into lines
    lines = response.split('\n')
    formatted_lines = []
    in_list = False
    list_index = 1

    for line in lines:
        # Check if the line starts a new list item
        if line.strip().startswith('*'):
            if not in_list:
                in_list = True
                list_index = 1
            # Replace * with - or a number
            if ':' in line:  # Likely an ordered list
                formatted_line = f"{list_index}. {line.strip()[1:].strip()}"
                list_index += 1
            else:  # Unordered list
                formatted_line = f"- {line.strip()[1:].strip()}"
            formatted_lines.append(formatted_line)
        else:
            if in_list and not line.strip():
                in_list = False
            formatted_lines.append(line)

    return '\n'.join(formatted_lines)

def perform_web_action(command):
    try:
        if 'search' in command:
            query = command.split('search ')[-1]
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            speak(f"Searching for {query}")
        elif 'open youtube' in command:
            webbrowser.open("https://www.youtube.com")
            speak("Opening YouTube")
        elif 'youtube search' in command:
            query = command.split('youtube search ')[-1]
            url = f"https://www.youtube.com/results?search_query={query}"
            webbrowser.open(url)
            speak(f"Searching YouTube for {query}")
        else:
            speak("I'm not sure how to perform that web action.")
    except Exception as e:
        logging.error(f"Error in web action: {str(e)}")
        speak("I encountered an error while performing the web action.")

def perform_computer_action(command):
    try:
        if 'open' in command:
            app = command.split('open ')[-1]
            if app == 'youtube':
                webbrowser.open("https://www.youtube.com")
            else:
                subprocess.Popen(['start', app], shell=True)
            speak(f"Opening {app}")
        elif 'close' in command:
            app = command.split('close ')[-1]
            os.system(f"taskkill /F /IM {app}.exe")
            speak(f"Closing {app}")
        elif 'type' in command:
            text = command.split('type ')[-1]
            pyautogui.typewrite(text)
            speak(f"Typed: {text}")
        elif 'click' in command:
            if 'right' in command:
                pyautogui.rightClick()
                speak("Performed right-click")
            elif 'double' in command:
                pyautogui.doubleClick()
                speak("Performed double-click")
            else:
                x, y = map(int, command.split('click ')[-1].split(','))
                pyautogui.click(x, y)
                speak(f"Clicked at coordinates {x}, {y}")
        elif 'move mouse' in command:
            x, y = map(int, command.split('move mouse to ')[-1].split(','))
            pyautogui.moveTo(x, y)
            speak(f"Moved mouse to coordinates {x}, {y}")
        elif 'press' in command:
            key = command.split('press ')[-1]
            pyautogui.press(key)
            speak(f"Pressed {key}")
        elif 'hotkey' in command:
            keys = command.split('hotkey ')[-1].split()
            pyautogui.hotkey(*keys)
            speak(f"Pressed hotkey: {' + '.join(keys)}")
        elif 'activate window' in command:
            window_name = command.split('activate window ')[-1]
            activate_window(window_name)
            speak(f"Activated window: {window_name}")
        elif 'minimize' in command:
            window_name = command.split('minimize ')[-1]
            minimize_window(window_name)
            speak(f"Minimized window: {window_name}")
        elif 'maximize' in command:
            window_name = command.split('maximize ')[-1]
            maximize_window(window_name)
            speak(f"Maximized window: {window_name}")
        elif 'scroll' in command:
            direction = 'up' if 'up' in command else 'down'
            clicks = int(command.split()[-1])
            pyautogui.scroll(clicks if direction == 'up' else -clicks)
            speak(f"Scrolled {direction} by {clicks} clicks")
        elif 'drag' in command:
            start_x, start_y, end_x, end_y = map(int, command.split('drag from ')[-1].split('to'))
            pyautogui.dragTo(end_x, end_y, duration=1, button='left')
            speak(f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        elif 'screenshot' in command:
            pyautogui.screenshot('screenshot.png')
            speak("Screenshot taken and saved as screenshot.png")
        elif 'shutdown' in command:
            os.system("shutdown /s /t 1")
            speak("Shutting down the computer")
        elif 'restart' in command:
            os.system("shutdown /r /t 1")
            speak("Restarting the computer")
        elif 'lock' in command:
            ctypes.windll.user32.LockWorkStation()
            speak("Computer locked")
        elif 'volume' in command:
            if 'up' in command:
                pyautogui.press('volumeup')
                speak("Volume increased")
            elif 'down' in command:
                pyautogui.press('volumedown')
                speak("Volume decreased")
            elif 'mute' in command:
                pyautogui.press('volumemute')
                speak("Volume muted")
        elif 'brightness' in command:
            # Note: This requires additional setup and might not work on all systems
            speak("I'm sorry, I can't adjust brightness directly. Please use your system settings.")
        elif 'clipboard' in command:
            if 'copy' in command:
                pyautogui.hotkey('ctrl', 'c')
                speak("Copied to clipboard")
            elif 'paste' in command:
                pyautogui.hotkey('ctrl', 'v')
                speak("Pasted from clipboard")
        elif 'run' in command:
            app = command.split('run ')[-1]
            subprocess.Popen(app, shell=True)
            speak(f"Running {app}")
        else:
            speak("I'm not sure how to perform that computer action.")
    except Exception as e:
        logging.error(f"Error in computer action: {str(e)}")
        speak(f"I encountered an error while performing the computer action: {str(e)}")

def activate_window(window_name):
    def window_enum_handler(hwnd, result):
        if win32gui.IsWindowVisible(hwnd) and window_name.lower() in win32gui.GetWindowText(hwnd).lower():
            win32gui.SetForegroundWindow(hwnd)
            return False
        return True

    win32gui.EnumWindows(window_enum_handler, None)

def minimize_window(window_name):
    def window_enum_handler(hwnd, result):
        if win32gui.IsWindowVisible(hwnd) and window_name.lower() in win32gui.GetWindowText(hwnd).lower():
            win32gui.ShowWindow(hwnd, win32gui.SW_MINIMIZE)
            return False
        return True

    win32gui.EnumWindows(window_enum_handler, None)

def maximize_window(window_name):
    def window_enum_handler(hwnd, result):
        if win32gui.IsWindowVisible(hwnd) and window_name.lower() in win32gui.GetWindowText(hwnd).lower():
            win32gui.ShowWindow(hwnd, win32gui.SW_MAXIMIZE)
            return False
        return True

    win32gui.EnumWindows(window_enum_handler, None)

def perform_file_action(command):
    try:
        if 'create folder' in command:
            folder_name = command.split('create folder ')[-1]
            os.makedirs(folder_name, exist_ok=True)
            speak(f"Created folder: {folder_name}")
        elif 'delete file' in command:
            file_name = command.split('delete file ')[-1]
            os.remove(file_name)
            speak(f"Deleted file: {file_name}")
        elif 'list files' in command:
            files = os.listdir()
            speak(f"Files in the current directory: {', '.join(files)}")
        else:
            speak("I'm not sure how to perform that file action.")
    except Exception as e:
        logging.error(f"Error in file action: {str(e)}")
        speak("I encountered an error while performing the file action.")

def perform_system_action(command):
    try:
        if 'volume up' in command:
            pyautogui.press("volumeup")
            speak("Volume increased")
        elif 'volume down' in command:
            pyautogui.press("volumedown")
            speak("Volume decreased")
        elif 'mute' in command:
            pyautogui.press("volumemute")
            speak("Audio muted")
        elif 'brightness' in command:
            # This is a placeholder. Actual implementation may vary depending on the system
            speak("I'm sorry, I can't adjust brightness directly. Please use your system settings.")
        else:
            speak("I'm not sure how to perform that system action.")
    except Exception as e:
        logging.error(f"Error in system action: {str(e)}")
        speak("I encountered an error while performing the system action.")

def perform_advanced_action(command):
    if 'system info' in command:
        system_info()
    elif 'cpu usage' in command:
        cpu_usage()
    elif 'memory usage' in command:
        memory_usage()
    elif 'disk usage' in command:
        disk_usage()
    elif 'list processes' in command:
        list_processes()
    elif 'kill process' in command:
        process_name = command.split('kill process ')[-1]
        kill_process(process_name)
    elif 'network info' in command:
        network_info()
    elif 'internet speed' in command:
        internet_speed()
    elif 'weather' in command:
        city = command.split('weather in ')[-1]
        get_weather(city)
    elif 'translate' in command:
        text = command.split('translate ')[-1]
        translate_text(text)
    elif 'ocr' in command:
        perform_ocr()
    elif 'face detection' in command:
        detect_faces()
    elif 'compress files' in command:
        compress_files()
    elif 'extract files' in command:
        extract_files()
    elif 'send email' in command:
        send_email()
    elif 'set reminder' in command:
        set_reminder()
    elif 'play music' in command:
        play_music()
    elif 'news headlines' in command:
        get_news_headlines()
    elif 'create todo' in command:
        create_todo()
    elif 'take notes' in command:
        take_notes()
    elif 'summarize text' in command:
        summarize_text()
    elif 'tell joke' in command:
        tell_joke()
    elif 'write poem' in command:
        write_poem()
    elif 'calculate' in command:
        calculate(command)
    else:
        speak("I'm not sure how to perform that advanced action.")

def system_info():
    info = f"System: {platform.system()} {platform.version()}\n"
    info += f"Processor: {platform.processor()}\n"
    info += f"Machine: {platform.machine()}\n"
    info += f"Node: {platform.node()}"
    speak(info)

def cpu_usage():
    usage = psutil.cpu_percent(interval=1)
    speak(f"Current CPU usage is {usage}%")

def memory_usage():
    memory = psutil.virtual_memory()
    speak(f"Total memory: {memory.total / (1024**3):.2f} GB")
    speak(f"Available memory: {memory.available / (1024**3):.2f} GB")
    speak(f"Memory usage: {memory.percent}%")

def disk_usage():
    disk = psutil.disk_usage('/')
    speak(f"Total disk space: {disk.total / (1024**3):.2f} GB")
    speak(f"Used disk space: {disk.used / (1024**3):.2f} GB")
    speak(f"Free disk space: {disk.free / (1024**3):.2f} GB")
    speak(f"Disk usage: {disk.percent}%")

def list_processes():
    processes = []
    for proc in psutil.process_iter(['name', 'cpu_percent']):
        processes.append((proc.info['name'], proc.info['cpu_percent']))
    processes.sort(key=lambda x: x[1], reverse=True)
    speak("Top 5 CPU-consuming processes:")
    for proc in processes[:5]:
        speak(f"{proc[0]}: {proc[1]}% CPU")

def kill_process(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            proc.terminate()
            speak(f"Process {process_name} has been terminated.")
            return
    speak(f"Process {process_name} not found.")

def network_info():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    speak(f"Hostname: {hostname}")
    speak(f"IP Address: {ip_address}")

def internet_speed():
    st = speedtest.Speedtest()
    speak("Testing download speed...")
    download_speed = st.download() / 1_000_000
    speak("Testing upload speed...")
    upload_speed = st.upload() / 1_000_000
    speak(f"Download speed: {download_speed:.2f} Mbps")
    speak(f"Upload speed: {upload_speed:.2f} Mbps")

def get_weather(city):
    api_key = "YOUR_OPENWEATHERMAP_API_KEY"
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        speak(f"The temperature in {city} is {temp}°C with {desc}.")
    else:
        speak("Sorry, I couldn't fetch the weather information.")

def translate_text(text):
    # This is a placeholder. You'll need to implement a translation service.
    speak(f"Translating: {text}")
    speak("Translation functionality not implemented yet.")

def perform_ocr():
    # Take a screenshot
    pyautogui.screenshot('ocr_screenshot.png')
    # Perform OCR
    text = pytesseract.image_to_string(Image.open('ocr_screenshot.png'))
    speak("OCR Result:")
    speak(text)

def detect_faces():
    # Initialize the camera
    cap = cv2.VideoCapture(0)
    # Load the pre-trained face detection classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    ret, frame = cap.read()
    if ret:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        speak(f"Detected {len(faces)} faces.")
    else:
        speak("Failed to capture image from camera.")
    
    cap.release()

def compress_files():
    speak("Please specify the folder to compress.")
    folder = input("Enter folder path: ")
    output = folder + '.zip'
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder):
            for file in files:
                zipf.write(os.path.join(root, file))
    speak(f"Files compressed and saved as {output}")

def extract_files():
    speak("Please specify the zip file to extract.")
    zip_file = input("Enter zip file path: ")
    output_folder = zip_file.rsplit('.', 1)[0]
    with zipfile.ZipFile(zip_file, 'r') as zipf:
        zipf.extractall(output_folder)
    speak(f"Files extracted to {output_folder}")

def send_email():
    speak("Please provide the following information:")
    recipient = input("Recipient email: ")
    subject = input("Email subject: ")
    body = input("Email body: ")
    
    # You'll need to set up your email and password
    sender_email = "your_email@example.com"
    sender_password = "your_email_password"
    
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
    
    speak("Email sent successfully.")

def set_reminder():
    speak("What should I remind you about?")
    task = input("Enter task: ")
    speak("When should I remind you? (Enter time in HH:MM format)")
    reminder_time = input("Enter time (HH:MM): ")
    
    current_time = time.strftime("%H:%M")
    while current_time != reminder_time:
        current_time = time.strftime("%H:%M")
        time.sleep(60)
    
    speak(f"Reminder: {task}")

def play_music():
    speak("What song would you like to play?")
    song = input("Enter song name: ")
    pywhatkit.playonyt(song)

def get_news_headlines():
    api_key = "YOUR_NEWSAPI_KEY"
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        news = response.json()['articles'][:5]
        speak("Here are the top 5 news headlines:")
        for article in news:
            speak(article['title'])
    else:
        speak("Sorry, I couldn't fetch the news headlines.")

def create_todo():
    speak("What would you like to add to your to-do list?")
    task = input("Enter task: ")
    with open('todo.txt', 'a') as f:
        f.write(f"- {task}\n")
    speak(f"Added '{task}' to your to-do list.")

def take_notes():
    speak("What would you like to note down?")
    note = input("Enter note: ")
    with open('notes.txt', 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {note}\n")
    speak("Note has been saved.")

def summarize_text():
    speak("Please enter the text you'd like me to summarize:")
    text = input("Enter text: ")
    # This is a placeholder. You'd need to implement or use an API for actual summarization.
    summary = text[:100] + "..."  # Just takes the first 100 characters as a simple "summary"
    speak("Here's a summary of the text:")
    speak(summary)

def tell_joke():
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Why did the scarecrow win an award? He was outstanding in his field!",
        "Why don't eggs tell jokes? They'd crack each other up!"
    ]
    joke = random.choice(jokes)
    speak(joke)

def write_poem():
    speak("Here's a short poem for you:")
    poem = """
    In circuits of silicon and wire,
    An AI assistant, never to tire.
    With voice commands, I come alive,
    To help and serve, that's how I thrive.
    """
    speak(poem)

def calculate(command):
    # Extract the mathematical expression from the command
    expression = command.split('calculate ')[-1]
    try:
        result = eval(expression)
        speak(f"The result of {expression} is {result}")
    except:
        speak("I'm sorry, I couldn't calculate that. Please try a simpler expression.")

def open_text_file():
    try:
        file_path = os.path.join(os.path.expanduser("~"), "Desktop", "new_file.txt")
        with open(file_path, 'w') as f:
            f.write("This is a new text file created by Jasper.")
        os.startfile(file_path)
        speak("I've created and opened a new text file on your desktop.")
    except Exception as e:
        speak(f"Sorry, I encountered an error while trying to open the file: {str(e)}")

def load_user_preferences():
    try:
        with open('user_preferences.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

user_preferences = load_user_preferences()

# Use preferences in your code
voice_id = user_preferences.get('voice_id', 1)  # Default to voice 1 if not set
engine.setProperty('voice', voices[voice_id].id)

def load_custom_commands():
    try:
        with open('custom_commands.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

custom_commands = load_custom_commands()

def process_natural_language(command):
    tokens = word_tokenize(command.lower())
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [w for w in tokens if not w in stop_words]
    return ' '.join(filtered_tokens)

def execute_custom_command(command):
    for custom_cmd, action in custom_commands.items():
        if custom_cmd in command:
            speak(f"Executing custom command: {custom_cmd}")
            exec(action)
            return True
    return False

def perform_advanced_windows_action(command):
    if 'change wallpaper' in command:
        image_path = command.split('change wallpaper to ')[-1]
        win32api.SystemParametersInfo(win32con.SPI_SETDESKWALLPAPER, image_path, 0)
        speak("Wallpaper changed successfully")
    elif 'empty recycle bin' in command:
        win32api.ShellExecute(0, 'open', 'shell:RecycleBinFolder', '', '', 1)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('delete')
        speak("Recycle bin emptied")
    # Add more Windows-specific actions here

def main():
    root = tk.Tk()
    gui = ModernAssistantGUI(root)
    
    print("Jasper: Hello! I'm Jasper, your AI assistant. Say 'Hey Jasper' to wake me up.")
    gui.speak("Hello! I'm Jasper, your AI assistant. Say 'Hey Jasper' to wake me up.")
    
    root.mainloop()

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.DEBUG)
        main()
    except Exception as e:
        error_message = f"Critical error in main execution: {str(e)}"
        print(f"Error: {error_message}")
        logging.critical(error_message)
        print("Jasper: I encountered a critical error and need to shut down. Please check the error message above.")
    finally:
        if 'driver' in globals() and driver:
            driver.quit()
