import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry  # Import tkcalendar for date selection
import threading
from PIL import Image, ImageTk

# Create or connect to the SQLite database
conn = sqlite3.connect('WeddingPlan_database.db')
cursor = conn.cursor()

# Drop and recreate the "Plan" table
cursor.execute("DROP TABLE IF EXISTS plan")
conn.commit()
cursor.execute('''  
    CREATE TABLE IF NOT EXISTS plan (
        clients INTEGER PRIMARY KEY,
        couplenames TEXT,
        hall INTEGER,
        rentin DATE,
        rentout DATE,
        price REAL,
        otherdetails TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Thread lock for bookings
booking_lock = threading.Lock()

# Price Calculation
def calculate_price(rentin, rentout):
    return 500 * (rentout - rentin).days

# Check Hall Availability
def is_hall_available(hall, rentin, rentout):
    cursor.execute("SELECT clients FROM plan WHERE hall = ? AND (rentin <= ? AND rentout >= ?)", (hall, rentout, rentin))
    return cursor.fetchone() is None

# Book Hall
def book_hall():
    couplenames = couplenames_entry.get()
    hall = hall_entry.get()
    rentin = rentin_calendar.get_date()
    rentout = rentout_calendar.get_date()
    otherdetails = otherdetails_entry.get("1.0", "end")

    if not couplenames or not hall:
        messagebox.showerror("Error", "Both name and hall number are required.")
        return

    try:
        hall = int(hall)
    except ValueError:
        messagebox.showerror("Error", "Hall must be a number.")
        return

    if not is_hall_available(hall, rentin, rentout):
        messagebox.showerror("Error", f"Hall {hall} is not available for the selected dates.")
        return

    price = calculate_price(rentin, rentout)

    with booking_lock:
        cursor.execute("INSERT INTO plan (couplenames, hall, rentin, rentout, price, otherdetails) VALUES (?, ?, ?, ?, ?, ?)",
                       (couplenames, hall, rentin, rentout, price, otherdetails))
        conn.commit()

    messagebox.showinfo("Booking Successful", f"Hall {hall} booked successfully for {couplenames}\nTotal Price: RM{price}")
    couplenames_entry.delete(0, "end")
    hall_entry.delete(0, "end")
    otherdetails_entry.delete(0, "end")
    view_hall_bookings()

# View Bookings
def view_hall_bookings():
    cursor.execute("SELECT couplenames, hall, rentin, rentout, price FROM plan")
    bookings = cursor.fetchall()
    result_label.config(text="\n".join(f"CoupleNames: {b[0]}, Hall: {b[1]}, Rent-in: {b[2]}, Rent-out: {b[3]}, Price: RM{b[4]}" for b in bookings) or "No bookings found.")

# Search Booking
def search_booking():
    couplenames = couplenames_search_entry.get()
    cursor.execute("SELECT couplenames, hall, rentin, rentout, price FROM plan WHERE couplenames = ?", (couplenames,))
    bookings = cursor.fetchall()
    search_result_label.config(text="\n".join(f"CoupleNames: {b[0]}, Hall: {b[1]}, Rent-in: {b[2]}, Rent-out: {b[3]}, Price: RM{b[4]}" for b in bookings) or f"No bookings found for {couplenames}.")

# Cancel Booking
def cancel_booking():
    couplenames = couplenames_cancel_entry.get()
    cursor.execute("DELETE FROM plan WHERE couplenames = ?", (couplenames,))
    conn.commit()
    messagebox.showinfo("Booking Canceled", f"Booking(s) for {couplenames} canceled.")
    view_hall_bookings()

# Main Window
root = tk.Tk()
root.title("Wedding Planner")
root.geometry("550x700")

# Scrollable Canvas
canvas = tk.Canvas(root, borderwidth=0, highlightthickness=0)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

# Configure the scroll region
scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

# Place the canvas and scrollbar
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Widgets inside the scrollable frame
logo_image = Image.open("marry.png").resize((370, 90))
logo_photo = ImageTk.PhotoImage(logo_image)
logo_label = tk.Label(scrollable_frame, image=logo_photo)
logo_label.grid(row=0, column=0, columnspan=2, pady=10)

# Form Widgets
tk.Label(scrollable_frame, text="Enter Couple Names:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
couplenames_entry = tk.Entry(scrollable_frame)
couplenames_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(scrollable_frame, text="Enter Hall Number:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
hall_entry = tk.Entry(scrollable_frame)
hall_entry.grid(row=2, column=1, padx=10, pady=5)

tk.Label(scrollable_frame, text="Rent-in Date:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
rentin_calendar = DateEntry(scrollable_frame, date_pattern="dd/mm/yyyy")
rentin_calendar.grid(row=3, column=1, padx=10, pady=5)

tk.Label(scrollable_frame, text="Rent-out Date:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
rentout_calendar = DateEntry(scrollable_frame, date_pattern="dd/mm/yyyy")
rentout_calendar.grid(row=4, column=1, padx=10, pady=5)

tk.Label(scrollable_frame, text="Other Details:").grid(row=5, column=0, padx=10, pady=5, sticky="e")
otherdetails_entry = tk.Text(scrollable_frame, height=5, width=40)
otherdetails_entry.grid(row=5, column=1, padx=10, pady=5)

tk.Button(scrollable_frame, text="Book Hall", command=book_hall).grid(row=6, column=0, columnspan=2, pady=10)
tk.Button(scrollable_frame, text="View Hall Bookings", command=view_hall_bookings).grid(row=7, column=0, columnspan=2, pady=10)

result_label = tk.Label(scrollable_frame, text="", justify="left")
result_label.grid(row=8, column=0, columnspan=2, pady=10)

# Search and Cancel Widgets
tk.Label(scrollable_frame, text="Search Booking by CoupleNames:").grid(row=9, column=0, padx=10, pady=5, sticky="e")
couplenames_search_entry = tk.Entry(scrollable_frame)
couplenames_search_entry.grid(row=9, column=1, padx=10, pady=5)
tk.Button(scrollable_frame, text="Search", command=search_booking).grid(row=10, column=0, columnspan=2, pady=10)

search_result_label = tk.Label(scrollable_frame, text="", justify="left")
search_result_label.grid(row=11, column=0, columnspan=2, pady=10)

tk.Label(scrollable_frame, text="Cancel Booking by CoupleNames:").grid(row=12, column=0, padx=10, pady=5, sticky="e")
couplenames_cancel_entry = tk.Entry(scrollable_frame)
couplenames_cancel_entry.grid(row=12, column=1, padx=10, pady=5)
tk.Button(scrollable_frame, text="Cancel Booking", command=cancel_booking).grid(row=13, column=0, columnspan=2, pady=10)

root.mainloop()
