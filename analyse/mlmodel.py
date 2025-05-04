# pip install pandas numpy scikit-learn matplotlib
import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt

# 1. Verbindung zur SQLite-Datenbank
conn = sqlite3.connect("../webapp/db_statisch.sqlite3")
query = """
SELECT mac, rssi, timestamp
FROM bledata_bledata
WHERE rssi IS NOT NULL AND mac IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

df['timestamp'] = pd.to_datetime(df['timestamp'])
df['timestamp_numeric'] = df['timestamp'].astype('int64') // 10**9  # Umwandlung in Sekunden

# 2. Feature-Engineering für jede MAC-Adresse
features = []

for mac, group in df.groupby('mac'):
    group = group.sort_values('timestamp_numeric')
    rssi_vals = group['rssi'].values
    if len(rssi_vals) < 4:
        continue

    slope = np.polyfit(np.arange(len(rssi_vals)), rssi_vals, 1)[0]
    var = np.var(rssi_vals)
    std = np.std(rssi_vals)
    rssi_range = np.max(rssi_vals) - np.min(rssi_vals)

    features.append({
        'mac': mac,
        'slope': slope,
        'variance': var,
        'std_dev': std,
        'rssi_range': rssi_range,
        # ✏️ Manuelle Labels: z. B. später ergänzen
        'label': None  # 'moving' oder 'stationary'
    })

df_feat = pd.DataFrame(features)

# 3. Manuelle Labels setzen alle Geräte mit Apple im Namen
# Beispielhaft:
df_feat.loc[df_feat['mac'].isin([
'40:14:c3:5b:3e:a8',
'50:f8:b0:05:a2:e5',
'5a:f1:6c:5a:c5:60',
'62:c5:96:52:4f:80',
'6f:1d:c2:fd:7a:7d',
'71:9e:5f:be:1a:2b',
'7a:70:03:ce:23:20',
'c1:23:62:12:82:d3',
'c4:86:62:cd:28:57',
'cc:e9:ed:f8:ba:a8',
'd3:e9:0b:2a:77:1d',
'e2:96:ff:96:5a:ec',
'f2:35:6e:fc:3a:05',
'fa:86:99:24:57:83',
'ff:5b:bb:b8:44:a2',
    ]), 'label'] = 'moving'

# Beispielhafte manuelle Labels für stationäre Geräte
# einerseits bekannte stationäre Geräte, andererseits Geräte bzw. mac adressen, die nachweislich nicht in Bewegung sind
df_feat.loc[df_feat['mac'].isin([
'18:bb:26:60:2d:8c',
'4c:b9:ea:3a:c3:1f',
'54:d2:72:4c:b3:a1',
'd1:06:04:06:0e:5b',
'd1:25:14:68:8b:78',
'd7:39:38:38:1a:73',
'e8:0f:c8:54:ba:f6',
'eb:2b:f6:9a:ec:5b',
'4a:e9:35:46:a4:de',
'c7:ed:09:ae:f9:82',
'f6:08:c2:f9:e2:0d',
'd1:06:04:06:0e:5b',
'62:10:0d:ad:f3:2e',
'23:27:0c:3f:e3:87',
'd9:d6:c9:3b:c0:f2',
    ]), 'label'] = 'stationary'

# 4. Training
labeled = df_feat.dropna(subset=['label'])
X = labeled[['slope', 'variance', 'std_dev', 'rssi_range']]
y = labeled['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Bewertung
y_pred = model.predict(X_test)
print("\nKlassifikationsbericht:")
print(classification_report(y_test, y_pred))

# 6. Anwendung auf alle Geräte
unlabeled = df_feat[df_feat['label'].isna()]
X_unlabeled = unlabeled[['slope', 'variance', 'std_dev', 'rssi_range']]
predictions = model.predict(X_unlabeled)

unlabeled['predicted_label'] = predictions
#print("\n📍 Automatisch erkannte bewegte Geräte:")
#print(unlabeled[unlabeled['predicted_label'] == 'moving'][['mac', 'slope', 'std_dev']])
#print("\n📍 Automatisch erkannte statische Geräte:")
#print(unlabeled[unlabeled['predicted_label'] == 'stationary'][['mac', 'slope', 'std_dev']])

print(classification_report(y_test, y_pred, target_names=["stationary", "moving"]))