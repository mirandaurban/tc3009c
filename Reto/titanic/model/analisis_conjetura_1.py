import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind

df = pd.read_csv('../dataset/Titanic-Dataset.csv')

# Filtro: Solo mujeres
mujeres = df[df['Sex'] == 'female'].copy()


# Clasificar aquellas que viajaban con menores
mujeres['Viaja_con_menores'] = mujeres['Parch'] > 0

# Generar tabla
resultado = mujeres.groupby('Viaja_con_menores')['Survived'].agg(
    mujeres='count',
    sobrevivieron='sum',
    tasa_supervivencia='mean'
)

resultado['tasa_supervivencia'] *= 100

print(f"\n--------- Tabla de resultados ---------")
print(resultado)

print(f"\nSupervivencia mujeres con menores: {resultado.loc[True, 'tasa_supervivencia']} %\n")

print(f"Supervivencia mujeres sin menores: {resultado.loc[False, 'tasa_supervivencia']} %")


# Comprobar con t-value y p-value
con_menores = mujeres[mujeres['Parch'] > 0]['Survived']
sin_menores = mujeres[mujeres['Parch'] == 0]['Survived']

print(f"\n\nTotal de mujeres: {len(mujeres)}")
print(f"Mujeres con menores: {len(con_menores)}")
print(f"Mujeres sin menores: {len(sin_menores)}\n")

# t-test
t_value, p_value = ttest_ind(con_menores, sin_menores)

print("t-value:", t_value)
print("p-value:", p_value)

if p_value < 0.05:
    print("La diferencia es estadísticamente significativa.")
else:
    print("No hay evidencia suficiente de una diferencia estadísticamente significativa.")