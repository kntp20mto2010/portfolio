import pymysql
import re
import datetime
import send_to_slack
import itertools

__databases = {}
database_column_status = {}
host = "118.27.22.246"


def connectDatabase(database_name):
    if database_name in __databases:
        return __databases[database_name]

    connect = connectToMysql(database_name)
    # 自動コミットにする場合は下記を指定（コメントアウトを解除のこと）
    # connect.isolation_level = None
    cursor = connect.cursor()

    b = True if "cash" in database_name else isExistsTable(cursor, database_name, "main")
    if b:
        query = "show tables" if "cash" in database_name else "SELECT COUNT(*) FROM main"
        all_count = selectCount(cursor=cursor, query=query)

        query = (
            "show tables"
            if "cash" in database_name
            else "SELECT COUNT(*) FROM main WHERE ERROR is NULL"
        )
        non_error_count = (
            selectCount(cursor=cursor, query=query) if database_name != "ship" else -1
        )

        send_to_slack.post(
            f"データベース名={database_name},全データ数={all_count},正常データ数={non_error_count},エラー数={all_count-non_error_count}"
        )

    __databases[database_name] = connect
    return connect


def createTableIfNotExists(cursor, database_name, table_name):
    count = selectCount(
        cursor=cursor,
        query=f"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{database_name}' AND TABLE_NAME = '{table_name}';",
    )
    if count == 0:
        # テーブル名が数字のみの場合は
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {getTableName(table_name)}(id INTEGER PRIMARY KEY AUTO_INCREMENT)"
        )
        # mysqlでは型指定が必要になるが､Noneでは型指定ができないため
        # データを保存する際のカラムチェックのときに存在しないカラムを追加することにした
        print(f"table={table_name}を作成しました")


def selectCount(database_name="amazon", cursor=None, query="", is_translate=False):
    # query = re.sub(r"FROM \'(\w*?)\'", r"FROM \1", query)
    match = re.search(r"FROM \'(\w*?)\'", query)
    if match:
        if match.group().isdecimal():
            # query = re.sub(r"FROM \'(\w*?)\'", r"FROM \1", query)
            pass
        else:
            query = re.sub(r"FROM \'(\w*?)\'", r"FROM \1", query)
    if cursor is None:
        cursor = connectDatabase(database_name).cursor()
    if is_translate:
        query = query.replace("*", "COUNT(*)")
    try:
        cursor.execute(query)
    except pymysql.Error as e:
        if "Unknown column" in e.args[1]:
            return 0

        send_to_slack.post(f"pymysql.Error occurred:{e.args[1]}")
    except Exception as e:
        print("Unknown column")
    result = cursor.fetchone()
    if query == "show tables":
        return len(result) if result else 0
    else:
        number_of_rows = result["COUNT(*)"]
        return number_of_rows


def save(database_name, table_name, data):
    try:
        createDatabaseIfNotExists(database_name)
        connect = connectDatabase(database_name)
        # connect = __main
        cursor = connect.cursor()
        # メイン
        createTableIfNotExists(cursor, database_name, table_name)
        isExistsAllColumns(database_name=database_name, table_name=table_name, data=data)

        if "ship" in database_name:
            if data.receipt_id:
                unique_data = data.receipt_id
                unique_column_name = "receipt_id"
            else:
                unique_data = data.order_id
                unique_column_name = "order_id"
        elif "cash" in database_name:
            unique_data = data.CROLLED_TIME
            unique_column_name = "CROLLED_TIME"
        elif "croller" in database_name:
            unique_data = data.croller_name
            unique_column_name = "croller_name"
        elif "yahoo_auction" in database_name:
            unique_data = data.PRODUCT_ID
            unique_column_name = "PRODUCT_ID"
        elif "log" in database_name:
            unique_data = data.TIME_STAMP
            unique_column_name = "TIME_STAMP"
        else:
            unique_data = data.PRODUCT_ID
            unique_column_name = "PRODUCT_ID"

        is_registerd = isRegisterd(
            database_name,
            table_name=table_name,
            unique_column_name=unique_column_name,
            value=unique_data,
        )

        if is_registerd:
            update(connect, table_name, data, unique_column_name, unique_data)
        else:
            insert(connect, table_name, data)

        # 更新処理かつクロール時間がある=定期的にクロールされているASINであるため､保存する
        if database_name == "new" and data.CROLLED_TIME:
            saveEachASINTable(data)

        # for row in cursor.execute(
        #     f"SELECT * FROM '{table_name}' WHERE {unique_column_name} = '{data.PRODUCT_ID}'"
        # ):
        #     print(row)
    except pymysql.Error as e:
        send_to_slack.post("pymysql.Error occurred:{e.args[0]}")
    except Exception as e:
        pass


# main.newデータベースは作成と削除が繰り返されるため各ASINの情報をストックするcashデータベースを用意する｡
def saveEachASINTable(data):
    connect = connectDatabase("cash")
    cursor = connect.cursor()
    table_name = data.PRODUCT_ID
    createTableIfNotExists(cursor, database_name="cash", table_name=table_name)
    isExistsAllColumns(database_name="cash", table_name=table_name, data=data)
    insert(connect, table_name, data)


# この関数→csv2sqlite()がリカバリーとして早い
def recoveryFromCash():
    connect = connectDatabase("cash")
    cursor = connect.cursor()

    cursor.execute("select * from sqlite_master where type='table'")
    for elem in cursor.fetchall():
        table_name = elem["name"]
        if table_name == "sqlite_sequence":
            continue
        cursor.execute(f"SELECT COUNT(*) FROM {getTableName(table_name)}")
        row_num = cursor.fetchone()
        row_num = row_num["COUNT(*)"]
        if row_num == 0:
            continue
        cursor.execute(f"select * from {getTableName(table_name)} where rowid = {row_num}")
        dict_ = cursor.fetchone()
        if dict_ is not None:
            data = AMAZON_PRODUCT_DATA(dict_)
            b = isRegisterd(
                database_name="amazon", data=data.PRODUCT_ID, unique_column_name="ASIN"
            )
            if b is False:
                yield data
                # save(database_name="amazon", table_name="main", data=data, unique_column_name="ASIN")
            else:
                a = 1
                pass


def insert(connect, table_name, data):
    cursor = connect.cursor()
    # エラー処理（例外処理）
    try:
        if isinstance(data, type(YAHOO_ORDER_DATA)):
            keys, values = data.serialize()
        else:
            # ASIN,CATEGORY_NAME,CROLLED_TIME,SELF_RANKING_IN_NEW,RIVAL_NUM,RIVAL_MIN_PRICE,MY_DISPLAY_PRICE,TOP_SELLERS_PRICES'
            # "'B0813G2MYK','その他キッチン、日用品、文具',cast('2020-11-14 19:26:36.746383' as datetime),'','',12,46,2447,2534,'2484,2474,3152,2447'"
            keys, values = serialize(data)
            keys = ",".join(keys)
            values = ",".join(values)
        cursor.execute(
            f"INSERT INTO {getTableName(table_name)} ({keys}) VALUES ({values})",
        )

    except pymysql.Error as e:
        print("pymysql.Error occurred:", e.args[0])

    # 保存を実行（忘れると保存されないので注意）
    connect.commit()


# カラムを随時追加型にしたため､値がNoneのものはカラムが作られていない可能性があるためserializeしない
def serialize(data):
    keys = []
    values = []
    items = data.__dict__.items()
    for k, v in items:
        if v is None:
            # values.append("NULL")
            pass
        elif type(v) is str:
            if "'" in v:
                v = re.sub("'", "''", v)
            values.append(f"'{v}'")
        elif type(v) is bool:
            v = 1 if v else 0
            values.append(f"{v}")
        elif type(v) is datetime.datetime:
            values.append(f"cast('{v}' as datetime)")
        else:
            values.append(f"{v}")

        # ""を含まない
        if v is None:
            pass
        else:
            keys.append(k)

    return keys, values


def update(connect, table_name, data, unique_column_name, value):
    cursor = connect.cursor()
    # エラー処理（例外処理）
    try:
        query = ""
        for k, v in data.__dict__.items():
            if k == "ASIN":
                continue

            if type(v) is str:
                if "'" in v:
                    v = re.sub("'", "''", v)
            elif type(v) is bool:
                v = 1 if v else 0

            if v is None:
                pass
                # v = "NULL"
            elif type(v) is str or type(v) is datetime.datetime:
                v = f"'{v}'"
            else:
                v = f"{v}"

            if v is not None:
                query += f"{k} = {v}" if query == "" else f",{k} = {v}"

        cursor.execute(
            f"UPDATE {getTableName(table_name)} SET {query} WHERE {unique_column_name}='{value}';"
        )
        for row in cursor:
            print(row)

    except pymysql.Error as e:
        send_to_slack.post(f"pymysql.Error occurred:{e.args[0]}")
        print()

    # 保存を実行（忘れると保存されないので注意）
    connect.commit()


def getAllProducts(database_name, table_name="main"):
    # データベース接続
    con = connectDatabase(database_name)
    # カーソル生成
    cursor = con.cursor()
    if isExistsTable(cursor, database_name, table_name):
        result = cursor.execute(f"SELECT * FROM {getTableName(table_name)}")
        for row in cursor.fetchall():
            yield row
    else:
        yield from ()


def getProductsWhereColumns(database_name, columns):
    # データベース接続
    con = connectDatabase(database_name)

    # カーソル生成
    cursor = con.cursor()
    if isExistsTable(cursor, database_name, "main"):
        str_ = ",".join(columns)
        for row in cursor.execute(f"SELECT {str_} FROM main"):
            yield row
    else:
        yield from ()


def getProduct(database_name, table_name, unique_column_name, data):
    # データベース接続
    con = connectDatabase(database_name)
    cursor = con.cursor()

    if isExistsTable(cursor, database_name, table_name):
        # カーソル生成
        cursor.execute(
            f"SELECT * FROM {getTableName(table_name)} WHERE {unique_column_name}='{data}'"
        )
        res = cursor.fetchone()
        return res
    else:
        return None


def getFirstProduct(database_name, table_name):
    con = connectDatabase(database_name)
    cursor = con.cursor()

    if isExistsTable(con.cursor(), database_name, table_name):
        cursor.execute(f"SELECT min(id) FROM {getTableName(table_name)}")
        min_id = cursor.fetchone()["min(id)"]
        # カーソル生成
        cursor.execute(f"SELECT * FROM {getTableName(table_name)} WHERE id={min_id}")
        return cursor.fetchone()
    else:
        return None


def getFirstProductWhere(database_name, table_name, query_where):
    con = connectDatabase(database_name)
    cursor = con.cursor()

    if isExistsTable(con.cursor(), database_name, table_name):
        cursor.execute(f"SELECT min(id) FROM {getTableName(table_name)} {query_where}")
        min_id = cursor.fetchone()["min(id)"]
        # カーソル生成
        cursor.execute(f"SELECT * FROM {getTableName(table_name)} WHERE id={min_id}")
        return cursor.fetchone()
    else:
        return None


def getLastProduct(database_name, table_name):
    con = connectDatabase(database_name)
    cursor = con.cursor()

    if isExistsTable(con.cursor(), database_name, table_name):
        cursor.execute(f"SELECT max(id) FROM {getTableName(table_name)}")
        max_id = cursor.fetchone()["max(id)"]
        # カーソル生成
        cursor.execute(f"SELECT * FROM {getTableName(table_name)} WHERE id={max_id}")
        return cursor.fetchone()
    else:
        return None


def fetchmany(cursor, size=20):
    """
    20件づつ fetch する
    """
    while True:
        rows = cursor.fetchmany(size)
        if not rows:
            break

        yield rows
        # for row in rows:
        #     yield row


def getProductsWhere(database_name, table_name, query, N=None):
    query = re.sub("'", "", query, count=2)
    # データベース接続
    con = connectDatabase(database_name)
    cursor = con.cursor()

    if isExistsTable(con.cursor(), database_name, table_name):
        count = selectCount(cursor=cursor, query=query, is_translate=True)
        print(f"{query}\nデータベース名={database_name},全データ数={count}")
        cursor.execute(query)
        if N:
            for rows in fetchmany(cursor, size=N):
                yield rows
        else:
            for row in cursor.fetchall():
                yield row
    else:
        return None


def isRegisterd(database_name, table_name, unique_column_name, value):
    con = connectDatabase(database_name)
    cursor = con.cursor()
    createTableIfNotExists(cursor, database_name, table_name=table_name)
    if isExistsColumn(database_name, table_name, column_name=unique_column_name):
        count = selectCount(
            database_name=database_name,
            cursor=cursor,
            query=f"SELECT COUNT(*) FROM {getTableName(table_name)} where {unique_column_name} = '{value}';",
        )
    else:
        count = 0
    return count > 0


def isExistsTable(cursor, database_name, table_name):
    count = selectCount(
        database_name=database_name,
        cursor=cursor,
        query=f"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{database_name}' AND TABLE_NAME = '{table_name}';",
    )
    return count == 1


def close():
    # 接続を閉じる
    for db in __databases.values():
        db.close()

    __databases.clear()


def delete(database_name, table_name, data, unique_column_name):
    con = connectDatabase(database_name)
    cursor = con.cursor()
    cursor.execute(f"DELETE FROM {getTableName(table_name)} WHERE {unique_column_name} = '{data}'")
    con.commit()


def addColumnIfNotExists(database_name, table_name, column_name, value) -> bool:
    con = connectDatabase(database_name)
    cursor = con.cursor()
    if isExistsColumn(database_name, table_name, column_name):
        return False
    else:
        if type(value) is str:
            kind = "TEXT"
        elif type(value) is datetime.datetime:
            kind = "DATETIME"
        else:
            kind = type(value).__name__
        cursor.execute(f"ALTER TABLE {getTableName(table_name)} ADD COLUMN {column_name} {kind}")
        return True
    con.commit()


def isExistsColumn(database_name, table_name, column_name):
    con = connectDatabase(database_name)
    cursor = con.cursor()
    cursor.execute(
        f"SELECT TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME, COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{database_name}' AND TABLE_NAME = '{table_name}' AND COLUMN_NAME = '{column_name}';"
    )
    for row in cursor.fetchall():
        if row["COLUMN_NAME"] == column_name:
            return True

    return False


def isExistsAllColumns(database_name, table_name, data):
    if database_name in database_column_status and database_column_status[database_name]:
        pass
    else:
        is_all_existed = True
        for key, value in data.__dict__.items():
            # 値がNoneのものは型を特定できないためskipする｡serializeするときにinsert文に値がNoneのカラムを書かないように注意
            # not None で ""を含むようにしている
            if value is not None:
                b = addColumnIfNotExists(
                    database_name=database_name,
                    table_name=table_name,
                    column_name=key,
                    value=value,
                )
                if b:
                    is_all_existed = False
            else:
                pass

        database_column_status.update({key: is_all_existed})


def getTableName(table_name):
    table_name = f"`{table_name}`" if table_name.isdecimal() else table_name
    return table_name


def isExistsDatabase(database_name):
    query = f"SHOW DATABASES LIKE '{database_name}';"
    connect = connectToMysql(database_name=database_name, is_use_database=False)
    cursor = connect.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    if len(result) > 0:
        return True
    else:
        return False


def createDatabaseIfNotExists(database_name):
    query = f"CREATE DATABASE IF NOT EXISTS {database_name}"
    connect = connectToMysql(database_name, is_use_database=False)
    cursor = connect.cursor()
    cursor.execute(query)


def deleteDatabase(database_name):
    query = f"DROP DATABASE IF EXISTS {database_name}"
    connect = connectToMysql(database_name)
    close()
    cursor = connect.cursor()
    cursor.execute(query)


def backup():
    query = "mysqldump --single-transaction -u croller -p -x --all-databases > ./mysql_backup.dump"
    ActQuery(query)


def ActQuery(query):
    connect = connectToMysql()
    close()
    cursor = connect.cursor()
    cursor.execute(query)


def connectToMysql(database_name, is_use_database=True):
    connect = pymysql.connect(
        host=host,
        user="root",
        db=database_name if is_use_database else None,
        password="root",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        port=3306,
    )
    return connect