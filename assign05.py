import random, subprocess, time, csv
from pysat.solvers import Solver

class Course:
    def __init__(self,i,s,d,t):
        self.i=i; self.s=s; self.d=d; self.t=t

def generate_instance(file):
    m=random.randint(3,7)
    n=random.randint(5,15)
    with open(file,"w") as f:
        f.write(f"M {m}\nN {n}\n")
        for i in range(1,n+1):
            s=random.randint(1,25)
            t=random.randint(1,6)
            d=s+t+random.randint(3,10)
            f.write(f"C {i} {s} {d} {t}\n")

def read_instance(file):
    rooms=0; courses=[]
    for line in open(file):
        p=line.split()
        if not p: continue
        if p[0]=="M": rooms=int(p[1])
        if p[0]=="C": courses.append(Course(int(p[1]),int(p[2]),int(p[3]),int(p[4])))
    return rooms,courses

def encode1(rooms,courses):
    var={}; vid=1
    for c in courses:
        for r in range(rooms):
            for t in range(c.s,c.d-c.t+2):
                var[(c.i,r,t)]=vid; vid+=1
    clauses=[]
    for c in courses:
        opts=[var[(c.i,r,t)] for r in range(rooms) for t in range(c.s,c.d-c.t+2)]
        clauses.append(opts)
        for i in range(len(opts)):
            for j in range(i+1,len(opts)):
                clauses.append([-opts[i],-opts[j]])
    for i in range(len(courses)):
        for j in range(i+1,len(courses)):
            c1,c2=courses[i],courses[j]
            for r in range(rooms):
                for t1 in range(c1.s,c1.d-c1.t+2):
                    for t2 in range(c2.s,c2.d-c2.t+2):
                        if not(t1+c1.t-1<t2 or t2+c2.t-1<t1):
                            clauses.append([-var[(c1.i,r,t1)],-var[(c2.i,r,t2)]])
    return vid-1,clauses

def encode2(rooms,courses):
    x={}; y={}; vid=1
    for c in courses:
        for r in range(rooms):
            x[(c.i,r)]=vid; vid+=1
    for c in courses:
        for t in range(c.s,c.d-c.t+2):
            y[(c.i,t)]=vid; vid+=1
    clauses=[]
    for c in courses:
        rooms_vars=[x[(c.i,r)] for r in range(rooms)]
        clauses.append(rooms_vars)
        for i in range(len(rooms_vars)):
            for j in range(i+1,len(rooms_vars)):
                clauses.append([-rooms_vars[i],-rooms_vars[j]])
        ts=[y[(c.i,t)] for t in range(c.s,c.d-c.t+2)]
        clauses.append(ts)
        for i in range(len(ts)):
            for j in range(i+1,len(ts)):
                clauses.append([-ts[i],-ts[j]])
    for i in range(len(courses)):
        for j in range(i+1,len(courses)):
            c1,c2=courses[i],courses[j]
            for r in range(rooms):
                for t1 in range(c1.s,c1.d-c1.t+2):
                    for t2 in range(c2.s,c2.d-c2.t+2):
                        if not(t1+c1.t-1<t2 or t2+c2.t-1<t1):
                            clauses.append([-x[(c1.i,r)],-y[(c1.i,t1)],-x[(c2.i,r)],-y[(c2.i,t2)]])
    return vid-1,clauses

def write_cnf(vars,clauses,file):
    with open(file,"w") as f:
        f.write(f"p cnf {vars} {len(clauses)}\n")
        for c in clauses:
            f.write(" ".join(map(str,c))+" 0\n")

def run_z3(file):
    t=time.time()
    out=subprocess.run(["z3",file],capture_output=True,text=True).stdout.lower()
    return ("sat" if "sat" in out else "unsat"),time.time()-t

def run_pysat(name,clauses):
    t=time.time()
    with Solver(name=name) as s:
        s.append_formula(clauses)
        res=s.solve()
    return ("sat" if res else "unsat"),time.time()-t

def experiment():
    rows=[["test","solver","encoding","vars","clauses","time"]]

    for i in range(1,101):

        fname=f"test{i}.txt"
        generate_instance(fname)
        rooms,courses=read_instance(fname)

        v1,c1=encode1(rooms,courses)
        v2,c2=encode2(rooms,courses)

        write_cnf(v1,c1,f"opt1.cnf")
        write_cnf(v2,c2,f"opt2.cnf")

        r,t=run_z3("opt1.cnf")
        rows.append([i,"Z3","opt1",v1,len(c1),t])

        r,t=run_z3("opt2.cnf")
        rows.append([i,"Z3","opt2",v2,len(c2),t])

        r,t=run_pysat("m22",c1)
        rows.append([i,"MiniSAT","opt1",v1,len(c1),t])

        r,t=run_pysat("m22",c2)
        rows.append([i,"MiniSAT","opt2",v2,len(c2),t])

        r,t=run_pysat("g3",c1)
        rows.append([i,"Glucose","opt1",v1,len(c1),t])

        r,t=run_pysat("g3",c2)
        rows.append([i,"Glucose","opt2",v2,len(c2),t])

        if i%10==0: print("completed",i)

    with open("results.csv","w",newline="") as f:
        csv.writer(f).writerows(rows)

    print("results.csv generated")

if __name__=="__main__":
    experiment()
