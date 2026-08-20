# Mejora de un modelo de predicción de precios

## Descripción

En este proyecto se busca mejorar un modelo de **predicción de precios de vehículos usados**, tomando como punto de partida un modelo de Regresión Lineal proporcionado por el profesor.

El objetivo principal es realizar diferentes experimentos modificando el procesamiento de los datos, las variables utilizadas y/o el algoritmo de aprendizaje, para identificar una configuración que mejore el desempeño respecto al modelo **baseline**.

## Dataset

Se utilizó el dataset Vehicle Dataset from Cardekho, disponible en Kaggle:
https://www.kaggle.com/datasets/nehalbirla/vehicle-dataset-from-cardekho

Específicamente, se hizo uso del archivo `Car details v3.csv`debido a que, de todos los archivos del Dataset, es el que más contiene datos; al ser tener más información, hace que el modelo sea más preciso.

El objetivo (`target`) del modelo es predecir la variable: `precio`

## Baseline

El baseline corresponde a la primera ejecución del código proporcionado, utilizando:

- Preparación de los datos.
- División en entrenamiento y prueba.
- Preprocesamiento.
- Regresión Lineal.
- Evaluación mediante MAE, RMSE y R².

Los resultados del baseline se utilizaron como referencia para comparar todos los experimentos posteriores.

## Experimentos

Se realizaron al menos cinco experimentos, modificando diferentes componentes del pipeline de machine learning.

| Experimento   | Modificación                            |       MAE |      RMSE |     R² | Resultado                                        |
| ------------- | --------------------------------------- | --------: | --------: | -----: | ------------------------------------------------ |
| Baseline      | Regresión Lineal original               | 273709.59 | 451950.32 | 0.7062 | Referencia                                       |
| Experimento 1 | Tratamiento de valores faltantes        |  275496.3 | 450134.35 | 0.6909 | No mejora                                        |
| Experimento 2 | Cambio de algorirmo Árbol CART          |  69073.66 | 131340.41 | 0.9752 | Mejora evidente                                  |
| Experimento 3 | Cambio de algoritmo ExtraTreesRegressor |  56438.57 |  106012.2 | 0.9838 | Mejora significativa ante iteraciones anteriores |
| Experimento 4 | Selección de features                   | 276726.68 | 459791.18 | 0.6959 | No mejora                                        |
| Experimento 5 | Escalamiento                            |  80596.56 | 154691.14 | 0.9656 | Mejora respecto al baseline, pero no es el mejor |

### Experimento 1 — Tratamiento de valores faltantes

**Cambio realizado:**
Originalmente solo se hacía uso de `df.dropna()` para eliminar las filas con datos faltantes (Heldmaier, 2025). Se cambió a un enfoque que aún desechaba las filas que tenían información faltante solo para la variable target, que se complementó con un tratamiento para las variables categóricas a través de la moda.

**Resultado:**
El RMSE mejora ligeramente, indicando que los errores grandes se reducen. Sin embargo, el MAE y R² empeoran, lo que se traduce en un aumento en el error absoluto promedio y un decremento en la capacidad del modelo en identificar la variabilidad del precio. En resumen, no se puede considerar como una mejora.

**Interpretación:**
Originalmente, al realizar la eliminación de filas completas para evitar que los valores faltantes potenciaran sesgos en el modelo se perdían 222 de 8128 filas o lo equivalente a un 2.7% del dataset. Se buscaba mejorar los resultados obtenidos al tener menores pérdidas con la completación artificial de datos, sin embargo, los resultados propablemente no fueron exitosos debido a que el uso de la moda y otras técnicas de imputación simple pueden provocar que el sistema subestime la incertidumbre, como errores estándar demasiado pequeños, y distorsione las distribuciones (Tüzen & Tüzen, 2025), alterando los valores de MAE y R² negativamente.

### Experimento 2 — Cambio de algorirmo Árbol CART

**Cambio realizado:**
Se modificó el algoritmo de entrenamiento del modelo. Originalmente se utilizaba Regresión Lineal y se remplazó por el algoritmo de Árbol de Regresión (CART).

**Resultado:**
El RMSE mejora significativamente, lo que se traduce en una menor porporción de errores grandes. El MAE también presenta resultados destacables que implican una reducción el error promedio. El R² crece, por lo que la capacidad del árbol de explicar la variabilidad del precio mejora de 70% a 97.5%.

**Interpretación:**
La mejora se debe probablemente a la forma en que opera este algoritmo. Básicamente, construye un árbol de decisión dividiendo recursivamente el conjunto de datos en función de la característica y el umbral que producen la mayor reducción en la impureza, lo que permite obtener un árbol que proporciona el error de predicción más bajo posible (GeeksforGeeks, 2025). Concretamente, este efecto de mejora se debe a la relación entre las características de los vehículos y el precio; anteriormente, al tratarse con una regresión lineal no se lograba capturar por completo su comportamiento, mientras que el uso de este árbol permite mapearla de mejor manera.

### Experimento 3 — Cambio de algoritmo ExtraTreesRegressor

**Cambio realizado:**
Se modificó el algoritmo de entrenamiento del modelo. Originalmente se utilizaba Regresión Lineal y se remplazó por el algoritmo de ExtraTreesRegressor.

**Resultado:**

Se observa una mejora ante las ejecuciones anteriores (baseline, experimento 1 y experimento 2). Hubo un aumento considerable entre los resultados de MAE, RMSE y R². Lo que implica que el modelo es más preciso, pues la diferencia absoluta entre el precio real y el predicho es menor, así como logra explicar la variabilidad de los precios

**Interpretación:**
Se optó por el uso de este método de imputación debido a que es ideal para llenar los valores que faltan en el dataset (Anil, 2025). Los resultados demuestran que la aplicación de este método permitió obtener un desempeño superior al de los modelos anteriores debido a que la forma en que se manejan los datos permite capturar relaciones no lineales y complejas entre las variables, a diferencia de la regresión lineal. Además, al igual que el experimento anterior, al combinar muchos árboles con particiones aleatorias, reduce la dependencia de un solo árbol y mejora la capacidad de generalización, pero este modelo lo logra de manera más óptima con el conjunto de datos dados.

### Experimento 4 — Selección de features

**Cambio realizado:**
Se hizo una selección de features según un test estadístico `f_regression`, este enfoque con `SelectKBest` identifica las variables menos importantes y las eliminaba al entrenar el modelo (Feature Selection Using SelectKBest, 2018).

**Resultado:**
La selección de features no mejoró el desempeño de la regresión lineal. El MAE y RMSE aumentaron, mientras que el R² disminuyó de 0.7062 a 0.6959. Lo que refleja un modelo poco confiable y que no debe de ser utilizado para la toma de decisiones.

**Interpretación:**
Se intentó este enfoque porque, en algunas ocasiones, las variables poco informativas puede reducir ruido y simplificar el modelo, por lo que al eliminarlas y dejar solo las más relevantes puede provocar mejoras. Sin embargo, este no fue el caso con este modelo y dataset. Concretamente, el uso de este método favoreción una eliminación de features que contenían información útil (como el nombre del vehículo, el tipo de combustible, la cantidad de dueños, entre otras variables con información relevante). Con esto en mente, el modelo no logró predecir correctamente el precio.

### Experimento 5 — Escalamiento

**Cambio realizado:**
Se aplicó escalamiento a las variables numéricas para llevarlas a una escala comparable antes de entrenar el modelo de regresión lineal.

**Resultado:**
Se obtuvo un MAE de 80,596.56, un RMSE de 154,691.14 y un R² de 0.9656, mejorando considerablemente respecto al baseline.

**Interpretación:**
El escalamiento permitió al modelo obtener predicciones más cercanas a los valores reales, reduciendo los errores y aumentando la proporción de variabilidad explicada del precio. Esto indica que, bajo la configuración utilizada en este experimento, trabajar con las variables numéricas en una escala comparable favoreció el desempeño de la regresión lineal. Concretamente, este efecto puede estar relacionado con el hecho de que el escalamiento permite tomar los features y asegurar que todas las características contribuyan por igual, solucionando un problema recurrente en donde features tienen un impacto demasiado alto en la predicción, mientras que otras características más pequeñas caen en el camino (Pelletier, 2025).

## Comparación de resultados

Los experimentos muestran diferencias importantes en el desempeño de los modelos. El baseline de Regresión Lineal obtuvo un MAE de 273,709.59, un RMSE de 451,950.32 y un R² de 0.7062. La selección de características no produjo una mejora, ya que aumentó los errores y redujo el R². En cambio, el escalamiento mejoró considerablemente el desempeño de la Regresión Lineal, pero no fue el mejor calificado. El cambio de modelo a CART produjo una mejora aún mayor, pero el cambio a Extra Trees Regression obtuvo los mejores resultados generales, con los valores más bajos de MAE y RMSE y el R² más alto.

## Mejor modelo

El mejor modelo seleccionado fue:

**Modelo:** Extra Trees Regression

Sus resultados fueron:

- **MAE:** `56,438.57`
- **RMSE:** `106,012.20`
- **R²:** `0.9838`

### Mejora respecto al baseline

| Métrica |   Baseline | Extra Trees Regression |  Mejora |
| ------- | ---------: | ---------------------: | ------: |
| MAE     | 273,709.59 |              56,438.57 |  79.38% |
| RMSE    | 451,950.32 |             106,012.20 |   76.54 |
| R²      |     0.7062 |                 0.9838 | +0.2776 |

La modificación que produjo la mayor mejora fue el cambio a Extra Trees Regression. Ya que el modelo puede capturar relaciones no lineales y complejas entre las características de los vehículos. Además, al combinar múltiples árboles, logra reducir los errores de predicción y mejorar el desempeño respecto a un único árbol y a la regresión lineal.

## Predicción de 3 vehículos

Finalmente, se utilizó el mejor modelo para estimar el precio de tres vehículos:

| Vehículo                 |  Precio estimado |
| ------------------------ | ---------------: |
| Volvo V40 D3 R-Design N  | $2,333,079.99 MX |
| Hyundai i10 Era 1.1      |  $149,669.91 MXN |
| Nissan Terrano XL 110 PS |  $700,215.00 MXN |

## Conclusiones

Los experimentos permitieron observar cómo diferentes decisiones dentro del pipeline de machine learning afectan el desempeño de un modelo de predicción de precios. La comparación con el baseline permitió identificar qué modificaciones fueron realmente útiles y cuáles no produjeron una mejora. El mejor modelo fue seleccionado considerando MAE, RMSE y R², priorizando una reducción de los errores y una mayor capacidad explicativa. En general, los resultados muestran la importancia de la preparación de datos, ingeniería de características y selección del modelo para mejorar el desempeño de un sistema de predicción. En particular, Extra Trees Regression obtuvo el mejor desempeño, reduciendo considerablemente los errores respecto al baseline y alcanzando un R² de 0.9838.

## Referencias

- Anil, P. A. (2025, 24 enero). Used Car Price Prediction using Machine Learning. Towards Data Science. https://towardsdatascience.com/used-car-price-prediction-using-machine-learning-e3be02d977b2/
- Feature selection using SelectKBest. (2018, 31 agosto). Kaggle. https://www.kaggle.com/code/jepsds/feature-selection-using-selectkbest
- GeeksforGeeks. (2025, 4 diciembre). CART (Classification and Regression Tree) in Machine learning. GeeksforGeeks. https://www.geeksforgeeks.org/machine-learning/cart-classification-and-regression-tree-in-machine-learning/
- Heldmaier, C. (2025, 26 junio). What is pandas dropna()? Digital Guide. https://www.ionos.com/digitalguide/websites/web-development/python-pandas-dataframe-dropna/
- Pelletier, H. (2025, 17 enero). Data Scaling 101: Standardization and Min-Max Scaling Explained. Towards Data Science. https://towardsdatascience.com/data-scaling-101-standardization-and-min-max-scaling-explained-60789833e160/
- Tüzen, M. F., & Tüzen, M. F. (2025, 17 agosto). Handling Missing Data in R: A Comprehensive Guide | R-Bloggers. R-bloggers. https://www.r-bloggers.com/2025/08/handling-missing-data-in-r-a-comprehensive-guide/#google_vignette

## Uso de inteligencia artificial

Se utilizó **ChatGPT como herramienta de apoyo** para solicitar el formato y la estructura de este README. La experimentación, ejecución del código, obtención de resultados y selección del modelo fueron realizadas para el desarrollo de la actividad.
