from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, UserMixin
import networkx as nx
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
import csv
from io import StringIO, BytesIO
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import timedelta, datetime

app = Flask(__name__)
app.secret_key = "kurir_secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kurir.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile_pic = db.Column(db.String(150), nullable=True)  # Hapus tanda komentar!

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start = db.Column(db.String(150), nullable=False)
    end = db.Column(db.String(150), nullable=False)
    route = db.Column(db.Text, nullable=False)
    distance = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# Daftar nama jalan
nodes = [
    "Jalan Raya Maospati–Madiun",
    "Jalan Raya Maospati–Ngawi",
    "Jalan Raya Maospati–Magetan",
    "Jalan Raya Sarangan",
    "Jalan Gubernur Suryo",
    "Jalan Pahlawan",
    "Jalan Jenderal Sudirman",
    "Jalan Ahmad Yani",
    "Jalan Diponegoro",
    "Jalan Munginsidi",
    "Jalan Pattimura",
    "Jalan Mayor Jenderal Sukowati",
    "Jalan Yos Sudarso",
    "Jalan Janoko",
    "Jalan Sadewo",
    "Jalan Srikandi",
    "Jalan Tripandita",
    "Jalan Kunti",
    "Jalan Nangkulo",
    "Jalan Gitadini",
    "Jalan Jawa",
    "Jalan Bromo",
    "Jalan Kawi",
    "Jalan Pandan",
    "Jalan Samodra",
    "Jalan Semeru",
    "Jalan Wilis",
    "Jalan Barat (Maospati–Barat)",
    "Jalan Agung",
    "Jalan Sendang Kamal",
    # Tambahkan node berikut agar sesuai dengan edges:
    "Jalan Raya Maospati",
    "Jalan Terminal Maospati",
    "Jalan Stasiun Maospati",
    "Jalan Sudirman",
    "Jalan Gatot Subroto",
    "Jalan Merdeka",
    "Jalan Mayor Jenderal Sungkono",
    "Jalan Kartini",
    "Gang Mawar",
    "Gang Melati",
    "Gang Dahlia",
    "Gang Cemara"
]

# Contoh edge antar jalan (isi sesuai peta nyata, ini hanya contoh acak)
edges = [
    # Hubungkan node utama ke node yang sudah ada di edges
    ("Jalan Raya Maospati–Madiun", "Jalan Raya Maospati", 2.5),
    ("Jalan Raya Maospati–Ngawi", "Jalan Raya Maospati", 3.0),
    ("Jalan Raya Maospati–Magetan", "Jalan Raya Maospati", 4.0),
    ("Jalan Raya Sarangan", "Jalan Raya Maospati–Magetan", 5.5),
    ("Jalan Gubernur Suryo", "Jalan Raya Maospati–Magetan", 1.2),
    ("Jalan Gubernur Suryo", "Jalan Pahlawan", 0.8),
    ("Jalan Pahlawan", "Jalan Jenderal Sudirman", 1.0),
    ("Jalan Jenderal Sudirman", "Jalan Ahmad Yani", 0.7),
    ("Jalan Ahmad Yani", "Jalan Diponegoro", 0.9),
    ("Jalan Diponegoro", "Jalan Munginsidi", 1.1),
    ("Jalan Munginsidi", "Jalan Pattimura", 1.3),
    ("Jalan Pattimura", "Jalan Mayor Jenderal Sukowati", 1.0),
    ("Jalan Mayor Jenderal Sukowati", "Jalan Yos Sudarso", 1.2),
    ("Jalan Yos Sudarso", "Jalan Janoko", 0.6),
    ("Jalan Janoko", "Jalan Sadewo", 0.5),
    ("Jalan Sadewo", "Jalan Srikandi", 0.4),
    ("Jalan Srikandi", "Jalan Tripandita", 0.7),
    ("Jalan Tripandita", "Jalan Kunti", 0.8),
    ("Jalan Kunti", "Jalan Nangkulo", 0.9),
    ("Jalan Nangkulo", "Jalan Gitadini", 1.0),
    ("Jalan Gitadini", "Jalan Jawa", 1.1),
    ("Jalan Jawa", "Jalan Bromo", 1.2),
    ("Jalan Bromo", "Jalan Kawi", 1.3),
    ("Jalan Kawi", "Jalan Pandan", 1.0),
    ("Jalan Pandan", "Jalan Samodra", 1.1),
    ("Jalan Samodra", "Jalan Semeru", 1.2),
    ("Jalan Semeru", "Jalan Wilis", 1.3),
    ("Jalan Wilis", "Jalan Barat (Maospati–Barat)", 1.0),
    ("Jalan Barat (Maospati–Barat)", "Jalan Agung", 1.1),
    ("Jalan Agung", "Jalan Sendang Kamal", 1.2),

    # Edge penghubung ke node yang sebelumnya hanya di edges lama
    ("Jalan Raya Maospati", "Jalan Ahmad Yani", 1.0),
    ("Jalan Raya Maospati", "Jalan Terminal Maospati", 0.8),
    ("Jalan Raya Maospati", "Jalan Stasiun Maospati", 1.2),
    ("Jalan Terminal Maospati", "Jalan Stasiun Maospati", 0.6),
    ("Jalan Terminal Maospati", "Jalan Diponegoro", 0.9),
    ("Jalan Stasiun Maospati", "Jalan Sudirman", 0.7),
    ("Jalan Ahmad Yani", "Jalan Gatot Subroto", 1.3),
    ("Jalan Gatot Subroto", "Jalan Pahlawan", 1.0),
    ("Jalan Pahlawan", "Jalan Merdeka", 0.5),
    ("Jalan Merdeka", "Jalan Mayor Jenderal Sungkono", 0.7),
    ("Jalan Mayor Jenderal Sungkono", "Jalan Yos Sudarso", 0.9),
    ("Jalan Yos Sudarso", "Jalan Kartini", 0.4),
    ("Jalan Kartini", "Jalan Srikandi", 0.6),
    ("Jalan Srikandi", "Gang Mawar", 0.3),
    ("Jalan Srikandi", "Gang Melati", 0.4),
    ("Gang Mawar", "Gang Dahlia", 0.2),
    ("Gang Dahlia", "Gang Melati", 0.3),
    ("Gang Melati", "Gang Cemara", 0.5),
    ("Gang Cemara", "Jalan Wilis", 0.7),

    # Edge tambahan agar node-node penting terhubung
    ("Jalan Sudirman", "Jalan Jenderal Sudirman", 0.5),
    ("Jalan Mayor Jenderal Sungkono", "Jalan Mayor Jenderal Sukowati", 0.7),
    ("Jalan Terminal Maospati", "Jalan Barat (Maospati–Barat)", 2.0),
    ("Jalan Stasiun Maospati", "Jalan Barat (Maospati–Barat)", 2.2),
    ("Jalan Sendang Kamal", "Jalan Raya Sarangan", 3.0),
    ("Jalan Sendang Kamal", "Jalan Srikandi", 2.5),
    ("Jalan Agung", "Jalan Kawi", 2.0),
    ("Jalan Nangkulo", "Jalan Barat (Maospati–Barat)", 1.8),
    ("Jalan Gitadini", "Jalan Sendang Kamal", 2.1),
    ("Jalan Jawa", "Jalan Barat (Maospati–Barat)", 2.3),
    ("Jalan Bromo", "Jalan Barat (Maospati–Barat)", 2.4),
    ("Jalan Kawi", "Jalan Barat (Maospati–Barat)", 2.5),
    ("Jalan Pandan", "Jalan Barat (Maospati–Barat)", 2.6),
    ("Jalan Samodra", "Jalan Barat (Maospati–Barat)", 2.7),
    ("Jalan Semeru", "Jalan Barat (Maospati–Barat)", 2.8),
    ("Jalan Wilis", "Jalan Barat (Maospati–Barat)", 2.9),
]

# Buat graf
G = nx.Graph()
G.add_nodes_from(nodes)
G.add_weighted_edges_from(edges)

UPLOAD_FOLDER = os.path.join('static', 'profile_pics')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

coordinates = {
    "Jalan Raya Maospati–Madiun": [-7.611012, 111.401589],
    "Jalan Raya Maospati–Ngawi": [-7.604978, 111.373241],
    "Jalan Raya Maospati–Magetan": [-7.630185, 111.347628],
    "Jalan Raya Sarangan": [-7.663915, 111.332912],
    "Jalan Gubernur Suryo": [-7.630925, 111.340918],
    "Jalan Pahlawan": [-7.631825, 111.338925],
    "Jalan Jenderal Sudirman": [-7.632935, 111.336815],
    "Jalan Ahmad Yani": [-7.634025, 111.334725],
    "Jalan Diponegoro": [-7.635125, 111.332625],
    "Jalan Munginsidi": [-7.636225, 111.330525],
    "Jalan Pattimura": [-7.637335, 111.328425],
    "Jalan Mayor Jenderal Sukowati": [-7.638445, 111.326325],
    "Jalan Yos Sudarso": [-7.639525, 111.324225],
    "Jalan Janoko": [-7.640645, 111.322125],
    "Jalan Sadewo": [-7.641745, 111.320045],
    "Jalan Srikandi": [-7.642835, 111.317945],
    "Jalan Tripandita": [-7.643955, 111.315845],
    "Jalan Kunti": [-7.645055, 111.313745],
    "Jalan Nangkulo": [-7.646155, 111.311645],
    "Jalan Gitadini": [-7.647255, 111.309545],
    "Jalan Jawa": [-7.648355, 111.307445],
    "Jalan Bromo": [-7.649455, 111.305345],
    "Jalan Kawi": [-7.650555, 111.303245],
    "Jalan Pandan": [-7.651655, 111.301145],
    "Jalan Samodra": [-7.652755, 111.299045],
    "Jalan Semeru": [-7.653855, 111.296945],
    "Jalan Wilis": [-7.654955, 111.294845],
    "Jalan Barat (Maospati–Barat)": [-7.655975, 111.292745],
    "Jalan Agung": [-7.656975, 111.290645],
    "Jalan Sendang Kamal": [-7.657985, 111.288555],
    "Jalan Raya Maospati": [-7.629035, 111.349025],
    "Jalan Terminal Maospati": [-7.627525, 111.348225],
    "Jalan Stasiun Maospati": [-7.626035, 111.347435],
    "Jalan Sudirman": [-7.624545, 111.346625],
    "Jalan Gatot Subroto": [-7.623035, 111.345825],
    "Jalan Merdeka": [-7.621525, 111.345035],
    "Jalan Mayor Jenderal Sungkono": [-7.620035, 111.344225],
    "Jalan Kartini": [-7.618545, 111.343425],
    "Gang Mawar": [-7.617035, 111.342625],
    "Gang Melati": [-7.615525, 111.341825],
    "Gang Dahlia": [-7.614035, 111.341035],
    "Gang Cemara": [-7.612525, 111.340225]
}



@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    path = []
    km = 0
    meter = 0
    start = None
    end = None

    if request.method == "POST":
        start = request.form["start"]
        end = request.form["end"]
        try:
            path = nx.dijkstra_path(G, start, end)
            distance = nx.dijkstra_path_length(G, start, end)
            km = round(distance, 2)
            meter = int(distance * 1000)
            # Simpan history
            new_hist = History(
                user_id=current_user.id,
                start=start,
                end=end,
                route=" → ".join(path),
                distance=distance
            )
            db.session.add(new_hist)
            db.session.commit()
        except nx.NetworkXNoPath:
            path = ["Tidak ada jalur ditemukan."]
        except Exception as e:
            path = [f"Error: {e}"]

    return render_template(
        "index.html",
        nodes=nodes,
        user=current_user,
        start=start,
        end=end,
        path=path,
        coordinates=coordinates,
        km=km,
        meter=meter
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Username atau password salah.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Username sudah terdaftar.", "warning")
            return redirect(url_for("register"))
        hashed_pw = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash("Registrasi berhasil, silakan login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        # Ubah username
        new_username = request.form.get("username")
        if new_username and new_username != current_user.username:
            if User.query.filter_by(username=new_username).first():
                flash("Username sudah digunakan.", "danger")
                return render_template("profile.html", user=current_user)
            current_user.username = new_username
            flash("Username berhasil diubah.", "success")

        # Ubah password jika diisi
        new_password = request.form.get("password")
        if new_password:
            current_user.password = generate_password_hash(new_password, method="pbkdf2:sha256")
            flash("Password berhasil diubah.", "success")

        # Ubah foto profil jika diupload
        file = request.files.get("profile_pic")
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{current_user.id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.profile_pic = filename
            flash("Foto profil berhasil diupdate.", "success")
        elif file and file.filename != "":
            flash("Format file tidak didukung.", "danger")

        db.session.commit()
    # Ambil history pencarian user
    history = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).limit(20).all()
    # Konversi waktu ke WIB (Waktu Indonesia Barat, UTC+7)
    for h in history:
        h.wib_time = (h.timestamp + timedelta(hours=7)).strftime("%d-%m-%Y %H:%M")
    
    # Hitung pendapatan harian (hanya history hari ini)
    today = datetime.utcnow() + timedelta(hours=7)
    total_km = sum(
        h.distance for h in history
        if (h.timestamp + timedelta(hours=7)).date() == today.date()
    )
    pendapatan = int(total_km * 5000)

    return render_template("profile.html", user=current_user, history=history, pendapatan=pendapatan, total_km=total_km)

@app.route("/export_history/excel")
@login_required
def export_history_excel():
    history = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["No", "Dari", "Ke", "Rute", "Jarak (km)", "Waktu"])
    for idx, h in enumerate(history, 1):
        cw.writerow([idx, h.start, h.end, h.route, "%.2f" % h.distance, h.timestamp.strftime("%d-%m-%Y %H:%M")])
    output = BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="history.csv")

@app.route("/export_history/pdf")
@login_required
def export_history_pdf():
    history = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).all()
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "History Pencarian Rute")
    y -= 30
    p.setFont("Helvetica", 10)
    p.drawString(40, y, "No")
    p.drawString(60, y, "Dari")
    p.drawString(150, y, "Ke")
    p.drawString(240, y, "Rute")
    p.drawString(400, y, "Jarak (km)")
    p.drawString(470, y, "Waktu")
    y -= 15
    for idx, h in enumerate(history, 1):
        if y < 50:
            p.showPage()
            y = height - 40
        p.drawString(40, y, str(idx))
        p.drawString(60, y, h.start[:12])
        p.drawString(150, y, h.end[:12])
        p.drawString(240, y, h.route[:30] + ("..." if len(h.route) > 30 else ""))
        p.drawString(400, y, "%.2f" % h.distance)
        p.drawString(470, y, h.timestamp.strftime("%d-%m-%Y %H:%M"))
        y -= 15
    p.save()
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name="history.pdf")

def get_all_jalan():
    return nodes

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
