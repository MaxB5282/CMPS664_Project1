
import pandas as pd
import mysql.connector
import itertools

# Step 1: CSV Data Import
def import_csv(file_path):
    df = pd.read_csv(file_path)
    print(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}\n")
    print("Sample Records:\n", df.head(), "\n")
    print("Data Types:\n", df.dtypes, "\n")
    return df

# Step 2: Functional Dependency Identification
def compute_closure(attributes, fds):
    closure = set(attributes)
    changed = True
    while changed:
        changed = False
        for lhs, rhs in fds.items():
            if set(lhs).issubset(closure) and not set(rhs).issubset(closure):
                closure.update(rhs)
                changed = True
    return closure

def suggest_candidate_keys(attributes, fds):
    candidate_keys = []
    for i in range(1, len(attributes) + 1):
        for subset in itertools.combinations(attributes, i):
            closure = compute_closure(subset, fds)
            if set(attributes).issubset(closure):
                is_minimal = True
                for key in candidate_keys:
                    if set(key).issubset(subset):
                        is_minimal = False
                        break
                if is_minimal:
                    candidate_keys.append(subset)
    return candidate_keys

def identify_dependencies(attributes, fds, primary_key):
    print("Primary Key:", primary_key)
    candidate_keys = suggest_candidate_keys(attributes, fds)
    print("Possible Candidate Keys:")
    for key in candidate_keys:
        print("-", key)
    closures = {attr: compute_closure([attr], fds) for attr in attributes}
    partial, transitive = [], []
    for lhs, rhs in fds.items():
        if set(lhs).issubset(primary_key) and not set(lhs) == set(primary_key):
            partial.append((lhs, rhs))
        elif not set(lhs).issubset(primary_key):
            transitive.append((lhs, rhs))
    return partial, transitive

# Step 3: Normalization Process
def normalize(attributes, fds, primary_key):
    partial, transitive = identify_dependencies(attributes, fds, primary_key)
    tables = []

    if partial:
        for lhs, rhs in partial:
            tables.append(set(list(lhs) + list(rhs)))
    if transitive:
        for lhs, rhs in transitive:
            tables.append(set(list(lhs) + list(rhs)))

    main_table = set(attributes) - set(itertools.chain(*[rhs for _, rhs in partial + transitive]))
    tables.append(main_table)

    print("Tables after normalization:")
    normalized_tables = []
    for i, table in enumerate(tables, start=1):
        print(f"Table_{i}:", table)
        normalized_tables.append((f"Table_{i}", sorted(list(table))))
    return normalized_tables

# Step 4: SQL Script Generation
def generate_sql(tables):
    script = ""
    for table_name, columns in tables:
        script += f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        for col in columns:
            script += f"    {col} TEXT,\n"
        script = script.rstrip(",\n") + "\n);\n\n"
    return script

# Step 5: Database Creation and Query Interface
def create_database(db_name, script, df, tables):
    mydb = mysql.connector.connect(host='localhost', user='root', passwd='Bily3524$!', database='project1')
    mycursor = mydb.cursor()

    for table_name, attributes in tables:
        if attributes:
            sql_command = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
            for attr in attributes:
                sql_command += f"    {attr} VARCHAR(255),\n"
            sql_command = sql_command.rstrip(",\n") + "\n);"
            mycursor.execute(sql_command)

            df_subset = df[attributes]
            for _, row in df_subset.iterrows():
                cols = ", ".join(attributes)
                vals = ", ".join([f"'{str(val)}'" for val in row])
                insert_sql = f"INSERT INTO {table_name} ({cols}) VALUES ({vals});"
                mycursor.execute(insert_sql)

    mydb.commit()
    mydb.close()

# Also step 5: providing interface to run any additional queries
def run_queries(query):
    mydb = mysql.connector.connect(host='localhost', user='root', passwd='Bily3524$!', database='project1')
    mycursor = mydb.cursor()
    mycursor.execute(query)

    mydb.commit()
    mydb.close()

# Interactive function
def main():
    csv_path = input("Enter CSV file name in same directory as this tool: ")
    df = import_csv(csv_path)

    attributes = list(df.columns)
    print("Attributes found:", attributes)

    fds_input = input("Enter FDs (format: A->B,C->D): ")
    fds = {}
    for fd in fds_input.split(","):
        lhs, rhs = fd.split("->")
        fds[tuple(lhs.strip().split())] = rhs.strip().split()

    primary_key = input("Enter primary key (comma-separated): ").split(",")

    normalized_tables = normalize(attributes, fds, primary_key)

    sql_script = generate_sql(normalized_tables)
    print("\nSQL Script:\n", sql_script)

    db_name = input("Enter Database Name (e.g., 'database.db'): ")
    create_database(db_name, sql_script, df, normalized_tables)

    action = input("Would you like to run any additional queries? (y/n):")
    if action == 'y':
        get_query = input("Please enter your SQL query here:")
        run_queries(get_query)
        print("Database created and populated successfully!")
    else:
        print("Database created and populated successfully!")

if __name__ == '__main__':
    main()
