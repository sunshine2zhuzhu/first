# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 10:27:58 2018

@author: 杨光
"""
import pandas as pd
import numpy as np
import random
import copy
import time


class Node(object):
    def __init__(self,c_id,x,y,demand1,demand2,demand3):
        self.c_id = [(c_id,i) for i in range(3)]
        self.x = x
        self.y = y
        self.demand = (demand1,demand2,demand3)
        self.belong_veh = None

class Vehicle(object):
    def __init__(self,v_id:int,cap:int):
        self.v_id = [v_id,v_id,v_id]
        self.cap = cap
        self.load = [0,0,0]
        self.r_k = 0
        self.site_k = 0
        self.Route = []
        self.distance = 0
        self.speed = 50
    
    def add_node(self,j:int,oil_number:int):
        self.Route.append((j,oil_number))
        self.update_var()
    
    def random_del(self,index:int):
        self.Route.pop(index)
        self.update_var()
    
    #根据对象删除节点
    def del_node_by_node(self,node:Node):
        self.Route.remove(node)
        self.update_var()
        
    def insert_node(self,node,index:int):
        self.Route.insert(index,node)
        self.update_var()
        
    #加入路径操作
    def add_route(self):
        self.Route = [(0,0),(0,0)]
        self.distance = 0
        self.update_var()

    #计算某点前后距离之和
    def distance_sum(self,node):
        c = self.Route[node]
        a = self.Route.index(c)-1
        b = self.Route.index(c)+1
        sum_num = distance_matrix[self.Route[a][0]][c[0]] + distance_matrix[c[0]][self.Route[b][0]]
        return sum_num
    
    #子路径删除
    def del_subroute(self,subroute):
        for sub in subroute:
            if sub in self.Route:
                self.Route.remove(sub)
        self.update_var()
    
    def update_var(self):
        #更新当前距离
        cur_distance = 0
        for i in range(len(self.Route)-1):
            a_1 = self.Route[i]
            b_1 = self.Route[i+1] 
            cur_distance += distance_matrix[a_1[0]][b_1[0]]
        self.distance = cur_distance

        #更新载重
        cur_load = [0,0,0]
        for n in self.Route:
            cur_load[n[1]] += nodes[n[0]].demand[n[1]]
        self.load = cur_load

        #更新当前时刻
        cur_r_k = 0
        for m in range(len(self.Route)-1):
            cur_r_k += distance_matrix[self.Route[m][0]][self.Route[m+1][0]]/self.speed
        self.r_k = cur_r_k
        
        #更新当前位置
        self.site_k = self.Route[-1][0]
        



#读取数据,包括车辆数量，车舱数，各加油站位置，需求量等
def read_data(path):
    with open(path,'r') as f:
        lines = f.readlines()
    capacity = (int)(lines[4].split()[-1]) #车辆容量（每个车舱）
    max_vehicle = (int)(lines[4].split()[0])#最大车辆数
    lines = lines[9:]
    nodes = []
    for line in lines:
        info = [int(j) for j in line.split()]
        if len(info) == 6:
            node = Node(*info)
            nodes.append(node)
    return capacity, max_vehicle, nodes

#计算距离
def cal_distance_matrix(nodes:list):
    distance_matrix = np.zeros((len(nodes),len(nodes)))
    for i in range(len(nodes)):
        for j in range(i+1,len(nodes)):
            if i != j:
                dis = np.sqrt((nodes[i].x - nodes[j].x)**2 +(nodes[i].y - nodes[j].y)**2)
                distance_matrix[i][j] = distance_matrix[j][i] = dis
    return distance_matrix

#目标函数：总成本
def cal_obj(vehicles:list,g_k:int=1,c_k:int=200):
    distance = sum([v.distance for v in vehicles])
    return distance*g_k+c_k*len(vehicles)

#获得需要服务的点
def total_node_not_zero(nodes):
    A = []
    for i in range(len(nodes)):
        A.extend(nodes[i].demand)
    length=len(A)
    x=0
    while x < length:
        if A[x] == 0:
            del A[x]
            x -= 1
            length -= 1
        x += 1
    total_number = len(A)
    return total_number

#贪婪算法生成初始解
def greedy_algorithm(max_vehicle:int,capacity_list:list,T_s:int = 8,c_k:int = 200,g_k:int=1):
    #
    vehicles = []
    assigned_node_id = set([])#已服务需求点集合
    for num_veh in range(max_vehicle):
        if len(assigned_node_id) == total_node_not_zero(nodes):
            break#当所有需求点都被服务时停止
        veh = Vehicle(num_veh,capacity_list)
        
        veh.Route.append((0,0))#开始加车场
        for oil_number in range(3):
            
            candidate_set = [] #有s油品需求的点
            
            for i in range(len(nodes)):
                if nodes[i].demand[oil_number] != 0 and (i,oil_number) not in assigned_node_id:
                    candidate_set.append(nodes[i].c_id[oil_number])
            is_done = True 
            #当该集合不为空时，do
            while is_done:
                if candidate_set:
                    Distance = []#这些点到当前位置的距离
                    for candidate in candidate_set:
                        Distance.append(distance_matrix[veh.site_k][candidate[0]])
                    j = candidate_set[np.argmin(Distance)][0]#选择距离当前点最近的点
                    #如果满足载重约束和时间约束，do
                    if veh.load[oil_number] + nodes[j].demand[oil_number] <= veh.cap[oil_number]\
                    and veh.r_k + (distance_matrix[veh.site_k][j]+distance_matrix[j][0])/veh.speed <= T_s:
                        veh.add_node(j,oil_number)#将该点加入到路径中
                        assigned_node_id.add((j,oil_number))#加入已服务集合
                        candidate_set.remove((j,oil_number))#将其从候选集合中删除
                    else:
                         is_done = False
                else:
                    is_done = False
        veh.add_node(0,0)

        vehicles.append(veh)
    cost = cal_obj(vehicles,g_k,c_k)
    return vehicles,cost


#获得一条路径上同一油品的路径
def get_node_num(A:list,B:int):
    C = []
    for a in A:
        if a[1] == B and a[0] != 0:
            C.append(a)
    return C


    
#大邻域搜索算法(模拟退火)
    #输入初始解，最大迭代次数，初始常数p,冷却率h
def big_neighbor_search(cur_vehs:list,cur_obj:int,iter_max = 100,p_init = 1000,h = 0.8,T_s = 8,lamd_1=0.4,lamd_2=0.4,lamd_3=0.2,mu=0.1):
    T = cur_obj*p_init
    t = 0
    #初始解为全局最优解
    global_best_vehs = [copy.copy(cur_vehs[i]) for i in range(len(cur_vehs))]
    for i in range(len(cur_vehs)):
        global_best_vehs[i].Route = copy.copy(cur_vehs[i].Route)
    cur_best_vehs = [copy.copy(cur_vehs[i]) for i in range(len(cur_vehs))]
    for i in range(len(cur_vehs)):
        cur_best_vehs[i].Route = copy.copy(cur_vehs[i].Route) 
    #初始目标值为全局最优值
    global_best_obj = cal_obj(global_best_vehs)
    cur_best_obj = cal_obj(cur_best_vehs)
    while t < iter_max:
        t += 1
        #随机选择一种删除方式
        p_1 = random.randint(1,7)
#        p_1 = 2
        L_s = set([])#已删除需求点集合
        n = 6#重复次数
        
        #删除操作
        #1.随机删除（RR）
        veh_num = len(cur_vehs)
        if p_1 == 1:
            for i in range(n):
                random_route_num = random.randint(0,veh_num-1)
                while len(cur_vehs[random_route_num].Route) <= 2:#长度要大于2
                    random_route_num = random.randint(0,veh_num-1)
                random_node_num = random.randint(1,len(cur_vehs[random_route_num].Route)-2)
                L_s.add(cur_vehs[random_route_num].Route[random_node_num])
                cur_vehs[random_route_num].random_del(random_node_num)#删除随机选择的点
        #2最长距离删除（WDR）
        if p_1 == 2:
           
            for i in range(n): 
                #距离差
                max_distance = 0
                #最优删除点，车辆编号
                best_cus = best_veh = 0
                for k in range(len(cur_vehs)):
                    if len(cur_vehs[k].Route) >= 3:
                        for p in range(1,len(cur_vehs[k].Route)-1):
                            cur_distance = cur_vehs[k].distance_sum(p)
                            if cur_distance > max_distance:
                                max_distance = cur_distance
                                best_cus = p
                                best_veh = k
                L_s.add(cur_vehs[best_veh].Route[best_cus])
                cur_vehs[best_veh].random_del(best_cus)
                
        #3.子路径删除（RR）
        if p_1 == 3:
            for i in range(n):
                #随机获得车辆序号
                random_route_num = random.randint(0,veh_num-1)
                while len(cur_vehs[random_route_num].Route) <= 2:#长度要大于2
                    random_route_num = random.randint(0,veh_num-1)
                random_oil_num = random.randint(0,2)
                #获得该条路该油品的子路径
                sub_route_1 = get_node_num(cur_vehs[random_route_num].Route,random_oil_num)
                for i in sub_route_1:
                    L_s.add(i)
                cur_vehs[random_route_num].del_subroute(sub_route_1)
        #4.相似需求点删除（SR）
#        if p_1 == 4:
#            for i in range(n):
                
        #5.距离最近需求点删除（NDR）
        if p_1 == 4:
            for i in range(n):
                #两点之间距离
                distance_a_b = np.inf
                #最优位置
                best_cus = best_veh = 0
                #随机获得车辆序号
                random_route_num = random.randint(0,veh_num-1)
                while len(cur_vehs[random_route_num].Route) <= 2:#长度要大于2
                    random_route_num = random.randint(0,veh_num-1)
                random_node_num = random.randint(1,len(cur_vehs[random_route_num].Route)-2)#随机一个位置
                node_ori = cur_vehs[random_route_num].Route[random_node_num]
                L_s.add(node_ori)#加入集合
                cur_vehs[random_route_num].random_del(random_node_num)#删除该点
               
                #找到距离最近的点(不能为0)
                for k in range(len(cur_vehs)):
                    for p in range(1,len(cur_vehs[k].Route)-1):
                        if cur_vehs[k].Route[p][1] == node_ori[1]:
                            if cur_vehs[k].Route[p][0] != node_ori[0]:
                                best_min_dis = distance_matrix[cur_vehs[k].Route[p][0]][node_ori[0]]
                                if best_min_dis < distance_a_b:
                                    distance_a_b = best_min_dis
                                    best_cus = p
                                    best_veh = k
                if best_cus != 0:
                    L_s.add(cur_vehs[best_veh].Route[best_cus])
                    cur_vehs[best_veh].random_del(best_cus)
        #6.需求量最近的需求点删除(DR)
        if p_1 == 5:
            for i in range(n):
                #两点之间距离
                quantity_a_b = np.inf
                #最优位置
                best_cus = best_veh = 0
                #随机获得车辆序号
                random_route_num = random.randint(0,veh_num-1)
                while len(cur_vehs[random_route_num].Route) <= 2:#长度要大于2
                    random_route_num = random.randint(0,veh_num-1)
                random_node_num = random.randint(1,len(cur_vehs[random_route_num].Route)-2)#随机一个位置
                node_ori = cur_vehs[random_route_num].Route[random_node_num]
                L_s.add(node_ori)#加入集合
                cur_vehs[random_route_num].random_del(random_node_num)#删除该点
                
                #找到需求最近的点
                for k in range(len(cur_vehs)):
                    for p in range(1,len(cur_vehs[k].Route)-1):
                        if cur_vehs[k].Route[p][1] == node_ori[1]:#同种油品
                            if cur_vehs[k].Route[p][0] != node_ori[0]:#非同一个点
                                best_min_quan = abs(nodes[cur_vehs[k].Route[p][0]].demand[node_ori[1]] - nodes[node_ori[0]].demand[node_ori[1]])
                                if best_min_quan < quantity_a_b:
                                    quantity_a_b = best_min_quan
                                    best_cus = p
                                    best_veh = k
                if best_cus != 0:
                    L_s.add(cur_vehs[best_veh].Route[best_cus])
                    cur_vehs[best_veh].random_del(best_cus)

        #7.基于历史信息的点删除(HR)
        if p_1 == 6:
            for i in range(n):
                #距离差
                min_distance = np.inf
                dis_distance = 0
#                #找到最优点及其最优位置
#                min_best_cus = min_best_veh = 0
                #删除点，及其位置
                best_cus = best_veh = 0
                for k in range(len(cur_vehs)):
                    if len(cur_vehs[k].Route) >= 3:
                        for p in range(1,len(cur_vehs[k].Route)-1):
                            cur_distance = cur_vehs[k].distance_sum(p)
                            if cur_distance < min_distance:
                                min_distance = cur_distance
                for k in range(len(cur_vehs)):
                    if len(cur_vehs[k].Route) >= 3:
                        for p in range(1,len(cur_vehs[k].Route)-1):
                            cur_distance = cur_vehs[k].distance_sum(p)
                            if cur_distance - min_distance > dis_distance:
                                dis_distance = cur_distance - min_distance
                                best_cus = p
                                best_veh = k
                L_s.add(cur_vehs[best_veh].Route[best_cus])
                cur_vehs[best_veh].random_del(best_cus)
#        #8.最远点删除（FDR）
#        if p_1 == 8:
#            for i in range(n):
#                random_route_num = random.randint(0,veh_num-1)
#                while len(cur_vehs[random_route_num].Route) <= 2:#长度要大于2
#                    random_route_num = random.randint(0,veh_num-1)
#                TRoute_k = len(cur_vehs[random_route_num])
                    
        #9.基于加油站的需求点删除（SR）
        if p_1 == 7:
            for i in range(n):
                random_gas = random.randint(1,len(nodes)-1)
                for k in range(len(cur_vehs)):
                    for p in range(1,len(cur_vehs[k].Route)-1):
                        if cur_vehs[k].Route[p][0] == random_gas:
                            L_s.add(cur_vehs[k].Route[p])
                for i in L_s:
                    for k in range(len(cur_vehs)):
                        if i in cur_vehs[k].Route:
                            cur_vehs[k].del_node_by_node(i)

                        

        p_2 = random.randint(1,4)
#        p_2 = 1
        #插入操作
        #1.贪婪插入（GI）
        if p_2 == 1:
            for ls in L_s:#遍历待分配点
                neigbor_best_obj = np.inf
                #最优插入客户，最优插入车辆
                best_cus = best_veh = 0
                
                for k in range(len(cur_vehs)):
                    #如果载重量允许
                    if cur_vehs[k].load[ls[1]] + nodes[ls[0]].demand[ls[1]] <= cur_vehs[k].cap[ls[1]]:
                        sub_route = get_node_num(cur_vehs[k].Route,ls[1])
                        sub_before = get_node_num(cur_vehs[k].Route,ls[1]-1)
                        sub_before_1 = get_node_num(cur_vehs[k].Route,ls[1]-2)
                        sub_after = get_node_num(cur_vehs[k].Route,ls[1]+1)
                        sub_after_1 = get_node_num(cur_vehs[k].Route,ls[1]+2)
                        if sub_route:#带插入路径中有同种需求的点
                            first = cur_vehs[k].Route.index(sub_route[0])
                            last = cur_vehs[k].Route.index(sub_route[-1])+1
                            for p in range(first,last+1):
                                cur_vehs[k].insert_node(ls,p)
                                if cur_vehs[k].r_k <= T_s:
                                    insert_obj = cal_obj(cur_vehs)
                                    if insert_obj < neigbor_best_obj:
                                        neigbor_best_obj = insert_obj
                                        best_cus = ls
                                        best_veh = k
                                        best_pos = p
                                    cur_vehs[k].del_node_by_node(ls)
                                else:
                                    cur_vehs[k].del_node_by_node(ls)
                        else:
                            if not sub_before + sub_before_1:
                                p = 1

                            elif not sub_after + sub_after_1:
                                p = -1

                            else:
                                p = cur_vehs[k].Route.index(sub_before[-1])+1
                            cur_vehs[k].insert_node(ls,p)
                            if cur_vehs[k].r_k <= T_s:
                                insert_obj = cal_obj(cur_vehs)
                                if insert_obj < neigbor_best_obj:
                                    neigbor_best_obj = insert_obj
                                    best_cus = ls
                                    best_veh = k
                                    best_pos = p
                                cur_vehs[k].del_node_by_node(ls)
                            else:
                                cur_vehs[k].del_node_by_node(ls)
                #否则加一条新路径
                if best_cus != 0:
                    cur_vehs[best_veh].insert_node(best_cus,best_pos)
                else:
                    add_r = Vehicle(1,capacity_list)
                    add_r.Route.extend([(0,0),(0,0)])
                    add_r.insert_node(ls,1)
                    cur_vehs.append(add_r)
            K = []
            for k in range(len(cur_vehs)):
                if len(cur_vehs[k].Route) == 2:
                    K.append(cur_vehs[k])
            for k in K:
                cur_vehs.remove(k)
            neigbor_best_obj = cal_obj(cur_vehs)
        #2.后悔值插入（RI）没有按油品种类插入
        if p_2 == 2:
            while L_s:
                dis_c = 0
                #最优插入客户，最优插入车辆
                best_cus = best_veh = 0
                best_cus_1 = best_veh_1 = 0
                for ls in L_s:
                    #差值
                    first_c = np.inf
                    second_c = np.inf
                    
                    for k in range(len(cur_vehs)):
                        #如果载重量允许
                        if cur_vehs[k].load[ls[1]] + nodes[ls[0]].demand[ls[1]] <= cur_vehs[k].cap[ls[1]]:
                            sub_route = get_node_num(cur_vehs[k].Route,ls[1])
                            sub_before = get_node_num(cur_vehs[k].Route,ls[1]-1)
                            sub_before_1 = get_node_num(cur_vehs[k].Route,ls[1]-2)
                            sub_after = get_node_num(cur_vehs[k].Route,ls[1]+1)
                            sub_after_1 = get_node_num(cur_vehs[k].Route,ls[1]+2)
                            if sub_route:#带插入路径中有同种需求的点
                                first = cur_vehs[k].Route.index(sub_route[0])
                                last = cur_vehs[k].Route.index(sub_route[-1])+1
                                for p in range(first,last+1):
                                    cur_vehs[k].insert_node(ls,p) #插入点(p是位置)
                                    if cur_vehs[k].r_k <= T_s:
                                        first_cost = cal_obj(cur_vehs)
                                        cur_vehs[k].del_node_by_node(ls)
                                        if first_cost < first_c:
                                            first_c = first_cost
                                            best_cus_1 = ls
                                            best_veh_1 = k
                                            best_pos_1 = p
                                    else:
                                        cur_vehs[k].del_node_by_node(ls)
                            else:
                                if not sub_before + sub_before_1:
                                    p = 1
                                    
                                elif not sub_after + sub_after_1:
                                    p = -1
                                    
                                else:
                                    p = cur_vehs[k].Route.index(sub_before[-1])+1
                                cur_vehs[k].insert_node(ls,p)
                                if cur_vehs[k].r_k <= T_s:
                                    first_cost = cal_obj(cur_vehs)
                                    cur_vehs[k].del_node_by_node(ls)
                                    if first_cost < first_c:
                                        first_c = first_cost
                                        best_cus_1 = ls
                                        best_veh_1 = k
                                        best_pos_1 = p
                                else:
                                    cur_vehs[k].del_node_by_node(ls)
                    for k in range(len(cur_vehs)):
                        #如果载重量允许
                        if cur_vehs[k].load[ls[1]] + nodes[ls[0]].demand[ls[1]] <= cur_vehs[k].cap[ls[1]]:
                            sub_route = get_node_num(cur_vehs[k].Route,ls[1])
                            sub_before = get_node_num(cur_vehs[k].Route,ls[1]-1)
                            sub_before_1 = get_node_num(cur_vehs[k].Route,ls[1]-2)
                            sub_after = get_node_num(cur_vehs[k].Route,ls[1]+1)
                            sub_after_1 = get_node_num(cur_vehs[k].Route,ls[1]+2)
                            if sub_route:#带插入路径中有同种需求的点
                                first = cur_vehs[k].Route.index(sub_route[0])
                                last = cur_vehs[k].Route.index(sub_route[-1])+1
                                for p in range(first,last+1):
                                    if p != best_pos_1 or k != best_veh_1:
                                        cur_vehs[k].insert_node(ls,p) #插入点(p是位置)
                                        if cur_vehs[k].r_k <= T_s:
                                            second_cost = cal_obj(cur_vehs)
                                            cur_vehs[k].del_node_by_node(ls)
                                            if second_cost < second_c:
                                                second_c = second_cost
                                        else:
                                            cur_vehs[k].del_node_by_node(ls)
                            else:
                                if not sub_before + sub_before_1:
                                    p = 1
                                elif not sub_after + sub_after_1:
                                    p = -1
                                else:
                                    p = cur_vehs[k].Route.index(sub_before[-1])+1
                                if p != best_pos_1 or k != best_veh_1:
                                    cur_vehs[k].insert_node(ls,p)
                                    if cur_vehs[k].r_k <= T_s:
                                        second_cost = cal_obj(cur_vehs)
                                        cur_vehs[k].del_node_by_node(ls)
                                        if second_cost < second_c:
                                            second_c = second_cost
                                    else:
                                        cur_vehs[k].del_node_by_node(ls)
                    if second_c - first_c > dis_c:
                        dis_c = second_c - first_c
                        best_cus = best_cus_1
                        best_veh = best_veh_1
                        best_pos = best_pos_1
                if best_cus != 0:
                    L_s.remove(best_cus)
                    cur_vehs[best_veh].insert_node(best_cus,best_pos)
                else:
                    add_r = Vehicle(1,capacity_list)
                    add_r.Route.extend([(0,0),(0,0)])
                    add_r.insert_node(ls,1)
                    L_s.remove(ls)
                    cur_vehs.append(add_r)
            K = []
            for k in range(len(cur_vehs)):
                if len(cur_vehs[k].Route) == 2:
                    K.append(cur_vehs[k])
            for k in K:
                cur_vehs.remove(k)
            neigbor_best_obj = cal_obj(cur_vehs)
            
        #3.带扰动的贪婪插入（GIN）
        if p_2 == 3:
            d_distance = distance_matrix.max()
            for ls in L_s:#遍历待分配点
                neigbor_best_obj = np.inf
                #最优插入客户，最优插入车辆
                best_cus = best_veh = 0
                
                for k in range(len(cur_vehs)):
                    #如果载重量允许
                    if cur_vehs[k].load[ls[1]] + nodes[ls[0]].demand[ls[1]] <= cur_vehs[k].cap[ls[1]]:
                        sub_route = get_node_num(cur_vehs[k].Route,ls[1])
                        sub_before = get_node_num(cur_vehs[k].Route,ls[1]-1)
                        sub_before_1 = get_node_num(cur_vehs[k].Route,ls[1]-2)
                        sub_after = get_node_num(cur_vehs[k].Route,ls[1]+1)
                        sub_after_1 = get_node_num(cur_vehs[k].Route,ls[1]+2)
                        if sub_route:#带插入路径中有同种需求的点
                            first = cur_vehs[k].Route.index(sub_route[0])
                            last = cur_vehs[k].Route.index(sub_route[-1])+1
                            for p in range(first,last+1):
                                cur_vehs[k].insert_node(ls,p)
                                if cur_vehs[k].r_k <= T_s:
                                    ep = random.uniform(-1,1)
                                    distribute_obj = cal_obj(cur_vehs)+d_distance*mu*ep#扰动项
                                    if distribute_obj < neigbor_best_obj:
                                        insert_obj = cal_obj(cur_vehs)
                                        neigbor_best_obj = insert_obj
                                        best_cus = ls
                                        best_veh = k
                                        best_pos = p
                                    cur_vehs[k].random_del(p)
                                else:
                                    cur_vehs[k].random_del(p)
                        else:
                            if not sub_before + sub_before_1:
                                p = 1
                                cur_vehs[k].insert_node(ls,p)
                            elif not sub_after + sub_after_1:
                                p = -1
                                cur_vehs[k].insert_node(ls,p)
                            else:
                                p = cur_vehs[k].Route.index(sub_before[-1])+1
                                cur_vehs[k].insert_node(ls,p)
                            if cur_vehs[k].r_k <= T_s:
                                ep = random.uniform(-1,1)
                                distribute_obj = cal_obj(cur_vehs)+d_distance*mu*ep#扰动项
                                if distribute_obj < neigbor_best_obj:
                                    insert_obj = cal_obj(cur_vehs)
                                    neigbor_best_obj = insert_obj
                                    best_cus = ls
                                    best_veh = k
                                    best_pos = p
                                cur_vehs[k].del_node_by_node(ls)
                            else:
                                cur_vehs[k].del_node_by_node(ls)
                if best_cus != 0:
                    cur_vehs[best_veh].insert_node(best_cus,best_pos)               
                else:
                    add_r = Vehicle(1,capacity_list)
                    add_r.Route.extend([(0,0),(0,0)])
                    add_r.insert_node(ls,1)
                    cur_vehs.append(add_r)
            K = []
            for k in range(len(cur_vehs)):
                if len(cur_vehs[k].Route) == 2:
                    K.append(cur_vehs[k])
            for k in K:
                cur_vehs.remove(k)
            neigbor_best_obj = cal_obj(cur_vehs)
        #4.带扰动的后悔值插入
        if p_2 == 4:
            d_distance = distance_matrix.max()
            while L_s:
                dis_c = 0
                #最优插入客户，最优插入车辆
                best_cus = best_veh = 0
                best_cus_1 = best_veh_1 = 0
                for ls in L_s:
                    #差值
                    first_c = np.inf
                    second_c = np.inf
                    
                    for k in range(len(cur_vehs)):
                        #如果载重量允许
                        if cur_vehs[k].load[ls[1]] + nodes[ls[0]].demand[ls[1]] <= cur_vehs[k].cap[ls[1]]:
                            sub_route = get_node_num(cur_vehs[k].Route,ls[1])
                            sub_before = get_node_num(cur_vehs[k].Route,ls[1]-1)
                            sub_before_1 = get_node_num(cur_vehs[k].Route,ls[1]-2)
                            sub_after = get_node_num(cur_vehs[k].Route,ls[1]+1)
                            sub_after_1 = get_node_num(cur_vehs[k].Route,ls[1]+2)
                            if sub_route:#带插入路径中有同种需求的点
                                first = cur_vehs[k].Route.index(sub_route[0])
                                last = cur_vehs[k].Route.index(sub_route[-1])+1
                                for p in range(first,last+1):
                                    cur_vehs[k].insert_node(ls,p) #插入点(p是位置)
                                    if cur_vehs[k].r_k <= T_s:
                                        first_cost = cal_obj(cur_vehs)
                                        cur_vehs[k].del_node_by_node(ls)
                                        if first_cost < first_c:
                                            first_c = first_cost
                                            best_cus_1 = ls
                                            best_veh_1 = k
                                            best_pos_1 = p
                                    else:
                                        cur_vehs[k].del_node_by_node(ls)
                            else:
                                if not sub_before + sub_before_1:
                                    p = 1

                                elif not sub_after + sub_after_1:
                                    p = -1

                                else:
                                    p = cur_vehs[k].Route.index(sub_before[-1])+1
                                cur_vehs[k].insert_node(ls,p)
                                if cur_vehs[k].r_k <= T_s:
                                    first_cost = cal_obj(cur_vehs)
                                    cur_vehs[k].del_node_by_node(ls)
                                    if first_cost < first_c:
                                        first_c = first_cost
                                        best_cus_1 = ls
                                        best_veh_1 = k
                                        best_pos_1 = p
                                else:
                                    cur_vehs[k].del_node_by_node(ls)
                    for k in range(len(cur_vehs)):
                        #如果载重量允许
                        if cur_vehs[k].load[ls[1]] + nodes[ls[0]].demand[ls[1]] <= cur_vehs[k].cap[ls[1]]:
                            sub_route = get_node_num(cur_vehs[k].Route,ls[1])
                            sub_before = get_node_num(cur_vehs[k].Route,ls[1]-1)
                            sub_before_1 = get_node_num(cur_vehs[k].Route,ls[1]-2)
                            sub_after = get_node_num(cur_vehs[k].Route,ls[1]+1)
                            sub_after_1 = get_node_num(cur_vehs[k].Route,ls[1]+2)
                            if sub_route:#带插入路径中有同种需求的点
                                first = cur_vehs[k].Route.index(sub_route[0])
                                last = cur_vehs[k].Route.index(sub_route[-1])+1
                                for p in range(first,last+1):
                                    if p != best_pos_1 or k != best_veh_1:
                                        cur_vehs[k].insert_node(ls,p) #插入点(p是位置)
                                        if cur_vehs[k].r_k <= T_s:
                                            second_cost = cal_obj(cur_vehs)
                                            cur_vehs[k].del_node_by_node(ls)
                                            if second_cost < second_c:
                                                second_c = second_cost
                                        else:
                                            cur_vehs[k].del_node_by_node(ls)
                            else:
                                if not sub_before + sub_before_1:
                                    p = 1
                                elif not sub_after + sub_after_1:
                                    p = -1
                                else:
                                    p = cur_vehs[k].Route.index(sub_before[-1])+1
                                if p != best_pos_1 or k != best_veh_1:
                                    cur_vehs[k].insert_node(ls,p)
                                    if cur_vehs[k].r_k <= T_s:
                                        second_cost = cal_obj(cur_vehs)
                                        cur_vehs[k].del_node_by_node(ls)
                                        if second_cost < second_c:
                                            second_c = second_cost
                                    else:
                                        cur_vehs[k].del_node_by_node(ls)
                    ep = random.uniform(-1,1)#扰动项
                    if second_c - first_c + d_distance*mu*ep >= dis_c:
                        dis_c = second_c - first_c
                        best_cus = best_cus_1
                        best_veh = best_veh_1
                        best_pos = best_pos_1
                if best_cus != 0:
                    L_s.remove(best_cus)
                    cur_vehs[best_veh].insert_node(best_cus,best_pos)
                else:
                    add_r = Vehicle(1,capacity_list)
                    add_r.Route.extend([(0,0),(0,0)])
                    add_r.insert_node(ls,1)
                    L_s.remove(ls)
                    cur_vehs.append(add_r)
            K = []
            for k in range(len(cur_vehs)):
                if len(cur_vehs[k].Route) == 2:
                    K.append(cur_vehs[k])
            for k in K:
                cur_vehs.remove(k)
            neigbor_best_obj = cal_obj(cur_vehs)
        #更新阶段     
        if neigbor_best_obj < cal_obj(cur_best_vehs):
            cur_best_obj = neigbor_best_obj
            cur_best_vehs = [copy.copy(cur_vehs[i]) for i in range(len(cur_vehs))]
            for i in range(len(cur_vehs)):
                cur_best_vehs[i].Route = copy.copy(cur_vehs[i].Route)
        else:
            v = np.exp(-(cur_best_obj-neigbor_best_obj)/T)
            R = random.random()
            if R < v:
                cur_best_obj = neigbor_best_obj
                cur_best_vehs = [copy.copy(cur_vehs[i]) for i in range(len(cur_vehs))]
                for i in range(len(cur_vehs)):
                    cur_best_vehs[i].Route = copy.copy(cur_vehs[i].Route)
        #如果当前解优于最优解
        if cur_best_obj < global_best_obj:
            global_best_obj = cur_best_obj
            global_best_vehs = cur_best_vehs
        cur_vehs = [copy.copy(cur_best_vehs[i]) for i in range(len(cur_best_vehs))]
        for i in range(len(cur_best_vehs)):
            cur_vehs[i].Route = copy.copy(cur_best_vehs[i].Route)
        T *= h
    return global_best_vehs,global_best_obj



