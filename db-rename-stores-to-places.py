#!/usr/bin/env python3

#
# A script to migrate the database from "stores" to "places"
#
# We use the fancy postgres tables to find things like sequence names, etc...
#
# Without any args it will print out the queries it would run.
# Pass --execute to actually run it.
#

import sys
from django.db import connection


def fetchall(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    return rows


queries = [
    "update django_content_type set app_label = 'places' where app_label = 'stores'",
    "update django_content_type set model = 'place' where model = 'store'",
    "update django_migrations set app = 'places' where app = 'stores'",
    "update django_migrations set name = replace(name, 'store', 'place')"
]

# foreign key columns

for table_name, column_name in fetchall(
        "select table_name, column_name from information_schema.columns where column_name = 'store_id'"):
    queries.append("alter table {} rename column store_id to place_id".format(table_name))

# constraints

for table_name, constraint_name in fetchall("""
        select table_name, constraint_name
        from information_schema.table_constraints
        where constraint_name like '%store%'
        """):
    queries.append(
        "alter table {} rename constraint {} to {}".format(
            table_name, constraint_name, constraint_name.replace('store', 'place')
        )
    )

# indexes

for indexname, in fetchall("select indexname from pg_indexes where schemaname = 'public' and indexname like '%store%'"
                           ):
    queries.append("alter index if exists {} rename to {}".format(indexname, indexname.replace('store', 'place')))

# sequences

for relname, in fetchall("select relname from pg_class where relkind = 'S' and relname like '%store%'"):
    queries.append("alter sequence if exists {} rename to {}".format(relname, relname.replace('store', 'place')))

queries.append("alter table if exists stores_store rename to places_place")

if '--execute' in sys.argv[1:]:
    with connection.cursor() as cursor:
        for query in queries:
            cursor.execute(query)
    print('done')
else:
    for query in queries:
        print(query + ';')
