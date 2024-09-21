from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image
import os


def hide_text_in_image(image_path, message, output_path):
    image = Image.open(image_path)
    encoded_image = image.copy()
    width, height = image.size
    idx = 0

    # Convert message to binary
    binary_message = ''.join([format(ord(i), '08b') for i in message])
    binary_message += '1111111111111110'  # End-of-message marker

    # Encode the message in the image
    for y in range(height):
        for x in range(width):
            pixel = list(encoded_image.getpixel((x, y)))
            for n in range(3):  # Iterate through the R, G, B values
                if idx < len(binary_message):
                    pixel[n] = pixel[n] & ~1 | int(binary_message[idx])
                    idx += 1
            encoded_image.putpixel((x, y), tuple(pixel))
            if idx >= len(binary_message):
                break
        if idx >= len(binary_message):
            break

    encoded_image.save(output_path)
    messagebox.showinfo("Success", f"Text successfully hidden in {output_path}")


def extract_text_from_image(image_path):
    image = Image.open(image_path)
    width, height = image.size
    binary_message = ''

    for y in range(height):
        for x in range(width):
            pixel = list(image.getpixel((x, y)))
            for n in range(3):  # Iterate through the R, G, B values
                binary_message += str(pixel[n] & 1)

    # Split by 8 bits and convert back to characters
    message = ''.join([chr(int(binary_message[i:i + 8], 2)) for i in range(0, len(binary_message), 8)])
    end_of_message = message.find('þ')  # End-of-message marker
    return message[:end_of_message]


def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
    return file_path


def open_text_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    return file_path


def hide_text():
    image_path = open_file()
    message = text_input.get("1.0", END)
    output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
    if image_path and message and output_path:
        hide_text_in_image(image_path, message, output_path)


def hide_text_from_file():
    image_path = open_file()
    file_path = open_text_file()
    if file_path:
        with open(file_path, 'r') as file:
            message = file.read()
    output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
    if image_path and message and output_path:
        hide_text_in_image(image_path, message, output_path)


def extract_text():
    image_path = open_file()
    if image_path:
        extracted_message = extract_text_from_image(image_path)
        messagebox.showinfo("Extracted Text", extracted_message)


# GUI Setup
root = Tk()
root.title("Steganography Tool")

# Text Input
Label(root, text="Enter text to hide:").pack(pady=5)
text_input = Text(root, height=5, width=40)
text_input.pack(pady=5)

# Buttons
Button(root, text="Hide Text in Image", command=hide_text).pack(pady=5)
Button(root, text="Hide Text File in Image", command=hide_text_from_file).pack(pady=5)
Button(root, text="Extract Text from Image", command=extract_text).pack(pady=5)

root.geometry("400x300")
root.mainloop()
