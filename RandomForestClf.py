import sqlite3
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime as dt
from sklearn.externals import joblib

start_time = dt.now()
# data loading
conn = sqlite3.connect("textarray.db")
cur = conn.cursor()
query = '''SELECT * from train'''
cur.execute(query)

y_train, names, descs, X_train = [], [], [], []
for c, n, d, w in cur.fetchall():
    y_train.append(c)
    names.append(n)
    descs.append(d)
    X_train.append(w)

vectorizer = joblib.load('vect.pkl')
XtrV = vectorizer.fit_transform(X_train).toarray()  # X-Train-Vectorized

RF = RandomForestClassifier(n_estimators=100,
                            max_depth=9,
                            n_jobs=4)

RF.fit(XtrV, y_train)
joblib.dump(RF, 'RF.pkl', compress=9)
# validation on the test set
query = '''SELECT * from test'''
cur.execute(query)
y_test, names, descs, X_test = [], [], [], []
for c, n, d, w in cur.fetchall():
    y_test.append(c)
    names.append(n)
    descs.append(d)
    X_test.append(w)
test_size = len(y_test)

XteV = vectorizer.transform(X_test).toarray()  # X-Test-Vectorized

pred = RF.predict(XteV)

for i in range(test_size):
    cur.execute('''UPDATE test SET cat=? WHERE name=?''', (pred[i], names[i]))

print('Estimated: {0}'.format(dt.now()-start_time))
