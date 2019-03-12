import psycopg2
import testing.postgresql

db = None
db_con = None


def prepare_db(sql='setup.sql'):
    """ Module level set-up called once before any tests in this file are executed. Creates a temporary database
    and sets it up """

    global db, db_con

    db = testing.postgresql.Postgresql()
    # Get a map of connection parameters for the database which can be passed
    # to the functions being tested so that they connect to the correct
    # database
    db_conf = db.dsn()
    # Create a connection which can be used by our test functions to set and
    # query the state of the database
    db_con = psycopg2.connect(**db_conf)
    # Commit changes immediately to the database
    db_con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    # Create the initial database structure (roles, schemas, tables etc.)
    # basically anything that doesn't change
    apply_sql_file(sql)

    return db_conf


def apply_sql_file(sql_path):
    global db_con

    with open(sql_path, 'r') as fh:
        lines_str = fh.read()

    with db_con.cursor() as cur:
        cur.execute(lines_str)


def apply_sql_clause(sql_clause):
    global db_con

    with db_con.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(sql_clause)
        rows = cur.fetchall()

    return rows


def close_db():
    db_con.close()
    db.stop()
