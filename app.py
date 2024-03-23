import random
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

import requests

app = Flask(__name__)

# Function to create the menu table
def create_menu_table():
    conn = sqlite3.connect('nutri.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS menu
                 (menu_number INTEGER PRIMARY KEY, dish_name TEXT, description TEXT, 
                 ingredients TEXT, price REAL, avg_time_taken INTEGER, disease_list TEXT, 
                 recipe_description TEXT, calories INTEGER, created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                 updated_at TEXT DEFAULT NULL, deleted_at TEXT DEFAULT NULL)''')
    conn.commit()
    conn.close()

create_menu_table()

# Error handling decorator
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify(error=str(e)), 500

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
    try:
        conn = sqlite3.connect('nutri.db')
        c = conn.cursor()
        c.execute("SELECT * FROM menu WHERE deleted_at IS NULL")
        menu = [{'menu_number': row[0], 'dish_name': row[1], 'description': row[2],
                 'ingredients': row[3], 'price': row[4], 'avg_time_taken': row[5],
                 'disease_list': row[6], 'recipe_description': row[7],
                 'calories': row[8], 'created_date': row[9], 'updated_at': row[10], 'deleted_at': row[11]} for row in c.fetchall()]
        conn.close()
        return jsonify(menu)
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
                temp['price'] = random.randint(3, 30)
                
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

    print(len(recipes))
    return jsonify(recipes)     


if __name__ == '__main__':
    app.run(debug=True)
