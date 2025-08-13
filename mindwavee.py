import pyttsx3
import pyaudio
import speech_recognition as sr
import wikipedia 
import webbrowser
import re
import urllib.parse
import pywhatkit as wk
import os
import random
import cv2
import sys
import time
import pyautogui
import numexpr
import pyperclip
import threading
import logging
import subprocess
import shutil
import psutil
import platform
import wmi
import datetime
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Setup logging
logging.basicConfig(level=logging.INFO, filename='assistant.log', format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize text-to-speech
engine = pyttsx3.init('sapi5')
engine.setProperty('voice', engine.getProperty('voices')[0].id)
engine.setProperty('rate', 140)

# Initialize recognizer
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Calibrate microphone
with microphone as source:
    print("Calibrating microphone for ambient noise...")
    recognizer.adjust_for_ambient_noise(source, duration=2)
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = 300

def speak(text):
    print(text)
    engine.say(text)
    engine.runAndWait()
    
def wishme():
    hour = datetime.datetime.now().hour
    greeting = "Good Morning" if 0 <= hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"
    speak(f"{greeting} master! Ready to comply. What can I do for you?")

def takeCommand():
    logging.info("Starting takeCommand")
    start_time = time.time()
    
    for attempt in range(2):
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("\033[92mListening...\033[0m")
            recognizer.pause_threshold = 1.2
            try:
                audio = recognizer.listen(source, timeout=7, phrase_time_limit=15)
                print("Processing audio...")
                try:
                    query = recognizer.recognize_google(audio, language='en-in')
                    print(f"Recognized: {query}")
                    logging.info(f"Recognized query: {query}")
                    if len(query.strip()) > 0:
                        return query.lower()
                    else:
                        if attempt == 0:
                            speak("I didn't catch that. Please try again.")
                        continue
                except sr.UnknownValueError:
                    if attempt == 0:
                        speak("I didn't understand that. Could you please repeat?")
                    logging.warning("Could not understand audio")
                    continue
                except sr.RequestError as e:
                    logging.error(f"Speech recognition error: {e}")
                    speak("There was an issue with the speech recognition service.")
                    return "none"
            except sr.WaitTimeoutError:
                if attempt == 0:
                    print("I didn't hear anything. Please try again.")
                logging.warning("No speech detected within timeout")
                continue
    logging.warning("Multiple recognition attempts failed")
    return "none"

cap = None
camera_running = False

def run_camera():
    global cap, camera_running
    cap = cv2.VideoCapture(0)
    while camera_running:
        ret, img = cap.read()
        if not ret:
            break
        cv2.imshow('webcam', img)
        if cv2.waitKey(1) == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    camera_running = False
    
def confirm_command(action_description):
    speak(f"I heard a request to {action_description}. Is that correct? Please say yes or no.")
    response = takeCommand().lower()
    return "yes" in response

def handle_browser_command(query):
    if "just open google" in query:
        webbrowser.open('https://www.google.com/')
        return True
    elif "open google" in query and "just" not in query:
        speak("What should I search?")
        search_query = takeCommand().lower()
        if search_query and search_query not in ["none", "timeout", "error"]:
            encoded_query = urllib.parse.quote(search_query)
            search_url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(search_url)
            try:
                results = wikipedia.summary(search_query, sentences=2)
                print(results)
                speak(results)
            except Exception as e:
                print(f"Wikipedia error: {e}")
            return True
        else:
            speak("Sorry, I didn't catch that. Opening Google homepage instead.")
            webbrowser.open('https://www.google.com/')
            return False
    return False

def set_brightness(level):
    try:
        wmi.WMI(namespace='wmi').WmiMonitorBrightnessMethods()[0].WmiSetBrightness(level, 0)
        return True
    except Exception as e:
        print(f"Error setting brightness: {e}")
        return False

def set_application_volume(app_name, level):
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        interface = session.SimpleAudioVolume
        if session.Process and session.Process.name().lower() == app_name.lower():
            interface.SetMasterVolume(level, None)
            print(f"Set {app_name} volume to {level}")
            return
    print(f"Application '{app_name}' not found.")

def list_commands():
    speak("I can help with:")
    speak("Browser tasks - opening websites, searching")
    speak("System controls - volume, brightness, shutdown")
    speak("Applications - opening and closing programs")
    speak("File navigation - accessing drives and folders")
    speak("Mouse and keyboard - clicking, typing")
    speak("Media playback - playing YouTube or pausing media")
    speak("Calculations - solving math problems")
    speak("System info - time, date, disk space")
    
    
  
    

if __name__ == "__main__":
    wishme()
    while True:
        query = takeCommand().lower()
        if 'mind wave' in query:
            print("Yes master")
            speak("Yes master")
           
        elif 'go to sleep' in query or 'exit' in query or 'quit' in query:
            speak('Goodbye master! Switching off.')
            if camera_running:
                camera_running = False
                time.sleep(1)
            sys.exit()

        elif 'who are you' in query:
            print("My name is MindWave and I'm your voice assistant. How can I help you, sir?")
            speak("My name is MindWave and I'm your voice assistant. How can I help you, sir?")
           
        elif 'who created you' in query:
            print("My master created me. I don't know her name, but I was created with Python.")
            speak("My master  created me. I don't know her name, but I was created with Python.")
            
        elif handle_browser_command(query):
            continue
                
        elif "just open youtube" in query:
            webbrowser.open('https://www.youtube.com/')
            
        elif "search on youtube" in query:
            query = query.replace("search on youtube", "")
            speak("Sure sir, searching on YouTube")
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            
        elif "close browser" in query:
            os.system("taskkill /f /im opera.exe")
            os.system("taskkill /f /im chrome.exe")
            os.system("taskkill /f /im firefox.exe")
            os.system("taskkill /f /im msedge.exe")
            speak("Browser closed.")
            
        elif "open notepad" in query:
            speak("Opening Notepad")
            npath = os.path.expandvars(r"%windir%\system32\notepad.exe")
            os.startfile(npath)
            
        elif "close notepad" in query:
            os.system("taskkill /f /im notepad.exe")
            speak("Notepad has been closed.")
            
        elif "open paint" in query:
            speak("Opening Paint")
            npath = os.path.expandvars(r"%windir%\system32\mspaint.exe")
            os.startfile(npath)
            
        elif "close paint" in query:
            os.system("taskkill /f /im mspaint.exe")
            speak("Paint has been closed.")
            
        elif "vs code" in query:
            speak("Opening VS Code")
            npath = os.path.expandvars(r"E:\vscode\Code.exe")
            os.startfile(npath)
            
        elif "close vs code" in query:
            print(f"Recognized query: {query}")
            processes = os.popen("tasklist").read()
            if "Code.exe" in processes:
                os.system("taskkill /f /im Code.exe")
                speak("VS Code has been closed.")
            else:
                speak("VS Code is not running.")
                
        elif "current time" in query:
            strTime = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"Master, current time is: {strTime}")
            speak(f"Master, current time is {strTime}")
               
        elif "shut down" in query:
            os.system("shutdown /s /t 5")
            print("Shutting down the system...")
            speak("Shutting down the system.")
               
        elif "restart" in query:
            os.system("shutdown /r /t 5")
            print("Restarting the system...")
            speak("Restarting the system.")
            
        elif any(cmd in query.lower() for cmd in ["take screenshot", "capture screen", "screenshot please", "save screen", "grab screen", "screenshot", "take a screenshot"]):
            speak("Tell me a name for the file")
            name = takeCommand().lower()
            save_directory = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
            os.makedirs(save_directory, exist_ok=True)
            time.sleep(3)
            img = pyautogui.screenshot()
            file_name = f"{name}.png"
            file_path = os.path.join(save_directory, file_name)
            img.save(file_path)
            speak(f"Screenshot saved as {file_name} in {save_directory}")
            print(f"Screenshot saved at: {file_path}")
            
         
        
            
        elif any(word in query.lower() for word in ["calculate", "calc", "math"]):
            print(f"Calculation request detected: {query}")
            math_part = re.sub(r'.*(calculate|calc|math)', '', query.lower(), flags=re.IGNORECASE).strip()
            if not math_part:
                speak("Please provide the calculation after the command, like 'calculate 2 plus 2'")
                continue
            conversions = [
                ('divided by', '/'), ('over', '/'), ('divide', '/'),
                ('times', '*'), ('x', '*'), ('multiplied by', '*'), ('multiply', '*'),
                ('plus', '+'), ('add', '+'),
                ('minus', '-'), ('subtract', '-'),
                ('to the power of', '**'), ('raised to', '**'), ('power', '**'),
                ('point', '.'), ('dot', '.')
            ]
            for word, symbol in conversions:
                math_part = math_part.replace(word, symbol)
            math_expr = re.sub(r'[^0-9+\-*/\s()^.]', '', math_part).strip()
            print(f"Original query: {query}")
            print(f"Extracted math part: {math_part}")
            print(f"Processed math expression: {math_expr}")
            if not math_expr:
                speak("I couldn't find any valid numbers to calculate")
                continue
            if re.search(r'[\+\-\*/\.\^]\s*$', math_expr):
                if len(math_expr) > 2 and not math_expr[-2].isspace():
                    speak("Your calculation seems incomplete. Please say the rest of the expression.")
                else:
                    speak("Your calculation seems incomplete. Please include all numbers.")
                continue
            if re.search(r'/(\s)*0', math_expr) or '/0' in math_expr.replace(" ", ""):
                speak("You can't divide by zero!")
                continue
            try:
                standard_result = numexpr.evaluate(math_expr).item()
                tokens = re.findall(r'(\d+\.?\d*|[\+\-\*/])', math_expr.replace(' ', ''))
                if len(tokens) > 1:
                    ltr_result = float(tokens[0])
                    for i in range(1, len(tokens), 2):
                        op = tokens[i]
                        num = float(tokens[i+1])
                        if op == '+': ltr_result += num
                        elif op == '-': ltr_result -= num
                        elif op == '*': ltr_result *= num
                        elif op == '/':
                            if num == 0:
                                speak("You can't divide by zero!")
                                continue
                            ltr_result /= num
                if isinstance(standard_result, float) and standard_result.is_integer():
                    standard_result = int(standard_result)
                if 'ltr_result' in locals() and isinstance(ltr_result, float) and ltr_result.is_integer():
                    ltr_result = int(ltr_result)
                if '*' in math_expr or '/' in math_expr:
                    if 'ltr_result' in locals() and standard_result != ltr_result:
                        speak(f"The result is {standard_result} (following math rules) or {ltr_result} (left-to-right)")
                    else:
                        speak(f"The result is {standard_result}")
                else:
                    speak(f"The result is {standard_result}")
                print(f"Calculation: {math_expr} = {standard_result} (standard) {f'= {ltr_result} (left-to-right)' if 'ltr_result' in locals() and standard_result != ltr_result else ''}")
            except ZeroDivisionError:
                speak("You can't divide by zero!")
            except SyntaxError:
                speak("That doesn't appear to be a valid math expression")
            except Exception as e:
                speak("Sorry, I couldn't calculate that")
                print(f"Calculation error: {e}")
            continue
        
        elif any(cmd in query.lower() for cmd in ["just open calculator", "just calculator","calculator"]):
            try:
                speak("Opening Calculator")
                os.startfile("calc")
                time.sleep(0.5)
                speak("Calculator opened successfully")
            except Exception as e:
                speak("Sorry, I couldn't open the Calculator")
                print(f"Error opening Calculator: {e}") 
        
        elif any(cmd in query.lower() for cmd in ["volume up", "increase volume", "turn up volume", "volume increase", "raise volume"]):
            try:
                number_words = {
                    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
                    '6': 6, '7': 7, '8': 8, '9': 9, '10': 10
                }
                level = 3
                query_lower = query.lower()
                for word, num in number_words.items():
                    if f"by {word}" in query_lower or f"by {word} " in query_lower:
                        level = num
                        break
                if level == 3:
                    try:
                        if "by" in query_lower:
                            num_part = query_lower.split("by")[1].strip()
                            level = int(re.search(r'\d+', num_part).group())
                    except (AttributeError, ValueError, IndexError):
                        pass
                level = max(1, min(10, level))
                print(f"Increasing volume by {level} steps")
                speak(f"Turning volume up by {level} steps")
                for _ in range(level):
                    pyautogui.press('volumeup')
                    time.sleep(0.1)
            except Exception as e:
                print(f"Volume adjustment error: {e}")
                speak("Sorry, I couldn't adjust the volume")
            
        elif any(cmd in query.lower() for cmd in ["volume down", "decrease volume", "turn down volume", "volume decrease", "lower volume"]):
            try:
                number_words = {
                    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
                    '6': 6, '7': 7, '8': 8, '9': 9, '10': 10
                }
                level = 3
                query_lower = query.lower()
                for word, num in number_words.items():
                    if f"by {word}" in query_lower or f"by {word} " in query_lower:
                        level = num
                        break
                if level == 3:
                    try:
                        if "by" in query_lower:
                            num_part = query_lower.split("by")[1].strip()
                            level = int(re.search(r'\d+', num_part).group())
                    except (AttributeError, ValueError, IndexError):
                        pass
                level = max(1, min(10, level))
                print(f"Decreasing volume by {level} steps")
                speak(f"Turning volume down by {level} steps")
                for _ in range(level):
                    pyautogui.press('volumedown')
                    time.sleep(0.1)
            except Exception as e:
                print(f"Volume adjustment error: {e}")
                speak("Sorry, I couldn't adjust the volume")
         
        elif any(cmd in query.lower() for cmd in ["mute", "unmute", "volume mute", "silence", "toggle mute"]):
            current_state = "muting" if "unmute" not in query.lower() else "unmuting"
            print(f"{current_state.capitalize()} volume")
            speak(f"{current_state} volume")
            pyautogui.press("volumemute")
            time.sleep(0.3)
                        
        elif "click" in query:
            if "right click" in query:
                speak("Right clicking")
                pyautogui.rightClick()
            elif "double click" in query:
                speak("Double clicking")
                pyautogui.doubleClick()
            else:
                speak("Clicking")
                pyautogui.click()
                    
        elif "scroll down" in query:
            try:
                scroll_amount = int(re.search(r'\d+', query).group()) if re.search(r'\d+', query) else 1
                speak(f"Scrolling down {scroll_amount} times")
                time.sleep(1)
                pyautogui.click()
                for _ in range(scroll_amount):
                    pyautogui.scroll(-800)
                    time.sleep(0.3)
            except Exception as e:
                print(f"Scroll failed: {e}")
                speak("Scroll failed. Please check permissions.")

        elif "scroll up" in query:
            try:
                scroll_amount = int(re.search(r'\d+', query).group()) if re.search(r'\d+', query) else 1
                speak(f"Scrolling up {scroll_amount} times")
                time.sleep(1)
                pyautogui.click()
                for _ in range(scroll_amount):
                    pyautogui.scroll(800)
                    time.sleep(0.3)
            except Exception as e:
                print(f"Scroll failed: {e}")
                speak("Scroll failed. Please check permissions.")
                
        elif any(word in query for word in ["undo", "un do", "and do", "on do"]):
            try:
                speak("Undoing last action")
                pyautogui.hotkey('ctrl', 'z')
                time.sleep(0.3)
            except Exception as e:
                print(f"Undo failed: {e}")
                speak("Could not undo. Please try manually.")

        elif any(word in query for word in ["redo", "re do", "read do", "ray do"]):
            try:
                speak("Redoing last action")
                try:
                    pyautogui.hotkey('ctrl', 'y')
                except:
                    pyautogui.hotkey('ctrl', 'shift', 'z')
                time.sleep(0.3)
            except Exception as e:
                print(f"Redo failed: {e}")
                speak("Could not redo. Please try manually.")
                
        elif any(word in query for word in ["press enter", "hit enter", "enter key", "push enter", "send enter", "enter"]):
            try:
                speak("Pressing enter")
                pyautogui.press('enter')
                time.sleep(0.2)
            except Exception as e:
                speak("Failed to press enter")
                print(f"Enter press error: {e}")

        elif any(word in query for word in ["press escape", "press esc", "escape key", "hit esc", "close menu"]):
            try:
                speak("Pressing escape")
                pyautogui.press('esc')
                time.sleep(0.2)
            except Exception as e:
                speak("Couldn't press escape")
                print(f"Escape press error: {e}")

        elif any(word in query for word in ["press tab", "tab key", "next field", "move focus", "hit tab"]):
            try:
                speak("Pressing tab")
                pyautogui.press('tab')
                time.sleep(0.2)
            except Exception as e:
                speak("Tab press failed")
                print(f"Tab press error: {e}")

        elif any(word in query for word in ["press space", "spacebar", "hit space", "space key", "push space"]):
            try:
                speak("Pressing space")
                pyautogui.press('space')
                time.sleep(0.2)
            except Exception as e:
                speak("Space press didn't work")
                print(f"Space press error: {e}")

        elif any(word in query for word in ["press backspace", "delete left", "erase back", "backspace key", "remove character"]):
            try:
                speak("Pressing backspace")
                pyautogui.press('backspace')
                time.sleep(0.2)
            except Exception as e:
                speak("Backspace failed")
                print(f"Backspace error: {e}")

        elif any(word in query for word in ["press delete", "delete right", "erase forward", "del key", "remove right", "delete"]):
            try:
                speak("Pressing delete")
                pyautogui.press('delete')
                time.sleep(0.2)
            except Exception as e:
                speak("Delete didn't work")
                print(f"Delete error: {e}")

        elif any(word in query for word in ["refresh the page", "refresh page", "reload page", "refresh screen", "reload window", "f5 key"]):
            try:
                speak("Refreshing page")
                pyautogui.press('f5')
                time.sleep(0.5)
            except Exception as e:
                speak("Refresh failed")
                print(f"Refresh error: {e}")

        elif any(word in query for word in ["full screen", "maximize screen", "toggle", "toggle fullscreen", "f11 key", "enter fullscreen"]):
            try:
                speak("Toggling full screen")
                pyautogui.press('f11')
                time.sleep(0.5)
            except Exception as e:
                speak("Full screen toggle failed")
                print(f"Fullscreen error: {e}")

        # Updated Cut Text Command with Selection Check
        elif any(word in query.lower() for word in ["cut text", "cut", "cut selection", "snip text", "copy remove", "cut to clipboard", "remove text", "clip text", "extract text", "cut selected"]):
            try:
                # Check if text is selected by copying to clipboard and checking content
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.1)
                clipboard_content = pyperclip.paste()
                if clipboard_content.strip():
                    speak("Cutting selected text")
                    if sys.platform == 'darwin':
                        pyautogui.hotkey('command', 'x')
                    else:
                        pyautogui.hotkey('ctrl', 'x')
                    time.sleep(0.3)
                else:
                    speak("Please select a text first")
            except Exception as e:
                speak("Cut operation failed")
                print(f"Cut error: {e}")

        # Updated Paste Command with Location Prompt
        elif any(word in query.lower() for word in ["paste", "paste text", "paste clipboard", "insert text", "place text", "paste content", "apply text", "stick text", "paste selection", "put text"]):
            try:
                # Check if clipboard has content
                clipboard_content = pyperclip.paste()
                if clipboard_content.strip():
                    speak("Where would you like to paste? For example, say 'Notepad,' 'Word,' or 'click here'")
                    location = takeCommand().lower()
                    if location and location != "none":
                        if "notepad" in location:
                            speak("Opening Notepad to paste")
                            os.startfile(os.path.expandvars(r"%windir%\system32\notepad.exe"))
                            time.sleep(1)
                            pyautogui.hotkey('ctrl', 'v')
                        elif "word" in location:
                            speak("Please ensure Microsoft Word is open")
                            time.sleep(1)
                            pyautogui.hotkey('ctrl', 'v')
                        elif "click here" in location:
                            speak("Please click where you want to paste")
                            time.sleep(3)
                            pyautogui.hotkey('ctrl', 'v')
                        else:
                            speak("Pasting in the current application")
                            pyautogui.hotkey('ctrl', 'v')
                    else:
                        speak("No location specified. Pasting in the current application")
                        pyautogui.hotkey('ctrl', 'v')
                    time.sleep(0.3)
                else:
                    speak("Nothing to paste. Please copy or cut something first")
            except Exception as e:
                speak("Paste operation failed")
                print(f"Paste error: {e}")

        elif "open camera" in query:
            if not camera_running:
                speak("Opening camera")
                camera_running = True
                threading.Thread(target=run_camera).start()
            else:
                speak("Camera is already open")

        elif "close camera" in query:
            if camera_running:
                speak("Closing camera")
                camera_running = False
            else:
                speak("Camera is not open")
                
        elif any(word in query for word in ["exit full screen", "f11 again", "off screen"]):
            try:
                speak("Turning off full screen")
                pyautogui.press('f11')
                time.sleep(0.5)
            except Exception as e:
                speak("Could not exit fullscreen mode")
                print(f"Exit fullscreen error: {e}")
                
        elif any(cmd in query.lower() for cmd in ["open youtube", "launch youtube", "start youtube", "go to youtube", "youtube please"]):
            speak("Would you like me to search something or play a video?")
            response = takeCommand().lower()
            if any(word in response for word in ['search', 'find', 'look up']):
                speak("What would you like me to search on YouTube?")
                search_query = takeCommand().lower()
                if search_query and search_query != "none":
                    encoded_query = urllib.parse.quote(search_query)
                    webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
                    speak(f"Searching YouTube for {search_query}")
                else:
                    speak("No search query provided. Just opening YouTube.")
                    webbrowser.open('https://www.youtube.com')
            elif any(word in response for word in ['play', 'video', 'song', 'music', 'watch']):
                speak("What would you like me to play?")
                play_query = takeCommand().lower()
                if play_query and play_query != "none":
                    try:
                        wk.playonyt(play_query)
                        speak(f"Playing {play_query} on YouTube")
                    except Exception as e:
                        print(f"Playonyt error: {e}")
                        speak("Sorry, I couldn't play that. Here are search results instead.")
                        encoded_query = urllib.parse.quote(play_query)
                        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
                else:
                    speak("No video specified. Just opening YouTube.")
                    webbrowser.open('https://www.youtube.com')
            else:
                speak("Could not understand. Just opening YouTube.")
                webbrowser.open('https://www.youtube.com')

        elif any(cmd in query.lower() for cmd in ["search on youtube", "youtube search", "find on youtube", "look up on youtube", "search youtube for"]):
            query = re.sub(r'search on youtube|youtube search|find on youtube|look up on youtube|search youtube for', '', query, flags=re.IGNORECASE).strip()
            if query:
                speak(f"Searching YouTube for {query}")
                encoded_query = urllib.parse.quote(query)
                webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
            else:
                speak("What would you like me to search on YouTube?")
                search_query = takeCommand().lower()
                if search_query and search_query != "none":
                    encoded_query = urllib.parse.quote(search_query)
                    webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
                    speak(f"Searching YouTube for {search_query}")
                else:
                    speak("No search query provided. Cancelling YouTube search.")
                    
        elif any(cmd in query.lower() for cmd in ["open search", "press windows s", "search bar", "windows search"]):
            try:
                speak("Opening Windows Search")
                pyautogui.hotkey('win', 's')
                time.sleep(0.5)
            except Exception as e:
                speak("Failed to open Windows Search")
                print(f"Windows Search error: {e}")
                
        elif any(word in query.lower() for word in ["write", "type", "start typing", "typing", "enter text"]):
            try:
                text_to_write = re.sub(r'write|type|enter text', '', query.lower(), flags=re.IGNORECASE).strip()
                if not text_to_write:
                    speak("What would you like me to write?")
                    text_to_write = takeCommand().lower()
                if text_to_write and text_to_write != "none":
                    speak(f"Typing: {text_to_write}")
                    time.sleep(1)
                    pyautogui.write(text_to_write, interval=0.05)
                else:
                    speak("No text provided. Cancelling write operation.")
            except Exception as e:
                speak("Failed to write the text")
                print(f"Write text error: {e}")
                
        elif any(cmd in query.lower() for cmd in ["open chrome", "launch chrome", "start chrome", "run chrome"]):
            try:
                speak("Opening Google Chrome")
                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                if os.path.exists(chrome_path):
                    os.startfile(chrome_path)
                else:
                    webbrowser.open("https://www.google.com")
                    speak("Chrome not found at default location. Opening default browser instead.")
            except Exception as e:
                speak("Sorry, I couldn't open Chrome")
                print(f"Error opening Chrome: {e}")
                
        elif any(cmd in query.lower() for cmd in ["maximize window", "full screen window", "enlarge window", "maximize screen", "maximize", "full screen"]):
            try:
                speak("Maximizing the window")
                pyautogui.hotkey('win', 'up')
                time.sleep(0.3)
            except Exception as e:
                speak("Sorry, I couldn't maximize the window")
                print(f"Error maximizing window: {e}")
                


# ...

        elif any(cmd in query.lower() for cmd in ["open new window", "new window", "open new tab", "new tab"]):
            try:
                speak("Opening a new tab")
                
                # Press Ctrl + T to open a new tab in the active browser
                pyautogui.hotkey('ctrl', 't')
                
                # Small delay to ensure the action completes
                time.sleep(0.5)
                
                speak("New tab opened successfully")
            
            except Exception as e:
                speak("Sorry, I couldn't open a new tab")
                print(f"Error opening new tab: {e}")
                            
        elif any(cmd in query.lower() for cmd in ["previous tab", "go to previous tab", "back tab", "switch to previous tab"]):
            speak("Switching to the previous tab")
            pyautogui.hotkey('ctrl', 'shift', 'tab')
            time.sleep(0.3)
            
        elif any(cmd in query.lower() for cmd in ["open history", "show history", "history page", "view history"]):
            speak("Opening the history page")
            pyautogui.hotkey('ctrl', 'h')
            time.sleep(0.3)
            
        elif any(cmd in query.lower() for cmd in ["open downloads", "show downloads", "downloads page", "view downloads"]):
            speak("Opening the downloads page")
            pyautogui.hotkey('ctrl', 'j')
            time.sleep(0.3)
            
        elif any(cmd in query.lower() for cmd in ["next tab", "go to next tab", "forward tab", "switch to next tab"]):
            speak("Switching to the next tab")
            pyautogui.hotkey('ctrl', 'tab')
            time.sleep(0.3)
            
        elif any(cmd in query.lower() for cmd in ["close tab", "close current tab", "shut tab", "exit tab"]):
            speak("Closing the current tab")
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(0.3)
            
        elif any(cmd in query.lower() for cmd in ["close window", "close browser window", "shut window", "exit window"]):
            speak("Closing the current window")
            pyautogui.hotkey('alt', 'f4')
            time.sleep(0.3)
            
        elif any(cmd in query.lower() for cmd in ["clear browsing history", "delete history", "clear history", "erase history"]):
            try:
                speak("Opening the clear browsing history dialog")
                pyautogui.hotkey('ctrl', 'h')
                time.sleep(1.5)
                pyautogui.hotkey('ctrl', 'shift', 'delete')
                time.sleep(1)
                speak("Please select the time range and confirm to clear the history")
            except Exception as e:
                speak(f"I encountered an error while trying to clear the history: {str(e)}")
                
        elif any(cmd in query.lower() for cmd in ["open start menu", "open windows menu", "start menu", "windows menu", "show start menu", "launch start menu"]):
            try:
                speak("Opening the Start Menu")
                pyautogui.press('win')  # Press Windows key to open Start Menu
                time.sleep(0.5)
                speak("Start Menu opened successfully")
            except Exception as e:
                speak("Sorry, I couldn't open the Start Menu")
                print(f"Error opening Start Menu: {e}")
                logging.error(f"Error opening Start Menu: {e}")
                
        elif any(cmd in query.lower() for cmd in ["open recycle bin", "open trash", "recycle bin", "trash"]):
            try:
                speak("Attempting to open the Recycle Bin")
                os.startfile("shell:RecycleBinFolder")
                time.sleep(0.5)
                speak("Recycle Bin opened successfully")
            except Exception as e:
                speak("Sorry, I couldn't open the Recycle Bin")
                print(f"Error opening Recycle Bin: {e}")
                
        elif any(cmd in query.lower() for cmd in ["open this pc", "open my computer", "this pc", "my computer", "this PC", "open this PC"]):
            try:
                speak("Attempting to open This PC")
                pyautogui.hotkey('win', 'e')
                time.sleep(0.5)
                speak("This PC opened successfully")
            except Exception as e:
                speak("Sorry, I couldn't open This PC")
                print(f"Error opening This PC: {e}")
                
        elif re.search(r"open\s+control\s+panel", query.lower()):
            try:
                speak("Opening Control Panel")
                os.startfile("control")
                time.sleep(0.5)
                speak("Control Panel opened successfully")
            except Exception as e:
                speak("Sorry, I couldn't open Control Panel")
                print(f"Error opening Control Panel: {e}")
                
        elif any(cmd in query.lower() for cmd in ["open drive c", "open local disk c", "drive c", "drive see", "local disk c", "open c drive"]):
            try:
                speak("Attempting to open Drive C")
                os.startfile("C:\\")
                time.sleep(0.5)
                speak("Drive C opened successfully")
            except Exception as e:
                speak("Sorry, I couldn't open Drive C")
                print(f"Error opening Drive C: {e}")

        elif any(cmd in query.lower() for cmd in ["open drive d", "open local disk d", "drive d", "local disk d", "open d drive"]):
            try:
                speak("Attempting to open Drive D")
                os.startfile("D:\\")
                time.sleep(0.5)
                speak("Drive D opened successfully")
            except Exception as e:
                speak("Sorry, I couldn't open Drive D")
                print(f"Error opening Drive D: {e}")

        elif any(cmd in query.lower() for cmd in ["open drive e", "open local disk e", "drive e", "local disk e", "open e drive"]):
            try:
                speak("Attempting to open Drive E")
                os.startfile("E:\\")
                time.sleep(0.5)
                speak("Drive E opened successfully")
            except Exception as e:
                speak("Sorry, I couldn't open Drive E")
                print(f"Error opening Drive E: {e}")
                
        elif any(cmd in query.lower() for cmd in ["open setting", "open settings", "setting", "settings"]):
            try:
                speak("Opening Settings")
                pyautogui.hotkey("win", "i")
                time.sleep(0.5)
                speak("Settings opened successfully")
            except Exception as e:
                speak("Sorry, I couldn't open Settings")
                print(f"Error opening Settings: {e}")
                
        elif any(cmd in query.lower() for cmd in ["switch app", "next app", "switch application"]):
            try:
                speak("Switching to the next application")
                pyautogui.hotkey("alt", "tab")
                time.sleep(0.5)
                speak("Switched to the next application")
            except Exception as e:
                speak("Sorry, I couldn't switch applications")
                print(f"Error switching applications: {e}")
                
        elif any(cmd in query.lower() for cmd in ["shutdown computer", "shut down", "power off"]):
            try:
                speak("Are you sure you want to shut down the computer? Say yes to confirm.")
                time.sleep(3)
                confirmation = takeCommand().lower()
                if "yes" in confirmation:
                    speak("Shutting down the computer in 5 seconds")
                    time.sleep(5)
                    subprocess.run("shutdown /s /t 0", shell=True)
                else:
                    speak("Shutdown cancelled")
            except Exception as e:
                speak("Sorry, I couldn't shut down the computer")
                print(f"Error shutting down: {e}")
                
        elif any(cmd in query.lower() for cmd in ["restart computer", "reboot", "restart"]):
            try:
                speak("Are you sure you want to restart the computer? Say yes to confirm.")
                time.sleep(3)
                confirmation = takeCommand().lower()
                if "yes" in confirmation:
                    speak("Restarting the computer in 5 seconds")
                    time.sleep(5)
                    subprocess.run("shutdown /r /t 0", shell=True)
                else:
                    speak("Restart cancelled")
            except Exception as e:
                speak("Sorry, I couldn't restart the computer")
                print(f"Error restarting: {e}")
                
        elif any(cmd in query.lower() for cmd in ["play media", "pause media", "play pause"]):
            try:
                speak("Toggling play or pause for media")
                pyautogui.press("playpause")
                time.sleep(0.5)
                speak("Media play or pause toggled")
            except Exception as e:
                speak("Sorry, I couldn't toggle media play or pause")
                print(f"Error toggling media: {e}")
                
        elif any(cmd in query.lower() for cmd in ["open downloads", "downloads folder", "open download folder","download"]):
            try:
                print(f"Matched command: open downloads (query: {query})")
                speak("Opening Downloads folder")
                downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
                os.startfile(downloads_path)
                time.sleep(0.5)
                speak("Downloads folder opened successfully")
            except Exception as e:
                speak("Sorry, I couldn't open the Downloads folder")
                print(f"Error opening Downloads folder: {e}")
                
                
        elif any(cmd in query.lower() for cmd in ["check disk space", "disk space", "open disk", "disc space"]):
            try:
                speak("Checking disk space")
                drives = ["C:\\", "D:\\", "E:\\"]
                for drive in drives:
                    usage = shutil.disk_usage(drive)
                    free_gb = usage.free / (1024 ** 3)
                    total_gb = usage.total / (1024 ** 3)
                    speak(f"Drive {drive[0]}: {free_gb:.2f} GB free of {total_gb:.2f} GB")
                    print(f"Drive {drive[0]}: {free_gb:.2f} GB free of {total_gb:.2f} GB")
                time.sleep(0.5)
            except Exception as e:
                speak("Sorry, I couldn't check disk space")
                print(f"Error checking disk space: {e}")
                
        elif any(cmd in query.lower() for cmd in ["increase brightness", "brightness up"]):
            try:
                speak("Increasing screen brightness")
                current_brightness = wmi.WMI(namespace='wmi').WmiMonitorBrightness()[0].CurrentBrightness
                new_brightness = min(current_brightness + 10, 100)
                if set_brightness(new_brightness):
                    time.sleep(0.5)
                    updated_brightness = wmi.WMI(namespace='wmi').WmiMonitorBrightness()[0].CurrentBrightness
                    speak(f"Current brightness: {updated_brightness}%")
                    print(f"Current brightness: {updated_brightness}%")
                else:
                    speak("Sorry, I couldn't increase brightness")
            except Exception as e:
                speak("Sorry, I couldn't increase brightness")
                print(f"Error increasing brightness: {e}")

        elif any(cmd in query.lower() for cmd in ["decrease brightness", "brightness down"]):
            try:
                speak("Decreasing screen brightness")
                current_brightness = wmi.WMI(namespace='wmi').WmiMonitorBrightness()[0].CurrentBrightness
                new_brightness = max(current_brightness - 10, 0)
                if set_brightness(new_brightness):
                    time.sleep(0.5)
                    updated_brightness = wmi.WMI(namespace='wmi').WmiMonitorBrightness()[0].CurrentBrightness
                    speak(f"Brightness decreased to {updated_brightness}%")
                    print(f"Current brightness: {updated_brightness}%")
                else:
                    speak("Sorry, I couldn't decrease brightness")
            except Exception as e:
                speak(f"Error decreasing brightness: {e}")
                print(f"Error decreasing brightness: {e}")
                
        elif any(cmd in query.lower() for cmd in ["create new folder", "new folder"]):
            try:
                print(f"Matched command: create new folder (query: {query})")
                speak("Sure, I can create a new folder for you. What would you like to name it?")
                for attempt in range(2):
                    folder_name = takeCommand().lower()
                    if folder_name and folder_name not in ["none", "timeout", "error"]:
                        break
                    elif attempt == 0:
                        speak("I didn't catch the folder name. Please try again.")
                    else:
                        speak("I still couldn't understand the folder name. Cancelling folder creation.")
                        continue
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                new_folder_path = os.path.join(desktop_path, folder_name)
                if os.path.exists(new_folder_path):
                    speak(f"A folder named '{folder_name}' already exists on the desktop.")
                    print(f"Folder '{folder_name}' already exists at: {new_folder_path}")
                else:
                    os.makedirs(new_folder_path, exist_ok=True)
                    time.sleep(0.5)
                    speak(f"New folder named '{folder_name}' has been created on the desktop.")
                    print(f"Created folder: {new_folder_path}")
            except Exception as e:
                speak("Sorry, I couldn't create the folder.")
                print(f"Error creating folder: {e}")
                    
        
        

           

# ...

        elif any(cmd in query.lower() for cmd in [
    "copy", "copy this", "copy that", "copy selected text", "copy the text",
    "please copy", "copy text","store this text", "get this copied", "i want to copy this", "make a copy of this",
    "select and copy", "copy highlighted text"
]):
            try:
                original_clipboard = pyperclip.paste()

                # Simulate Ctrl+C
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.3)

                copied_text = pyperclip.paste()

                if copied_text == original_clipboard:
                    speak("You did not select any text.")
                    print("No text was selected.")
                else:
                    speak("Text copied successfully.")
                    print("Copied text:", copied_text)

            except Exception as e:
                speak("Sorry, I couldn't copy the text.")
                print(f"Error copying text: {e}")
                
        elif "open" in query and len(query.split()) < 3:
            speak("I heard a request to open something, but I'm not sure what. Could you repeat the full command?")
            query = takeCommand().lower()