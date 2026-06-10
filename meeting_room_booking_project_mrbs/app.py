import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os

import db

BG     = "#2b2b2b"   # window background
CARD   = "#403a3a"   # card / panel background
CARD2  = "#504a4a"   # input field background
TEXT   = "#e36767"   # main text colour
MUTED  = "#888888"   # secondary / hint text
ACCENT = "#c04f4f"   # highlight (buttons, selection)
BORD   = "#605a5a"   # border / outline colour
BTN    = "#555a5e"   # default button background

def _round_rect(canvas, x1, y1, x2, y2, r=20, **kw):
    """Draw a smooth rounded rectangle on a canvas widget."""
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
    ]
    canvas.create_polygon(pts, smooth=True, **kw)


def _btn(parent, text, command, accent=False, big=False):
    """Create a flat styled button."""
    bg  = ACCENT if accent else BTN
    abg = "#993a3a" if accent else ACCENT
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg="grey" if accent else TEXT,
        activebackground=abg, activeforeground="grey",
        relief="flat", bd=0,
        font=("Arial", 15 if big else 13),
        cursor="hand2",
        padx=18, pady=10 if big else 7,
    )


def _entry(parent, show=None):
    """Create a styled single-line text input."""
    return tk.Entry(
        parent,
        bg=CARD2, fg=TEXT, insertbackground=TEXT,
        relief="flat", font=("Arial", 13),
        highlightthickness=1,
        highlightbackground=BORD,
        highlightcolor=ACCENT,
        show=show or "",
    )


def _lbl(parent, text, size=13, bold=False, muted=False):
    """Create a styled label."""
    return tk.Label(
        parent, text=text,
        font=("Arial", size, "bold" if bold else "normal"),
        bg=parent.cget("bg"),
        fg=MUTED if muted else TEXT,
    )









class MeetingRoomBookingApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Meeting Room Booking System")
        self.root.geometry("1350x900")
        self.root.minsize(1100, 760)
        self.root.configure(bg=BG)

        self._setup_ttk_style()

        self.current_user = None   # set to a user dict after login
        self.show_login_page()

    # Apply dark theme to ttk widgets

    def _setup_ttk_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(".",                background=BG,    foreground=TEXT, font=("Arial", 13))
        style.configure("TFrame",           background=BG)
        style.configure("TLabel",           background=BG,    foreground=TEXT)
        style.configure("TLabelframe",      background=BG,    bordercolor=BORD)
        style.configure("TLabelframe.Label",background=BG,    foreground=TEXT, font=("Arial", 13, "bold"))
        style.configure("TEntry",           fieldbackground=CARD2, foreground=TEXT, borderwidth=1)
        style.configure("TButton",          background=BTN,   foreground=TEXT, padding=(14, 9), borderwidth=0, relief="flat")
        style.map("TButton",                background=[("active", ACCENT), ("pressed", "#993a3a")])
        style.configure("Treeview",         background=CARD,  foreground=TEXT, fieldbackground=CARD, rowheight=30, font=("Arial", 12))
        style.configure("Treeview.Heading", background=CARD2, foreground=TEXT, font=("Arial", 12, "bold"))
        style.map("Treeview",               background=[("selected", ACCENT)])
        style.configure("TCombobox",        fieldbackground=CARD2, foreground=TEXT, selectbackground=ACCENT)

    # Shared utilities

    def clear_window(self):
        """Remove every widget from the window so we can build a new page."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def _card(self, parent, w, h, r=22):
        """
        Build a rounded card. Returns (canvas, inner_frame).
        Put your widgets inside inner_frame.
        """
        c = tk.Canvas(parent, width=w, height=h, bg=BG, highlightthickness=0)
        _round_rect(c, 1, 1, w-1, h-1, r=r, fill=CARD, outline=BORD)
        f = tk.Frame(c, bg=CARD)
        c.create_window(w // 2, h // 2, window=f, width=w - 36, height=h - 36)
        return c, f

    def _top_bar(self, back_command):
        """Add a top bar with a Back button. Used on every page except Login/Signup."""
        bar = tk.Frame(self.root, bg=CARD, pady=10, padx=16)
        bar.pack(fill="x")
        _btn(bar, "← Back", back_command).pack(side="left")

    def _page_title(self, title):
        """Show a large page title below the top bar."""
        tk.Label(self.root, text=title, font=("Arial", 22, "bold"),
                  bg=BG, fg=TEXT).pack(pady=14)

    def _make_table(self, parent, columns):
        """Create a scrollable table (Treeview) with the given column names."""
        t = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        for col in columns:
            t.heading(col, text=col)
            t.column(col, width=130, anchor="center")
        sy = ttk.Scrollbar(parent, orient="vertical",   command=t.yview)
        sx = ttk.Scrollbar(parent, orient="horizontal", command=t.xview)
        t.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        t.pack(side="left", fill="both", expand=True)
        sy.pack(side="right",  fill="y")
        sx.pack(side="bottom", fill="x")
        return t

    def _load_rooms_into_table(self, table):
        """Clear a table and fill it with current room data."""
        for row in table.get_children():
            table.delete(row)
        for room in db.get_rooms():
            table.insert("", "end", values=[
                room["roomID"], room["roomName"],
                room["capacity"], room["availabilityStatus"]
            ])

    def _load_bookings_into_table(self, table):
        """Clear a table and fill it with current booking data."""
        for row in table.get_children():
            table.delete(row)
        for b in db.get_bookings():
            table.insert("", "end", values=[
                b["bookingID"], b["userID"], b["employeeName"], b["roomID"],
                b["bookingDate"], b["startTime"], b["endTime"],
                b["bookingPurpose"], b["bookingStatus"]
            ])

    def logout(self):
        self.current_user = None
        self.show_login_page()






    # PAGE 1 LOGIN

    def show_login_page(self):
        self.clear_window()
        self.root.bind("<Return>", lambda _: self._handle_login())

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(expand=True)

        c, f = self._card(outer, 480, 430, r=26)
        c.pack(pady=30)

        _lbl(f, "Meeting Room Booking System", 21, bold=True).pack(pady=(24, 6))
        _lbl(f, "Login to continue", 13, muted=True).pack(pady=(0, 22))

        # User ID field
        r1 = tk.Frame(f, bg=CARD)
        r1.pack(fill="x", padx=22, pady=6)
        _lbl(r1, "User ID").pack(anchor="w")
        self.login_userID = _entry(r1)
        self.login_userID.pack(fill="x", pady=(5, 0), ipady=6)

        # Password field
        r2 = tk.Frame(f, bg=CARD)
        r2.pack(fill="x", padx=22, pady=6)
        _lbl(r2, "Password").pack(anchor="w")
        self.login_password = _entry(r2, show="*")
        self.login_password.pack(fill="x", pady=(5, 0), ipady=6)

        bf = tk.Frame(f, bg=CARD)
        bf.pack(fill="x", padx=22, pady=(20, 6))
        _btn(bf, "Login", self._handle_login, accent=True, big=True).pack(fill="x", pady=(0, 10))
        tk.Button(
            bf, text="Sign Up to Create a new account",
            command=self.show_signup_page,
            bg=BG, fg=MUTED, activebackground=CARD2, activeforeground=TEXT,
            relief="flat", font=("Arial", 12), cursor="hand2", bd=0,
        ).pack(fill="x")

        self.login_userID.focus()

    def _handle_login(self):
        uid = self.login_userID.get().strip()
        pwd = self.login_password.get().strip()

        # secret easter egg login - doesnt go thru the normal databse cheack
        if uid == "bfdi" and pwd == "battle for dream island":
            self.root.unbind("<Return>")
            self.show_easter_egg_page()
            return

        user = db.login(uid, pwd)
        if not user:
            messagebox.showerror("Login Failed", "Invalid User ID or password.")
            return
        self.current_user = user
        self.root.unbind("<Return>")
        self.show_home_page()



    # EASTER EGG PAGE secret bfdi login

    def show_easter_egg_page(self):
        self.clear_window()

        outer = tk.Frame(self.root, bg="#1a1a2e")  # dark bg for the suprise page
        outer.pack(expand=True, fill="both")

        # load the image from the assets folder
        img_path = os.path.join("assets", "easter_egg.png")
        try:
            # pillow isnt always avaliable so we try the built in way first
            from PIL import Image, ImageTk
            img = Image.open(img_path)
            img = img.resize((520, 520), Image.LANCZOS)  # rezise to fit nicly
            self._easter_img = ImageTk.PhotoImage(img)  # keep refernce so it doesnt get garbagged
        except Exception:
            # fallback if pillow not instaled - tkinter only supports gif and png nativly
            self._easter_img = tk.PhotoImage(file=img_path)

        tk.Label(outer, image=self._easter_img, bg="#1a1a2e").pack(pady=(60, 10))
        tk.Label(
            outer, text="you found the secret :)",
            font=("Arial", 18, "bold"), bg="#1a1a2e", fg="#f5c518"
        ).pack(pady=(0, 6))
        tk.Label(
            outer, text="battle for dream island!!",
            font=("Arial", 13), bg="#1a1a2e", fg="#aaaaaa"
        ).pack(pady=(0, 24))

        # back button so they can actualy get back to the login page
        tk.Button(
            outer, text="← go back",
            command=self.show_login_page,
            bg="#333355", fg="#f5c518",
            activebackground="#555577", activeforeground="#ffffff",
            relief="flat", font=("Arial", 13), cursor="hand2",
            padx=18, pady=8
        ).pack()


    # PAGE 2 SIGN UP

    def show_signup_page(self):
        self.clear_window()
        self.root.bind("<Return>", lambda _: self._handle_signup())

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(expand=True)

        c, f = self._card(outer, 480, 510, r=26)
        c.pack(pady=30)

        _lbl(f, "Create Account", 21, bold=True).pack(pady=(24, 6))
        _lbl(f, "Choose a User ID and password", 12, muted=True).pack(pady=(0, 18))

        def field(label, show=None):
            row = tk.Frame(f, bg=CARD)
            row.pack(fill="x", padx=22, pady=5)
            _lbl(row, label).pack(anchor="w")
            e = _entry(row, show=show)
            e.pack(fill="x", pady=(5, 0), ipady=6)
            return e

        self.su_userID = field("User ID  (e.g. U004)")
        self.su_name   = field("Full Name")
        self.su_pw     = field("Password",         show="*")
        self.su_pw2    = field("Confirm Password", show="*")

        bf = tk.Frame(f, bg=CARD)
        bf.pack(fill="x", padx=22, pady=(18, 6))
        _btn(bf, "Create Account", self._handle_signup, accent=True, big=True).pack(fill="x", pady=(0, 10))
        tk.Button(
            bf, text="← Back to Login",
            command=self.show_login_page,
            bg=BG, fg=MUTED, activebackground=CARD2, activeforeground=TEXT,
            relief="flat", font=("Arial", 12), cursor="hand2", bd=0,
        ).pack(fill="x")

        self.su_userID.focus()

    def _handle_signup(self):
        userID = self.su_userID.get().strip()
        name   = self.su_name.get().strip()
        pw     = self.su_pw.get().strip()
        pw2    = self.su_pw2.get().strip()

        if not userID or not name or not pw:
            messagebox.showerror("Sign Up", "All fields are required.")
            return
        if pw != pw2:
            messagebox.showerror("Sign Up", "Passwords do not match.")
            return
        if len(pw) < 4:
            messagebox.showerror("Sign Up", "Password must be at least 4 characters.")
            return

        success, message = db.register(userID, name, pw)
        if success:
            messagebox.showinfo("Account Created", message + "\n\nYou can now log in.")
            self.show_login_page()
        else:
            messagebox.showerror("Sign Up Failed", message)





    # PAGE 3 HOME

    def show_home_page(self):
        self.clear_window()

        # Top bar with user info and Logout button
        top = tk.Frame(self.root, bg=CARD, pady=12, padx=18)
        top.pack(fill="x")
        name = self.current_user["employeeName"]
        role = self.current_user["role"]
        tk.Label(top, text=f"Logged in as:  {name}  ({role})",
                  bg=CARD, fg=TEXT, font=("Arial", 13)).pack(side="left")
        _btn(top, "Logout", self.logout).pack(side="right")

        # Main content
        container = tk.Frame(self.root, bg=BG)
        container.pack(expand=True)

        _lbl(container, "Main Menu", 32, bold=True).pack(pady=(32, 8))
        _lbl(container, "Select what you want to do", 15, muted=True).pack(pady=(0, 32))

        cards = tk.Frame(container, bg=BG)
        cards.pack()

        self._menu_card(cards, "Create Booking",
                         "Check room availability and\ncreate a new booking.",
                         self.show_create_booking_page, col=0)

        self._menu_card(cards, "View Bookings",
                         "View, modify, or cancel\nan existing booking.",
                         self.show_view_booking_page, col=1)

        self._menu_card(cards, "Admin",
                         "Add rooms, update details,\nand manage availability.",
                         self.show_admin_login_page, col=2)

    def _menu_card(self, parent, title, desc, command, col):
        """Build one of the three big home page cards."""
        cw, ch = 330, 300
        c, f = self._card(parent, cw, ch, r=22)
        c.grid(row=0, column=col, padx=20, pady=8)

        _lbl(f, title, 19, bold=True).pack(pady=(26, 12))
        _lbl(f, desc, 13, muted=True).pack(padx=12, pady=(0, 28))

        tk.Button(
            f, text=title, command=command,
            bg=ACCENT, fg="grey",
            activebackground="#993a3a", activeforeground="grey",
            relief="flat", font=("Arial", 13, "bold"),
            cursor="hand2", padx=20, pady=9, bd=0,
        ).pack()





    # PAGE 4 CREATE BOOKING

    def show_create_booking_page(self):
        self.clear_window()
        self._top_bar(self.show_home_page)
        self._page_title("Create Booking")

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=18)

        # Booking form
        ff = ttk.LabelFrame(main, text="Booking Details", padding=14)
        ff.pack(fill="x", pady=(0, 10))

        def field(label, row, col, width=28):
            ttk.Label(ff, text=label).grid(row=row, column=col, sticky="w", padx=5, pady=6)
            e = ttk.Entry(ff, width=width)
            e.grid(row=row, column=col+1, sticky="w", padx=5, pady=6)
            return e

        self.cb_userID  = field("User ID",           0, 0)
        self.cb_name    = field("Employee Name",      0, 2)
        self.cb_roomID  = field("Room ID",            1, 0)
        self.cb_date    = field("Date (YYYY-MM-DD)",  1, 2)
        self.cb_start   = field("Start Time (HH:MM)", 2, 0)
        self.cb_end     = field("End Time (HH:MM)",   2, 2)
        self.cb_purpose = field("Purpose",            3, 0, width=62)

        # Pre-fill the current user's details
        self.cb_userID.insert(0, self.current_user["userID"])
        self.cb_name.insert(0, self.current_user["employeeName"])
        self.cb_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.cb_start.insert(0, "09:00")
        self.cb_end.insert(0, "10:00")

        # Buttons
        bf = ttk.Frame(main)
        bf.pack(fill="x", pady=6)
        ttk.Button(bf, text="Check Availability", command=self._check_avail).pack(side="left", padx=5)
        ttk.Button(bf, text="Create Booking",     command=self._handle_create_booking).pack(side="left", padx=5)
        ttk.Button(bf, text="Clear Form",         command=self._clear_create_form).pack(side="left", padx=5)

        # Room table so user can see what's available
        rf = ttk.LabelFrame(main, text="All Rooms", padding=10)
        rf.pack(fill="both", expand=True, pady=(6, 0))
        self.create_room_table = self._make_table(
            rf, ["roomID", "roomName", "capacity", "availabilityStatus"]
        )
        self._load_rooms_into_table(self.create_room_table)

    def _check_avail(self):
        ok, msg = db.check_availability(
            self.cb_roomID.get().strip(),
            self.cb_date.get().strip(),
            self.cb_start.get().strip(),
            self.cb_end.get().strip(),
        )
        (messagebox.showinfo if ok else messagebox.showerror)("Availability", msg)

    def _handle_create_booking(self):
        ok, msg, booking = db.create_booking(
            self.cb_userID.get().strip(),
            self.cb_name.get().strip(),
            self.cb_roomID.get().strip(),
            self.cb_date.get().strip(),
            self.cb_start.get().strip(),
            self.cb_end.get().strip(),
            self.cb_purpose.get().strip(),
        )
        if ok:
            messagebox.showinfo("Booking Confirmed",
                                 f"{msg}\nBooking ID: {booking['bookingID']}")
            self._clear_create_form()
            self._load_rooms_into_table(self.create_room_table)
        else:
            messagebox.showerror("Booking Error", msg)

    def _clear_create_form(self):
        for e in [self.cb_userID, self.cb_name, self.cb_roomID,
                   self.cb_date, self.cb_start, self.cb_end, self.cb_purpose]:
            e.delete(0, tk.END)
        self.cb_userID.insert(0, self.current_user["userID"])
        self.cb_name.insert(0, self.current_user["employeeName"])
        self.cb_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.cb_start.insert(0, "09:00")
        self.cb_end.insert(0, "10:00")







    # PAGE 5 VIEW BOOKINGS

    def show_view_booking_page(self):
        self.clear_window()
        self._top_bar(self.show_home_page)
        self._page_title("View Bookings")

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=18)

        ttk.Label(main,
                   text="Click a booking in the table, then choose Modify or Cancel.",
                   font=("Arial", 12), foreground=MUTED).pack(anchor="w", pady=(0, 8))

        # Action buttons
        bf = ttk.Frame(main)
        bf.pack(fill="x", pady=(0, 8))
        ttk.Button(bf, text="Modify Selected",
                    command=self._go_to_modify).pack(side="left", padx=5)
        ttk.Button(bf, text="Cancel Selected",
                    command=self._go_to_cancel).pack(side="left", padx=5)
        ttk.Button(bf, text="Refresh",
                    command=lambda: self._load_bookings_into_table(self.view_table)).pack(side="left", padx=5)

        # Bookings table
        tf = ttk.LabelFrame(main, text="All Bookings", padding=10)
        tf.pack(fill="both", expand=True)
        self.view_table = self._make_table(tf, [
            "bookingID", "userID", "employeeName", "roomID",
            "bookingDate", "startTime", "endTime",
            "bookingPurpose", "bookingStatus"
        ])
        self._load_bookings_into_table(self.view_table)

    def _get_selected_booking(self):
        """Read the selected row from the view table and return it as a dict."""
        sel = self.view_table.focus()
        if not sel:
            messagebox.showerror("No Selection",
                                  "Please click on a booking in the table first.")
            return None
        v = self.view_table.item(sel, "values")
        return {
            "bookingID":      v[0],
            "userID":         v[1],
            "employeeName":   v[2],
            "roomID":         v[3],
            "bookingDate":    v[4],
            "startTime":      v[5],
            "endTime":        v[6],
            "bookingPurpose": v[7],
            "bookingStatus":  v[8],
        }

    def _go_to_modify(self):
        booking = self._get_selected_booking()
        if booking:
            self.show_modify_booking_page(booking)

    def _go_to_cancel(self):
        booking = self._get_selected_booking()
        if booking:
            self.show_cancel_booking_page(booking)








    # PAGE 6 MODIFY BOOKING

    def show_modify_booking_page(self, booking):
        self.clear_window()
        self._top_bar(self.show_view_booking_page)
        self._page_title("Modify Booking")

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=18)

        # Show which booking is being edited
        ttk.Label(main,
                   text=f"Editing:  {booking['bookingID']}",
                   font=("Arial", 14, "bold"), foreground=ACCENT).pack(anchor="w", pady=(0, 10))

        ff = ttk.LabelFrame(main, text="Edit Booking Details", padding=14)
        ff.pack(fill="x")

        def field(label, row, col, prefill="", width=28):
            ttk.Label(ff, text=label).grid(row=row, column=col, sticky="w", padx=5, pady=8)
            e = ttk.Entry(ff, width=width)
            e.grid(row=row, column=col+1, sticky="w", padx=5, pady=8)
            e.insert(0, prefill)
            return e

        self.mod_roomID  = field("Room ID",            0, 0, booking["roomID"])
        self.mod_date    = field("Date (YYYY-MM-DD)",   0, 2, booking["bookingDate"])
        self.mod_start   = field("Start Time (HH:MM)",  1, 0, booking["startTime"])
        self.mod_end     = field("End Time (HH:MM)",    1, 2, booking["endTime"])
        self.mod_purpose = field("Purpose",             2, 0, booking.get("bookingPurpose", ""), width=62)

        self._editing_bookingID = booking["bookingID"]

        bf = ttk.Frame(main)
        bf.pack(fill="x", pady=14)
        ttk.Button(bf, text="Save Changes", command=self._handle_modify).pack(side="left", padx=5)

    def _handle_modify(self):
        ok, msg = db.modify_booking(
            self._editing_bookingID,
            self.mod_roomID.get().strip(),
            self.mod_date.get().strip(),
            self.mod_start.get().strip(),
            self.mod_end.get().strip(),
            self.mod_purpose.get().strip(),
        )
        if ok:
            messagebox.showinfo("Updated", msg)
            self.show_view_booking_page()
        else:
            messagebox.showerror("Error", msg)






    # PAGE 7 CANCEL BOOKING

    def show_cancel_booking_page(self, booking):
        self.clear_window()
        self._top_bar(self.show_view_booking_page)
        self._page_title("Cancel Booking")

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(expand=True)

        c, f = self._card(outer, 540, 400, r=22)
        c.pack(pady=20)

        _lbl(f, "Are you sure you want to cancel?", 16, bold=True).pack(pady=(22, 18))

        # Show the booking details so the user knows what they're cancelling
        details = [
            ("Booking ID", booking["bookingID"]),
            ("Room",       booking["roomID"]),
            ("Date",       booking["bookingDate"]),
            ("Time",       f"{booking['startTime']} – {booking['endTime']}"),
            ("Purpose",    booking.get("bookingPurpose") or "---"),
        ]
        detail_frame = tk.Frame(f, bg=CARD)
        detail_frame.pack(fill="x", padx=24, pady=4)
        for label, value in details:
            row = tk.Frame(detail_frame, bg=CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{label}:", font=("Arial", 12),
                      bg=CARD, fg=MUTED, width=14, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=("Arial", 12, "bold"),
                      bg=CARD, fg=TEXT).pack(side="left")

        self._cancelling_bookingID = booking["bookingID"]

        btn_row = tk.Frame(f, bg=CARD)
        btn_row.pack(pady=(24, 8))
        _btn(btn_row, "Yes, Cancel Booking",
              self._handle_cancel, accent=True, big=True).pack(side="left", padx=10)
        _btn(btn_row, "No, Go Back",
              self.show_view_booking_page).pack(side="left", padx=10)

    def _handle_cancel(self):
        ok, msg = db.cancel_booking(self._cancelling_bookingID)
        if ok:
            messagebox.showinfo("Cancelled", msg)
            self.show_view_booking_page()
        else:
            messagebox.showerror("Error", msg)






    # PAGE 8 ADMIN

    def show_admin_login_page(self):
        """If already admin, skip straight to the admin page. Otherwise ask for credentials."""
        if self.current_user and self.current_user["role"] == "admin":
            self.show_admin_page()
            return

        self.clear_window()
        self._top_bar(self.show_home_page)
        self._page_title("Admin Login Required")

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(expand=True)

        c, f = self._card(outer, 480, 340, r=22)
        c.pack(pady=20)

        _lbl(f, "Enter admin credentials to continue.", 13, muted=True).pack(pady=(20, 22))

        r1 = tk.Frame(f, bg=CARD)
        r1.pack(fill="x", padx=22, pady=6)
        _lbl(r1, "Admin User ID").pack(anchor="w")
        self.adm_login_userID = _entry(r1)
        self.adm_login_userID.pack(fill="x", pady=(5, 0), ipady=6)

        r2 = tk.Frame(f, bg=CARD)
        r2.pack(fill="x", padx=22, pady=6)
        _lbl(r2, "Admin Password").pack(anchor="w")
        self.adm_login_pw = _entry(r2, show="*")
        self.adm_login_pw.pack(fill="x", pady=(5, 0), ipady=6)

        bf = tk.Frame(f, bg=CARD)
        bf.pack(fill="x", padx=22, pady=(20, 6))
        _btn(bf, "Enter Admin Area", self._handle_admin_login, accent=True, big=True).pack(fill="x")

        self.adm_login_userID.focus()

    def _handle_admin_login(self):
        user = db.login(
            self.adm_login_userID.get().strip(),
            self.adm_login_pw.get().strip()
        )
        if not user or user["role"] != "admin":
            messagebox.showerror("Access Denied", "Incorrect admin credentials.")
            return
        self.current_user = user
        self.show_admin_page()

    def show_admin_page(self):
        self.clear_window()
        self._top_bar(self.show_home_page)
        self._page_title("Admin - Room Management")

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=18)

        # Room form
        ff = ttk.LabelFrame(main, text="Add or Update a Room", padding=14)
        ff.pack(fill="x", pady=(0, 10))

        def field(label, row, col):
            ttk.Label(ff, text=label).grid(row=row, column=col, sticky="w", padx=5, pady=6)
            e = ttk.Entry(ff, width=28)
            e.grid(row=row, column=col+1, sticky="w", padx=5, pady=6)
            return e

        self.adm_roomID   = field("Room ID",   0, 0)
        self.adm_roomName = field("Room Name", 0, 2)
        self.adm_capacity = field("Capacity",  1, 0)

        ttk.Label(ff, text="Status").grid(row=1, column=2, sticky="w", padx=5, pady=6)
        self.adm_status = ttk.Combobox(
            ff, values=["Available", "Unavailable"], state="readonly", width=27
        )
        self.adm_status.grid(row=1, column=3, padx=5, pady=6)
        self.adm_status.set("Available")

        # Buttons
        bf = ttk.Frame(main)
        bf.pack(fill="x", pady=6)
        ttk.Button(bf, text="Add Room",           command=self._handle_add_room).pack(side="left", padx=5)
        ttk.Button(bf, text="Update Room",        command=self._handle_update_room).pack(side="left", padx=5)
        ttk.Button(bf, text="Load Selected Room", command=self._load_room_into_form).pack(side="left", padx=5)
        ttk.Button(bf, text="Refresh",
                    command=lambda: self._load_rooms_into_table(self.admin_room_table)).pack(side="left", padx=5)

        # Room table
        rf = ttk.LabelFrame(main, text="All Rooms", padding=10)
        rf.pack(fill="both", expand=True)
        self.admin_room_table = self._make_table(
            rf, ["roomID", "roomName", "capacity", "availabilityStatus"]
        )
        self._load_rooms_into_table(self.admin_room_table)

    def _handle_add_room(self):
        ok, msg = db.add_room(
            self.adm_roomID.get().strip(),
            self.adm_roomName.get().strip(),
            self.adm_capacity.get().strip(),
        )
        (messagebox.showinfo if ok else messagebox.showerror)("Add Room", msg)
        if ok:
            self._clear_admin_form()
            self._load_rooms_into_table(self.admin_room_table)

    def _handle_update_room(self):
        ok, msg = db.update_room(
            self.adm_roomID.get().strip(),
            self.adm_roomName.get().strip(),
            self.adm_capacity.get().strip(),
            self.adm_status.get(),
        )
        (messagebox.showinfo if ok else messagebox.showerror)("Update Room", msg)
        if ok:
            self._clear_admin_form()
            self._load_rooms_into_table(self.admin_room_table)

    def _load_room_into_form(self):
        """Click a room in the table → fills the form fields above for editing."""
        sel = self.admin_room_table.focus()
        if not sel:
            messagebox.showerror("No Selection", "Please click on a room in the table first.")
            return
        v = self.admin_room_table.item(sel, "values")
        self.adm_roomID.delete(0, tk.END)
        self.adm_roomName.delete(0, tk.END)
        self.adm_capacity.delete(0, tk.END)
        self.adm_roomID.insert(0, v[0])
        self.adm_roomName.insert(0, v[1])
        self.adm_capacity.insert(0, v[2])
        self.adm_status.set(v[3])

    def _clear_admin_form(self):
        self.adm_roomID.delete(0, tk.END)
        self.adm_roomName.delete(0, tk.END)
        self.adm_capacity.delete(0, tk.END)
        self.adm_status.set("Available")
