import duckdb

conn = duckdb.connect('C:/Projetos Claude/Iot/iot-data-platform/iot_platform.duckdb')

conn.execute("CREATE SCHEMA IF NOT EXISTS main_raw")

conn.execute("""
CREATE TABLE IF NOT EXISTS main_raw.sensor_readings AS 
SELECT * FROM read_csv_auto('C:/Projetos Claude/Iot/iot-data-platform/dbt_project/seeds/sensor_readings.csv')
""")

result = conn.execute('SELECT COUNT(*) FROM main_raw.sensor_readings').fetchone()
print(f'Registros carregados: {result[0]}')
conn.close()