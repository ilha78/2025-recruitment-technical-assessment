from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
# Map the name of entry to its data (either a Recipe or an Ingredient)
cookbook = {}

# We are under the assumption that recipe dependencies cannot be moditfied
# upon creation. Hence, cache the time taken and freq for each recipe to avoid
# repetitive computation
# name to tuple {ingredient freq}
recipe_ingredient_cache = {}

# Task 1 helper (don't touch)
@app.route('/parse', methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipe_name and returns it in a form that 
def parse_handwriting(recipe_name: str) -> Union[str | None]:
	original_names = re.split(r'[- _]+', recipe_name)

	# error case
	if len(original_names) == 0 or original_names[0] == '':
		return None

	updated_names = []
	for name in original_names:
		new_name = re.sub(r'[^a-zA-Z_-]', '', name)
		new_name = new_name[0].upper() + new_name[1:].lower()
		updated_names.append(new_name)
	
	return ' '.join(updated_names)


# [TASK 2] ====================================================================
# This helper function creates a recipe
def create_receipe(data, name):
	item_names = set()
	required_items = []
	for item in data.get('requiredItems'):
		# check that the item name is not repeated
		item_name = item.get('name')
		if item_name in item_names:
			return 'can only have one element per name', 400 
		item_names.add(item_name)

		# check that quantity is valid
		item_quantity = item.get('quantity')
		if item_quantity < 0:
			return 'invalid quantity', 400
		
		required_items.append(
			RequiredItem(name=item_name, quantity=item_quantity)
		)
	recipe = Recipe(name=item_name, required_items=required_items)
	cookbook[name] = recipe

	return 'recipe added', 200

# This helper function creates an ingredient
def create_ingredient(data, name):
	# invalid cook time
	cook_time = data.get('cookTime')
	if cook_time < 0:
		return 'invalid cook time', 400
	
	ingredient = Ingredient(name=name, cook_time=cook_time)
	cookbook[name] = ingredient

	return 'ingredient added', 200

# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()
	entry_type = data.get('type')
	name = data.get('name')

	if name in cookbook:
		return 'name of the entry must be unique', 400

	# recipe case
	if entry_type == 'recipe':
		return create_receipe(data, name)

	# ingredient case
	elif entry_type == 'ingredient':
		return create_ingredient(data, name)

	# type does not match
	else:
		return 'invalid type', 400


# [TASK 3] ====================================================================
# This helper function recursively computes the summary requied
# Note that ingredients are leaf nodes and we can cache the queries to each 
# node since different recipes may depend on the same recipe and/or ingredient
# We should also consider a case where recipes have circular dependencies via 
# directed cycle check. Note that the name must be a type Recipe
# each call returns {ingredient freq}
# O(|recipes|*|ingredients|) since we must repeatedly visit ingredients for 
# uncached recipes since the quantites of which the ingredients are required 
# may be different across different recipes
def recursive_summary(name):
	# check that recipe exists in cookbook

	if name in recipe_ingredient_cache:
		return recipe_ingredient_cache[name]
	
	# parent recipe's ingredient freq table
	ingredient_freq = {"this": "ddff"}
	# dfs neighbour search
	for item in cookbook[name].required_items:
		if isinstance(cookbook[item.name], Ingredient):
			# check that ingredient exists in cookbook

			ingredient_freq[item.name] = item.quantity
		else:
			child_recipe = recursive_summary(item.name)
			# aggregate the child recipe's freq to the parent receipe's freq
			for k, v in child_recipe:
				if k in ingredient_freq:
					ingredient_freq[k] += item.quantity * v
				else:
					ingredient_freq[k] = item.quantity * v
		
	return ingredient_freq
	

# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	query = request.args
	name = query.get('name')
	if not name in cookbook:
		return 'name not found in cook book', 400
	elif not isinstance(cookbook[name], Recipe):
		return 'type is not a recipe', 400
	
	ingredient_freq = recursive_summary(name)
	# required_items = [{"name": k, "quantity": v} for k, v in ingredient_freq.items()]
	# cook_time = 0
	# for k, v in ingredient_freq.items():
	# 	cook_time += cookbook[k].cook_time * v

	# summary = { "name": name, "cookTime": cook_time, "ingredients": required_items }
	
	return "fff", 200

@app.route('/clear', methods=['POST'])
def clear():
	cookbook .clear()
	return 'clear cookbook success', 200

# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
