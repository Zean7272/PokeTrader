from auth import login_required
from db import admin_engine
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, g
)
from werkzeug.security import generate_password_hash
import random
import pokebase as pb
from sqlalchemy import text

bp = Blueprint('admin', __name__, url_prefix='/admin')

# gets users from database
def getUsers():
    connection = admin_engine.connect()

    result = connection.execute(text("SELECT id, username, email From users where role_id = :role_id order by id DESC;"), dict(role_id=2)).fetchall()
    connection.commit()
    connection.close()
    return result

# gets a user from database
def getUser(id):
    connection = admin_engine.connect()

    result = connection.execute(text("SELECT id, username, email From users where id = :id;"), dict(id=id)).fetchone()
    connection.commit()
    connection.close()
    return result


@bp.route('/admin_home', methods=('GET', 'POST'))
@login_required
def admin_home():
    return render_template('admin/admin_home.html')


@bp.route('/admin_account_manager', methods=('GET', 'POST'))
@login_required
def admin_account_manager():
    result = getUsers()
    return render_template('admin/admin_account_manager.html', result=result)


@bp.route('/admin_account_register', methods=('GET', 'POST'))
@login_required
def admin_account_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        ww1 = request.form['ww-1']
        ww2 = request.form['ww-2']
        role = request.form['role']
        error = None
        connection = admin_engine.connect()
        if ww1 == ww2:

            connection.execute(text("INSERT INTO users(username ,email, password, role_id, is_2fa_enabled, secret_token) "
                                    "VALUES(:username, :email, :password, :role_id, :is_2fa_enabled, :secret_token);"),
                                    dict(username=username, email=email , password=generate_password_hash(ww1), role_id=0, secret_token=0))
            connection.commit()
            connection.close()
        return redirect(url_for('admin.admin_account_manager'))
    return render_template('admin/admin_account_register.html')

@bp.route('/admin_account_editor/<id>', methods=('GET', 'POST'))
@login_required
def admin_account_editor(id):
    result = getUser(id)
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        connection = admin_engine.connect()

        connection.execute(text("UPDATE users set username = :username, email = :email WHERE users.id = :id;"),
                           dict(username=username, email=email,  id=id))
        connection.commit()
        connection.close()
        return redirect(url_for('admin.admin_account_manager'))
    return render_template('admin/admin_account_editor.html', result=result)


@bp.route('/admin_account_deleter/<id>', methods=('GET', 'POST'))
@login_required
def admin_account_deleter(id):
    result = getUser(id)
    own_id = g.user[0]
    if int(id) != int(own_id):
        connection = admin_engine.connect()

        connection.execute(text("Delete from users WHERE users.id = :id;"), dict(id=id))
        connection.commit()
        connection.close()
    else:
        flash("No delete self plz call 113 if you want to delete yourself")
    return redirect(url_for('admin.admin_account_manager'))

#--------------------------------------------------------------------------------------------------
# cards, sets, pokemons en images

@bp.route('/admin_cards', methods=('GET', 'POST'))
@login_required
def admin_cards():
    cards = admin_get_cards()
    return render_template('admin/admin_cards.html', cards=cards)


@bp.route('/admin_card_info/<id>', methods=('GET', 'POST'))
@login_required
def admin_card_info(id):
    card = admin_get_card_info(id)
    return render_template('admin/admin_card_info.html', card = card)


@bp.route('/admin_pokemons', methods=('GET', 'POST'))
@login_required
def admin_pokemons():
    pokemons = get_pokemons()
    sets = get_sets()
    images = get_images()

    if request.method == 'POST':
        pokemon_id = request.form['poke']
        set_id = request.form['set']
        image_id = request.form['image']

        connection = admin_engine.connect()
        connection.execute(text('INSERT INTO card(pokemon_id, set_id, image_id) VALUES(:pokemon_id, :set_id, :image_id);'),
                           dict(pokemon_id=pokemon_id, set_id=set_id, image_id=image_id))
        connection.commit()
        card_id = connection.execute(text('SELECT LAST_INSERT_ID() FROM card;'), dict()).fetchone()[0]
        connection.commit()

        card_condition = 'New'
        card_value = 20.00
        sellable = 1
        owner = g.user[0]

        connection.execute(text('INSERT INTO collection(user_id, card_id, card_condition, value, sellable) '
                                'VALUES(:user_id, :card_id, :card_condition, :card_value, :sellable);'),
                                dict(user_id=owner, card_id=card_id, card_condition=card_condition, card_value=card_value, sellable=sellable))
        connection.commit()
        connection.close()
        flash(f'Card was added successfully!')
        return redirect(url_for('admin.admin_cards'))
    return render_template('admin/admin_pokemons.html', pokemons=pokemons, sets=sets, images=images)


@bp.route('/add_random_poke', methods=('GET', 'POST'))
@login_required
def add_random_poke():
    success = False
    while not success:
        rand_num = random.randint(1, 1200)
        try:
            rand_poke = pb.pokemon(rand_num)
            connection = admin_engine.connect()

            connection.execute(text('INSERT INTO pokemons(id, name, type_id, weight, height) '
                                'VALUES(:id, :name, :type_id, :weight, :height);'),
                           dict(id=rand_num, name=rand_poke.name, type_id=get_type_id(rand_poke.types[0].type.name.title().lower()), weight=rand_poke.weight, height=rand_poke.height))
            connection.commit()
            connection.close()
            success = True
            flash(f'Pokemon {rand_poke.name} was added successfully!')
            return redirect(url_for('admin.admin_pokemons'))
        except:     # betere exception maken!!
            flash('Failed to add pokemon! Retrying...')
            continue


@bp.route('/admin_add_set', methods=('GET', 'POST'))
@login_required
def admin_add_set():
    if request.method == 'POST':
        set = request.form['set']

        connection = admin_engine.connect()

        connection.execute(text('INSERT INTO sets(name) VALUES(:name);'), dict(name=set))
        connection.commit()
        connection.close()
        flash(f'Pokemon {set} was added successfully!')
        return redirect(url_for('admin.admin_pokemons'))
    return render_template('admin/admin_add_set.html')


def get_type_id(type_name:str):
    connection = admin_engine.connect()
    result = connection.execute(text('SELECT id FROM types WHERE name = :name;'), dict(name=type_name,)).fetchone()
    connection.commit()
    connection.close()
    return result[0]

def get_pokemons():
    connection = admin_engine.connect()
    result = connection.execute(text('SELECT id, name FROM pokemons ORDER BY name;')).fetchall()
    connection.commit()
    connection.close()
    return result

def get_sets():
    connection = admin_engine.connect()
    result = connection.execute(text('SELECT id, name FROM sets ORDER BY name;')).fetchall()
    connection.commit()
    connection.close()
    return result

def get_images():
    connection = admin_engine.connect()
    result = connection.execute(text('SELECT id, image_name FROM images ORDER BY image_name;')).fetchall()
    connection.commit()
    connection.close()
    return result

def admin_get_cards():
    connection = admin_engine.connect()

    result = connection.execute(text('SELECT collection.card_id, collection.user_id, '
                               'pokemons.name, '
                               'sets.name , '
                                'card.image_id '
                               'FROM collection '
                               'INNER JOIN card ON collection.card_id = card.id '
                               'INNER JOIN pokemons ON card.pokemon_id = pokemons.id '
                               'INNER JOIN sets ON card.set_id = sets.id '
                               'ORDER BY pokemons.name;')).fetchall()

    connection.close()
    return result

def admin_get_card_info(id):
    connection = admin_engine.connect()

    result = connection.execute(text('SELECT collection.card_id, collection.card_condition, collection.value, '
                               'pokemons.name, pokemons.weight, pokemons.height, '
                               'types.name, '
                               'sets.name , '
                               'users.username, '
                                'card.image_id '
                               'FROM collection '
                               'INNER JOIN card ON collection.card_id = card.id '
                               'INNER JOIN pokemons ON card.pokemon_id = pokemons.id '
                               'INNER JOIN types ON pokemons.type_id = types.id '
                               'INNER JOIN sets ON card.set_id = sets.id '
                               'INNER JOIN users ON collection.user_id = users.id '
                               'WHERE card.id = :id '
                               'ORDER BY pokemons.name;'),
                                dict(id=id)).fetchone()
    connection.commit()
    connection.close()
    return result

#--------------------------------------------------------------------------------------------------
# auctions

@bp.route('/admin_auction_location_deleter/<id>', methods=('GET', 'POST'))
def admin_auction_location_deleter(id):
    result = getUser(id)
    connection = admin_engine.connect()
    sql = "Delete from auction_location WHERE id = %s;"
    connection.execute(text("Delete from auction_location WHERE id = :id;"), dict(id=id))
    connection.commit()
    connection.close()
    return redirect(url_for('admin.admin_auction_location_manager'))

def getLocation():
    connection = admin_engine.connect()

    result = connection.execute(text("SELECT id, street, postalcode, city From auction_location")).fetchall()
    connection.commit()
    connection.close()
    return result


@bp.route('/admin_auction_location_manager', methods=('GET', 'POST'))
def admin_auction_location_manager():
    result = getLocation()
    return render_template('admin/admin_auction_location_manager.html', result=result)

@bp.route('/admin_auction_location_register', methods=('GET', 'POST'))
def admin_auction_location_register():
    if request.method == 'POST':
        street = request.form['street']
        postalcode = request.form['postalcode']
        city = request.form['city']
        connection = admin_engine.connect()

        connection.execute(text("INSERT INTO auction_location(street, postalcode, city) VALUES(:street, :postalcode, :city);"),
                           dict(street=street, postalcode=postalcode, city=city))
        connection.commit()
        connection.close()
        return redirect(url_for('admin.admin_auction_location_manager'))
    return render_template('admin/admin_auction_location_register.html')



@bp.route('/admin_auction_deleter/<id>', methods=('GET', 'POST'))
def admin_auction_deleter(id):
    connection = admin_engine.connect()

    connection.execute(text("Delete from auction WHERE id = :id;"), dict(id=id))
    connection.commit()
    connection.close()
    return redirect(url_for('admin.admin_auction_manager'))

def getAuction():
    connection = admin_engine.connect()

    result = connection.execute(text("SELECT auction.id, auction.name, auction_location.street, auction_location.postalcode, auction_location.city, "
                           "auction.start_time, auction.end_time "
                           "From auction "
                           "inner join auction_location on auction.location_id = auction_location.id;")).fetchall()
    connection.commit()
    connection.close()
    return result


@bp.route('/admin_auction_manager', methods=('GET', 'POST'))
def admin_auction_manager():
    result = getAuction()
    return render_template('admin/admin_auction_manager.html', result=result)

@bp.route('/admin_auction_maker', methods=('GET', 'POST'))
def admin_auction_maker():
    result = getLocation()
    if request.method == 'POST':
        name = request.form['name']
        location_id = request.form['location_id']
        start_time = request.form['start-time']
        end_time = request.form['end-time']
        connection = admin_engine.connect()

        connection.execute(text("INSERT INTO auction(name, location_id, start_time, end_time) "
                                "VALUES(:name, :location_id, :start_time, :end_time);"),
                           dict(name=name, location_id=location_id, start_time=start_time, end_time=end_time))
        connection.commit()
        connection.close()
        return redirect(url_for('admin.admin_auction_manager'))
    return render_template('admin/admin_auction_maker.html', result=result)
