from db import user_engine, admin_engine
from flask import (
    Blueprint, abort, make_response, request, redirect, url_for, flash
)
from sqlalchemy import text
from werkzeug.utils import secure_filename
from PIL import Image
import io


bp = Blueprint('image', __name__, url_prefix='/image')


@bp.route('/upload', methods=('GET', 'POST'))
def upload():
    if request.method == 'POST':
        pic = request.files['pic']
        if not pic:
            flash('No pic uploaded!')

        filename = secure_filename(pic.filename)
        mimetype = pic.mimetype
        # Validate that the uploaded file is an image
        if not mimetype.startswith('image/'):
            flash('Uploaded file is not an image!')

        try:
            # Open the image file and convert it to JPG format
            img = Image.open(pic)
            # Ensure compatibility with JPG format
            img = img.convert('RGB')

            # Save the image to a bytes buffer
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            buffer.seek(0)

            # Use a new filename with a .jpg extension
            filename = f"{filename.rsplit('.', 1)[0]}.jpg"
            mimetype = 'image/jpg'

            # Save the converted image to the database
            connection = admin_engine.connect()
            connection.execute(
                text('INSERT INTO images(image, image_name, image_type) VALUES(:image, :image_name, :image_type);'),
                dict(image=buffer.read(), image_name=filename, image_type=mimetype))
            connection.commit()
            connection.close()

            return redirect(url_for('admin.admin_pokemons'))
        except Exception as e:
            flash(f"Image processing failed: {e}")
            return redirect(url_for('admin.admin_pokemons'))


@bp.route('/serveImage/<image_id>')
def serve_image(image_id):
    connection = user_engine.connect()
    image = connection.execute(text('SELECT id, image, image_name, image_type FROM images WHERE id = :id;'), dict(id=image_id)).fetchone()
    connection.commit()
    connection.close()

    if image is None:
        abort(404)

    response = make_response(image[1])
    response.headers.set('Content-Type', image[3])
    response.headers.set('Content-Disposition', 'inline', filename=image[2])
    return response