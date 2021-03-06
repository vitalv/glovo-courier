import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sb 
sb.set_style("whitegrid", {'axes.grid' : False})
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import RandomizedSearchCV 
from sklearn.model_selection import GridSearchCV


lifetime = pd.read_csv('Courier_lifetime_data.csv')
weekly = pd.read_csv('Courier_weekly_data.csv')

plt.hist(lifetime.feature_2)


# keep only data within +3 to -3 standard deviations
outliers_ix = lifetime.index[np.abs(lifetime.feature_2-lifetime.feature_2.mean()) >= (3*lifetime.feature_2.std())]
lifetime.loc[outliers_ix, 'feature_2'] = np.NaN
for c in weekly.columns[2:]:
  outliers_ix = weekly.index[np.abs(weekly[c]-weekly[c].mean()) >= (3*weekly[c].std())]


#1st find couriers that do have weekly data to inspect the distributions
merge = pd.merge(lifetime, weekly, on='courier', how='right') #.to_csv('merge.csv')

#Then get the complete dataset. Lots of couriers will have lifetime data but no weekly data:
merge_all = pd.merge(lifetime, weekly, on='courier', how='left') #.to_csv('merge.csv')


#Plot distributions to check whether lifetime categories a, b, c, d are related to the distribution of the weekly features

a = merge.loc[merge.feature_1_x=='a']
b = merge.loc[merge.feature_1_x=='b']
c = merge.loc[merge.feature_1_x=='c']
d = merge.loc[merge.feature_1_x=='d']

weekly_features = merge.columns[4:] 

fig, axes = plt.subplots(9, 2, figsize=(20,30))

ax = axes.flatten() #ravel()

for i in range(len(weekly_features)):
    ax[i].hist(a.ix[:,weekly_features[i]], bins=20, color='red', alpha=.7)
    ax[i].hist(b.ix[:,weekly_features[i]], bins=20, color='green', alpha=.7)
    ax[i].hist(c.ix[:,weekly_features[i]], bins=20, color='blue', alpha=.7)
    ax[i].hist(d.ix[:,weekly_features[i]], bins=20, color='yellow', alpha=.7)
    ax[i].set_title(weekly_features[i], fontsize=18)
    ax[i].set_yticks(())
    
ax[0].set_xlabel("Feature distribution")
ax[0].legend(["a", "b", "c", "d"], loc="best")
fig.tight_layout()

plt.show()








#First knn-predict lifetime.feature_2 . I can only do this for couriers with weekly features 
#First create train X and target y
'''
X = np.matrix(merge.dropna()[weekly_features]) #will remove rows with missing feature_2_x 
y = np.matrix(merge['feature_2_x'].dropna())

#k = 5 by default
regr = KNeighborsRegressor().fit(X, y.transpose())
feature_2_x_ = regr.predict(np.matrix(merge[weekly_features]))#[:, 'feature_2_x']
merge['feature_2_x_'] = [int(i) for i in feature_2_x_]
'''

'''
#Do the same knn-prediction of feature_2_x for subsets a, b, c, d:
X = np.matrix(a.dropna()[weekly_features])
y = np.matrix(a['feature_2_x'].dropna())

#k = 5 by default
regr = KNeighborsRegressor().fit(X, y.transpose())
feature_2_x_ = regr.predict(np.matrix(a[weekly_features]))#[:, 'feature_2_x']
a['feature_2_x_'] = [int(i) for i in feature_2_x_]
'''

'''

#Replace the missing values in feature_2_x with the knn-predicted feature_2_x_ values
missing_f2_ix = merge.index[merge.feature_2_x.isnull()]
predicted_f2  = merge[merge.feature_2_x.isnull()].feature_2_x_
merge.loc[missing_f2_ix, 'feature_2_x'] = predicted_f2

#Note: the predicted feature_2_x values will be different for same courier! Is this right?

#Find the couriers in merge_all and replace the missing feature_2 values with the predicted one
#(will only affect the missing feature_2_x for the couriers that have weekly data)
merge.loc[missing_f2_ix, 'courier']

'''








#Impute missing values with combinations of feature_1_x and feature_2_x
#For example, of 103 couriers with feature1 == a, and feature2 == 31.0 
#43 of them have weekly data. Impute the remaining 60 ones with the median of the 43

#Note I can predict weekly features like this (with KNNRegressor)
#But not week, since it's not a continuous variable (KNNClassifier)

list_f1 = list(set(merge_all.feature_1_x))
list_f2 = list(set(merge_all[merge_all.feature_2_x.notnull()].feature_2_x))

frames = []
for f1 in list_f1:
  for f2 in list_f2:
    df = merge_all.loc[merge_all.feature_1_x==f1][merge_all.feature_2_x==f2]
    if len(df.dropna())>0: #some feature 1, feature 2 combinations don't have weekly data
      df = df.fillna(df[weekly_features].dropna().median())
      frames.append(df)
    else: #if feature_1_x + feature_2_x don't have weekly data, use the meadian of the f1 group
      df = df.fillna(merge_all.loc[merge_all.feature_1_x==f1].dropna().median())
      frames.append(df)
#And then for the 1227 couriers that have feature_1 but no feature_2 just impute the median of the category a, b, c, d
for f1 in list_f1:
  df = merge_all[merge_all.feature_2_x.isnull()][merge_all.feature_1_x==f1]
  df = df.fillna(df[weekly_features].dropna().median())
  frames.append(df)
data = pd.concat(frames)





#With the imputed data I can now knn-predict the missing feature_2_x values
X = np.matrix(data[data['feature_2_x'].notnull()][weekly_features])
y = np.matrix(data['feature_2_x'].dropna()).T

#k = 5 by default
regr = KNeighborsRegressor().fit(X, y)
feature_2_x_ = regr.predict(np.matrix(data[weekly_features]))#[:, 'feature_2_x']
data['feature_2_x_'] = feature_2_x_ #[int(i) for i in feature_2_x_]
#Replace the missing values in feature_2_x with the knn-predicted feature_2_x_ values
missing_f2_ix = data.index[data.feature_2_x.isnull()]
predicted_f2  = data[data.feature_2_x.isnull()].feature_2_x_
data.loc[missing_f2_ix, 'feature_2_x'] = predicted_f2


#Do not predict week here. Couriers with missing values for weeks 9, 10 and 11 will be removed
'''
X = np.matrix(data[data.week.notnull()][weekly_features])
y = np.matrix(data.week.dropna()).T
clf = KNeighborsClassifier().fit(X,y.ravel().tolist()[0])
week_ = clf.predict(np.matrix(data[weekly_features]))#[:, 'feature_2_x']
data['week_'] = week_
missing_week_ix = data.index[data.week.isnull()]
predicted_week  = data[data.week.isnull()].week_
data.loc[missing_week_ix, 'week'] = predicted_week
'''


sb.pairplot(data[weekly_features], kind='reg')
plt.show()




#Label data. If a specific courier’s week 9, 10 and 11 data is not provided, we label this
#courier as “1” otherwise “0”. After labeling, remove week 8(Yes including 8!), 9, 10 and 11 data to
#avoid bias in your next task

data['label'] = ''*len(data)

grouped = data.groupby('courier')

couriers1 = list(set(grouped.filter(lambda x: x.week.max() < 9).courier))
couriers0 = list(set(grouped.filter(lambda x: x.week.max() >= 9).courier))

data.loc[data[data.courier.isin(couriers1)].index, 'label'] = 1
data.loc[data[data.courier.isin(couriers0)].index, 'label'] = 0

#there are a lot of couriers that don't have week data (bc they didn't have weekly data at all). Label those 1
data.loc[data[data.label==''].index, 'label'] = 1 

data = data[data.week < 8]



#create a logistic regression model that classifies the previous labels
#You are free to choose your algorithm and libraries / packages to use.
#Finally, tune your hyper-parameters of your model by randomized search, grid search or any other
#search method and explain your reasoning for this choice.


x_train, x_test, y_train, y_test = train_test_split(data[weekly_features], data.label, test_size=0.25, random_state=0)

#1st try default parameters
logisticRegr = \
LogisticRegression(C=1.0, class_weight=None, dual=False, fit_intercept=True,
          intercept_scaling=1, max_iter=100, multi_class='ovr', n_jobs=1,
          penalty='l2', random_state=None, solver='liblinear', tol=0.0001,
          verbose=0, warm_start=False)

logisticRegr.fit(x_train, y_train)

predictions = logisticRegr.predict(x_test)



print(confusion_matrix(y_test,predictions))
print(classification_report(y_test, predictions))
print(accuracy_score(y_test,predictions))






#Logistic Regression supports only liblinear, newton-cg, lbfgs, sag and saga solvers
params = {'penalty': ['l1','l2'],
          'C':   np.arange(0.1, 10, 0.1)}
          
grid = GridSearchCV(logisticRegr, params)
grid.fit(x_train, y_train)
print(grid.best_params_)
#{'penalty': 'l2', 'C': 5.6}





#Solvers newton-cg, lbfgs, sag and saga support only l2 penalties. GridSearch won't work with those combinations
params = {'penalty': ['l2'], 
          'C': [0.001,0.01,0.1,1,10,100,1000],
          'solver': ['liblinear', 'lbfgs', 'sag', 'saga'],
          'multi_class': ['ovr', 'multinomial', 'auto'],
          'class_weight': [None, 'balanced']}
grid = GridSearchCV(logisticRegr, params)
grid.fit(x_train, y_train)
print(grid.best_params_)
          
#Solver liblinear does not support a multinomial backend. Can't choose that option for multi_class

'''
{'tol': 1.3225, 'penalty': 'l1', 'C': 96.7694}

   precision    recall  f1-score   support

          0       0.60      0.80      0.69       479
          1       0.61      0.38      0.47       406

avg / total       0.61      0.61      0.59       885





'''













#default parameters
knn_clf = KNeighborsClassifier(n_neighbors=5, weights='uniform', algorithm='auto',leaf_size=30, p=2, metric='minkowski', metric_params=None)
#run the classifier with default params first
knn_clf.fit(x_train, y_train)
predictions = knn_clf.predict(x_test)
print(confusion_matrix(y_test,predictions))

print(classification_report(y_test, predictions))

print(accuracy_score(y_test,predictions))







params = {"n_neighbors": np.arange(1, 31, 2),
          "metric": ["euclidean", "cityblock", "cosine"],
          "weights":["uniform", "distance"]}#,
          #"leaf_size": np.arange(20,41)}

grid = GridSearchCV(knn_clf, params)
grid.fit(x_train, y_train)
grid.best_params_
#{'metric': 'cosine', 'n_neighbors': 15, 'weights': 'uniform'}



knn_clf = KNeighborsClassifier(n_neighbors=9, weights='uniform', algorithm='auto', leaf_size=30, p=2, metric='cosine', metric_params=None)
knn_clf.fit(x_train, y_train)
predictions = knn_clf.predict(x_test)
print(confusion_matrix(y_test,predictions))

 
