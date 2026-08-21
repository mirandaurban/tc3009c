"""
Primer acercamiento al Machine Learning
"""
from sklearn import tree 

# features = [[140, "smooth"], [150, "bumpy"], ]
# labels = ["apple", "apple", "orange", "orange"]
features = [[140, 1],[130, 1],[150, 0], [170, 0]]
labels = [0,0,1,1]

# Train classifier - Decision Tree
clf = tree.DecisionTreeClassifier()
clf = clf.fit(features, labels) # Classifier is trained on our data

res1 = clf.predict([[140,0]])

match res1:
    case 0:
        print("Apple")
    case 1:
        print("Orange")
    case _:
        print("Unknown")