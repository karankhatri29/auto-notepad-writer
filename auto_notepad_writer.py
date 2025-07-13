# auto_notepad_writer.py
import pyautogui
import time
import subprocess
import psutil
import speech_recognition as sr
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
import queue
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoNotepadWriter:
    def __init__(self):
        self.is_listening = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.text_queue = queue.Queue()
        self.notepad_process = None
        
        # Adjust for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
    def open_notepad(self):
        """Open Notepad application."""
        try:
            # Check if Notepad is already running
            for proc in psutil.process_iter(['pid', 'name']):
                if 'notepad' in proc.info['name'].lower():
                    logger.info("Notepad is already running")
                    return True
            
            # Open new Notepad instance
            self.notepad_process = subprocess.Popen(['notepad.exe'])
            time.sleep(2)  # Wait for Notepad to open
            
            # Focus on Notepad window
            pyautogui.click(500, 300)  # Click in the middle of screen
            logger.info("Notepad opened successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open Notepad: {e}")
            return False
    
    def type_text(self, text):
        """Type text into the active window (Notepad)."""
        try:
            # Add timestamp
            timestamp = time.strftime("[%H:%M:%S] ")
            full_text = f"{timestamp}{text}\n"
            
            # Type the text
            pyautogui.typewrite(full_text, interval=0.02)
            logger.info(f"Typed: {text}")
            
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
    
    def listen_continuously(self):
        """Continuously listen for speech and convert to text."""
        while self.is_listening:
            try:
                # Listen for audio
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Convert speech to text
                try:
                    text = self.recognizer.recognize_google(audio)
                    if text.strip():
                        self.text_queue.put(text)
                        logger.info(f"Recognized: {text}")
                        
                except sr.UnknownValueError:
                    # Speech was unintelligible
                    pass
                except sr.RequestError as e:
                    logger.error(f"Speech recognition error: {e}")
                    
            except sr.WaitTimeoutError:
                # No speech detected, continue listening
                pass
            except Exception as e:
                logger.error(f"Error in speech recognition: {e}")
                time.sleep(1)
    
    def process_text_queue(self):
        """Process text from the queue and type it."""
        while True:
            try:
                text = self.text_queue.get(timeout=0.1)
                self.type_text(text)
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Error processing text: {e}")
            time.sleep(0.1)
    
    def start_listening(self):
        """Start the speech recognition process."""
        if not self.is_listening:
            self.is_listening = True
            
            # Start listening thread
            self.listen_thread = threading.Thread(target=self.listen_continuously, daemon=True)
            self.listen_thread.start()
            
            # Start text processing thread
            self.process_thread = threading.Thread(target=self.process_text_queue, daemon=True)
            self.process_thread.start()
            
            logger.info("Started listening for speech...")
            return True
        return False
    
    def stop_listening(self):
        """Stop the speech recognition process."""
        self.is_listening = False
        logger.info("Stopped listening for speech")
    
    def type_manual_text(self, text):
        """Manually type text (for GUI input)."""
        if text.strip():
            self.type_text(text)

class NotepadWriterGUI:
    def __init__(self):
        self.writer = AutoNotepadWriter()
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI interface."""
        self.root = tk.Tk()
        self.root.title("Auto Notepad Writer")
        self.root.geometry("500x400")
        self.root.configure(bg="#f0f0f0")
        
        # Title
        title_label = tk.Label(self.root, text="Auto Notepad Writer", 
                              font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
        
        # Status
        self.status_label = tk.Label(self.root, text="Status: Ready", 
                                    font=("Arial", 10), bg="#f0f0f0", fg="green")
        self.status_label.pack(pady=5)
        
        # Control buttons frame
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(pady=10)
        
        # Open Notepad button
        self.open_btn = tk.Button(control_frame, text="Open Notepad", 
                                 command=self.open_notepad, bg="#4CAF50", fg="white",
                                 font=("Arial", 10, "bold"))
        self.open_btn.pack(side=tk.LEFT, padx=5)
        
        # Start/Stop listening buttons
        self.start_btn = tk.Button(control_frame, text="Start Listening", 
                                  command=self.start_listening, bg="#2196F3", fg="white",
                                  font=("Arial", 10, "bold"))
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(control_frame, text="Stop Listening", 
                                 command=self.stop_listening, bg="#f44336", fg="white",
                                 font=("Arial", 10, "bold"))
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Manual text input
        manual_frame = tk.Frame(self.root, bg="#f0f0f0")
        manual_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(manual_frame, text="Manual Text Input:", 
                font=("Arial", 12, "bold"), bg="#f0f0f0").pack(anchor=tk.W)
        
        self.text_area = scrolledtext.ScrolledText(manual_frame, height=8, width=50,
                                                  font=("Arial", 10))
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Type manual text button
        self.type_btn = tk.Button(manual_frame, text="Type This Text", 
                                 command=self.type_manual_text, bg="#FF9800", fg="white",
                                 font=("Arial", 10, "bold"))
        self.type_btn.pack(pady=5)
        
        # Instructions
        instructions = tk.Label(self.root, 
                               text="Instructions:\n1. Click 'Open Notepad' to open Notepad\n2. Click 'Start Listening' to begin voice typing\n3. Speak clearly into your microphone\n4. Use manual input for specific text",
                               font=("Arial", 9), bg="#f0f0f0", justify=tk.LEFT)
        instructions.pack(pady=10, padx=20)
        
    def open_notepad(self):
        """Open Notepad through the writer."""
        if self.writer.open_notepad():
            self.status_label.config(text="Status: Notepad opened", fg="green")
            messagebox.showinfo("Success", "Notepad opened successfully!")
        else:
            self.status_label.config(text="Status: Failed to open Notepad", fg="red")
            messagebox.showerror("Error", "Failed to open Notepad")
    
    def start_listening(self):
        """Start listening for speech."""
        if self.writer.start_listening():
            self.status_label.config(text="Status: Listening for speech...", fg="blue")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            messagebox.showinfo("Started", "Started listening for speech. Speak into your microphone!")
        else:
            messagebox.showwarning("Warning", "Already listening!")
    
    def stop_listening(self):
        """Stop listening for speech."""
        self.writer.stop_listening()
        self.status_label.config(text="Status: Stopped listening", fg="orange")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        messagebox.showinfo("Stopped", "Stopped listening for speech")
    
    def type_manual_text(self):
        """Type the manual text input."""
        text = self.text_area.get("1.0", tk.END).strip()
        if text:
            self.writer.type_manual_text(text)
            self.text_area.delete("1.0", tk.END)
            messagebox.showinfo("Success", "Text typed successfully!")
        else:
            messagebox.showwarning("Warning", "Please enter some text first!")
    
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()

# Simple command-line version
def simple_voice_to_notepad():
    """Simple command-line version for quick use."""
    writer = AutoNotepadWriter()
    
    print("Auto Notepad Writer - Simple Mode")
    print("=" * 40)
    
    # Open Notepad
    print("Opening Notepad...")
    if not writer.open_notepad():
        print("Failed to open Notepad!")
        return
    
    print("Notepad opened successfully!")
    print("Starting voice recognition...")
    
    # Start listening
    writer.start_listening()
    
    print("\nListening for your speech...")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        writer.stop_listening()
        print("Stopped listening. Goodbye!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        # Run simple command-line version
        simple_voice_to_notepad()
    else:
        # Run GUI version
        app = NotepadWriterGUI()
        app.run()