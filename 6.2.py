# Задание 6.2

# Запросить у пользователя ввод IP-адреса в формате 10.0.1.1
# В зависимости от типа адреса (описаны ниже), вывести на стандартный поток вывода:
#    'unicast' - если первый байт в диапазоне 1-223
#    'multicast' - если первый байт в диапазоне 224-239
#    'local broadcast' - если IP-адрес равен 255.255.255.255
#    'unassigned' - если IP-адрес равен 0.0.0.0
#    'unused' - во всех остальных случаях

# Ограничение: Все задания надо выполнять используя только пройденные темы.

ip = input('Enter ip: ')
f_ip = int(ip.split('.')[0])
if f_ip <= 223 and f_ip > 0:
   print('unicast')
elif f_ip <= 239 and f_ip >= 224:
   print('multicast')
elif ip == '255.255.255.255':
   print('local broadcast')
elif ip == '0.0.0.0':
   print('unassigned')
else:
   print('unused')