import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import instaloader
import re
import os
import requests
from io import BytesIO
import pyperclip
import threading

# Create the Instaloader instance
loader = instaloader.Instaloader()

# Global variables for carousel index and URL entry
image_list = []
image_index = 0
url_entry = None  # Placeholder for URL entry widget
current_window = None  # To keep track of the current window
progress_bar = None  # Global variable for progress bar


# Function to extract shortcode from URL
def extract_shortcode(url):
    post_pattern = re.compile(r"instagram\.com/p/([^/]+)/")
    reel_pattern = re.compile(r"instagram\.com/reel/([^/]+)/")
    story_pattern = re.compile(r"instagram\.com/stories/([^/]+)/([^/]+)")

    post_match = post_pattern.search(url)
    if post_match:
        return post_match.group(1), 'post'

    reel_match = reel_pattern.search(url)
    if reel_match:
        return reel_match.group(1), 'reel'

    story_match = story_pattern.search(url)
    if story_match:
        return story_match.group(1), 'story'

    return None, None


# Function to select the folder where the content will be saved
def choose_directory():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        path_label.config(text=folder_selected)
    return folder_selected


# Function to display post image in the window
def display_post_image(image_url):
    try:
        response = requests.get(image_url)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img.thumbnail((200, 200))
        img_tk = ImageTk.PhotoImage(img)

        post_image_label.config(image=img_tk)
        post_image_label.image = img_tk  # Keep a reference to avoid garbage collection

        # Show carousel navigation buttons if it's a post
        if 'carousel_frame' in globals():
            prev_button.pack(side=tk.LEFT, padx=5)
            next_button.pack(side=tk.LEFT, padx=5)

    except Exception as e:
        status_label.config(text=f"Error loading image: {e}")


# Function to display carousel images in the window (slidable)
def display_carousel_images():
    global image_index
    if image_list:
        display_post_image(image_list[image_index])


# Move to next image in carousel
def next_image():
    global image_index
    if image_list:
        image_index = (image_index + 1) % len(image_list)
        display_carousel_images()


# Move to previous image in carousel
def previous_image():
    global image_index
    if image_list:
        image_index = (image_index - 1) % len(image_list)
        display_carousel_images()


# Function to download content and handle carousel images
def download_from_link():
    global image_list, image_index
    url = url_entry.get()
    save_folder = path_label.cget("text")

    if not url or not save_folder:
        status_label.config(text="Please enter a valid URL and select a folder.")
        return

    shortcode, content_type = extract_shortcode(url)
    if not shortcode:
        status_label.config(text="The URL is not valid for posts, reels, or stories.")
        return

    # Update the UI to show the progress bar
    progress_bar['value'] = 0
    progress_bar.pack(pady=10)
    root.update_idletasks()

    def download_task():
        try:
            if content_type == 'post':
                post = instaloader.Post.from_shortcode(loader.context, shortcode)
                image_list = [post.url] + [node.display_url for node in post.get_sidecar_nodes()]
                image_index = 0

                # Hide carousel navigation buttons initially
                if 'carousel_frame' in globals():
                    prev_button.pack_forget()
                    next_button.pack_forget()

                # Display the first image
                display_carousel_images()

                # Download all images in carousel or single image post
                total_images = len(image_list)
                for i, image_url in enumerate(image_list):
                    img_data = requests.get(image_url).content
                    img_filename = os.path.join(save_folder, f'{shortcode}_{i}.jpg')
                    with open(img_filename, 'wb') as img_file:
                        img_file.write(img_data)

                    # Update progress bar
                    progress = (i + 1) / total_images * 100
                    progress_bar['value'] = progress
                    root.update_idletasks()

                status_label.config(text=f"Post downloaded successfully!")

            elif content_type == 'reel':
                post = instaloader.Post.from_shortcode(loader.context, shortcode)
                selected_option = reel_option_var.get()  # Get the selected option

                if selected_option == 'cover_image':
                    # Handle cover image download
                    cover_image_url = post.url
                    if cover_image_url:
                        cover_image_data = requests.get(cover_image_url).content
                        cover_image_filename = os.path.join(save_folder, f'{shortcode}_cover.jpg')
                        with open(cover_image_filename, 'wb') as cover_image_file:
                            cover_image_file.write(cover_image_data)

                        # Update progress bar
                        progress_bar['value'] = 50
                        root.update_idletasks()

                    status_label.config(text=f"Reel cover image downloaded successfully!")

                elif selected_option == 'full_reel':
                    # Handle full reel download (video + cover image)
                    video_url = post.video_url
                    if video_url:
                        video_data = requests.get(video_url).content
                        video_filename = os.path.join(save_folder, f'{shortcode}.mp4')
                        with open(video_filename, 'wb') as video_file:
                            video_file.write(video_data)

                        # Update progress bar
                        progress_bar['value'] = 75
                        root.update_idletasks()

                    # Download the reel cover image
                    cover_image_url = post.url
                    if cover_image_url:
                        cover_image_data = requests.get(cover_image_url).content
                        cover_image_filename = os.path.join(save_folder, f'{shortcode}_cover.jpg')
                        with open(cover_image_filename, 'wb') as cover_image_file:
                            cover_image_file.write(cover_image_data)

                        # Final update to progress bar
                        progress_bar['value'] = 100
                        root.update_idletasks()

                    status_label.config(text=f"Reel downloaded successfully!")

                elif selected_option == 'reel_only':
                    # Handle downloading only the reel (video)
                    video_url = post.video_url
                    if video_url:
                        video_data = requests.get(video_url).content
                        video_filename = os.path.join(save_folder, f'{shortcode}.mp4')
                        with open(video_filename, 'wb') as video_file:
                            video_file.write(video_data)

                        # Final update to progress bar
                        progress_bar['value'] = 100
                        root.update_idletasks()

                    status_label.config(text=f"Reel video downloaded successfully!")

            elif content_type == 'story':
                profile = instaloader.Profile.from_username(loader.context, shortcode)
                loader.download_stories(userids=[profile.userid], filename_target=save_folder)
                status_label.config(text=f"Stories of {profile.username} downloaded successfully!")

        except Exception as e:
            status_label.config(text=f"Error downloading {content_type}: {e}")
        finally:
            # Hide the progress bar after download completes
            progress_bar.pack_forget()

    # Run download task in a separate thread
    threading.Thread(target=download_task).start()


# Function to paste the link from the clipboard into the entry field
def paste_link():
    clipboard_content = pyperclip.paste()
    if url_entry:  # Ensure url_entry is defined
        url_entry.delete(0, tk.END)
        url_entry.insert(0, clipboard_content)


# Function to show the main menu window
def show_main_window():
    global current_window
    if current_window:
        current_window.destroy()

    global main_window
    main_window = tk.Tk()
    main_window.title("Instagram Downloader - Main Page")
    main_window.geometry("300x200")

    # Option selection
    option_var = tk.StringVar(value='post')  # Default to 'post'

    tk.Label(main_window, text="Select content type to download:").pack(pady=10)

    tk.Radiobutton(main_window, text="Post", variable=option_var, value='post').pack(pady=5)
    tk.Radiobutton(main_window, text="Reel", variable=option_var, value='reel').pack(pady=5)

    tk.Button(main_window, text="Open Downloader", command=lambda: open_downloader_window(option_var.get())).pack(
        pady=20)

    # Run the main page window
    current_window = main_window
    main_window.mainloop()


# Function to open the downloader window
def open_downloader_window(selected_option):
    global current_window
    if current_window:
        current_window.destroy()

    global root
    root = tk.Tk()
    root.title("Instagram Downloader")
    root.geometry("500x600")

    # Instagram link input section
    global url_entry
    url_label = tk.Label(root, text="Paste Instagram link here:")
    url_label.pack(pady=5)

    url_entry = tk.Entry(root, width=40)
    url_entry.pack(pady=5)

    # Create a frame for the "Paste Link" and "Download" buttons side by side
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    # Paste link button
    paste_button = tk.Button(button_frame, text="Paste Link", command=paste_link, width=15)
    paste_button.pack(side=tk.LEFT, padx=5)

    # Download button
    download_button = tk.Button(button_frame, text="Download", command=download_from_link, width=15)
    download_button.pack(side=tk.LEFT, padx=5)

    # Select folder section
    folder_button = tk.Button(root, text="Select Folder", command=choose_directory, width=15)
    folder_button.pack(pady=5)

    # Display chosen path
    global path_label
    path_label = tk.Label(root, text="No folder selected", fg="gray")
    path_label.pack(pady=5)

    # Label for displaying the status (success or error messages)
    global status_label
    status_label = tk.Label(root, text="", fg="green")
    status_label.pack(pady=5)

    # Label to display the post image or first carousel image
    global post_image_label
    post_image_label = tk.Label(root)
    post_image_label.pack(pady=10)

    # Conditionally create carousel frame and buttons only if 'post' is selected
    global carousel_frame
    if selected_option == 'post':
        carousel_frame = tk.Frame(root)
        carousel_frame.pack(pady=5)

        global prev_button, next_button
        prev_button = tk.Button(carousel_frame, text="Previous", command=previous_image, width=10)
        next_button = tk.Button(carousel_frame, text="Next", command=next_image, width=10)

        # Initially hide the carousel navigation buttons
        prev_button.pack_forget()
        next_button.pack_forget()

    if selected_option == 'reel':
        # Radio buttons for reel download options
        global reel_option_var
        reel_option_var = tk.StringVar(value='cover_image')  # Default to cover image

        reel_option_frame = tk.Frame(root)
        reel_option_frame.pack(pady=10)

        cover_image_radio = tk.Radiobutton(reel_option_frame, text="Cover Image", variable=reel_option_var,
                                           value='cover_image')
        cover_image_radio.pack(side=tk.LEFT, padx=5)

        full_reel_radio = tk.Radiobutton(reel_option_frame, text="Full Reel (Video + Cover Image)",
                                         variable=reel_option_var, value='full_reel')
        full_reel_radio.pack(side=tk.LEFT, padx=5)

        reel_only_radio = tk.Radiobutton(reel_option_frame, text="Reel Only (Video)",
                                         variable=reel_option_var, value='reel_only')
        reel_only_radio.pack(side=tk.LEFT, padx=5)

    # Progress bar for download progress
    global progress_bar
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=10)
    progress_bar.pack_forget()  # Initially hidden

    # Main Menu button
    main_menu_button = tk.Button(root, text="Main Menu", command=show_main_window, width=15)
    main_menu_button.pack(pady=10)

    # Run the downloader window
    current_window = root
    root.mainloop()


# Initialize the application
show_main_window()
