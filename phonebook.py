import psycopg2
import csv

conn = psycopg2.connect(
    dbname="phonebook",
    user="postgres",
    password="123456",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL
);
""")
conn.commit()

# Insert contact from console

def add_contact_console():
    name = input("Enter name: ")
    phone = input("Enter phone: ")
    cur.execute("INSERT INTO contacts (first_name, phone) VALUES (%s, %s)", (name, phone))
    conn.commit()
    print("Contact added!")

# Using CSV file

def add_contacts_from_csv():
    file_name = input("Enter CSV file name:")
    try:
        with open(file_name, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 2:
                    cur.execute("INSERT INTO contacts (first_name, phone) VALUES (%s, %s)", (row[0], row[1]))
            conn.commit()
            print("Contacts loaded from CSV!")
    except Exception as e:
        print("[ERROR]:", e)

# Update contact data

def update_contact():
    field = input("What do you want to update? (name/phone): ").strip().lower()
    if field == "name":
        old = input("Enter current name: ")
        new = input("Enter new name: ")
        cur.execute("UPDATE contacts SET first_name = %s WHERE first_name = %s", (new, old))
    elif field == "phone":
        old = input("Enter current phone: ")
        new = input("Enter new phone: ")
        cur.execute("UPDATE contacts SET phone = %s WHERE phone = %s", (new, old))
    else:
        print("Invalid option")
        return
    conn.commit()
    print("Contact updated!")

# Query contacts with filters

def query_contacts():
    field = input("Search by name or phone: ").strip().lower()
    value = input("Enter search value: ")
    if field == "name":
        cur.execute("SELECT * FROM contacts WHERE first_name ILIKE %s", (f"%{value}%",))
    elif field == "phone":
        cur.execute("SELECT * FROM contacts WHERE phone ILIKE %s", (f"%{value}%",))
    else:
        print("Invalid search field")
        return
    rows = cur.fetchall()
    for row in rows:
        print(f"ID: {row[0]} | Name: {row[1]} | Phone: {row[2]}")

# Delete contact by name or phone

def delete_contact():
    field = input("Delete by name or phone: ").strip().lower()
    value = input("Enter value to delete: ")
    if field == "name":
        cur.execute("DELETE FROM contacts WHERE first_name = %s", (value,))
    elif field == "phone":
        cur.execute("DELETE FROM contacts WHERE phone = %s", (value,))
    else:
        print("Invalid field")
        return
    conn.commit()
    print("Contact deleted!")

# Menu

if __name__ == "__main__":
    while True:
        print("\nPhoneBook Menu:")
        print("1. Add contact from console")
        print("2. Load contacts from CSV")
        print("3. Update contact")
        print("4. Query contacts")
        print("5. Delete contact")
        print("6. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            add_contact_console()
        elif choice == "2":
            add_contacts_from_csv()
        elif choice == "3":
            update_contact()
        elif choice == "4":
            query_contacts()
        elif choice == "5":
            delete_contact()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Try again.")

    cur.close()
    conn.close()
