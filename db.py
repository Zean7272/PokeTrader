import pymysql
from sqlalchemy import create_engine, text

db = 'poketrader'

# user_connection = pymysql.connections.Connection(

# )

user_engine = create_engine("mysql+mysqlconnector://pokeUser:DitIs1User@localhost/poketrader")

#admin_connection = pymysql.connections.Connection(

# )

admin_engine = create_engine("mysql+mysqlconnector://pokeAdmin:DitIs1Admin@localhost/poketrader")

#----------------------------------------------
# Voorbeeld!!!!!!!
#----------------------------------------------
# connection = admin_engine.connect()
# result = connection.execute(text("SELECT * FROM types WHERE id = :id ORDER BY id;"), dict(id=id)).fetchone/all()
# connection.close()
#
# for row in result:
#     print(row)

