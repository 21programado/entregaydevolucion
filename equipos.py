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
# PAGINACIÓN Y FILTRO
# ===============================
REGISTROS_POR_PAGINA = 10
pagina_actual = 0
equipo_filtro = None  # None = sin búsqueda

# ===============================
# FUNCIONES
# ===============================
def ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def registrar_entrega():
    global pagina_actual
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
    pagina_actual = 0
    limpiar_formulario()
    cargar_registros()


def registrar_devolucion():
    global pagina_actual
    seleccion = tree.selection()
    if not seleccion:
        messagebox.showwarning("Selección", "Seleccione un registro pendiente.")
        return

    valores = tree.item(seleccion[0], "values")

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
    pagina_actual = 0
    cargar_registros()


def cargar_registros():
    for i in tree.get_children():
        tree.delete(i)

    offset = pagina_actual * REGISTROS_POR_PAGINA

    # =========================
    # CONSULTA DE DATOS
    # =========================
    if equipo_filtro:
        cursor.execute("""
            SELECT registro, nombre, cargo, equipo, entrega, salida, devolucion
            FROM registros
            WHERE equipo = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (equipo_filtro, REGISTROS_POR_PAGINA, offset))
    else:
        cursor.execute("""
            SELECT registro, nombre, cargo, equipo, entrega, salida, devolucion
            FROM registros
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (REGISTROS_POR_PAGINA, offset))

    filas = cursor.fetchall()

    # =========================
    # CONSULTA DE CONTEO
    # =========================
    if equipo_filtro:
        cursor.execute(
            "SELECT COUNT(*) FROM registros WHERE equipo = ?",
            (equipo_filtro,)
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM registros")

    total = cursor.fetchone()[0]

    # =========================
    # CARGA EN LA TABLA
    # =========================
    for row in filas:
        tag = "pendiente" if row[6] == "Pendiente" else "devuelto"
        tree.insert("", "end", values=row, tags=(tag,))

    actualizar_label_pagina(total)



def actualizar_label_pagina(total):
    total_paginas = max(1, (total + REGISTROS_POR_PAGINA - 1) // REGISTROS_POR_PAGINA)
    pagina_label.config(text=f"Página {pagina_actual + 1} de {total_paginas}")


def pagina_siguiente():
    global pagina_actual
    pagina_actual += 1
    cargar_registros()


def pagina_anterior():
    global pagina_actual
    if pagina_actual > 0:
        pagina_actual -= 1
        cargar_registros()


def buscar_por_equipo():
    global equipo_filtro, pagina_actual
    equipo = buscar_equipo_entry.get().strip()
    if not equipo:
        return
    equipo_filtro = equipo
    pagina_actual = 0
    cargar_registros()


def limpiar_busqueda():
    global equipo_filtro, pagina_actual
    equipo_filtro = None
    pagina_actual = 0
    buscar_equipo_entry.delete(0, "end")
    cargar_registros()


def limpiar_formulario():
    nombre_entry.delete(0, "end")
    cargo_combo.set("")
    equipo_combo.set("")
    salida_text.delete("1.0", "end")


def copiar_registros():
    texto = ""
    for item in tree.get_children():
        texto += " | ".join(tree.item(item, "values")) + "\n"
    root.clipboard_clear()
    root.clipboard_append(texto)
    root.update()


def cargar_salida_al_seleccionar(event):
    seleccion = tree.selection()
    if seleccion:
        salida_text.delete("1.0", "end")
        salida_text.insert("1.0", tree.item(seleccion[0], "values")[5])

# ===============================
# INTERFAZ
# ===============================
root = tk.Tk()
#linea para colores de botones
style = ttk.Style()

style.configure(
    "Entrega.TButton",
    background="#1f7a1f",
    foreground="black",
    font=("Segoe UI", 10, "bold")
)

style.configure(
    "Devolucion.TButton",
    background="#9a7d0a",
    foreground="black",
    font=("Segoe UI", 10, "bold")
)
#--------------------------------------------------------------------------
root.title("Control de Entrega y Devolución de Equipos")
root.state("zoomed")

main = ttk.Frame(root, padding=15)
main.pack(fill="both", expand=True)

ttk.Label(main, text="Control de Entrega y Devolución de Equipos",
          font=("Segoe UI", 16, "bold")).pack(pady=10)

# FORMULARIO
form = ttk.Frame(main)
form.pack(fill="x", pady=10)

ttk.Label(form, text="Nombre").grid(row=0, column=0, padx=5)
nombre_entry = ttk.Entry(form, width=30)
nombre_entry.grid(row=0, column=1, padx=5)

ttk.Label(form, text="Cargo").grid(row=0, column=2, padx=5)
cargo_combo = ttk.Combobox(form, width=28, state="readonly",
                           values=["Auxiliar de Enfermería", "Licenciada en Enfermería",
                                   "Practicante Interno", "Médico", "ASG", "Otro"])
cargo_combo.grid(row=0, column=3, padx=5)

ttk.Label(form, text="Equipo").grid(row=1, column=0, padx=5)
equipo_combo = ttk.Combobox(form, width=28, state="readonly",
                            values=["Monitor 1", "Monitor 2", "ECG", "Saturómetro",
                                    "Otoscopio", "Valija de Traslado", "Videolaringo", "Otro"])
equipo_combo.grid(row=1, column=1, padx=5)

ttk.Label(form, text="Salida / Destino").grid(row=1, column=2, padx=5)
salida_text = tk.Text(form, width=30, height=3)
#salida_text.grid(row=1, column=3, padx=5)
salida_text.grid(row=1, column=3, padx=(20, 5), pady=5)


# BOTONES
botones = ttk.Frame(main)
botones.pack(pady=10)

ttk.Button(botones, text="Registrar Entrega", command=registrar_entrega, style="Entrega.TButton").pack(side="left", padx=5)
ttk.Button(botones, text="Registrar Devolución", command=registrar_devolucion, style="Devolucion.TButton").pack(side="left", padx=5)
ttk.Button(botones, text="Copiar Registros", command=copiar_registros).pack(side="left", padx=5)

# BÚSQUEDA
busqueda = ttk.Frame(main)
busqueda.pack(fill="x", pady=5)

ttk.Label(busqueda, text="Buscar historial por equipo:").pack(side="left", padx=5)
buscar_equipo_entry = ttk.Entry(busqueda, width=30)
buscar_equipo_entry.pack(side="left", padx=5)

ttk.Button(busqueda, text="Buscar", command=buscar_por_equipo).pack(side="left", padx=5)
ttk.Button(busqueda, text="Limpiar búsqueda", command=limpiar_busqueda).pack(side="left", padx=5)

# TABLA
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

# PAGINACIÓN
paginacion = ttk.Frame(main)
paginacion.pack(pady=5)

ttk.Button(paginacion, text="◀ Anterior", command=pagina_anterior).pack(side="left", padx=5)
pagina_label = ttk.Label(paginacion, text="Página 1")
pagina_label.pack(side="left", padx=10)
ttk.Button(paginacion, text="Siguiente ▶", command=pagina_siguiente).pack(side="left", padx=5)

cargar_registros()
root.mainloop()
