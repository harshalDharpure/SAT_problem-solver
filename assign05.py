import random
import subprocess
import time
import csv
import os
import psutil
import math
from pysat.solvers import Solver
import pandas as pd
import matplotlib.pyplot as plt

class Course:
    def __init__(self,i,s,d,t):
        self.i=i
        self.s=s
        self.d=d
        self.t=t

def random_instance_to_file(path,rooms=None,n=None):
    if rooms is None:
        rooms=random.randint(3,8)
    if n is None:
        n=random.randint(5,20)
    with open(path,"w") as f:
        f.write(f"M {rooms}\n")
        f.write(f"N {n}\n")
        for i in range(1,n+1):
            s=random.randint(1,30)
            t=random.randint(1,7)
            d=s+t+random.randint(3,20)
            f.write(f"C {i} {s} {d} {t}\n")

def parse_input(file):
    rooms=0
    courses=[]
    with open(file) as f:
        for line in f:
            p=line.strip().split()
            if not p:
                continue
            if p[0]=="M":
                rooms=int(p[1])
            if p[0]=="C":
                courses.append(Course(int(p[1]),int(p[2]),int(p[3]),int(p[4])))
    return rooms,courses

def encode_option1(rooms,courses):
    var={}
    vid=1
    for c in courses:
        for j in range(1,rooms+1):
            for t in range(c.s,c.d-c.t+2):
                var[(c.i,j,t)]=vid
                vid+=1
    clauses=[]
    for c in courses:
        cl=[var[(c.i,j,t)] for j in range(1,rooms+1) for t in range(c.s,c.d-c.t+2)]
        clauses.append(cl)
    for c in courses:
        poss=[(j,t) for j in range(1,rooms+1) for t in range(c.s,c.d-c.t+2)]
        L=len(poss)
        for a in range(L):
            for b in range(a+1,L):
                j1,t1=poss[a]
                j2,t2=poss[b]
                clauses.append([-var[(c.i,j1,t1)],-var[(c.i,j2,t2)]])
    for i in range(len(courses)):
        for jdx in range(i+1,len(courses)):
            c1=courses[i]; c2=courses[jdx]
            for room in range(1,rooms+1):
                for t1 in range(c1.s,c1.d-c1.t+2):
                    for t2 in range(c2.s,c2.d-c2.t+2):
                        if not (t1+c1.t-1 < t2 or t2+c2.t-1 < t1):
                            clauses.append([-var[(c1.i,room,t1)],-var[(c2.i,room,t2)]])
    return vid-1,clauses

def encode_option2(rooms,courses):
    x={}
    y={}
    vid=1
    for c in courses:
        for room in range(1,rooms+1):
            x[(c.i,room)]=vid; vid+=1
    for c in courses:
        for t in range(c.s,c.d-c.t+2):
            y[(c.i,t)]=vid; vid+=1
    clauses=[]
    for c in courses:
        clauses.append([x[(c.i,room)] for room in range(1,rooms+1)])
        ts=list(range(c.s,c.d-c.t+2))
        for a in range(len(ts)):
            for b in range(a+1,len(ts)):
                clauses.append([-y[(c.i,ts[a])],-y[(c.i,ts[b])]])
        clauses.append([y[(c.i,t)] for t in ts])
        for r1 in range(1,rooms+1):
            for r2 in range(r1+1,rooms+1):
                clauses.append([-x[(c.i,r1)],-x[(c.i,r2)]])
    for i in range(len(courses)):
        for jdx in range(i+1,len(courses)):
            c1=courses[i]; c2=courses[jdx]
            for room in range(1,rooms+1):
                for t1 in range(c1.s,c1.d-c1.t+2):
                    for t2 in range(c2.s,c2.d-c2.t+2):
                        if not (t1+c1.t-1 < t2 or t2+c2.t-1 < t1):
                            clauses.append([-x[(c1.i,room)],-y[(c1.i,t1)],-x[(c2.i,room)],-y[(c2.i,t2)]])
    return vid-1,clauses

def write_dimacs(num_vars,clauses,path):
    with open(path,"w") as f:
        f.write(f"p cnf {num_vars} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(map(str,cl))+" 0\n")

def clause_length_counts(clauses):
    two=0; three=0; more=0
    for cl in clauses:
        l=len(cl)
        if l==2: two+=1
        elif l==3: three+=1
        elif l>3: more+=1
    return two,three,more

def run_z3(cnf_path,timeout=None):
    cmd=["z3",cnf_path]
    start=time.time()
    try:
        p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        ps=psutil.Process(p.pid)
        out,err=p.communicate(timeout=timeout)
        end=time.time()
        mem=0
        try:
            mem=ps.memory_info().rss
        except:
            mem=0
        txt=out.decode()+err.decode()
        res="unknown"
        if "sat" in txt.lower(): res="sat"
        if "unsat" in txt.lower(): res="unsat"
        return res,end-start,mem
    except subprocess.TimeoutExpired:
        p.kill()
        return "timeout",None,None

def run_pysat_solver(name,clauses,timeout=None):
    start=time.time()
    proc=psutil.Process(os.getpid())
    mem_before=proc.memory_info().rss
    with Solver(name=name) as s:
        s.append_formula(clauses)
        sat=s.solve()
    end=time.time()
    mem_after=proc.memory_info().rss
    mem=mem_after-mem_before
    res="sat" if sat else "unsat"
    return res,end-start,max(mem,0)

def single_case_run(testfile,do_write_dimacs=True,run_z3_flag=True,run_pysat_flag=True,timeout=60):
    rooms,courses=parse_input(testfile)
    v1,c1=encode_option1(rooms,courses)
    v2,c2=encode_option2(rooms,courses)
    if do_write_dimacs:
        write_dimacs(v1,c1,testfile.replace(".txt","_opt1.cnf"))
        write_dimacs(v2,c2,testfile.replace(".txt","_opt2.cnf"))
    two1,three1,more1=clause_length_counts(c1)
    two2,three2,more2=clause_length_counts(c2)
    results=[]
    if run_z3_flag:
        r1,t1,mem1=run_z3(testfile.replace(".txt","_opt1.cnf"),timeout)
        r2,t2,mem2=run_z3(testfile.replace(".txt","_opt2.cnf"),timeout)
        results.append(("z3","opt1",v1,len(c1),two1,three1,more1,r1,t1,mem1))
        results.append(("z3","opt2",v2,len(c2),two2,three2,more2,r2,t2,mem2))
    if run_pysat_flag:
        cl1=list(c1); cl2=list(c2)
        r1p,t1p,mem1p=run_pysat_solver("m22",cl1,timeout)
        r2p,t2p,mem2p=run_pysat_solver("m22",cl2,timeout)
        results.append(("m22","opt1",v1,len(c1),two1,three1,more1,r1p,t1p,mem1p))
        results.append(("m22","opt2",v2,len(c2),two2,three2,more2,r2p,t2p,mem2p))
        r1g,t1g,mem1g=run_pysat_solver("g3",cl1,timeout)
        r2g,t2g,mem2g=run_pysat_solver("g3",cl2,timeout)
        results.append(("g3","opt1",v1,len(c1),two1,three1,more1,r1g,t1g,mem1g))
        results.append(("g3","opt2",v2,len(c2),two2,three2,more2,r2g,t2g,mem2g))
    return results

def batch_experiment(output_csv="results.csv",tests=100,timeout=60):
    header=["test","solver","encoding","vars","clauses","two_lit","three_lit","more_lit","result","time","mem_bytes"]
    rows=[header]
    for i in range(1,tests+1):
        fname=f"test_{i}.txt"
        random_instance_to_file(fname)
        res=single_case_run(fname,do_write_dimacs=True,run_z3_flag=True,run_pysat_flag=True,timeout=timeout)
        for r in res:
            rows.append([i,r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[9]])
        if i%10==0:
            print("done",i)
    with open(output_csv,"w",newline="") as f:
        w=csv.writer(f)
        w.writerows(rows)
    df=pd.read_csv(output_csv)
    agg=df.groupby(["solver","encoding"])["time"].mean().unstack()
    agg.plot(kind="bar")
    plt.ylabel("avg time (s)")
    plt.tight_layout()
    plt.savefig("performance.png")
    print("done all; results.csv and performance.png written")

if __name__=="__main__":
    batch_experiment(output_csv="results.csv",tests=100,timeout=30)
