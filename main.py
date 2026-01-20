import sys
import sqlite3
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QTabWidget, QDateEdit, QComboBox, 
    QGroupBox, QFormLayout
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPixmap, QFont

# --- FUNGSI FIX UNTUK LOGO & EXE ---
def resource_path(relative_path):
    """ Mendapatkan path absolut ke file, berfungsi untuk dev dan setelah jadi .exe """
    try:
        # PyInstaller membuat folder sementara di _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- 1. MODEL (DATABASE) ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("fikrigarage.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mobil (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plat TEXT UNIQUE,
                merk TEXT,
                tipe TEXT,
                harga INTEGER,
                status TEXT DEFAULT 'Tersedia'
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaksi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_mobil INTEGER,
                nama_penyewa TEXT,
                tgl_sewa TEXT,
                tgl_kembali_rencana TEXT,
                total_biaya INTEGER,
                status TEXT DEFAULT 'Berjalan',
                tgl_kembali_aktual TEXT,
                denda INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

# --- 2. VIEW & CONTROLLER (GUI) ---
class FikriGarageApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("FikriGarage - Sistem Rental Mobil")
        self.setGeometry(100, 100, 1000, 750)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # --- HEADER DENGAN LOGO ---
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(10, 5, 10, 10)
        header_layout.setSpacing(20)

        self.label_logo = QLabel()
        # MENGGUNAKAN resource_path AGAR LOGO MUNCUL DI EXE
        path_logo = resource_path("Rental.png")
        pixmap = QPixmap(path_logo) 
        
        if not pixmap.isNull():
            self.label_logo.setPixmap(pixmap.scaledToHeight(70, Qt.SmoothTransformation))
        else:
            self.label_logo.setText("[Logo Tidak Ditemukan]")
            self.label_logo.setStyleSheet("color: red; font-weight: bold;")
        
        title_label = QLabel("FikriGarage - Manajemen Sewa")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        
        header_layout.addWidget(self.label_logo)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addWidget(header_container)

        # --- SISTEM TAB ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_mobil = QWidget()
        self.tab_sewa = QWidget()
        self.tab_kembali = QWidget()
        self.tab_laporan = QWidget()

        self.tabs.addTab(self.tab_mobil, "Manajemen Mobil")
        self.tabs.addTab(self.tab_sewa, "Transaksi Sewa")
        self.tabs.addTab(self.tab_kembali, "Pengembalian & Denda")
        self.tabs.addTab(self.tab_laporan, "Laporan")

        self.setup_tab_mobil()
        self.setup_tab_sewa()
        self.setup_tab_kembali()
        self.setup_tab_laporan()

    def setup_tab_mobil(self):
        layout = QVBoxLayout()
        group = QGroupBox("Tambah Armada Mobil")
        form = QFormLayout()

        self.in_plat = QLineEdit()
        self.in_merk = QLineEdit()
        self.in_tipe = QLineEdit()
        self.in_harga = QLineEdit()
        self.in_harga.setPlaceholderText("Contoh: 300000")

        form.addRow("Plat Nomor:", self.in_plat)
        form.addRow("Merk Mobil:", self.in_merk)
        form.addRow("Tipe:", self.in_tipe)
        form.addRow("Harga Sewa/Hari (Rp):", self.in_harga)
        
        btn_add = QPushButton("Simpan Data Mobil")
        btn_add.clicked.connect(self.save_car)
        form.addRow(btn_add)
        group.setLayout(form)

        self.table_mobil = QTableWidget()
        self.table_mobil.setColumnCount(5)
        self.table_mobil.setHorizontalHeaderLabels(["ID", "Plat", "Merk", "Harga", "Status"])
        self.table_mobil.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(group)
        layout.addWidget(self.table_mobil)
        self.tab_mobil.setLayout(layout)
        self.refresh_car_table()

    def save_car(self):
        msg = QMessageBox.question(self, "Konfirmasi", "Simpan data mobil ini?", QMessageBox.Yes | QMessageBox.No)
        if msg == QMessageBox.Yes:
            try:
                data = (self.in_plat.text(), self.in_merk.text(), self.in_tipe.text(), int(self.in_harga.text()))
                self.db.cursor.execute("INSERT INTO mobil (plat, merk, tipe, harga) VALUES (?,?,?,?)", data)
                self.db.conn.commit()
                self.refresh_car_table()
                self.load_combo_mobil()
                QMessageBox.information(self, "Berhasil", "Data mobil ditambahkan.")
                self.in_plat.clear(); self.in_merk.clear(); self.in_tipe.clear(); self.in_harga.clear()
            except Exception as e:
                QMessageBox.critical(self, "Gagal", f"Error: {str(e)}")

    def refresh_car_table(self):
        self.table_mobil.setRowCount(0)
        self.db.cursor.execute("SELECT id, plat, merk, harga, status FROM mobil")
        for r_idx, row in enumerate(self.db.cursor.fetchall()):
            self.table_mobil.insertRow(r_idx)
            for c_idx, val in enumerate(row):
                self.table_mobil.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

    def setup_tab_sewa(self):
        layout = QVBoxLayout()
        form = QFormLayout()
        self.cb_mobil = QComboBox()
        self.in_customer = QLineEdit()
        self.date_s = QDateEdit(calendarPopup=True)
        self.date_s.setDate(QDate.currentDate())
        self.date_k = QDateEdit(calendarPopup=True)
        self.date_k.setDate(QDate.currentDate().addDays(1))
        btn_rent = QPushButton("Konfirmasi Penyewaan")
        btn_rent.clicked.connect(self.process_rent)
        form.addRow("Pilih Mobil:", self.cb_mobil)
        form.addRow("Nama Pelanggan:", self.in_customer)
        form.addRow("Tgl Pinjam:", self.date_s)
        form.addRow("Tgl Kembali:", self.date_k)
        form.addRow(btn_rent)
        layout.addLayout(form)
        layout.addStretch()
        self.tab_sewa.setLayout(layout)
        self.load_combo_mobil()

    def load_combo_mobil(self):
        self.cb_mobil.clear()
        self.db.cursor.execute("SELECT id, merk, plat, harga FROM mobil WHERE status='Tersedia'")
        self.cars_list = self.db.cursor.fetchall()
        for c in self.cars_list:
            self.cb_mobil.addItem(f"{c[1]} ({c[2]}) - Rp {c[3]}/hari")

    def process_rent(self):
        idx = self.cb_mobil.currentIndex()
        if idx < 0 or not self.in_customer.text():
            QMessageBox.warning(self, "Data Kurang", "Harap isi semua data.")
            return
        durasi = self.date_s.date().daysTo(self.date_k.date())
        total = self.cars_list[idx][3] * (durasi if durasi > 0 else 1)
        data = (self.cars_list[idx][0], self.in_customer.text(), 
                self.date_s.date().toString("yyyy-MM-dd"), 
                self.date_k.date().toString("yyyy-MM-dd"), total)
        self.db.cursor.execute("INSERT INTO transaksi (id_mobil, nama_penyewa, tgl_sewa, tgl_kembali_rencana, total_biaya) VALUES (?,?,?,?,?)", data)
        self.db.cursor.execute("UPDATE mobil SET status='Disewa' WHERE id=?", (self.cars_list[idx][0],))
        self.db.conn.commit()
        QMessageBox.information(self, "Berhasil", "Transaksi Berhasil.")
        self.load_combo_mobil(); self.refresh_car_table(); self.load_active_rentals()

    def setup_tab_kembali(self):
        layout = QVBoxLayout()
        form = QFormLayout()
        self.cb_active = QComboBox()
        self.date_actual = QDateEdit(calendarPopup=True)
        self.date_actual.setDate(QDate.currentDate())
        btn_return = QPushButton("Proses Pengembalian")
        btn_return.clicked.connect(self.process_return)
        form.addRow("Pilih Transaksi Aktif:", self.cb_active)
        form.addRow("Tanggal Kembali Aktual:", self.date_actual)
        form.addRow(btn_return)
        layout.addLayout(form)
        layout.addStretch()
        self.tab_kembali.setLayout(layout)
        self.load_active_rentals()

    def load_active_rentals(self):
        self.cb_active.clear()
        query = "SELECT t.id, m.plat, t.nama_penyewa, t.tgl_kembali_rencana, m.harga, t.id_mobil FROM transaksi t JOIN mobil m ON t.id_mobil = m.id WHERE t.status='Berjalan'"
        self.db.cursor.execute(query)
        self.active_list = self.db.cursor.fetchall()
        for a in self.active_list:
            self.cb_active.addItem(f"{a[1]} - {a[2]} (Deadline: {a[3]})")

    def process_return(self):
        idx = self.cb_active.currentIndex()
        if idx < 0: return
        trx = self.active_list[idx]
        tgl_deadline = QDate.fromString(trx[3], "yyyy-MM-dd")
        terlambat = tgl_deadline.daysTo(self.date_actual.date())
        denda = (terlambat * 50000) if terlambat > 0 else 0
        self.db.cursor.execute("UPDATE transaksi SET status='Selesai', tgl_kembali_aktual=?, denda=? WHERE id=?", 
                               (self.date_actual.date().toString("yyyy-MM-dd"), denda, trx[0]))
        self.db.cursor.execute("UPDATE mobil SET status='Tersedia' WHERE id=?", (trx[5],))
        self.db.conn.commit()
        QMessageBox.information(self, "Selesai", f"Denda: Rp {denda}")
        self.load_active_rentals(); self.load_combo_mobil(); self.refresh_car_table(); self.refresh_report()

    def setup_tab_laporan(self):
        layout = QVBoxLayout()
        self.table_rep = QTableWidget()
        self.table_rep.setColumnCount(5)
        self.table_rep.setHorizontalHeaderLabels(["Penyewa", "Mobil", "Tgl Sewa", "Biaya", "Denda"])
        self.table_rep.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("Riwayat Transaksi Selesai"))
        layout.addWidget(self.table_rep)
        self.tab_laporan.setLayout(layout)
        self.refresh_report()

    def refresh_report(self):
        self.table_rep.setRowCount(0)
        query = "SELECT t.nama_penyewa, m.plat, t.tgl_sewa, t.total_biaya, t.denda FROM transaksi t JOIN mobil m ON t.id_mobil = m.id WHERE t.status='Selesai'"
        self.db.cursor.execute(query)
        for r_idx, row in enumerate(self.db.cursor.fetchall()):
            self.table_rep.insertRow(r_idx)
            for c_idx, val in enumerate(row):
                self.table_rep.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    win = FikriGarageApp()
    win.show()
    sys.exit(app.exec_())