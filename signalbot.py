#!/usr/bin/env python3.10
import os
import subprocess
import time
import re
from faster_whisper import WhisperModel

#whisper model:
model_size = "large-v3"
#model = WhisperModel(model_size, device="cpu", compute_type="int8")
model = WhisperModel("large-v3", device="cpu", compute_type="int8")


# Your phone number
PHONE_NUMBER = "+"


def transcribe_audio(audio_file):
    print(f"Transcribing audio file: {audio_file}")
    segments, info = model.transcribe(audio_file, beam_size=5)
    result = ""
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    for segment in segments:
        result += ("[%.2fs -> %.2fs] %s\n" % (segment.start, segment.end, segment.text))
    subprocess.run(['whisper', audio_file, '--output_format', 'txt', '--output_dir', '/dev/null'], capture_output=True, text=True)
    transcript = result
    print(f"Transcript: {transcript}")
    return transcript

def handle_message(sender, attachment_path, message_timestamp, content_type, attachment_id, is_video=False):
    print(f"Handling message from: {sender}")

    # Send read receipt
    print(f"Sending read receipt to: {sender} for message timestamp: {message_timestamp}")
    subprocess.run([
        'signal-cli', '-u', PHONE_NUMBER, 'sendReceipt', '-t', message_timestamp, '--type', 'read', sender
    ], check=True)


    # Extract audio if it's a video
    if is_video:
        audio_file = os.path.splitext(attachment_path)[0] + '.wav'
        print(f"Converting video to audio: {audio_file}")
        subprocess.run(['ffmpeg', '-i', attachment_path, '-q:a', '0', '-map', 'a', audio_file], check=True)
    else:
        audio_file = attachment_path

    # Transcribe the audio
    transcript = transcribe_audio(audio_file)
    print(f"Transcript: {transcript}")

    # Send the cleaned transcript back as a reply
    quote_attachment = f"{content_type}:{attachment_id}"
    print(f"Sending transcript back to: {sender} as a reply to message timestamp: {message_timestamp} with attachment: {quote_attachment}")
    subprocess.run([
        'signal-cli', '-u', PHONE_NUMBER, 'send', '-m', transcript, sender, 
        '--quote-timestamp', message_timestamp, '--quote-author', sender,
        '--quote-attachment', quote_attachment
    ], check=True)



def main():
    # Capture the output of signal-cli receive
    result = subprocess.run(['signal-cli', '-u', PHONE_NUMBER, 'receive'], capture_output=True, text=True)
    messages = result.stdout.strip()

    # Debug: Print the raw messages
    print(f"Raw messages: {messages}")

    if messages:
        # Split the messages by "Envelope from" to handle multiple messages
        envelopes = messages.split("Envelope from:")
        for envelope in envelopes:
            if envelope.strip():
                # Extract sender and attachment details using regex
                sender_match = re.search(r'“([^”]+)” \+(\d+) \(device: \d+\) to \+(\d+)', envelope)
                attachment_match = re.search(r'Stored plaintext in: (/.+)', envelope)
                message_timestamp_match = re.search(r'Message timestamp: (\d+)', envelope)
                content_type_match = re.search(r'Content-Type: ([^ ]+)', envelope)
                attachment_id_match = re.search(r'Id: ([^\s]+)', envelope)

                if sender_match and message_timestamp_match and content_type_match and attachment_id_match:
                    sender_name = sender_match.group(1)
                    sender_number = "+" + sender_match.group(2)
                    recipient_number = "+" + sender_match.group(3)
                    message_timestamp = message_timestamp_match.group(1)
                    content_type = content_type_match.group(1)
                    attachment_id = attachment_id_match.group(1)

                    print(f"Sender: {sender_name} {sender_number}")
                    print(f"Recipient: {recipient_number}")
                    print(f"Message Timestamp: {message_timestamp}")
                    print(f"Content Type: {content_type}")
                    print(f"Attachment ID: {attachment_id}")

                    if attachment_match:
                        attachment_path = attachment_match.group(1)
                        is_video = 'video message' in envelope
                        handle_message(sender_number, attachment_path, message_timestamp, content_type, attachment_id, is_video)
                    else:
                        print("No attachment found.")
                else:
                    print("No valid sender information, message timestamp, content type, or attachment ID found.")


if __name__ == "__main__":
    main()

