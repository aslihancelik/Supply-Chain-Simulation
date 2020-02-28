# coding: utf-8

# In[58]:

import numpy as np
import math
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

INIT_INV = 0
ITEM_REC = 1
ITEM_ON_HAND = 2
ORD_REC = 3 #ORDER RECEIVED
ITEM_OWED = 4
ITEM_SENT = 5
FIN_INV = 6
ITEM_ORD = 7
INV_POS = 8
FORECAST = 9

L=0 #LEADTIME

order = np.zeros((1, 9))
order = [10, 9, 12, 8, 11, 9, 12, 8, 11]

class  Simulation:
    def __init__(self, total_time_steps, entities, method):
        self.current_time_step = 0
        self.entities = entities
        self.total_time_steps = total_time_steps
        self.method = method

    def run_simulation(self):
        for i in range(self.total_time_steps):
            self.advance_time_step()
            
    def advance_time_step(self):
#        print("time step: "+ str(self.current_time_step))
    
        for entity_object in self.entities:
            #call all columns
            entity_object.initInv(self.current_time_step)
            entity_object.orderRec(self.current_time_step)
            entity_object.forecast(self.current_time_step, self.method)
            
            entity_object.itemRec(self.current_time_step)
            entity_object.itemOnHand(self.current_time_step)
            
            entity_object.itemsOwed(self.current_time_step)
            
            entity_object.itemRecManuf(self.current_time_step)
            entity_object.itemSent(self.current_time_step)
            
            entity_object.finalInv(self.current_time_step)
            entity_object.invPos(self.current_time_step)
   
            entity_object.itemOrder(self.current_time_step, self.method)
            
        self.current_time_step += 1

class Entity:
    def __init__(self, name, customer, initial_inventory, lead_time):
        self.name = name
        self.table = np.zeros((3000,10))
        self.customer = customer
        self.initial_inventory = initial_inventory    
        self.lead_time = lead_time
 

    def initInv(self, time_step):
        if(time_step == 0):
            self.table[0][INIT_INV] = self.initial_inventory
        else:
            self.table[time_step, INIT_INV] = self.table[time_step-1, FIN_INV]
            
    def orderRec(self,time_step):  #items ordered = my forecast and orderRec = customer's forecast
        if(time_step > 0):
            if(self.name == "retailer"):
                self.table[time_step,ORD_REC] = order[(time_step-1) % len(order)]
            else:
                self.table[time_step,ORD_REC] = self.customer.table[time_step-1,ITEM_ORD]
        
        
    def forecast(self, time_step, method):
        if(time_step == 0):
            self.table[1, FORECAST] = 10 #forecast at time zero
        else:
            self.table[time_step+1, FORECAST] = self.table[time_step, FORECAST]*(1-alpha)+ alpha* self.table[time_step, ORD_REC]
    
    def itemRec(self, time_step):
        if(time_step > 0):
            if (self.lead_time>0 and time_step <= self.lead_time):
                self.table[time_step,ITEM_REC]=10
                
            
    def itemOnHand(self, time_step):  #items on hand= initial inventory + items received
        self.table[time_step,ITEM_ON_HAND] = max(self.table[time_step,INIT_INV], 0)+ self.table[time_step,ITEM_REC]
        
    def itemsOwed(self, time_step):
        self.table[time_step,ITEM_OWED] = max(self.table[time_step,ORD_REC], self.table[time_step,ORD_REC] - self.table[time_step,INIT_INV])
        
    def itemSent(self, time_step):
        quantity_to_send = min(self.table[time_step][ITEM_ON_HAND],self.table[time_step][ITEM_OWED])
        self.table[time_step][ITEM_SENT] = quantity_to_send
        if(self.name != "retailer"):
            self.customer.table[time_step+self.lead_time][ITEM_REC] = quantity_to_send
            
        
    def itemRecManuf(self, time_step):
        if(self.name == "manufacturer"):
           self.table[time_step][ITEM_REC] = self.table[max(0,time_step-self.lead_time-1)][ITEM_ORD]
    
    def finalInv(self, time_step):
        
        self.table[time_step,FIN_INV] = self.table[time_step][ITEM_ON_HAND]- self.table[time_step,ORD_REC]

        
    def invPos(self, time_step):
        if(time_step == 0):
            self.table[0][INV_POS] = 10+self.lead_time*10
        else:
            itemExp =sum(self.table[max(0,time_step-self.lead_time):time_step+1,ITEM_ORD])
            self.table[time_step,INV_POS] = self.table[time_step,FIN_INV]  + itemExp
        
    def itemOrder(self, time_step, method):
        if(method == "ES1"):
            if(time_step == 0):
                self.table[time_step, ITEM_ORD] = 10
            else:
                self.table[time_step,ITEM_ORD]= max((self.lead_time+1)*self.table[time_step+1, FORECAST]-self.table[time_step, INV_POS], 0)
            
        if(method == "ES2"):     
            if(time_step == 0):
                self.table[time_step, ITEM_ORD] = 10
            
            elif(time_step == 1):
                variance=0
            
            else:
                
                variance = np.std(self.table[1:time_step,ORD_REC])**2
                self.table[time_step,ITEM_ORD] = max((self.lead_time+1)*self.table[time_step+1, FORECAST] + 2.33 * math.sqrt((self.lead_time+1)*variance)- self.table[time_step,INV_POS], 0)
        if(method == "ES3"):

            if(time_step == 0):
                self.table[time_step, ITEM_ORD] = 10
                
            elif(time_step == 1):
                variance=0
            else:

                variance = np.std(self.table[1:time_step,ORD_REC])**2
                z_score = 0.84  #from newsvendor
                basestock = self.table[time_step+1, FORECAST] + z_score * (math.sqrt(variance))
                self.table[time_step,ITEM_ORD] = max(basestock-self.table[time_step,INV_POS], 0)
                

time_steps = 2000
alphas = np.linspace(0.01, 1.0, num=99)

stds_I_retailer     = []
stds_I_wholesaler   = []
stds_I_distributor  = []
stds_I_manufacturer = []

stds_O_retailer     = []
stds_O_wholesaler   = []
stds_O_distributor  = []
stds_O_manufacturer = []

for alpha in alphas:
    #print(running for alph)
    retailer = Entity("retailer", None, 10, L)
    wholesaler = Entity("wholesaler",retailer , 10, L)
    distributor = Entity("distributor", wholesaler, 10, L)
    manufacturer = Entity("manufacturer", distributor, 10, L)

    main_simulation = Simulation(time_steps, [manufacturer, distributor, wholesaler, retailer], "ES1")
    main_simulation.run_simulation()

    stds_I_retailer.append(np.std(retailer.table[1000:time_steps,        FIN_INV]))
    stds_I_wholesaler.append(np.std(wholesaler.table[1000:time_steps,    FIN_INV]))
    stds_I_distributor.append(np.std(distributor.table[1000:time_steps,  FIN_INV]))
    stds_I_manufacturer.append(np.std(manufacturer.table[1000:time_steps,FIN_INV]))

    stds_O_retailer.append(np.std(retailer.table[1000:time_steps,ITEM_ORD]))
    stds_O_wholesaler.append(np.std(wholesaler.table[1000:time_steps,ITEM_ORD]))
    stds_O_distributor.append(np.std(distributor.table[1000:time_steps,ITEM_ORD]))
    stds_O_manufacturer.append(np.std(manufacturer.table[1000:time_steps,ITEM_ORD]))


plt.figure(1)
plt.plot(alphas,stds_I_retailer   ,  label="std retailer")
plt.plot(alphas,stds_I_wholesaler ,  label="std wholesaler")
plt.plot(alphas,stds_I_distributor,  label="std distributor")
plt.plot(alphas,stds_I_manufacturer, label="std manufacturer")
plt.xlabel("Alphas")
plt.ylabel("Std of Final Inventory")
plt.legend()
plt.title("Standard Deviation of Final inventory vs Alphas")


plt.figure(2)
plt.plot(alphas,stds_O_retailer   ,  label="std retailer")
plt.plot(alphas,stds_O_wholesaler ,  label="std wholesaler")
plt.plot(alphas,stds_O_distributor,  label="std distributor")
plt.plot(alphas,stds_O_manufacturer, label="std manufacturer")
plt.xlabel("Alphas")
plt.ylabel("Std of Orders")
plt.legend()
plt.title("Standard Deviation of Orders vs Alphas")

#plt.show()

#plt.figure(3)
##plt.plot(retailer.table[1000:2000,ITEM_ORD])
##plt.plot(wholesaler.table[1000:2000,ITEM_ORD])
##plt.plot(distributor.table[1000:2000,ITEM_ORD])
##plt.plot(manufacturer.table[1000:2000,ITEM_ORD])
#plt.xlabel("Time")
#plt.ylabel("Orders")
#plt.legend()
#plt.title("Orders vs Time")

#plt.show()


#final inventory vs time#
#plt.figure(4)
##plt.plot(retailer.table[1000:2000,FIN_INV])
##plt.plot(wholesaler.table[1000:2000,FIN_INV])
##plt.plot(distributor.table[1000:2000,FIN_INV])
##plt.plot(manufacturer.table[1000:2000,FIN_INV])
#plt.xlabel("Time")
#plt.ylabel("Final Inventory")
#plt.legend()
#plt.title("Final Inventory vs Time")

plt.show()
    


plt.figure(figsize = (30, 5))

col_string =["I_IN",
"It.REC",
"It.HAn",
"OR.RE", #ORDER RECEIVED
"I.OWE",
"I.SEN",
"F_In",
"It.OR",
"IP",
"FOR"]
#

print("retailer")
df = pd.DataFrame(data=(retailer.table[0:time_steps+1,:].astype(int)), index=["t="+str(i) for i in range(time_steps+1)], columns=col_string)
print(df)

print("wholesaler")
df = pd.DataFrame(data=wholesaler.table[0:time_steps+1,:].astype(int), index=["t="+str(i) for i in range(time_steps+1)], columns=col_string)
print(df)

print("distributor")
df = pd.DataFrame(data=distributor.table[0:time_steps+1,:].astype(int), index=["t="+str(i) for i in range(time_steps+1)], columns=col_string)
print(df)

print("manufacturer")
df = pd.DataFrame(data=manufacturer.table[0:time_steps+1,:].astype(int), index=["t="+str(i) for i in range(time_steps+1)], columns=col_string)
print(df)


# In[60]:



plt.figure(2)
plt.plot(alphas,stds_I_retailer   ,  label="std retailer")
plt.plot(alphas,stds_I_wholesaler ,  label="std wholesaler")
plt.plot(alphas,stds_I_distributor,  label="std distributor")
plt.plot(alphas,stds_I_manufacturer, label="std manufacturer")

plt.xlabel("Alphas")
plt.ylabel("Standard Deviations of Final Inventory")
plt.legend()
plt.title("Standard Deviation of Final Inventory vs Alphas")


# In[59]:


plt.figure(2)
plt.plot(alphas,stds_O_retailer   ,  label="std retailer")
plt.plot(alphas,stds_O_wholesaler ,  label="std wholesaler")
plt.plot(alphas,stds_O_distributor,  label="std distributor")
plt.plot(alphas,stds_O_manufacturer, label="std manufacturer")
plt.xlabel("Alphas")
plt.ylabel("Standard Deviations of Orders")
plt.legend()
plt.title("Standard Deviation of Orders vs Alphas")


# In[64]:

#
#plt.figure(3)
##plt.plot(retailer.table[1000:2000,ITEM_ORD])
##plt.plot(wholesaler.table[1000:1050,ITEM_ORD])
##plt.plot(distributor.table[1000:1050,ITEM_ORD])
#plt.plot(manufacturer.table[1000:1050,ITEM_ORD])
#plt.xlabel("Time")
#plt.ylabel("Orders")
#plt.legend()
#plt.title("Orders vs Time")

