# import random
# import pokebase as pb
# from db import admin_connection


# print('Name: {}'.format(rand_poke.name))
# print('Height: {}'.format(rand_poke.height))
# print('Weight: {}'.format(rand_poke.weight))
# print('Type: {}'.format(rand_poke.types[0].type.name.title().lower()))

# def add_random_poke():
#     success = False
#     while not success:
#         rand_num = random.randint(1, 1200)
#         try:
#             print(rand_num)
#             rand_poke = pb.pokemon(rand_num)
#             cursor = admin_connection.cursor()
#             sql = 'INSERT INTO pokemons(id, name, type_id, weight, height) VALUES(%s, %s, %s, %s, %s);'
#             cursor.execute(sql, (rand_num, rand_poke.name, get_type_id(rand_poke.types[0].type.name.title().lower()), rand_poke.weight, rand_poke.height))
#             admin_connection.commit()
#             cursor.close()
#             print(f'Pokemon {rand_poke.name} was added successfully')
#             success = True
#         except:     # betere exception maken!!
#             print(rand_num)
#             print('Failed to add pokemon! Retrying...')
#             continue
#
# def get_type_id(type_name:str):
#     cursor = admin_connection.cursor()
#     sql = 'SELECT id FROM types WHERE name = %s;'
#     cursor.execute(sql, (type_name,))
#     admin_connection.commit()
#     cursor.close()
#     return cursor.fetchone()[0]
#
# def add_new_set(set_name:str):
#     cursor = admin_connection.cursor()
#     sql = 'INSERT INTO sets(name) VALUES(%s);'
#     cursor.execute(sql, (set_name,))
#     admin_connection.commit()
#     cursor.close()
#
# def add_new_card(pokemon_id:int, set_id:int):
#     cursor = admin_connection.cursor()
#     sql = 'INSERT INTO card(pokemon_id, set_id) VALUES(%s, %s);'
#     cursor.execute(sql, (pokemon_id, set_id))
#     admin_connection.commit()
#     cursor.close()
#
# def add_card_to_collection(user_id:int, card_id:int, condition:str, value:float, sellable:int):
#     cursor = admin_connection.cursor()
#     sql = 'INSERT INTO collection(user_id, card_id, card_condition, value, sellable) VALUES(%s, %s, %s, %s, %s);'
#     cursor.execute(sql, (user_id, card_id, condition, value, sellable))
#     admin_connection.commit()
#     cursor.close()

#add_new_set('Christmas-2024')
#add_random_poke()
#add_new_card(505, 1)
#add_card_to_collection(37, 2, 'New', 30.00, 1)