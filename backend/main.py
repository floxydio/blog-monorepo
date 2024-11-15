from flask import Flask, request,jsonify,url_for
from pony.orm import *
from dotenv import load_dotenv, dotenv_values
from werkzeug.utils import secure_filename

import os
import pymysql
import bcrypt
import uuid

load_dotenv()
app = Flask(__name__)

config = dotenv_values(".env")
mysql = pymysql.connect(
        host= config['DB_HOST'],
        user= config['DB_USER'],
        password= config['DB_PASSWORD'],
        database= config['DB_NAME'],
)
UPLOAD_FOLDER = 'static/storage'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def hello_world():
    return {
        "status": 200,
        "theme": "black"
    }

@app.route("/submit-blog", methods=['POST'])
def submitBlog():
    if 'img_blog' not in request.files:
        return jsonify({
            "status": 400,
            "error": True,
            "message": "No image file provided"
        }), 400
    
    file = request.files['img_blog']
    
    if file.filename == '':
        return jsonify({
            "status": 400,
            "error": True,
            "message": "No selected file"
        }), 400

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(file_path)
        
        image_url = url_for('static', filename=f'storage/{unique_filename}', _external=True)
        
        title = request.form['title']
        description = request.form['content']
        
        cur = mysql.cursor()
        cur.execute("INSERT INTO blog (title, img_blog, content) VALUES (%s, %s, %s)", (title, image_url, description))
        mysql.commit()

        if cur.rowcount > 0:
            return jsonify({
                "status": 201,
                "error": False,
                "message": "Blog submitted successfully",
                "image_url": image_url 
            }), 201
        else:
            return jsonify({
                "status": 400,
                "error": True,
                "message": "Blog submission failed"
            }), 400
    else:
        return jsonify({
            "status": 400,
            "error": True,
            "message": "Invalid file format"
        }), 400   
    
    
@app.route("/get-blogs", methods=['GET'])
def getBlogs():
    page = request.args.get('page', default=1, type=int)  
    page_size = request.args.get('page_size', default=5, type=int) 

    offset = (page - 1) * page_size  
    cur = mysql.cursor()
    cur.execute("SELECT * FROM blog LIMIT %s OFFSET %s", (page_size, offset))
    blogs = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM blog")
    total_blogs = cur.fetchone()[0]
    total_pages = (total_blogs + page_size - 1) // page_size
    return jsonify({
        "status": 200,
        "error": False,
        "data": blogs,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_blogs": total_blogs
        }
    })

@app.route("/get-blog/<int:id>", methods=['GET'])
def getBlogById(id):
    cur = mysql.cursor()
    cur.execute("SELECT * FROM blog WHERE id_blog = %s", (id,))
    blog = cur.fetchone()
    if blog:
        return jsonify({
            "status": 200,
            "error": False,
            "data": blog
        }), 200
    else:
        return jsonify({
            "status": 404,
            "error": True,
            "message": "Blog not found"
        }), 404
    
@app.route("/sign-up", methods=['POST'])
def registerUser():
    if request.method == 'POST':
        nama=request.form['nama']
        username=request.form['username']
        password=request.form['password']

        bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()

        hash = bcrypt.hashpw(bytes,salt)

        cur = mysql.cursor()

        cur.execute("INSERT INTO user(nama,username,password,online) VALUES (%s,%s,%s,1)", (nama,username,hash))

        mysql.commit()

        if cur.rowcount > 0:
            return jsonify({
                "status": 200,
                "error": False,
                "message": "Successfully Sign In"
            }), 200
        else:
            return jsonify({
                "status": 400,
                "error": False,
                "message": "Something went wrong"
            }), 400


@app.route("/sign-in", methods=["POST"])
def signInUser():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cur = mysql.cursor()
        cur.execute("SELECT * FROM user WHERE username = %s", (username,))
        user = cur.fetchone()
        if not user:
            return jsonify({
                "status": 400,
                "error": True,
                "message": "Username not found"
            }), 400

        stored_hash = user[3] 
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")
        password_bytes = password.encode("utf-8")
       
        if bcrypt.checkpw(password_bytes, stored_hash):
            data_map = {
            "id_user": user[0],
            "nama": user[1]
            }
            response = {
                "status": 200,
                "error": False,
                "data": data_map,
                "message": "Login Successfull"
            }
            return jsonify(response), 200
        else:
            return jsonify({
                "status": 400,
                "error": True,
                "message": "Invalid password"
            }), 400