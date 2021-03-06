import sys
import re

def fisher_cluster(data_list):
    sum_cost = sys.maxsize
    label = 0
    for i in range(1, len(data_list)):
        d1 = 0
        d2 = 0
        avg1 = get_average(data_list[0:i])
        avg2 = get_average(data_list[i:len(data_list)])
        for j in range(i):
            d1 += (data_list[j] - avg1) * (data_list[j] - avg1)# * (data_list[j] - avg1)
        for j in range(i, len(data_list)):
            d2 += (data_list[j] - avg2) * (data_list[j] - avg2)# * (data_list[j] - avg2)
        if d1 + d2 < sum_cost:
            sum_cost = d1 + d2
            label = i
    return label, sum_cost


def get_average(inlist):
    sum_inlist = 0
    for item in inlist:
        sum_inlist += item
    return sum_inlist / len(inlist)


if __name__ == '__main__':
    file_obj = open('./time_clo.txt','r').read()
    print(file_obj)
    re_pattern = '\d+'
    match = re.findall(re_pattern,file_obj)
    print(match)
    data = []
    for d in match:
        data.append(int(d))
    print(data)
    label = fisher_cluster(data)[0]
    print(sum(data[0:label]))
    print(sum(data[label:len(data)]))
    print(label, data[label])


    # re_pattern = '^\\[(\d+, )*(\d+)\\]'
    # test_list = [9.3,1.8,1.9,1.7,1.5,1.3,1.4,2.0,1.9,2.3,2.1]
    # print(fisher_cluster(test_list))

