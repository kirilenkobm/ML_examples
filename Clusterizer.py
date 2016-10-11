import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime as dt
from sklearn.cluster import KMeans, AgglomerativeClustering, SpectralClustering
from sklearn.externals import joblib

knnf, aggf, spef = False, False, True  # choose for the clusterization algorhytm
start_time = dt.now()
n_clusters = int(input('Число кластеров: '))  # clusters count

"""
Script loads text data from SQL database, then clusterize it
"""

conn = sqlite3.connect("textarray.db")
cur = conn.cursor()
query = '''SELECT * from train'''
cur.execute(query)
dummy, names, descs, walls = [], [], [], []
for foo, n, d, w in cur.fetchall():
    dummy.append(foo)
    names.append(n)
    descs.append(d)
    walls.append(w)
basesize = len(names)
# data from db loaded


# TF-IDF vectorization
vectorizer = TfidfVectorizer(min_df=5,
                             sublinear_tf=True)
Xw = vectorizer.fit_transform(walls).toarray()
# Xd = vectorizer.transform(descs).toarray()  # description may be empty
Xd = 'null'
print('Description shape: {0}, Wall shape: {1}\n'.format(Xd, Xw.shape))
# X = np.hstack((Xd, Xw)) for description
X = Xw
joblib.dump(vectorizer, 'vect.pkl', compress=9)  # model persistence
#
# kNN clusterizer
if knnf:
    print('kNN clf:')
    clf = KMeans(n_clusters=n_clusters,
                 tol=0.00001,
                 n_init=100,
                 init='k-means++',
                 precompute_distances=True)

    y = clf.fit_predict(X)
    for i in range(basesize):
        print('Community: {0}, ClusterNo: {1}'.format(names[i], y[i]))
#
# Agglomerative clustering
if aggf:
    print('\nAgglomerativeClustering clf:')
    clf = AgglomerativeClustering(n_clusters=3,
                                  linkage='ward')
    y = clf.fit_predict(X)
    for i in range(basesize):
        print('Community: {0}, ClusterNo: {1}'.format(names[i], y[i]))
#
# Spectral clustering
if spef:
    print('\nSpectralClustering clf:')
    clf = SpectralClustering(n_clusters=n_clusters,
                             n_init=100)

    y = clf.fit_predict(X)
    for i in range(basesize):
        print('Community: {0}, ClusterNo: {1}'.format(names[i], y[i]))

joblib.dump(clf, 'clf.pkl', compress=9)  # persistance of choosen model
for i in range(basesize):
    cur.execute('''UPDATE train SET cat=? WHERE name=?''', (int(y[i]), names[i]))

print(vectorizer.get_feature_names())
conn.commit()
print('Estimated time: {0}'.format(dt.now() - start_time))
