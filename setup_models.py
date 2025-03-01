import os
import sys
import zipfile
import tempfile
from urllib.request import urlretrieve
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

class ModelDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vosk Model Downloader")
        self.root.geometry("600x400")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions label
        ttk.Label(main_frame, text="Download a Vosk speech recognition model:", font=('Arial', 12)).pack(pady=5)

        
        # Model selection frame
        select_frame = ttk.LabelFrame(main_frame, text="Select Model", padding=5)
        select_frame.pack(fill=tk.X, pady=5)
        
        # Model options
        self.model_var = tk.StringVar(value="vosk-model-small-en-us-0.15")
        
        models = [
            ("Small English (80MB)", "vosk-model-small-en-us-0.15"),
            ("Medium English (500MB)", "vosk-model-en-us-0.22"),
            ("Large English (1.8GB)", "vosk-model-en-us-0.42")
        ]
        
        for i, (text, value) in enumerate(models):
            ttk.Radiobutton(select_frame, text=text, value=value, 
                           variable=self.model_var).grid(row=i, column=0, sticky=tk.W, padx=20)
        
        # Location frame
        location_frame = ttk.LabelFrame(main_frame, text="Download Location", padding=5)
        location_frame.pack(fill=tk.X, pady=5)
        
        # Default models directory
        self.models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        
        # Location entry
        self.location_var = tk.StringVar(value=self.models_dir)
        ttk.Entry(location_frame, textvariable=self.location_var, width=50).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(location_frame, text="Browse", command=self.browse_location).pack(side=tk.LEFT, padx=5, pady=5)


        # add donwload button
        ttk.Button(main_frame, text="Download", command=self.download_model).pack(pady=10)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=5)
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # Log text area
        self.log = ScrolledText(progress_frame, height=10)
        self.log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Download button
        self.download_button = ttk.Button(main_frame, text="Download", command=self.download_model)
        self.download_button.pack(pady=10)
    
    def browse_location(self):
        directory = tk.filedialog.askdirectory(initialdir=self.models_dir, 
                                             title="Select download location")
        if directory:
            self.location_var.set(directory)
    
    def log_message(self, message):
        self.log.configure(state='normal')
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state='disabled')
        self.root.update()
    
    def download_model(self):
        model_name = self.model_var.get()
        download_dir = self.location_var.get()
        
        # Create directory if it doesn't exist
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create directory: {e}")
                return
        
        self.log_message(f"Downloading {model_name}...")
        self.download_button.configure(state='disabled')
        
        # Download URL
        url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
        
        try:
            # Progress callback
            def progress_callback(count, block_size, total_size):
                percentage = count * block_size * 100 / total_size
                self.progress['value'] = min(percentage, 100)
                self.root.update()
            
            # Download file
            temp_zip = os.path.join(tempfile.gettempdir(), f"{model_name}.zip")
            self.log_message(f"Downloading from {url}")
            urlretrieve(url, temp_zip, progress_callback)
            
            # Extract zip
            self.log_message("Download complete. Extracting files...")
            self.progress['value'] = 0
            
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                # Get total size for progress calculation
                total_size = sum(file.file_size for file in zip_ref.infolist())
                extracted_size = 0
                
                for file in zip_ref.infolist():
                    zip_ref.extract(file, download_dir)
                    extracted_size += file.file_size
                    self.progress['value'] = min(extracted_size * 100 / total_size, 100)
                    self.root.update()
            
            os.remove(temp_zip)
            
            self.log_message(f"Model extracted to {download_dir}")
            self.log_message("Setup complete! You can now start the transcription app.")
            
            messagebox.showinfo("Download Complete", 
                               f"Model {model_name} has been downloaded and extracted successfully.")
            
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        finally:
            self.download_button.configure(state='normal')

def main():
    root = tk.Tk()
    app = ModelDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
