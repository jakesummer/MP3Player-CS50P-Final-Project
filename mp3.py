import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
from pygame import mixer
from tinytag import TinyTag
from PIL import Image, ImageTk
import io
import sv_ttk


class MP3Player:
    def __init__(self):
        mixer.init()  # initialize pygame music
        mixer.music.set_volume(1)

        self.ALBUM_COVER_SIZE = 300

        self.file = None
        self.current_song_num = 0

        self.songs = [] # list of songs

        self.is_paused = True
        self.music_ended = False
        self.update_timestamp_after = None

        self.queue_root = None

        #set timestamp defaults
        self.duration = 0
        self.timestamp = 0
        self.updating_timestamp = False

        # set up window
        self.root = tk.Tk()
        self.root.geometry("450x680")
        self.root.resizable(False, False)
        self.root.title("MP3")

        sv_ttk.set_theme("dark")

        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0)

        # song title
        self.title_label = ttk.Label(
            self.root,
            text="No Song Playing",
            wraplength=370,
            justify="center",
        )
        self.title_label.config(font=("Times New Roman", self.title_font_size(self.title_label["text"])))
        self.title_label.grid(row=0, column=1, pady=(25, 0))

        # artist name
        self.artist_label = ttk.Label(
            self.root,
            text=None,
            font=("Times New Roman", 15),
            wraplength=350,
            justify="center",
            foreground="#a1a1a1",
        )
        self.artist_label.grid(row=1, column=1, pady=(5, 10))

        # album cover
        self.default_cover = Image.open("default_cover.png")
        self.default_cover = ImageTk.PhotoImage(self.default_cover.resize((self.ALBUM_COVER_SIZE, self.ALBUM_COVER_SIZE)))
        self.album_cover_label = tk.Label(
            self.root,
            image=self.default_cover,
            highlightbackground="white",
            highlightthickness=4,
        )
        self.album_cover_label.grid(row=2, column=1, sticky="n", pady=(0, 25))

        #frame for play/pause, restart button, and skip to end button
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=3, column=1, sticky="n", pady=(0, 15))

        # play/pause button
        self.play_pause_button = ttk.Button(
            button_frame, text="▶ Play", command=self.toggle_play_pause, width=7.5
        )
        self.play_pause_button.grid(row=0, column=0, padx=10)
        self.play_pause_button.state(["disabled"])

        # restart button
        self.restart_button = ttk.Button(button_frame, text="⟳ Restart", command=self.restart)
        self.restart_button.grid(row=0, column=2, padx=10)
        self.restart_button.state(["disabled"])

        #skip to end button
        self.skip_to_end_button = ttk.Button(button_frame, text="⏯ End", command=self.end_button)
        self.skip_to_end_button.grid(row=0, column=3, padx=10)
        self.skip_to_end_button.state(["disabled"])

        # seeker scale and timestamp label
        seeker_frame = ttk.Frame(self.root, width=308, height=30)
        seeker_frame.grid(row=4, column=1, pady=(0, 5))
        seeker_frame.grid_propagate(False)

        self.seeker_scale = ttk.Scale(seeker_frame, length=263, command=self.seek)
        self.seeker_scale.grid(row=0, column=0)
        self.seeker_scale.state(["disabled"]) # disable scale at start

        self.timestamp_label = ttk.Label(seeker_frame, text=f"00:00")
        self.timestamp_label.grid(row=0, column=1, padx=10)

        #frame for next/previous song buttons and open files buttons
        song_button_frame = ttk.Frame(self.root)
        song_button_frame.grid(row=5, column=1, pady=(0, 15))

        #previous song button
        self.previous_song_button = ttk.Button(song_button_frame, text="⏮", command=self.previous_song)
        self.previous_song_button.grid(row=0, column=0, padx=10)
        self.previous_song_button.state(["disabled"])

        #next song button
        self.next_song_button = ttk.Button(song_button_frame, text="⏭", command=self.next_song)
        self.next_song_button.grid(row=0, column=2, padx=10)
        self.next_song_button.state(["disabled"])

        #add song button
        self.add_song_button = ttk.Button(song_button_frame, text="Add Song", command=self.add_song)
        self.add_song_button.grid(row=0, column=1, padx=10)
        self.add_song_button.state(["disabled"])

        #volume scale and label
        volume_frame = ttk.Frame(self.root)
        volume_frame.grid(row=6, column=1, sticky="n", pady=(0, 15))

        self.volume_label_img = Image.open("volume_scale_cursor.png")
        self.volume_label_img = self.volume_label_img.resize((20, 20))
        self.volume_label_img = ImageTk.PhotoImage(self.volume_label_img)

        self.volume_label = ttk.Label(volume_frame, image=self.volume_label_img)
        self.volume_label.grid(row=0, column=1, padx=10)

        self.volume_scale = ttk.Scale(volume_frame, length=200, command=self.change_volume, value=1.0)
        self.volume_scale.grid(row=0, column=0)

        #frame for open songs button and open queue button
        frame = ttk.Frame(self.root)
        frame.grid(row=7, column=1)

        # open songs button
        self.open_files_button = ttk.Button(frame, text="Select Songs", command=self.open_files)
        self.open_files_button.grid(row=0, column=0, padx=10)

        #open queue button
        self.open_queue_button = ttk.Button(frame, text="View Queue", command=self.open_queue)
        self.open_queue_button.grid(row=0, column=1, padx=10)

        self.root.mainloop()

    def open_files(self):
        files = list(filedialog.askopenfilenames(
            title="Select Songs",
            filetypes=(
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav"),
                ("M4A Files", "*.m4a"),
                ("FLAC Files", "*.flac"),
                ("All Files", "*"),
            ),
        ))

        if len(files) > 0:
            self.songs = [file for file in files if TinyTag.is_supported(file)]
            unsupported_file_count = len(files) - len(self.songs)
            if len(self.songs) == 0: # no supported files
                self.show_error("No supported files!")
            elif unsupported_file_count > 0: # some unsupported files
                self.show_error(f"{unsupported_file_count} unsupported files! Playing {len(self.songs)} songs.")
            
            if len(self.songs) > 0:
                self.current_song_num = 0
                self.play_songs()

    def add_song(self):
        song = filedialog.askopenfilename(
            title="Add a song",
            filetypes=(
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav"),
                ("M4A Files", "*.m4a"),
                ("FLAC Files", "*.flac"),
                ("All Files", "*"),
            ),
        )

        if song:
            if TinyTag.is_supported(song) and song not in self.songs:
                self.songs.append(song)
                self.update_queue()
            elif song in self.songs:
                self.show_error("Song already in queue!")
            elif not TinyTag.is_supported(song):
                self.show_error("File not supported!")

            if self.music_ended == True:
                self.current_song_num = len(self.songs) - 1
                self.play_songs()
    
    def play_songs(self):
        self.file = self.songs[self.current_song_num]
        mixer.music.load(self.file)
        mixer.music.play()

        #enable ui elements
        self.play_pause_button.state(["!disabled"])
        self.restart_button.state(["!disabled"])
        self.skip_to_end_button.state(["!disabled"])
        self.seeker_scale.state(["!disabled"])
        self.previous_song_button.state(["!disabled"])
        self.next_song_button.state(["!disabled"])
        self.add_song_button.state(["!disabled"])

        self.update_queue()

        self.play_pause_button.config(text="⏸ Pause")
        self.music_ended = False
        self.is_paused = False
        self.timestamp = 0
        self.cancel_timestamp_after()
        self.config_gui_elements(self.file)

    def config_gui_elements(self, file=None, restart=False):
        if file:
            metadata = self.get_song_metadata(file)

            self.title_label.config(
                text=metadata["song"],
                font=("Times New Roman", self.title_font_size(metadata["song"])),
            )

            self.artist_label.config(text=metadata["artist"])

            self.duration = metadata["duration"]
            self.timestamp_label.config(text=self.format_time(self.duration))
            self.update_timestamp()

            if image_bytes := metadata["album_art"]:
                image = Image.open(io.BytesIO(image_bytes))
                image = image.resize((self.ALBUM_COVER_SIZE, self.ALBUM_COVER_SIZE))

                self.album_photo = ImageTk.PhotoImage(image)

                self.album_cover_label.config(image=self.album_photo)
            else:
                self.album_photo = ImageTk.PhotoImage(self.default_cover)

    def get_song_metadata(self, file):
        tag = TinyTag.get(file, image=True)

        image_data = None
        if tag.images.front_cover:
            image_data = tag.images.front_cover.data

        return {
            "artist": tag.artist,
            "song": tag.title,
            "year": tag.year,
            "album_art": image_data,
            "duration": tag.duration,
        }

    def toggle_play_pause(self):
        if len(self.songs) > 0 and not self.music_ended:
            if self.is_paused:
                self.play_pause_button.config(text="⏸ Pause")
                self.is_paused = False
                mixer.music.unpause()
                self.update_timestamp()
            else:
                self.play_pause_button.config(text="▶ Play")
                self.is_paused = True
                mixer.music.pause()
                self.cancel_timestamp_after()
        elif self.music_ended and self.timestamp == 0.0: #music ended; user pressed play so restart
            self.restart()
        elif self.music_ended and self.timestamp > 0.0: #music ended but user seeked to part of song so play at that part
            mixer.music.load(self.file)
            mixer.music.play(start=self.timestamp)
            self.play_pause_button.config(text="⏸ Pause")
            self.music_ended = False
            self.is_paused = False
            self.update_timestamp()

    def seek(self, seek_timestamp): #change position in song
        seek_timestamp = float(seek_timestamp)
        seconds = seek_timestamp * self.duration
        if not self.updating_timestamp and not self.music_ended and mixer.music.get_busy() and seek_timestamp != 1.0 and not self.is_paused:
            self.timestamp = seconds
            mixer.music.set_pos(seconds)
        elif seek_timestamp == 1.0 and not self.music_ended: #skipped to end of song:
            if mixer.music.get_busy():
                mixer.music.set_pos(self.duration)
            self.music_ended = True
            self.end_song()
        elif self.music_ended and seek_timestamp != 1.0: # music ended but user is seeking
            self.timestamp = seconds
            self.timestamp_label.config(text=self.format_time(self.duration-self.timestamp))
        elif self.is_paused and not self.music_ended: #user skipped while song was paused
            self.timestamp = seconds
            mixer.music.set_pos(seconds)
            self.timestamp_label.config(text=self.format_time(self.duration-self.timestamp))
    
    def update_timestamp(self):
        if self.timestamp < self.duration and mixer.music.get_busy() and not self.is_paused:
            self.timestamp += 1
            seconds_left = self.duration - self.timestamp
            self.timestamp_label.config(text=self.format_time(seconds_left))

            self.updating_timestamp = True
            self.seeker_scale.set(value=self.timestamp/self.duration)
            self.updating_timestamp = False

        if not mixer.music.get_busy(): # music ended
            self.end_song()
        
        if not self.music_ended and not self.is_paused:
            self.update_timestamp_after = self.root.after(1000, self.update_timestamp) #repeat every second (1000 milliseconds)
    
    def restart(self):
        if self.current_song_num == len(self.songs):
            self.current_song_num = 0
            self.play_songs()
            return

        if len(self.songs) > 0:
            if self.music_ended:
                mixer.music.load(self.file)
                mixer.music.play(start=self.timestamp)
                self.play_pause_button.config(text="⏸ Pause")
                self.music_ended = False
                self.is_paused = False
            else:
                self.cancel_timestamp_after()
                mixer.music.rewind()
                self.updating_timestamp = True
                self.seeker_scale.set(0.0)
                self.updating_timestamp = False
            
            self.timestamp = 0.0
            self.update_timestamp()

    def end_song(self):
        self.cancel_timestamp_after()
        if self.current_song_num < (len(self.songs) - 1): # there are songs left to play
            self.current_song_num += 1
            self.root.after(500, self.play_songs)
        else: # no songs left to play
            self.title_label.config(text="All songs finished playing", font=("Times New Roman", self.title_font_size("All songs finished playing")))
            self.artist_label.config(text="")
            self.timestamp_label.config(text="00:00")
            self.album_cover_label.config(image=self.default_cover)

            if mixer.music.get_busy():
                mixer.music.stop()

            self.root.after_cancel(self.update_timestamp_after)
            self.seeker_scale.set(0.0)
            
            #disable ui elements
            self.skip_to_end_button.state(["disabled"])
            self.seeker_scale.state(["disabled"])
            self.next_song_button.state(["disabled"])

            self.updating_timestamp = True
            self.seeker_scale.set(1.0)
            self.updating_timestamp = False

            self.music_ended = True
            self.is_paused = True
            self.play_pause_button.config(text="▶ Play")
            self.timestamp = 0.0
            self.current_song_num = len(self.songs)

            self.update_queue()

    def previous_song(self):
        if len(self.songs) > 0:
            if self.current_song_num - 1 >= 0 or self.music_ended:
                self.current_song_num -= 1
                self.play_songs()
            else:
                self.restart()
    
    def next_song(self):
        if len(self.songs) > 0:
            if self.current_song_num + 1 < len(self.songs):
                self.current_song_num += 1
                self.play_songs()
            else:
                self.end_song()

    def end_button(self):
        if len(self.songs) > 0:
            self.current_song_num = len(self.songs)
            self.end_song()

    def show_error(self, message):
        self.error_label = ttk.Label(
            self.root, text=message, foreground="red", font=("Times New Roman", 15)
        )
        self.error_label.grid(row=6, column=1, pady=(0, 10))

        self.root.after(3000, self.error_label.destroy)

    def change_volume(self, volume):
        mixer.music.set_volume(float(volume))

    def open_queue(self):
        if self.queue_root and self.queue_root.winfo_exists: # if window already exists bring it to front
            if self.queue_root.state() == "iconic": # if window is minimized, bring it back
                self.queue_root.deiconify()
            self.queue_root.lift()
            self.queue_root.focus_force()
            return

        self.queue_root = tk.Toplevel()
        self.queue_root.geometry("300x350")
        self.queue_root.resizable(False, False)
        self.queue_root.title("Song Queue")

        self.queue_root.protocol("WM_DELETE_WINDOW", self.close_queue)

        sv_ttk.set_theme("dark")

        self.queue_root.columnconfigure(0, weight=1)
        self.queue_root.rowconfigure(0, weight=1)

        # canvas and scrollbar
        canvas = tk.Canvas(self.queue_root, borderwidth=0)
        scrollbar = ttk.Scrollbar(self.queue_root, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # frame with buttons inside canvas
        self.queue_frame = ttk.Frame(canvas)
        self.queue_frame.columnconfigure(0, weight=1)

        self.canvas_window = canvas.create_window((0, 0), window=self.queue_frame, anchor="nw")

        def resize_frame(event): #make frame width equal canvas width
            canvas.itemconfig(self.canvas_window, width=event.width)
        canvas.bind("<Configure>", resize_frame)
        
        self.queue_frame.bind("<Configure>", lambda a: canvas.configure(scrollregion=canvas.bbox("all")))
            
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.load_queue()

    def load_queue(self):
        for widget in self.queue_frame.winfo_children(): #clear all old widgets
            widget.destroy()

        for i, song in enumerate(self.songs):
            song_name = TinyTag.get(song).title

            if i == self.current_song_num:
                text = f"⇒ {song_name}"
            else:
                text = f"{song_name}"

            button = ttk.Button(self.queue_frame, text=text, command=lambda index=i: self.change_song(index))
            button.grid(row=i, column=0, sticky="ew", pady=2)

    def close_queue(self):
        self.queue_root.destroy()
        self.queue_root = None

    def change_song(self, song_num): # change song when user clicks it in queue
        self.current_song_num = song_num
        self.play_songs()

    def format_time(self, seconds):
        seconds = int(seconds)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def title_font_size(self, text):
        return max(25 - (len(text) - 25) // 2, 13)
    
    def cancel_timestamp_after(self): #cancel after statement in update_timestamp
        if self.update_timestamp_after:
            self.root.after_cancel(self.update_timestamp_after)

    def update_queue(self):
        try:
            self.load_queue()
        except AttributeError:
            pass



if __name__ == "__main__":
    MP3Player()
