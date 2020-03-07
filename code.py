class Rtree:
    def __init__(self):
        self.root = Node()
    def search(self, n, range_query): # rtree search: traversing through the tree and identify points
        count = 0
        if n.check_leaf_condition():
            for p in n.data_points:
                if range_query['x1']<= p['x'] <= range_query['x2'] and range_query['y1'] <= p['y'] <= range_query['y2']:
                    count+=1
        else:
            for n in n.children:
                if self.check_intersections(n, range_query):
                    count+=self.search(n, range_query)
        return count

    def check_intersections(self, node, q): # Checks whether the mbr of node intersects with the mbr of query
        c1_x,c1_y = (node.min_bound['x2'] + node.min_bound['x1'])*0.5,(node.min_bound['y2'] + node.min_bound['y1'])*0.5
        len_1,breadth_1= node.min_bound['x2'] - node.min_bound['x1'],node.min_bound['y2'] - node.min_bound['y1']
        len_2,breadth_2= q['x2'] - q['x1'],q['y2'] - q['y1']
        c2_x,c2_y  = 0.5*(q['x2'] + q['x1']),0.5*(q['y2'] + q['y1'])
        return(abs(c1_x - c2_x) <= (len_1+len_2)/2 and abs(c1_y-c2_y) <= (breadth_1+breadth_2)/2)

             

    def insert(self, n, p):     # wrapper for insert
        if n.check_leaf_condition():
            self.add_points(n, p)
            if n.overflow_report():
                self.overflow_call(n)
        else:
            v = self.select_optimal_subtree(n, p)
            self.insert(v, p)
            self.update_min_bound(v)


    
    def select_optimal_subtree(self, n, p): # Traverses through feasible subtree
        if n.check_leaf_condition():
            return n
        else:
            min_change = 999999999
            next_node = None
            for i in n.children:
                if min_change > self.changein_perimeter(i, p):
                    min_change= self.changein_perimeter(i, p)
                    next_node = i
            
            return next_node

    def changein_perimeter(self, n, p):     # calculates the increment in perimeter
       
        x1=min([n.min_bound['x1'],n.min_bound['x2'],p['x']])
        x2=max([n.min_bound['x1'],n.min_bound['x2'],p['x']])
        y1=min([n.min_bound['y1'],n.min_bound['y2'],p['y']])
        y2=max([n.min_bound['y1'],n.min_bound['y2'],p['y']])
        increase = (x2-x1)+(y2-y1) - n.get_perimeter()
        return increase

    def overflow_call(self, n):     # Handles the overflow cases
        node1, node2 = self.node_split(n)
        if n.check_root_condition():
            root = Node()
            self.insert_child(root, node1)
            self.insert_child(root, node2)
            self.root = root
            self.update_min_bound(root)
        else:
            w = n.predecessor
            w.children.remove(n)
            self.insert_child(w, node1)
            self.insert_child(w, node2)
            if w.overflow_report():
                self.overflow_call(w)
            self.update_min_bound(w)

    def node_split(self, n): 
        node1 = Node()
        node2 = Node()
        minimum_perimeter = 9999999999
        if n.check_leaf_condition():
            m = n.data_points.__len__()
            sample = [sorted(n.data_points, key=lambda data_point: data_point['x']),sorted(n.data_points, key=lambda data_point: data_point['y'])]
            flag=1
        else:
            m = n.children.__len__()
            sample = [sorted(n.children, key=lambda child_node: child_node.min_bound['x1']),sorted(n.children, key=lambda child_node: child_node.min_bound['x2']),sorted(n.children, key=lambda child_node: child_node.min_bound['y1']),sorted(n.children, key=lambda child_node: child_node.min_bound['y2'])]
            
            flag=0
        node1,node2=self.optimal_node_split(sample,m,minimum_perimeter,flag)
        for node in node1.children:
            node.predecessor = node1
        for node in node2.children:
            node.predecessor = node2

        return node1, node2
    def optimal_node_split(self,sample,m,minimum_perimeter,flag): # finds out the optimal split 
        if flag:
            for points in sample:
                for i in range(ceil(0.4*B),m-ceil(0.4*B)+1):
                    temp_node1 = Node()   
                    temp_node2 = Node()     
                    temp_node1.data_points = points[0: i]
                    temp_node2.data_points = points[i: points.__len__()]
                    self.update_min_bound(temp_node1)
                    self.update_min_bound(temp_node2)
                    if minimum_perimeter > temp_node1.get_perimeter() + temp_node2.get_perimeter():
                        minimum_perimeter = temp_node1.get_perimeter() + temp_node2.get_perimeter()
                        node1,node2 = temp_node1,temp_node2
                        
        else:
            for points in sample:
                for i in range(ceil(0.4 * B), m - ceil(0.4 * B) + 1):
                    temp_node1 = Node()
                    temp_node2 = Node()
                    temp_node1.children = points[0: i]
                    temp_node2.children = points[i: points.__len__()]
                    self.update_min_bound(temp_node1)
                    self.update_min_bound(temp_node2)
                    if minimum_perimeter > temp_node1.get_perimeter() + temp_node2.get_perimeter():
                        minimum_perimeter = temp_node1.get_perimeter() + temp_node2.get_perimeter()
                        node1,node2 = temp_node1,temp_node2
            
        return(node1,node2)

    def insert_child(self, parent, child):  # insert a node to a node
        parent.children.append(child)
        child.predecessor = parent
        
        parent.min_bound['x1'] =get_minimum(parent.min_bound['x1'],child.min_bound['x1'])    
        parent.min_bound['x2'] =get_maximum(parent.min_bound['x2'],child.min_bound['x2'])
        parent.min_bound['y1'] =get_minimum(parent.min_bound['y1'],child.min_bound['y1'])    # get_maximum
        parent.min_bound['y2'] =get_maximum(parent.min_bound['y2'],child.min_bound['y2'])

    def add_points(self, parent, data_point):   #adds data points to a leaf node
        parent.data_points.append(data_point)
        parent.min_bound['x1'] = get_minimum(parent.min_bound['x1'],data_point['x']) 
        parent.min_bound['x2'] = get_maximum(parent.min_bound['x2'],data_point['x'])
        parent.min_bound['y1'] = get_minimum(parent.min_bound['y1'],data_point['y'])
        parent.min_bound['y2'] = get_maximum(parent.min_bound['y2'],data_point['y'])

    def update_min_bound(self, n):  # updates MBR of a node
        x_coordinates,y_coordinates=[],[]   
        if len(n.children)==0:
            x_coordinates = [i['x'] for i in n.data_points]
            y_coordinates = [i['y'] for i in n.data_points]
        else:
            x_coordinates =[i.min_bound['x1'] for i in n.children] + [j.min_bound['x2'] for j in n.children]
            y_coordinates =[i.min_bound['y1'] for i in n.children] + [j.min_bound['y2'] for j in n.children]
        n.min_bound ={'x1':min(x_coordinates),'x2':max(x_coordinates),'y1':min(y_coordinates),'y2':max(y_coordinates)}

def sequential_search_query(points,search_query):
    count=0
    for i,j in zip(points['x'],points['y']):
        if search_query['x1'] <= i <= search_query['x2'] and search_query['y1'] <=j<= search_query['y2']:
            count+= 1
    return count
def get_maximum(x,y): # returns( maximum of two values
    if x<y:
        return(y)
    else:
        return(x)
def get_minimum(x,y):   # returns minimum of two values
    if x<y:
        return(x)
    else:
        return(y)
class Node:
    def __init__(self):
        self.children=[]
        self.data_points=[]
        self.predecessor= None
        self.min_bound={'x1':-1,'y1':-1,'x2':-1,'y2':-1}

    def get_perimeter(self): 
        return ((self.min_bound['x2'] -self.min_bound['x1'])+(self.min_bound['y2']-self.min_bound['y1']))

    def overflow_report(self):  # checks overflow condition
        if self.check_leaf_condition():
            return(self.data_points.__len__()>B)
        else:
            return(self.children.__len__()>B)
    def check_root_condition(self): # checks whether it is a root node
        return(self.predecessor is None)

    def check_leaf_condition(self): # checks whether it is a leaf node
        return(self.children.__len__()==0)


## main funtion

import pandas as pd;
from math import ceil
from tqdm import tqdm;
import sys;
B = 4
# importing data from the text files
input1=open("C:/Users/Tarun/Desktop/"+sys.argv[1],"r")
input2=open("C:/Users/Tarun/Desktop/"+sys.argv[2],"r")
range_query=[]
raw_data=[];data=[]
for i in input1.readlines():
    raw_data.append([int(x) for x in i.split(" ")])
for i in input2.readlines():
    range_query.append([int(x) for x in i.split(" ")])
number_instances=int(raw_data[0][0])
for i in range(1,number_instances+1):
    data.append(raw_data[i][1:])
data=pd.DataFrame(data,columns=['x','y'])
range_query=pd.DataFrame(range_query,columns=['x1','x2','y1','y2'])

# creating a rtree
rtree_ob=Rtree()
print("Creating r tree:")
for i in tqdm(range(number_instances)):
    rtree_ob.insert(rtree_ob.root,data.iloc[i,:])
res=[]
print(rtree_ob.root)

## querying r tree search
import time
zab=[]
print(zab)
print("R tree Search:")
start_time1=time.time()
for i in tqdm(range(len(range_query))):
    zab.append(rtree_ob.search(rtree_ob.root,range_query.iloc[i,:]))
end_time1=time.time()
print("Time taken by rtree algorithm to search: {}".format(end_time1-start_time1))
avg1=(end_time1-start_time1)/len(range_query)
print("Average Time taken by rtree algorithm to search: {}".format(avg1))
print(zab)

## Sequential search query is a simple linear search algorithm which exhaustively iterates through each data point in the dimensional space and returns the number of points that lie in the given range query.
q=[]
start_time2=time.time()
print(type(data))
for i in tqdm(range(len(range_query))):
    q.append(sequential_search_query(data,range_query.iloc[i,:]))
print(q)
end_time2=time.time()
print("Time taken by Sequenial algorithm to search: {}".format(end_time2-start_time2))
avg2=(end_time2-start_time2)/len(range_query)
print("Average Time taken by Sequential algorithm to search: {}".format(avg2))
print("#################################################################################################################################################")
print("Rtree search algorithm is {}* times faster than sequential search".format(avg2/avg1))
