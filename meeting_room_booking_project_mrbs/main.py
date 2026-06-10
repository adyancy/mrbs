import tkinter as tk
import db
from app import MeetingRoomBookingApp

if __name__ == "__main__":
    db.setup_db()          # create tables + seed rooms/admin if first run
    root = tk.Tk()
    app = MeetingRoomBookingApp(root)
    root.mainloop()
