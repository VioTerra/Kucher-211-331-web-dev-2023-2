# Задание 4.5

# Из строк command1 и command2 получить список VLANов, которые есть и в команде command1 и в команде command2 (пересечение).
# В данном случае, результатом должен быть такой список: ['1', '3', '8']
# Записать итоговый список в переменную result. (именно эта переменная будет проверяться в тесте)
# Полученный список result вывести на стандартный поток вывода (stdout) с помощью print.

# Ограничение: Все задания надо выполнять используя только пройденные темы.

command1 = "switchport trunk allowed vlan 1,2,3,5,8"
command2 = "switchport trunk allowed vlan 1,3,8,9"

result1 = set(command1.split()[-1].split(","))
result2 = set(command2.split()[-1].split(","))
# set изменяет тип данных на множество (строка в множнество {})
print(sorted(result1.intersection(result2)))
# intersection осуществляет пересечение элементов множеств
# а затем просто идет сортировка
