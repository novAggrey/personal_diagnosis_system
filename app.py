import os
import pickle
import cv2
from fpdf import FPDF
import tensorflow,numpy as np
from keras.models import load_model
from flask import Flask, render_template, flash,redirect, url_for, request,Response,session,g
from flask_login import login_required
from werkzeug.utils import secure_filename
import sqlite3 as sql

app = Flask(__name__)
app.secret_key = "pds"

model_d = pickle.load(open('models/diabetes.pkl','rb'))
model_t = load_model('models/tb_model.h5')
model_p = pickle.load(open('models/pressure.pkl','rb'))

conn = sql.connect("database.db",check_same_thread=False)
c = conn.cursor()

def create_table():
    c.execute('CREATE TABLE IF NOT EXISTS users(user_id INTEGER,fullname TEXT,age TEXT,sex TEXT,password TEXT,PRIMARY KEY(user_id))')

def add_user_reg(fullname,age,sex,password):
    c.execute('INSERT INTO users(fullname,age,sex,password) VALUES (?,?,?,?)',(fullname,age,sex,password))
    conn.commit()

def add_Bp(name,pr,age,sex):
    c.execute('INSERT INTO pressure(fullname,pressure,age,sex) VALUES (?,?,?,?)',(name,pr,age,sex))
    conn.commit()

def add_Db(name,pr,age,sex):
    c.execute('INSERT INTO diabetes(fullname,diabetes,age,sex) VALUES (?,?,?,?)',(name,pr,age,sex))
    conn.commit()

def add_Tb(name,pr):
    c.execute('INSERT INTO tibii(fullname,tuberculosis) VALUES (?,?)',(name,pr))
    conn.commit()
    
def login_user(fullname,password):
    c.execute('SELECT * FROM users WHERE fullname =? AND password=?',(fullname,password))
    data = c.fetchall()
    return data

def view_all():
    c.execute('SELECT * FROM users')
    data = c.fetchall()
    return data

def delete_all():
    c.execute('DELETE  FROM users')
   
#START
@app.route("/index")
def index():
    con=sql.connect("database.db")
    con.row_factory=sql.Row
    cur=con.cursor()
    cur.execute("select * from users")
    data=cur.fetchall()
    return render_template("index.html",datas=data)

@app.route("/add_user",methods=['POST','GET'])
def add_user():
    if request.method=='POST':
        fullname=request.form['fullname']
        age=request.form['age']
        sex=request.form['sex']
        password=request.form['password']
        con=sql.connect("database.db")
        cur=con.cursor()
        cur.execute("insert into users(fullname,age,sex,password) values (?,?,?,?)",(fullname,age,sex,password))
        con.commit()
        flash('User Added','success')
        return redirect(url_for("index"))
    return render_template("add_user.html")

@app.route("/edit_user/<string:user_id>",methods=['POST','GET'])
def edit_user(user_id):
    if request.method=='POST':
        fullname=request.form['fullname']
        age=request.form['age']
        sex=request.form['sex']
        password=request.form['password']
        con=sql.connect("database.db")
        cur=con.cursor()
        cur.execute("update users set fullname=?,age=?,sex=?,password=? where user_id=?",(fullname,age,sex,password,user_id))
        con.commit()
        flash('User Updated','success')
        return redirect(url_for("index"))
    con=sql.connect("database.db")
    con.row_factory=sql.Row
    cur=con.cursor()
    cur.execute("select * from users where user_id=?",(user_id,))
    data=cur.fetchone()
    return render_template("edit_user.html",datas=data)
    
@app.route("/delete_user/<string:user_id>",methods=['GET'])
def delete_user(user_id):
    con=sql.connect("database.db")
    cur=con.cursor()
    cur.execute("delete from users where user_id=?",(user_id,))
    con.commit()
    flash('User Deleted','warning')
    return redirect(url_for("index"))

#END
@app.route("/",methods=["POST","GET"])
#@login_required
def login():
    if request.method == "POST":
        fullname = request.form["fullname"]
        password = request.form["password"]
        session['name'] = fullname

        create_table()
        login = login_user(fullname,password)
        if login:
            #return redirect(url_for("index_auth"))
            return render_template("home.html")
        if fullname == "admin" and password == "admin":
            return redirect(url_for('index'))
        
    return render_template("login.html")
    
@app.route("/pressure")
def pressure():
    return render_template("pressure.html")

@app.route("/pressure",methods=['POST'])
def press():
    sex = request.form['sex']
    gender = request.form['sex']
    if sex == 'male':
        sex = 1
    else:
        sex = 0
    age = int(request.form['age'])
    mar = request.form['marry']
    if mar == 'yes':
        mar = 1
    else:
        mar = 0
    work = request.form['cig']
    if work == 'child':
        work = 0
    elif work == 'gvt':
        work = 1
    elif work == 'none':
        work = 2
    elif work == 'private':
        work = 3
    else:
        work = 4
    res = request.form['area']
    if res == 'urban':
        res = 1
    else:
        res = 0
    glucose = float(request.form['glucose'])
    bmi = float(request.form['bmi'])
    smoke = request.form['cig']
    if smoke == 'smoked':
        smoke = 1
    elif smoke == 'never':
        smoke = 2
    elif smoke == 'smokes':
        smoke = 3
    else:
        smoke = 4
    arr = [[sex,age,mar,work,res,glucose,bmi,smoke]]
    pred = model_p.predict(arr)
    pr = pred
    if pr == 0:
        pr = "NORMAL"
    else:
        pr = "BLOOD PRESSURE"
        
    c.execute('CREATE TABLE IF NOT EXISTS pressure(pr_id INTEGER,fullname TEXT,pressure TEXT,age TEXT,sex TEXT, PRIMARY KEY(pr_id))')
    add_Bp(session['name'],pr,age,gender)
    
    return render_template("pressure.html",data=pred)

@app.route('/diabetes')
#@login_required
def diabetes():
    return render_template("diabetes.html")
@app.route('/submit_d',methods=['POST'])
def make():
    glucose = float(request.form['glucose'])
    sys_bp = int(request.form['sys_bp'])
    dias_bp = int(request.form['dias_bp'])
    height = int(request.form['height'])
    chol = float(request.form['chol'])
    sex = request.form['sex']
    gender = request.form['sex']
    if sex == "Male":
        sex = 1
    else:
        sex = 0
    age = int(request.form['age'])
    whp = float(request.form['whp'])
    mass = float(request.form['mass'])
    
    inputs = [[glucose,age,sex,height,mass,sys_bp,dias_bp,chol,whp]]
    pred = model_d.predict(inputs)
    
    pr = pred
    if pr == 0:
        pr = "NORMAL"
    else:
        pr = "DIABETIC"
    c.execute('CREATE TABLE IF NOT EXISTS diabetes(db_id INTEGER,fullname TEXT,diabetes TEXT,age TEXT,sex TEXT, PRIMARY KEY(db_id))')
    add_Db(session['name'],pr,age,gender)
    conn.commit()
    
    return render_template("diabetes.html",data=pred)

@app.route("/tuberculosis")#
def tuberculosis():
      return render_template("tuberculosis.html")
  
UPLOAD_FOLDER = 'static/uploads/'
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submit_t', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image = "static/uploads/"+file.filename
        img = cv2.imread(image)
        img = tensorflow.image.resize(img,(50,50))
        img = tensorflow.expand_dims(img,0)/255
        
        pred = model_t.predict(img)# MODEL USE
        pred = np.argmax(pred)
        tuberculosis = pred
        if tuberculosis == 0:
            tuberculosis = "NO"
        else:
            tuberculosis = "YES"
            
        c.execute('CREATE TABLE IF NOT EXISTS tibii(tb_id INTEGER,fullname TEXT,tuberculosis TEXT, PRIMARY KEY(tb_id))')
        add_Tb(session['name'],tuberculosis)
        conn.commit()
        return render_template('tuberculosis.html', filename=filename,data=pred)
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)
        
@app.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route("/home")
#@login_required
def index_auth():
    #if g.user:
    return render_template("home.html")
  
####SESSION START
"""
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

@app.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return 'Dropped!'

@app.route('/getsession')
def getsession():
    if 'user' in session:
        return session['user']
 
    return 'Not logged in!'"""
####SESSION END

@app.route("/map")
def map():
    return render_template("map.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form['fullname']
        age = request.form['age']
        sex = request.form['sex']
        password = request.form['password']

        create_table()
        add_user_reg(fullname,age,sex,password)

        return redirect(url_for("login"))
    return render_template("register.html")

@app.route('/repo')
def home():
    #if g.user:
    return render_template("repo.html")

@app.route('/view')
def mine():
    conn = sql.connect("database.db",check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pressure")
    data = cursor.fetchall()
    
    return render_template("repo.html",data=data)

@app.route('/download/report/pdf')
def download_report():
    conn = None
    cursor = None
    conn = sql.connect("database.db",check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pressure WHERE fullname=?",(session['name'],))
    result = cursor.fetchall()
    
    """cursor.execute("SELECT * FROM diabetes WHERE fullname=?",(session['name'],))
    result1 = cursor.fetchall()
    
    cursor.execute("SELECT * FROM tibii WHERE fullname=?",(session['name'],))
    result2 = cursor.fetchall()"""
    
    try:     
        #c.execute('CREATE TABLE IF NOT EXISTS pressure(pr_id INTEGER,fullname TEXT,pressure TEXT,age TEXT,sex TEXT, PRIMARY KEY(pr_id))')        
        
        pdf = FPDF()
        pdf.add_page()
         
        page_width = pdf.w - 5 * pdf.l_margin
         
        pdf.set_font('Times','B',14.0) 
        pdf.cell(page_width, 0.0, 'User Data', align='C')
        pdf.ln(10)
 
        pdf.set_font('Courier', '', 12)
         
        col_width = page_width/4
         
        pdf.ln(1)
         
        th = pdf.font_size
        
        pdf.cell(col_width, th,"ID",border=1)
        pdf.cell(col_width, th,"NAME",border=1)
        pdf.cell(col_width, th,"STATUS",border=1)
        pdf.cell(col_width, th,"AGE",border=1)
        pdf.cell(col_width, th,"GENDER", border=1)
        pdf.ln(th)
                    
        for row in result:
            pdf.cell(col_width, th,str(row[0]),border=1)
            pdf.cell(col_width, th,str(row[1]),border=1)
            pdf.cell(col_width, th,str(row[2]),border=1)
            pdf.cell(col_width, th,str(row[3]),border=1)
            pdf.cell(col_width, th,str(row[4]), border=1)
            pdf.ln(th)
         
        pdf.ln(10)
         
        pdf.set_font('Times','',10.0) 
        pdf.cell(page_width, 0.0, '- end of report -', align='C')
         
        return Response(pdf.output(dest='S').encode('latin-1'), 
                        mimetype='application/pdf',
                        headers={'Content-Disposition':'attachment;filename=employee_report.pdf'})
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
    

if __name__ == "__main__":
    app.run(debug=False, port=3000,threaded=False)
    
