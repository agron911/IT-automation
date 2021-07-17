o,f,t,ff,th,s,three,fif = 0,0,0,0,0,0,0,0

n = input()
lis = [int(j) for j in n.split()]
lis[0]=lis[0]/(60*24)
lis[1]=lis[1]*5/(60*24)
lis[2]=lis[2]*10/(60*24)
lis[3]=lis[3]*15/(60*24)
lis[4]=lis[4]*30/(60*24)
lis[5]=lis[5]/24
lis[6]=lis[6]*3/24
lis[7]=lis[7]*15/24
res=0
for i in lis:
    res+=i
print(res)