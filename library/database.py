import MySQLdb
import os
import read_csv

'''
This is a private function that automatically updates the csv files
for the database tables necessary to do the rest of the calculates

tables: all_data_better", "bed_types_gobig","bed_types_gosmall", "listing_types", "listings_accomodation
'''
class database():

	def __init__(self, database_name):
		self.database_name = database_name
		self.host = "localhost"
		self.user = "root"
		self.passwd = "castrated1432"
		self.directory = "~/Thesis/"

		#database_types
		self.text = "TEXT"
		self.string = "VARCHAR (100)"
		self.integer = "INT"
		self.floating = "DECIMAL (10,4)"
		self.enum = "ENUM "

		self.db = MySQLdb.connect(host= self.host, user = self.user, passwd = self.passwd, db = self.database_name)
		self.cursor = self.db.cursor() #does execution statements

		self._test_connection()


	#### THIS BEGINS SMALL TASKS FOR THE DATABASE OBJECT ######

	'''
	This tests the connection parts of this class
	'''
	def _test_connection(self):
		#connect to database
		test = "SHOW TABLES FROM `Thesis`";

		try:
			self.cursor.execute(test)
			print "Success! We have connected to %s" % self.database_name
		except Exception as e:
			print "We have a problem"
			print e.message


	'''
	returns true if table exists, false if table doesn't
	'''
	def _find_table(self, table_name):
		query = "SELECT * FROM " + table_name
		try:
			self.db.execute()
			return True
		except Exception as e:
			return False


	def clear_table(self, table_name):
		query = "TRUNCATE TABLE %s" % table_name
		self.cursor.execute(query)
		self.db.commit()
		print "Truncated table %s" , (table_name)

	def add_entry_to_table(self, table_name, data_list):
		#make the %s string
		mini_s_string = "("
		for n in range(0, len(data_list)):
			mini_s_string += "%s, "

		mini_s_string = mini_s_string[:len(mini_s_string)-1] + ");"

		#make query string
		query = ("INSERT INTO " + table_name + " VALUES " + mini_s_string) % tuple(data_list)
		print query
		self.cursor.execute(query)
		self.db.commit()

	def save_to_table(self, table_name, list_of_list):
		for entry in list_of_list:
			add_entry_to_table(table_name, data_list)

	####HERE ARE BIG METHODS FOR THE DATABASE OBJECT #####
	def check_table(self, database_name, csv_file):
		if _find_table:
			print "cool this database %s already exists" % database_name
		else:
			print "Seems like database %s doens't exist.  LEt's make it" % database_name

			#get the datatypes
			read_csv.csv_to_array(csv_file)
			self.cursor.execute()

	'''
	If given a csv, this updates csv files in the data folder of the table specified.
	'''
	def update_table_csv(self, tables_to_update):
		os.chdir(directory + "data")
		print "this is the working directory ", os.getcwd()
		query_text = "SELECT * FROM `Thesis Data`."
		output_folder = "database_tables/"
		for table in tables_to_update:
			output_file = output_folder + table + ".csv"
			query = query_text + table
			self.cursor.execute(query)
			final = list(self.cursor.fetchall())
			try:
				read_csv.print_to_csv(output_file, final)
			except IOError:
				print "we have a problem.  cannot find"
				print (os.getcwd() + "/" + output_file)
		print "Okay, base tables have been updated"




	'''
	updates the first tables to their csv.
	takes in the database object
	'''

	def update_to_start(self):
		tables_to_update = ["all_data_better", "bed_types_gobig","bed_types_gosmall", "listing_types", "listings_accomodation"]
		update_table_csv(tables_to_update)

	'''
	This method takes in a database object, performs a query and updates
	the query results to the inputed file name

	input: query_file: query file document name or location
		output_file: output_file name or location
		db: the database connection object
	'''
	def query_search_to_print(self, query_file, output_file):
		os.chdir("../mysql_scripts") #put it in the thesis folder *note to self
		query_text = ""
		with open(query_file, 'r') as f:
			query_text = f.read().replace('\n', ' ')

		self.db.execute(query_text)
		final = list(db.fetchall())
		#print
		read_csv.print_to_csv(output_file, final)

	'''
	This method takes in a database object, performs a query and updates
	the query results to the inputed file name

	input: query_file: query file document name or location
		cursor: the database cursor

	output: a list with the query results
	'''
	def get_data_from_query_search(self, query_file):
		os.chdir("/Users/ameewongstein/Thesis/mysql_scripts")
		query_text = ""
		with open(query_file, 'r') as f:
			query_text = f.read().replace('\n', ' ')

		self.cursor.execute(query_text)
		final = list(cursor.fetchall())

		return final

	'''
	This method truncates a table, and updates it based on a csv file
	input :
	csv_file: the name of the csv where we need to update
	table_name: the name of the table to be updated
	db: the connection database
	'''
	def update_table(self, csv_file, table_name):
		#os.chdir("/Users/ameewongstein/data")
		truncate = "TRUNCATE `Thesis`." + table_name
		self.cursor.execute(truncate)

		file_location = "/Users/ameewongstein/data/" + csv_file
		import_csv = "LOAD DATA LOCAL INFILE '%s' INTO TABLE " % file_location
		import_csv += "`Thesis Data`."
		import_csv += table_name
		import_csv += " FIELDS TERMINATED BY ',' ENCLOSED BY '' LINES TERMINATED BY '\n'"
		self.cursor.execute(import_csv)
		self.db.commit()


	'''
	Checks to see if a database table exist.  takes in the column dictionary too
	'''
	def check_table(self, table_name, column_dict):
		try:
			query = "SELECT * FROM `%s`" % table_name
			self.cursor.execute(query)
		except Exception as e: #it doesn't exist, so make it
			_create_table(table_name, column_dict)

	'''
	internal method to create a table with specifid column /type dicitionary
	column dict should be like this: "name":"type"
	'''
	def _create_table(self, table_name, column_dict):
		print "hello"
		try:
			#get
			self.cursor.execute("CREATE TABLE ")
		except Exception as e:
			print "can't do anything FIX ME!"

	def destroy_connection(self):
		self.db.close()
		self.cursor.close()

	def execute(self, query_string):
		self.cursor.execute(query_string)
		self.db.commit()

	def get_data(self, query_string):
		self.cursor.execute(query_string)
		return list(self.cursor.fetchall())





