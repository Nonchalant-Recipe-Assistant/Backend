import numpy as np
from scipy.optimize import linprog

c = [3, -8, 0, 0, 0]

A_ub = [[2, 3, 1, 0, 0],  
        [1, -2, 0, 1, 0],   
        [1, 1, 0, 0, -1]]  
b_ub = [12, 4, 1]

# Границы переменных
x1_bounds = (0, None)  # x1 >= 0
x2_bounds = (-0.5, 3.5)  # 0.5 <= x2 <= 3.5
x3_bounds = (0, None)
x4_bounds = (0, None)
x5_bounds = (0, None)

# Решение задачи
result = linprog(c, A_ub=A_ub, b_ub=b_ub, 
                 bounds=[x1_bounds, x2_bounds, x3_bounds, x4_bounds, x5_bounds],
                 method='highs')

print(f"Оптимальное значение целевой функции: {result.fun}")
print(f"x1 = {result.x[0]:.1f}")
print(f"x2 = {result.x[1]:.1f}")
print(f"x3 = {result.x[2]:.1f}")
print(f"x4 = {result.x[3]:.1f}")
print(f"x5 = {result.x[4]:.1f}")
print(f"Значение исходной целевой функции (3x1 - 8x2): {3*result.x[0] - 8*result.x[1]:.2f}")

import pulp
import numpy as np

# Создаем задачу МИНИМИЗАЦИИ
prob_min = pulp.LpProblem('Целочисленная_задача_минимум', pulp.LpMinimize)

# Целочисленные переменные
x1 = pulp.LpVariable('x1', lowBound=0, cat='Integer')
x2 = pulp.LpVariable('x2', lowBound=-0.5, upBound=3.5, cat='Integer')

# Целевая функция: 3x1 - 8x2 -> MIN
prob_min += 3*x1 - 8*x2

# Ограничения
prob_min += 2*x1 + 3*x2 <= 12
prob_min += x1 - 2*x2 <= 4
prob_min += x1 + x2 >= 1

# Решение
prob_min.solve(pulp.PULP_CBC_CMD(msg=False))

print("\n" + "="*60 + "\n")

print(f"Минимальное значение функции: {pulp.value(prob_min.objective)}")
print(f"x1 = {pulp.value(x1)}")
print(f"x2 = {pulp.value(x2)}")