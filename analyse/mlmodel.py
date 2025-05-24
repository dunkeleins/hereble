# required packages:
# pip install pandas numpy scikit-learn matplotlib
import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt

# 1. Verbindung zur SQLite-Datenbank aus dem Django-Projekt herstellen
conn = sqlite3.connect("../webapp/db_statisch.sqlite3")
query = """
SELECT mac_hash, rssi, timestamp
FROM bledata_bledata
WHERE rssi IS NOT NULL AND mac IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

df['timestamp'] = pd.to_datetime(df['timestamp'])
df['timestamp_numeric'] = df['timestamp'].astype('int64') // 10**9  # Umwandlung in Sekunden

# 2. Feature-Engineering für jeden MAC-Hash-Adresse
features = []

for mac_hash, group in df.groupby('mac'):
    group = group.sort_values('timestamp_numeric')
    rssi_vals = group['rssi'].values
    if len(rssi_vals) < 4:
        continue

    slope = np.polyfit(np.arange(len(rssi_vals)), rssi_vals, 1)[0]
    var = np.var(rssi_vals)
    std = np.std(rssi_vals)
    rssi_range = np.max(rssi_vals) - np.min(rssi_vals)

    features.append({
        'mac_hash': mac_hash,
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
df_feat.loc[df_feat['mac_hash'].isin([
'61936a2eb45ba5fff1316f69ca40f0a3156a85fcdca2bda5eae6781b9ee45335',
'c4ab86e17d7d081ce681df774b8b3b6c1710b45652caae2afb936e15cfb47749',
'7c858ed325ce985e723c518a854547bc91cd7586424647822252ccaab62c07c1',
'4de862df8a4529ff846a47964695ea3bae5b52121e6c8190bdd7da7fb5bc08be',
'5a554cef08aeb92dbb577a4f89a7b7b8c8207644aad9c7e7c4998ad189122334',
'74096226121fa51d1f492e0107eba31e7403c9c41e3bbb93c53ce94fe645e112',
'6b7dcb6d752bac034dfd2baa6bbd2f02771e278ca248c3203c25af275a4667d9',
'8cac42c3bc53cf15e2462005779c319b752df50e9b37066443d0f907228728fb',
'102f5be6b040b6610fb6b7194c4975b3a47af416e3cd8107d31c59cbc9b19b00',
'09b25d7586c502c93c9782033cff297cf9e58b9141950c6218fdea2027985000',
'1b2ed7178cf45a848ef33e541e0740d76828a4e5c1970eede08b7a5cd5026ba7',
'212edfa2edd367f90b91df4bfe8ef87f51ded06c8f05f69954bae19f088e4eed',
'90bce71cc96c725d6a8060edaa28c401c28288db7413299df013036efbc3f7e5',
'4770e275699ce1394013bfe14b7f31872e796fa40a2eaff04a682ee612990d57',
'b7c6449d71983b441ef0b5c44ff56d7ddb06de0f0c73413a7d1409008ad20924',
    ]), 'label'] = 'moving'

# Beispielhafte manuelle Labels für stationäre Geräte
# einerseits bekannte stationäre Geräte, andererseits Geräte bzw. mac adressen, die nachweislich nicht in Bewegung sind
df_feat.loc[df_feat['mac_hash'].isin([
'f65497b80dbc14e87fdd0813e4fe85d546861ebbd43319e3671ffd1aa05f2c5f',
'65107e7da57ddc88b18f35198f4a9b4a5dc9d436fd19d84f2efbc47619d8d042',
'd7602dca9c766b550cee2f4b2f70a56645fa6a57350c0d323a601efeeafac526',
'8ff2415f64d5f8ac3216e0e2b42e9763c5cbe99b99b5f4038aa38d286a6e5bb9',
'f9c10efaf5236b78491570e000169cd72b175230e5341902b32003c1181333b0',
'3ff3b4449ca9dbc93f930a4a9e13c6b93dd0cbd9be932716960b77c536ed7ecc',
'55424b51879a6fcc0f9abb42be6331be0365bca9ad6ad3f7128be65169c592cc',
'5072097ba0cdfcb30a663d798e89b908b29e8afb188f2ffc682185f8e8ea5121',
'33d5891f21c422a981f3b7cd80a657a413611ebbe793452d83235d7cfddfb21f',
'caa805632a2ed02edc660ccee1d73d196c21ef61c8e1a313925cce7c45f4c64d',
'0eae4234858238d07539ef891ca5652505c51ff47669ecdabd6ecb90ae86ccda',
'f9c10efaf5236b78491570e000169cd72b175230e5341902b32003c1181333b0',
'e0595653c73b1558528753b6d1db40103bc7a1ddd15942949ef2c770a6d19731',
'b9f2cdcbfeafaa63f7a97db21eb7082fec484269473140aafd65829735f28e9b',
'0511f93fb1c1b86477092f35741a87b4699612b89b065f5fbff396a11853a852',
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
#print("\nAutomatisch erkannte bewegte Geräte:")
#print(unlabeled[unlabeled['predicted_label'] == 'moving'][['mac', 'slope', 'std_dev']])
#print("\nAutomatisch erkannte statische Geräte:")
#print(unlabeled[unlabeled['predicted_label'] == 'stationary'][['mac', 'slope', 'std_dev']])

print(classification_report(y_test, y_pred, target_names=["stationary", "moving"]))