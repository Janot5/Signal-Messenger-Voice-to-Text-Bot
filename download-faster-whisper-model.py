import os
from faster_whisper import WhisperModel, download_model

# Define the directory path
model_dir_path = "whisper_model"

# Create the directory if it does not exist
if not os.path.exists(model_dir_path):
    os.makedirs(model_dir_path)
    print(f"Directory '{model_dir_path}' created.")
else:
    print(f"Directory '{model_dir_path}' already exists.")

# Download the large model to the directory, you could also use medium or small
model_dir = download_model("large-v3", output_dir=model_dir_path)
model = WhisperModel(model_dir)
