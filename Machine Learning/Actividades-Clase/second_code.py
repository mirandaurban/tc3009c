"""
 Machine Learning
"""
from sklearn import tree 
from sklearn.model_selection import train_test_split 
from sklearn.metrics import accuracy_score, confusion_matrix 

# Features: [weight, texture] --› texture: 1 = smooth, 0 = bumpy
features = [
    [140, 1], [130, 1], [150, 0], [170, 0], [120, 1],
    [160, 0], [135, 1], [155, 0], [145, 1], [165, 0],
    [125, 1], [175, 0], [115, 1], [180, 0], [138, 1],
    [158, 0], [148, 1], [168, 0], [132, 1], [152, 0]
]

# Labels: 0 - apple (smooth), 1 = orange (bumpy)
labels = [
    0, 0, 1, 1, 0, 
    1, 0, 1, 0, 1,
    0, 1, 0, 1, 0,
    1, 0, 1, 0, 1
]
# Split dataset into 70% training and 30% testing
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.3, random_state=42)

# Train the Decision Tree Classifier
clf = tree.DecisionTreeClassifier()
clf = clf.fit(X_train, y_train)

# Predict on test data
y_pred = clf.predict (X_test)

# Evaluate
print("Predictions:" , y_pred)
print("Actual:" , y_test)