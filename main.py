import tkinter as tk
from tkinter import messagebox, filedialog
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageTk
import os
import fitz  # PyMuPDF
import math

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)


class VisualSecurityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Visual Security Lock - PDF Protector")
        self.root.geometry("1000x1000")
        self.settings = {"lock_type": "number", "password": "", "pdf_path": ""}
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Choose Lock Type:").pack(pady=10)
        self.lock_type_var = tk.StringVar(value="number")
        tk.Radiobutton(self.root, text="Number Lock", variable=self.lock_type_var, value="number").pack()
        tk.Radiobutton(self.root, text="Pattern Lock", variable=self.lock_type_var, value="pattern").pack()

        tk.Label(self.root, text="Set Password (e.g., 1234):").pack(pady=10)
        self.pass_entry = tk.Entry(self.root)
        self.pass_entry.pack()

        tk.Button(self.root, text="Select PDF to Protect", command=self.select_pdf).pack(pady=10)
        tk.Button(self.root, text="Start Lock", command=self.start_lock).pack(pady=10)

    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.settings["pdf_path"] = path
            messagebox.showinfo("PDF Selected", f"Selected: {os.path.basename(path)}")

    def start_lock(self):
        password = self.pass_entry.get()
        if not password.isdigit():
            messagebox.showerror("Error", "Only digit passwords supported for now.")
            return
        if not self.settings["pdf_path"]:
            messagebox.showerror("Error", "Please select a PDF first.")
            return
        self.settings["lock_type"] = self.lock_type_var.get()
        self.settings["password"] = password
        self.root.withdraw()
        self.show_camera_window()

    def show_camera_window(self):
        self.cam_window = tk.Toplevel()
        self.cam_window.title("Unlock PDF")
        self.canvas = tk.Canvas(self.cam_window, width=640, height=480)
        self.canvas.pack()
        self.entered_code = []
        self.video_loop()

    def get_buttons(self, lock_type):
        if lock_type == "number":
            positions = []
            for i in range(9):
                x = 150 + (i % 3) * 100
                y = 100 + (i // 3) * 100
                positions.append((x, y, str(i+1)))
            return positions
        return []

    def video_loop(self):
        cap = cv2.VideoCapture(0)
        def loop():
            ret, frame = cap.read()
            if not ret:
                return
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)
            h, w, _ = frame.shape
            fingertip = None

            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    x = int(hand_landmarks.landmark[8].x * w)
                    y = int(hand_landmarks.landmark[8].y * h)
                    fingertip = (x, y)
                    cv2.circle(frame, fingertip, 10, (255, 0, 0), -1)

            self.buttons = self.get_buttons(self.settings["lock_type"])
            for bx, by, val in self.buttons:
                cv2.rectangle(frame, (bx - 40, by - 40), (bx + 40, by + 40), (0, 255, 0), 2)
                cv2.putText(frame, str(val), (bx - 15, by + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                if fingertip:
                    dist = math.hypot(fingertip[0] - bx, fingertip[1] - by)
                    if dist < 40:
                        if len(self.entered_code) < len(self.settings["password"]) and                             (len(self.entered_code) == 0 or self.entered_code[-1] != val):
                            self.entered_code.append(str(val))
                            print("Touched:", val)
                            if "".join(self.entered_code) == self.settings["password"]:
                                messagebox.showinfo("Unlocked", "Access Granted!")
                                cap.release()
                                self.open_pdf()
                                return
                            elif len(self.entered_code) == len(self.settings["password"]):
                                messagebox.showerror("Failed", "Access Denied!")
                                self.entered_code.clear()

            rgb_final = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_final)
            imgtk = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.imgtk = imgtk
            self.cam_window.after(10, loop)
        loop()

    def open_pdf(self):
        os.startfile(self.settings["pdf_path"])

if __name__ == "__main__":
    root = tk.Tk()
    app = VisualSecurityApp(root)
    root.mainloop()
