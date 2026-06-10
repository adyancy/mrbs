import sqlite3
import os
import hashlib
from datetime import datetime

# path to the database file, stored inside the data folder
DB_PATH = os.path.join("data", "mrbs.db")


def hash_password(password):
    # converts a plain text pasword into a sha256 hash so we dont store it as plain text
    # the encode() turns the string into bytes first becuse hashlib needs bytes not a string
    return hashlib.sha256(password.encode()).hexdigest()  # retuns a 64 charcter hex string


def get_db():
    # row_factory lets us access colums by name like row["roomID"] instead of row[0]
    os.makedirs("data", exist_ok=True)  # create the data folder if it doesnt exist yet
    db = sqlite3.connect(DB_PATH)  # conect to the database file
    db.row_factory = sqlite3.Row  # lets us use column names to access data
    return db  # returns the connection so other funcitons can use it


def setup_db():
    # this funciton runs once at startup to create all the tables
    # if the tables already exsist, the IF NOT EXISTS part skips them
    db = get_db()  # open a conection to the databse

    # create the users table to store login informaton
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            userID        TEXT PRIMARY KEY,
            employeeName  TEXT NOT NULL,
            password      TEXT NOT NULL,
            role          TEXT DEFAULT 'user'
        )
    """)

    # create the rooms table to store all meeting room detials
    db.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            roomID             TEXT PRIMARY KEY,
            roomName           TEXT NOT NULL,
            capacity           INTEGER NOT NULL,
            availabilityStatus TEXT DEFAULT 'Available'
        )
    """)

    # create the bookings table to store all bookings made by users
    db.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            bookingID          TEXT PRIMARY KEY,
            userID             TEXT NOT NULL,
            employeeName       TEXT NOT NULL,
            roomID             TEXT NOT NULL,
            bookingDate        TEXT NOT NULL,
            startTime          TEXT NOT NULL,
            endTime            TEXT NOT NULL,
            bookingPurpose     TEXT,
            bookingStatus      TEXT DEFAULT 'Confirmed',
            confirmationStatus TEXT DEFAULT 'Confirmed'
        )
    """)

    # only add the defualt admin account if no users exsist yet
    # this stops it from adding duplicat accounts every time the program starts
    if not db.execute("SELECT 1 FROM users").fetchone():
        db.execute(
            "INSERT INTO users VALUES ('ADMIN', 'System Admin', ?, 'admin')",
            (hash_password("admin123"),)  # hash the pasword before storing it
        )

    # only seed the 8 rooms from the storyboard if the rooms table is empty
    if not db.execute("SELECT 1 FROM rooms").fetchone():
        db.executemany("INSERT INTO rooms VALUES (?, ?, ?, ?)", [
            ("R001", "Fire",        4,  "Available"),    # small room, 4 people
            ("R002", "Leaf",        4,  "Unavailable"),  # also small, currently unavailble
            ("R003", "Teardrop",    8,  "Available"),    # medium sized room
            ("R004", "Fries",       9,  "Available"),    # medium room
            ("R005", "Golf Ball",   13, "Available"),    # larger room
            ("R006", "Tennis Ball", 16, "Unavailable"),  # large but currenty unavailble
            ("R007", "Pin",         18, "Available"),    # big room
            ("R008", "Needle",      30, "Available"),    # biggest room, fits 30 people
        ])

    db.commit()  # save all the changes to the databse file
    db.close()   # close the conection when done


# ── user funcitons ─────────────────────────────────────────────────────────────

def login(userID, password):
    # cheacks if the userID and password match a record in the users tabel
    # retuns the user as a dictionary if correct, or None if the login is wrong
    db = get_db()  # open database conection
    user = db.execute(
        "SELECT * FROM users WHERE userID = ? AND password = ?",
        (userID, hash_password(password))  # hash the password befor comparing to the stored hash
    ).fetchone()  # get the first matching row, or None if none found
    db.close()  # always close the conection after use
    return dict(user) if user else None  # convert the row to a dict so its easier to use


def register(userID, name, password):
    # creates a new user account and saves it to the databse
    # retuns (True, message) if it worked, or (False, error) if somthing went wrong
    if not userID or not name or not password:
        return False, "All fields are required."  # stop if any field is empty

    db = get_db()  # open the databse conection
    # cheack if the userID is already taken before inseting
    if db.execute("SELECT 1 FROM users WHERE userID = ?", (userID,)).fetchone():
        db.close()
        return False, f"User ID '{userID}' is already taken. Please choose another."

    # insert the new user into the tabel with role set to user by defualt
    # we hash the pasword here so it is never saved as plain text in the databse
    db.execute(
        "INSERT INTO users (userID, employeeName, password, role) VALUES (?, ?, ?, 'user')",
        (userID, name, hash_password(password))
    )
    db.commit()  # save the new user to disk
    db.close()
    return True, f"Account created! Your User ID is: {userID}"


# ── room funcitons ─────────────────────────────────────────────────────────────

def get_rooms():
    # retuns a list of all rooms from the databse ordered by roomID
    db = get_db()
    rooms = db.execute("SELECT * FROM rooms ORDER BY roomID").fetchall()  # get all rows
    db.close()
    return [dict(r) for r in rooms]  # convert each row to a dict and return as a list


def add_room(roomID, roomName, capacity):
    # adds a new room to the databse
    # retuns (True, message) if succesful, or (False, error) if not
    if not roomID or not roomName or not capacity:
        return False, "All fields are required."  # validaiton check

    try:
        cap = int(capacity)  # try to convert capacity to a whole number
    except ValueError:
        return False, "Capacity must be a whole number."  # retun error if its not a number

    db = get_db()
    # cheack that the roomID doesnt already exsist in the tabel
    if db.execute("SELECT 1 FROM rooms WHERE roomID = ?", (roomID,)).fetchone():
        db.close()
        return False, f"Room ID '{roomID}' already exists."

    # insert the new room, automaticly set status to available
    db.execute("INSERT INTO rooms VALUES (?, ?, ?, 'Available')", (roomID, roomName, cap))
    db.commit()  # save the changes
    db.close()
    return True, f"Room '{roomName}' added successfully."


def update_room(roomID, roomName, capacity, status):
    # updates an exsiting rooms detials in the databse
    # retuns (True, message) or (False, error message)
    if not roomID or not roomName or not capacity or not status:
        return False, "All fields are required."  # all fields are requierd

    try:
        cap = int(capacity)  # capacity must be a whole number
    except ValueError:
        return False, "Capacity must be a whole number."

    db = get_db()
    # make sure the room actualy exsists before trying to update it
    if not db.execute("SELECT 1 FROM rooms WHERE roomID = ?", (roomID,)).fetchone():
        db.close()
        return False, f"Room '{roomID}' not found."  # room doesnt exsist

    # update the room record with the new values
    db.execute(
        "UPDATE rooms SET roomName=?, capacity=?, availabilityStatus=? WHERE roomID=?",
        (roomName, cap, status, roomID)
    )
    db.commit()  # save changes to disk
    db.close()
    return True, f"Room '{roomID}' updated successfully."


# ── booking funcitons ─────────────────────────────────────────────────────────────

def get_bookings():
    # retuns every booking from the databse, ordered by date then start time
    db = get_db()
    bookings = db.execute(
        "SELECT * FROM bookings ORDER BY bookingDate, startTime"  # sort by date first
    ).fetchall()
    db.close()
    return [dict(b) for b in bookings]  # turn each row into a dict


def check_availability(roomID, bookingDate, startTime, endTime, skip_bookingID=None):
    # cheacks wether a room is free for a given time slot
    # skip_bookingID is used when modifing - we dont want to conflict with the current bookign
    # retuns (True, message) if avaliable, or (False, reason) if not
    db = get_db()

    # first cheack that the room actualy exsists in the databse
    room = db.execute("SELECT * FROM rooms WHERE roomID = ?", (roomID,)).fetchone()
    if not room:
        db.close()
        return False, f"Room '{roomID}' does not exist."

    # if the room is marked unavailble then no one can book it
    if dict(room)["availabilityStatus"] == "Unavailable":
        db.close()
        return False, f"Room '{roomID}' is currently marked as unavailable."

    # look for any existing bookign in the same room on the same date that overlapin the time
    # the startTime < endTime and endTime > startTime logic cheacks for any overlap
    query = """
        SELECT 1 FROM bookings
        WHERE roomID = ? AND bookingDate = ?
          AND bookingStatus != 'Cancelled'
          AND startTime < ? AND endTime > ?
    """
    params = [roomID, bookingDate, endTime, startTime]  # endTime and startTime are swapped on purpose for overlap logic

    # if we are modifing a bookign, exclude the curent bookign from the conflict cheack
    if skip_bookingID:
        query += " AND bookingID != ?"  # exclude this bookign id from the search
        params.append(skip_bookingID)

    conflict = db.execute(query, params).fetchone()  # retuns a row if there is a conflict
    db.close()

    if conflict:
        return False, f"Room '{roomID}' is already booked during that time."
    return True, f"Room '{roomID}' is available."


def create_booking(userID, employeeName, roomID, bookingDate, startTime, endTime, purpose):
    # creates a new bookign after validatig all the input fields
    # retuns (True, message, booking_dict) if it worked, or (False, message, None) if not
    if not all([userID, employeeName, roomID, bookingDate, startTime, endTime]):
        return False, "All fields are required.", None  # cheack none of the fields are blank

    # try to parse the date and time to make sure the formatt is correct
    try:
        datetime.strptime(bookingDate, "%Y-%m-%d")  # must be year-month-day
        datetime.strptime(startTime,   "%H:%M")     # must be hour:minute
        datetime.strptime(endTime,     "%H:%M")     # same for end time
    except ValueError:
        return False, "Use YYYY-MM-DD for date and HH:MM for times.", None  # invalide format

    # end time must be after start time, not the same or before
    if startTime >= endTime:
        return False, "End time must be after start time.", None

    # cheack the room is actualy free for this time slot
    available, msg = check_availability(roomID, bookingDate, startTime, endTime)
    if not available:
        return False, msg, None  # retun the error from check_availability

    db = get_db()
    # count existing bookings to generate a unique bookingID like B001, B002 etc
    count     = db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    bookingID = f"B{str(count + 1).zfill(3)}"  # pad with zeros so its always 3 digits

    # insert the new bookign into the databse with status set to confirmed
    db.execute(
        "INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', 'Confirmed')",
        (bookingID, userID, employeeName, roomID, bookingDate, startTime, endTime, purpose)
    )
    db.commit()  # save the bookign to disk
    db.close()
    return True, "Booking confirmed!", {"bookingID": bookingID}  # retun success with the new id


def modify_booking(bookingID, roomID, bookingDate, startTime, endTime, purpose):
    # updates an existng bookign with new detials
    # retuns (True, message) if it worked, or (False, error) if somthing failed
    if not all([bookingID, roomID, bookingDate, startTime, endTime]):
        return False, "All fields are required."  # cant update if fields are missing

    # validat the date and time formats before doing anything
    try:
        datetime.strptime(bookingDate, "%Y-%m-%d")
        datetime.strptime(startTime,   "%H:%M")
        datetime.strptime(endTime,     "%H:%M")
    except ValueError:
        return False, "Use YYYY-MM-DD for date and HH:MM for times."

    if startTime >= endTime:
        return False, "End time must be after start time."  # same vaildation as create

    db = get_db()
    # make sure the bookign we are trying to modify actualy exsists
    if not db.execute("SELECT 1 FROM bookings WHERE bookingID = ?", (bookingID,)).fetchone():
        db.close()
        return False, f"Booking '{bookingID}' not found."
    db.close()

    # cheack availability but skip the current bookign so it doesnt conflict with itself
    available, msg = check_availability(
        roomID, bookingDate, startTime, endTime, skip_bookingID=bookingID
    )
    if not available:
        return False, msg  # room is not avalible for the new time

    db = get_db()
    # update only the fields that the user is allowed to change
    db.execute("""
        UPDATE bookings
        SET roomID=?, bookingDate=?, startTime=?, endTime=?, bookingPurpose=?
        WHERE bookingID=?
    """, (roomID, bookingDate, startTime, endTime, purpose, bookingID))
    db.commit()  # save the updated bookign
    db.close()
    return True, f"Booking '{bookingID}' updated successfully."


def cancel_booking(bookingID):
    # marks a bookign as canceld instead of deleteing it from the databse
    # this keeps a record of past bookigns for the admin to view
    # retuns (True, message) or (False, error)
    db = get_db()
    # cheack the bookign exsists before trying to cancel it
    if not db.execute("SELECT 1 FROM bookings WHERE bookingID = ?", (bookingID,)).fetchone():
        db.close()
        return False, f"Booking '{bookingID}' not found."  # bookign not found in databse

    # update the status to cancelled instead of deleteing the row
    db.execute(
        "UPDATE bookings SET bookingStatus='Cancelled', confirmationStatus='Cancelled' WHERE bookingID=?",
        (bookingID,)
    )
    db.commit()  # save the change to disk
    db.close()
    return True, f"Booking '{bookingID}' has been cancelled."
