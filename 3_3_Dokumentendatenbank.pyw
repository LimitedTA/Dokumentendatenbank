#from cgi import print_arguments
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os
import sys
import sqlite3
import shutil
import datetime
#from tkcalendar import *
from datetime import date
import threading
#import PyPDF2
import time
from pathlib import Path

db = None

########## Pfad ermitteln ##########
PFAD_PY = ""
PFAD_EXE = os.path.dirname(sys.executable)
PFAD = os.path.abspath(__file__)

pfad_splitted = PFAD.split("\\")
pfad_splitted.remove(pfad_splitted[-1])

for i in pfad_splitted:
    PFAD_PY = PFAD_PY + i + "/"

if "\\Python\\" in PFAD_EXE:
    PFAD = PFAD_PY
else:
    PFAD = PFAD_EXE

########## Ordner erstellen ##########
if not os.path.exists(PFAD + '/_Dokumente'):
    os.makedirs(PFAD + '/_Dokumente')
if not os.path.exists(PFAD + "/_Workspace"):
    os.makedirs(PFAD + "/_Workspace")
if not os.path.exists(PFAD + "/_Anhang"):
    os.makedirs(PFAD + "/_Anhang")

########## Datum ermitteln ##########
aktuelles_datum = date.today()
aktuelles_datum_de = aktuelles_datum.strftime("%d.%m.%Y")

########## Globale Funktionen ##########
def closing_main_window():
    if os.path.exists(PFAD + "/_Dokumente"):
        dateien = os.listdir(PFAD + "/_Dokumente")
        for i in dateien:
            #print(PFAD + "/_Dokumente/" + i)
            db.update_blob(i.split(".")[0], convertToBinaryData(PFAD + "/_Dokumente/" + i))
        shutil.rmtree(PFAD + "/" + "_Dokumente")

    if os.path.exists(PFAD + "/_Workspace"):
        shutil.rmtree(PFAD + "/_Workspace")
    if os.path.exists(PFAD + "/_Anhang"):
        shutil.rmtree(PFAD + "/_Anhang")
    
    #db.vakuum()
    window.destroy()

def center(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y - 40))

def button_enter(widget, bild_aktiv, status_leiste=None, anzeigetext=""):
    widget.config(image=bild_aktiv)
    if status_leiste != None:
        status_leiste.status_leiste.config(text=anzeigetext)

def button_leave(widget, bild_standard, status_leiste=None):
    widget.config(image=bild_standard)
    if status_leiste != None:
        status_leiste.status_leiste.config(text="")

def button_pressed(widget, color):
    widget.config(borderwidth=0)
    widget.config(activebackground=color)

def convertToBinaryData(filename):
    if filename == "" or filename == "-":
        return ""
    else:
        with open(filename, 'rb') as file:
            blobData = file.read()
        return blobData


########## Datenbank laden ##########
class Database(Tk):
    def __init__(self, datenbank=None):

        self.datenbank = datenbank

        self.conn = sqlite3.connect(self.datenbank, check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS dokumente(id INTEGER PRIMARY KEY,
                datum TEXT,
                kategorie TEXT,
                bezeichnung TEXT,
                beschreibung TEXT,
                person TEXT,
                kommentar TEXT,
                datei BLOB,
                dateiart TEXT,
                link TEXT,
                status TEXT
            )""") 

        self.conn.commit()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspace(id INTEGER PRIMARY KEY,
                datenbankname TEXT,
                nummer INTEGER,
                datei BLOB
            )""")

        self.conn.commit()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS datenbanken(id INTEGER PRIMARY KEY,
                bezeichnung TEXT,
                link TEXT
            )""")

        self.conn.commit()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS anhaenge(id INTEGER PRIMARY KEY,
                dokumentennummer INTEGER,
                bezeichnung TEXT,
                format TEXT,
                anhang BLOB
            )""")

        self.conn.commit()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS erinnerung(id INTEGER PRIMARY KEY,
                datenbankname TEXT,
                dokumentennummer INTEGER,
                bezeichnung TEXT,
                beschreibung TEXT,
                erinnerungsdatum TEXT,
                abgeschlossen TEXT, 
                ergebnis TEXT
            )""")

        self.conn.commit()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS themen(id INTEGER PRIMARY KEY,
                name TEXT,
                beschreibung TEXT,
                dok_nummern TEXT,
                datenbankname TEXT
            )""")

        self.conn.commit()

    ##### Tabelle Themen
    def thema_einfuegen(self, daten):
        self.cursor.execute("""
            INSERT INTO themen (name, beschreibung, dok_nummern, datenbankname) VALUES(?,?,?,?)""", (daten[0], daten[1], daten[2], daten[3]))
        self.conn.commit()

    def thema_bearbeiten(self, nummer, daten):
        self.cursor.execute("""UPDATE themen SET
            name = :name,
            beschreibung = :beschreibung, 
            dok_nummern = :dok_nummern

            WHERE id = :id""",

            {
            'name': daten[0],
            'beschreibung': daten[1],
            'dok_nummern': daten[2],

            'id': int(nummer)
        })

        self.conn.commit()

    def themen_auslesen(self):
        self.cursor.execute("SELECT * FROM themen")
        daten = self.cursor.fetchall()
        
        return daten

    def themen_id_nummern_auslesen(self):
        self.cursor.execute("SELECT id, dok_nummern FROM themen")
        daten = self.cursor.fetchall()
        
        return daten

    ##### FILTER TEST

    def filter_test_db(self):
        self.cursor.execute("SELECT id, bezeichnung, dateiart, link FROM dokumente")
        daten = self.cursor.fetchall()

        return daten


    ##### Tabelle Erinnerungen

    def erinnerung_abschließen(self, nummer):
        self.cursor.execute("""UPDATE erinnerung SET
            abgeschlossen = :abgeschlossen

            WHERE id = :id""",

            {
            'abgeschlossen': "x",

            'id': int(nummer)
        })

        self.conn.commit()

    def erinnerung_bearbeiten(self, id, daten, ergebnis=None):
        if daten[4] == True:
            abgeschlossen = "x"
        else:
            abgeschlossen = None

        if ergebnis == None:
            ergebnis_text = None
        else:
            ergebnis_text = ergebnis

        self.cursor.execute("""UPDATE erinnerung SET
            bezeichnung = :bezeichnung,
            beschreibung = :beschreibung,
            erinnerungsdatum = :erinnerungsdatum, 
            abgeschlossen = :abgeschlossen,
            ergebnis = :ergebnis

            WHERE id = :id""",

            {
            'bezeichnung': daten[1],
            'beschreibung': daten[2],
            'erinnerungsdatum': daten[3],
            'abgeschlossen': abgeschlossen,
            'ergebnis': ergebnis_text,

            'id': int(id)
        })

        self.conn.commit()

    def ergebnisse_auslesen(self, nummer):
        self.cursor.execute("SELECT ergebnis, id FROM erinnerung WHERE dokumentennummer=?", (nummer,))
        daten = self.cursor.fetchall()

        return daten

    def erinnerung_erstellen(self, daten):
        self.cursor.execute("""
            INSERT INTO erinnerung (datenbankname, dokumentennummer, bezeichnung, beschreibung, erinnerungsdatum) VALUES(?,?,?,?,?)""", (daten[0], daten[1], daten[2], daten[3], daten[4]))
        self.conn.commit()

    def erinnerungen_auslesen(self):
        self.cursor.execute("SELECT * FROM erinnerung")
        daten = self.cursor.fetchall()

        return daten

    def datum_filtern_erinnerung(self, datum):
        self.cursor.execute("SELECT dokumentennummer, id, abgeschlossen FROM erinnerung WHERE erinnerungsdatum=?", (datum,))
        daten = self.cursor.fetchall()

        return daten

    def erinnerung_auslesen_id(self, id):
        self.cursor.execute("SELECT * FROM erinnerung WHERE id=?", (id,))
        daten = self.cursor.fetchall()

        return daten

    def erinnerung_spalte_auslesen(self, spalte, id):
        self.cursor.execute("SELECT " + spalte + " FROM erinnerung WHERE id=?", (id,))
        daten = self.cursor.fetchall()

        return daten

    ##### Tabelle Anhaenge

    def anhang_loeschen(self, nummer):
        self.cursor.execute("DELETE from anhaenge where id=?", (nummer,))
        self.conn.commit()

    def anhang_spalte_auslesen(self, spalte, doc_nummer):
        self.cursor.execute("SELECT " + spalte + " FROM anhaenge WHERE dokumentennummer=?", (doc_nummer,))
        daten = self.cursor.fetchall()

        return daten

    def neuer_anhang(self, daten):
        self.cursor.execute("""
            INSERT INTO anhaenge (dokumentennummer, bezeichnung, format, anhang) VALUES(?,?,?,?)""", (daten[0], daten[1], daten[2], daten[3]))
        self.conn.commit()

    def anhang_auslesen(self, spalte):
        self.cursor.execute("SELECT " + spalte + " FROM anhaenge")
        daten = self.cursor.fetchall()

        return daten

    def anhang_einzelwert_auslesen(self, spalte, id):
        self.cursor.execute("SELECT " + spalte + " FROM anhaenge WHERE id=?", (id,))
        daten = self.cursor.fetchall()

        return daten

    ##### Tabelle Datenbanken

    def neue_db_einfuegen(self, bezeichnung, neuer_link):
        self.cursor.execute("""
            INSERT INTO datenbanken (bezeichnung, link) VALUES(?,?)""", (bezeichnung, neuer_link))
        self.conn.commit()

    def datenbank_daten_auslesen(self, spalte):
        self.cursor.execute("SELECT " + spalte + " FROM datenbanken")
        daten = self.cursor.fetchall()
        return daten

    def datenbank_daten_auslesen_einzeln(self, spalte, id):
        self.cursor.execute("SELECT " + spalte + " FROM datenbanken WHERE id=?", (id,))
        daten = self.cursor.fetchall()

        return daten

    def datenbank_loeschen(self, nummer):
        self.cursor.execute("""UPDATE datenbanken SET
            bezeichnung = :bezeichnung,
            link = :link

            WHERE id = :id""",

            {
            'bezeichnung': "-",
            'link': "-",

            'id': int(nummer)
        })

        self.conn.commit()

    # Tabelle Workspace

    def workfile_einfuegen(self, daten):
        self.cursor.execute("""
            INSERT INTO workspace (datenbankname, nummer, datei) VALUES(?,?,?)""", (daten[0], daten[1], daten[2]))
        self.conn.commit()

    def daten_auslesen_workspace(self):
        self.cursor.execute("SELECT * FROM workspace")
        daten = self.cursor.fetchall()

        return daten

    def daten_loeschen_workspace(self, id):
        self.cursor.execute("DELETE FROM workspace WHERE id=?", (id,))
        self.conn.commit()

    def update_blob_workspace(self, nummer, blob):
        self.cursor.execute("""UPDATE workspace SET
                    datei = :datei

                    WHERE id = :id""",

                    {
                    'datei': blob,

                    'id': int(nummer)
                })

        self.conn.commit()

    # Tabelle Dokumente

    def datum_filtern(self, datum):
        self.cursor.execute("SELECT id FROM dokumente WHERE datum=?", (datum,))
        daten = self.cursor.fetchall()

        return daten

    def dokument_einfuegen(self, daten):
        self.cursor.execute("""
            INSERT INTO dokumente (datum, kategorie, bezeichnung, beschreibung, person, kommentar, datei, dateiart, link) VALUES(?,?,?,?,?,?,?,?,?)""",(daten[0], daten[1], daten[2], daten[3], daten[4], daten[5], daten[6], daten[7], "-"))
        self.conn.commit()
    
    def link_einfuegen(self, daten):
        self.cursor.execute("""
            INSERT INTO dokumente (datum, kategorie, bezeichnung, beschreibung, person, kommentar, datei, dateiart, link) VALUES(?,?,?,?,?,?,?,?,?)""",(daten[0], daten[1], daten[2], daten[3], daten[4], daten[5], "-", daten[7], daten[8]))
        self.conn.commit()
        
    def datenwerte_auslesen(self, spalte):
        self.cursor.execute("SELECT " + spalte + " FROM dokumente")
        daten = self.cursor.fetchall()

        datenliste = []

        for i in daten:
            datenliste.append(i[0])

        return datenliste

    def datenwert_auslesen_einzeln(self, spalte, id):
        self.cursor.execute("SELECT " + spalte + " FROM dokumente WHERE id=?", (id,))
        daten = self.cursor.fetchall()

        return daten

    def datenwerte_auslesen_einzeln(self, nummer):
        self.cursor.execute("SELECT * FROM dokumente WHERE id=?", (nummer,))
        daten = self.cursor.fetchall()

        return daten

    def update_blob(self, nummer, blob):
        self.cursor.execute("""UPDATE dokumente SET
                    datei = :datei

                    WHERE id = :id""",

                    {
                    'datei': blob,

                    'id': int(nummer)
                })

        self.conn.commit()

    def status_updaten(self, nummer, status):
        self.cursor.execute("""UPDATE dokumente SET
                status = :status

                WHERE id = :id""",

                {
                'status': status,

                'id': int(nummer)
            })
        self.conn.commit()


    def dokument_updaten(self, nummer, neue_daten, link=False):

        self.cursor.execute("""UPDATE dokumente SET
                datum = :datum,
                kategorie = :kategorie,
                bezeichnung = :bezeichnung,
                beschreibung = :beschreibung,
                person = :person, 
                kommentar = :kommentar

                WHERE id = :id""",

                {
                'datum': neue_daten[0],
                'kategorie': neue_daten[1],
                'bezeichnung': neue_daten[2],
                'beschreibung': neue_daten[3],
                'person': neue_daten[4],
                'kommentar': neue_daten[5],

                'id': int(nummer)
            })
        self.conn.commit()

        if neue_daten[6] != "" and neue_daten[6] != "-" and link == False:
            self.cursor.execute("""UPDATE dokumente SET
                    datei = :datei,
                    dateiart = :dateiart,
                    link = :link

                    WHERE id = :id""",

                    {
                    'datei': neue_daten[6],
                    'dateiart': neue_daten[7],
                    'link': "-",

                    'id': int(nummer)
                })

        elif neue_daten[6] != "" and neue_daten[6] != "-" and link == True:
            self.cursor.execute("""UPDATE dokumente SET
                    datei = :datei,
                    dateiart = :dateiart,
                    link = :link

                    WHERE id = :id""",

                    {
                    'datei': "-",
                    'dateiart': neue_daten[7],
                    'link': neue_daten[8],

                    'id': int(nummer)
                })

        self.conn.commit()

    def datensatz_loeschen(self, nummer):
        bezeichnung = self.datenwert_auslesen_einzeln("bezeichnung", nummer)
        if self.datenwert_auslesen_einzeln("link", nummer)[0][0] != "-":
            art_text = "Dateiart: Link"
        else:
            art_text = "Dateiart: Dokument"

        self.cursor.execute("""UPDATE dokumente SET
                datum = :datum,
                kategorie = :kategorie,
                bezeichnung = :bezeichnung,
                beschreibung = :beschreibung,
                person = :person, 
                kommentar = :kommentar,
                datei = :datei,
                dateiart = :dateiart,
                link = :link

                WHERE id = :id""",

                {
                'datum': "-",
                'kategorie': "-",
                'bezeichnung': "-",
                'beschreibung': "Datensatz (" + bezeichnung[0][0] + ") wurde am " + aktuelles_datum_de + " gelöscht...\n" + art_text,
                'person': "-",
                'kommentar': "-",
                'datei': "-",
                'dateiart': "-",
                'link': "-",

                'id': int(nummer)
            })
        self.conn.commit()

    def vakuum(self, pg_bar):
        start_size = os.path.getsize(self.datenbank)
        self.conn.execute("VACUUM")
        #pg_bar.pg.stop()
        pg_bar.destroy()
        new_size = os.path.getsize(self.datenbank)
        ersparnis = round(((start_size - new_size) / (1024*1024)), 2)
        #messagebox.showinfo("   Info", str((start_size - new_size) / (1024*1024)) + " MB wurden eingespart...", parent=window)
        messagebox.showinfo("   Info", str(ersparnis) + " MB wurden eingespart...", parent=window)

        #"{:02d}".format(number)
        #self.input_box_dateigroeße.entry.insert(0, "%.2f" % groeße + " MB")

#db = Database()

########## Standard Elemente ##########

class Button_Bar():
    def __init__(self, sheet, col_span):

        self.sheet = sheet
        self.col_span = col_span

        self.btn_frame = Frame(self.sheet, height=80, width=700, bg="#CBE8F7")
        self.btn_frame.pack()
        self.btn_frame.pack_propagate(0)

class Input_Box(Tk):
    def __init__(self, elternelement,  row=None, column=None, bild=None, first_widget=False, pady_value=(0, 0), padx_value=(0, 0), text_input=False, link=False, small=False):
        self.elternelement = elternelement
        self.row = row
        self.column = column
        self.bild = bild
        self.first_widget = first_widget
        self.pady_value = pady_value
        self.padx_value = padx_value
        self.text_input = text_input
        self.link = link
        self.small = small

        self.frame = Frame(self.elternelement, bg="white")
        self.frame.grid(row=self.row, column=self.column, pady=self.pady_value, padx=self.padx_value, sticky="W")
        self.entry_img = Label(self.frame, image=self.bild, bg="white")
        self.entry_img.grid(row=0, column=0, sticky="W")
        if self.text_input == False and self.link != False: 
            self.entry = Entry(self.frame, width=56, relief=FLAT)
        elif self.text_input == False and self.small != False: 
            self.entry = Entry(self.frame, width=20, relief=FLAT, disabledbackground="white")
        elif self.text_input == False and self.link == False:
            self.entry = Entry(self.frame, width=62, relief=FLAT)
        else:
            self.entry = Text(self.frame, width=46, height=3, relief=FLAT, wrap=WORD)
        self.entry.place(x=10, y=12)
        self.entry_img.bind("<Button-1>", lambda e: self.entry.focus_set())

        if self.first_widget != False:
            self.entry.focus_set()

class Status_Leiste:
    def __init__(self, sheet):

        self.sheet = sheet

        self.status_leiste = Label(self.sheet, text="", width=650, relief="flat", font=(15), bg="#f0f0f0", anchor='e')
        self.status_leiste.pack(side=BOTTOM)

class Combobox_customized(Tk):
    def __init__(self, window, elternelement, rahmen, rahmen_aktiv, row, column, columnspan, padx, pady, liste, disabled=False, input=False):
        self.window = window
        self.elternelement = elternelement
        self.rahmen = rahmen
        self.rahmen_aktiv = rahmen_aktiv
        self.row = row
        self.column = column
        self.columnspan = columnspan
        self.padx = padx
        self.pady = pady
        self.liste = liste
        self.disabled = disabled

        self.liste_aktiv = False
        self.aktuelles_wort = ""

        self.combobox_rahmen = Label(self.elternelement, image=self.rahmen, bg="white")
        self.combobox_rahmen.grid(row=self.row, column=self.column, columnspan=self.columnspan, padx=self.padx, pady=self.pady, sticky="W")
        self.combo_entry = Entry(self.elternelement, width=55, relief=FLAT, bg="white")
        self.combo_entry.grid(row=self.row, column=self.column, padx=7, pady=self.pady, sticky="W")
        self.combo_entry.bind("<Enter>", lambda e, x = "enter": self.combobox_change_image(e, x))
        self.combo_entry.bind("<Leave>", lambda e, x = "leave": self.combobox_change_image(e, x))
        self.combo_entry.bind("<Return>", lambda e: self.push_combobox(e, ignore=True))

        self.combo_entry.bind('<KeyRelease>', self.input_letter)
        self.combo_entry.bind('<Tab>', self.tab)

        self.combobox_rahmen.bind("<Enter>", lambda e, x = "enter": self.combobox_change_image(e, x))
        self.combobox_rahmen.bind("<Leave>", lambda e, x = "leave": self.combobox_change_image(e, x))
        self.combobox_rahmen.bind("<Button-1>", lambda e: self.push_combobox(e))

    def tab(self, event):
        self.combobox_rahmen.focus_set()

    def input_letter(self, event):
        taste = event.keysym
        #print(taste)
        if taste != "BackSpace" and taste != "Delete" and taste != "Shift_L":
            self.aktuelles_wort = self.combo_entry.get()
            self.combo_entry.delete(len(self.aktuelles_wort), END)
            for i in self.liste:
                teilstring_v = i[0:len(self.aktuelles_wort)]
                teilstring_n = i[len(self.aktuelles_wort):]

                if self.aktuelles_wort.lower() == teilstring_v.lower() and self.aktuelles_wort != "":
                    self.combo_entry.insert(END, teilstring_n)
                    self.combo_entry.selection_range(len(self.aktuelles_wort), END)
                    break

    def update_liste(self, neue_liste):
        self.liste = neue_liste

    def combobox_change_image(self, event, art):
        if art == "enter":
            self.combobox_rahmen.config(image=self.rahmen_aktiv)
        else:
            self.combobox_rahmen.config(image=self.rahmen)

    def push_combobox(self, *event, ignore=False):
        kategorie = self.combo_entry.get()
        for i in self.liste:
            if kategorie.lower() == i.lower():
                self.combo_entry.delete(0, END)
                self.combo_entry.insert(0, i)
        #print(self.liste_aktiv)
        if self.liste_aktiv == True:
            self.liste_aktiv = False
            self.auswahl_menu.destroy()
            #self.window.focus_set()
            self.combo_entry.focus_set()
            #self.window.grab_set()
            return  

        if ignore == True:
            return
                        
        self.auswahl_menu = Toplevel()

        self.auswahl_menu.geometry("398x100")
        self.auswahl_menu.geometry("+%d+%d" %(self.combobox_rahmen.winfo_rootx() + 3, self.combobox_rahmen.winfo_rooty() + 35))
        self.auswahl_menu.overrideredirect(TRUE)

        self.listbox_frame = Frame(self.auswahl_menu, highlightbackground="grey", highlightthickness=0.5)
        self.listbox_frame.pack()
        self.listbox_frame.pack_propagate()

        self.listbox_scrollbar = Scrollbar(self.listbox_frame)
        self.listbox_scrollbar.pack(side=RIGHT, fill=Y, padx=1)

        self.auswahl_listbox = Listbox(self.listbox_frame, width=100, relief=FLAT, bg="#F2F2F1", yscrollcommand=self.listbox_scrollbar.set)
        for i in self.liste:
            self.auswahl_listbox.insert(END, i)
        self.auswahl_listbox.pack()
        self.listbox_scrollbar.config(command=self.auswahl_listbox.yview)
        self.auswahl_listbox.bind("<<ListboxSelect>>", lambda e: self.ausgewaehltes_item(e))

        self.window.grab_release()
        #self.combo_entry.focus_set()

        self.liste_aktiv = True

        # Liste mit Eingabedaten aktualisieren 
        if input == False:
            neue_liste = []
            aktueller_inhalt = self.combo_entry.get().lower()
            for i in self.liste:
                if aktueller_inhalt in i.lower():
                    neue_liste.append(i)

            self.auswahl_listbox.delete(0, END)
            for i in neue_liste:
                self.auswahl_listbox.insert(END, i)

    def ausgewaehltes_item(self, event):
        change_back = False
        if self.disabled == True:
            change_back = True
            self.combo_entry.config(state="normal")
        self.combo_entry.delete(0, END)
        self.combo_entry.insert(0, self.auswahl_listbox.get(self.auswahl_listbox.curselection()))
        self.liste_aktiv = False
        self.auswahl_menu.destroy()
        if change_back == True:
            self.combo_entry.config(state="disabled", disabledbackground="white", disabledforeground="black")

    def close_combobox(self, event):
        if self.window.focus_get() != None:
            try:
                self.auswahl_menu.destroy()
                self.liste_aktiv = False
            except:
                pass

class Standard_Btn(Tk):
    def __init__(self, elternelement, icon, icon_aktiv, statusleiste, infotext, command, first=False):
        self.elternelement = elternelement
        self.icon = icon
        self.icon_aktiv = icon_aktiv
        self.statusleiste = statusleiste
        self.infotext = infotext
        self.command = command
        self.first = first

        self.btn = Button(self.elternelement, image=self.icon, relief='flat', highlightthickness=0, bd=0, bg="#CBE8F7", command=self.command)
        if self.first != False:
            self.btn.pack(side='left', padx=(20, 5), pady=10, ipadx=10, ipady=10)
        else:
            self.btn.pack(side='left', padx=5, pady=10, ipadx=10, ipady=10)
        self.btn.bind("<Enter>", lambda e, x=self.statusleiste, x1=self.infotext: self.enter_btn(e, x, x1))
        self.btn.bind("<Leave>", lambda e, x=self.statusleiste: self.leave_btn(e, x))
        self.btn.bind("<Button-1>", lambda e: self.push_button(e))

    def enter_btn(self, event, statusleiste, text):
        statusleiste.config(text=text)
        self.btn.config(image=self.icon_aktiv)
        self.btn.config(relief=SUNKEN)

    def leave_btn(self, event, statusleiste):
        statusleiste.config(text="")
        self.btn.config(image=self.icon)
        self.btn.config(relief=FLAT)

    def push_button(self, event):
        self.btn.config(activebackground='#CBE8F7')

########## Notebook Seiten ##########

class Datenbank_Management(Frame):
    def __init__(self, bilder, hauptfenster):
        super().__init__()

        self.bilder = bilder
        self.hauptfenster = hauptfenster

        self.config(bg="white")

        self.button_bar = Button_Bar(self, 3)
        self.status_leiste = Status_Leiste(self)

        self.neue_db_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[39], self.bilder[40], self.status_leiste.status_leiste, "Neue Datenbank erstellen...", command=self.hauptfenster.neu_erstellen, first=True)
        self.neue_db_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[41], self.bilder[42], self.status_leiste.status_leiste, "Markierte Datenbank laden...", command=self.hauptfenster.datenbank_laden)
        self.neue_db_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[43], self.bilder[44], self.status_leiste.status_leiste, "Markierte Datenbank löschen...", command=self.datenbank_loeschen)

        self.gesamt_frame_ui = Frame(self, bg="white")
        self.gesamt_frame_ui.pack(anchor="w", padx=35)

        self.titel = Label(self.gesamt_frame_ui, text="Datenbank Management:", bg="white")
        self.titel.grid(row=1, column=0, padx=0, pady=(15, 10), sticky="W")
        self.titel.configure(font=("Comic Sans MS", 14, "underline"))

        self.aktuelle_datenbank = Label(self.gesamt_frame_ui, text="Aktuell geladen:     Standard Dokumentendatenbank", bg="white")
        self.aktuelle_datenbank.grid(row=2, column=0, padx=0, pady=10, sticky="W")
        self.aktuelle_datenbank.config(font=("Comic Sans MS", 10))

        self.treeview_frame = Frame(self, bg="white")
        self.treeview_frame.pack(padx=(35, 0), pady=10, anchor="w")

        self.optionen_frame = Frame(self.treeview_frame, height=44)
        self.optionen_frame.pack(fill=X)
        self.optionen_frame.grid_propagate(0)

        self.datensaetze_text = Label(self.optionen_frame, text="Datenbanken:", bg="white")
        self.datensaetze_text.grid(row=0, column=0, padx=(10, 3), pady=8, ipadx=1, ipady=2, sticky="W")
        self.datensaetze_text.configure(font=("Comic Sans MS", 10))

        self.datensaetze_anzahl = Label(self.optionen_frame, text="0", bg="white", width=5, height=1)
        self.datensaetze_anzahl.grid(row=0, column=1, padx=(3, 20), pady=8, ipadx=2, ipady=1, sticky="W")
        self.datensaetze_anzahl.configure(font=("Comic Sans MS", 10))
        self.datensaetze_anzahl.grid_propagate(0)

        #self.suchen_frame = Frame(self.optionen_frame, bg="white", width=210, height=30)
        #self.suchen_frame.grid(row=0, column=4, sticky="E")
        #self.suchen_frame.grid_propagate(0)

        #self.suchen_entry = ttk.Entry(self.suchen_frame, width=27)
        #self.suchen_entry.grid(row=0, column=0, padx=(5, 0), pady=4)
        #self.suchen_entry.config(foreground="#AEADAD")
        #self.suchen_entry.insert(0, "Suchen...")
        #self.suchen_entry.bind("<Button-1>", lambda e: self.select_entry(e))
        #self.suchen_entry.bind("<Return>", lambda e: self.suchen(e))
        #self.suchen_entry.bind("<FocusOut>", lambda e: self.on_focus_out(e))

        #self.suchen_btn = Button(self.suchen_frame, image=self.bilder[25], relief='flat', highlightthickness=0, bd=0, bg="white", command=self.suchen)
        #self.suchen_btn.grid(row=0, column=1, padx=10)

        self.dokumenten_scrollbar = Scrollbar(self.treeview_frame)
        self.dokumenten_scrollbar.pack(side=RIGHT, fill=Y, padx=1)

        self.dokumenten_treeview = ttk.Treeview(self.treeview_frame, style="Treeview", height=8, yscrollcommand=self.dokumenten_scrollbar.set)

        self.dokumenten_treeview["columns"]=("Bezeichnung")
        self.dokumenten_treeview.column("#0", width=50, minwidth=50, stretch=NO)
        self.dokumenten_treeview.column("Bezeichnung", width=500, minwidth=500, stretch=NO)

        self.dokumenten_treeview.heading("#0", text="Nr.", anchor=W)
        self.dokumenten_treeview.heading("Bezeichnung", text="Bezeichnung", anchor=W)

        self.dokumenten_treeview.pack(side=TOP, fill=X, anchor="e")
        self.dokumenten_scrollbar.config(command=self.dokumenten_treeview.yview)
        self.dokumenten_treeview.bind("<ButtonRelease>", lambda e: self.daten_eintragen())
        self.dokumenten_treeview.bind('<KeyRelease-Up>', lambda e: self.daten_eintragen())
        self.dokumenten_treeview.bind('<KeyRelease-Down>', lambda e: self.daten_eintragen())

        self.daten_frame = Frame(self, bg="white")
        self.daten_frame.pack(padx=(35, 0), pady=10, anchor="w")

        self.anzahl_elemente_txt = Label(self.daten_frame, text="Datensätze:", font = "Arial 12", bg="white").grid(row=0, column=0, padx=(0, 55), pady=5, sticky="W")
        self.input_box_anzahl_elemente = Input_Box(self.daten_frame, 0, 1, self.bilder[47], pady_value=(5, 5), small=True)

        self.dateigroeße_txt = Label(self.daten_frame, text="Dateigröße:", font = "Arial 12", bg="white").grid(row=1, column=0, padx=(0, 55), pady=5, sticky="W")
        self.input_box_dateigroeße = Input_Box(self.daten_frame, 1, 1, self.bilder[47], pady_value=(5, 5), small=True)

        self.geaendert_txt = Label(self.daten_frame, text="Zuletzt geändert:", font = "Arial 12", bg="white").grid(row=2, column=0, padx=(0, 55), pady=5, sticky="W")
        self.input_box_geaendert = Input_Box(self.daten_frame, 2, 1, self.bilder[47], pady_value=(5, 5), small=True)

    def daten_eintragen(self):
        curItem = self.dokumenten_treeview.focus()
        nummer = self.dokumenten_treeview.item(curItem)["text"] - 1

        try:
            link = self.link_auslesen(nummer)[0][0]
        except:
            link = ""

        if link == "-":
            anzahl = 0
            groeße = 0
            modifikation = "-"
        elif link == "":
            anzahl = self.anzahl_datensaetze(PFAD + "/Dokumente.db")
            groeße = float(os.path.getsize(PFAD + "/Dokumente.db") / (1024*1024))
            modifikation = os.path.getmtime(PFAD + "/Dokumente.db")
        else:
            anzahl = self.anzahl_datensaetze(link)
            groeße = os.path.getsize(link) / (1024*1024)
            modifikation = os.path.getmtime(link)

        converted_modifikation = time.localtime(modifikation)
        format_modifikation = time.strftime('%d%m%Y', converted_modifikation)
        datum_modifikation = str(format_modifikation[0:2]) + "." + str(format_modifikation[2:4]) + "." + str(format_modifikation[4:8])

        self.input_box_anzahl_elemente.entry.delete(0, END)
        self.input_box_anzahl_elemente.entry.insert(0, anzahl)

        self.input_box_dateigroeße.entry.delete(0, END)
        self.input_box_dateigroeße.entry.insert(0, "%.2f" % groeße + " MB")

        self.input_box_geaendert.entry.delete(0, END)
        self.input_box_geaendert.entry.insert(0, datum_modifikation)

    def daten_leeren(self):
        self.input_box_anzahl_elemente.entry.delete(0, END)
        self.input_box_dateigroeße.entry.delete(0, END)
        self.input_box_geaendert.entry.delete(0, END)

    def anzahl_datensaetze(self, datenbank_link):
        self.conn = sqlite3.connect(datenbank_link)
        self.cursor = self.conn.cursor()

        self.cursor.execute("SELECT bezeichnung FROM dokumente")
        results = self.cursor.fetchall()

        self.conn.commit()

        return len(results)

    def link_auslesen(self, nummer):
        self.conn = sqlite3.connect(PFAD + "/Dokumente.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("SELECT link FROM datenbanken WHERE id=?", (nummer,))
        results = self.cursor.fetchall()

        self.conn.commit()

        return results

    def anzahl_datenbanken(self):
        daten = db.datenbank_daten_auslesen("Bezeichnung")

        zaehler = 0
        for i in daten:
            if i[0] == "-":
                pass
            else:
                zaehler += 1

        self.datensaetze_anzahl.config(text=zaehler + 1)
    
    def datenbank_loeschen(self):
        curItem = self.dokumenten_treeview.focus()
        nummer = self.dokumenten_treeview.item(curItem)["text"]
        
        if nummer == 1:
            messagebox.showerror("   Fehler", "Standard Datenbank kann nicht gelöscht werden...", parent=self)
        else:
            if nummer != "":
                loeschen = messagebox.askquestion ('   Löschen','Wollen Sie die markierte Datenbank löschen?', parent=self)
                if loeschen == "yes":
                    for i in window.datenbanken:
                        if int(i[0]) == int(nummer):
                            try:
                                os.remove(i[2])
                                messagebox.showinfo("   Info", "Datenbank wurde entfernt...", parent=self)
                            except:
                                window.datenbank_laden(standard=True)
                                os.remove(i[2])
                                messagebox.showinfo("   Info", "Datenbank wurde entfernt...", parent=self)

                    db.datenbank_loeschen(int(nummer) - 1)

                    for i in window.datenbanken:
                        if i[0] == int(nummer):
                            i[1] = "-"
                            i[2] = "-" 

                    window.update_db_treeview()

        self.anzahl_datenbanken()
        self.daten_leeren()


class Neues_Dokument(Frame):
    def __init__(self, bilder):
        super().__init__()

        self.bilder = bilder
        self.speicherart = 0
        self.speicherart_text = "Dokument speichern..."

        kat_daten = self.combobox_vorauswahl_aktualisieren()[0]
        personen_daten = self.combobox_vorauswahl_aktualisieren()[1]

        self.config(bg="white")

        self.button_bar = Button_Bar(self, 3)
        self.status_leiste = Status_Leiste(self)

        self.loeschen_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[9], self.bilder[10], self.status_leiste.status_leiste, "Alle Felder leeren...", command=self.input_leeren, first=True)
        self.anzeigen_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[11], self.bilder[12], self.status_leiste.status_leiste, "Ausgewähltes Dokument öffnen...", command=self.dokument_anzeigen)

        self.gesamt_frame_ui = Frame(self, bg="white")
        self.gesamt_frame_ui.pack(anchor="w", padx=35)

        self.titel_frame = Frame(self.gesamt_frame_ui, bg="white", height=30, width=560)
        self.titel_frame.grid(row=1, column=0, columnspan=3, padx=0, pady=(30, 40), sticky="W")
        self.titel_frame.grid_propagate(0)

        self.titel = Label(self.titel_frame, text="Neues Dokument einfügen:", bg="white", width=25, anchor="w")
        self.titel.grid(row=1, column=0, padx=0, pady=0, sticky="E")
        self.titel.configure(font=("Comic Sans MS", 14, "underline"))

        self.speicherart_btn = Button(self.titel_frame, image=self.bilder[33], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.speicherart_wechseln)
        self.speicherart_btn.grid(row=1, column=1, padx=215, ipady=2, ipadx=5, sticky="E")
        self.speicherart_btn.bind("<Enter>", lambda e: button_enter(self.speicherart_btn, None, self.status_leiste, self.speicherart_text))
        self.speicherart_btn.bind("<Leave>", lambda e: button_leave(self.speicherart_btn, None, self.status_leiste))

        self.datum_txt = Label(self.gesamt_frame_ui, text="Datum: *", font = "Arial 12", bg="white").grid(row=2, column=0, padx=(0, 50), pady=(10, 5), sticky="W")

        self.datum_frame = Frame(self.gesamt_frame_ui, bg="white")
        self.datum_frame.grid(row=2, column=1, pady=(10, 5), sticky="W")
        self.input_box_datum = Input_Box(self.datum_frame, 0, 0, self.bilder[6], pady_value=(5, 5), link=True)

        self.datum_btn = Button(self.datum_frame, image=self.bilder[13], relief=FLAT, bg="white", bd=0, command=lambda: self.heutiges_datum_einfuegen(self.input_box_datum.entry))
        self.datum_btn.grid(row=0, column=1, padx=7, sticky="E")
        self.datum_btn.bind("<Enter>", lambda e: button_enter(self.datum_btn, self.bilder[14], self.status_leiste, "Heutiges Datum einfügen..."))
        self.datum_btn.bind("<Leave>", lambda e: button_leave(self.datum_btn, self.bilder[13], self.status_leiste))
        self.datum_btn.bind("<Button-1>", lambda e: button_pressed(self.datum_btn, "white"))
        self.input_box_datum.entry.insert(0, aktuelles_datum_de)
        self.input_box_datum.entry.focus_set()

        self.kategorie_txt = Label(self.gesamt_frame_ui, text="Kategorie: *", font = "Arial 12", bg="white").grid(row=3, column=0, padx=(0, 50), pady=5, sticky="W")
        self.combobox_customized_kat = Combobox_customized(self, self.gesamt_frame_ui, self.bilder[4], self.bilder[5], 3, 1, 2, 0, 5, kat_daten)

        self.bezeichnung_txt = Label(self.gesamt_frame_ui, text="Bezeichnung: *", font = "Arial 12", bg="white").grid(row=4, column=0, padx=(0, 50), pady=5, sticky="W")
        self.input_box_bezeichnung = Input_Box(self.gesamt_frame_ui, 4, 1, self.bilder[0], pady_value=(5, 5))

        self.beschreibung_txt = Label(self.gesamt_frame_ui, text="Beschreibung:", font = "Arial 12", bg="white").grid(row=5, column=0, padx=(0, 50), pady=5, sticky="W")
        self.input_box_beschreibung = Input_Box(self.gesamt_frame_ui, 5, 1, self.bilder[1], pady_value=(5, 5), text_input=True)
        self.input_box_beschreibung.entry.bind("<Tab>", self.focus_next_widget)

        self.person_txt = Label(self.gesamt_frame_ui, text="Person:", font = "Arial 12", bg="white").grid(row=6, column=0, padx=(0, 50), pady=5, sticky="W")
        self.combobox_customized_person = Combobox_customized(self, self.gesamt_frame_ui, self.bilder[4], self.bilder[5], 6, 1, 2, 0, 5, personen_daten)

        self.kommentar_txt = Label(self.gesamt_frame_ui, text="Kommentar:", font = "Arial 12", bg="white").grid(row=7, column=0, padx=(0, 50), pady=5, sticky="W")
        self.input_box_kommentar = Input_Box(self.gesamt_frame_ui, 7, 1, self.bilder[0], pady_value=(5, 5))

        self.dokument_txt = Label(self.gesamt_frame_ui, text="Dokument: *", font = "Arial 12", bg="white").grid(row=8, column=0, padx=(0, 50), pady=5, sticky="W")

        self.dokument_frame = Frame(self.gesamt_frame_ui, bg="white")
        self.dokument_frame.grid(row=8, column=1, sticky="W")

        self.input_box_dokument = Input_Box(self.dokument_frame, 0, 0, self.bilder[6], pady_value=(5, 5), link=True)

        self.dokument_btn = Button(self.dokument_frame, image=self.bilder[7], relief=FLAT, bg="white", bd=0, command=self.dokument_auswaehlen)
        self.dokument_btn.grid(row=0, column=1, padx=7, sticky="E")
        self.dokument_btn.bind("<Enter>", lambda e: button_enter(self.dokument_btn, self.bilder[8], self.status_leiste, "Dokument laden..."))
        self.dokument_btn.bind("<Leave>", lambda e: button_leave(self.dokument_btn, self.bilder[7], self.status_leiste))
        self.dokument_btn.bind("<Button-1>", lambda e: button_pressed(self.dokument_btn, "white"))

        self.einfuegen_btn = Button(self.gesamt_frame_ui, image=self.bilder[2], bg="white", relief=FLAT, bd=0, command=self.dokument_einfuegen)
        self.einfuegen_btn.grid(row=9, column=1, padx=5, pady=10, sticky="E")
        self.einfuegen_btn.bind("<Enter>", lambda e: button_enter(self.einfuegen_btn, self.bilder[3], self.status_leiste, "Dokument in Datenbank einfügen..."))
        self.einfuegen_btn.bind("<Leave>", lambda e: button_leave(self.einfuegen_btn, self.bilder[2], self.status_leiste))
        self.einfuegen_btn.bind("<Button-1>", lambda e: button_pressed(self.einfuegen_btn, "white"))

    def speicherart_wechseln(self):
        if self.speicherart == 0:
            self.speicherart_btn.config(image=self.bilder[34])
            self.speicherart = 1
            self.speicherart_text = "Link speichern..."
            self.status_leiste.status_leiste.config(text="Link speichern...")
            self.titel.config(text="Neuen Link einfügen:")
        else:
            self.speicherart_btn.config(image=self.bilder[33])
            self.speicherart = 0
            self.speicherart_text = "Dokument speichern..."
            self.status_leiste.status_leiste.config(text="Dokument speichern...")
            self.titel.config(text="Neues Dokument einfügen:")


    def combobox_vorauswahl_aktualisieren(self):
        daten = []
        kat_daten = set(db.datenwerte_auslesen("kategorie"))
        personen_daten = set(db.datenwerte_auslesen("person"))
        daten.append(kat_daten)
        daten.append(personen_daten)
        return daten

    def focus_next_widget(self, event):
        event.widget.tk_focusNext().focus()
        return("break")

    def heutiges_datum_einfuegen(self, widget):
        widget.delete(0, END)
        widget.insert(0, aktuelles_datum_de)

    def dokument_auswaehlen(self):
        dokumenten_name = filedialog.askopenfilename(initialdir = "./", title = "Select file",filetypes = (("pdf files","*.pdf"),("all files","*.*")), parent=self)
        self.input_box_dokument.entry.delete(0, END)
        self.input_box_dokument.entry.insert(0, dokumenten_name)

    def dokument_einfuegen(self):
        daten = [
                    self.input_box_datum.entry.get(), self.combobox_customized_kat.combo_entry.get(), self.input_box_bezeichnung.entry.get(),
                    self.input_box_beschreibung.entry.get(1.0, END).strip(), self.combobox_customized_person.combo_entry.get(), self.input_box_kommentar.entry.get(),
                    convertToBinaryData(self.input_box_dokument.entry.get()), self.input_box_dokument.entry.get().split(".")[-1]
                ]

        if daten[0] != "" and daten[1] != "" and daten[2] != "" and daten[6] != "":
            if self.speicherart == 0:
                daten = [
                    self.input_box_datum.entry.get(), self.combobox_customized_kat.combo_entry.get(), self.input_box_bezeichnung.entry.get(),
                    self.input_box_beschreibung.entry.get(1.0, END).strip(), self.combobox_customized_person.combo_entry.get(), self.input_box_kommentar.entry.get(),
                    convertToBinaryData(self.input_box_dokument.entry.get()), self.input_box_dokument.entry.get().split(".")[-1]
                ]

                loeschen = messagebox.askquestion ('   Löschen','Wollen Sie das original Dokument löschen?', parent=self)
                if loeschen == 'yes':
                    os.remove(self.input_box_dokument.entry.get())
                else:
                    pass

                db.dokument_einfuegen(daten)

            elif self.speicherart == 1:
                daten = [
                    self.input_box_datum.entry.get(), self.combobox_customized_kat.combo_entry.get(), self.input_box_bezeichnung.entry.get(),
                    self.input_box_beschreibung.entry.get(1.0, END).strip(), self.combobox_customized_person.combo_entry.get(), self.input_box_kommentar.entry.get(),
                    "-", self.input_box_dokument.entry.get().split(".")[-1], self.input_box_dokument.entry.get()
                ]
                db.link_einfuegen(daten)

            self.input_leeren()
            messagebox.showinfo("   Info", "Dokument wurde eingefügt...", parent=self)
            Datenbank_anzeigen.treeview_update(window.tabliste[1])
            window.tabliste[1].daten_leeren(window.tabliste[1].input_box_datum.entry, window.tabliste[1].input_box_kategorie.entry, window.tabliste[1].input_box_bezeichnung.entry, window.tabliste[1].input_box_beschreibung.entry, window.tabliste[1].input_box_person.entry)

            kat_daten = self.combobox_vorauswahl_aktualisieren()[0]
            personen_daten = self.combobox_vorauswahl_aktualisieren()[1]
            self.combobox_customized_kat.update_liste(kat_daten)
            self.combobox_customized_person.update_liste(personen_daten)
                
        else:
            messagebox.showerror("   Fehler", "Bitte füllen Sie alle Pflichtfelder (*) aus...", parent=self)

        window.tab_1.datensatz = window.tab_1.daten_dict_erstellen()

    def input_leeren(self):
        self.input_box_datum.entry.delete(0, END)
        self.input_box_datum.entry.focus_set()
        self.combobox_customized_kat.combo_entry.delete(0, END)
        self.input_box_bezeichnung.entry.delete(0, END)
        self.input_box_beschreibung.entry.delete(1.0, END)
        self.combobox_customized_person.combo_entry.delete(0, END)
        self.input_box_kommentar.entry.delete(0, END)
        self.input_box_dokument.entry.delete(0, END)

    def dokument_anzeigen(self):
        os.startfile(self.input_box_dokument.entry.get())

class Datenbank_anzeigen(Frame):
    def __init__(self, bilder):
        super().__init__()

        self.kommentar_sichtbar = False

        self.bilder = bilder
        self.suche = False
        self.suche_spalten = False
        self.filter = False
        self.anhang_aktiv = False

        self.aktuelle_auswahl = []
        self.anhang_liste = []
        self.vorhandene_themen = []
        self.thema_filter = 0

        self.config(bg="white")

        self.button_bar = Button_Bar(self, 3)
        self.status_leiste = Status_Leiste(self)

        self.anzeigen_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[11], self.bilder[12], self.status_leiste.status_leiste, "Ausgewähltes Dokument öffnen...", command=self.datei_oeffnen, first=True)
        self.bearbeiten_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[15], self.bilder[16], self.status_leiste.status_leiste, "Ausgewählten Datensatz bearbeiten...", command=self.datensatz_bearbeiten)
        self.loeschen_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[9], self.bilder[10], self.status_leiste.status_leiste, "Ausgewählten Datensatz löschen...", command=self.datensatz_loeschen)
        self.suchen_btn_spalten = Standard_Btn(self.button_bar.btn_frame, self.bilder[27], self.bilder[28], self.status_leiste.status_leiste, "Datenbank nach Spalte durchsuchen...", command=self.datenbank_durchsuchen)
        self.auschecken_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[48], self.bilder[49], self.status_leiste.status_leiste, "Ausgewähltes Dokument auschecken...", command=self.dokument_auschecken)
        self.einchecken_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[52], self.bilder[53], self.status_leiste.status_leiste, "Ausgewähltes Dokument einchecken...", command=self.dokument_einchecken)
        self.anhang_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[64], self.bilder[65], self.status_leiste.status_leiste, "Anhang zu ausgewähltem Dokument hinzufügen...", command=self.anhang_anzeigen_ausblenden)

        self.gesamt_frame_ui = Frame(self, bg="white")
        self.gesamt_frame_ui.pack(anchor="w", padx=35)

        self.titel = Label(self.gesamt_frame_ui, text="Dokument laden / ändern:", bg="white")
        self.titel.grid(row=1, column=0, padx=0, pady=(20, 10), sticky="W")
        self.titel.configure(font=("Comic Sans MS", 14, "underline"))

        self.themen_filter = Button(self.gesamt_frame_ui, image=self.bilder[100], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=self.nach_thema_filtern)
        self.themen_filter.grid(row=1, column=1, padx=(110, 5), pady=(20, 10))
        self.themen_filter.bind("<Enter>", lambda e: button_enter(self.themen_filter, self.bilder[101], self.status_leiste, 'Nach Thema filtern...'))
        self.themen_filter.bind("<Leave>", lambda e: button_leave(self.themen_filter, self.bilder[100], self.status_leiste))

        self.erinnerung_filter_offen = Button(self.gesamt_frame_ui, image=self.bilder[93], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=lambda: self.filter_test("erinnerung_offen"))
        self.erinnerung_filter_offen.grid(row=1, column=2, padx=(5, 5), pady=(20, 10))
        self.erinnerung_filter_offen.bind("<Enter>", lambda e: button_enter(self.erinnerung_filter_offen, self.bilder[94], self.status_leiste, 'Nach Dokumenten mit offener Erinnerung filtern...'))
        self.erinnerung_filter_offen.bind("<Leave>", lambda e: button_leave(self.erinnerung_filter_offen, self.bilder[93], self.status_leiste))

        self.erinnerung_filter = Button(self.gesamt_frame_ui, image=self.bilder[81], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=lambda: self.filter_test("erinnerung_vorhanden"))
        self.erinnerung_filter.grid(row=1, column=3, padx=(0, 5), pady=(20, 10))
        self.erinnerung_filter.bind("<Enter>", lambda e: button_enter(self.erinnerung_filter, self.bilder[82], self.status_leiste, 'Nach allen Dokumenten mit Erinnerung filtern...'))
        self.erinnerung_filter.bind("<Leave>", lambda e: button_leave(self.erinnerung_filter, self.bilder[81], self.status_leiste))

        self.status_filter = Button(self.gesamt_frame_ui, image=self.bilder[50], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=lambda: self.filter_test("ausgecheckt"))#self.quick_filter(1))
        self.status_filter.grid(row=1, column=4, padx=(0, 5), pady=(20, 10))
        self.status_filter.bind("<Enter>", lambda e: button_enter(self.status_filter, self.bilder[51], self.status_leiste, 'Nach ausgecheckten Dokumenten filtern...'))
        self.status_filter.bind("<Leave>", lambda e: button_leave(self.status_filter, self.bilder[50], self.status_leiste))

        self.links_filter = Button(self.gesamt_frame_ui, image=self.bilder[35], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=lambda: self.filter_test("link"))#)command=lambda: self.quick_filter(0))
        self.links_filter.grid(row=1, column=5, padx=(0, 5), pady=(20, 10))
        self.links_filter.bind("<Enter>", lambda e: button_enter(self.links_filter, self.bilder[36], self.status_leiste, 'Nach Links filtern...'))
        self.links_filter.bind("<Leave>", lambda e: button_leave(self.links_filter, self.bilder[35], self.status_leiste))

        self.quickfilter = Button(self.gesamt_frame_ui, image=self.bilder[37], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=lambda: self.filter_test("none"))
        self.quickfilter.grid(row=1, column=6, padx=0, pady=(20, 10))
        self.quickfilter.bind("<Enter>", lambda e: button_enter(self.quickfilter, self.bilder[38], self.status_leiste, "Quickfilter entfernen..."))
        self.quickfilter.bind("<Leave>", lambda e: button_leave(self.quickfilter, self.bilder[37], self.status_leiste))
        self.quickfilter.config(state="disabled")

        ##### Treeview #####
        self.tree_style = ttk.Style()
        self.tree_style.configure("Treeview.Heading", foreground="#636D72")
        self.tree_style.configure("Treeview", foreground="#636D72")
        self.tree_style.map("Treeview", background=[('selected', '#559AF6')])
        
        self.treeview_frame = Frame(self, bg="white")
        self.treeview_frame.pack(padx=(35, 0), pady=10, anchor="w")

        self.optionen_frame = Frame(self.treeview_frame, height=44)
        self.optionen_frame.pack(fill=X)
        self.optionen_frame.grid_propagate(0)

        self.datensaetze_text = Label(self.optionen_frame, text="Datensätze:", bg="white")
        self.datensaetze_text.grid(row=0, column=0, padx=10, pady=8, ipadx=1, ipady=2, sticky="W")
        self.datensaetze_text.configure(font=("Comic Sans MS", 10))

        self.datensaetze_anzahl = Label(self.optionen_frame, text="0", bg="white", width=5, height=1)
        self.datensaetze_anzahl.grid(row=0, column=1, padx=(5, 202), pady=8, ipadx=2, ipady=1, sticky="W")
        self.datensaetze_anzahl.configure(font=("Comic Sans MS", 10))
        self.datensaetze_anzahl.grid_propagate(0)

        self.suchen_frame = Frame(self.optionen_frame, bg="white", width=210, height=30)
        self.suchen_frame.grid(row=0, column=3, sticky="E")
        self.suchen_frame.grid_propagate(0)

        self.suchen_entry = ttk.Entry(self.suchen_frame, width=27)
        self.suchen_entry.grid(row=0, column=0, padx=(5, 0), pady=4)
        self.suchen_entry.config(foreground="#AEADAD")
        self.suchen_entry.insert(0, "Suchen...")
        self.suchen_entry.bind("<Button-1>", lambda e: self.select_entry(e))
        self.suchen_entry.bind("<Return>", lambda e: self.suchen(e))
        self.suchen_entry.bind("<FocusOut>", lambda e: self.on_focus_out(e))

        self.suchen_btn = Button(self.suchen_frame, image=self.bilder[25], relief='flat', highlightthickness=0, bd=0, bg="white", command=self.suchen)
        self.suchen_btn.grid(row=0, column=1, padx=10)

        self.dokumenten_scrollbar = Scrollbar(self.treeview_frame)
        self.dokumenten_scrollbar.pack(side=RIGHT, fill=Y, padx=1)

        self.dokumenten_treeview = ttk.Treeview(self.treeview_frame, style="Treeview", height=6, yscrollcommand=self.dokumenten_scrollbar.set)

        self.dokumenten_treeview["columns"]=("Bezeichnung", "Dokumentenart", "Link")
        self.dokumenten_treeview.column("#0", width=50, minwidth=50, stretch=NO)
        self.dokumenten_treeview.column("Bezeichnung", width=350, minwidth=350, stretch=NO)
        self.dokumenten_treeview.column("Dokumentenart", width=100, minwidth=100, stretch=NO)
        self.dokumenten_treeview.column("Link", width=50, minwidth=50, stretch=NO)

        self.dokumenten_treeview.heading("#0", text="Nr.", anchor=W)
        self.dokumenten_treeview.heading("Bezeichnung", text="Bezeichnung", anchor=W)
        self.dokumenten_treeview.heading("Dokumentenart", text="Dokumentenart", anchor=W)
        self.dokumenten_treeview.heading("Link", text="Link", anchor=W)

        self.dokumenten_treeview.pack(side=TOP, fill=X, anchor="e")
        self.dokumenten_scrollbar.config(command=self.dokumenten_treeview.yview)
        self.dokumenten_treeview.bind("<ButtonRelease>", lambda e: self.daten_eintragen(self.input_box_datum.entry, self.input_box_kategorie.entry, self.input_box_bezeichnung.entry, self.input_box_beschreibung.entry, self.input_box_person.entry))
        self.dokumenten_treeview.bind('<KeyRelease-Up>', lambda e: self.daten_eintragen(self.input_box_datum.entry, self.input_box_kategorie.entry, self.input_box_bezeichnung.entry, self.input_box_beschreibung.entry, self.input_box_person.entry))
        self.dokumenten_treeview.bind('<KeyRelease-Down>', lambda e: self.daten_eintragen(self.input_box_datum.entry, self.input_box_kategorie.entry, self.input_box_bezeichnung.entry, self.input_box_beschreibung.entry, self.input_box_person.entry))
        self.dokumenten_treeview.bind("<Button-3>", lambda e: self.create_menu(e))
        #self.dokumenten_treeview.bind('<<TreeviewSelect>>', self.aktuell_ausgewaehlte_aktualisieren)

        self.info_frame = Frame(self, bg="white")
        self.info_frame.pack(padx=(35, 0), pady=(10, 20), anchor="w")

        self.state_info_lbl = Label(self.info_frame, text="Dokumentenstatus: ", bg="white")
        self.state_info_lbl.grid(row=0, column=0, sticky="w", pady=(10, 20))

        self.status_row = Frame(self.info_frame, bg="white", width=500, height=50)
        self.status_row.grid(row=0, column=1, columnspan=2, sticky="w")
        self.status_row.grid_propagate(0)

        self.state_lbl = Label(self.status_row, text="-", bg="white", width=10, anchor='w')
        self.state_lbl.grid(row=0, column=0, sticky="w", pady=(5, 20))

        self.arbeitsversion_btn = Button(self.status_row, image=self.bilder[54], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=self.ausgechecktes_doc_oeffnen)
        self.arbeitsversion_btn.grid(row=0, column=1, padx=(20, 5), pady=(5, 20))
        self.arbeitsversion_btn.bind("<Enter>", lambda e: button_enter(self.arbeitsversion_btn, self.bilder[55], self.status_leiste, 'Ausgechecktes Element zum Bearbeiten öffnen...'))
        self.arbeitsversion_btn.bind("<Leave>", lambda e: button_leave(self.arbeitsversion_btn, self.bilder[54], self.status_leiste))
        self.arbeitsversion_btn.config(state="disabled")

        self.workspace_aktualisieren_btn = Button(self.status_row, image=self.bilder[56], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=self.workspace_aktualisieren)
        self.workspace_aktualisieren_btn.grid(row=0, column=2, padx=(0, 5), pady=(5, 20))
        self.workspace_aktualisieren_btn.bind("<Enter>", lambda e: button_enter(self.workspace_aktualisieren_btn, self.bilder[57], self.status_leiste, 'Bearbeitete Version im Workspace speichern...'))
        self.workspace_aktualisieren_btn.bind("<Leave>", lambda e: button_leave(self.workspace_aktualisieren_btn, self.bilder[56], self.status_leiste))
        self.workspace_aktualisieren_btn.config(state="disabled")

        self.arbeitsversion_loeschen_btn = Button(self.status_row, image=self.bilder[58], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=self.workspace_version_loeschen)
        self.arbeitsversion_loeschen_btn.grid(row=0, column=3, padx=(0, 5), pady=(5, 20))
        self.arbeitsversion_loeschen_btn.bind("<Enter>", lambda e: button_enter(self.arbeitsversion_loeschen_btn, self.bilder[59], self.status_leiste, 'Ausgecheckte Version löschen und Originaldatei behalten...'))
        self.arbeitsversion_loeschen_btn.bind("<Leave>", lambda e: button_leave(self.arbeitsversion_loeschen_btn, self.bilder[58], self.status_leiste))
        self.arbeitsversion_loeschen_btn.config(state="disabled")

        self.erinnerung_btn = Button(self.status_row, image=self.bilder[76], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=self.erinnerung_erstellen)
        self.erinnerung_btn.grid(row=0, column=4, padx=(120), pady=(5, 20))
        self.erinnerung_btn.bind("<Enter>", lambda e: button_enter(self.erinnerung_btn, self.bilder[77], self.status_leiste, 'Erinnerung hinzufügen...'))
        self.erinnerung_btn.bind("<Leave>", lambda e: button_leave(self.erinnerung_btn, self.bilder[76], self.status_leiste))
        self.erinnerung_btn.config(state="disabled")

        self.datum_kategorie_frame = Frame(self.info_frame, bg="white")
        self.datum_kategorie_frame.grid(row=1, column=0, columnspan=4, pady=(5, 0), sticky="w")

        self.datum_txt = Label(self.datum_kategorie_frame, text="Datum:", font = "Arial 12", bg="white").grid(row=0, column=0, padx=(0, 110), pady=5, sticky="W")
        #self.input_box_datum = Input_Box(self.info_frame, 2, 1, self.bilder[0], pady_value=(5, 5))
        self.input_box_datum = Input_Box(self.datum_kategorie_frame, 0, 1, self.bilder[47], pady_value=(5, 5), small=True)

        self.kategorie_txt = Label(self.datum_kategorie_frame, text="Kategorie:", font = "Arial 12", bg="white").grid(row=0, column=2, padx=(30, 20), pady=5, sticky="W")
        #self.input_box_kategorie = Input_Box(self.info_frame, 3, 1, self.bilder[0], pady_value=(5, 5))
        self.input_box_kategorie = Input_Box(self.datum_kategorie_frame, 0, 3, self.bilder[47], pady_value=(5, 5), small=True)

        self.bezeichnung_txt = Label(self.info_frame, text="Bezeichnung:", font = "Arial 12", bg="white").grid(row=4, column=0, padx=(0, 50), pady=5, sticky="W")
        self.input_box_bezeichnung = Input_Box(self.info_frame, 4, 1, self.bilder[0], pady_value=(5, 5))

        self.beschreibung_frame = Frame(self.info_frame, bg="white")
        self.beschreibung_frame.grid(row=5, column=0, padx=(0, 25))

        self.beschreibung_txt = Label(self.beschreibung_frame, text="Beschreibung:", font = "Arial 12", bg="white", width=11)
        self.beschreibung_txt.grid(row=0, column=0, padx=(0, 15), pady=3, sticky="W")
        self.beschreibung_txt.grid_propagate(0)
        self.kommentar_vorhanden_btn = Button(self.beschreibung_frame, image=self.bilder[45], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=lambda: self.kommentar_anzeigen(self.beschreibung_txt))
        self.kommentar_vorhanden_btn.grid(row=0, column=1)
        self.kommentar_vorhanden_btn.config(state="disabled")
        self.kommentar_vorhanden_btn.bind("<Enter>", lambda e: button_enter(self.kommentar_vorhanden_btn, self.bilder[46], self.status_leiste, "Kommentar anzeigen..."))
        self.kommentar_vorhanden_btn.bind("<Leave>", lambda e: button_leave(self.kommentar_vorhanden_btn, self.bilder[45], self.status_leiste))

        #self.beschreibung_txt = Label(self.info_frame, text="Beschreibung:", font = "Arial 12", bg="white").grid(row=5, column=0, padx=(0, 50), pady=5, sticky="W")
        self.input_box_beschreibung = Input_Box(self.info_frame, 5, 1, self.bilder[1], pady_value=(5, 5), text_input=True)

        self.person_txt = Label(self.info_frame, text="Person:", font = "Arial 12", bg="white").grid(row=6, column=0, padx=(0, 50), pady=5, sticky="W")
        self.person_row_frame = Frame(self.info_frame, bg="white")
        self.person_row_frame.grid(row=6, column=1, pady=0, sticky="W")
        self.input_box_person = Input_Box(self.person_row_frame, 0, 0, self.bilder[47], pady_value=(5, 5), small=True)

        self.btn_frame = Frame(self.person_row_frame, bg="white")
        self.btn_frame.grid(row=0, column=1, padx=(145), pady=0)

        self.thema_vorhanden_btn = Button(self.btn_frame, image=self.bilder[100], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=self.nach_thema_filtern_quick)
        self.thema_vorhanden_btn.pack(side="left", padx=5)
        self.thema_vorhanden_btn.bind("<Enter>", lambda e: button_enter(self.thema_vorhanden_btn, self.bilder[101], self.status_leiste, 'Nach vorhandenem Thema filtern...'))
        self.thema_vorhanden_btn.bind("<Leave>", lambda e: button_leave(self.thema_vorhanden_btn, self.bilder[100], self.status_leiste))
        self.thema_vorhanden_btn.config(state="disabled")

        self.anhang_vorhanden_btn = Button(self.btn_frame, image=self.bilder[97], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=lambda: self.anhang_anzeigen_ausblenden(True))
        self.anhang_vorhanden_btn.pack(side="left")
        self.anhang_vorhanden_btn.bind("<Enter>", lambda e: button_enter(self.anhang_vorhanden_btn, self.bilder[98], self.status_leiste, 'Vorhandenen Anhang anzeigen...'))
        self.anhang_vorhanden_btn.bind("<Leave>", lambda e: button_leave(self.anhang_vorhanden_btn, self.bilder[97], self.status_leiste))
        self.anhang_vorhanden_btn.config(state="disabled")

        self.ergebnis_btn = Button(self.btn_frame, image=self.bilder[95], relief=FLAT, borderwidth=0, activebackground="white", bg="white", command=self.ergebnis_anzeigen)
        self.ergebnis_btn.pack(padx=5)
        self.ergebnis_btn.bind("<Enter>", lambda e: button_enter(self.ergebnis_btn, self.bilder[96], self.status_leiste, 'Vorhandene Ergebnisse anzeigen...'))
        self.ergebnis_btn.bind("<Leave>", lambda e: button_leave(self.ergebnis_btn, self.bilder[95], self.status_leiste))
        self.ergebnis_btn.config(state="disabled")

        # Anhang hinzufügen
        self.anhang_frame = Frame(self, bg="white")
        self.anhang_frame.pack()

        self.anhang_heading = Label(self.anhang_frame, text="Anhang hinzufügen:", bg="white")
        self.anhang_heading.pack(pady=(30, 20))
        self.anhang_heading.configure(font=("Comic Sans MS", 14, "underline"))

        self.btn_frame_anhang = Frame(self.anhang_frame, bg="white")
        self.btn_frame_anhang.pack(pady=(0, 10))

        self.anhang_hinzufuegen_btn = Button(self.btn_frame_anhang, image=self.bilder[60], bg="white", activebackground="white", relief=FLAT, bd=0, command=self.anhang_hinzufuegen)
        self.anhang_hinzufuegen_btn.grid(row=0, column=1, padx=10, sticky="E")
        self.anhang_hinzufuegen_btn.bind("<Enter>", lambda e: button_enter(self.anhang_hinzufuegen_btn, self.bilder[61], self.status_leiste, "Anhang hinzufügen..."))
        self.anhang_hinzufuegen_btn.bind("<Leave>", lambda e: button_leave(self.anhang_hinzufuegen_btn, self.bilder[60], self.status_leiste))

        self.anhang_loeschen_btn = Button(self.btn_frame_anhang, image=self.bilder[62], bg="white", activebackground="white", relief=FLAT, bd=0, command=self.anhang_loeschen)
        self.anhang_loeschen_btn.grid(row=0, column=2, padx=10, sticky="E")
        self.anhang_loeschen_btn.bind("<Enter>", lambda e: button_enter(self.anhang_loeschen_btn, self.bilder[63], self.status_leiste, "Anhang löschen..."))
        self.anhang_loeschen_btn.bind("<Leave>", lambda e: button_leave(self.anhang_loeschen_btn, self.bilder[62], self.status_leiste))

        self.treeview_frame_anhang = Frame(self.anhang_frame, bg="white")
        self.treeview_frame_anhang.pack(padx=(10, 0), pady=10, anchor="w")

        self.anhang_scrollbar = Scrollbar(self.treeview_frame_anhang)
        self.anhang_scrollbar.pack(side=RIGHT, fill=Y, padx=1)

        self.anhang_treeview = ttk.Treeview(self.treeview_frame_anhang, style="Treeview", height=4, yscrollcommand=self.anhang_scrollbar.set)

        self.anhang_treeview["columns"]=("Bezeichnung", "Format")
        self.anhang_treeview.column("#0", width=50, minwidth=50, stretch=NO)
        self.anhang_treeview.column("Bezeichnung", width=350, minwidth=350, stretch=NO)
        self.anhang_treeview.column("Format", width=100, minwidth=100, stretch=NO)

        self.anhang_treeview.heading("#0", text="Nr.", anchor=W)
        self.anhang_treeview.heading("Bezeichnung", text="Bezeichnung", anchor=W)
        self.anhang_treeview.heading("Format", text="Format", anchor=W)

        self.anhang_treeview.pack(side=TOP, fill=X, anchor="e")
        self.anhang_treeview.bind('<Double-1>', lambda e: self.anhang_oeffnen(e))
        self.anhang_scrollbar.config(command=self.anhang_treeview.yview)

        self.anhang_frame.pack_forget()

        self.disable_entrys()
        self.treeview_update()

    def select_items(self):
        for i in self.aktuelle_auswahl:
            self.dokumenten_treeview.selection_set(0)

    def aktuell_ausgewaehlte_aktualisieren(self, iid):
        self.aktuelle_auswahl = []
        for child in self.dokumenten_treeview.selection():
            #self.dokumenten_treeview.focus_set(self.dokumenten_treeview.get_children())
            #iid = self.dokumenten_treeview.focus()
            #print(self.dokumenten_treeview.identify('item', event.x, event.y))
            nummer = self.dokumenten_treeview.item(child)["text"]
            name = self.dokumenten_treeview.item(child)["values"]
            self.aktuelle_auswahl.append([nummer, name, iid])

    def nach_thema_filtern_quick(self):
        #print(self.vorhandene_themen[self.thema_filter])
        self.quick_filter_themen(self.vorhandene_themen[self.thema_filter])

        if self.thema_filter >= len(self.vorhandene_themen) - 1:
            self.thema_filter = 0
        else:
            self.thema_filter += 1

    def thema_vorhanden(self, nummer):
        self.vorhandene_themen = []
        daten = db.themen_id_nummern_auslesen()

        thema_vorhanden = False
        datenliste = []
        
        for i in daten:
            nummern_liste = i[1].split(", ")
            datenliste.append(nummern_liste)

        for i in datenliste:
            neue_liste = [feld for feld in i if feld != '']
            if str(nummer) in neue_liste:
                thema_vorhanden = True
                self.vorhandene_themen.append(neue_liste)

        return thema_vorhanden

    def thema_bearbeiten_auswahl(self):
        daten = db.themen_auslesen()

        themen = Listbox_customized(self, text="Bitte wählen Sie ein Thema:", ok_btn=True, daten=daten, themen=True, thema_bearbeiten=True)
        center(themen)

    def nach_thema_filtern(self):
        daten = db.themen_auslesen()

        themen = Listbox_customized(self, text="Bitte wählen Sie ein Thema:", ok_btn=True, daten=daten, themen=True)
        center(themen)


    def popup(self, event):
        iid = self.dokumenten_treeview.identify_row(event.y)

        if iid:
            self.dokumenten_treeview.selection_set(iid)
            self.dokumenten_treeview.focus(iid)
            self.right_click_menu.tk_popup(event.x_root, event.y_root)

    def create_menu(self, event):
        for child in self.dokumenten_treeview.selection():
            nummer = self.dokumenten_treeview.item(child)["text"]
            name = self.dokumenten_treeview.item(child)["values"]

        self.select_items()

        self.right_click_menu = Menu(self, tearoff=False)
        self.right_click_menu.add_command(label="Neues Thema erstellen", command=self.neues_Thema_erstellen)
        self.right_click_menu.add_command(label="Zu Thema hinzufügen", command=self.thema_bearbeiten_auswahl)
        self.popup(event)

    def neues_Thema_erstellen(self):
        curItem = self.dokumenten_treeview.focus()
        nummer = self.dokumenten_treeview.item(curItem)["text"]
        neues_thema = Thema_erstellen(self, [nummer])
        center(neues_thema)

    def erinnerung_erstellen(self):
        if self.erinnerung_vorhanden == False:
            erinnerung = Erinnerung_hinzufuegen(self, self.bilder, self.datensatz_anwaehlen())
            center(erinnerung)
        else:
            self.auswahl_menu = Toplevel()
            self.auswahl_menu.geometry("+%d+%d" %(self.erinnerung_btn.winfo_rootx() + 30, self.erinnerung_btn.winfo_rooty()))

            self.auswahl_menu.geometry("150x75")
            self.auswahl_menu.resizable(0, 0)
            self.auswahl_menu.config(bg="#F0F0F0")
            self.auswahl_menu.overrideredirect(TRUE)

            self.neue_erinnerung = Label(self.auswahl_menu, text=" Neue Erinnerung", anchor="w")
            self.neue_erinnerung.grid(row=0, column=0, pady=2, sticky="we")
            self.neue_erinnerung.bind("<Enter>", lambda e: self.neue_erinnerung.config(bg="#E3E3E3"))
            self.neue_erinnerung.bind("<Leave>", lambda e: self.neue_erinnerung.config(bg="#F0F0F0"))
            self.neue_erinnerung.bind("<Button-1>", lambda e, x=self.neue_erinnerung: self.menu_aktion(e, x))

            self.bearbeiten = Label(self.auswahl_menu, text=" Bestehende bearbeiten", anchor="w")
            self.bearbeiten.grid(row=1, column=0, pady=2, sticky="we")
            self.bearbeiten.bind("<Enter>", lambda e: self.bearbeiten.config(bg="#E3E3E3"))
            self.bearbeiten.bind("<Leave>", lambda e: self.bearbeiten.config(bg="#F0F0F0"))
            self.bearbeiten.bind("<Button-1>", lambda e, x=self.bearbeiten: self.menu_aktion(e, x))

            self.abbrechen = Label(self.auswahl_menu, text=" Abbrechen", anchor="w")
            self.abbrechen.grid(row=2, column=0, pady=2, sticky="we")
            self.abbrechen.bind("<Button-1>", lambda e: self.auswahl_menu_beenden())
            self.abbrechen.bind("<Enter>", lambda e: self.abbrechen.config(bg="#E3E3E3"))
            self.abbrechen.bind("<Leave>", lambda e: self.abbrechen.config(bg="#F0F0F0"))

            self.auswahl_menu.grab_set()

    def menu_aktion(self, event, btn):
        btn_value = btn.cget("text")

        if btn_value == " Neue Erinnerung":
            self.auswahl_menu.destroy()
            erinnerung = Erinnerung_hinzufuegen(self, self.bilder, self.datensatz_anwaehlen())
            center(erinnerung)
        elif btn_value == " Bestehende bearbeiten":
            self.auswahl_menu.destroy()
            erinnerung = Listbox_customized(self, text="Bitte wählen Sie eine Erinnerung:", nummer=self.datensatz_anwaehlen(), daten=None, bestehende_erinnerung=True)
            center(erinnerung)

    def auswahl_menu_beenden(self, *event):
        self.auswahl_menu.destroy()

    def anhang_oeffnen(self, *event):
        #datenbankname = window.tab_2.aktuelle_datenbank.cget("text").split(":     ")[1]
        #dok_nummer = self.datensatz_anwaehlen()

        curItem = self.anhang_treeview.focus()
        anhang_nummer = int(self.anhang_treeview.item(curItem)["text"]) - 1

        anhang_name = db.anhang_einzelwert_auslesen("bezeichnung", self.anhang_liste[anhang_nummer])[0][0]
        anhang_format = db.anhang_einzelwert_auslesen("format", self.anhang_liste[anhang_nummer])[0][0]
        anhang_blob = db.anhang_einzelwert_auslesen("anhang", self.anhang_liste[anhang_nummer])[0][0]

        with open(PFAD + "/_Anhang/" + str(anhang_name) + "." + anhang_format, "wb") as file:
            file.write(anhang_blob)

        try:
            os.startfile(PFAD + "/_Anhang/" + str(anhang_name) + "." + anhang_format)
        except:
            pass        

    def update_anhang_treeview(self, nummer):
        self.anhang_treeview.delete(*self.anhang_treeview.get_children())
        
        #liste_anhaenge = db.anhang_auslesen("dokumentennummer")
        #liste_anhang_doc = []


        #liste_bezeichnungen = db.anhang_auslesen("bezeichnung")
        #liste_format = db.anhang_auslesen("format")

        liste_bezeichnungen_neu = []
        liste_bezeichnungen = db.anhang_spalte_auslesen("bezeichnung", nummer)
        for i in liste_bezeichnungen:
            liste_bezeichnungen_neu.append(i[0])
        
        liste_format_neu = []
        liste_format = db.anhang_spalte_auslesen("format", nummer)
        for i in liste_format:
            liste_format_neu.append(i[0])

        liste_anhang_doc = db.anhang_spalte_auslesen("id", nummer)
        for i in liste_anhang_doc:
            self.anhang_liste.append(i[0])

        #zaehler = 0
        #for i in liste_anhaenge:
            #if i[0] == nummer:
                #liste_anhang_doc.append(zaehler)
            #zaehler += 1

        zaehler = 1
        for i in range(0, len(liste_anhang_doc)):
            self.anhang_treeview.insert('', 'end', text=zaehler, values=(liste_bezeichnungen_neu[i], liste_format_neu[i]))
            zaehler += 1
            

    def anhang_anzeigen_ausblenden(self, button_zwei=False):
        self.update_anhang_treeview(self.datensatz_anwaehlen())
        if self.anhang_aktiv == False:
            self.info_frame.pack_forget()
            self.anhang_frame.pack()

            if button_zwei == True:
                self.anhang_btn.btn.config(image=self.bilder[66])
            else:
                self.anhang_btn.btn.config(image=self.bilder[67])
            self.anhang_btn.icon = self.bilder[66]
            self.anhang_btn.icon_aktiv = self.bilder[67]

            self.anhang_aktiv = True
            self.dokumenten_treeview.focus_set()
        else:
            self.anhang_frame.pack_forget()
            self.info_frame.pack(padx=(35, 0), pady=(10, 20), anchor="w")

            self.anhang_btn.btn.config(image=self.bilder[65])
            self.anhang_btn.icon = self.bilder[64]
            self.anhang_btn.icon_aktiv = self.bilder[65]

            self.anhang_aktiv = False

    def anhang_hinzufuegen(self):
        doc_nummer = self.datensatz_anwaehlen()
        name = Infokasten(self, abbrechen=True)
        center(name)
        self.wait_window(name)

        if name.beendet != True:
            dokument = filedialog.askopenfilename(initialdir = "./", title = "Select file",filetypes = (("pdf files","*.pdf"),("all files","*.*")), parent=self)
            format = dokument.split("/")[-1].split(".")[-1]

            blob_datei = convertToBinaryData(dokument)

            db.neuer_anhang([doc_nummer, name.name, format, blob_datei])
            self.update_anhang_treeview(doc_nummer)
            self.anhang_liste_befuellen(self.datensatz_anwaehlen())

            messagebox.showinfo("   Info", "Anhang wurde hinzugefügt...", parent=self)

    def anhang_nummer_auslesen(self, nummer):
        nummern = db.anhang_auslesen("dokumentennummer")

        liste_zaehler = []
        zaehler = 0

        for i in nummern:
            if i[0] == nummer:
                liste_zaehler.append(zaehler)
            zaehler += 1

        return liste_zaehler

    def anhang_loeschen(self):
        loeschen = messagebox.askquestion("   Anhang löschen", "Wollen Sie den gewählten Anhang wirklich löschen?", parent=self)
        if loeschen == "yes":
            curItem = self.anhang_treeview.focus()
            anhang_nummer = int(self.anhang_treeview.item(curItem)["text"]) - 1

            anhang_id = self.anhang_liste[anhang_nummer]

            db.anhang_loeschen(anhang_id)
            self.update_anhang_treeview(self.datensatz_anwaehlen())
            self.anhang_liste_befuellen(self.datensatz_anwaehlen())

            messagebox.showinfo("   Info", "Der Anhang wurde gelöscht...", parent=self)

    def workspace_version_loeschen(self):
        loeschen = messagebox.askquestion("   Löschen", "Wollen Sie das Ausgecheckte Dokument wirklich löschen?", parent=self)
        if loeschen == "yes":
            nummer = self.datensatz_anwaehlen()
            datenbankname = window.tab_2.aktuelle_datenbank.cget("text").split(":     ")[1]
            daten_workspace = db.daten_auslesen_workspace()

            for i in daten_workspace:
                if i[1] == datenbankname and i[2] == nummer:
                    id_workspace = i[0]

            db.status_updaten(nummer, None)
            db.daten_loeschen_workspace(id_workspace)
            self.quick_filter(3)
            self.quick_filter(1)

            messagebox.showinfo("   Info", "Dokument " + str(nummer) + " wurde aus dem Workspace gelöscht...", parent=self)

    def workspace_aktualisieren(self):
        nummer = self.datensatz_anwaehlen()
        datenbankname = window.tab_2.aktuelle_datenbank.cget("text").split(":     ")[1]
        dok_art = db.datenwert_auslesen_einzeln("dateiart", nummer)[0][0]

        daten_workspace = db.daten_auslesen_workspace()

        for i in daten_workspace:
            if i[1] == datenbankname and i[2] == nummer:
                aktive_id = i[0]

        neue_datei = convertToBinaryData(PFAD + "/_Workspace/" + str(nummer) + "." + dok_art)

        db.update_blob_workspace(aktive_id, neue_datei)

        messagebox.showinfo("   Info", "Die Datei im Workspace wurde aktualisiert...", parent=self)

    def ausgechecktes_doc_oeffnen(self):
        nummer = self.datensatz_anwaehlen()
        dok_art = db.datenwert_auslesen_einzeln("dateiart", nummer)[0][0]
        datenbankname = window.tab_2.aktuelle_datenbank.cget("text").split(":     ")[1]
        workspace_daten = db.daten_auslesen_workspace()

        for i in workspace_daten:
            if i[1] == datenbankname and i[2] == nummer:
  
                if Path(PFAD + "/_Workspace/" + str(i[2]) + "." + dok_art).is_file():
                    os.startfile(PFAD + "/_Workspace/" + str(i[2]) + "." + dok_art)
                else:
                    with open(PFAD + "/_Workspace/" + str(i[2]) + "." + dok_art, "wb") as file:
                        file.write(i[3])
                        os.startfile(PFAD + "/_Workspace/" + str(i[2]) + "." + dok_art)

    def datensatz_anwaehlen(self):
        curItem = self.dokumenten_treeview.focus()
        nummer = self.dokumenten_treeview.item(curItem)["text"]
        return nummer

    def dokument_einchecken(self):
        einchecken = messagebox.askquestion("   Einchecken", "Wollen Sie den gewählten Datensatz einchecken?\nDie Originaldatei wird hierbei überschrieben...", parent=self)
        if einchecken == "yes":
            nummer = self.datensatz_anwaehlen()
            datenbankname = window.tab_2.aktuelle_datenbank.cget("text").split(":     ")[1]

            daten_workspace = db.daten_auslesen_workspace()

            for i in daten_workspace:
                if i[1] == datenbankname and i[2] == nummer:
                    neue_datei = i[3]
                    id_workspace = i[0]

            db.update_blob(nummer, neue_datei)
            db.status_updaten(nummer, None)
            db.daten_loeschen_workspace(id_workspace)
            self.quick_filter(3)
            self.quick_filter(1)

            messagebox.showinfo("   Info", "Die Datei wurde aktualisiert...", parent=self)
        
        window.tab_1.datensatz = self.daten_dict_erstellen()

    def dokument_auschecken(self):
        nummer = self.datensatz_anwaehlen()
        dokument_daten = db.datenwerte_auslesen_einzeln(nummer)
        datenbankname = window.tab_2.aktuelle_datenbank.cget("text").split(":     ")[1]

        datei = dokument_daten[0][7]

        auschecken = messagebox.askquestion("   Auschecken", "Wollen Sie den gewählten Datensatz auschecken?", parent=self)
        if auschecken == "yes":
            db.workfile_einfuegen([datenbankname, nummer, datei])
            db.status_updaten(nummer, "Ausgecheckt")

            self.state_lbl.config(text="Ausgecheckt")
            self.state_lbl.config(fg="red")
            self.arbeitsversion_btn.config(state="normal")
            self.workspace_aktualisieren_btn.config(state="normal")
            self.auschecken_btn.btn.config(state="disabled")
            self.einchecken_btn.btn.config(state="normal")
            self.arbeitsversion_loeschen_btn.config(state="normal")

        window.tab_1.datensatz = self.daten_dict_erstellen()

    def kommentar_anzeigen(self, widget):
        curItem = self.dokumenten_treeview.focus()
        nummer = self.dokumenten_treeview.item(curItem)["text"]

        if self.kommentar_sichtbar == False:
            self.kommentar_sichtbar = True
            widget.config(text="Kommentar:    ")
            #self.beschreibung_frame.config(padx=24)
            text = db.datenwerte_auslesen_einzeln(nummer)[0][6]
        else:
            self.kommentar_sichtbar = False
            widget.config(text="Beschreibung:")
            text = db.datenwerte_auslesen_einzeln(nummer)[0][4]

        self.input_box_beschreibung.entry.config(state="normal")
        self.input_box_beschreibung.entry.delete(1.0, END)
        self.input_box_beschreibung.entry.insert(1.0, text)
        self.input_box_beschreibung.entry.config(state="disabled")

    def daten_dict_erstellen(self):
        erinnerungen = db.erinnerungen_auslesen()

        daten = {}

        for child in self.dokumenten_treeview.get_children():
            status = db.datenwert_auslesen_einzeln("status", self.dokumenten_treeview.item(child)["text"])

            erinnerung_vorhanden = False
            erinnerung_offen = False

            for i in erinnerungen:
                if self.dokumenten_treeview.item(child)["text"] == i[2]:
                    erinnerung_vorhanden = True
                    if i[6] == "x":
                        pass 
                    else:
                        erinnerung_offen = True
            
            #if self.dokumenten_treeview.item(child)["text"] in erinnerungen[2]:
                #print("jop")

            if len(self.dokumenten_treeview.item(child)["values"]) == 2:
                liste = self.dokumenten_treeview.item(child)["values"]
                liste.append("")
            else:
                liste = self.dokumenten_treeview.item(child)["values"]

            liste.append(status[0][0])
            liste.append(erinnerung_vorhanden)
            liste.append(erinnerung_offen)
            
            daten[self.dokumenten_treeview.item(child)["text"]] = liste
            
        return daten

    def filter_test(self, name):
        filter_btns = [self.links_filter, self.status_filter, self.erinnerung_filter, self.erinnerung_filter_offen, self.themen_filter]
        self.dokumenten_treeview.delete(*self.dokumenten_treeview.get_children())

        if name == "link":
            for key in self.datensatz:
                if self.datensatz[key][2] == "x":
                    self.dokumenten_treeview.insert('', 'end', text=key, values=(self.datensatz[key][0], self.datensatz[key][1], "x"))
        elif name == "none":
            for key in self.datensatz:
                if self.datensatz[key][2] == "":
                    link = ""
                else:
                    link = "x"

                self.dokumenten_treeview.insert('', 'end', text=key, values=(self.datensatz[key][0], self.datensatz[key][1], link))

        elif name == "ausgecheckt":
            for key in self.datensatz:
                if self.datensatz[key][2] == "":
                    link = ""
                else:
                    link = "x"

                if self.datensatz[key][3] == "Ausgecheckt":
                    self.dokumenten_treeview.insert('', 'end', text=key, values=(self.datensatz[key][0], self.datensatz[key][1], link))

        elif name == "erinnerung_vorhanden":
            for key in self.datensatz:
                if self.datensatz[key][2] == "":
                    link = ""
                else:
                    link = "x"

                if self.datensatz[key][4] == True:
                    self.dokumenten_treeview.insert('', 'end', text=key, values=(self.datensatz[key][0], self.datensatz[key][1], link))

        elif name == "erinnerung_offen":
            for key in self.datensatz:
                if self.datensatz[key][2] == "":
                    link = ""
                else:
                    link = "x"

                if self.datensatz[key][5] == True:
                    self.dokumenten_treeview.insert('', 'end', text=key, values=(self.datensatz[key][0], self.datensatz[key][1], link))

        self.thema_vorhanden_btn.config(state="disabled")

        if self.filter == False:
            self.filter = True

            self.quickfilter.config(state="normal")
            for i in filter_btns:
                i.config(state="disabled")
        else:
            self.quickfilter.config(state="disabled")
            for i in filter_btns:
                i.config(state="normal")
            self.filter = False

        self.datensaetze_anzahl.config(text=str(len(self.dokumenten_treeview.get_children())))


    def quick_filter(self, btn_nr):
        self.erinnerung_btn.config(state="disabled")
        self.ergebnis_btn.config(state="disabled")

        if btn_nr == 4 or btn_nr == 5:
            erinnerungen = db.erinnerungen_auslesen()
            dok_erinnerungen = []
            dok_erinnerung_offen = []

            for i in erinnerungen:
                dok_erinnerungen.append(i[2])
                if i[6] != "x":
                    dok_erinnerung_offen.append(i[2])

            dok_erinnerungen = sorted(set(dok_erinnerungen))
            dok_erinnerung_offen = sorted(set(dok_erinnerung_offen))
            
        nummern = []
        if self.filter == False:
            self.filter = True
            for child in self.dokumenten_treeview.get_children():
                nummern.append(self.dokumenten_treeview.item(child)["text"])

            self.dokumenten_treeview.delete(*self.dokumenten_treeview.get_children())

            liste_bezeichnung = []
            liste_dateiart = []
            liste_link = []
            liste_status = []

            for i in nummern:
                liste_bezeichnung.append(db.datenwert_auslesen_einzeln("bezeichnung", i)[0][0])
                liste_dateiart.append(db.datenwert_auslesen_einzeln("dateiart", i)[0][0])
                liste_status.append(db.datenwert_auslesen_einzeln("status", i)[0][0])
                if db.datenwert_auslesen_einzeln("link", i)[0][0] == "-":
                    liste_link.append("")
                else:
                    liste_link.append("x")

            zaehler = 0

            for i in range(0, len(liste_link)):
                if btn_nr == 0:
                    if liste_link[i] == "x":
                        self.dokumenten_treeview.insert('', 'end', text=nummern[i], values=(liste_bezeichnung[i], liste_dateiart[i], liste_link[i]))
                        zaehler += 1
                elif btn_nr == 1:
                    if liste_status[i] == "Ausgecheckt":
                        self.dokumenten_treeview.insert('', 'end', text=nummern[i], values=(liste_bezeichnung[i], liste_dateiart[i], liste_link[i]))
                        zaehler += 1
                elif btn_nr == 4:
                    if i + 1 in dok_erinnerungen:
                        self.dokumenten_treeview.insert('', 'end', text=nummern[i], values=(liste_bezeichnung[i], liste_dateiart[i], liste_link[i]))
                        zaehler += 1
                elif btn_nr == 5:
                    if i + 1 in dok_erinnerung_offen:
                        self.dokumenten_treeview.insert('', 'end', text=nummern[i], values=(liste_bezeichnung[i], liste_dateiart[i], liste_link[i]))
                        zaehler += 1

            self.datensaetze_anzahl.config(text=zaehler)

            self.quickfilter.config(state="normal")
            #self.offene_ausblenden_filter.config(state="disabled")
            #self.nicht_gezahlt_filter.config(state="disabled")
            self.links_filter.config(state="disabled")
            self.status_filter.config(state="disabled")
            self.erinnerung_filter.config(state="disabled")
            self.erinnerung_filter_offen.config(state="disabled")
            self.themen_filter.config(state="disabled")
        else:
            self.quickfilter.config(state="disabled")
            #self.offene_ausblenden_filter.config(state="normal")
            #self.nicht_gezahlt_filter.config(state="normal")
            self.links_filter.config(state="normal")
            self.status_filter.config(state="normal")
            self.erinnerung_filter.config(state="normal")
            self.erinnerung_filter_offen.config(state="normal")
            self.themen_filter.config(state="normal")
            self.filter = False
            self.treeview_update()

    def quick_filter_themen(self, ids):
        self.quickfilter.config(state="normal")
        filter_btns = [self.links_filter, self.status_filter, self.erinnerung_filter, self.erinnerung_filter_offen, self.themen_filter]
        for i in filter_btns:
            i.config(state="disabled")

        self.filter = True
        self.dokumenten_treeview.delete(*self.dokumenten_treeview.get_children())

        liste_bezeichnung = []
        liste_dateiart = []
        liste_link = []
        liste_status = []

        for i in ids:
            liste_bezeichnung.append(db.datenwert_auslesen_einzeln("bezeichnung", i)[0][0])
            liste_dateiart.append(db.datenwert_auslesen_einzeln("dateiart", i)[0][0])
            liste_status.append(db.datenwert_auslesen_einzeln("status", i)[0][0])
            if db.datenwert_auslesen_einzeln("link", i)[0][0] == "-":
                liste_link.append("")
            else:
                liste_link.append("x")

        zaehler = 0

        for i in range(0, len(liste_link)):
            self.dokumenten_treeview.insert('', 'end', text=ids[i], values=(liste_bezeichnung[i], liste_dateiart[i], liste_link[i]))
            zaehler += 1

    def customized_filter(self, ids):
        if self.filter == False:
            self.filter = True

            self.dokumenten_treeview.delete(*self.dokumenten_treeview.get_children())

            liste_bezeichnung = []
            liste_dateiart = []
            liste_link = []
            liste_status = []

            for i in ids:
                liste_bezeichnung.append(db.datenwert_auslesen_einzeln("bezeichnung", i)[0][0])
                liste_dateiart.append(db.datenwert_auslesen_einzeln("dateiart", i)[0][0])
                liste_status.append(db.datenwert_auslesen_einzeln("status", i)[0][0])
                if db.datenwert_auslesen_einzeln("link", i)[0][0] == "-":
                    liste_link.append("")
                else:
                    liste_link.append("x")

            zaehler = 0

            for i in range(0, len(liste_link)):
                self.dokumenten_treeview.insert('', 'end', text=ids[i], values=(liste_bezeichnung[i], liste_dateiart[i], liste_link[i]))
                zaehler += 1

            self.datensaetze_anzahl.config(text=zaehler)

            self.quickfilter.config(state="normal")
            self.links_filter.config(state="disabled")
            self.status_filter.config(state="disabled")
            self.erinnerung_filter.config(state="disabled")
            self.erinnerung_filter_offen.config(state="disabled")
            self.themen_filter.config(state="disabled")
        else:
            self.quickfilter.config(state="disabled")
            self.links_filter.config(state="normal")
            self.status_filter.config(state="normal")
            self.erinnerung_filter.config(state="normal")
            self.erinnerung_filter_offen.config(state="normal")
            self.themen_filter.config(state="normal")
            self.filter = False
            self.treeview_update()

    def datenbank_durchsuchen(self):
        if self.suche_spalten == True:
            self.suche = False
            self.on_focus_out()
            self.focus_set()
            self.suchen_btn.config(image=self.bilder[25])
            self.suche_spalten = False
            self.suchen_btn_spalten.btn.config(image=self.bilder[28])
            self.suchen_btn_spalten.icon = self.bilder[27]
            self.suchen_btn_spalten.icon_aktiv = self.bilder[28]
            self.treeview_update()
        else:
            datenbank_durchsuchen = Suchen(self)
            center(datenbank_durchsuchen)

    def disable_entrys(self):
        self.input_box_datum.entry.config(state="disabled", disabledbackground="white", disabledforeground="black")
        self.input_box_kategorie.entry.config(state="disabled", disabledbackground="white", disabledforeground="black")
        self.input_box_bezeichnung.entry.config(state="disabled", disabledbackground="white", disabledforeground="black")
        self.input_box_beschreibung.entry.config(state="disabled")
        self.input_box_person.entry.config(state="disabled", disabledbackground="white", disabledforeground="black")

    def enable_entrys(self):
        self.input_box_datum.entry.config(state="normal")
        self.input_box_kategorie.entry.config(state="normal")
        self.input_box_bezeichnung.entry.config(state="normal")
        self.input_box_beschreibung.entry.config(state="normal")
        self.input_box_person.entry.config(state="normal")

    def suchen(self, *event):
        self.anzeigen_btn.btn.config(state="normal")
        self.bearbeiten_btn.btn.config(state="normal")
        self.loeschen_btn.btn.config(state="normal")
        self.daten_leeren(self.input_box_datum.entry, self.input_box_kategorie.entry, self.input_box_bezeichnung.entry, self.input_box_beschreibung.entry, self.input_box_person.entry)
        if self.suche == False:
            suchbegriff = self.suchen_entry.get().lower()

            uebereinstimmung = []

            for child in self.dokumenten_treeview.get_children():
                nummer = self.dokumenten_treeview.item(child)["text"]
                bezeichnung = self.dokumenten_treeview.item(child)['values'][0].lower()
                dateiart = self.dokumenten_treeview.item(child)['values'][1].lower()

                if suchbegriff in str(nummer) or suchbegriff in str(bezeichnung) or suchbegriff in str(dateiart):
                    uebereinstimmung.append(nummer)
                    continue

            self.dokumenten_treeview.delete(*self.dokumenten_treeview.get_children())

            for i in uebereinstimmung:
                bezeichnung = db.datenwert_auslesen_einzeln("bezeichnung", i)
                dateiart = db.datenwert_auslesen_einzeln("dateiart", i)
                link = db.datenwert_auslesen_einzeln("link", i)

                if link[0][0] == "-":
                    self.dokumenten_treeview.insert('', 'end', text=i, values=(bezeichnung[0][0], dateiart[0][0]))
                else:
                    self.dokumenten_treeview.insert('', 'end', text=i, values=(bezeichnung[0][0], dateiart[0][0], "x"))

            self.suchen_btn.config(image=self.bilder[26])
            self.suche = True
            self.datensaetze_anzahl.config(text=str(len(uebereinstimmung)))

        else:
            self.treeview_update()

            self.suchen_btn.config(image=self.bilder[25])
            self.suche = False

            self.suche_spalten = False
            self.suchen_btn_spalten.btn.config(image=self.bilder[27])
            self.suchen_btn_spalten.icon = self.bilder[27]
            self.suchen_btn_spalten.icon_aktiv = self.bilder[28]

    def on_focus_out(self, *event):
        self.suchen_entry.config(foreground="#AEADAD")
        self.suchen_entry.delete(0, END)
        self.suchen_entry.insert(0, "Suchen...")

    def select_entry(self, event):
        self.suchen_entry.delete(0, END)
        self.suchen_entry.config(foreground="black")

    def erinnerungen_pruefen(self, nummer):
        daten = db.erinnerungen_auslesen()
        self.erinnerung_vorhanden = False

        for i in daten:
            if i[2] == nummer:
                self.erinnerung_vorhanden = True

        if self.erinnerung_vorhanden == True:
            self.erinnerung_btn.config(image=self.bilder[78])
            self.erinnerung_btn.bind("<Leave>", lambda e: button_leave(self.erinnerung_btn, self.bilder[78], self.status_leiste))
        else:
            self.erinnerung_btn.config(image=self.bilder[76])
            self.erinnerung_btn.bind("<Leave>", lambda e: button_leave(self.erinnerung_btn, self.bilder[76], self.status_leiste))

    def ergebnis_vorhanden(self, nummer):
        ergebnisse = db.ergebnisse_auslesen(nummer)

        ergebnis_vorhanden = False
        
        for i in ergebnisse:
            if i[0] != "" and i[0] != None:
                ergebnis_vorhanden = True

            if ergebnis_vorhanden == True:
                self.ergebnis_btn.config(state="normal")
            else:
                self.ergebnis_btn.config(state="disabled")

    def anhang_vorhanden(self):
        curItem = self.dokumenten_treeview.focus()
        nummer = self.dokumenten_treeview.item(curItem)["text"]

        anhang_id = db.anhang_auslesen("dokumentennummer")

        anhang_vorhanden = False

        for i in anhang_id:
            if i[0] == nummer:
                anhang_vorhanden = True

        if anhang_vorhanden == True:
            self.anhang_vorhanden_btn.config(state="normal")
            self.anhang_vorhanden_btn.config(image=self.bilder[99])
            self.anhang_vorhanden_btn.bind("<Leave>", lambda e: button_leave(self.anhang_vorhanden_btn, self.bilder[99], self.status_leiste))
        else:
            self.anhang_vorhanden_btn.config(state="disabled")
            self.anhang_vorhanden_btn.config(image=self.bilder[97])
            self.anhang_vorhanden_btn.bind("<Leave>", lambda e: button_leave(self.anhang_vorhanden_btn, self.bilder[97], self.status_leiste))

    def ergebnis_anzeigen(self):  
        curItem = self.dokumenten_treeview.focus()
        nummer = self.dokumenten_treeview.item(curItem)["text"]

        ergebnisse = db.ergebnisse_auslesen(nummer)
        ergebnis_liste = []
        
        for i in ergebnisse:
            if i[0] != "" and i[0] != None:
                ergebnis_liste.append(i[0])

        self.ergebnis_fenster = Toplevel()

        self.aktuelles_ergebnis = 0

        self.ergebnis_fenster.geometry("550x300")
        self.ergebnis_fenster.resizable(0, 0)
        self.ergebnis_fenster.config(bg="#686767")
        self.ergebnis_fenster.overrideredirect(TRUE)

        self.hauptframe = Frame(self.ergebnis_fenster, bg="white", width=510, height=260)
        self.hauptframe.pack(padx=20, pady=20)
        self.hauptframe.pack_propagate(0)

        self.input_frame = Frame(self.hauptframe, bg="white")
        self.input_frame.pack(pady=(20, 5))

        self.weiter_btn = Button(self.input_frame, image=self.bilder[60], bg="white", activebackground="white", relief=FLAT, bd=0, command=lambda: self.naechstes_ergebnis(ergebnis_liste))
        self.weiter_btn.grid(row=0, column=0, padx=10, pady=20)
        self.weiter_btn.bind("<Enter>", lambda e: button_enter(self.weiter_btn, self.bilder[61]))
        self.weiter_btn.bind("<Leave>", lambda e: button_leave(self.weiter_btn, self.bilder[60]))

        self.input_box_ergebnis = Input_Box(self.input_frame, 1, 0, self.bilder[1], pady_value=(5, 5), text_input=True)
        self.input_box_ergebnis.entry.insert(1.0, ergebnis_liste[0])

        self.abbrechen_btn = Button(self.input_frame, image=self.bilder[19], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=lambda: self.ergebnis_fenster.destroy())
        self.abbrechen_btn.grid(row=2, column=0, padx=5, pady=15, ipadx=2, ipady=2)
        self.abbrechen_btn.bind("<Enter>", lambda e: button_enter(self.abbrechen_btn, self.bilder[20]))
        self.abbrechen_btn.bind("<Leave>", lambda e: button_leave(self.abbrechen_btn, self.bilder[19]))

        center(self.ergebnis_fenster)

        self.ergebnis_fenster.focus_set()
        self.ergebnis_fenster.grab_set()
        #self.combo_entry.focus_set()

    def naechstes_ergebnis(self, ergebnis_liste):
        if self.aktuelles_ergebnis + 2 <= len(ergebnis_liste):
            self.aktuelles_ergebnis += 1
        else:
            self.aktuelles_ergebnis = 0
        
        self.input_box_ergebnis.entry.delete(1.0, END)
        self.input_box_ergebnis.entry.insert(1.0, ergebnis_liste[self.aktuelles_ergebnis])

    def daten_eintragen(self, datum_widget, kategorie_widget, bezeichnung_widget, beschreibung_widget, person_widget):
        self.anhang_liste_befuellen(self.datensatz_anwaehlen())
        self.enable_entrys()
        try:
            curItem = self.dokumenten_treeview.focus()
            nummer = self.dokumenten_treeview.item(curItem)["text"]

            self.erinnerungen_pruefen(nummer)
            ergebnisse = self.ergebnis_vorhanden(nummer)
            self.anhang_vorhanden()
            
            if self.thema_vorhanden(nummer) == True:
                self.thema_vorhanden_btn.config(state="normal")
            else:
                self.thema_vorhanden_btn.config(state="disabled")

            if db.datenwerte_auslesen_einzeln(nummer)[0][10] == "Ausgecheckt":
                self.state_lbl.config(text="Ausgecheckt")
                self.state_lbl.config(fg="red")
                self.arbeitsversion_btn.config(state="normal")
                self.workspace_aktualisieren_btn.config(state="normal")
                self.arbeitsversion_loeschen_btn.config(state="normal")
                self.auschecken_btn.btn.config(state="disabled")
                self.einchecken_btn.btn.config(state="normal")
            else:
                self.state_lbl.config(text="Eingecheckt")
                self.state_lbl.config(fg="green")
                self.arbeitsversion_btn.config(state="disabled")
                self.workspace_aktualisieren_btn.config(state="disabled")
                self.arbeitsversion_loeschen_btn.config(state="disabled")
                self.auschecken_btn.btn.config(state="normal")
                self.einchecken_btn.btn.config(state="disabled")

            datum_widget.delete(0, END)
            kategorie_widget.delete(0, END)
            bezeichnung_widget.delete(0, END)
            beschreibung_widget.delete(1.0, END)
            person_widget.delete(0, END)
            datum_widget.insert(0, db.datenwerte_auslesen_einzeln(nummer)[0][1])
            kategorie_widget.insert(0, db.datenwerte_auslesen_einzeln(nummer)[0][2])
            bezeichnung_widget.insert(0, db.datenwerte_auslesen_einzeln(nummer)[0][3])
            beschreibung_widget.insert(1.0, db.datenwerte_auslesen_einzeln(nummer)[0][4])
            person_widget.insert(0, db.datenwerte_auslesen_einzeln(nummer)[0][5])

            kommentar = db.datenwerte_auslesen_einzeln(nummer)[0][6]

            if kommentar != "-" and kommentar != "":
                self.kommentar_vorhanden_btn.config(state="normal")
            elif kommentar == "-":
                self.kommentar_vorhanden_btn.config(state="disabled")
            
            self.beschreibung_txt.config(text="Beschreibung:")
            self.kommentar_sichtbar = False

            if db.datenwerte_auslesen_einzeln(nummer)[0][7] == "-" and db.datenwerte_auslesen_einzeln(nummer)[0][9] == "-":
                self.anzeigen_btn.btn.config(state="disabled")
                self.bearbeiten_btn.btn.config(state="disabled")
                self.loeschen_btn.btn.config(state="disabled")
                self.erinnerung_btn.config(state="disabled")
            else:
                self.anzeigen_btn.btn.config(state="normal")
                self.bearbeiten_btn.btn.config(state="normal")
                self.loeschen_btn.btn.config(state="normal")
                self.erinnerung_btn.config(state="normal")
        except:
            pass
        self.disable_entrys()

        if self.anhang_aktiv == True:
            #self.anhang_liste = []

            anhang_id = db.anhang_auslesen("id")
            nummern = db.anhang_auslesen("dokumentennummer")
            bezeichnung = db.anhang_auslesen("bezeichnung")
            format = db.anhang_auslesen("format")

            anhang_liste = []
            bezeichnungs_liste = []
            format_liste = []

            zaehler = -1

            for i in nummern:
                zaehler += 1
                if int(i[0]) == int(nummer):
                    anhang_liste.append(anhang_id[zaehler])
                    bezeichnungs_liste.append(bezeichnung[zaehler])
                    format_liste.append(format[zaehler])
                    #if not anhang_id[zaehler] in self.anhang_liste: 
                        #self.anhang_liste.append(anhang_id[zaehler])

            self.update_anhang_treeview(self.datensatz_anwaehlen())

    def anhang_liste_befuellen(self, nummer):
        anhaenge = db.anhang_spalte_auslesen("id", nummer)
        self.id_anhang = db.anhang_auslesen("id")

        self.anhang_liste = []
        self.gesamtliste_anhang = db.anhang_auslesen("dokumentennummer")

        #zaehler = 1
        #for i in self.gesamtliste_anhang:
            #if int(nummer) == int(i[0]):
                #self.anhang_liste.append(zaehler)
            #zaehler += 1
        for i in anhaenge:
            self.anhang_liste.append(i[0])

        #print(self.anhang_liste)

    def daten_leeren(self, datum_widget, kategorie_widget, bezeichnung_widget, beschreibung_widget, person_widget):
        self.enable_entrys()
        datum_widget.delete(0, END)
        kategorie_widget.delete(0, END)
        bezeichnung_widget.delete(0, END)
        beschreibung_widget.delete(1.0, END)
        person_widget.delete(0, END)
        self.disable_entrys()
        
    def datensatz_loeschen(self):
        curItem = self.dokumenten_treeview.focus()
        if curItem == "":
            messagebox.showerror("   Fehler", "Bitte markieren Sie ein Dokument", parent=self)
            return
        else:
            nummer = self.dokumenten_treeview.item(curItem)["text"]
        
        datensatz_loeschen = messagebox.askquestion ('   Löschen','Wollen Sie den Datensatz wirklich löschen?', parent=self)
        if datensatz_loeschen == 'yes':
            db.datensatz_loeschen(nummer)
            messagebox.showinfo("   Info", "Datensatz wurde gelöscht...", parent=self)
            self.treeview_update()
            kat_daten = Neues_Dokument.combobox_vorauswahl_aktualisieren(window.tabliste[1])[0]
            personen_daten = Neues_Dokument.combobox_vorauswahl_aktualisieren(window.tabliste[1])[1]
            window.tabliste[0].combobox_customized_kat.update_liste(kat_daten)
            window.tabliste[0].combobox_customized_person.update_liste(personen_daten)
            self.daten_leeren(self.input_box_datum.entry, self.input_box_kategorie.entry, self.input_box_bezeichnung.entry, self.input_box_beschreibung.entry, self.input_box_person.entry)

        window.tab_1.datensatz = window.tab_1.daten_dict_erstellen()

    def datensatz_bearbeiten(self):
        try:
            curItem = self.dokumenten_treeview.focus()
            nummer = self.dokumenten_treeview.item(curItem)["text"]
            daten = db.datenwerte_auslesen_einzeln(nummer)[0]
        except:
            messagebox.showerror("   Fehler", "Bitte markieren Sie ein Dokument", parent=self)
            return

        window.withdraw()
        bearbeiten = Bearbeiten(self, self.bilder, daten, nummern_liste=None)
        center(bearbeiten)

    def datei_oeffnen(self):
        try:
            curItem = self.dokumenten_treeview.focus()
            nummer = self.dokumenten_treeview.item(curItem)["text"]
            daten = db.datenwerte_auslesen_einzeln(nummer)[0]
        except:
            messagebox.showerror("   Fehler", "Bitte markieren Sie ein Dokument", parent=self)
            return

        if daten[9] == "-":
            with open(PFAD + "/_Dokumente/" + str(daten[0]) + "." + daten[8], "wb") as file:
                file.write(daten[7])

            try:
                os.startfile(PFAD + "/_Dokumente/" + str(daten[0]) + "." + daten[8])
            except:
                pass

        else:
            os.startfile(daten[9])

    def treeview_update(self):
        ids = db.datenwerte_auslesen("id")
        bezeichnung = db.datenwerte_auslesen("bezeichnung")
        dokumentart = db.datenwerte_auslesen("dateiart")
        link = db.datenwerte_auslesen("link")

        self.dokumenten_treeview.delete(*self.dokumenten_treeview.get_children())

        for i in range(0, len(ids)):
            if link[i] == "-":
                self.dokumenten_treeview.insert('', 'end', text=ids[i], values=(bezeichnung[i], dokumentart[i]))
            else:
                self.dokumenten_treeview.insert('', 'end', text=ids[i], values=(bezeichnung[i], dokumentart[i], "x"))

        self.datensaetze_anzahl.config(text=str(len(ids)))
        

class Bearbeiten(Toplevel):
    def __init__(self, first, bilder, daten, nummern_liste=None):
        super().__init__()
        
        self.first = first
        self.bilder = bilder
        self.daten = daten
        self.nummern_liste = nummern_liste

        self.speicherart = 0
        self.speicherart_text = "Dokument speichern..."

        self.geometry("700x760")
        self.resizable(0, 0)
        self.overrideredirect(TRUE)
        self.title("Dokumentendatenbank")

        kat_daten = Neues_Dokument.combobox_vorauswahl_aktualisieren(window.tabliste[1])[0]
        personen_daten = Neues_Dokument.combobox_vorauswahl_aktualisieren(window.tabliste[1])[1]

        self.hauptframe = Frame(self, bg="white", height=720, width=700)
        self.hauptframe.pack(padx=20, pady=(20, 5))
        self.hauptframe.pack_propagate(0)

        self.config(bg="#686767")

        self.button_bar = Button_Bar(self.hauptframe, 3)
        self.status_leiste = Status_Leiste(self.hauptframe)

        self.zurueck_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[21], self.bilder[22], self.status_leiste.status_leiste, "Ohne Speichern zurück...", command=self.zurueck, first=True)
        self.anzeigen_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[11], self.bilder[12], self.status_leiste.status_leiste, "Aktuelles Dokument öffnen...", command=self.aktuelles_dokument_oeffnen)
        self.anzeigen_btn_neu = Standard_Btn(self.button_bar.btn_frame, self.bilder[23], self.bilder[24], self.status_leiste.status_leiste, "Neues Dokument öffnen...", command=self.neues_dokument_anzeigen)

        self.gesamt_frame_ui = Frame(self.hauptframe, bg="white")
        self.gesamt_frame_ui.pack(anchor="w", padx=35)

        self.titel_frame = Frame(self.gesamt_frame_ui, bg="white", height=30, width=500)
        self.titel_frame.grid(row=1, column=0, columnspan=3, padx=0, pady=(10, 10), sticky="W")

        self.titel = Label(self.titel_frame, text="Ausgewähltes Dokument ändern:", bg="white")
        self.titel.grid(row=0, column=0, padx=0, pady=(10, 10), sticky="W")
        self.titel.configure(font=("Comic Sans MS", 14, "underline"))

        if self.daten[9] == "-":
            self.speicherart_btn = Button(self.titel_frame, image=self.bilder[33], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.speicherart_wechseln)
        else:
            self.speicherart = 1
            self.speicherart_text = "Link speichern..."
            self.speicherart_btn = Button(self.titel_frame, image=self.bilder[34], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.speicherart_wechseln)

        self.speicherart_btn.grid(row=0, column=1, padx=(225, 0), pady=(10, 10), ipady=2, ipadx=5, sticky="E")
        self.speicherart_btn.bind("<Enter>", lambda e: button_enter(self.speicherart_btn, None, self.status_leiste, self.speicherart_text))
        self.speicherart_btn.bind("<Leave>", lambda e: button_leave(self.speicherart_btn, None, self.status_leiste))

        self.datum_txt = Label(self.gesamt_frame_ui, text="Datum: *", font = "Arial 12", bg="white").grid(row=2, column=0, padx=(0, 50), pady=(20, 5), sticky="W")

        self.datum_frame = Frame(self.gesamt_frame_ui, bg="white")
        self.datum_frame.grid(row=2, column=1, pady=(20, 0), sticky="W")
        self.input_box_datum = Input_Box(self.datum_frame, 0, 0, self.bilder[6], pady_value=(5, 5), link=True)
        self.input_box_datum.entry.delete(0, END)
        self.input_box_datum.entry.insert(0, self.daten[1])

        self.datum_btn = Button(self.datum_frame, image=self.bilder[13], relief=FLAT, bg="white", bd=0, command=lambda: self.heutiges_datum_einfuegen(self.input_box_datum.entry))
        self.datum_btn.grid(row=0, column=1, padx=7, sticky="E")
        self.datum_btn.bind("<Enter>", lambda e: button_enter(self.datum_btn, self.bilder[14], self.status_leiste, "Heutiges Datum einfügen..."))
        self.datum_btn.bind("<Leave>", lambda e: button_leave(self.datum_btn, self.bilder[13], self.status_leiste))
        self.datum_btn.bind("<Button-1>", lambda e: button_pressed(self.datum_btn, "white"))
        #self.input_box_datum.entry.insert(0, aktuelles_datum_de)
        self.input_box_datum.entry.focus_set()

        self.kategorie_txt = Label(self.gesamt_frame_ui, text="Kategorie: *", font = "Arial 12", bg="white").grid(row=3, column=0, padx=(0, 50), pady=5, sticky="W")
        self.combobox_customized_kat = Combobox_customized(self, self.gesamt_frame_ui, self.bilder[4], self.bilder[5], 3, 1, 2, 0, 10, kat_daten)
        self.combobox_customized_kat.combo_entry.delete(0, END)
        self.combobox_customized_kat.combo_entry.insert(0, self.daten[2])

        self.bezeichnung_txt = Label(self.gesamt_frame_ui, text="Bezeichnung: *", font = "Arial 12", bg="white").grid(row=4, column=0, padx=(0, 50), pady=5, sticky="W")
        self.input_box_bezeichnung = Input_Box(self.gesamt_frame_ui, 4, 1, self.bilder[0], pady_value=(5, 5))
        self.input_box_bezeichnung.entry.delete(0, END)
        self.input_box_bezeichnung.entry.insert(0, self.daten[3])

        self.beschreibung_txt = Label(self.gesamt_frame_ui, text="Beschreibung:", font = "Arial 12", bg="white").grid(row=5, column=0, padx=(0, 50), pady=5, sticky="W")
        self.input_box_beschreibung = Input_Box(self.gesamt_frame_ui, 5, 1, self.bilder[1], pady_value=(5, 5), text_input=True)
        self.input_box_beschreibung.entry.delete(1.0, END)
        self.input_box_beschreibung.entry.insert(1.0, self.daten[4])
        #self.input_box_beschreibung.entry.bind("<Tab>", self.focus_next_widget)

        self.person_txt = Label(self.gesamt_frame_ui, text="Person:", font = "Arial 12", bg="white").grid(row=6, column=0, padx=(0, 50), pady=5, sticky="W")
        self.combobox_customized_person = Combobox_customized(self, self.gesamt_frame_ui, self.bilder[4], self.bilder[5], 6, 1, 2, 0, 10, personen_daten)
        self.combobox_customized_person.combo_entry.delete(0, END)
        self.combobox_customized_person.combo_entry.insert(0, self.daten[5])

        self.kommentar_txt = Label(self.gesamt_frame_ui, text="Kommentar:", font = "Arial 12", bg="white").grid(row=7, column=0, padx=(0, 50), pady=5, sticky="W")
        self.input_box_kommentar = Input_Box(self.gesamt_frame_ui, 7, 1, self.bilder[0], pady_value=(5, 5))
        self.input_box_kommentar.entry.delete(0, END)
        self.input_box_kommentar.entry.insert(0, self.daten[6])

        self.dokument_txt = Label(self.gesamt_frame_ui, text="Dokument Neu: *", font = "Arial 12", bg="white")
        self.dokument_txt.grid(row=8, column=0, padx=(0, 50), pady=5, sticky="W")

        self.dokument_frame = Frame(self.gesamt_frame_ui, bg="white")
        self.dokument_frame.grid(row=8, column=1, pady=5, sticky="W")

        self.input_box_dokument = Input_Box(self.dokument_frame, 0, 0, self.bilder[6], pady_value=(5, 5), link=True)

        self.dokument_btn = Button(self.dokument_frame, image=self.bilder[7], relief=FLAT, bg="white", bd=0, command=self.dokument_auswaehlen)
        self.dokument_btn.grid(row=0, column=1, padx=7, sticky="E")
        self.dokument_btn.bind("<Enter>", lambda e: button_enter(self.dokument_btn, self.bilder[8], self.status_leiste, "Dokument laden..."))
        self.dokument_btn.bind("<Leave>", lambda e: button_leave(self.dokument_btn, self.bilder[7], self.status_leiste))
        self.dokument_btn.bind("<Button-1>", lambda e: button_pressed(self.dokument_btn, "white"))

        self.btn_frame = Frame(self.gesamt_frame_ui, bg="white")
        self.btn_frame.grid(row=9, column=0, columnspan=3, pady=5, sticky="E")

        self.aendern_btn = Button(self.btn_frame, image=self.bilder[17], bg="white", relief=FLAT, bd=0, command=lambda: self.daten_aendern(self.daten[0]))
        self.aendern_btn.grid(row=0, column=0, padx=5, pady=5, sticky="E")
        self.aendern_btn.bind("<Enter>", lambda e: button_enter(self.aendern_btn, self.bilder[18], self.status_leiste, "Dokument ändern..."))
        self.aendern_btn.bind("<Leave>", lambda e: button_leave(self.aendern_btn, self.bilder[17], self.status_leiste))
        self.aendern_btn.bind("<Button-1>", lambda e: button_pressed(self.aendern_btn, "white"))

        self.focus_set()
        self.grab_set()

    def speicherart_wechseln(self):
        if self.speicherart == 0:
            self.speicherart_btn.config(image=self.bilder[34])
            self.speicherart = 1
            self.speicherart_text = "Link speichern..."
            self.status_leiste.status_leiste.config(text="Link speichern...")
        else:
            self.speicherart_btn.config(image=self.bilder[33])
            self.speicherart = 0
            self.speicherart_text = "Dokument speichern..."
            self.status_leiste.status_leiste.config(text="Dokument speichern...")

    def heutiges_datum_einfuegen(self, widget):
        widget.delete(0, END)
        widget.insert(0, aktuelles_datum_de)

    def zurueck(self):
        for child in self.first.dokumenten_treeview.get_children():
            if self.first.dokumenten_treeview.item(child)["text"] == self.daten[0]:
                self.first.enable_entrys()
                self.destroy()
                window.deiconify()
                self.first.dokumenten_treeview.selection_set(child)
                self.first.dokumenten_treeview.see(child)
                self.first.disable_entrys()
                return

    def aktuelles_dokument_oeffnen(self):
        if self.daten[9] == "-":
            with open(PFAD + "/_Dokumente/" + str(self.daten[0]) + "." + self.daten[8], "wb") as file:
                file.write(self.daten[7])
            try:
                os.startfile(PFAD + "/_Dokumente/" + str(self.daten[0]) + "." + self.daten[8])
            except:
                pass
        else:
            os.startfile(self.daten[9])

    def neues_dokument_anzeigen(self):
        os.startfile(self.input_box_dokument.entry.get())

    def dokument_auswaehlen(self):
        dokumenten_name = filedialog.askopenfilename(initialdir = "./", title = "Select file",filetypes = (("pdf files","*.pdf"),("all files","*.*")), parent=self)
        self.input_box_dokument.entry.delete(0, END)
        self.input_box_dokument.entry.insert(0, dokumenten_name)

    def daten_aendern(self, nummer):
        if self.speicherart == 0:
            neue_daten = [   
                    self.input_box_datum.entry.get(), self.combobox_customized_kat.combo_entry.get(), self.input_box_bezeichnung.entry.get(),
                    self.input_box_beschreibung.entry.get(1.0, END).strip(), self.combobox_customized_person.combo_entry.get(), self.input_box_kommentar.entry.get(), 
                    convertToBinaryData(self.input_box_dokument.entry.get()), self.input_box_dokument.entry.get().split(".")[-1], "-"
                ]
            link = False
        else:
            neue_daten = [   
                    self.input_box_datum.entry.get(), self.combobox_customized_kat.combo_entry.get(), self.input_box_bezeichnung.entry.get(),
                    self.input_box_beschreibung.entry.get(1.0, END).strip(), self.combobox_customized_person.combo_entry.get(), self.input_box_kommentar.entry.get(), 
                    "-", self.input_box_dokument.entry.get().split(".")[-1], self.input_box_dokument.entry.get()
                ]
            link = True

        datensatz_aendern = messagebox.askquestion ('   Ändern','Wollen Sie den Datensatz wirklich ändern?', parent=self)
        if datensatz_aendern == 'yes':
            db.dokument_updaten(nummer, neue_daten, link)
            messagebox.showinfo("   Info", "Dokument wurde geupdated...", parent=self)
            Datenbank_anzeigen.treeview_update(window.tabliste[1])
            kat_daten = Neues_Dokument.combobox_vorauswahl_aktualisieren(window.tabliste[1])[0]
            personen_daten = Neues_Dokument.combobox_vorauswahl_aktualisieren(window.tabliste[1])[1]
            window.tabliste[0].combobox_customized_kat.update_liste(kat_daten)
            window.tabliste[0].combobox_customized_person.update_liste(personen_daten)
            window.tabliste[1].daten_leeren(window.tabliste[1].input_box_datum.entry, window.tabliste[1].input_box_kategorie.entry, window.tabliste[1].input_box_bezeichnung.entry, window.tabliste[1].input_box_beschreibung.entry, window.tabliste[1].input_box_person.entry)

        window.tab_1.datensatz = window.tab_1.daten_dict_erstellen()

class Suchen(Toplevel):
    def __init__(self, first):
        Toplevel.__init__(self)

        self.first = first
        spalten = ["Alle Spalten durchsuchen", "Nummer", "Datum", "Kategorie", "Bezeichnung", "Beschreibung", "Person", "Kommentar", "Dateiart"]

        self.title("Suchen")
        self.minsize(550, 200)
        self.resizable(0,0)

        self.config(bg="white")

        self.such_frame = Frame(self, bg="white")
        self.such_frame.pack(padx=15, pady=30)

        self.spalte_txt = Label(self.such_frame, text="Suchspalte:", font = "Arial 12", bg="white").grid(row=0, column=0, padx=(0, 20), pady=10, sticky="W")
        self.combobox_customized_spalte = Combobox_customized(self, self.such_frame, self.first.bilder[4], self.first.bilder[5], 0, 1, 1, 0, 10, spalten, True)
        self.combobox_customized_spalte.combo_entry.insert(0, "Alle Spalten durchsuchen")
        self.combobox_customized_spalte.combo_entry.config(state="disabled", disabledbackground="white", disabledforeground="black")

        self.begriff_txt = Label(self.such_frame, text="Suchbegriff:", font = "Arial 12", bg="white").grid(row=1, column=0, padx=(0, 20), pady=10, sticky="W")
        self.input_box_begriff = Input_Box(self.such_frame, 1, 1, self.first.bilder[0], pady_value=10)
        self.input_box_begriff.entry.focus_set()
        self.input_box_begriff.entry.bind("<Return>", lambda e: self.suchen(e))

        self.suchen_btn = Button(self.such_frame, image=self.first.bilder[29], bg="white", relief=FLAT, bd=0, command=self.suchen)
        self.suchen_btn.grid(row=2, column=1, padx=5, pady=10, sticky="E")
        self.suchen_btn.bind("<Enter>", lambda e: button_enter(self.suchen_btn, self.first.bilder[30], None, ""))
        self.suchen_btn.bind("<Leave>", lambda e: button_leave(self.suchen_btn, self.first.bilder[29], None))
        self.suchen_btn.bind("<Button-1>", lambda e: button_pressed(self.suchen_btn, "white"))

        self.focus_set()
        self.grab_set()

    def suchen(self, *event):
        if self.first.suche_spalten == False:
            self.first.suche_spalten = True
            daten_gefunden = []
            list_nummer = []
            list_bezeichnung = []
            list_dateiart = []
            suchbegriff = self.input_box_begriff.entry.get()
            if self.combobox_customized_spalte.combo_entry.get() == "Alle Spalten durchsuchen":
                nummern = []

                ids = db.datenwerte_auslesen("id")
                datum = db.datenwerte_auslesen("datum")
                kategorie = db.datenwerte_auslesen("kategorie")
                bezeichnung = db.datenwerte_auslesen("bezeichnung")
                beschreibung = db.datenwerte_auslesen("beschreibung")
                person = db.datenwerte_auslesen("person") 
                kommentar = db.datenwerte_auslesen("kommentar")
                dateiart = db.datenwerte_auslesen("dateiart")
                link = db.datenwerte_auslesen("link")

                for i in range(0, len(ids)):
                    if suchbegriff.lower() in str(ids[i]) or suchbegriff.lower() in str(datum[i].lower()) or suchbegriff.lower() in str(kategorie[i].lower()) or suchbegriff.lower() in str(bezeichnung[i].lower()) or suchbegriff.lower() in str(beschreibung[i].lower()) or suchbegriff.lower() in str(person[i].lower()) or suchbegriff.lower() in str(kommentar[i].lower()) or suchbegriff.lower() in str(dateiart[i].lower()):
                        nummern.append(ids[i])

                self.first.dokumenten_treeview.delete(*self.first.dokumenten_treeview.get_children())

                for i in range(0, len(nummern)):
                    if link[nummern[i] - 1] == "-":
                        self.first.dokumenten_treeview.insert('', 'end', text=nummern[i], values=(bezeichnung[nummern[i] - 1], dateiart[nummern[i] - 1]))
                    else:
                        self.first.dokumenten_treeview.insert('', 'end', text=nummern[i], values=(bezeichnung[nummern[i] - 1], dateiart[nummern[i] - 1], "x"))

            elif self.combobox_customized_spalte.combo_entry.get() == "Nummer":
                list_nummer.append(db.datenwert_auslesen_einzeln("id", int(suchbegriff))[0][0])
                list_bezeichnung.append(db.datenwert_auslesen_einzeln("bezeichnung", int(suchbegriff))[0][0])
                list_dateiart.append(db.datenwert_auslesen_einzeln("dateiart", int(suchbegriff))[0][0])

                self.first.dokumenten_treeview.delete(*self.first.dokumenten_treeview.get_children())
            elif self.combobox_customized_spalte.combo_entry.get() != "Alle Spalten durchsuchen":
                daten = db.datenwerte_auslesen(self.combobox_customized_spalte.combo_entry.get().lower())
                zaehler = 0
                for i in daten:
                    if suchbegriff.lower() in i.lower():
                        list_nummer.append(db.datenwert_auslesen_einzeln("id", zaehler + 1)[0][0])
                        list_bezeichnung.append(db.datenwert_auslesen_einzeln("bezeichnung", zaehler + 1)[0][0])
                        list_dateiart.append(db.datenwert_auslesen_einzeln("dateiart", zaehler + 1)[0][0])
                    zaehler += 1

                self.first.dokumenten_treeview.delete(*self.first.dokumenten_treeview.get_children())

            self.destroy()

            for i in range(0, len(list_nummer)):
                self.first.dokumenten_treeview.insert('', 'end', text=list_nummer[i], values=(list_bezeichnung[i], list_dateiart[i]))

            self.first.suchen_btn_spalten.btn.config(image=self.first.bilder[31])
            self.first.suchen_btn_spalten.icon = self.first.bilder[31]
            self.first.suchen_btn_spalten.icon_aktiv = self.first.bilder[32]

            self.first.datensaetze_anzahl.config(text=str(len(self.first.dokumenten_treeview.get_children())))
        else:
            self.first.suche_spalten = False
            self.first.suchen_btn_spalten.btn.config(image=self.first.bilder[26])
            self.first.suchen_btn_spalten.icon = self.first.bilder[26]
            self.first.suchen_btn_spalten.icon_aktiv = self.first.bilder[27]

class Progress(Toplevel):
    def __init__(self, first):
        Toplevel.__init__(self)

        self.title("")
        self.minsize(300, 50)
        self.resizable(0,0)
        
        #self.config(bg="red")

        self.pg = ttk.Progressbar(self, orient='horizontal', mode='indeterminate', length=150)
        self.pg.pack(pady=20)

        #self.pg.start()

        self.focus_set()
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.disable_event)

    def disable_event(self):
        pass

class Listbox_customized(Toplevel):
    def __init__(self, first, text=None, nummer=None, ok_btn=False, daten=None, themen=False, bestehende_erinnerung=False, thema_bearbeiten=False):
        Toplevel.__init__(self)

        self.first = first
        self.text = text
        self.nummer = nummer
        self.ok_btn = ok_btn
        self.daten = daten # daten[0] = Nummer, daten[1] = Bezeichnung, daten[2] = Beschreibung
        self.themen = themen
        self.bestehende_erinnerung = bestehende_erinnerung
        self.thema_bearbeiten = thema_bearbeiten

        self.geometry("500x400")
        self.resizable(0, 0)
        self.config(bg="#686767")
        self.overrideredirect(TRUE)

        self.hauptframe = Frame(self, bg="white", width=460, height=360)
        self.hauptframe.grid(row=0, column=0, padx=20, pady=20)
        self.hauptframe.pack_propagate(0)

        self.info_lbl = Label(self.hauptframe, text=self.text, bg="white")
        self.info_lbl.pack(pady=(20, 10))
        self.info_lbl.configure(font=("Comic Sans MS", 10))

        self.treeview_frame = Frame(self.hauptframe, bg="white")
        self.treeview_frame.pack(pady=20)

        self.dokumenten_scrollbar = Scrollbar(self.treeview_frame)
        self.dokumenten_scrollbar.pack(side=RIGHT, fill=Y, padx=1)

        self.dokumenten_treeview = ttk.Treeview(self.treeview_frame, style="Treeview", height=3, yscrollcommand=self.dokumenten_scrollbar.set)

        self.dokumenten_treeview["columns"]=("Bezeichnung")
        self.dokumenten_treeview.column("#0", width=50, minwidth=50, stretch=NO)
        self.dokumenten_treeview.column("Bezeichnung", width=300, minwidth=300, stretch=NO)

        self.dokumenten_treeview.heading("#0", text="Nr.", anchor=W)
        self.dokumenten_treeview.heading("Bezeichnung", text="Bezeichnung", anchor=W)

        self.dokumenten_treeview.pack(side=TOP, fill=X, anchor="e")
        self.dokumenten_scrollbar.config(command=self.dokumenten_treeview.yview)
        self.dokumenten_treeview.bind("<ButtonRelease>", lambda e: self.bechreibung_eintragen())
        self.dokumenten_treeview.bind('<KeyRelease-Up>', lambda e: self.bechreibung_eintragen())
        self.dokumenten_treeview.bind('<KeyRelease-Down>', lambda e: self.bechreibung_eintragen())

        self.beschreibung_frame = Frame(self.hauptframe, bg="white")
        self.beschreibung_frame.pack()

        self.input_box_beschreibung = Input_Box(self.beschreibung_frame, 4, 1, self.first.bilder[1], pady_value=(5), text_input=True)
        #self.input_box_beschreibung.entry.focus_set()

        self.btn_frame = Frame(self.hauptframe, bg="white")
        self.btn_frame.pack()

        self.abbrechen_btn = Button(self.btn_frame, image=self.first.bilder[19], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=lambda: self.destroy())
        self.abbrechen_btn.pack(side="left", padx=5, pady=15, ipadx=2, ipady=2)
        self.abbrechen_btn.bind("<Enter>", lambda e: button_enter(self.abbrechen_btn, self.first.bilder[20]))
        self.abbrechen_btn.bind("<Leave>", lambda e: button_leave(self.abbrechen_btn, self.first.bilder[19]))

        if self.ok_btn == True:
            btn_image = self.first.bilder[102] 
            btn_image_aktiv = self.first.bilder[103] 
        else:
            btn_image = self.first.bilder[17]
            btn_image_aktiv = self.first.bilder[18]
        if self.thema_bearbeiten == True:
            self.aendern_btn = Button(self.btn_frame, image=btn_image, relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=lambda: self.aktives_thema_bearbeiten())
        else:
            self.aendern_btn = Button(self.btn_frame, image=btn_image, relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=lambda: self.aendern())
        self.aendern_btn.pack(padx=5, pady=15, ipadx=2, ipady=2)
        self.aendern_btn.bind("<Enter>", lambda e: button_enter(self.aendern_btn, btn_image_aktiv))
        self.aendern_btn.bind("<Leave>", lambda e: button_leave(self.aendern_btn, btn_image))

        #print(self.daten)

        self.daten_eintragen()

    def aktives_thema_bearbeiten(self):
        selected_iid = self.dokumenten_treeview.selection()[0]
        current_idx = self.dokumenten_treeview.index(selected_iid)

        themen = db.themen_auslesen()
        for i in themen:
            if str(i[0]) == str(current_idx + 1):
                bearbeitungsdaten = i

        self.destroy()
        neues_thema = Thema_erstellen(self.first, ueberschrift_text="Thema bearbeiten", ok_btn=True, bearbeitungsdaten=bearbeitungsdaten)
        center(neues_thema)

    def aendern(self):
        if self.themen == True:
            selected_iid = self.dokumenten_treeview.selection()[0]
            current_idx = self.dokumenten_treeview.index(selected_iid)

            nummern = []

            for i in self.daten[current_idx][3].split(", "):
                if i != "":
                    nummern.append(int(i))

            self.first.customized_filter(nummern)

            self.destroy()


        else:
            selected_iid = self.dokumenten_treeview.selection()[0]
            current_idx = self.dokumenten_treeview.index(selected_iid)

            daten = db.erinnerung_auslesen_id(self.ids[current_idx])

            self.destroy()
            
            #print(daten)
            self.erinnerung_bearbeiten = Erinnerung_hinzufuegen(self.first, self.first.bilder, daten[0][2], daten=daten)
            center(self.erinnerung_bearbeiten)


    def bechreibung_eintragen(self):
        if self.daten != None and self.bestehende_erinnerung == False:
            selected_iid = self.dokumenten_treeview.selection()[0]
            current_idx = self.dokumenten_treeview.index(selected_iid)

            self.input_box_beschreibung.entry.delete(1.0, END)
            self.input_box_beschreibung.entry.insert(1.0, self.daten[current_idx][2])
        else:
            selected_iid = self.dokumenten_treeview.selection()[0]
            current_idx = self.dokumenten_treeview.index(selected_iid)

            self.input_box_beschreibung.entry.delete(1.0, END)
            self.input_box_beschreibung.entry.insert(1.0, self.beschreibung[current_idx])

    def daten_eintragen(self, *event):
        if self.daten != None:
            for i in self.daten:
                self.dokumenten_treeview.insert('', 'end', text=i[0], values=(i[1], ))
        else:
            self.daten = db.erinnerungen_auslesen()
            
            zaehler = 1
            self.beschreibung = []
            self.ids = []

            for i in self.daten:
                if i[2] == self.nummer:
                    beschreibungstext = i[3]
                    self.ids.append(i[0])
                    self.beschreibung.append(i[4])
                    self.dokumenten_treeview.insert('', 'end', text=zaehler, values=(beschreibungstext, ))
                    #print(beschreibungstext)
                    zaehler += 1


        
class Infokasten(Toplevel):
    def __init__(self, first, suchen=False, kommentar=False, abbrechen=False):
        Toplevel.__init__(self)

        self.first = first
        self.suchen = suchen
        self.kommentar = kommentar
        self.abbrechen = abbrechen

        self.beendet = False

        self.geometry("500x220")
        self.resizable(0, 0)
        self.config(bg="#686767")
        self.overrideredirect(TRUE)

        if self.kommentar == True:
            self.hauptframe = Frame(self, bg="white", width=460, height=230)
        else:
            self.hauptframe = Frame(self, bg="white", width=460, height=180)
        self.hauptframe.grid(row=0, column=0, padx=20, pady=20)
        self.hauptframe.grid_propagate(0)

        if self.suchen == True:
            self.info_text = Label(self.hauptframe, text="Bitte geben Sie den Suchbegriff ein:", bg="white")
        elif self.kommentar == True:
            self.geometry("500x270")
            self.hauptframe = Frame(self, bg="white", width=460, height=230)
            self.hauptframe.grid(row=0, column=0, padx=20, pady=20)
            self.hauptframe.grid_propagate(0)
            self.info_text = Label(self.hauptframe, text="Bitte geben Sie ein Ergebnis ein:", bg="white")
        else:
            self.info_text = Label(self.hauptframe, text="Bitte geben Sie eine Bezeichnung ein:", bg="white")
        self.info_text.grid(row=0, column=0, padx=(28, 3), pady=(20, 5), ipadx=1, ipady=2, sticky="W")
        self.info_text.configure(font=("Comic Sans MS", 10))

        if self.kommentar == True:
            self.namensfeld = Input_Box(self.hauptframe, 1, 0, self.first.bilder[1], pady_value=10, padx_value=28, text_input=True)
        else:
            self.namensfeld = Input_Box(self.hauptframe, 1, 0, self.first.bilder[0], pady_value=10, padx_value=28)
        self.namensfeld.entry.focus_set()
        self.namensfeld.entry.bind("<Return>", lambda e: self.einfuegen(e))

        if self.abbrechen == True:
            self.btn_frame = Frame(self.hauptframe, bg="white")
            self.btn_frame.grid(row=2, column=0)
            self.abbrechen_btn = Button(self.btn_frame, image=self.first.bilder[19], bg="white", relief=FLAT, bd=0, command=self.close_window)
            self.abbrechen_btn.grid(row=0, column=1, padx=20, pady=10)
            self.abbrechen_btn.bind("<Enter>", lambda e: button_enter(self.abbrechen_btn, self.first.bilder[20]))
            self.abbrechen_btn.bind("<Leave>", lambda e: button_leave(self.abbrechen_btn, self.first.bilder[19]))

        if self.suchen == True:
            btn_image = self.first.bilder[29]
            btn_image_aktiv = self.first.bilder[30]
        else:
            btn_image = self.first.bilder[2]
            btn_image_aktiv = self.first.bilder[3]

        #self.einfuegen_btn = Button(self.hauptframe, image=btn_image, bg="white", relief=FLAT, bd=0, command=self.einfuegen)
        
        if self.abbrechen == True:
            self.einfuegen_btn = Button(self.btn_frame, image=btn_image, bg="white", relief=FLAT, bd=0, command=self.einfuegen)
            self.einfuegen_btn.grid(row=0, column=0, padx=20, pady=10)
        else:
            self.einfuegen_btn = Button(self.hauptframe, image=btn_image, bg="white", relief=FLAT, bd=0, command=self.einfuegen)
            self.einfuegen_btn.grid(row=2, column=0, padx=50, pady=10)

        self.einfuegen_btn.bind("<Enter>", lambda e: button_enter(self.einfuegen_btn, btn_image_aktiv))
        self.einfuegen_btn.bind("<Leave>", lambda e: button_leave(self.einfuegen_btn, btn_image))

    def close_window(self):
        self.beendet = True
        self.destroy()

        

    def einfuegen(self, *event):
        if self.kommentar == True:
            self.name = self.namensfeld.entry.get(1.0, END)
        else:
            self.name = self.namensfeld.entry.get()
        self.destroy()


class Kalender(Frame):
    def __init__(self, bilder, hauptfenster):
        super().__init__()

        self.bilder = bilder
        self.hauptfenster = hauptfenster

        self.config(bg="white")

        aktueller_tag = date.today()
        self.tagesliste = [aktueller_tag]
        self.wochentage = {"Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch", "Thursday": "Donnerstag", "Friday": "Freitag", "Saturday": "Samstag", "Sunday": "Sonntag"}
        self.dokumenten_state = True

        for i in range(1, 7):
            datum = aktueller_tag + datetime.timedelta(days=i)
            self.tagesliste.append(datum)

        # Anzahl der Dokumente zu Datum auslesen
        self.dokumente_datum = self.anzahl_dokumente_bestimmen()
        # Anzahl der Erinnerungen auslesen
        self.erinnerung_datum = self.anzahl_erinnerungen_bestimmen()

        self.button_bar = Button_Bar(self, 3)
        self.status_leiste = Status_Leiste(self)

        self.erinnerung_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[64], self.bilder[65], self.status_leiste.status_leiste, "Neue Erinnerung hinzufügen...", command=self.ueberfaellige_erinnerungen, first=True)
        self.datum_suchen_btn = Standard_Btn(self.button_bar.btn_frame, self.bilder[27], self.bilder[28], self.status_leiste.status_leiste, "Datum suchen...", command=self.datum_suchen)

        self.nav_frame = Frame(self, bg="white", width=600, height=50)
        self.nav_frame.pack(pady=(20, 0))
        self.nav_frame.pack_propagate(0)

        self.button_nav_frame_back = Frame(self.nav_frame, bg="white")
        self.button_nav_frame_back.pack(anchor="e", side="left")

        self.tag_zurueck = Button(self.button_nav_frame_back, image=self.bilder[72], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=lambda: self.tag_aendern(True))
        self.tag_zurueck.grid(row=0, column=0, pady=10, ipady=2, ipadx=2, sticky="W")
        self.tag_zurueck.bind("<Enter>", lambda e: button_enter(self.tag_zurueck, self.bilder[74], self.status_leiste, "Einen Tag zurück blättern..."))
        self.tag_zurueck.bind("<Leave>", lambda e: button_leave(self.tag_zurueck, self.bilder[72], self.status_leiste))

        self.heutiges_datum = Button(self.nav_frame, image=self.bilder[13], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.gehe_zu_heute)
        self.heutiges_datum.pack(side="left", padx=245)
        self.heutiges_datum.bind("<Enter>", lambda e: button_enter(self.heutiges_datum, self.bilder[14], self.status_leiste, "Heutiges Datum anwählen..."))
        self.heutiges_datum.bind("<Leave>", lambda e: button_leave(self.heutiges_datum, self.bilder[13], self.status_leiste))

        self.button_nav_frame_forward = Frame(self.nav_frame, bg="white")
        self.button_nav_frame_forward.pack(anchor="e")

        self.tag_vor = Button(self.button_nav_frame_forward, image=self.bilder[70], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.tag_aendern)
        self.tag_vor.grid(row=0, column=0, pady=10, ipady=2, ipadx=2, sticky="W")
        self.tag_vor.bind("<Enter>", lambda e: button_enter(self.tag_vor, self.bilder[73], self.status_leiste, "Einen Tag weiter blättern..."))
        self.tag_vor.bind("<Leave>", lambda e: button_leave(self.tag_vor, self.bilder[70], self.status_leiste))
        

        ##### Kalender #####
        self.kalender_bausteine = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}

        self.hauptframe = Frame(self, bg="white")
        self.hauptframe.pack(pady=(40, 10))

        self.label_liste = []
        self.kalender_image_liste = []
        self.color_liste = []

        for i in range(0, 7):
            tag = self.tagesliste[i]
            wochentag = tag.strftime("%A")

            if tag.strftime("%d.%m.%Y") == aktuelles_datum_de:
                kalender_img = self.bilder[69]
                kalender_color = "#FFE699"
            else:
                if wochentag == "Saturday" or wochentag == "Sunday":
                    kalender_img = self.bilder[75]
                    kalender_color = "#FBE5D6"
                else:
                    kalender_img = self.bilder[68]
                    kalender_color = "#EDEDED"

            self.bg_frame = Frame(self.hauptframe, bg="white")
            self.bg_frame.pack(side="left", padx=2)

            self.bg_lbl = Label(self.bg_frame, image=kalender_img, bg="white") 
            self.bg_lbl.grid(row=0, column=i)
            self.kalender_image_liste.append(self.bg_lbl)

            self.daten_frame = Frame(self.bg_frame, bg=kalender_color)
            self.daten_frame.grid(row=0, column=i, rowspan=3)  
            self.kalender_bausteine[i].append(self.daten_frame)          

            self.doc_frame = Frame(self.daten_frame, bg=kalender_color)
            self.doc_frame.grid(row=1, column=i)
            self.kalender_bausteine[i].append(self.doc_frame)    

            self.wochentag_lbl = Label(self.daten_frame, text=self.tagesliste[i].strftime("%d.%m.%Y") +  "\n" + self.wochentage[wochentag], bg=kalender_color)
            self.wochentag_lbl.grid(row=0, column=i)
            self.wochentag_lbl.configure(font=("Comic Sans MS", 10))
            self.wochentag_lbl.bind("<ButtonRelease>", lambda e: self.gehe_zu_datum(e))
            self.wochentag_lbl.bind("<Button-1>", lambda e: self.on_click(e))
            self.label_liste.append(self.wochentag_lbl)
            self.kalender_bausteine[i].append(self.wochentag_lbl)

            self.dokumente_lbl = Label(self.doc_frame, text="📝", bg=kalender_color)
            self.dokumente_lbl.grid(row=1, column=0, padx=4, pady=3, sticky="W")
            self.dokumente_lbl.config(font=("Comic Sans MS", 12))
            self.kalender_bausteine[i].append(self.dokumente_lbl)

            self.dokumente_lbl_anzahl = Label(self.doc_frame, text=len(self.dokumente_datum[i]), bg=kalender_color) 
            self.dokumente_lbl_anzahl.grid(row=1, column=1, padx=2, pady=3, sticky="E")
            self.dokumente_lbl_anzahl.config(font=("Comic Sans MS", 12))
            self.kalender_bausteine[i].append(self.dokumente_lbl_anzahl)

            self.reminder_lbl = Label(self.doc_frame, text="🕛", bg=kalender_color)
            self.reminder_lbl.grid(row=2, column=0, padx=4, pady=3, sticky="W")
            self.reminder_lbl.config(font=("Comic Sans MS", 12))
            self.kalender_bausteine[i].append(self.reminder_lbl)

            self.reminder_lbl_anzahl = Label(self.doc_frame, text=len(self.erinnerung_datum[i]), bg=kalender_color)
            self.reminder_lbl_anzahl.grid(row=2, column=1, padx=2, pady=3, sticky="E")
            self.reminder_lbl_anzahl.config(font=("Comic Sans MS", 12))
            self.kalender_bausteine[i].append(self.reminder_lbl_anzahl)

        self.daten_frame_tag = Frame(self, bg="white")
        self.daten_frame_tag.pack()

        tag = self.tagesliste[0]
        wochentag = tag.strftime("%A")
        woche = datetime.date(int(self.tagesliste[0].strftime("%d.%m.%Y").split(".")[2]), int(self.tagesliste[0].strftime("%d.%m.%Y").split(".")[1]), int(self.tagesliste[0].strftime("%d.%m.%Y").split(".")[0])).isocalendar()[1]

        self.tag_ueberschrift = Label(self.daten_frame_tag, text=self.tagesliste[0].strftime("%d.%m.%Y") + "  -  " + self.wochentage[wochentag] + "  -  " + "KW" + str(woche), bg="white", font=("Comic Sans MS", 14))
        self.tag_ueberschrift.pack(pady=10)

        self.auswahl_frame = Frame(self.daten_frame_tag, bg="white")
        self.auswahl_frame.pack()

        self.dok_icon = Button(self.auswahl_frame, image=self.bilder[87], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=None)
        self.dok_icon.grid(row=0, column=0, pady=(0, 10))
        self.dok_icon.bind("<Enter>", lambda e: button_enter(self.dok_icon, self.bilder[86], self.status_leiste, "Dokumente für den aktuell aktiven Tag anzeigen..."))
        self.dok_icon.bind("<Leave>", lambda e: button_leave(self.dok_icon, self.bilder[87], self.status_leiste))
        self.dok_icon.bind("<Button-1>", lambda e: self.switch_btn_state("dokument"))

        self.erinnerung_icon = Button(self.auswahl_frame, image=self.bilder[88], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=None)
        self.erinnerung_icon.grid(row=0, column=1, pady=(0, 10))
        self.erinnerung_icon.bind("<Enter>", lambda e: button_enter(self.erinnerung_icon, self.bilder[89], self.status_leiste, "Erinnerungen für den aktuell aktiven Tag anzeigen..."))
        self.erinnerung_icon.bind("<Leave>", lambda e: button_leave(self.erinnerung_icon, self.bilder[88], self.status_leiste))
        self.erinnerung_icon.bind("<Button-1>", lambda e: self.switch_btn_state("erinnerung"))

        ##### Treeview #####
        self.tree_style = ttk.Style()
        self.tree_style.configure("Treeview.Heading", foreground="#636D72")
        self.tree_style.configure("Treeview", foreground="#636D72")
        self.tree_style.map("Treeview", background=[('selected', '#559AF6')])
        
        self.treeview_frame = Frame(self.daten_frame_tag, bg="white")
        self.treeview_frame.pack()

        self.dokumenten_scrollbar = Scrollbar(self.treeview_frame)
        self.dokumenten_scrollbar.pack(side=RIGHT, fill=Y, padx=1)

        self.dokumenten_treeview = ttk.Treeview(self.treeview_frame, style="Treeview", height=3, yscrollcommand=self.dokumenten_scrollbar.set)

        self.dokumenten_treeview["columns"]=("Bezeichnung")
        self.dokumenten_treeview.column("#0", width=50, minwidth=50, stretch=NO)
        self.dokumenten_treeview.column("Bezeichnung", width=450, minwidth=450, stretch=NO)

        self.dokumenten_treeview.heading("#0", text="Nr.", anchor=W)
        self.dokumenten_treeview.heading("Bezeichnung", text="Bezeichnung", anchor=W)

        self.dokumenten_treeview.pack(side=TOP, fill=X, anchor="e")
        self.dokumenten_scrollbar.config(command=self.dokumenten_treeview.yview)
        self.dokumenten_treeview.bind('<Double-1>', lambda e: self.dokument_anzeigen(e))
        self.dokumenten_treeview.bind("<ButtonRelease-1>", lambda e: self.beschreibung_eintragen())
        self.dokumenten_treeview.bind("<Button-3>", lambda e: self.create_menu(e))
        #self.dokumenten_treeview.bind('<KeyRelease-Up>', lambda e: self.beschreibung_eintragen())
        #self.dokumenten_treeview.bind('<KeyRelease-Down>', lambda e: self.beschreibung_eintragen())
        
        self.treeview_frame_erinnerung = Frame(self.daten_frame_tag, bg="white")
        self.treeview_frame_erinnerung.pack()
        self.treeview_frame_erinnerung.pack_forget()

        self.erinnerung_scrollbar = Scrollbar(self.treeview_frame_erinnerung)
        self.erinnerung_scrollbar.pack(side=RIGHT, fill=Y, padx=1)

        self.erinnerung_treeview = ttk.Treeview(self.treeview_frame_erinnerung, style="Treeview", height=3, yscrollcommand=self.erinnerung_scrollbar.set)

        self.erinnerung_treeview["columns"]=("Bezeichnung", "Abgeschlossen")
        self.erinnerung_treeview.column("#0", width=50, minwidth=50, stretch=NO)
        self.erinnerung_treeview.column("Bezeichnung", width=350, minwidth=350, stretch=NO)
        self.erinnerung_treeview.column("Abgeschlossen", width=100, minwidth=100, stretch=NO)

        self.erinnerung_treeview.heading("#0", text="Nr.", anchor=W)
        self.erinnerung_treeview.heading("Bezeichnung", text="Bezeichnung", anchor=W)
        self.erinnerung_treeview.heading("Abgeschlossen", text="Abgeschlossen", anchor=W)

        self.erinnerung_treeview.pack(side=TOP, fill=X, anchor="e")
        self.erinnerung_scrollbar.config(command=self.erinnerung_treeview.yview)
        self.erinnerung_treeview.bind('<Double-1>', lambda e: self.dokument_anzeigen(e))
        self.erinnerung_treeview.bind("<ButtonRelease-1>", lambda e: self.beschreibung_eintragen())
        self.erinnerung_treeview.bind("<Button-3>", lambda e: self.create_menu(e))

        self.inputbox_frame = Frame(self, bg="white")
        self.inputbox_frame.pack()

        self.input_box_beschreibung = Input_Box(self.inputbox_frame, 0, 0, self.bilder[1], pady_value=(40), text_input=True)
        #if self.daten != None:
            #self.input_box_beschreibung.entry.insert(1.0, self.daten[0][4])
        #else:
            #self.input_box_beschreibung.entry.focus_set()

        self.dokumente_eintragen()

    def popup(self, event):
        iid = self.erinnerung_treeview.identify_row(event.y)

        if iid:
            self.erinnerung_treeview.selection_set(iid)
            self.erinnerung_treeview.focus(iid)
            self.right_click_menu.tk_popup(event.x_root, event.y_root)

    def create_menu(self, event):
        if self.dokumenten_state != True:
            self.right_click_menu = Menu(self, tearoff=False)
            self.right_click_menu.add_command(label="Bearbeiten", command=self.erinnerung_bearbeiten)
            self.right_click_menu.add_command(label="Abschließen", command=None)
            self.popup(event)

    def erinnerung_bearbeiten(self):
        selected_iid = self.erinnerung_treeview.selection()[0]
        current_idx = self.erinnerung_treeview.index(selected_iid)
        self.input_box_beschreibung.entry.delete(1.0, END)

        curItem = self.erinnerung_treeview.focus()
        nummer = self.erinnerung_treeview.item(curItem)["text"]
            
        erinnerungs_id = db.datum_filtern_erinnerung(self.tagesliste[0].strftime("%d.%m.%Y"))[current_idx][1]
        daten = db.erinnerung_auslesen_id(erinnerungs_id)

        erinnerung_bearbeiten = Erinnerung_hinzufuegen(self, self.bilder, nummer, daten=daten)
        center(erinnerung_bearbeiten)
        self.wait_window(erinnerung_bearbeiten)
        self.dokumente_eintragen()

    def beschreibung_eintragen(self, *event):
        self.input_box_beschreibung.entry.delete(1.0, END)
        if self.dokumenten_state == True:
            curItem = self.dokumenten_treeview.focus()
            nummer = self.dokumenten_treeview.item(curItem)["text"]

            beschreibung = db.datenwert_auslesen_einzeln("beschreibung", nummer)
            self.input_box_beschreibung.entry.insert(1.0, beschreibung[0][0])
        elif self.dokumenten_state == False:
            selected_iid = self.erinnerung_treeview.selection()[0]
            current_idx = self.erinnerung_treeview.index(selected_iid)
            
            erinnerungs_id = db.datum_filtern_erinnerung(self.tagesliste[0].strftime("%d.%m.%Y"))[current_idx][1]

            beschreibung = db.erinnerung_auslesen_id(erinnerungs_id)[0][4]
            self.input_box_beschreibung.entry.insert(1.0, beschreibung)

    def switch_btn_state(self, btn):
        self.input_box_beschreibung.entry.delete(1.0, END)
        if self.dokumenten_state == True and btn != "dokument":
            self.treeview_frame.pack_forget()
            self.treeview_frame_erinnerung.pack()
            self.dokumenten_state = False
            self.dok_icon.config(image=self.bilder[85])
            self.dok_icon.bind("<Leave>", lambda e: button_leave(self.dok_icon, self.bilder[85], self.status_leiste))
            self.erinnerung_icon.bind("<Leave>", lambda e: button_leave(self.erinnerung_icon, self.bilder[90], self.status_leiste))
        elif self.dokumenten_state == False and btn != "erinnerung":
            self.treeview_frame_erinnerung.pack_forget()
            self.treeview_frame.pack()
            self.dokumenten_state = True
            self.erinnerung_icon.config(image=self.bilder[88])
            self.erinnerung_icon.bind("<Leave>", lambda e: button_leave(self.erinnerung_icon, self.bilder[88], self.status_leiste))
            self.dok_icon.bind("<Leave>", lambda e: button_leave(self.dok_icon, self.bilder[87], self.status_leiste))
            
        self.dokumente_eintragen()

    def dokument_anzeigen(self, *event):
        if self.dokumenten_state == True:
            curItem = self.dokumenten_treeview.focus()
            nummer = self.dokumenten_treeview.item(curItem)["text"]

        else:
            curItem = self.erinnerung_treeview.focus()
            nummer = self.erinnerung_treeview.item(curItem)["text"]

        if window.tab_1.filter == True:
            window.tab_1.quick_filter(3)
            
        window.tab_1.customized_filter([nummer])

        window.notebook.select(window.tab_1)

    def dokumente_eintragen(self):
        self.dokumenten_treeview.delete(*self.dokumenten_treeview.get_children())
        self.erinnerung_treeview.delete(*self.erinnerung_treeview.get_children())

        if self.dokumenten_state == True:
            daten = db.datum_filtern(self.tagesliste[0].strftime("%d.%m.%Y"))
            for i in daten:
                self.dokumenten_treeview.insert('', 'end', text=i[0], values=(db.datenwert_auslesen_einzeln("bezeichnung", i[0])[0]))

        elif self.dokumenten_state == False:
            daten = db.datum_filtern_erinnerung(self.tagesliste[0].strftime("%d.%m.%Y"))
            for i in daten:
                if i[2] != None:
                    abgeschlossen = "x"
                else:
                    abgeschlossen = ""
                self.erinnerung_treeview.insert('', 'end', text=i[0], values=(db.datenwert_auslesen_einzeln("bezeichnung", i[0])[0][0], abgeschlossen))

    def datum_schreiben(self):
        tag = self.tagesliste[0]
        wochentag = tag.strftime("%A")
        woche = datetime.date(int(self.tagesliste[0].strftime("%d.%m.%Y").split(".")[2]), int(self.tagesliste[0].strftime("%d.%m.%Y").split(".")[1]), int(self.tagesliste[0].strftime("%d.%m.%Y").split(".")[0])).isocalendar()[1]
        self.tag_ueberschrift.config(text=self.tagesliste[0].strftime("%d.%m.%Y") + "  -  " + self.wochentage[wochentag] + "  -  " + "KW" + str(woche))

    def datum_suchen(self):
        datum = Infokasten(self, True)
        center(datum)
        self.wait_window(datum)

        self.gehe_zu_heute(datum.name)
        self.datum_schreiben()
        self.dokumente_eintragen()

    def dokumenten_anzahl_lbl_aendern(self):
        for i in self.kalender_bausteine:
            datums_daten = self.anzahl_dokumente_bestimmen()[i]
            self.kalender_bausteine[i][4].config(text=len(datums_daten))

    def erinnerung_anzahl_lbl_aendern(self):
        for i in self.kalender_bausteine:
            datums_daten = self.anzahl_erinnerungen_bestimmen()[i]
            self.kalender_bausteine[i][6].config(text=len(datums_daten))

    def ueberfaellige_erinnerungen(self):
        self.ueberfaellige = []
        daten = db.erinnerungen_auslesen()

        for i in daten:
            if i[6] != "x":
                erinnerungs_datum = datetime.datetime.strptime(i[5], "%d.%m.%Y").date()

                if erinnerungs_datum < aktuelles_datum:
                    self.ueberfaellige.append(i)

        if self.ueberfaellige == []:
            self.ueberfaellige.append([])

        return self.ueberfaellige

    def anzahl_erinnerungen_bestimmen(self):
        self.datenliste = []
        for i in self.tagesliste:
            daten = db.datum_filtern_erinnerung(i.strftime("%d.%m.%Y"))
            self.datenliste.append(daten)
        
        return self.datenliste 

    def anzahl_dokumente_bestimmen(self):
        self.datenliste = []
        for i in self.tagesliste:
            daten = db.datum_filtern(i.strftime("%d.%m.%Y"))
            self.datenliste.append(daten)
        
        return self.datenliste

    def gehe_zu_datum(self, event):
        #print(event.widget.cget("text").split("\n")[0])
        #event.widget.config(relief="flat")
        self.gehe_zu_heute(event.widget.cget("text").split("\n")[0])

    def on_click(self, event):
        #event.widget.config(relief=SUNKEN)
        event.widget.config(bg="white")

    def farbe_einstellen(self):
        for i in range(0, 7):
            tag = self.tagesliste[i]
            wochentag = tag.strftime("%A")

            if tag.strftime("%d.%m.%Y") == aktuelles_datum_de:
                kalender_img = self.bilder[69]
                kalender_color = "#FFE699"
            else:
                if wochentag == "Saturday" or wochentag == "Sunday":
                    kalender_img = self.bilder[75]
                    kalender_color = "#FBE5D6"
                else:
                    kalender_img = self.bilder[68]
                    kalender_color = "#EDEDED"

            self.bg_lbl.config(image=kalender_img)

            for j in self.kalender_bausteine[i]:
                j.config(bg=kalender_color)
            
    def gehe_zu_heute(self, datum=None):
        self.input_box_beschreibung.entry.delete(1.0, END)
        if datum != None:
            aktueller_tag = datetime.datetime.strptime(datum, '%d.%m.%Y').date()
        else:
            aktueller_tag = date.today()
        self.tagesliste = [aktueller_tag]

        for i in range(1, 8):
            datum = aktueller_tag + datetime.timedelta(days=i)
            self.tagesliste.append(datum)

        for i in range(0, 7):
            tag = self.tagesliste[i]
            wochentag = tag.strftime("%A")

            self.label_liste[i].config(text=self.tagesliste[i].strftime("%d.%m.%Y") + "\n" + self.wochentage[wochentag])

            if self.tagesliste[i].strftime("%d.%m.%Y") == aktuelles_datum_de:
                self.kalender_image_liste[i].config(image=self.bilder[69])
                self.label_liste[i].config(bg="#FFE699")
            else:
                if wochentag == "Saturday" or wochentag == "Sunday":
                    self.kalender_image_liste[i].config(image=self.bilder[75])
                    self.label_liste[i].config(bg="#FBE5D6")
                else:
                    self.kalender_image_liste[i].config(image=self.bilder[68])
                    self.label_liste[i].config(bg="#EDEDED")

        self.farbe_einstellen()
        self.dokumenten_anzahl_lbl_aendern()
        self.erinnerung_anzahl_lbl_aendern()
        self.datum_schreiben()
        self.dokumente_eintragen()

    def tag_aendern(self, zurueck=False):
        self.input_box_beschreibung.entry.delete(1.0, END)
        if zurueck == True:
            anzahl_tage = -1
        else:
            anzahl_tage = 1

        for i in range(0, 7):
            self.tagesliste[i] = self.tagesliste[i] + datetime.timedelta(days=anzahl_tage)

        for i in range(0, 7):
            tag = self.tagesliste[i]
            wochentag = tag.strftime("%A")

            if self.tagesliste[i].strftime("%d.%m.%Y") == aktuelles_datum_de:
                self.kalender_image_liste[i].config(image=self.bilder[69])
                self.label_liste[i].config(bg="#FFE699")
            else:
                if wochentag == "Saturday" or wochentag == "Sunday":
                    self.kalender_image_liste[i].config(image=self.bilder[75])
                    self.label_liste[i].config(bg="#FBE5D6")
                else:
                    self.kalender_image_liste[i].config(image=self.bilder[68])
                    self.label_liste[i].config(bg="#EDEDED")

            wochentag = self.tagesliste[i].strftime("%A")
            self.label_liste[i].config(text=self.tagesliste[i].strftime("%d.%m.%Y") + "\n" + self.wochentage[wochentag])

        self.farbe_einstellen()
        self.dokumenten_anzahl_lbl_aendern()
        self.erinnerung_anzahl_lbl_aendern()
        self.datum_schreiben()
        self.dokumente_eintragen()


class Erinnerung_hinzufuegen(Toplevel):
    def __init__(self, first, bilder, nummer, daten=None):
        super().__init__()

        self.first = first
        self.bilder = bilder
        self.nummer = nummer
        self.daten = daten
        self.checkbox_state = False

        self.geometry("700x550")
        self.resizable(0, 0)
        self.config(bg="#686767")
        self.overrideredirect(TRUE)

        #print(self.daten)

        self.hauptframe = Frame(self, bg="white", width=660, height=510)
        self.hauptframe.grid(row=0, column=0, padx=20, pady=20)
        self.hauptframe.grid_propagate(0)

        self.ueberschrift_lbl = Label(self.hauptframe, text="Erinnerung anlegen", bg="white", font=("Comic Sans MS", 14, "underline"))
        self.ueberschrift_lbl.grid(row=0, column=0, padx=30, pady=40, sticky="W")

        self.nummer_lbl = Label(self.hauptframe, text="Dokumentennummer:", bg="white", font = "Arial 12")
        self.nummer_lbl.grid(row=1, column=0, padx=30, pady=5, sticky="W")

        self.input_box_nummer = Input_Box(self.hauptframe, 1, 1, self.bilder[47], pady_value=(5), small=True)
        self.input_box_nummer.entry.insert(0, self.nummer)
        self.input_box_nummer.entry.config(state="disabled", disabledbackground="white")

        self.datenbankname_lbl = Label(self.hauptframe, text="Datenbankname:", bg="white", font = "Arial 12")
        self.datenbankname_lbl.grid(row=2, column=0, padx=30, pady=5, sticky="W")

        self.input_box_datenbankname = Input_Box(self.hauptframe, 2, 1, self.bilder[0], pady_value=(5))
        if self.daten != None:
            self.input_box_datenbankname.entry.insert(0, self.daten[0][1])
        else:
            self.input_box_datenbankname.entry.insert(0, window.tab_2.aktuelle_datenbank.cget("text").split("     ")[1])
        self.input_box_datenbankname.entry.config(state="disabled", disabledbackground="white")

        self.bezeichnung_lbl = Label(self.hauptframe, text="Bezeichnung:", bg="white", font = "Arial 12")
        self.bezeichnung_lbl.grid(row=3, column=0, padx=30, pady=5, sticky="W")

        self.input_box_bezeichnung = Input_Box(self.hauptframe, 3, 1, self.bilder[0], pady_value=(5))
        if self.daten != None:
            self.input_box_bezeichnung.entry.insert(0, self.daten[0][3])
        else:
            self.input_box_bezeichnung.entry.insert(0, db.datenwert_auslesen_einzeln("bezeichnung", self.nummer)[0][0])

        self.beschreibung_lbl = Label(self.hauptframe, text="Beschreibung:", bg="white", font = "Arial 12")
        self.beschreibung_lbl.grid(row=4, column=0, padx=30, pady=5, sticky="W")

        self.input_box_beschreibung = Input_Box(self.hauptframe, 4, 1, self.bilder[1], pady_value=(5), text_input=True)
        if self.daten != None:
            self.input_box_beschreibung.entry.insert(1.0, self.daten[0][4])
        else:
            self.input_box_beschreibung.entry.focus_set()

        self.datum_lbl = Label(self.hauptframe, text="Erinnerungsdatum:", bg="white", font = "Arial 12")
        self.datum_lbl.grid(row=5, column=0, padx=30, pady=5, sticky="W")

        self.datum_frame = Frame(self.hauptframe, bg="white")
        self.datum_frame.grid(row=5, column=1, pady=5, sticky="W")

        self.input_box_datum = Input_Box(self.datum_frame, 0, 0, self.bilder[47], pady_value=(5), small=True)
        if self.daten != None:
            self.input_box_datum.entry.insert(0, self.daten[0][5])
        else:
            pass

        if self.daten != None:
            if self.daten[0][6] == "x":
                self.haken_btn = Label(self.datum_frame, image=self.bilder[92], bg="white", activebackground="white")
                self.checkbox_state = True
                self.offen_lbl = Label(self.datum_frame, text="Abgeschlossen", bg="white", width=14, height=1, font="Arial 12", anchor="w")
            else:
                self.haken_btn = Label(self.datum_frame, image=self.bilder[91], bg="white", activebackground="white")
                self.offen_lbl = Label(self.datum_frame, text="Offen", bg="white", width=14, height=1, font="Arial 12", anchor="w")

            self.haken_btn.grid(row=0, column=1, padx=(80, 10), ipadx=2, ipady=2)
            self.haken_btn.bind("<Button-1>", lambda e: self.change_state(e))

            #self.offen_lbl = Label(self.datum_frame, text="Offen", bg="white", width=14, height=1, font="Arial 12", anchor="w")
            self.offen_lbl.grid(row=0, column=2, sticky="W")

        self.btn_frame = Frame(self.hauptframe, bg="white")
        self.btn_frame.grid(row=6, column=0, columnspan=2, pady=35, sticky="E")

        self.abbrechen_btn = Button(self.btn_frame, image=self.bilder[19], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.abbrechen)
        self.abbrechen_btn.grid(row=0, column=1, padx=5, ipadx=2, ipady=2, sticky="W")
        self.abbrechen_btn.bind("<Enter>", lambda e: button_enter(self.abbrechen_btn, self.bilder[20]))
        self.abbrechen_btn.bind("<Leave>", lambda e: button_leave(self.abbrechen_btn, self.bilder[19]))

        if self.daten != None:
            btn_bild = self.bilder[17]
            btn_bild_aktiv = self.bilder[18]
            btn_command = self.bearbeiten
        else:
            btn_bild = self.bilder[2]
            btn_bild_aktiv = self.bilder[3]
            btn_command = self.einfuegen

        self.einfuegen_btn = Button(self.btn_frame, image=btn_bild, relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=btn_command)
        self.einfuegen_btn.grid(row=0, column=2, ipadx=2, ipady=2, sticky="W")
        self.einfuegen_btn.bind("<Enter>", lambda e: button_enter(self.einfuegen_btn, btn_bild_aktiv))
        self.einfuegen_btn.bind("<Leave>", lambda e: button_leave(self.einfuegen_btn, btn_bild))

    def change_state(self, *event):
        if self.checkbox_state == False:
            self.haken_btn.config(image=self.bilder[92])
            self.checkbox_state = True
            self.offen_lbl.config(text="Abgeschlossen")
        else:
            self.haken_btn.config(image=self.bilder[91])
            self.checkbox_state = False
            self.offen_lbl.config(text="Offen")

    def abbrechen(self):
        self.destroy()

    def bearbeiten(self):
        #print(self.daten)
        daten = [self.daten[0][0], self.input_box_bezeichnung.entry.get(), self.input_box_beschreibung.entry.get(1.0, END).strip(), self.input_box_datum.entry.get(), self.checkbox_state]
        
        ergebnis_text = None

        if self.daten[0][6] != "x" and daten[4] == True:
            kommentar = messagebox.askquestion ('   Ergebnis','Wollen Sie ein Ergebnis hinzufügen?', parent=self)
            if kommentar == "yes":
                ergebnis = Infokasten(self, kommentar=True)
                center(ergebnis)
                self.wait_window(ergebnis)
                ergebnis_text = ergebnis.name
        elif self.daten[0][6] == "x" and self.daten[0][7] != "" and self.daten[0][7] != None:
            ergebnis = messagebox.askquestion ('   Ergebnis','Das vorhandene Ergebnis wird gelöscht... Fortfahren?', parent=self)
            if ergebnis != "yes":
                messagebox.showinfo("   Info", "Die Aktion wurde abgebrochen...")
                return

        db.erinnerung_bearbeiten(daten[0], daten, ergebnis_text)

        self.destroy()

        messagebox.showinfo("   Info", "Die Erinnerung wurde geändert...")

    def einfuegen(self):
        self.input_box_nummer.entry.config(state="normal")
        self.input_box_datenbankname.entry.config(state="normal")

        daten = [
            self.input_box_datenbankname.entry.get(), self.input_box_nummer.entry.get(), self.input_box_bezeichnung.entry.get(),
            self.input_box_beschreibung.entry.get(1.0, END).strip(), self.input_box_datum.entry.get()
        ]

        db.erinnerung_erstellen(daten)

        self.destroy()
        messagebox.showinfo("   Info", "Die Erinnerung wurde gespeichert...")


class Erinnerung_anzeigen(Toplevel):
    def __init__(self, first, bilder, faellig):
        super().__init__()

        self.first = first
        self.bilder = bilder
        self.faellig = faellig

        #print(self.faellig)

        self.geometry("550x550")
        self.resizable(0, 0)
        self.config(bg="#686767")
        self.overrideredirect(TRUE)

        self.hauptframe = Frame(self, bg="white", width=510, height=510)
        self.hauptframe.pack(padx=20, pady=20)
        self.hauptframe.pack_propagate(0)

        self.info_lbl = Label(self.hauptframe, text="Bitte beachten Sie folgende\nheute fälligen / überfälligen Dokumente:", bg="white", font=("Comic Sans MS", 14, "underline"))
        self.info_lbl.pack(padx=20, pady=(20, 40))

        ##### Treeview #####
        self.tree_style = ttk.Style()
        self.tree_style.configure("Treeview.Heading", foreground="#636D72")
        self.tree_style.configure("Treeview", foreground="#636D72")
        self.tree_style.map("Treeview", background=[('selected', '#559AF6')])
        
        self.treeview_frame = Frame(self.hauptframe, bg="white")
        self.treeview_frame.pack()

        self.dokumenten_scrollbar = Scrollbar(self.treeview_frame)
        self.dokumenten_scrollbar.pack(side=RIGHT, fill=Y, padx=1)

        self.dokumenten_treeview = ttk.Treeview(self.treeview_frame, style="Treeview", height=6, yscrollcommand=self.dokumenten_scrollbar.set)

        self.dokumenten_treeview["columns"]=("Bezeichnung")
        self.dokumenten_treeview.column("#0", width=50, minwidth=50, stretch=NO)
        self.dokumenten_treeview.column("Bezeichnung", width=350, minwidth=350, stretch=NO)

        self.dokumenten_treeview.heading("#0", text="Nr.", anchor=W)
        self.dokumenten_treeview.heading("Bezeichnung", text="Bezeichnung", anchor=W)

        self.dokumenten_treeview.pack(side=TOP, fill=X, anchor="e")
        self.dokumenten_scrollbar.config(command=self.dokumenten_treeview.yview)
        self.dokumenten_treeview.bind("<ButtonRelease>", lambda e: self.beschreibung_eintragen())
        self.dokumenten_treeview.bind('<KeyRelease-Up>', lambda e: self.beschreibung_eintragen())
        self.dokumenten_treeview.bind('<KeyRelease-Down>', lambda e: self.beschreibung_eintragen())

        #self.treeview.insert('', 'end', text=i[0], values=(i[1], i[2], verbleibende_Tage + " Tage", i[4]), tags=(markier_option,))

        #self.treeview.tag_configure('faellig', background='#FBF29F')
        #self.treeview.tag_configure('ueberfaellig', background='#FCC396')

        for i in range(0, len(self.faellig)):
            if len(self.faellig[i]) == 3:
                self.dokumenten_treeview.insert('', 'end', text=self.faellig[i][0], values=(db.datenwert_auslesen_einzeln("bezeichnung", self.faellig[i][0])[0]))
            elif len(self.faellig[i]):
                self.dokumenten_treeview.insert('', 'end', text=self.faellig[i][0], values=(db.datenwert_auslesen_einzeln("bezeichnung", self.faellig[i][0])[0]), tags=(self.faellig[i][3],))

        self.dokumenten_treeview.tag_configure('ueberfaellig', background='#FCC396')

        self.beschreibung_lbl = Label(self.hauptframe, text="Beschreibung:", bg="white", font = "Arial 12")
        self.beschreibung_lbl.pack(pady=(30, 5)) 

        self.beschreibung_frame = Frame(self.hauptframe, bg="white")
        self.beschreibung_frame.pack(pady=5)

        self.input_box_beschreibung = Input_Box(self.beschreibung_frame, 4, 1, self.bilder[1], pady_value=(5), text_input=True)

        self.btn_frame = Frame(self.hauptframe, bg="white")
        self.btn_frame.pack(pady=10)

        self.abbrechen_btn = Button(self.btn_frame, image=self.bilder[19], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.abbrechen)
        self.abbrechen_btn.grid(row=0, column=0, padx=5, ipadx=2, ipady=2)
        self.abbrechen_btn.bind("<Enter>", lambda e: button_enter(self.abbrechen_btn, self.bilder[20]))
        self.abbrechen_btn.bind("<Leave>", lambda e: button_leave(self.abbrechen_btn, self.bilder[19]))

        self.filtern_btn = Button(self.btn_frame, image=self.bilder[79], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.filtern)
        self.filtern_btn.grid(row=0, column=1, padx=5, ipadx=2, ipady=2)
        self.filtern_btn.bind("<Enter>", lambda e: button_enter(self.filtern_btn, self.bilder[80]))
        self.filtern_btn.bind("<Leave>", lambda e: button_leave(self.filtern_btn, self.bilder[79]))

        self.abschließen_btn = Button(self.btn_frame, image=self.bilder[83], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.abschließen)
        self.abschließen_btn.grid(row=0, column=2, padx=5, ipadx=2, ipady=2)
        self.abschließen_btn.bind("<Enter>", lambda e: button_enter(self.abschließen_btn, self.bilder[84]))
        self.abschließen_btn.bind("<Leave>", lambda e: button_leave(self.abschließen_btn, self.bilder[83]))

        self.focus_set()
        self.grab_set()

    def faellige_auslesen(self, ueberfaellig=False):
        erinnerungen = window.tab_3.anzahl_erinnerungen_bestimmen()
        ueberfaellige = window.tab_3.ueberfaellige_erinnerungen()

        if not erinnerungen[0] :
            pass
        else:
            aktualisierte_liste = []
            for i in erinnerungen[0]:
                if i[2] == "x":
                    pass
                else:
                    aktualisierte_liste.append(i)
        
        if ueberfaellig == True:
            for i in ueberfaellige:
                daten = [i[2], i[0], i[6], "ueberfaellig"]
                aktualisierte_liste.append(daten)

        return aktualisierte_liste

    def abschließen(self):
        abschließen = messagebox.askquestion ('   Abschließen','Wollen Sie die markierte Erinnerung abschließen?', parent=self)
        if abschließen == "yes":
            selected_iid = self.dokumenten_treeview.selection()[0]
            current_idx = self.dokumenten_treeview.index(selected_iid)
            id_erinnerung = db.erinnerung_spalte_auslesen("id", self.faellig[current_idx][1])
            db.erinnerung_abschließen(id_erinnerung[0][0])

            messagebox.showinfo("   Info", "Erinnerung wurde abgeschlossen...", parent=self)

            selected_items = self.dokumenten_treeview.selection()        
            for selected_item in selected_items:          
                self.dokumenten_treeview.delete(selected_item)

            self.input_box_beschreibung.entry.delete(1.0, END)

            del self.faellig
            self.faellig = self.faellige_auslesen(ueberfaellig=True)

    def abbrechen(self):
        self.destroy()

    def filtern(self):
        ids = []
        for i in self.faellig:
            ids.append(i[0])

        self.destroy()
        self.first.notebook.select(self.first.tab_1)
        Datenbank_anzeigen.customized_filter(self.first.tab_1, ids)

    def beschreibung_eintragen(self):
        selected_iid = self.dokumenten_treeview.selection()[0]
        current_idx = self.dokumenten_treeview.index(selected_iid)
        #print(current_idx)

        self.input_box_beschreibung.entry.delete(1.0, END)

        curItem = self.dokumenten_treeview.focus()
        nummer = self.dokumenten_treeview.item(curItem)["text"]

        #for i in self.faellig:
            #if i[0] == nummer:
                #beschreibung = db.erinnerung_spalte_auslesen("beschreibung", i[1])

        beschreibung = db.erinnerung_spalte_auslesen("beschreibung", self.faellig[current_idx][1])

        self.input_box_beschreibung.entry.insert(1.0, beschreibung[0][0])


class Thema_erstellen(Toplevel):
    def __init__(self, first, nummer=None, ueberschrift_text="Thema erstellen", ok_btn=False, bearbeitungsdaten=None):
        Toplevel.__init__(self)

        self.first = first
        self.nummer = nummer
        self.ueberschrift_text = ueberschrift_text
        self.ok_btn = ok_btn
        self.bearbeitungsdaten = bearbeitungsdaten

        self.geometry("700x450")
        self.resizable(0, 0)
        self.config(bg="#686767")
        self.overrideredirect(TRUE)

        self.hauptframe = Frame(self, bg="white", width=660, height=410)
        self.hauptframe.grid(row=0, column=0, padx=20, pady=20)
        self.hauptframe.pack_propagate(0)

        self.ueberschrift_lbl = Label(self.hauptframe, text=self.ueberschrift_text, bg="white", font=("Comic Sans MS", 14, "underline"))
        self.ueberschrift_lbl.pack(pady=20)

        self.gesamt_frame = Frame(self.hauptframe, bg="white")
        self.gesamt_frame.pack(padx=20, pady=10, anchor="w")

        self.themen_name = Label(self.gesamt_frame, text="Name: *", bg="white", font=("Comic Sans MS", 12))
        self.themen_name.grid(row=0, column=0, padx=20, pady=5, sticky="W")

        self.input_box_name = Input_Box(self.gesamt_frame, 0, 1, self.first.bilder[0], pady_value=(5, 5))
        self.input_box_name.entry.focus_set()

        self.themen_beschreibung = Label(self.gesamt_frame, text="Beschreibung:", bg="white", font=("Comic Sans MS", 12))
        self.themen_beschreibung.grid(row=1, column=0, padx=20, pady=5, sticky="W")

        self.input_box_beschreibung = Input_Box(self.gesamt_frame, 1, 1, self.first.bilder[1], pady_value=(5, 5), text_input=True)

        self.nummern_lbl = Label(self.gesamt_frame, text="Nummern: *", bg="white", font=("Comic Sans MS", 12))
        self.nummern_lbl.grid(row=2, column=0, padx=20, pady=5, sticky="W")

        self.tree_style = ttk.Style()
        self.tree_style.configure("Treeview.Heading", foreground="#636D72")
        self.tree_style.configure("Treeview", foreground="#636D72")
        self.tree_style.map("Treeview", background=[('selected', '#559AF6')])

        self.gesamtframe_row_2 = Frame(self.gesamt_frame, bg="white")
        self.gesamtframe_row_2.grid(row=2, column=1, padx=2, sticky="W")
        
        self.treeview_frame = Frame(self.gesamtframe_row_2, bg="white")
        self.treeview_frame.grid(row=0, column=1, pady=5, sticky="W")

        self.nummern_scrollbar = Scrollbar(self.treeview_frame)
        self.nummern_scrollbar.pack(side=RIGHT, fill=Y, padx=1)

        self.nummern_treeview = ttk.Treeview(self.treeview_frame, style="Treeview", height=3, yscrollcommand=self.nummern_scrollbar.set)

        self.nummern_treeview["columns"]=("Bezeichnung")
        self.nummern_treeview.column("#0", width=50, minwidth=50, stretch=NO)
        self.nummern_treeview.column("Bezeichnung", width=330, minwidth=330, stretch=NO)

        self.nummern_treeview.heading("#0", text="Nr.", anchor=W)
        self.nummern_treeview.heading("Bezeichnung", text="Bezeichnung", anchor=W)

        self.nummern_treeview.pack(side=TOP, fill=X, anchor="e")
        self.nummern_scrollbar.config(command=self.nummern_treeview.yview)
        #self.nummern_treeview.bind("<ButtonRelease>", lambda e: self.beschreibung_eintragen())
        #self.nummern_treeview.bind('<KeyRelease-Up>', lambda e: self.beschreibung_eintragen())
        #self.nummern_treeview.bind('<KeyRelease-Down>', lambda e: self.beschreibung_eintragen())

        self.btn_frame_numbers = Frame(self.gesamtframe_row_2, bg="white")
        self.btn_frame_numbers.grid(row=0, column=2, padx=20)

        self.nummer_hinzufuegen_btn = Button(self.btn_frame_numbers, image=self.first.bilder[70], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.nummer_hinzufuegen_toplevel)
        self.nummer_hinzufuegen_btn.grid(row=0, column=0, pady=10, ipady=2, ipadx=2, sticky="W")
        self.nummer_hinzufuegen_btn.bind("<Enter>", lambda e: button_enter(self.nummer_hinzufuegen_btn, self.first.bilder[73]))
        self.nummer_hinzufuegen_btn.bind("<Leave>", lambda e: button_leave(self.nummer_hinzufuegen_btn, self.first.bilder[70]))

        self.nummer_loeschen_btn = Button(self.btn_frame_numbers, image=self.first.bilder[72], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=self.nummer_loeschen)
        self.nummer_loeschen_btn.grid(row=1, column=0, pady=10, ipady=2, ipadx=2, sticky="W")
        self.nummer_loeschen_btn.bind("<Enter>", lambda e: button_enter(self.nummer_loeschen_btn, self.first.bilder[74]))
        self.nummer_loeschen_btn.bind("<Leave>", lambda e: button_leave(self.nummer_loeschen_btn, self.first.bilder[72]))

        self.btn_frame = Frame(self.gesamt_frame, bg="white")
        self.btn_frame.grid(row=3, column=0, columnspan=2, padx=50, pady=30, sticky="W")

        if self.ok_btn == True:
            btn_image = self.first.bilder[102] 
            btn_image_aktiv = self.first.bilder[103] 
            self.einfuegen_btn = Button(self.btn_frame, image=btn_image, bg="white", relief=FLAT, bd=0, command=self.thema_aendern)
        else:
            btn_image = self.first.bilder[2]
            btn_image_aktiv = self.first.bilder[3]
            self.einfuegen_btn = Button(self.btn_frame, image=btn_image, bg="white", relief=FLAT, bd=0, command=self.nummern_als_thema_verknuepfen)
        self.einfuegen_btn.pack(side="left", ipadx=2, ipady=2, padx=(150, 20))
        self.einfuegen_btn.bind("<Enter>", lambda e: button_enter(self.einfuegen_btn, btn_image_aktiv))
        self.einfuegen_btn.bind("<Leave>", lambda e: button_leave(self.einfuegen_btn, btn_image))

        self.abbrechen_btn = Button(self.btn_frame, image=self.first.bilder[19], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=lambda: self.destroy())
        self.abbrechen_btn.pack(ipadx=2, ipady=2)
        self.abbrechen_btn.bind("<Enter>", lambda e: button_enter(self.abbrechen_btn, self.first.bilder[20]))
        self.abbrechen_btn.bind("<Leave>", lambda e: button_leave(self.abbrechen_btn, self.first.bilder[19]))

        if nummer != None:
            for i in nummer:
                self.nummern_treeview.insert('', 'end', text=i, values=(db.datenwert_auslesen_einzeln("bezeichnung", i)[0]))

        if self.bearbeitungsdaten != None:
            self.input_box_name.entry.insert(0, self.bearbeitungsdaten[1])
            self.input_box_beschreibung.entry.insert(1.0, self.bearbeitungsdaten[2])

            for i in self.bearbeitungsdaten[3].split(", "):
                if i != "":
                    self.nummern_treeview.insert('', 'end', text=i, values=(db.datenwert_auslesen_einzeln("bezeichnung", i)[0]))

        self.focus_set()
        self.grab_set()

    def thema_aendern(self):
        nummern = ""
        for child in self.nummern_treeview.get_children():
            nummer = self.nummern_treeview.item(child)["text"]
            nummern = nummern + str(nummer) + ", "

        daten = [self.input_box_name.entry.get(), self.input_box_beschreibung.entry.get(1.0, END), nummern]

        db.thema_bearbeiten(self.bearbeitungsdaten[0], daten)
        self.destroy()

        messagebox.showinfo("   Info", "Das Thema wurde geändert...")

    def nummern_als_thema_verknuepfen(self):
        themen_name = self.input_box_name.entry.get()
        themen_beschreibung = self.input_box_beschreibung.entry.get(1.0, END).strip()
        nummern = ""
        datenbankname = window.tab_2.aktuelle_datenbank.cget("text").split(":     ")[1]

        for child in self.nummern_treeview.get_children():
            nummer = self.nummern_treeview.item(child)["text"]
            nummern = nummern + str(nummer) + ", "

        daten = [themen_name, themen_beschreibung, nummern, datenbankname]

        db.thema_einfuegen(daten)

        self.destroy()
        messagebox.showinfo("   Info", "Das Thema wurde erstellt...")

    def nummer_loeschen(self):
        selected_items = self.nummern_treeview.selection()        
        for selected_item in selected_items:          
            self.nummern_treeview.delete(selected_item)

    def nummer_hinzufuegen_toplevel(self):
        #self.grab_release()
        self.hinzufuegen = Toplevel()

        self.hinzufuegen.geometry("550x500")
        self.hinzufuegen.resizable(0, 0)
        self.hinzufuegen.config(bg="#686767")
        self.hinzufuegen.overrideredirect(TRUE)

        self.hauptframe = Frame(self.hinzufuegen, bg="white", width=510, height=460)
        self.hauptframe.pack(padx=20, pady=20)
        self.hauptframe.pack_propagate(0)

        #self.hauptframe = Frame(self.hinzufuegen, bg="white")
        #self.hauptframe.pack()

        self.tree_style = ttk.Style()
        self.tree_style.configure("Treeview.Heading", foreground="#636D72")
        self.tree_style.configure("Treeview", foreground="#636D72")
        self.tree_style.map("Treeview", background=[('selected', '#559AF6')])
        
        self.treeview_frame = Frame(self.hauptframe, bg="white")
        self.treeview_frame.pack(padx=20, pady=20)

        self.info_lbl = Label(self.treeview_frame, text="Bitte markieren Sie die gewünschten Dokumente durch\ndrücken der Tasten Strg + Linke Maustaste...", bg="white", font=("Comic Sans MS", 12))
        self.info_lbl.pack(pady=(0, 20))

        self.dokumenten_scrollbar = Scrollbar(self.treeview_frame)
        self.dokumenten_scrollbar.pack(side=RIGHT, fill=Y, padx=1)

        self.dokumenten_treeview = ttk.Treeview(self.treeview_frame, style="Treeview", height=12, yscrollcommand=self.dokumenten_scrollbar.set)

        self.dokumenten_treeview["columns"]=("Bezeichnung")
        self.dokumenten_treeview.column("#0", width=50, minwidth=50, stretch=NO)
        self.dokumenten_treeview.column("Bezeichnung", width=350, minwidth=350, stretch=NO)

        self.dokumenten_treeview.heading("#0", text="Nr.", anchor=W)
        self.dokumenten_treeview.heading("Bezeichnung", text="Bezeichnung", anchor=W)

        self.dokumenten_treeview.pack(side=TOP, fill=X, anchor="e")
        self.dokumenten_scrollbar.config(command=self.dokumenten_treeview.yview)
        #self.dokumenten_treeview.bind('<Double-1>', lambda e: self.dokument_anzeigen(e))
        #self.dokumenten_treeview.bind("<ButtonRelease-1>", lambda e: self.beschreibung_eintragen())

        self.btn_frame = Frame(self.hauptframe, bg="white")
        self.btn_frame.pack()

        self.einfuegen_btn_nummer = Button(self.btn_frame, image=self.first.bilder[2], bg="white", relief=FLAT, bd=0, command=self.nummer_uebernehmen)
        self.einfuegen_btn_nummer.pack(side="left", ipadx=2, ipady=2, padx=10)
        self.einfuegen_btn_nummer.bind("<Enter>", lambda e: button_enter(self.einfuegen_btn_nummer, self.first.bilder[3]))
        self.einfuegen_btn_nummer.bind("<Leave>", lambda e: button_leave(self.einfuegen_btn_nummer, self.first.bilder[2]))

        self.abbrechen_btn_nummer = Button(self.btn_frame, image=self.first.bilder[19], relief='flat', highlightthickness=0, bd=0, bg="white", activebackground="white", command=lambda: self.hinzufuegen.destroy())
        self.abbrechen_btn_nummer.pack(ipadx=2, ipady=2)
        self.abbrechen_btn_nummer.bind("<Enter>", lambda e: button_enter(self.abbrechen_btn_nummer, self.first.bilder[20]))
        self.abbrechen_btn_nummer.bind("<Leave>", lambda e: button_leave(self.abbrechen_btn_nummer, self.first.bilder[19]))

        daten_liste = []

        for child in self.first.dokumenten_treeview.get_children():
            nummer = self.first.dokumenten_treeview.item(child)["text"]
            name = self.first.dokumenten_treeview.item(child)["values"][0]
            daten_liste.append([nummer, name])

        for i in daten_liste:
            self.dokumenten_treeview.insert('', 'end', text=i[0], values=(i[1],))

        center(self.hinzufuegen)
        self.hinzufuegen.focus_set()
        self.hinzufuegen.grab_set()

    def nummer_uebernehmen(self):
        daten_liste_uebernehmen = []
        for child in self.dokumenten_treeview.selection():
            nummer = self.dokumenten_treeview.item(child)["text"]
            name = self.dokumenten_treeview.item(child)["values"]

            daten_liste_uebernehmen.append([nummer, name])
        
        self.hinzufuegen.destroy()

        for i in daten_liste_uebernehmen:
            self.nummern_treeview.insert('', 'end', text=i[0], values=(i[1]))

        
class Hauptfenster(Tk):
    tabliste = []

    def __init__(self, datenbank=None):
        super().__init__()

        self.datenbanken = []

        global db
        db=Database(datenbank)

        ########## Bilder laden ##########
        self.INPUT_BOX_1 = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Input_Box_1.png"))
        self.INPUT_TEXT = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Input_Text.png"))
        self.EINFUEGEN_BTN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Einfuegen_btn.png"))
        self.EINFUEGEN_BTN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Einfuegen_btn_aktiv.png"))
        self.COMBOBOX = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Combobox.png"))
        self.COMBOBOX_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Combobox_aktiv.png"))
        self.INPUT_LINK = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Inputbox_link.png"))
        self.BTN_LINK = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Btn_link.png"))
        self.BTN_LINK_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Btn_link_aktiv.png"))
        self.BTN_LOESCHEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Loeschen.png"))
        self.BTN_LOESCHEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Loeschen_aktiv.png"))
        self.BTN_ANZEIGEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anzeigen.png"))
        self.BTN_ANZEIGEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anzeigen_aktiv.png"))
        self.BTN_DATUM = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Datum_einfuegen.png"))
        self.BTN_DATUM_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Datum_einfuegen_aktiv.png"))
        self.BTN_BEARBEITEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Bearbeiten.png"))
        self.BTN_BEARBEITEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Bearbeiten_aktiv.png"))
        self.BTN_AENDERN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Aendern_btn.png"))
        self.BTN_AENDERN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Aendern_btn_aktiv.png"))
        self.BTN_ABBRECHEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Abbrechen_btn.png"))
        self.BTN_ABBRECHEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Abbrechen_btn_aktiv.png"))
        self.BTN_ZURUECK = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Zurueck_btn.png"))
        self.BTN_ZURUECK_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Zurueck_btn_aktiv.png"))
        self.BTN_ANZEIGEN_NEU = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anzeigen_neu.png"))
        self.BTN_ANZEIGEN_NEU_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anzeigen_neu_aktiv.png"))
        self.BTN_SUCHEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "suchen.png"))
        self.BTN_FILTER_ENTFERNEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "filter_entfernen.png"))
        self.BTN_SUCHEN_1 = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Suchen_btn.png"))
        self.BTN_SUCHEN_1_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Suchen_btn_aktiv.png"))
        self.BTN_SUCHEN_2 = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Suchen_btn_1.png"))
        self.BTN_SUCHEN_2_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Suchen_btn_1_aktiv.png"))
        self.BTN_ALLE_ZEIGEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Alle_zeigen_btn.png"))
        self.BTN_ALLE_ZEIGEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Alle_zeigen_btn_aktiv.png"))
        self.DOKUMENT_SPEICHERN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Dokument_speichern.png"))
        self.LINK_SPEICHERN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Link_speichern.png"))
        self.FILTER_LINKS = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Filter_links.png"))
        self.FILTER_LINKS_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Filter_links_aktiv.png"))
        self.ALLE_FILTER_ENTFERNEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "quickfilter_entfernen.png"))
        self.ALLE_FILTER_ENTFERNEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "quickfilter_entfernen_aktiv.png"))
        self.NEUE_DATENBANK = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "neue_datenbank.png"))
        self.NEUE_DATENBANK_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "neue_datenbank_aktiv.png"))
        self.DATENBANK_LADEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "datenbank_laden.png"))
        self.DATENBANK_LADEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "datenbank_laden_aktiv.png"))
        self.DATENBANK_LOESCHEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "datenbank_loeschen.png"))
        self.DATENBANK_LOESCHEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "datenbank_loeschen_aktiv.png"))
        self.KOMMENTAR_VORHANDEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "kommentar_vorhanden.png"))
        self.KOMMENTAR_VORHANDEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "kommentar_vorhanden_aktiv.png"))
        self.INPUTBOX_KLEIN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Input_Box_2.png")) 
        self.BTN_AUSCHECKEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Auschecken_btn.png"))
        self.BTN_AUSCHECKEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Auschecken_btn_aktiv.png"))
        self.BTN_FILTER_AUSGECHECKT = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Filter_ausgecheckt.png"))
        self.BTN_FILTER_AUSGECHECKT_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Filter_ausgecheckt_aktiv.png"))
        self.BTN_EINCHECKEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Einchecken_btn.png"))
        self.BTN_EINCHECKEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Einchecken_btn_aktiv.png"))
        self.ARBEITSVERSION_OEFFNEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Arbeitsversion_oeffnen.png")) 
        self.ARBEITSVERSION_OEFFNEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Arbeitsversion_oeffnen_aktiv.png")) 
        self.WORKSPACE_AKTUALISIEREN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Workspace_aktualisieren.png")) 
        self.WORKSPACE_AKTUALISIEREN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Workspace_aktualisieren_aktiv.png")) 
        self.WORKSPACE_VERSION_LOESCHEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Workspace_version_loeschen.png")) 
        self.WORKSPACE_VERSION_LOESCHEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Workspace_version_loeschen_aktiv.png")) 
        self.ANHANG_HINZUFUEGEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_hinzufuegen.png")) 
        self.ANHANG_HINZUFUEGEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_hinzufuegen_aktiv.png")) 
        self.ANHANG_LOESCHEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_loeschen.png")) 
        self.ANHANG_LOESCHEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_loeschen_aktiv.png")) 
        self.ANHANG_HINZUFUEGEN_BTN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_hinzufuegen_btn.png")) 
        self.ANHANG_HINZUFUEGEN_BTN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_hinzufuegen_btn_aktiv.png")) 
        self.ANHANG_AUSBLENDEN_BTN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_ausblenden_btn.png")) 
        self.ANHANG_AUSBLENDEN_BTN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_ausblenden_btn_aktiv.png")) 
        self.KALENDERTAG = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Kalendertag.png")) 
        self.KALENDERTAG_AKTUELL = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Kalendertag_aktuell.png")) 
        self.TAG_VORWAERTS = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Tag_vorwaerts.png")) 
        self.WOCHE_VORWAERTS = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Woche_vorwaerts.png")) 
        self.TAG_ZURUECK = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Tag_zurueck.png")) 
        self.TAG_VORWAERTS_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Tag_vorwaerts_aktiv.png")) 
        self.TAG_ZURUECK_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Tag_zurueck_aktiv.png")) 
        self.KALENDERTAG_WOCHENENDE = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Kalendertag_wochenende.png"))
        self.ERINNERUNG = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Erinnerung.png"))  
        self.ERINNERUNG_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Erinnerung_aktiv.png")) 
        self.ERINNERUNG_VORHANDEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Erinnerung_vorhanden.png")) 
        self.FILTERN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Filtern_btn.png"))  
        self.FILTERN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Filtern_btn_aktiv.png")) 
        self.FILTER_ERINNERUNG = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Filter_erinnerung.png"))  
        self.FILTER_ERINNERUNG_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Filter_erinnerung_aktiv.png")) 
        self.ABSCHLIEßEN_BTN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Abschließen_btn.png"))  
        self.ABSCHLIEßEN_BTN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Abschließen_btn_aktiv.png")) 
        self.DOKUMENTEN_BTN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Dokumenten_btn.png"))  
        self.DOKUMENTEN_BTN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Dokumenten_btn_aktiv.png")) 
        self.DOKUMENTEN_BTN_AN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Dokumenten_btn_an.png"))
        self.ERINNERUNGS_BTN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Erinnerungs_btn.png"))  
        self.ERINNERUNGS_BTN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Erinnerungs_btn_aktiv.png")) 
        self.ERINNERUNGS_BTN_AN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Erinnerungs_btn_an.png"))
        self.CHECKBOX_LEER = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Checkbox_leer.png"))
        self.CHECKBOX_HAKEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Checkbox_haken.png"))
        self.FILTER_ERINNERUNG_OFFEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Filter_erinnerung_offen.png"))
        self.FILTER_ERINNERUNG_OFFEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Filter_erinnerung_offen_aktiv.png"))
        self.ERINNERUNG_ERGEBNIS = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Erinnerung_ergebnis.png"))
        self.ERINNERUNG_ERGEBNIS_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Erinnerung_ergebnis_aktiv.png"))
        self.ANHANG_VORHANDEN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_vorhanden.png"))
        self.ANHANG_VORHANDEN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_vorhanden_aktiv.png"))
        self.ANHANG_VORHANDEN_AN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Anhang_vorhanden_an.png"))
        self.THEMEN_FILTERN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Themen_filtern.png")) 
        self.THEMEN_FILTERN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Themen_filtern_aktiv.png")) 
        self.OK_BTN = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Ok_button.png")) 
        self.OK_BTN_AKTIV = PhotoImage(file=os.path.join(PFAD + "/Bilder/", "Ok_button_aktiv.png")) 

        self.bilder = [
                        self.INPUT_BOX_1, self.INPUT_TEXT, self.EINFUEGEN_BTN, self.EINFUEGEN_BTN_AKTIV, self.COMBOBOX, self.COMBOBOX_AKTIV, # 0 1 2 3 4 5
                        self.INPUT_LINK, self.BTN_LINK, self.BTN_LINK_AKTIV, self.BTN_LOESCHEN, self.BTN_LOESCHEN_AKTIV, self.BTN_ANZEIGEN, # 6 7 8 9 10 11
                        self.BTN_ANZEIGEN_AKTIV, self.BTN_DATUM, self.BTN_DATUM_AKTIV, self.BTN_BEARBEITEN, self.BTN_BEARBEITEN_AKTIV, # 12 13 14 15 16
                        self.BTN_AENDERN, self.BTN_AENDERN_AKTIV, self.BTN_ABBRECHEN, self.BTN_ABBRECHEN_AKTIV, self.BTN_ZURUECK, self.BTN_ZURUECK_AKTIV, # 17 18 19 20 21 22
                        self.BTN_ANZEIGEN_NEU, self.BTN_ANZEIGEN_NEU_AKTIV, self.BTN_SUCHEN, self.BTN_FILTER_ENTFERNEN, self.BTN_SUCHEN_1, 
                        self.BTN_SUCHEN_1_AKTIV, self.BTN_SUCHEN_2, self.BTN_SUCHEN_2_AKTIV, self.BTN_ALLE_ZEIGEN, self.BTN_ALLE_ZEIGEN_AKTIV,
                        self.DOKUMENT_SPEICHERN, self.LINK_SPEICHERN, self.FILTER_LINKS, self.FILTER_LINKS_AKTIV, self.ALLE_FILTER_ENTFERNEN, # 33 - 37
                        self.ALLE_FILTER_ENTFERNEN_AKTIV, self.NEUE_DATENBANK, self.NEUE_DATENBANK_AKTIV, # 38 39 40
                        self.DATENBANK_LADEN, self.DATENBANK_LADEN_AKTIV,  self.DATENBANK_LOESCHEN, self.DATENBANK_LOESCHEN_AKTIV, # 41 42 43 44
                        self.KOMMENTAR_VORHANDEN, self.KOMMENTAR_VORHANDEN_AKTIV, self.INPUTBOX_KLEIN, # 45 46 47
                        self.BTN_AUSCHECKEN, self.BTN_AUSCHECKEN_AKTIV, self.BTN_FILTER_AUSGECHECKT, self.BTN_FILTER_AUSGECHECKT_AKTIV, # 48 49 50 51
                        self.BTN_EINCHECKEN, self.BTN_EINCHECKEN_AKTIV, self.ARBEITSVERSION_OEFFNEN, self.ARBEITSVERSION_OEFFNEN_AKTIV, # 52 53 54 55
                        self.WORKSPACE_AKTUALISIEREN, self.WORKSPACE_AKTUALISIEREN_AKTIV, self.WORKSPACE_VERSION_LOESCHEN, self.WORKSPACE_VERSION_LOESCHEN_AKTIV, # 56 57 58 59
                        self.ANHANG_HINZUFUEGEN, self.ANHANG_HINZUFUEGEN_AKTIV, self.ANHANG_LOESCHEN, self.ANHANG_LOESCHEN_AKTIV, # 60 61 62 63
                        self.ANHANG_HINZUFUEGEN_BTN, self.ANHANG_HINZUFUEGEN_BTN_AKTIV, self.ANHANG_AUSBLENDEN_BTN, self.ANHANG_AUSBLENDEN_BTN_AKTIV, # 64 65 66 67
                        self.KALENDERTAG, self.KALENDERTAG_AKTUELL, self.TAG_VORWAERTS, self.WOCHE_VORWAERTS, self.TAG_ZURUECK, self.TAG_VORWAERTS_AKTIV, # 68 69 70 71 72 73
                        self.TAG_ZURUECK_AKTIV, self.KALENDERTAG_WOCHENENDE, self.ERINNERUNG, self.ERINNERUNG_AKTIV, self.ERINNERUNG_VORHANDEN, # 74 75 76 77 78
                        self.FILTERN, self.FILTERN_AKTIV, self.FILTER_ERINNERUNG, self.FILTER_ERINNERUNG_AKTIV, self.ABSCHLIEßEN_BTN, self.ABSCHLIEßEN_BTN_AKTIV, # 79 80 81 82 83 84
                        self.DOKUMENTEN_BTN, self.DOKUMENTEN_BTN_AKTIV, self.DOKUMENTEN_BTN_AN, self.ERINNERUNGS_BTN, self.ERINNERUNGS_BTN_AKTIV, self.ERINNERUNGS_BTN_AN,  # 85 86 87 88 89 90
                        self.CHECKBOX_LEER, self.CHECKBOX_HAKEN, self.FILTER_ERINNERUNG_OFFEN, self.FILTER_ERINNERUNG_OFFEN_AKTIV, self.ERINNERUNG_ERGEBNIS, self.ERINNERUNG_ERGEBNIS_AKTIV, # 91 92 93 94 95 96
                        self.ANHANG_VORHANDEN, self.ANHANG_VORHANDEN_AKTIV, self.ANHANG_VORHANDEN_AN, self.THEMEN_FILTERN, self.THEMEN_FILTERN_AKTIV, # 97 98 99 100 101
                        self.OK_BTN, self.OK_BTN_AKTIV # 102 103
                    ]

        self.geometry("650x750")
        self.resizable(0, 0)
        self.title("Dokumentendatenbank")

        # Menü erstellen
        self.menu = Menu(self)
        self.config(menu=self.menu)
        self.filemenu = Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="Datei", menu=self.filemenu)
        self.filemenu.add_command(label="Neue Datenbank erstellen", command=self.neu_erstellen)
        self.filemenu.add_command(label="Datenbank komprimieren", command=self.komprimieren)
        self.filemenu.add_command(label="Sicherungskopie erstellen", command=self.db_speichern)
        self.filemenu.add_command(label="Datenbank laden", command=self.datenbank_laden)

        self.dok_menu = Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="Dokument", menu=self.dok_menu)
        self.dok_menu.add_command(label="PDF an markiertes Dokument anhängen (Anfang)", command=lambda: self.anhaengen(anfang=True))
        self.dok_menu.add_command(label="PDF an markiertes Dokument anhängen (Ende)", command=self.anhaengen)
        self.dok_menu.add_command(label="Dokument speichern unter", command=self.dokument_speichern)

        self.abstand_lbl = Label(self, height=1)
        self.abstand_lbl.pack()
        self.pack_propagate(0)

        self.notebook = ttk.Notebook()
        tabliste = self.add_tab()
        self.notebook.pack(expand=1, fill="both")

        ids = db.datenbank_daten_auslesen("id")
        bezeichnung = db.datenbank_daten_auslesen("bezeichnung")
        link = db.datenbank_daten_auslesen("link")

        for i in range(0, len(ids)):
            item = [int(ids[i][0]) + 1, bezeichnung[i][0], link[i][0]]
            self.datenbanken.append(item)

        self.update_db_treeview()

    def neu_erstellen(self):
        des = filedialog.asksaveasfilename(defaultextension=".db", filetypes=(("Database", ".db"),), initialfile="Dokumente")
        if des != "":
            with open(des, "w") as file:
                file.write("")
            name = Infokasten(self)
            center(name)
            self.wait_window(name)
            db.neue_db_einfuegen(name.name, des)
            self.datenbanken.append([len(self.datenbanken) + 2, name.name, des])
            self.update_db_treeview()
            messagebox.showinfo("   Info", " Neue Datenbank wurde unter " + des + " erstellt...", parent=self)

        self.tab_2.anzahl_datenbanken()

    '''
    def neu_erstellen(self):
        des = filedialog.asksaveasfilename(defaultextension=".db", filetypes=(("Database", ".db"),), initialfile="Dokumente")
        if des != "":
            with open(des, "w") as file:
                file.write("")
            messagebox.showinfo("   Info", " Neue Datenbank wurde unter " + des + " erstellt...", parent=self)
    '''

    def datenbank_laden(self, standard=False):
        global db

        if standard != False:
            bezeichnung = "Standard Dokumentendatenbank"
            filename = PFAD + "/Dokumente.db"
        else:
            curItem = window.tab_2.dokumenten_treeview.focus()
            nummer = window.tab_2.dokumenten_treeview.item(curItem)["text"]

            for i in self.datenbanken:
                if int(i[0]) == int(nummer):
                    bezeichnung = i[1]
                    filename = i[2]
                elif int(nummer) == 1:
                    bezeichnung = "Standard Dokumentendatenbank"
                    filename = PFAD + "/Dokumente.db"

        dateien = os.listdir(PFAD + "/_Dokumente")
        for i in dateien:
            if convertToBinaryData(PFAD + "/_Dokumente/" + i) != db.datenwert_auslesen_einzeln("datei", i.split(".")[0])[0][0]:
                db.update_blob(i.split(".")[0], convertToBinaryData(PFAD + "/_Dokumente/" + i))
            os.remove(PFAD + "/_Dokumente/" + i)

        if filename != "" and filename[-3:] == ".db":
            db = Database(filename)
            window.tab_1.treeview_update()
            window.tab_2.aktuelle_datenbank.config(text="Aktuell geladen:     " + bezeichnung)
            if standard != True:
                messagebox.showinfo("   Info", " Datenbank wurde geladen...", parent=self)
        elif filename[-3:] != ".db":
            messagebox.showerror("   Fehler", 'Datei konnte nicht geladen werden...', parent=self)

        window.tabliste[1].daten_leeren(window.tabliste[1].input_box_datum.entry, window.tabliste[1].input_box_kategorie.entry, window.tabliste[1].input_box_bezeichnung.entry, window.tabliste[1].input_box_beschreibung.entry, window.tabliste[1].input_box_person.entry)

        window.tab_1.datensatz = window.tab_1.daten_dict_erstellen()

    def db_speichern(self):
        des = filedialog.asksaveasfilename(defaultextension=".db", filetypes=(("Database", ".db"),), initialfile="Dokumente")
        if des != "":
            src = PFAD + "/Dokumente.db"
            shutil.copy(src, des)
            messagebox.showinfo("   Info", " Sicherungskopie wurde unter " + des + " erstellt...", parent=self)

    def anhaengen(self, anfang=False):
        pdfs = []
        try:
            curItem = self.tab_1.dokumenten_treeview.focus()
            nummer = self.tab_1.dokumenten_treeview.item(curItem)["text"]
            dateiart = db.datenwert_auslesen_einzeln("dateiart", nummer)[0][0]
            link = db.datenwert_auslesen_einzeln("link", nummer)[0][0]
        except:
            messagebox.showerror("   Fehler", 'Bitte wählen Sie ein Dokument im Tab "Datenbank anzeigen"...', parent=self)
            return
        if nummer == "":
            messagebox.showerror("   Fehler", 'Bitte wählen Sie ein Dokument im Tab "Datenbank anzeigen"...', parent=self)
            return
        elif dateiart != "pdf":
            messagebox.showerror("   Fehler", 'Bitte wählen Sie eine PDF-Datei...', parent=self)
            return
        elif link != "-":
            messagebox.showerror("   Fehler", 'Aktion bei Links nicht möglich...', parent=self)
            return
        else:
            R_neu = filedialog.askopenfilename(initialdir = "./", title = "Select file",filetypes = (("pdf files","*.pdf"),("all files","*.*")), parent=self)
            with open(PFAD + "/_Dokumente/" + str("R_neu") + ".pdf", "wb") as file:
                file.write(convertToBinaryData(R_neu))

            pdfs.append(PFAD + "/_Dokumente/" + str("R_neu") + ".pdf")

        R_alt = db.datenwert_auslesen_einzeln("datei", nummer)[0][0]
        with open(PFAD + "/_Dokumente/" + str("R_alt") + ".pdf", "wb") as file:
            file.write(R_alt)

        pdfs.append(PFAD + "/_Dokumente/" + str("R_alt") + ".pdf")

        merger = PyPDF2.PdfFileMerger(strict=False)        

        if anfang == True:
            for pdf in pdfs:
                merger.append(pdf)
        else:
            for pdf in reversed(pdfs):
                merger.append(pdf)

        with open(PFAD + "/_Dokumente/" + "Neues_Dokument.pdf", "wb") as fout:
            merger.write(fout)
            pdfs.append(PFAD + "/_Dokumente/" + "Neues_Dokument.pdf")

        merger.close()

        blob_datei_neu = convertToBinaryData(PFAD + "/_Dokumente/" + "Neues_Dokument.pdf")
        db.update_blob(nummer, blob_datei_neu)
        for pdf in pdfs:
            os.remove(pdf)
        messagebox.showinfo("   Info", "Datensatz wurde geändert...", parent=self)

    def dokument_speichern(self):
        files = []
        try:
            curItem = self.tab_1.dokumenten_treeview.focus()
            nummer = self.tab_1.dokumenten_treeview.item(curItem)["text"]
            datei = db.datenwert_auslesen_einzeln("datei", nummer)[0][0]
            dateiart = db.datenwert_auslesen_einzeln("dateiart", nummer)[0][0]
            files.append((dateiart, "." + dateiart))
        except:
            messagebox.showerror("   Fehler", 'Bitte wählen Sie ein Dokument im Tab "Datenbank anzeigen"...', parent=self)
            return

        speicherort = filedialog.asksaveasfilename(filetypes=files, defaultextension=files[0])
        if speicherort != "":
            with open(speicherort, "wb") as file:
                file.write(datei)
            messagebox.showinfo("   Info", "Dokument wurde gespeichert...", parent=self)

    def komprimieren(self):
        progress = Progress(self)
        center(progress)
        first = threading.Thread(target=lambda: progress.pg.start(5)).start()
        second = threading.Thread(target=lambda: db.vakuum(progress)).start()

    def add_tab(self):
        self.tab_2 = Datenbank_Management(self.bilder, self)
        self.notebook.add(self.tab_2, text="   Datenbank Management   ")

        self.tab = Neues_Dokument(self.bilder)
        self.notebook.add(self.tab, text="   Neues Dokument   ")

        self.tab_1 = Datenbank_anzeigen(self.bilder)
        self.notebook.add(self.tab_1, text="   Datenbank anzeigen   ")

        self.tab_3 = Kalender(self.bilder, self)
        self.notebook.add(self.tab_3, text="   Kalender   ")

        self.tabliste = [self.tab, self.tab_1, self.tab_2]
        return self.tabliste

    def update_db_treeview(self):
        self.tab_2.dokumenten_treeview.delete(*self.tab_2.dokumenten_treeview.get_children())
        
        self.tab_2.dokumenten_treeview.insert('', 'end', text=int(1), values=("Standard Dokumentendatenbank",))

        for i in range(0, len(self.datenbanken)):
            nummer = self.datenbanken[i][0]
            bezeichnung = self.datenbanken[i][1]

            self.tab_2.dokumenten_treeview.insert('', 'end', text=nummer, values=(bezeichnung,))

        self.tab_2.anzahl_datenbanken()

window = Hauptfenster(datenbank=PFAD + "/Dokumente.db")
center(window)

# Datensatz erstellen
window.tab_1.datensatz = window.tab_1.daten_dict_erstellen()

erinnerungen = window.tab_3.anzahl_erinnerungen_bestimmen()
ueberfaellige = window.tab_3.ueberfaellige_erinnerungen()

if not erinnerungen[0] and not ueberfaellige[0]:
    pass
else:
    aktualisierte_liste = []
    for i in erinnerungen[0]:
        if i[2] == "x":
            pass
        else:
            aktualisierte_liste.append(i)

    for i in ueberfaellige:
        try:
            daten = [i[2], i[0], i[6], "ueberfaellig"]
            aktualisierte_liste.append(daten)
        except:
            pass
    
    if not aktualisierte_liste:
        pass
    else:
        erinnerung_anzeigen = Erinnerung_anzeigen(window, window.bilder, aktualisierte_liste)
        center(erinnerung_anzeigen)

window.protocol("WM_DELETE_WINDOW", closing_main_window)
window.mainloop()

