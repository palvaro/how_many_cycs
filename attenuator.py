import copy
import random

from graphviz import Digraph

MAX_AMBIGUITY = 5


class Transaction(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Xact(" + self.name + ")"


class Dependency(object):
    def __init__(self, kind, tfrom, tto):
        self.kind = kind
        self.tfrom = tfrom
        self.tto = tto

    def __str__(self):
        return self.tfrom.name + "--" + self.kind + "->" + self.tto.name


class DSG(object):
    def __init__(self):
        self.transactions = []
        self.dependencies = []
        self.outgoing = {}
        self.incoming = {}

    def add_xact(self, name):
        xact = Transaction(name)
        self.transactions.append(xact)
        return xact

    def add_dep(self, kind, tfrom, tto):
        self.dependencies.append(Dependency(kind, tfrom, tto))
        new = [tto, kind]
        # print "ADD DEP " + tto.name
        if tfrom in self.outgoing:
            self.outgoing[tfrom].append(new)
        else:
            self.outgoing[tfrom] = [new]
        new = [tfrom, kind]

        print "OK"
        if tto in self.incoming:
            self.incoming[tto].append(new)
        else:
            self.incoming[tto] = [new]

    def all_reachable(self, tfrom, visited):
        if tfrom in self.outgoing:
            ret = set(map(lambda x: x[0], self.outgoing[tfrom]))
            ret.add(tfrom)
            visited.add(tfrom)
            for t in self.outgoing[tfrom]:
                ret.add(t[0])
                if t[0] not in visited:
                    ret = ret.union(self.all_reachable(t[0], visited))
                    visited = visited.union(ret)
            return ret
        else:
            return set([tfrom])

    def __str__(self):
        return "\n".join(map(lambda x: x.__str__(), self.dependencies))

    def to_dot(self):
        dot = Digraph(comment="dwarf")
        for xact in self.transactions:
            dot.node(xact.name)

        for dep in self.dependencies:
            dot.edge(dep.tfrom.name, dep.tto.name, label=dep.kind)

        return dot


class HyperDSG(object):
    def __init__(self, dwarf):
        self.hyper_deps = []
        self.dsg = dwarf.dwarf
        print "UM  " + str(self.dsg.dependencies)
        for dep in self.dsg.dependencies:
            if dep.kind == "WR":
                print "Yay"
                print "DEP is " + str(dep)
                # flip a coin about how many dep hyper edges to make
                edges = random.randint(1, MAX_AMBIGUITY)
                if edges > 1:
                    # delete the initial edge
                    self.dsg.dependencies.remove(dep)
                    # add my own edge back as a hyperedge
                    self.hyper_deps.append(Dependency(dep.kind, dep.tfrom, dep.tto))
                    # and then add in a bunch more hyperedges.  should we sometimes create new transactions?
                    # probably.  but not for now; let's go wild.

                    # pick a transaction that is reachable from tto.  draw a maybe WR EDGE FROM IT TO TTO!
                    print "reach from " + str(dep.tto)
                    all = list(self.dsg.all_reachable(dep.tto, set()))
                    indx = random.randint(0, len(all) - 1)
                    self.hyper_deps.append(Dependency(dep.kind, all[indx], dep.tto))

    def to_dot(self):
        dot = self.dsg.to_dot()
        for dep in self.hyper_deps:
            dot.edge(dep.tfrom.name, dep.tto.name, label=dep.kind, style="dashed")
        return dot

    def to_history(self):
        txns = {}
        #FIXME obviously will need to change potential key choices.
        letters = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        letters = random.shuffle(letters)
        # go through dsg edges first, assign variables and their associated values as dictated by the label type.
        for dep in self.dsg.dependencies:
            ti_ops = {}
            tj_ops = {}
            if dep.kind == "WW":
                # assign Ti: {X=foo} Tj: {X=bar}
                ti_ops[":f"] = tj_ops[":f"] = "write"
                ti_ops[":k"] = tj_ops[":k"] = letters.pop()
                ti_ops[":v"] = random.randint(1, MAX_AMBIGUITY)
                tj_ops[":v"] = random.randint(1, MAX_AMBIGUITY)
                txns[dep.tfrom] = ti_ops
                txns[dep.tto] = tj_ops
            if dep.kind == "WR":
                # assign Ti: {X=foo} Tj: {Read X=foo}
                ti_ops[":f"] = "write"
                tj_ops[":f"] = "read"
                ti_ops[":k"] = tj_ops[":k"] = letters.pop()
                ti_ops[":v"] = tj_ops[":v"] = random.randint(1, MAX_AMBIGUITY)
                txns[dep.tfrom] = ti_ops
                txns[dep.tto] = tj_ops
            if dep.kind == "RW":
                # assign Ti: {Read X=foo} Tj: {X=bar} where there already exists some Tk: {X=foo}
        # then go through hdsg edges,
        # for maybe_dep in self.hyper_deps:


class Dwarf(object):
    # need to define your own init!
    def __init__(self):
        raise Exception("please define init")

    def withdraw(self):
        # pick an outgoing at random
        indx = random.randint(0, len(self.dwarf.dependencies) - 1)
        some_edge = self.dwarf.dependencies[indx]
        self.dwarf.dependencies.pop(indx)
        return some_edge

    def serial_grow(self, name):
        # pick a node at random
        some_node = self.dwarf.transactions[random.randint(0, len(self.dwarf.transactions) - 1)]
        # create a new transaction
        # N.B. OR GRAB AN EXISTING ONE BEAVIS!!
        xact = Transaction(name)
        # pick a label
        options = ["WW", "WR", "RW"]
        label = options[random.randint(0, 2)]
        # pick a direction
        if random.randint(0, 1) == 0:
            self.dwarf.add_dep(label, xact, some_node)
        else:
            self.dwarf.add_dep(label, some_node, xact)

    def cycle_grow(self, name):
        # pick an edge at random
        # TODO: wait wait how do I know the edge is in a cycle?
        some_edge = self.withdraw()
        while not some_edge.tfrom in self.dwarf.all_reachable(some_edge.tto, set()):
            self.dwarf.add_dep(some_edge.kind, some_edge.tfrom, some_edge.tto)
            some_edge = self.withdraw()
        print "EDGE is " + str(some_edge)
        # create a new transaction
        xact = Transaction(name)
        self.local_grow(xact, some_edge)

    def grow(self, name):
        if random.randint(0, 1) == 0:
            self.serial_grow(name)
        else:
            self.cycle_grow(name)

    def grow_n(self, n):
        for x in range(0, n):
            self.grow(str(x))

    def dfs(self, current, sentinel, seen):
        if current == sentinel:
            return True
        else:
            # N.B. this seems wrong; we want to test if there *exists* a way to find myself.
            # this appears to declare victory if there *exists a way to not* find myself.
            if current not in self.dwarf.outgoing:
                return False
            seen[current] = True
            for ptr in self.dwarf.outgoing[current]:
                if ptr[0] not in seen:
                    if self.dfs(ptr[0], sentinel, seen):
                        return True
        return False

    def is_in_cycle(self, edge):
        return self.dfs(edge.tto, edge.tfrom, {})

    def shrink(self):
        # (this is not a smart algorithm)
        # pick an edge at random
        # doing this randomly is likely to hurt us!

        while len(self.dwarf.dependencies) > 2:
            print "OK!!!"
            some_edge = self.withdraw()
            # if the edge doesn't participate in a cycle, go ahead and delete it.
            if self.is_in_cycle(some_edge):
                print  "CYC " + str(some_edge)
                if self.can_shrink(some_edge):
                    # patch things up
                    print "patching UP " + str(some_edge)
                    if some_edge.tto in self.dwarf.incoming:
                        print "INC: " + str(self.dwarf.incoming[some_edge.tto])
                    else:
                        print "lookup " + some_edge.tto + "hrm, nothing in " + str(self.dwarf.incoming)
                    isnap = copy.deepcopy(self.dwarf.incoming)
                    # if some_edge.tto in isnap:
                    if some_edge.tto in self.dwarf.incoming:
                        print "UM"
                        snap = list(self.dwarf.incoming[some_edge.tto])
                        # for incoming in isnap[some_edge.tto]:
                        for incoming in snap:
                            print "AGIN " + str(incoming[0].name)
                            self.dwarf.add_dep(incoming[1], incoming[0], some_edge.tto)

                    print "OK1"
                    # osnap = copy.deepcopy(self.dwarf.outgoing)

                    if some_edge.tfrom in self.dwarf.outgoing:
                        snap = list(self.dwarf.outgoing[some_edge.tfrom])
                        for outgoing in snap:
                            self.dwarf.add_dep(outgoing[1], some_edge.tfrom, outgoing[0])

                    print "DONE PATCHING UP"
                else:
                    # add it back!
                    print "adding back"
                    self.dwarf.add_dep(some_edge.label, some_edge.tfrom, some_edge.tto)

            else:
                print "NO CYC " + str(some_edge)

    def graph(self, name):
        dot = self.dwarf.to_dot()
        dot.render(name, view=True)


class WriteConflict(Dwarf):
    def __init__(self):
        self.dwarf = DSG()
        a = self.dwarf.add_xact("A")
        b = self.dwarf.add_xact("B")
        self.dwarf.add_dep("WW", a, b)
        self.dwarf.add_dep("WW", b, a)

    def local_grow(self, xact, edge):
        self.dwarf.add_dep("WW", edge.tfrom, xact)
        self.dwarf.add_dep("WW", xact, edge.tto)

    def can_shrink(self, edge):
        # we can delete any edge in our WW cycle.
        return True


class CircularDependency(Dwarf):
    def __init__(self):
        self.dwarf = DSG()
        a = self.dwarf.add_xact("A")
        b = self.dwarf.add_xact("B")
        self.dwarf.add_dep("WR", a, b)
        self.dwarf.add_dep("WR", b, a)

    def local_grow(self, xact, edge):
        # anything but a RW
        options = ["WW", "WR"]
        option1 = options[random.randint(0, 1)]
        option2 = options[random.randint(0, 1)]
        self.dwarf.add_dep(option1, edge.tfrom, xact)
        self.dwarf.add_dep(option2, xact, edge.tto)

    def can_shrink(self, edge):
        # FIXME
        return True


class AntiDependency(Dwarf):
    # N.B. there don't have to be two RW edge!  what is the best
    # way to minimally constrain?
    def __init__(self):
        self.dwarf = DSG()
        a = self.dwarf.add_xact("A")
        b = self.dwarf.add_xact("B")
        self.dwarf.add_dep("RW", a, b)
        self.dwarf.add_dep("RW", b, a)

    def local_grow(self, xact, edge):
        options = ["WW", "WR", "RW"]
        option1 = options[random.randint(0, 2)]
        option2 = options[random.randint(0, 2)]
        self.dwarf.add_dep(option1, edge.tfrom, xact)
        self.dwarf.add_dep(option2, xact, edge.tto)

    def can_shrink(self, some_edge):
        # FIXME
        return True
