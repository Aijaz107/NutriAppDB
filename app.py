import random
from flask import Flask, request, jsonify
import sqlite3
import textrazor
from datetime import datetime
from difflib import SequenceMatcher

import requests

textrazor.api_key = "148e07b6094bfd5b58eb169c49b0407475c3a374bd017a6dd0c213d6"
client = textrazor.TextRazor(extractors=["entities", "topics"])

app = Flask(__name__)

def create_tables():
    conn = sqlite3.connect('nutri.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS menu
                 (menu_number INTEGER PRIMARY KEY, dish_name TEXT, description TEXT, 
                 ingredients TEXT, price REAL, avg_time_taken INTEGER, disease_list TEXT, 
                 recipe_description TEXT, calories INTEGER, created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                 updated_at TEXT DEFAULT NULL, deleted_at TEXT DEFAULT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (order_id INTEGER PRIMARY KEY, total_bill REAL, customer_name TEXT, preferences TEXT,
                 created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                 updated_at TEXT DEFAULT NULL, deleted_at TEXT DEFAULT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS order_items
                 (order_item_id INTEGER PRIMARY KEY, order_id INTEGER, dish_name TEXT, quantity INTEGER,
                 imagelink TEXT, price REAL,
                 FOREIGN KEY (order_id) REFERENCES orders(order_id))''')
    conn.commit()
    conn.close()

create_tables()

# Error handling decorator
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify(error=str(e)), 500

# Load base keywords from a file
with open("base_keywords.txt", "r", encoding="utf-8") as base_file:
    base_keywords = set(line.strip().lower() for line in base_file)

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def filter_generated_keywords(keywords):
    filtered_keywords = set()  # Use a set to store unique keywords
    for keyword in keywords:
        add_keyword = True
        for base_keyword in filtered_keywords.copy():
            similarity_score = similarity(keyword, base_keyword)
            if similarity_score >= 0.8:
                # Keep the keyword with greater length
                if len(keyword) > len(base_keyword):
                    filtered_keywords.remove(base_keyword)
                else:
                    add_keyword = False
                    break

        if add_keyword:
            filtered_keywords.add(keyword)

    return list(filtered_keywords)

def filter_base_keywords(generated_keywords):
    filtered_base_keywords = []
    for base_keyword in base_keywords:
        for generated_keyword in generated_keywords:
            similarity_score = similarity(generated_keyword.lower(), base_keyword)
            if similarity_score >= 0.8:
                filtered_base_keywords.append(generated_keyword)
                break  # Move to the next base keyword
    return filtered_base_keywords


# Create operation - Add dish to menu
@app.route('/add', methods=['POST'])
def add_dish():
    try:
        data = request.get_json()
        dish_name = data.get('dish_name')
        description = data.get('description')
        ingredients = data.get('ingredients')
        price = data.get('price')
        avg_time_taken = data.get('avg_time_taken')
        disease_list = data.get('disease_list')
        recipe_description = data.get('recipe_description')
        calories = data.get('calories')
        
        conn = sqlite3.connect('nutri.db')
        c = conn.cursor()
        c.execute("INSERT INTO menu (dish_name, description, ingredients, price, avg_time_taken, disease_list, recipe_description, calories) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                  (dish_name, description, ingredients, price, avg_time_taken, disease_list, recipe_description, calories))
        conn.commit()
        menu_number = c.lastrowid
        conn.close()
        return jsonify({'menu_number': menu_number, 'dish_name': dish_name}), 201
    except Exception as e:
        return jsonify(error=str(e)), 500

# Read operation - Display all dishes on menu
@app.route('/')
def get_menu():
    
    def get_image(item):
        print("inside")
        response = requests.get(f'https://api.edamam.com/search?app_id=900da95e&app_key=40698503668e0bb3897581f4766d77f9&q={item}', timeout=5)
        response.raise_for_status()
        response = response.json()
        if response['hits']:
            return response['hits'][0]['recipe']['image']
        
        return "https://www.clipartmax.com/png/middle/109-1094645_we-will-now-be-serving-supper-bowl-of-soup-animated.png"
        
    try:
        conn = sqlite3.connect('nutri.db')
        c = conn.cursor()
        c.execute("SELECT * FROM menu WHERE deleted_at IS NULL")
        print("line 111")
        # print(c.fetchall())
        # print(type(c.fetchall()))
        # for r in c.fetchall():
        #     print(r)
        #     print(r[1])
        menu = [{'menu_number': row[0], 'dish_name': row[1], 'description': row[2],
                 'ingredients': row[3], 'price': row[4], 'avg_time_taken': row[5],
                 'disease_list': row[6], 'recipe_description': row[7],
                 'calories': row[8], 'created_date': row[9], 'updated_at': row[10], 'deleted_at': row[11], 'image': get_image(row[3])} for row in c.fetchall()]
        conn.close()
        
        print(menu)
        menu_res = {}
        
        menu_res['menu'] = menu
        
        return jsonify(menu_res)
    except Exception as e:
        return jsonify(error=str(e)), 500

# Update operation - Edit dish on menu
@app.route('/edit/<int:menu_number>', methods=['PUT'])
def edit_dish(menu_number):
    try:
        data = request.get_json()
        dish_name = data.get('dish_name')
        description = data.get('description')
        ingredients = data.get('ingredients')
        price = data.get('price')
        avg_time_taken = data.get('avg_time_taken')
        disease_list = data.get('disease_list')
        recipe_description = data.get('recipe_description')
        calories = data.get('calories')
        
        conn = sqlite3.connect('nutri.db')
        c = conn.cursor()
        c.execute("UPDATE menu SET dish_name=?, description=?, ingredients=?, price=?, avg_time_taken=?, disease_list=?, recipe_description=?, calories=?, updated_at=? WHERE menu_number=?", 
                  (dish_name, description, ingredients, price, avg_time_taken, disease_list, recipe_description, calories, datetime.now(), menu_number))
        conn.commit()
        conn.close()
        return jsonify({'menu_number': menu_number, 'dish_name': dish_name}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

# Delete operation - Remove dish from menu
@app.route('/delete/<int:menu_number>', methods=['DELETE'])
def delete_dish(menu_number):
    try:
        conn = sqlite3.connect('nutri.db')
        c = conn.cursor()
        c.execute("UPDATE menu SET deleted_at=? WHERE menu_number=?", (datetime.now(), menu_number))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Dish deleted successfully'}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

     
@app.route('/recipes', methods=['POST'])
def get_recipes():
    data = request.get_json()
    if 'keywords' not in data or not isinstance(data['keywords'], list):
        return jsonify({'error': 'Invalid input. Please provide a list of keywords.'}), 400
    
    recipes = []
    for keyword in data['keywords']:
        try:
            response = requests.get(f'https://api.edamam.com/search?app_id=900da95e&app_key=40698503668e0bb3897581f4766d77f9&q={keyword}', timeout=5)
            response.raise_for_status()
            response = response.json()
            
            for i in range(5):
                temp ={}
                temp['lable'] = response['hits'][i]['recipe']['label']
                temp['image'] = response['hits'][i]['recipe']['image']
                temp['ingredients'] = response['hits'][i]['recipe']['ingredientLines']
                temp['totalNutrients'] = response['hits'][i]['recipe']['totalNutrients']
                temp['calories'] = response['hits'][i]['recipe']['calories']
                temp['url'] = response['hits'][i]['recipe']['url']
                temp['price'] = int(random.randint(3, 30))
                
                recipes.append(temp)
        
        except requests.exceptions.RequestException as e:
            recipes.append({'error': f'Failed to fetch recipes for keyword: {keyword}. {e}'})
        except ValueError:
            recipes.append({'error': f'Invalid JSON response for keyword: {keyword}'})
         
    try:
        keywords = data['keywords']

        conn = sqlite3.connect('nutri.db')
        c = conn.cursor()
        # Constructing the WHERE clause dynamically to search for any match with keywords
        where_clause = ' OR '.join(f'{column} LIKE ?' for column in ['dish_name', 'description', 'ingredients', 'recipe_description'])
        query = f"SELECT * FROM menu WHERE ({where_clause}) AND deleted_at IS NULL"
        
        db_matches =[]
        for k in keywords:
            
            # Constructing the values for bindings
            bindings = ['%' + k + '%' for _ in range(4)]
            c.execute(query, bindings)
            db_matches.append(c.fetchall())

        # Executing the query with keyword matching
        c.execute(query, bindings)
        
        print( c.fetchall())

        combined_list = [item for sublist in db_matches for item in sublist]

        for row in combined_list:
            response = requests.get(f'https://api.edamam.com/search?app_id=900da95e&app_key=40698503668e0bb3897581f4766d77f9&q={row[3]}', timeout=5)
            response.raise_for_status()
            response = response.json()
            price_int = int(row[4])
            print("proce int", price_int )
            dish = {
                'label': row[1],
                'ingredients': row[3],
                'price': price_int,
                'recipe_description': row[7],
                'calories': row[8],
                'totalNutrients': row[8],
                'image': response['hits'][0]['recipe']['image'],
            }
            recipes.append(dish)

        conn.close()   
    except requests.exceptions.RequestException as e:
        recipes.append({'error': f'Failed to fetch recipes for keyword: {keyword}. {e}'})
    except ValueError:
        recipes.append({'error': f'Invalid JSON response for keyword: {keyword}'})

    print(len(recipes))
    
    r_obj = {}
    
    r_obj['dishes'] = recipes 
    
    return jsonify(r_obj)     


@app.route("/audio_dishes", methods=["POST"])
def audio_dishes():
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            text = data["text"]
        except KeyError:
            return jsonify({"error": "Invalid request format. Make sure to provide 'text' in the request payload."}), 400

        txt_len = len(text.split())
        first_recipes = []
        if txt_len < 5:
            response = requests.get(f'https://api.edamam.com/search?app_id=900da95e&app_key=40698503668e0bb3897581f4766d77f9&q={text}', timeout=5)
            response.raise_for_status()
            response = response.json()
            
            for i in range(8):
                temp ={}
                temp['lable'] = response['hits'][i]['recipe']['label']
                temp['image'] = response['hits'][i]['recipe']['image']
                temp['ingredients'] = response['hits'][i]['recipe']['ingredientLines']
                temp['totalNutrients'] = response['hits'][i]['recipe']['totalNutrients']
                temp['calories'] = response['hits'][i]['recipe']['calories']
                temp['url'] = response['hits'][i]['recipe']['url']
                temp['price'] = random.randint(3, 30)
                
                first_recipes.append(temp)
                
            recipes_res ={}
            
            recipes_res['dishes'] =first_recipes
                
            return jsonify(recipes_res) 

        response = client.analyze(text)
        generated_keywords = [entity.id.lower() for entity in response.entities()]

        filtered_generated_keywords = filter_generated_keywords(generated_keywords)
        filtered_base_keywords = filter_base_keywords(filtered_generated_keywords)

        print(filtered_base_keywords)
        
        filtered_base_keywords = list(set(filtered_base_keywords))
        
        recipes = []
        for keyword in filtered_base_keywords:
            try:
                response = requests.get(f'https://api.edamam.com/search?app_id=900da95e&app_key=40698503668e0bb3897581f4766d77f9&q={keyword}', timeout=5)
                response.raise_for_status()
                response = response.json()
                
                for i in range(5):
                    temp ={}
                    temp['lable'] = response['hits'][i]['recipe']['label']
                    temp['image'] = response['hits'][i]['recipe']['image']
                    temp['ingredients'] = response['hits'][i]['recipe']['ingredientLines']
                    temp['totalNutrients'] = response['hits'][i]['recipe']['totalNutrients']
                    temp['calories'] = response['hits'][i]['recipe']['calories']
                    temp['url'] = response['hits'][i]['recipe']['url']
                    temp['price'] = random.randint(3, 30)
                    
                    recipes.append(temp)
            
            except requests.exceptions.RequestException as e:
                recipes.append({'error': f'Failed to fetch recipes for keyword: {keyword}. {e}'})
            except ValueError:
                recipes.append({'error': f'Invalid JSON response for keyword: {keyword}'})
                
        try:
            keywords = filtered_base_keywords

            conn = sqlite3.connect('nutri.db')
            c = conn.cursor()
            # Constructing the WHERE clause dynamically to search for any match with keywords
            where_clause = ' OR '.join(f'{column} LIKE ?' for column in ['dish_name', 'description', 'ingredients', 'recipe_description'])
            query = f"SELECT * FROM menu WHERE ({where_clause}) AND deleted_at IS NULL"
            
            db_matches =[]
            for k in keywords:
                
                # Constructing the values for bindings
                bindings = ['%' + k + '%' for _ in range(4)]
                c.execute(query, bindings)
                db_matches.append(c.fetchall())

            # Executing the query with keyword matching
            c.execute(query, bindings)
            
            print( c.fetchall())

            combined_list = [item for sublist in db_matches for item in sublist]

            for row in combined_list:
                response = requests.get(f'https://api.edamam.com/search?app_id=900da95e&app_key=40698503668e0bb3897581f4766d77f9&q={row[3]}', timeout=5)
                response.raise_for_status()
                response = response.json()
                
                dish = {
                    'label': row[1],
                    'ingredients': row[3],
                    'price': row[4],
                    'recipe_description': row[7],
                    'calories': row[8],
                    'totalNutrients': row[8],
                    'image': response['hits'][0]['recipe']['image'],
                }
                recipes.append(dish)

            conn.close()   
        except requests.exceptions.RequestException as e:
            recipes.append({'error': f'Failed to fetch recipes for keyword: {keyword}. {e}'})
        except ValueError:
            recipes.append({'error': f'Invalid JSON response for keyword: {keyword}'})

        recipes_res ={}
        
        recipes_res['dishes'] =recipes
            
        return jsonify(recipes_res)     

@app.route("/keywords_from_audio", methods=["POST"])
def keywords_from_audio():
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            text = data["text"]
        except KeyError:
            return jsonify({"error": "Invalid request format. Make sure to provide 'text' in the request payload."}), 400

        if len(text.split()) < 5:
            filtered_generated_keywords = filter_generated_keywords(text.split())
            filtered_base_keywords = filter_base_keywords(filtered_generated_keywords)
            return jsonify({"keywords": filtered_base_keywords})
        response = client.analyze(text)
        generated_keywords = [entity.id.lower() for entity in response.entities()]

        filtered_generated_keywords = filter_generated_keywords(generated_keywords)
        filtered_base_keywords = filter_base_keywords(filtered_generated_keywords)

        print(filtered_base_keywords)
        
        result = list(set(filtered_base_keywords))
        
        return jsonify({"keywords": result})
    
    
# Place an order
@app.route('/place_order', methods=['POST'])
def place_order():
    try:
        data = request.json
        dishes = data.get('dishes', [])
        conn = sqlite3.connect('nutri.db')
        c = conn.cursor()
        c.execute("INSERT INTO orders (total_bill, customer_name, preferences) VALUES (?, ?, ?)",
                  (data['total_bill'], data['customer_name'], data.get('preferences', '')))
        order_id = c.lastrowid
        for dish in dishes:
            c.execute("INSERT INTO order_items (order_id, dish_name, quantity, imagelink, price) VALUES (?, ?, ?, ?, ?)",
                      (order_id, dish['dish_name'], dish['quantity'], dish['imagelink'], dish['price']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Order placed successfully'}), 201
    except Exception as e:
        return jsonify(error=str(e)), 500

# Get all orders
@app.route('/get_orders', methods=['GET'])
def get_orders():
    try:
        conn = sqlite3.connect('nutri.db')
        c = conn.cursor()
        c.execute("SELECT * FROM orders WHERE deleted_at IS NULL")
        orders = [{'order_id': row[0], 'total_bill': row[1], 'customer_name': row[2], 'preferences': row[3],
                   'created_date': row[4], 'updated_at': row[5], 'deleted_at': row[6]} for row in c.fetchall()]
        for order in orders:
            c.execute("SELECT * FROM order_items WHERE order_id=?", (order['order_id'],))
            items = [{'dish_name': row[2], 'quantity': row[3], 'imagelink': row[4], 'price': row[5]} for row in c.fetchall()]
            order['dishes'] = items
        conn.close()
        orders_json ={}
        orders_json['orders'] = orders 
        return jsonify(orders_json)
    except Exception as e:
        return jsonify(error=str(e)), 500

# Update an order
@app.route('/update_order/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    try:
        data = request.json
        conn = sqlite3.connect('nutri.db')
        c = conn.cursor()
        c.execute("UPDATE orders SET total_bill=?, customer_name=?, preferences=?, updated_at=? WHERE order_id=?", 
                  (data['total_bill'], data['customer_name'], data.get('preferences', ''), datetime.now(), order_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Order updated successfully'}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

# Delete an order
@app.route('/delete_order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    try:
        conn = sqlite3.connect('nutri.db')
        c = conn.cursor()
        c.execute("UPDATE orders SET deleted_at=? WHERE order_id=?", (datetime.now(), order_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Order deleted successfully'}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == '__main__':
    app.run(debug=True)
