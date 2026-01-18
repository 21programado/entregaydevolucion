import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os

# ===============================
# RUTAS SEGURAS
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "registros.db")

# ===============================
# BASE DE DATOS
# ===============================
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registro TEXT,
    nombre TEXT,
    cargo TEXT,
    equipo TEXT,
    entrega TEXT,
    salida TEXT,
    devolucion TEXT
)
""")
conn.commit()

# ===============================
# CONFIGURACIÓN
# ===============================
REGISTROS_PDF = 50

# ===============================
# FUNCIONES
# ===============================
def ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def registrar_entrega():
    nombre = nombre_entry.get().strip()
    cargo = cargo_combo.get()
    equipo = equipo_combo.get()
    salida = salida_text.get("1.0", "end").strip()

    if not nombre or not cargo or not equipo:
        messagebox.showwarning("Datos incompletos", "Complete Nombre, Cargo y Equipo.")
        return

    if not messagebox.askyesno("Confirmar entrega", f"¿Confirma la entrega de {equipo} a {nombre}?"):
        return

    cursor.execute("""
        INSERT INTO registros (registro, nombre, cargo, equipo, entrega, salida, devolucion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ahora(), nombre, cargo, equipo, ahora(), salida, "Pendiente"))

    conn.commit()
    limpiar_formulario()
    cargar_registros()

def registrar_devolucion():
    seleccion = tree.selection()
    if not seleccion:
        messagebox.showwarning("Selección", "Seleccione un registro pendiente.")
        return

    item = seleccion[0]
    valores = tree.item(item, "values")

    if valores[6] != "Pendiente":
        messagebox.showinfo("Información", "Este equipo ya fue devuelto.")
        return

    if not messagebox.askyesno("Confirmar devolución", f"¿Confirma la devolución del equipo {valores[3]}?"):
        return

    salida_actual = salida_text.get("1.0", "end").strip()

    cursor.execute("""
        UPDATE registros
        SET devolucion = ?, salida = ?
        WHERE registro = ?
    """, (ahora(), salida_actual, valores[0]))

    conn.commit()
    cargar_registros()

def cargar_registros():
    for i in tree.get_children():
        tree.delete(i)

    cursor.execute("""
        SELECT registro, nombre, cargo, equipo, entrega, salida, devolucion
        FROM registros
        ORDER BY id DESC
        LIMIT 200
    """)

    for row in cursor.fetchall():
        tag = "pendiente" if row[6] == "Pendiente" else "devuelto"
        tree.insert("", "end", values=row, tags=(tag,))

def limpiar_formulario():
    nombre_entry.delete(0, "end")
    cargo_combo.set("")
    equipo_combo.set("")
    salida_text.delete("1.0", "end")

def cargar_salida_al_seleccionar(event):
    seleccion = tree.selection()
    if seleccion:
        salida_text.delete("1.0", "end")
        salida_text.insert("1.0", tree.item(seleccion[0], "values")[5])

# ===============================
# PDF MINIMALISTA
# ===============================
def exportar_pdf():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        messagebox.showerror(
            "PDF no disponible",
            "No está instalada la librería 'reportlab'.\n\n"
            "Para habilitar el PDF:\n"
            "pip install reportlab"
        )
        return

    cursor.execute("""
        SELECT registro, nombre, cargo, equipo, entrega, salida, devolucion
        FROM registros
        ORDER BY id DESC
        LIMIT ?
    """, (REGISTROS_PDF,))

    filas = cursor.fetchall()

    if not filas:
        messagebox.showinfo("PDF", "No hay registros para exportar.")
        return

    pdf_path = os.path.join(BASE_DIR, "ultimos_50_registros.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica", 9)

    c.drawString(40, y, "Últimos 50 registros - Control de Equipos")
    y -= 30

    for fila in filas:
        linea = " | ".join(fila)
        if y < 40:
            c.showPage()
            c.setFont("Helvetica", 9)
            y = height - 40
        c.drawString(40, y, linea[:120])
        y -= 14

    c.save()
    messagebox.showinfo("PDF generado", f"Archivo creado:\n{pdf_path}")

# ===============================
# INTERFAZ
# ===============================
root = tk.Tk()
root.title("Control de Entrega y Devolución de Equipos y Materiales")
root.state("zoomed")

main = ttk.Frame(root, padding=15)
main.pack(fill="both", expand=True)

ttk.Label(
    main,
    text="Control de Entrega y Devolución de Equipos y Materiales",
    font=("Segoe UI", 16, "bold")
).pack(pady=10)

form = ttk.Frame(main)
form.pack(fill="x", pady=10)

ttk.Label(form, text="Nombre").grid(row=0, column=0, sticky="w", padx=5, pady=5)
nombre_entry = ttk.Entry(form, width=30)
nombre_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(form, text="Cargo").grid(row=0, column=2, sticky="w", padx=5, pady=5)
cargo_combo = ttk.Combobox(
    form,
    width=28,
    state="readonly",
    values=[
        "Auxiliar de Enfermería",
        "Licenciada en Enfermería",
        "Practicante Interno",
        "Médico",
        "ASG",
        "Otro"
    ]
)
cargo_combo.grid(row=0, column=3, padx=5, pady=5)

ttk.Label(form, text="Equipo").grid(row=1, column=0, sticky="w", padx=5, pady=5)
equipo_combo = ttk.Combobox(
    form,
    width=28,
    state="readonly",
    values=[
        "Monitor 1",
        "Monitor 2",
        "ECG",
        "Saturómetro",
        "Otoscopio",
        "Valija de Traslado",
        "Videolaringo",
        "Otro"
    ]
)
equipo_combo.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(form, text="Salida / Destino").grid(row=1, column=2, sticky="nw", padx=(20, 5), pady=5)
salida_text = tk.Text(form, width=30, height=3)
salida_text.grid(row=1, column=3, padx=5, pady=5)

botones = ttk.Frame(main)
botones.pack(pady=10)

ttk.Button(botones, text="Registrar Entrega", command=registrar_entrega).pack(side="left", padx=5)
ttk.Button(botones, text="Registrar Devolución", command=registrar_devolucion).pack(side="left", padx=5)
ttk.Button(botones, text="Exportar últimos 50 a PDF", command=exportar_pdf).pack(side="left", padx=5)

tabla_frame = ttk.Frame(main)
tabla_frame.pack(fill="both", expand=True)

cols = ("Registro", "Nombre", "Cargo", "Equipo", "Entrega", "Salida/Destino", "Devolución")
tree = ttk.Treeview(tabla_frame, columns=cols, show="headings")

for c in cols:
    tree.heading(c, text=c)
    tree.column(c, width=180 if c != "Salida/Destino" else 260)

tree.pack(side="left", fill="both", expand=True)

scroll = ttk.Scrollbar(tabla_frame, orient="vertical", command=tree.yview)
scroll.pack(side="right", fill="y")
tree.configure(yscrollcommand=scroll.set)

tree.tag_configure("pendiente", background="#ffe5e5")
tree.tag_configure("devuelto", background="#e5ffe5")

tree.bind("<<TreeviewSelect>>", cargar_salida_al_seleccionar)

cargar_registros()
root.mainloop()
