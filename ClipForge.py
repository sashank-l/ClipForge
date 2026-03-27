import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import pandas as pd
from datetime import datetime
import threading
import os


class VideoClipMarker:
    def __init__(self, root):
        self.root = root
        self.root.title("ClipForge ~ By Kunal Sinha")
        self.root.geometry("1100x650")
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

        # Video variables
        self.cap = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.video_width = 0
        self.video_height = 0
        self.playback_speed = 1
        self.is_playing = False
        self.updating_slider = False

        # Clip marking variables
        self.start_frame = None
        self.start_time = None
        self.end_frame = None
        self.end_time = None
        self.clips = []
        self.clip_counter = 1

        # File paths
        self.video_path = tk.StringVar()
        self.save_path = tk.StringVar()

        self.setup_ui()

    def setup_ui(self):
        # Top Section - File Paths and Action Buttons
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # File Paths (left)
        paths_frame = tk.Frame(top_frame)
        paths_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Video Path
        tk.Label(paths_frame, text="Video Path:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        tk.Entry(paths_frame, textvariable=self.video_path, width=50).grid(
            row=0, column=1, padx=5
        )
        tk.Button(paths_frame, text="Browse", command=self.browse_video).grid(
            row=0, column=2, padx=2
        )
        tk.Button(
            paths_frame, text="Load", command=self.load_video, bg="#4CAF50", fg="white"
        ).grid(row=0, column=3, padx=2)

        # Save Path
        tk.Label(paths_frame, text="Save Path:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        tk.Entry(paths_frame, textvariable=self.save_path, width=50).grid(
            row=1, column=1, padx=5
        )
        tk.Button(paths_frame, text="Browse", command=self.browse_save_path).grid(
            row=1, column=2, padx=2
        )
        tk.Button(
            paths_frame,
            text="Load History",
            command=self.load_history,
            bg="#9C27B0",
            fg="white",
        ).grid(row=1, column=3, padx=2)

        # Action Buttons (right)
        actions_frame = tk.Frame(top_frame)
        actions_frame.pack(side=tk.RIGHT, padx=20)

        tk.Button(
            actions_frame,
            text="💾 Save All Clips & Export CSV",
            command=self.save_all_clips,
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=10,
        ).pack(pady=5)
        tk.Button(
            actions_frame,
            text="🗑️ Delete Selected Clip",
            command=self.delete_selected_clip,
            font=("Arial", 10),
            bg="#f44336",
            fg="white",
            padx=20,
            pady=5,
        ).pack()

        # Main Section - Split into Left and Right
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # LEFT SIDE PANEL
        left_panel = tk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Video Player
        player_frame = tk.LabelFrame(
            left_panel, text="Video Player", font=("Arial", 10, "bold")
        )
        player_frame.pack(fill=tk.BOTH, pady=2)

        self.canvas = tk.Canvas(player_frame, width=512, height=288, bg="black")
        self.canvas.pack(pady=2)

        # Controls Section
        controls_frame = tk.LabelFrame(
            left_panel, text="Controls", font=("Arial", 10, "bold")
        )
        controls_frame.pack(fill=tk.X, pady=5)

        # Play/Pause
        btn_frame = tk.Frame(controls_frame)
        btn_frame.pack(pady=5)

        self.play_btn = tk.Button(
            btn_frame,
            text="▶ Play",
            command=self.toggle_play,
            font=("Arial", 10),
            width=10,
            bg="#4CAF50",
            fg="white",
        )
        self.play_btn.pack(side=tk.LEFT, padx=5)

        # Speed Controls
        speed_frame = tk.Frame(btn_frame)
        speed_frame.pack(side=tk.LEFT, padx=20)

        tk.Label(speed_frame, text="Speed:", font=("Arial", 9)).pack(
            side=tk.LEFT, padx=5
        )
        for speed in [-16, -8, -4, -3, -2, -1, 1, 2, 3, 4, 8, 16]:
            tk.Button(
                speed_frame,
                text=f"{speed}x",
                command=lambda s=speed: self.set_speed(s),
                width=4,
                font=("Arial", 8),
            ).pack(side=tk.LEFT, padx=2)

        self.speed_label = tk.Label(
            speed_frame, text="→ 1x", font=("Arial", 10, "bold"), fg="#2196F3"
        )
        self.speed_label.pack(side=tk.LEFT, padx=10)

        # Timeline
        timeline_frame = tk.Frame(controls_frame)
        timeline_frame.pack(fill=tk.X, padx=10, pady=5)

        self.timeline = tk.Scale(
            timeline_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self.seek_video,
            showvalue=False,
        )
        self.timeline.pack(fill=tk.X)

        self.time_label = tk.Label(
            timeline_frame, text="00:00:00.000 / 00:00:00.000", font=("Arial", 10)
        )
        self.time_label.pack()

        # Clip Marking Section
        marking_frame = tk.LabelFrame(
            left_panel, text="Clip Marking", font=("Arial", 10, "bold")
        )
        marking_frame.pack(fill=tk.X, pady=5)

        mark_btn_frame = tk.Frame(marking_frame)
        mark_btn_frame.pack(pady=5)

        tk.Button(
            mark_btn_frame,
            text="⏺ Mark Start",
            command=self.mark_start,
            font=("Arial", 10),
            bg="#FF9800",
            fg="white",
            width=15,
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            mark_btn_frame,
            text="⏹ Mark End",
            command=self.mark_end,
            font=("Arial", 10),
            bg="#f44336",
            fg="white",
            width=15,
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            mark_btn_frame,
            text="✖ Clear Current",
            command=self.clear_current,
            font=("Arial", 10),
            width=15,
        ).pack(side=tk.LEFT, padx=5)

        mark_info_frame = tk.Frame(marking_frame)
        mark_info_frame.pack(pady=5)

        self.start_label = tk.Label(
            mark_info_frame, text="Start: Not marked", font=("Arial", 10), fg="green"
        )
        self.start_label.pack(side=tk.LEFT, padx=20)

        self.end_label = tk.Label(
            mark_info_frame, text="End: Not marked", font=("Arial", 10), fg="red"
        )
        self.end_label.pack(side=tk.LEFT, padx=20)

        # Metadata Section - Single Row
        metadata_frame = tk.LabelFrame(
            left_panel, text="Metadata", font=("Arial", 10, "bold")
        )
        metadata_frame.pack(fill=tk.X, pady=5)

        metadata_row = tk.Frame(metadata_frame)
        metadata_row.pack(fill=tk.X, padx=5, pady=10)

        # Add metadata fields in single row
        fields = [
            ("Action Class:", "action_class", 15),
            ("Description:", "description", 25),
            ("Team:", "team", 15),
            ("Equipment:", "equipment", 15),
        ]

        self.metadata_vars = {}
        col_idx = 0
        for label, var_name, width in fields:
            tk.Label(metadata_row, text=label, font=("Arial", 9)).grid(
                row=0, column=col_idx, sticky=tk.W, padx=5
            )
            var = tk.StringVar()
            tk.Entry(metadata_row, textvariable=var, width=width).grid(
                row=0, column=col_idx + 1, padx=5
            )
            self.metadata_vars[var_name] = var
            col_idx += 2

        # RIGHT SIDE PANEL - Reduced width
        right_panel = tk.Frame(main_frame, width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        right_panel.pack_propagate(False)

        # Action History (reduced proportion)
        history_frame = tk.LabelFrame(
            right_panel, text="Action History", font=("Arial", 10, "bold")
        )
        history_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 5))

        history_container = tk.Frame(history_frame, height=200)
        history_container.pack(fill=tk.BOTH, expand=False)
        history_container.pack_propagate(False)

        history_scrollbar = tk.Scrollbar(history_container)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_text = tk.Text(
            history_container,
            width=40,
            yscrollcommand=history_scrollbar.set,
            state=tk.DISABLED,
        )
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.config(command=self.history_text.yview)

        # Marked Clips List (extended)
        clips_frame = tk.LabelFrame(
            right_panel, text="Marked Clips", font=("Arial", 10, "bold")
        )
        clips_frame.pack(fill=tk.BOTH, expand=True)

        clips_container = tk.Frame(clips_frame)
        clips_container.pack(fill=tk.BOTH, expand=True)

        clips_scrollbar = tk.Scrollbar(clips_container)
        clips_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("Clip Name", "Start Time", "End Time", "Action Class", "Description")
        self.clips_tree = ttk.Treeview(
            clips_container,
            columns=columns,
            show="headings",
            yscrollcommand=clips_scrollbar.set,
        )

        for col in columns:
            self.clips_tree.heading(col, text=col)
            width = 100 if col != "Description" else 120
            self.clips_tree.column(col, width=width)

        self.clips_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        clips_scrollbar.config(command=self.clips_tree.yview)

        self.log_action("Application started")

    def log_action(self, action):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        message = f"{timestamp} {action}\n"

        # Display in history text widget
        self.history_text.config(state=tk.NORMAL)
        self.history_text.insert(tk.END, message)
        self.history_text.config(state=tk.DISABLED)
        self.history_text.see(tk.END)

        # Save to log file
        if self.save_path.get() and self.video_path.get():
            video_name = os.path.splitext(os.path.basename(self.video_path.get()))[0]
            export_folder = os.path.join(self.save_path.get(), f"{video_name}_clips")

            if not os.path.exists(export_folder):
                os.makedirs(export_folder)

            log_file = os.path.join(export_folder, "actions_log.txt")
            try:
                with open(log_file, "a") as f:
                    f.write(message)
            except Exception as e:
                print(f"Error writing to log: {e}")

    def load_history(self):
        if not self.save_path.get() or not self.video_path.get():
            messagebox.showerror(
                "Error", "Please select a save directory and load a video first"
            )
            return

        video_name = os.path.splitext(os.path.basename(self.video_path.get()))[0]
        export_folder = os.path.join(self.save_path.get(), f"{video_name}_clips")

        csv_path = os.path.join(export_folder, "clips_metadata.csv")
        log_path = os.path.join(export_folder, "actions_log.txt")

        # Load CSV if exists
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)

                # Clear existing clips
                self.clips = []
                for item in self.clips_tree.get_children():
                    self.clips_tree.delete(item)

                # Load clips from CSV
                for _, row in df.iterrows():
                    clip_data = {
                        "clip_name": row["Clip Name"],
                        "start_frame": None,  # Frame info not in CSV
                        "end_frame": None,
                        "start_time": row["Start Time Stamp"],
                        "end_time": row["End Time Stamp"],
                        "action_class": row["Action Class ID"],
                        "description": row["Description"],
                        "team": row["Team"],
                        "equipment": row["Equipment"],
                    }
                    self.clips.append(clip_data)

                    # Add to treeview
                    self.clips_tree.insert(
                        "",
                        tk.END,
                        values=(
                            clip_data["clip_name"],
                            clip_data["start_time"],
                            clip_data["end_time"],
                            clip_data["action_class"],
                            clip_data["description"],
                        ),
                    )

                # Update clip counter
                if len(self.clips) > 0:
                    # Extract the highest clip number
                    clip_numbers = []
                    for clip in self.clips:
                        try:
                            # Extract number from "clip_X.mp4"
                            num = int(
                                clip["clip_name"]
                                .replace("clip_", "")
                                .replace(".mp4", "")
                            )
                            clip_numbers.append(num)
                        except:
                            pass

                    if clip_numbers:
                        self.clip_counter = max(clip_numbers) + 1

                self.log_action(f"Loaded {len(self.clips)} clips from history")
                messagebox.showinfo(
                    "Success", f"Loaded {len(self.clips)} clips from history"
                )

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV: {str(e)}")
                self.log_action(f"Error loading history: {str(e)}")
        else:
            messagebox.showinfo("Info", "No history file found. Starting fresh.")
            self.log_action("No history file found")

        # Load action log if exists
        if os.path.exists(log_path):
            try:
                with open(log_path, "r") as f:
                    log_content = f.read()
                    self.history_text.config(state=tk.NORMAL)
                    self.history_text.delete(1.0, tk.END)
                    self.history_text.insert(tk.END, log_content)
                    self.history_text.config(state=tk.DISABLED)
                    self.history_text.see(tk.END)
            except Exception as e:
                print(f"Error loading log: {e}")

    def browse_video(self):
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mkv *.mov"),
                ("All Files", "*.*"),
            ],
        )
        if filename:
            self.video_path.set(filename)

    def browse_save_path(self):
        directory = filedialog.askdirectory(title="Select Save Directory")
        if directory:
            self.save_path.set(directory)

            if self.video_path.get():
                video_name = os.path.splitext(os.path.basename(self.video_path.get()))[
                    0
                ]
                export_folder = os.path.join(directory, f"{video_name}_clips")
                # Auto-load history if available
                csv_path = os.path.join(export_folder, "clips_metadata.csv")
                if os.path.exists(csv_path):
                    response = messagebox.askyesno(
                        "History Found",
                        "Found existing clip history for this video. Load it?",
                    )
                    if response:
                        self.load_history()

    def load_video(self):
        if not self.video_path.get():
            messagebox.showerror("Error", "Please select a video file first")
            return

        if not os.path.exists(self.video_path.get()):
            messagebox.showerror("Error", "Video file does not exist")
            return

        self.cap = cv2.VideoCapture(self.video_path.get())

        if not self.cap.isOpened():
            messagebox.showerror("Error", "Failed to open video file")
            return

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.timeline.config(to=self.total_frames - 1)
        self.current_frame = 0

        self.display_frame()
        self.update_time_display()

        self.log_action(
            f"Video loaded: {os.path.basename(self.video_path.get())} "
            f"({self.total_frames} frames, {self.fps:.2f} FPS)"
        )

    def frames_to_time(self, frame_num):
        if self.fps == 0:
            return "00:00:00.000"

        total_seconds = frame_num / self.fps
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int((total_seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

    def display_frame(self):
        if self.cap is None:
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (512, 288))

            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.image = imgtk

    def update_time_display(self):
        current_time = self.frames_to_time(self.current_frame)
        total_time = self.frames_to_time(self.total_frames)
        self.time_label.config(text=f"{current_time} / {total_time}")

        self.updating_slider = True
        self.timeline.set(self.current_frame)
        self.updating_slider = False

    def seek_video(self, value):
        if self.updating_slider or self.cap is None:
            return

        self.current_frame = int(float(value))
        self.display_frame()
        self.update_time_display()

    def toggle_play(self):
        if self.cap is None:
            messagebox.showerror("Error", "Please load a video first")
            return

        self.is_playing = not self.is_playing

        if self.is_playing:
            self.play_btn.config(text="⏸ Pause")
            self.play_video()
        else:
            self.play_btn.config(text="▶ Play")

    def play_video(self):
        if self.is_playing and self.cap is not None:
            if self.playback_speed > 0:
                self.current_frame += abs(self.playback_speed)
                if self.current_frame >= self.total_frames:
                    self.current_frame = self.total_frames - 1
                    self.is_playing = False
                    self.play_btn.config(text="▶ Play")
            else:
                self.current_frame -= abs(self.playback_speed)
                if self.current_frame < 0:
                    self.current_frame = 0
                    self.is_playing = False
                    self.play_btn.config(text="▶ Play")

            self.display_frame()
            self.update_time_display()

            if self.is_playing:
                delay = int(1000 / (self.fps * abs(self.playback_speed)))
                self.root.after(delay, self.play_video)

    def set_speed(self, speed):
        self.playback_speed = speed
        arrow = "←" if speed < 0 else "→"
        self.speed_label.config(text=f"{arrow} {abs(speed)}x")
        self.log_action(f"Speed changed to {speed}x")

    def mark_start(self):
        if self.cap is None:
            messagebox.showerror("Error", "Please load a video first")
            return

        self.start_frame = self.current_frame
        self.start_time = self.frames_to_time(self.start_frame)
        self.start_label.config(text=f"Start: {self.start_time}")
        self.log_action(f"Start marked at {self.start_time}")

    def mark_end(self):
        if self.cap is None:
            messagebox.showerror("Error", "Please load a video first")
            return

        if self.start_frame is None:
            messagebox.showerror("Error", "Please mark start first")
            return

        self.end_frame = self.current_frame

        if self.end_frame <= self.start_frame:
            messagebox.showerror("Error", "End frame must be after start frame")
            return

        self.end_time = self.frames_to_time(self.end_frame)
        self.end_label.config(text=f"End: {self.end_time}")

        # Collect metadata
        clip_name = f"clip_{self.clip_counter}.mp4"
        action_class = self.metadata_vars["action_class"].get()
        description = self.metadata_vars["description"].get()
        team = self.metadata_vars["team"].get()
        equipment = self.metadata_vars["equipment"].get()

        # Store clip
        clip_data = {
            "clip_name": clip_name,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "action_class": action_class,
            "description": description,
            "team": team,
            "equipment": equipment,
        }

        self.clips.append(clip_data)

        # Add to treeview
        self.clips_tree.insert(
            "",
            tk.END,
            values=(
                clip_name,
                self.start_time,
                self.end_time,
                action_class,
                description,
            ),
        )

        self.log_action(
            f"Clip marked: {clip_name} ({self.start_time} - {self.end_time})"
        )

        self.clip_counter += 1
        self.clear_current()

    def clear_current(self):
        self.start_frame = None
        self.start_time = None
        self.end_frame = None
        self.end_time = None

        self.start_label.config(text="Start: Not marked")
        self.end_label.config(text="End: Not marked")

        for var in self.metadata_vars.values():
            var.set("")

    def delete_selected_clip(self):
        selection = self.clips_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a clip to delete")
            return

        item = selection[0]
        values = self.clips_tree.item(item, "values")
        clip_name = values[0]

        # Remove from list
        self.clips = [c for c in self.clips if c["clip_name"] != clip_name]

        # Remove from treeview
        self.clips_tree.delete(item)

        self.log_action(f"Clip deleted: {clip_name}")

    def save_all_clips(self):
        if not self.clips:
            messagebox.showwarning("Warning", "No clips to save")
            return

        if not self.save_path.get():
            messagebox.showerror("Error", "Please select a save directory")
            return

        if self.cap is None:
            messagebox.showerror("Error", "No video loaded")
            return

        save_dir = self.save_path.get()

        # Create a dedicated folder for all clips from this video
        video_name = os.path.splitext(os.path.basename(self.video_path.get()))[0]
        export_folder = os.path.join(save_dir, f"{video_name}_clips")

        if not os.path.exists(export_folder):
            os.makedirs(export_folder)

        try:
            # Save video clips
            for i, clip in enumerate(self.clips, 1):
                output_path = os.path.join(export_folder, clip["clip_name"])

                # Skip if clip already exists
                if os.path.exists(output_path):
                    self.log_action(
                        f"Clip already exists, skipped: {clip['clip_name']}"
                    )
                    continue

                # Create new VideoCapture for extraction
                temp_cap = cv2.VideoCapture(self.video_path.get())
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                out = cv2.VideoWriter(
                    output_path, fourcc, self.fps, (self.video_width, self.video_height)
                )

                temp_cap.set(cv2.CAP_PROP_POS_FRAMES, clip["start_frame"])

                for frame_num in range(clip["start_frame"], clip["end_frame"] + 1):
                    ret, frame = temp_cap.read()
                    if ret:
                        out.write(frame)
                    else:
                        break

                temp_cap.release()
                out.release()

                self.log_action(
                    f"Clip saved: {clip['clip_name']} in folder {export_folder}"
                )

            # Create CSV
            csv_data = []
            for i, clip in enumerate(self.clips, 1):
                csv_data.append(
                    {
                        "S.No": i,
                        "Clip Name": clip["clip_name"],
                        "Action Class ID": clip["action_class"],
                        "Start Time Stamp": clip["start_time"],
                        "End Time Stamp": clip["end_time"],
                        "Description": clip["description"],
                        "Team": clip["team"],
                        "Equipment": clip["equipment"],
                    }
                )

            df = pd.DataFrame(csv_data)
            csv_path = os.path.join(export_folder, "clips_metadata.csv")
            df.to_csv(csv_path, index=False)

            self.log_action(f"CSV exported: clips_metadata.csv")

            messagebox.showinfo(
                "Success",
                f"All clips and metadata saved successfully!\n"
                f"Location: {export_folder}",
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save clips: {str(e)}")
            self.log_action(f"Error saving clips: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoClipMarker(root)
    root.mainloop()
