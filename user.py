from auth import login_required
from db import user_engine
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, g
)
from sqlalchemy import text

bp = Blueprint('user', __name__, url_prefix='/user')


#--------------------------------------------------------------------------------------------------------
# home

@bp.route('/user_home', methods=('GET', 'POST'))
@login_required
def user_home():
    return render_template('user/user_home.html')


#--------------------------------------------------------------------------------------------------------
# pokemon dollars

@bp.route('/user_dollars', methods=('GET', 'POST'))
@login_required
def user_dollars():
    balance = get_dollars(g.user[0])
    if request.method == 'POST':
        amount = request.form['amount']
        method = request.form['method']
        add_dollars(g.user[0], amount)
        flash(f'{amount}$ were added successfully!')
        return redirect(url_for('user.user_dollars'))
    return render_template('user/user_dollars.html', balance=balance)


def get_dollars(user_id):
    connection = user_engine.connect()

    balance = connection.execute(text('SELECT balance FROM users WHERE id = :id;'), dict(id=user_id)).fetchone()
    connection.commit()
    connection.close()
    return balance[0]

def add_dollars(user_id, amount):
    balance = get_dollars(user_id)
    new_balance = float(balance) + float(amount)
    connection = user_engine.connect()

    connection.execute(text('UPDATE users SET balance = :balance WHERE id = :id;'), dict(balance=new_balance, id=user_id))
    connection.commit()
    connection.close()

def subtract_dollars(user_id, amount):
    balance = get_dollars(user_id)
    new_balance = float(balance) - float(amount)

    connection = user_engine.connect()

    connection.execute(text('UPDATE users SET balance = :balance WHERE id = :id;'), dict(balance=new_balance, id=user_id))
    connection.commit()
    connection.close()

def transfer_dollars(buyer_id, seller_id, amount):
    buyer_balance = get_dollars(buyer_id)
    if buyer_balance >= amount:
        subtract_dollars(buyer_id, amount)
        add_dollars(seller_id, amount)
    else:
        flash('You don\'t have enough dollars!')


#--------------------------------------------------------------------------------------------------------
# cards

@bp.route('/user_collection', methods=('GET', 'POST'))
@login_required
def user_collection():
    cards = get_cards()
    return render_template('user/user_collection.html', cards = cards)


@bp.route('/user_card/<id>', methods=('GET', 'POST'))
@login_required
def user_card(id):
    card = get_card_info(id)
    return render_template('user/user_card.html', card = card)

def get_card_info(id):
    connection = user_engine.connect()
    # [0=id, 1=condition, 2=value, 3=name, 4=weight, 5=height, 6=type, 7=set, 8=img]
    result = connection.execute(text('SELECT collection.card_id, collection.card_condition, collection.value, '
                                       'pokemons.name, pokemons.weight, pokemons.height, '
                                       'types.name, '
                                       'sets.name, '
                                        'card.image_id '
                                       'FROM collection '
                                       'INNER JOIN card ON collection.card_id = card.id '
                                       'INNER JOIN pokemons ON card.pokemon_id = pokemons.id '
                                       'INNER JOIN types ON pokemons.type_id = types.id '
                                       'INNER JOIN sets ON card.set_id = sets.id '
                                       'WHERE card.id = :id '
                                       'ORDER BY pokemons.name;'), dict(id=id)).fetchone()
    connection.commit()
    connection.close()
    return result

def get_cards():
    connection = user_engine.connect()
    # [0=id, 1=name, 2=set, 3=img]
    result = connection.execute(text('SELECT collection.card_id, '
                                       'pokemons.name, '
                                       'sets.name, '
                                        'card.image_id '
                                       'FROM collection '
                                       'INNER JOIN card ON collection.card_id = card.id '
                                       'INNER JOIN pokemons ON card.pokemon_id = pokemons.id '
                                       'INNER JOIN sets ON card.set_id = sets.id '
                                       'WHERE collection.user_id = :id '
                                       'ORDER BY pokemons.name;'), dict(id=g.user[0])).fetchall()
    connection.commit()
    connection.close()
    return result


#--------------------------------------------------------------------------------------------------------
# auctions

@bp.route('/user_auctions', methods=('GET', 'POST'))
@login_required
def user_auctions():
    return render_template('user/user_auctions.html')


@bp.route('/place_bid', methods=('GET', 'POST'))
@login_required
def place_bid():
    return render_template('user/place_bid.html')


@bp.route('/user_bids', methods=('GET', 'POST'))
@login_required
def user_bids():
    return render_template('user/user_bids.html')


@bp.route('/user_bids_history', methods=('GET', 'POST'))
@login_required
def user_bids_history():
    return render_template('user/user_bids_history.html')